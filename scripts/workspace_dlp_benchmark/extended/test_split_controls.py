"""語句対照の分割を合成した設定・原票だけで確認する。"""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import audit
from common import object_digest
from controls import control_expression, control_references
from test_audit import fixture


def split_fixture(root):
    f = fixture(root)
    policies = {p['name']: p for p in f.policy_before['policies']}
    references = {}
    for edge in ('head', 'tail'):
        original = policies[f.profiles[0]['roles'][edge]['detector_id']]
        words = original['setting']['value']['wordList']['words']
        references[edge] = []
        for index, chunk in enumerate((words[:1], words[1:])):
            detector = copy.deepcopy(original)
            detector['name'] = f'policies/synthetic-split-{edge}-{index}'
            detector['setting']['value']['wordList'] = {'words': chunk}
            policies[detector['name']] = detector
            references[edge].append({'id': detector['name'], 'sha256': object_digest(detector)})
    for profile in f.profiles:
        for edge in ('head', 'tail'):
            role = profile['roles'][edge]
            role.pop('detector_id')
            role.pop('detector_sha256')
            role['control_detectors'] = copy.deepcopy(references[edge])
        conditions = audit.expected_conditions(profile, policies)
        for role, reference in profile['roles'].items():
            policy = policies[reference['id']]
            policy['setting']['value']['condition'] = {'contentCondition': conditions[role]}
            reference['policy_sha256'] = object_digest(policy)
    f.policy_before['policies'] = copy.deepcopy(list(policies.values()))
    f.policy_after['policies'] = copy.deepcopy(list(policies.values()))
    f.flush()
    return f


class SplitControlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.f = split_fixture(self.tmp.name)

    def imported(self):
        self.f.flush()
        return audit.import_audit(self.f.dataset, self.f.raw_path, self.f.manifest_path, self.f.bundle_path)

    def edit_detector(self, edge, index, mutate, resign=True):
        reference = self.f.profiles[0]['roles'][edge]['control_detectors'][index]
        for snapshot in (self.f.policy_before, self.f.policy_after):
            detector = next(p for p in snapshot['policies'] if p['name'] == reference['id'])
            mutate(detector)
        if resign:
            for profile in self.f.profiles:
                profile['roles'][edge]['control_detectors'][index]['sha256'] = object_digest(detector)

    def test_second_split_contains_marker_and_negative_is_accepted(self):
        self.f.negative(case='adversarial', profile=0)
        bundle = self.imported()
        row = next(r for r in bundle['rows'] if r['case_id'] == 'adversarial' and r['configuration'] == 'standard')
        self.assertEqual(row['status'], 'not_detected')
        result = audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)
        self.assertEqual(result['by_threshold']['POSSIBLE']['evaluation_by_item']['standard']['email']['counts']['FN'], 1)

    def test_or_condition_gates_both_positive_and_negative(self):
        policies = {p['name']: p for p in self.f.policy_before['policies']}
        conditions = audit.expected_conditions(self.f.profiles[0], policies)
        for edge in ('head', 'tail'):
            self.assertIn(' || ', conditions[edge])
            self.assertIn('(' + conditions[edge] + ')', conditions['positive'])
            self.assertIn('(' + conditions[edge] + ')', conditions['negative'])
        self.assertIn('&& !(', conditions['negative'])

    def test_old_single_format_and_single_element_array_have_identical_expression(self):
        f = fixture(self.tmp.name)
        role = f.profiles[0]['roles']['head']
        multiple = {k: v for k, v in role.items() if k not in ('detector_id', 'detector_sha256')}
        multiple['control_detectors'] = [{'id': role['detector_id'], 'sha256': role['detector_sha256']}]
        self.assertEqual(control_expression(role), control_expression(multiple))
        f.add('positive')
        f.flush()
        audit.import_audit(f.dataset, f.raw_path, f.manifest_path, f.bundle_path)

    def test_head_can_be_split_while_tail_uses_legacy_single_form(self):
        policies = {p['name']: p for p in self.f.policy_before['policies']}
        original_tail = policies['policies/synthetic-tail']
        for profile in self.f.profiles:
            role = profile['roles']['tail']
            role.pop('control_detectors')
            role.update(detector_id=original_tail['name'], detector_sha256=object_digest(original_tail))
            conditions = audit.expected_conditions(profile, policies)
            for edge, reference in profile['roles'].items():
                for snapshot in (self.f.policy_before, self.f.policy_after):
                    policy = next(p for p in snapshot['policies'] if p['name'] == reference['id'])
                    policy['setting']['value']['condition'] = {'contentCondition': conditions[edge]}
                reference['policy_sha256'] = object_digest(policy)
        self.f.negative(case='adversarial', profile=0)
        bundle = self.imported()
        row = next(r for r in bundle['rows'] if r['case_id'] == 'adversarial' and r['configuration'] == 'standard')
        self.assertEqual(row['status'], 'not_detected')

    def test_regex_control_is_not_accepted_as_a_split_word_list(self):
        role = dict(self.f.profiles[0]['roles']['head'], control_kind='regular_expression')
        with self.assertRaisesRegex(ValueError, '語句一覧'):
            control_references(role)

    def test_old_and_new_formats_cannot_be_combined(self):
        for old_key, value in (('detector_id', 'policies/synthetic-old'), ('detector_sha256', '0' * 64)):
            role = copy.deepcopy(self.f.profiles[0]['roles']['head'])
            role[old_key] = value
            with self.assertRaisesRegex(ValueError, '併用'):
                control_references(role)

    def test_malformed_references_are_rejected(self):
        role = self.f.profiles[0]['roles']['head']
        one = role['control_detectors'][0]
        for values in ([], None, [one, one], [{'id': one['id']}],
                       [{'id': "policies/x')", 'sha256': '0' * 64}],
                       [{'id': one['id'], 'sha256': 'invalid'}]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                control_references(dict(role, control_detectors=values))

    def test_head_and_tail_id_sets_must_not_intersect(self):
        self.f.profiles[0]['roles']['tail']['control_detectors'][1] = copy.deepcopy(
            self.f.profiles[0]['roles']['head']['control_detectors'][0])
        with self.assertRaisesRegex(ValueError, '重複'):
            self.imported()

    def test_missing_definition_and_hash_change_are_rejected(self):
        self.edit_detector('head', 0, lambda p: p['setting']['value'].update(description='changed'), resign=False)
        with self.assertRaisesRegex(ValueError, '全文'):
            self.imported()
        self.f = split_fixture(Path(self.tmp.name) / 'other')
        reference = self.f.profiles[0]['roles']['head']['control_detectors'][0]
        for snapshot in (self.f.policy_before, self.f.policy_after):
            snapshot['policies'] = [p for p in snapshot['policies'] if p['name'] != reference['id']]
        with self.assertRaisesRegex(ValueError, '全文'):
            self.imported()

    def test_resigned_different_customer_or_scope_or_type_are_rejected(self):
        edits = [lambda p: p.update(customer='customers/COTHER'),
                 lambda p: p.update(policyQuery={'query': 'different'}),
                 lambda p: p['setting'].update(type='settings/detector.regular_expression')]
        for index, edit in enumerate(edits):
            self.f = split_fixture(Path(self.tmp.name) / f'case-{index}')
            self.edit_detector('head', 0, edit)
            with self.assertRaisesRegex(ValueError, '全文'):
                self.imported()

    def test_duplicate_words_across_splits_are_rejected_including_case_or_symbols(self):
        # 参照IDで正しい先頭分割を探し、リストの物理順序に依存しない。
        ident = self.f.profiles[0]['roles']['head']['control_detectors'][0]['id']
        first = next(p for p in self.f.policy_before['policies'] if p['name'] == ident)['setting']['value']['wordList']['words'][0]
        for index, duplicate in enumerate((first, first.lower(), first[:3] + '-' + first[3:])):
            self.f = split_fixture(Path(self.tmp.name) / f'duplicate-{index}')
            self.edit_detector('head', 1, lambda p, word=duplicate: p['setting']['value']['wordList']['words'].append(word))
            with self.assertRaisesRegex(ValueError, '重複'):
                self.imported()

    def test_each_file_marker_must_belong_to_its_own_edge_union(self):
        self.edit_detector('head', 0, lambda p: p['setting']['value'].update(wordList={'words': ['SYNTHETICUNUSED']}))
        with self.assertRaisesRegex(ValueError, '対照語'):
            self.imported()

    def test_word_count_bytes_and_unknown_definition_are_rejected(self):
        oversized_count = [f'SYNTHETICWORD{i:04}' for i in range(951)]
        oversized_bytes = ['あ' * 35 + f'{i:05}' for i in range(600)]
        candidates = [{'words': oversized_count}, {'words': oversized_bytes}, {'words': []},
                      {'words': 'not-a-list'}, {'words': [None]}, {'words': ['A']},
                      {'words': ['SYNTHETIC'], 'unknown': True}]
        for index, word_list in enumerate(candidates):
            self.f = split_fixture(Path(self.tmp.name) / f'words-{index}')
            self.edit_detector('head', 0, lambda p, value=word_list: p['setting']['value'].update(wordList=value))
            with self.assertRaises(ValueError):
                self.imported()

    def test_one_control_without_other_edge_does_not_prove_negative(self):
        self.f.add('head', profile=0)
        self.f.add('negative', profile=0)
        bundle = self.imported()
        row = next(r for r in bundle['rows'] if r['case_id'] == 'basic' and r['configuration'] == 'standard')
        self.assertEqual(row['status'], 'pending')


if __name__ == '__main__':
    unittest.main()
