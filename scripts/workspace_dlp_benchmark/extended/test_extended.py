"""v3の生成と独自検知器定義の検査。google-re2がない環境では正規表現の検査を飛ばす。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
from catalog import GROUPS, ITEMS, LIMITS  # noqa: E402


class ExtendedTest(unittest.TestCase):
    def test_accuracy_and_null_truth(self):
        result = build._counts([(1, True), (1, False), (0, True), (0, False), (None, True)])
        self.assertEqual(result['accuracy'], 0.5)
        self.assertEqual(result['recall'], 0.5)
        self.assertEqual(result['f1'], 0.5)
        self.assertEqual(result['保留'], 1)
        self.assertIsNone(build._counts([(None, True)])['accuracy'])

    def test_limits(self):
        problems, detectors = build.check_limits()
        self.assertEqual(problems, [])
        self.assertLessEqual(detectors, LIMITS['custom_detectors_in_rules'])

    def test_regex_compiles_in_re2(self):
        try:
            import re2
        except ImportError:
            self.skipTest('google-re2なし')
        for item in ITEMS:
            re2.compile(build.combined_regex(item))

    def test_generation_is_deterministic_and_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = build.make(Path(tmp) / 'a')
            b = build.make(Path(tmp) / 'b')
            self.assertEqual([r['sha256'] for r in a], [r['sha256'] for r in b])
            self.assertEqual({r['item'] for r in a}, set(ITEMS))
            self.assertTrue({r['group'] for r in a} <= set(GROUPS))
            for row in a:
                self.assertEqual(row['expected_by_item'][row['item']], row['expected'])
                text = (Path(tmp) / 'a' / 'drive_upload' / row['file']).read_text(encoding='utf-8')
                self.assertIn(row['scan_control']['head_token'], text)
            ids = [r['case_id'] for r in a]
            self.assertEqual(len(ids), len(set(ids)))

    def test_truth_r2_records_cross_category_corrections(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = build.make(Path(tmp) / 'dataset')
            by_case = {row['case_id']: row for row in rows}
            self.assertEqual(by_case['medical_history-family']['expected_by_item']['family'], 1)
            disability = [row for row in rows if row['item'] == 'disability' and row['expected'] == 1]
            self.assertEqual(len(disability), 9)
            self.assertTrue(all(row['expected_by_item']['medical_history'] is None for row in disability))
            self.assertTrue(all(row['truth_revision'] == 'r2' for row in rows))

    def test_api_label_plan_omits_multi_value_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = build.label_plan(Path(tmp) / 'plan.json')
            requests = plan['drive_labels_api_create_plan']
            self.assertEqual({request['group'] for request in requests}, set(GROUPS) - {'G8'})
            for request in requests:
                self.assertEqual(request['method'], 'labels.create')
                self.assertEqual(request['body']['labelType'], 'ADMIN')
                field = request['body']['fields'][0]
                self.assertNotIn('listOptions', field['selectionOptions'])
                self.assertEqual([choice['properties']['displayName'] for choice in field['selectionOptions']['choices']],
                                 ['確度高', '確度中'])
                self.assertNotIn('id', field)
                self.assertTrue(request['parameters']['useAdminAccess'])

    def test_label_plan_uses_single_select_per_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = build.label_plan(Path(tmp) / 'plan.json')
            for rule in plan['rules']:
                self.assertIn(rule['action']['value'], ('確度高', '確度中'))
            self.assertEqual(json.loads((Path(tmp) / 'plan.json').read_text())['rules'], plan['rules'])


if __name__ == '__main__':
    unittest.main()
