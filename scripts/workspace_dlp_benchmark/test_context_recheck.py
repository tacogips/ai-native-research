import unittest
from collections import Counter
from itertools import groupby

import context_recheck as benchmark
from dataset import individual_valid, luhn_valid


class ContextRecheckTests(unittest.TestCase):
    def test_context_pairs_keep_same_literal_and_distinct_truth(self):
        records = benchmark.make_cases()
        self.assertEqual(len(records), 8768)
        self.assertEqual(len({row['case_id'] for row, _ in records}), len(records))
        self.assertEqual(len({row['scan_control']['head_token'] for row, _ in records}), len(records))
        groups = sorted(records, key=lambda pair: (pair[0]['item'], pair[0]['family']))
        for (item, family), group in groupby(groups, key=lambda pair: (pair[0]['item'], pair[0]['family'])):
            scenarios = {row['scenario']: (row, text.split('\n\n')[1]) for row, text in group}
            if item in benchmark.SOURCES:
                bare, value = scenarios['bare']
                other, substitute = scenarios['unrelated']
                self.assertIn(value, substitute)
                self.assertEqual((bare['role_truth'], other['role_truth']), (1, 0))
                self.assertEqual(bare['format_truth'], other['format_truth'])
                self.assertNotIn(item, bare['file'])
            else:
                filled = scenarios['heading'][1].splitlines()[-1]
                reference, body = scenarios['reference']
                # 記録用コードや人物は変えても、同じ病名・所見の文言を含む。
                self.assertIn(filled.split('\t')[-1].rsplit('　', 1)[-1], body)
                self.assertEqual(reference['role_truth'], 0)
                self.assertEqual(reference['format_truth'], None)
        self.assertEqual(Counter(row['scenario'] for row, _ in records)['internationalized'], 64)

    def test_prefixes_cannot_identify_contact_numbers_by_themselves(self):
        rows = {(row['family'], row['scenario']): (row, text.split('\n\n')[1])
                for row, text in benchmark.make_cases() if row['item'] == 'phone'}
        for family in range(benchmark.FAMILIES):
            contact, left = rows[family, 'prefix_contact']
            employee, right = rows[family, 'prefix_employee']
            self.assertEqual(left.split('：')[1], right.split('：')[1])
            self.assertEqual(employee['role_truth'], 0)
            self.assertEqual(employee['employee_truth'], 1)
            self.assertEqual(contact['employee_truth'], 0)
            self.assertEqual(contact['role_truth'], int(contact['number_prefix'] != '1234'))

    def test_individual_number_cross_truth_preserves_checksum_requirement(self):
        for row, body in benchmark.make_cases():
            if row['item'] != 'license' or row['scenario'] != 'competing_bare':
                continue
            value = body.split('\n\n')[1]
            self.assertEqual(row['cross_role_truth']['individual'], int(individual_valid(value)))

    def test_checksum_pairs_change_validity_without_changing_width(self):
        for kind, valid in (
            ('individual', individual_valid), ('card', luhn_valid),
            ('iban', lambda v: benchmark.iban_remainder(v) == 1),
        ):
            for family in range(benchmark.FAMILIES):
                good, near, _ = benchmark.variants(kind, family)
                self.assertEqual(len(good), len(near))
                self.assertTrue(valid(good))
                self.assertFalse(valid(near))

    def test_rule_create_bodies_resolve_only_the_replay_scope(self):
        import json
        import recheck_rule_payloads as payloads

        plan = json.loads(payloads.PLAN.read_text(encoding='utf-8'))
        parameters = ('customers/CExample', 'orgUnits/Example', 'test-run', 'DLPVERIFYABCDEFGH')
        detectors = payloads.materialize(plan, 'detectors', *parameters, {})
        resources = {row['key']: f'policies/Example-{i}' for i, row in enumerate(detectors)}
        with self.assertRaisesRegex(ValueError, 'リソース対応が不足'):
            payloads.materialize(plan, 'rules', *parameters, {})
        rules = payloads.materialize(plan, 'rules', *parameters, resources)
        self.assertEqual(len(plan['rules_and_detectors']), 69)
        self.assertEqual(len(detectors) + len(rules), 62)
        self.assertEqual(sum(
            1 for row in rules if 'matches_regex_detector' in row['body']['setting']['value']['condition']['contentCondition']
        ), 14)
        for row in rules:
            value = row['body']['setting']['value']
            actions = value['action']
            self.assertEqual(actions['driveAction'], {'auditOnly': {}})
            self.assertEqual({key: action for key, action in actions.items() if key != 'driveAction'},
                             {'alertCenterAction': {}} if 'alertCenterAction' in actions else {})
            self.assertFalse(payloads.PLACEHOLDER.search(json.dumps(row['body'])))

    def test_properties_separate_file_extension_and_mime_type(self):
        import hashlib
        import tempfile
        from pathlib import Path
        from recheck_property_fixtures import make

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'fixtures'
            rows = make(output, 'DLPVERIFYABCDEFGH')
            self.assertEqual(len(rows), 16)
            cases = {(row['item'], row['scenario']): row for row in rows}
            self.assertEqual(cases['extension', 'mismatch_dat']['condition_truth'], 0)
            self.assertEqual(cases['mime', 'mismatch_dat']['condition_truth'], 1)
            for row in rows:
                content = (output / row['file']).read_bytes()
                self.assertEqual(content.startswith(b'%PDF-'), row['upload_mime_type'] == 'application/pdf')
                self.assertEqual(hashlib.sha256(content).hexdigest(), row['sha256'])
