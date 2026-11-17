"""実APIへ接続せず、v3の原票→証拠照合→採点を一貫して確認する。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import audit
from build import combined_regex
from catalog import ITEMS
from common import object_digest
from test_support import AuditFixture, write


def fixture(root, kind='email'):
    f = AuditFixture(root, kinds=('email',), thresholds=('POSSIBLE',))
    for row in f.truth:
        row.update(item=kind, group=ITEMS[kind]['group'])
        row['expected_by_item'] = dict.fromkeys(ITEMS, 0)
        row['expected_by_item'][kind] = row['expected']
    original = copy.deepcopy(f.profiles[0])
    old_policies = {p['name']: p for p in f.policy_before['policies']}
    policies = {key: value for key, value in old_policies.items() if value['setting']['type'] == 'settings/detector.word_list'}
    profiles = []
    for configuration in audit.CONFIGURATIONS:
        profile = copy.deepcopy(original)
        profile.update(benchmark='v3-extended', configuration=configuration, kind=kind)
        for role in profile['roles']:
            profile['roles'][role]['id'] = 'policies/v3-' + configuration + '-' + role
            policy = copy.deepcopy(old_policies[original['roles'][role]['id']])
            policy['name'] = profile['roles'][role]['id']
            policy['setting']['value']['displayName'] = 'v3-' + configuration + '-' + role
            policies[policy['name']] = policy
        profile['custom_detectors'] = []
        if configuration != 'standard':
            detector = {'name': 'policies/v3-' + configuration + '-regex', 'customer': 'customers/CSYNTHETIC',
                        'policyQuery': copy.deepcopy(f.query), 'setting': {
                            'type': 'settings/detector.regular_expression', 'value': {
                                'displayName': 'synthetic-regex',
                                # 内部フィールド名は通信をしない合成応答用。API作成仕様の主張ではない。
                                'regularExpression': {'syntheticPattern': combined_regex(kind)}}}}
            policies[detector['name']] = detector
            profile['custom_detectors'].append({'id': detector['name'], 'kind': 'regular_expression',
                                                'sha256': object_digest(detector)})
        if configuration != 'standard' and ITEMS[kind].get('word_list'):
            detector = {'name': 'policies/v3-' + configuration + '-words', 'customer': 'customers/CSYNTHETIC',
                        'policyQuery': copy.deepcopy(f.query), 'setting': {
                            'type': 'settings/detector.word_list', 'value': {
                                'wordList': {'words': ITEMS[kind]['word_list']}}}}
            policies[detector['name']] = detector
            profile['custom_detectors'].append({'id': detector['name'], 'kind': 'word_list',
                                                'sha256': object_digest(detector)})
        conditions = audit.expected_conditions(profile, policies)
        for role, reference in profile['roles'].items():
            policy = policies[reference['id']]
            policy['setting']['value']['condition'] = {'contentCondition': conditions[role]}
            reference['policy_sha256'] = object_digest(policy)
        profiles.append(profile)
    f.profiles = profiles
    f.manifest.update(benchmark='v3-extended', profiles=profiles)
    f.policy_before['policies'] = copy.deepcopy(list(policies.values()))
    f.policy_after['policies'] = copy.deepcopy(list(policies.values()))
    f.flush()
    return f


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.f = fixture(self.tmp.name)

    def imported(self):
        self.f.flush()
        return audit.import_audit(self.f.dataset, self.f.raw_path, self.f.manifest_path, self.f.bundle_path)

    def score(self):
        self.imported()
        return audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)['by_threshold']['POSSIBLE']

    def test_raw_to_score_keeps_three_configurations_separate(self):
        self.f.add('positive', profile=0)
        self.f.negative(profile=1)
        result = self.score()
        self.assertEqual(result['evaluation_by_item']['standard']['email']['counts']['TP'], 1)
        self.assertEqual(result['evaluation_by_item']['custom']['email']['counts']['FN'], 1)
        self.assertEqual(result['evaluation_by_item']['combined']['email']['counts']['pending'], 3)
        self.assertEqual(len(result['matrix']), 3 * 31 * 3)
        self.assertEqual(result['evaluation_by_item']['standard']['assets']['counts']['unsupported'], 3)

    def test_complete_rule_column_produces_correct_metrics(self):
        for profile in range(3):
            for case in ('basic', 'adversarial'):
                self.f.add('positive', case=case, profile=profile)
            self.f.negative(case='negative', profile=profile)
        result = self.score()
        for configuration in audit.CONFIGURATIONS:
            metric = result['evaluation_by_item'][configuration]['email']['primary_metrics']
            self.assertEqual(metric['recall'], 1)
            self.assertEqual(metric['accuracy'], 1)
            self.assertEqual(metric['f1'], 1)

    def test_controls_without_negative_remain_unresolved(self):
        self.f.add('head', profile=1)
        self.f.add('tail', profile=1)
        result = self.score()
        metric = result['evaluation_by_item']['custom']['email']
        self.assertEqual(metric['counts']['conditional_not_detected'], 1)
        self.assertEqual(metric['counts']['FN'], 0)
        self.assertIsNone(metric['primary_metrics'])

    def test_configuration_relabel_without_rule_change_is_rejected(self):
        self.f.profiles[0]['configuration'] = 'combined'
        with self.assertRaises(ValueError):
            self.imported()

    def test_changed_regex_even_with_recomputed_reference_hash_is_rejected(self):
        reference = self.f.profiles[1]['custom_detectors'][0]
        for saved in (self.f.policy_before, self.f.policy_after):
            detector = next(p for p in saved['policies'] if p['name'] == reference['id'])
            detector['setting']['value']['regularExpression'] = {'syntheticPattern': 'wrong'}
        reference['sha256'] = object_digest(detector)
        with self.assertRaisesRegex(ValueError, '正規表現'):
            self.imported()

    def test_regex_struct_flags_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            audit.regex_string({'pattern': 'x', 'flag': True})
        self.assertEqual(audit.regex_string({'nested': {'pattern': 'x'}}), 'x')

    def test_detector_scope_mismatch_even_with_new_hash_is_rejected(self):
        reference = self.f.profiles[1]['custom_detectors'][0]
        for saved in (self.f.policy_before, self.f.policy_after):
            detector = next(p for p in saved['policies'] if p['name'] == reference['id'])
            detector['policyQuery'] = {'query': 'different'}
        reference['sha256'] = object_digest(detector)
        with self.assertRaises(ValueError):
            self.imported()

    def test_manual_observation_edit_is_rejected(self):
        self.f.add('positive')
        self.imported()
        bundle = json.loads(self.f.bundle_path.read_text())
        bundle['rows'][0]['status'] = 'not_detected'
        write(self.f.bundle_path, bundle)
        with self.assertRaises(ValueError):
            audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)

    def test_truth_and_source_changes_are_rejected(self):
        self.imported()
        original = (self.f.dataset / 'ground_truth.json').read_bytes()
        write(self.f.dataset / 'ground_truth.json', list(reversed(self.f.truth)))
        with self.assertRaises(ValueError):
            audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)
        (self.f.dataset / 'ground_truth.json').write_bytes(original)
        (self.f.dataset / 'drive_upload/basic.txt').write_text('changed')
        with self.assertRaises(ValueError):
            audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)

    def test_missing_scope_and_old_version_remain_pending(self):
        self.f.scope['bindings'] = []
        self.f.add('positive', profile=1)
        result = self.score()
        self.assertEqual(result['evaluation_by_item']['custom']['email']['counts']['TP'], 0)
        self.f.scope['bindings'] = []  # 所有範囲なしは検知の証明にしない。

    def test_wordlist_is_required_and_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = fixture(tmp, kind='medical_history')
            f.add('positive', profile=1)
            f.flush()
            audit.import_audit(f.dataset, f.raw_path, f.manifest_path, f.bundle_path)
            result = audit.score(f.dataset, f.bundle_path, f.report_path)
            self.assertEqual(result['by_threshold']['POSSIBLE']['evaluation_by_item']['custom']['medical_history']['counts']['TP'], 1)
            f.profiles[1]['custom_detectors'] = f.profiles[1]['custom_detectors'][:1]
            f.flush()
            with self.assertRaises(ValueError):
                audit.import_audit(f.dataset, f.raw_path, f.manifest_path, f.bundle_path)

    def test_root_cli_import_and_score_dispatch_to_v3(self):
        from benchmark import main
        self.f.add('positive', profile=2)
        self.f.flush()
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            main(['import-audit', '--dataset', str(self.f.dataset), '--raw', str(self.f.raw_path),
                  '--manifest', str(self.f.manifest_path), '--output', str(self.f.bundle_path)])
            main(['score', '--dataset', str(self.f.dataset), '--observations', str(self.f.bundle_path),
                  '--report', str(self.f.report_path)])
        self.assertEqual(json.loads(self.f.report_path.read_text())['benchmark'], 'v3-extended')

    def test_separate_configuration_runs_can_be_combined_without_duplicate_profiles(self):
        for index in range(3):
            self.f.add('positive', profile=index)
        profiles = self.f.profiles
        paths = []
        for index, profile in enumerate(profiles):
            self.f.manifest['profiles'] = [profile]
            self.f.flush()
            manifest = Path(self.tmp.name) / f'manifest-{index}.json'
            manifest.write_bytes(self.f.manifest_path.read_bytes())
            output = Path(self.tmp.name) / f'observations-{index}.json'
            audit.import_audit(self.f.dataset, self.f.raw_path, manifest, output)
            paths.append(output)
        result = audit.score(self.f.dataset, paths, self.f.report_path)
        for configuration in audit.CONFIGURATIONS:
            self.assertEqual(result['by_threshold']['POSSIBLE']['evaluation_by_item'][configuration]['email']['counts']['TP'], 1)
        with self.assertRaisesRegex(ValueError, '重複'):
            audit.score(self.f.dataset, [paths[0], paths[0]], self.f.report_path)

    def test_legacy_manifest_cannot_claim_configuration(self):
        self.f.manifest.pop('benchmark')
        with self.assertRaises(ValueError):
            self.imported()


if __name__ == '__main__':
    unittest.main()
