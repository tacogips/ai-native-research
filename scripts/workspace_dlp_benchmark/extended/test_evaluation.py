"""v3集計の母数・構成分離を独立した小さい正解表で確認する。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
import evaluation
from catalog import ITEMS


def truth():
    rows = []
    for case, value in [('positive', 1), ('negative', 0), ('unknown', None)]:
        matrix = dict.fromkeys(ITEMS, 0)
        matrix['individual'] = value
        rows.append({'case_id': case, 'item': 'individual', 'group': 'G1', 'split': '評価',
                     'expected': value, 'expected_by_item': matrix, 'sha256': 'synthetic-hash'})
    return rows


def observed(case, item='individual', configuration='custom', status='detected'):
    return {'case_id': case, 'item': item, 'configuration': configuration, 'status': status}


class EvaluationTest(unittest.TestCase):
    def test_complete_matrix_has_all_items_and_three_configurations(self):
        result = evaluation.reduce_matrix(truth(), [])
        self.assertEqual(len(result['matrix']), 3 * 31 * 3)
        self.assertEqual(len(result['group_matrix']), 3 * 7 * 3)
        self.assertTrue(all(row['status'] == 'pending' for row in result['matrix']))

    def test_configuration_results_do_not_leak(self):
        result = evaluation.reduce_matrix(truth(), [observed('positive')])
        self.assertEqual(result['evaluation_by_item']['custom']['individual']['counts']['TP'], 1)
        self.assertEqual(result['evaluation_by_item']['standard']['individual']['counts']['TP'], 0)
        self.assertEqual(result['evaluation_by_item']['combined']['individual']['counts']['TP'], 0)

    def test_unknown_truth_excluded_but_pending_prevents_point_estimate(self):
        partial = evaluation.reduce_matrix(truth(), [observed('positive')])
        self.assertIsNone(partial['evaluation_by_item']['custom']['individual']['primary_metrics'])
        complete = evaluation.reduce_matrix(truth(), [observed('positive'), observed('negative', status='not_detected')])
        metric = complete['evaluation_by_item']['custom']['individual']
        self.assertEqual(metric['primary_metrics']['recall'], 1)
        self.assertEqual(metric['primary_metrics']['accuracy'], 1)
        self.assertEqual(metric['counts']['unscorable'], 1)

    def test_fp_and_fn_counted_against_all_items(self):
        result = evaluation.reduce_matrix(truth(), [observed('positive', status='not_detected'),
                                                   observed('negative'), observed('negative', item='license')])
        item = result['evaluation_by_item']['custom']['individual']
        self.assertEqual(item['counts']['FN'], 1)
        self.assertEqual(item['counts']['FP'], 1)
        self.assertEqual(item['primary_metrics']['f1'], 0)
        self.assertEqual(result['evaluation_by_item']['custom']['license']['counts']['FP'], 1)

    def test_failures_and_unsupported_never_negative(self):
        for state in ('error', 'timeout', 'unsupported', 'stale', 'conditional_not_detected'):
            with self.subTest(state=state):
                result = evaluation.reduce_matrix(truth(), [observed('positive', status=state)])
                metric = result['evaluation_by_item']['custom']['individual']
                self.assertEqual(metric['counts']['FN'], 0)
                self.assertIsNone(metric['primary_metrics'])

    def test_group_or_requires_every_negative_but_one_detection_suffices(self):
        self.assertEqual(evaluation.union_state(['not_detected', 'unsupported']), 'unsupported')
        self.assertEqual(evaluation.union_state(['not_detected', 'pending']), 'pending')
        self.assertEqual(evaluation.union_state(['detected', 'pending']), 'detected')
        self.assertEqual(evaluation.union_state(['not_detected', 'not_detected']), 'not_detected')
        with self.assertRaises(ValueError):
            evaluation.union_state([])
        with self.assertRaises(ValueError):
            evaluation.union_state(['arbitrary'])

    def test_group_truth_positive_wins_unknown_otherwise_unknown(self):
        row = truth()[2]
        self.assertIsNone(evaluation.expected_group(row, 'G1'))
        row['expected_by_item']['license'] = 1
        self.assertEqual(evaluation.expected_group(row, 'G1'), 1)

    def test_development_excluded_from_primary(self):
        rows = truth()
        rows[0]['split'] = '開発'
        result = evaluation.reduce_matrix(rows, [observed('positive')])
        self.assertEqual(result['all_by_item']['custom']['individual']['counts']['TP'], 1)
        self.assertEqual(result['evaluation_by_item']['custom']['individual']['counts']['TP'], 0)

    def test_duplicate_and_unknown_observation_rejected(self):
        for rows in ([observed('positive')] * 2, [observed('missing')],
                     [observed('positive', item='unknown')], [observed('positive', status='absent')]):
            with self.assertRaises(ValueError):
                evaluation.reduce_matrix(truth(), rows)

    def test_incomplete_or_invalid_truth_rejected(self):
        for value in ('bad', 2, True):
            rows = truth()
            rows[0]['expected_by_item']['individual'] = value
            with self.assertRaises(ValueError):
                evaluation.reduce_matrix(rows, [])
        rows = truth()
        del rows[0]['expected_by_item']['license']
        with self.assertRaises(ValueError):
            evaluation.reduce_matrix(rows, [])

    def test_artifact_fingerprint_mismatch_rejected(self):
        row = dict(observed('positive'), artifact_sha256='changed')
        with self.assertRaises(ValueError):
            evaluation.reduce_matrix(truth(), [row])

    def test_generated_dataset_loader_checks_file_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'dataset'
            build.make(root)
            rows, _ = evaluation.load_truth(root)
            self.assertEqual(len(rows), 385)
            (root / 'drive_upload' / rows[0]['file']).write_text('changed')
            with self.assertRaises(ValueError):
                evaluation.load_truth(root)


if __name__ == '__main__':
    unittest.main()
