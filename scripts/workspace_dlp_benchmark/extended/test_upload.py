"""v3のアップロード処理を模擬Driveで検証。認証・通信は行わない。"""
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
import upload


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class FakeDrive:
    def __init__(self, owner='owner@example.test', shared=None, corrupt=None, fail_at=None):
        self.owner, self.shared = owner, shared
        self.corrupt, self.fail_at = corrupt, fail_at
        self.calls, self.created = [], []

    def about(self):
        return SimpleNamespace(get=lambda **kwargs: Request({'user': {'emailAddress': self.owner}}))

    def files(self):
        return self

    def metadata(self, ident, body):
        result = {'id': ident, **body, 'trashed': False, 'version': '1',
                  'capabilities': {'canAddChildren': True}, 'createdTime': '2026-01-01T00:00:00Z'}
        if self.shared:
            result['driveId'] = self.shared
        else:
            result['owners'] = [{'emailAddress': self.owner}]
        return result

    def get(self, **kwargs):
        self.calls.append(('get', kwargs))
        return Request(self.metadata('parent-test', {'mimeType': 'application/vnd.google-apps.folder'}))

    def create(self, **kwargs):
        self.calls.append(('create', kwargs))
        if len(self.created) == self.fail_at:
            return Request(RuntimeError('synthetic transport failure'))
        result = self.metadata('new-' + str(len(self.created)), kwargs['body'])
        self.created.append(result)
        if 'media_body' in kwargs:
            payload = kwargs['media_body'].getvalue()
            result['md5Checksum'] = hashlib.md5(payload, usedforsecurity=False).hexdigest()
        if self.corrupt:
            self.corrupt(result)
        return Request(result)


def scope(root, shared=None, owner='owner@example.test', age=0, active=True):
    readback = {'schema_version': 1, 'kind': 'workspace_dlp_scope_evidence',
                'verified_at': (datetime.now(timezone.utc) - timedelta(hours=age)).isoformat(),
                'rule_scope_checks': [{'rule_id': 'rule-test', 'active': active, 'service': 'drive',
                    'matches': True, 'target_kind': 'shared_drive' if shared else 'user',
                    'target_id': shared or owner, 'scope_kind': 'org_unit', 'scope_id': 'synthetic-ou',
                    'basis': '通信なし試験用の合成証跡'}]}
    proof = root / 'scope-readback.json'
    proof.write_text(json.dumps(readback))
    value = {'schema_version': 1, 'creator_email': owner, 'parent_id': 'parent-test',
             'drive_kind': 'shared_drive' if shared else 'my_drive', 'rule_ids': ['rule-test'],
             'scope_readback': {'path': proof.name, 'sha256': upload.digest(proof)}}
    if shared:
        value['shared_drive_id'] = shared
    path = root / 'scope.json'
    path.write_text(json.dumps(value))
    return path


class UploadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dataset = self.root / 'dataset'
        rows = build.make(self.dataset)
        # 通信模擬は2資料で十分。余分な383資料が勝手にアップロードされないことも検査。
        self.rows = rows[:2]
        (self.dataset / 'ground_truth.json').write_text(json.dumps(self.rows))
        self.output = self.root / 'result.json'

    def execute(self, drive=None, evidence=None, **options):
        return upload.execute(self.dataset, 'parent-test', self.output,
                              evidence or scope(self.root), drive or FakeDrive(), SimpleNamespace(),
                              lambda stream, **kwargs: stream, **options)

    def test_inactive_rules_are_rejected_by_default_before_network(self):
        drive = FakeDrive()
        with self.assertRaises(ValueError):
            self.execute(drive, scope(self.root, active=False))
        self.assertEqual(drive.calls, [])
        self.assertFalse(self.output.exists())

    def test_explicit_pre_activation_placement_records_inactive_without_activating(self):
        drive = FakeDrive()
        evidence = scope(self.root, active=False)
        result = self.execute(drive, evidence, pre_activation_placement=True)
        self.assertTrue(result['complete'])
        self.assertTrue(result['pre_activation_placement'])
        self.assertFalse(result['rule_activation']['all_rules_active'])
        self.assertEqual(result['rule_activation']['rule_states'], [{'rule_id': 'rule-test', 'active': False}])
        self.assertFalse(result['rule_activation']['activation_performed'])
        self.assertFalse(result['preflight']['binding']['all_rules_active'])
        self.assertEqual({name for name, _ in drive.calls}, {'get', 'create'})
        self.assertFalse(json.loads((self.root / 'scope-readback.json').read_text())['rule_scope_checks'][0]['active'])
        # 配置用の許可を後続の既定確認に引き継がない。
        with self.assertRaises(ValueError):
            upload.drive_support().preflight(drive, SimpleNamespace(), 'parent-test', evidence)

    def test_pre_activation_placement_does_not_accept_unknown_activation_state(self):
        for active in (None, 0, 1, 'false'):
            drive = FakeDrive()
            with self.subTest(active=active), self.assertRaises(ValueError):
                self.execute(drive, scope(self.root, active=active), pre_activation_placement=True)
            self.assertEqual(drive.calls, [])

    def test_pre_activation_placement_keeps_owner_and_age_checks(self):
        for options in ({'age': 73}, {'owner': 'different@example.test'}):
            drive = FakeDrive()
            with self.subTest(options=options), self.assertRaises((ValueError, RuntimeError)):
                self.execute(drive, scope(self.root, active=False, **options), pre_activation_placement=True)
            self.assertEqual(drive.created, [])

    def test_pre_activation_flag_is_recorded_in_offline_plan(self):
        with patch.object(upload, 'execute') as execute, contextlib.redirect_stdout(io.StringIO()) as stream:
            upload.main(['--dataset', str(self.dataset), '--pre-activation-placement'])
        execute.assert_not_called()
        self.assertTrue(json.loads(stream.getvalue())['pre_activation_placement'])

    def test_plan_is_default_and_never_constructs_api_client(self):
        with patch.object(upload, 'execute') as execute, contextlib.redirect_stdout(io.StringIO()) as stream:
            upload.main(['--dataset', str(self.dataset)])
        execute.assert_not_called()
        result = json.loads(stream.getvalue())
        self.assertEqual(result['file_count'], 2)
        self.assertFalse(result['network_executed'])

    def test_only_new_folder_and_declared_txt_created_no_permission_api(self):
        drive = FakeDrive()
        result = self.execute(drive)
        self.assertTrue(result['complete'])
        self.assertEqual(len(drive.created), 3)
        self.assertEqual([r['name'] for r in drive.created[1:]], [r['file'] for r in self.rows])
        self.assertEqual(drive.created[0]['parents'], ['parent-test'])
        self.assertTrue(all(r['parents'] == ['new-0'] for r in drive.created[1:]))
        self.assertTrue(all(r['content_verified'] for r in result['uploads']))
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual({name for name, _ in drive.calls}, {'get', 'create'})

    def test_shared_drive_path_uses_shared_scope(self):
        drive = FakeDrive(shared='synthetic-shared')
        result = self.execute(drive, scope(self.root, shared='synthetic-shared'))
        self.assertTrue(result['complete'])
        self.assertEqual(result['preflight']['drive_kind'], 'shared_drive')

    def test_wrong_identity_stops_before_creation(self):
        drive = FakeDrive(owner='different@example.test')
        with self.assertRaises(RuntimeError):
            self.execute(drive)
        self.assertEqual(drive.created, [])
        self.assertEqual(json.loads(self.output.read_text())['phase'], 'failed')

    def test_non_delegated_service_account_stops(self):
        owner = 'synthetic@example.gserviceaccount.com'
        drive = FakeDrive(owner=owner)
        with self.assertRaises(RuntimeError):
            self.execute(drive, scope(self.root, owner=owner))
        self.assertEqual(drive.created, [])

    def test_old_scope_and_parent_mismatch_fail_before_network(self):
        drive = FakeDrive()
        with self.assertRaises(ValueError):
            self.execute(drive, scope(self.root, age=73))
        self.assertEqual(drive.calls, [])
        source = scope(self.root)
        value = json.loads(source.read_text())
        value['parent_id'] = 'different'
        source.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.execute(drive, source)
        self.assertEqual(drive.calls, [])

    def test_existing_report_prevents_duplicate_create(self):
        self.output.write_text('existing')
        drive = FakeDrive()
        with self.assertRaises(ValueError):
            self.execute(drive)
        self.assertEqual(drive.calls, [])
        self.assertEqual(self.output.read_text(), 'existing')

    def test_report_cannot_be_in_dataset_or_repository(self):
        for path in (self.dataset / 'result.json', upload.HERE / 'result.json'):
            with self.assertRaises(ValueError):
                upload.validate_output(self.dataset, path)

    def test_changed_source_rejected_before_network(self):
        (self.dataset / 'drive_upload' / self.rows[0]['file']).write_text('modified')
        drive = FakeDrive()
        with self.assertRaises(ValueError):
            self.execute(drive)
        self.assertEqual(drive.calls, [])

    def test_partial_failure_preserves_successes_and_unknown_inflight(self):
        drive = FakeDrive(fail_at=2)
        with self.assertRaises(RuntimeError):
            self.execute(drive)
        saved = json.loads(self.output.read_text())
        self.assertFalse(saved['complete'])
        self.assertEqual(len(saved['uploads']), 1)
        self.assertEqual(saved['folder']['id'], 'new-0')
        self.assertEqual(saved['inflight']['name'], self.rows[1]['file'])
        self.assertEqual(saved['inflight']['outcome'], 'unknown_until_response')
        self.assertEqual(len([c for c in drive.calls if c[0] == 'create']), 3)

    def test_checksum_failure_preserves_returned_file_id(self):
        def corrupt(result):
            if result['mimeType'] == 'text/plain':
                result['md5Checksum'] = 'wrong'
        with self.assertRaises(RuntimeError):
            self.execute(FakeDrive(corrupt=corrupt))
        saved = json.loads(self.output.read_text())
        self.assertEqual(saved['uploads'][0]['metadata']['id'], 'new-1')
        self.assertFalse(saved['uploads'][0]['content_verified'])
        self.assertFalse(saved['complete'])

    def test_source_change_after_plan_stops_without_uploading_changed_bytes(self):
        drive = FakeDrive()
        original = drive.create
        def create(**kwargs):
            request = original(**kwargs)
            if len(drive.created) == 1:
                (self.dataset / 'drive_upload' / self.rows[0]['file']).write_text('modified')
            return request
        drive.create = create
        with self.assertRaises(RuntimeError):
            self.execute(drive)
        self.assertEqual(len(drive.created), 1)


if __name__ == '__main__':
    unittest.main()
