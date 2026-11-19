import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

import identifier_benchmark as benchmark


class IdentifierBenchmarkTests(unittest.TestCase):
    def test_shared_formats_and_unknown_pairs(self):
        explicit = defaultdict(set)
        pairs = defaultdict(list)
        identifiers = set()
        rows = benchmark.cases()
        self.assertEqual(len(rows), 1536)
        for row, text in rows:
            self.assertNotIn(row['case_id'], identifiers)
            identifiers.add(row['case_id'])
            if row['scenario'] == 'explicit':
                value = text.splitlines()[1].split('：')[1]
                explicit[(row['value_family'], value)].update(
                    kind for kind, truth in row['expected_by_kind'].items() if truth
                )
            if row['scenario'] == 'no_context_pair':
                self.assertEqual(set(row['expected_by_kind'].values()), {None})
                pairs[row['value_family']].append((text, row['provenance_kind']))
        self.assertEqual(len(explicit), 48)
        self.assertTrue(all(kinds == set(benchmark.LABELS) for kinds in explicit.values()))
        self.assertEqual(len(pairs), 48)
        for pair in pairs.values():
            self.assertEqual(len({text for text, _ in pair}), 1)
            self.assertEqual({kind for _, kind in pair}, {'employee', 'order'})

    def test_scoring_counts_documents_and_rejects_changed_input(self):
        class MatchEveryDocument:
            def search(self, _):
                return True

        with tempfile.TemporaryDirectory() as name:
            dataset = Path(name) / 'dataset'
            benchmark.make(dataset)
            report = benchmark.evaluate(dataset, benchmark.DEFAULT_RULES, lambda _: MatchEveryDocument())
            result = report['rule_sets']['format_only']
            self.assertEqual(result['by_item']['employee']['counts'],
                             Counter(TP=336, FP=1104, TN=0, FN=0, unscorable=96))
            self.assertEqual(result['by_item']['employee_or_contract']['evaluated'], 1440)
            self.assertIsNone(result['by_item']['employee']['full_cohort_point_metrics'])
            self.assertIsNone(report['likelihood_threshold'])
            document = next((dataset / 'drive_upload').iterdir())
            document.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, '検査値'):
                benchmark.evaluate(dataset, benchmark.DEFAULT_RULES, lambda _: MatchEveryDocument())
