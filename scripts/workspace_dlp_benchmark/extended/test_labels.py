"""ラベル読取りを模擬応答だけで検証。実環境には接続しない。"""
import copy
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import labels
from catalog import ITEMS


def mapping():
    return {'schema_version': 1, 'configuration': 'combined',
            'files': [{'case_id': 'fictional-case', 'file_id': 'fictional-file', 'expected_md5': hashlib.md5(b'synthetic').hexdigest()}],
            'groups': {g: {'label_id': 'fictional-' + g, 'field_id': 'field',
                           'selection_ids': ['high', 'medium']} for g in labels.GROUP_IDS}}


def metadata(version='1'):
    return {'id': 'fictional-file', 'version': version, 'modifiedTime': '2026-01-01T00:00:00Z', 'trashed': False, 'mimeType': 'text/plain', 'md5Checksum': hashlib.md5(b'synthetic').hexdigest()}


def drive_with(pages):
    drive = Mock()
    drive.files.return_value.get.return_value.execute.side_effect = [metadata(), metadata()]
    drive.files.return_value.listLabels.return_value.execute.side_effect = pages
    return drive


def truth():
    matrix = dict.fromkeys(ITEMS, 0)
    matrix['individual'] = 1
    return [{'case_id': 'fictional-case', 'split': '評価', 'expected_by_item': matrix,
             'item': 'individual', 'group': 'G1', 'expected': 1, 'file': 'case.txt',
             'sha256': hashlib.sha256(b'synthetic').hexdigest()}]


class LabelsTest(unittest.TestCase):
    def test_pagination_collects_second_page_value_and_only_reads(self):
        drive = drive_with([{'labels': [], 'nextPageToken': 'page2'},
                            {'labels': [{'id': 'fictional-G1', 'fields': {
                                'field': {'valueType': 'selection', 'selection': ['high']}}}]}])
        saved = labels.collect(drive, mapping())
        result = labels.compare(truth(), saved)
        self.assertTrue(result['rows'][0]['label_present'])
        self.assertEqual(result['rows'][0]['detection_status'], 'pending')
        self.assertEqual(result['evaluation_label_snapshot_metrics']['G1']['recall'], 1)
        drive.files.return_value.listLabels.assert_called_with(fileId='fictional-file', maxResults=100, pageToken='page2')
        self.assertEqual({call[0] for call in drive.mock_calls},
                         {'files', 'files().get', 'files().get().execute',
                          'files().listLabels', 'files().listLabels().execute'})

    def test_empty_labels_are_snapshot_absence_only(self):
        saved = labels.collect(drive_with([{}]), mapping())
        row = labels.compare(truth(), saved)['rows'][0]
        self.assertFalse(row['label_present'])
        self.assertEqual(row['label_state'], 'absent')
        self.assertEqual(row['detection_status'], 'pending')

    def test_api_failure_does_not_become_absence(self):
        saved = labels.collect(drive_with([RuntimeError('synthetic error')]), mapping())
        row = labels.compare(truth(), saved)['rows'][0]
        self.assertIsNone(row['label_present'])
        self.assertEqual(row['label_state'], 'error')

    def test_changed_file_version_is_stale(self):
        drive = drive_with([{}])
        drive.files.return_value.get.return_value.execute.side_effect = [metadata(), metadata('2')]
        saved = labels.collect(drive, mapping())
        self.assertEqual(saved['files'][0]['status'], 'stale')
        self.assertIsNone(labels.compare(truth(), saved)['rows'][0]['label_present'])

    def test_looped_token_retains_error(self):
        drive = drive_with([{'nextPageToken': 'same'}, {'nextPageToken': 'same'}])
        saved = labels.collect(drive, mapping())
        self.assertEqual(saved['files'][0]['status'], 'error')
        self.assertEqual(drive.files.return_value.listLabels.call_count, 2)

    def test_missing_metadata_and_trashed_are_unresolved(self):
        for final, expected in [({'id': 'fictional-file'}, 'error'),
                                (dict(metadata(), trashed=True), 'pending')]:
            with self.subTest(expected=expected):
                drive = drive_with([{}])
                drive.files.return_value.get.return_value.execute.side_effect = [metadata(), final]
                saved = labels.collect(drive, mapping())
                self.assertEqual(saved['files'][0]['status'], expected)

    def test_unexpected_choice_and_duplicate_label_are_unresolved(self):
        label = {'id': 'fictional-G1', 'fields': {'field': {'valueType': 'selection', 'selection': ['other']}}}
        for content, expected in [([label], 'unexpected_selection'), ([label, label], 'conflict')]:
            saved = labels.collect(drive_with([{'labels': content}]), mapping())
            row = labels.compare(truth(), saved)['rows'][0]
            self.assertEqual(row['label_state'], expected)
            self.assertIsNone(row['label_present'])

    def test_unknown_truth_excluded_from_primary_metrics(self):
        data = truth()
        data[0]['expected_by_item']['individual'] = None
        saved = labels.collect(drive_with([{}]), mapping())
        result = labels.compare(data, saved)
        metric = result['evaluation_label_snapshot_metrics']['G1']
        self.assertEqual(metric['counts']['unscorable'], 1)
        self.assertIsNone(metric['accuracy'])

    def test_unobserved_files_remain_pending(self):
        saved = labels.collect(drive_with([{}]), mapping())
        saved['files'] = []
        result = labels.compare(truth(), saved)
        self.assertEqual(result['rows'][0]['label_state'], 'pending')
        self.assertIsNone(result['evaluation_label_snapshot_metrics']['G1']['recall'])

    def test_binding_mismatch_and_duplicate_are_rejected(self):
        for mutate in ('mismatch', 'duplicate'):
            saved = labels.collect(drive_with([{}]), mapping())
            if mutate == 'mismatch':
                saved['files'][0]['file_id'] = 'another-file'
            else:
                saved['files'].append(copy.deepcopy(saved['files'][0]))
            with self.assertRaises(ValueError):
                labels.compare(truth(), saved)

    def test_default_plan_does_not_collect(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'mapping.json'
            source.write_text(json.dumps(mapping()))
            with patch.object(labels, 'collect') as collect, contextlib.redirect_stdout(io.StringIO()) as stream:
                labels.main(['--mapping', str(source)])
            collect.assert_not_called()
            self.assertFalse(json.loads(stream.getvalue())['network_executed'])

    def test_offline_compare_checks_truth_binding_and_writes_privately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'ground_truth.json').write_text(json.dumps(truth()))
            (root / 'drive_upload').mkdir()
            (root / 'drive_upload/case.txt').write_bytes(b'synthetic')
            (root / 'mapping.json').write_text(json.dumps(mapping()))
            saved = labels.collect(drive_with([{}]), mapping())
            saved['truth_sha256'] = labels.digest(root / 'ground_truth.json')
            (root / 'snapshot.json').write_text(json.dumps(saved))
            arguments = ['--mapping', str(root / 'mapping.json'), '--snapshot', str(root / 'snapshot.json'),
                         '--dataset', str(root), '--output', str(root / 'report.json')]
            with patch.object(labels, 'collect') as collect:
                labels.main(arguments)
                collect.assert_not_called()
            self.assertEqual((root / 'report.json').stat().st_mode & 0o777, 0o600)
            (root / 'ground_truth.json').write_text('[]')
            with self.assertRaisesRegex(ValueError, '正解表'):
                labels.main(arguments)

    def test_execute_rejects_invalid_truth_before_authentication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'mapping.json').write_text(json.dumps(mapping()))
            (root / 'ground_truth.json').write_text('[]')
            with patch.object(labels, 'collect') as collect, self.assertRaisesRegex(ValueError, '正解表'):
                labels.main(['--mapping', str(root / 'mapping.json'), '--dataset', str(root),
                             '--output', str(root / 'result.json'), '--execute'])
            collect.assert_not_called()

    def test_edited_before_observation_is_stale_even_if_version_stays_constant(self):
        drive = drive_with([{}])
        changed = dict(metadata(), md5Checksum=hashlib.md5(b'changed').hexdigest())
        drive.files.return_value.get.return_value.execute.side_effect = [changed, changed]
        saved = labels.collect(drive, mapping())
        row = labels.compare(truth(), saved)['rows'][0]
        self.assertEqual(row['label_state'], 'stale')
        self.assertIsNone(row['label_present'])

    def test_missing_checksum_does_not_become_absence(self):
        drive = drive_with([{}])
        missing = metadata()
        del missing['md5Checksum']
        drive.files.return_value.get.return_value.execute.side_effect = [missing, missing]
        saved = labels.collect(drive, mapping())
        self.assertEqual(saved['files'][0]['status'], 'error')

    def test_collect_requires_content_binding_before_network(self):
        value = mapping()
        del value['files'][0]['expected_md5']
        drive = Mock()
        with self.assertRaises(ValueError):
            labels.collect(drive, value)
        self.assertEqual(drive.mock_calls, [])

    def test_primary_metrics_exclude_unknown_truth(self):
        data = truth()
        unknown = copy.deepcopy(data[0])
        unknown['case_id'] = 'unknown-case'
        unknown['expected_by_item']['individual'] = None
        data.append(unknown)
        page = {'labels': [{'id': 'fictional-G1', 'fields': {
            'field': {'valueType': 'selection', 'selection': ['high']}}}]}
        saved = labels.collect(drive_with([page]), mapping())
        metric = labels.compare(data, saved)['evaluation_label_snapshot_metrics']['G1']
        self.assertEqual(metric['primary_metrics']['recall'], 1)
        self.assertEqual(metric['primary_metrics']['accuracy'], 1)
        self.assertEqual(metric['counts']['unscorable'], 1)

    def test_invalid_mapping_is_rejected(self):
        value = mapping()
        value['groups']['G2']['label_id'] = value['groups']['G1']['label_id']
        with self.assertRaises(ValueError):
            labels.plan(value)
        value = mapping()
        value['configuration'] = 'arbitrary'
        with self.assertRaises(ValueError):
            labels.plan(value)


if __name__ == '__main__':
    unittest.main()
