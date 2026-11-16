"""二値判定の数え方・未確定の上下限・観測証拠の再導出を独立に検算する。"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import common
import scoring
from test_support import AuditFixture, write


def pair(expected, status):
    return ({'expected': expected}, {'status': status})


class MetricsTests(unittest.TestCase):
    def test_independent_confusion_matrix_example(self):
        rows = ([pair(1, 'detected')]*40 + [pair(0, 'detected')]*5
                + [pair(1, 'not_detected')]*10 + [pair(0, 'not_detected')]*45)
        result = scoring.metrics(rows)
        self.assertEqual([result['counts'][k] for k in ['TP', 'FP', 'FN', 'TN']], [40, 5, 10, 45])
        self.assertAlmostEqual(result['precision'], 40/45)
        self.assertAlmostEqual(result['recall'], .8)
        self.assertAlmostEqual(result['accuracy'], .85)
        self.assertAlmostEqual(result['f1'], 80/95)
        self.assertAlmostEqual(result['false_positive_rate'], .1)
        self.assertEqual(result['coverage'], 1)

    def test_pending_does_not_become_false_negative_or_true_negative(self):
        result = scoring.metrics([pair(1, 'detected'), pair(0, 'not_detected'), pair(1, 'pending'), pair(0, 'timeout')])
        self.assertEqual([result['counts'][k] for k in ['TP', 'FP', 'FN', 'TN']], [1, 0, 0, 1])
        self.assertEqual(result['coverage'], .5)
        self.assertIsNone(result['full_cohort_point_metrics'])
        self.assertIsNone(result['accuracy'])
        self.assertEqual(result['adjudicated_subset_metrics']['accuracy'], 1)
        self.assertEqual(result['full_cohort_bounds']['recall'], [.5, 1])
        self.assertEqual(result['full_cohort_bounds']['accuracy'], [.5, 1])
        self.assertEqual(result['full_cohort_bounds']['f1'], [.5, 1])

    def test_conditional_control_only_state_is_not_point_negative(self):
        result = scoring.metrics([pair(1, 'conditional_not_detected')])
        self.assertEqual(result['evaluated'], 0)
        self.assertEqual(result['counts']['FN'], 0)
        self.assertIsNone(result['full_cohort_point_metrics'])
        self.assertEqual(result['full_cohort_bounds']['recall'], [0, 1])

    def test_no_positive_truth_does_not_yield_recall_one(self):
        result = scoring.metrics([pair(0, 'not_detected')])
        self.assertIsNone(result['recall']);self.assertIsNone(result['precision']);self.assertIsNone(result['f1'])
        self.assertEqual(result['accuracy'], 1)

    def test_unknown_truth_does_not_support_full_cohort_point_or_bounds(self):
        result = scoring.metrics([pair(1, 'detected'), pair(None, 'detected')])
        self.assertEqual(result['counts']['unscorable'], 1)
        self.assertEqual(result['eligible'], 1)
        self.assertIsNone(result['full_cohort_point_metrics'])
        self.assertIsNone(result['f1'])
        self.assertIsNone(result['full_cohort_bounds'])
        self.assertEqual(result['eligible_subset_point_metrics']['f1'], 1)

    def test_all_unknown_truth_is_unscorable(self):
        result = scoring.metrics([pair(None, 'not_detected')])
        self.assertEqual(result['eligible'], 0)
        self.assertEqual(result['evaluated'], 0)
        self.assertIsNone(result['coverage'])
        self.assertIsNone(result['full_cohort_point_metrics'])


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f = AuditFixture(self.temp.name)

    def score(self, axis='content'):
        return scoring.score(self.f.dataset, self.f.bundle_path, self.f.report_path, axis=axis)

    def test_complete_kind_by_threshold_matrix_and_separate_tracks(self):
        self.f.populate();self.f.imported();result = self.score()
        self.assertEqual(result['unique_files'], 3)
        self.assertEqual(result['source_families'], 2)
        self.assertEqual(len(result['matrix']), 12)
        self.assertEqual(set(result['primary']), {'email:POSSIBLE', 'email:LIKELY', 'card:POSSIBLE', 'card:LIKELY'})
        for threshold in ['POSSIBLE', 'LIKELY']:
            self.assertEqual(result['primary']['email:'+threshold]['total'], 2)
            self.assertEqual(result['primary']['email:'+threshold]['counts']['TP'], 1)
            self.assertEqual(result['primary']['email:'+threshold]['counts']['TN'], 1)
            self.assertEqual(result['groups']['adversarial:email:'+threshold]['total'], 1)
            self.assertEqual(result['groups']['adversarial:email:'+threshold]['counts']['TP'], 1)
            self.assertEqual(result['groups']['all:email:'+threshold]['counts']['TP'], 2)
            self.assertIsNone(result['primary']['card:'+threshold]['recall'])

    def test_cli_import_and_score_use_same_provenance_checks(self):
        self.f.populate();self.f.flush();script = Path(__file__).with_name('benchmark.py')
        imported = subprocess.run([sys.executable, str(script), 'import-audit', '--dataset', str(self.f.dataset),
            '--raw', str(self.f.raw_path), '--manifest', str(self.f.manifest_path), '--output', str(self.f.bundle_path)],
            capture_output=True, text=True, timeout=20)
        self.assertEqual(imported.returncode, 0, imported.stderr)
        scored = subprocess.run([sys.executable, str(script), 'score', '--dataset', str(self.f.dataset),
            '--observations', str(self.f.bundle_path), '--report', str(self.f.report_path)],
            capture_output=True, text=True, timeout=20)
        self.assertEqual(scored.returncode, 0, scored.stderr)
        self.assertEqual(json.loads(scored.stdout)['email:POSSIBLE']['f1'], 1)
        result = json.loads(self.f.report_path.read_text())
        self.assertEqual(result['source_families'], 2);self.assertEqual(len(result['matrix']), 12)

    def test_other_kind_detection_is_false_positive_not_target_success(self):
        self.f.add('positive', profile=2);self.f.imported();result = self.score()
        self.assertEqual(result['primary']['card:POSSIBLE']['counts']['FP'], 1)
        self.assertEqual(result['primary']['email:POSSIBLE']['counts']['TP'], 0)
        self.assertEqual(result['primary']['email:POSSIBLE']['counts']['FN'], 0)
        self.assertIsNone(result['primary']['email:POSSIBLE']['full_cohort_point_metrics'])

    def test_protection_truth_is_separate_from_type_presence(self):
        self.f.truth[0]['protection_expected_by_kind']['email'] = 0
        self.f.populate();self.f.imported()
        content = self.score();protection = self.score('protection')
        self.assertEqual(content['primary']['email:POSSIBLE']['counts']['TP'], 1)
        self.assertEqual(protection['primary']['email:POSSIBLE']['counts']['FP'], 1)

    def test_null_number_truth_is_unscorable(self):
        self.f.populate();self.f.imported();result = self.score('valid_number')
        metric = result['primary']['email:POSSIBLE']
        self.assertEqual(metric['counts']['unscorable'], 2)
        self.assertEqual(metric['evaluated'], 0)
        self.assertIsNone(metric['full_cohort_point_metrics'])

    def test_hand_edited_status_is_rejected(self):
        self.f.populate();bundle = self.f.imported()
        bundle['rows'][0]['status'] = 'not_detected';write(self.f.bundle_path, bundle)
        with self.assertRaisesRegex(ValueError, '導出'):self.score()

    def test_hand_edited_profile_is_rejected(self):
        self.f.populate();bundle = self.f.imported()
        bundle['profiles'][0]['threshold'] = 'UNLIKELY';write(self.f.bundle_path, bundle)
        with self.assertRaisesRegex(ValueError, '導出'):self.score()

    def test_changed_raw_after_import_is_rejected(self):
        self.f.populate();self.f.imported();write(self.f.raw_path, {'items': []})
        with self.assertRaisesRegex(ValueError, '指紋'):self.score()

    def test_changed_manifest_after_import_is_rejected(self):
        self.f.populate();self.f.imported();self.f.manifest['customer_id'] = 'COTHER';write(self.f.manifest_path, self.f.manifest)
        with self.assertRaisesRegex(ValueError, '指紋'):self.score()

    def test_changed_ground_truth_after_import_is_rejected(self):
        self.f.populate();self.f.imported();self.f.truth[0]['expected_by_kind']['email'] = 0
        write(self.f.dataset/'ground_truth.json', self.f.truth)
        with self.assertRaisesRegex(ValueError, '正解表'):self.score()

    def test_changed_input_body_after_import_is_rejected(self):
        self.f.populate();self.f.imported();(self.f.dataset/'drive_upload/basic.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError, '変更'):self.score()

    def test_free_text_negative_observation_is_rejected(self):
        write(self.f.bundle_path, [{'case_id': 'basic', 'status': 'not_detected', 'evidence': 'an operator said so'}])
        with self.assertRaisesRegex(ValueError, '自由記述'):self.score()

    def test_observation_input_inside_repository_is_rejected(self):
        write(self.f.bundle_path, [])
        with patch.object(common, 'REPOSITORY', self.f.root.resolve()):
            with self.assertRaises(ValueError):scoring.load_observations(self.f.bundle_path)

    def test_raw_proof_inside_repository_is_rejected(self):
        self.f.populate();self.f.imported()
        with patch.object(common, 'REPOSITORY', self.f.raw_path.resolve()):
            with self.assertRaises(ValueError):scoring.load_observations(self.f.bundle_path)

    def test_report_inside_repository_is_rejected(self):
        self.f.populate();self.f.imported()
        with patch.object(common, 'REPOSITORY', self.f.report_path.resolve()):
            with self.assertRaises(ValueError):self.score()


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        path = self.root/'drive_upload/sample.txt';path.parent.mkdir(parents=True);path.write_text('sample@example.test')
        self.item = {'path': 'sample.txt', 'source_id': 'synthetic-source', 'format': 'TXT', 'positive': True,
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def load(self):
        write(self.root/'ground_truth/files.json', [self.item])
        return scoring.load_truth(self.root)[0][0]

    def test_missing_entities_are_unknown_not_negative(self):
        row = self.load()
        self.assertTrue(all(v is None for v in row['expected_by_kind'].values()))

    def test_null_entities_are_unknown_not_negative(self):
        self.item['entities'] = None;row = self.load()
        self.assertTrue(all(v is None for v in row['expected_by_kind'].values()))

    def test_explicit_empty_inventory_is_not_inferred_positive(self):
        self.item.update(positive=False, entities=[]);row = self.load()
        self.assertTrue(all(v == 0 for v in row['expected_by_kind'].values()))
        self.assertTrue(all(v is None for v in row['protection_expected_by_kind'].values()))

    def test_expanded_inventory_maps_known_types_but_not_protection(self):
        self.item['entities'] = [{'type': 'メール', 'value': 'sample@example.test'}]
        row = self.load()
        self.assertEqual(row['expected_by_kind']['email'], 1)
        self.assertEqual(row['expected_by_kind']['card'], 0)
        self.assertEqual(row['evaluation_track'], 'format_coverage')
        self.assertIsNone(row['protection_expected_by_kind']['email'])

    def test_input_path_cannot_escape_dataset(self):
        self.item['path'] = '../../outside.txt'
        with self.assertRaises(ValueError):self.load()


class StorageTests(unittest.TestCase):
    def test_existing_temporary_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);target = root/'must-not-change.txt';target.write_text('keep')
            output = root/'report.json';output.with_name('report.json.tmp').symlink_to(target)
            common.write_private(output, {'synthetic': 'value'})
            self.assertEqual(target.read_text(), 'keep')
            self.assertEqual(json.loads(output.read_text()), {'synthetic': 'value'})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':unittest.main()
