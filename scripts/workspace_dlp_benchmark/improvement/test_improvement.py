"""改善案の検証コードの単体試験。RE2がない環境では正規表現の試験を飛ばす。"""
import hashlib
import json
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'extended'))
import context_rules  # noqa: E402
import flow  # noqa: E402
from catalog import ITEMS, LIMITS  # noqa: E402

try:
    import re2
except ImportError:
    re2 = None

FROZEN = json.loads((HERE / 'frozen.json').read_text(encoding='utf-8'))


class FrozenRecord(unittest.TestCase):
    def test_rules_and_holdout_unchanged(self):
        """保留資料を見た後に規則を調整していないこと。変えるなら新しい保留資料で測り直す。"""
        self.assertEqual(hashlib.sha256((HERE / FROZEN['rules_file']).read_bytes()).hexdigest(), FROZEN['rules_sha256'])
        self.assertEqual(hashlib.sha256((HERE / FROZEN['holdout_file']).read_bytes()).hexdigest(), FROZEN['holdout_sha256'])

    def test_holdout_generator_reproduces(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(HERE / 'holdout_generator.py', d)
            subprocess.run([sys.executable, '-I', str(Path(d) / 'holdout_generator.py')], check=True,
                           capture_output=True)
            self.assertEqual(hashlib.sha256((Path(d) / 'holdout_cases.json').read_bytes()).hexdigest(),
                             FROZEN['holdout_sha256'])


class Holdout(unittest.TestCase):
    def test_schema(self):
        cases = json.loads((HERE / 'holdout_cases.json').read_text(encoding='utf-8'))
        self.assertEqual(len({c['case_id'] for c in cases}), len(cases))
        for c in cases:
            self.assertIn(c['item'], ITEMS)
            self.assertIn(c['kind'], ('positive', 'negative', 'ambiguous'))
            self.assertTrue(set(c['present']) | set(c['ambiguous']) <= set(ITEMS))
            if c['kind'] == 'positive':
                self.assertIn(c['item'], c['present'])
            if c['kind'] == 'negative':
                self.assertNotIn(c['item'], c['present'])


@unittest.skipIf(re2 is None, 'google-re2 が必要')
class Rules(unittest.TestCase):
    def test_compile_and_limits(self):
        rx = context_rules.detectors()
        for r in rx:
            re2.compile(r)
        self.assertLessEqual(len(rx), LIMITS['custom_detectors_in_rules'])
        self.assertLessEqual(max(len(r) for r in rx), LIMITS['regex_chars'])

    def test_every_item_has_rule(self):
        self.assertEqual(set(context_rules.RULES), set(ITEMS))

    def test_empty_and_masked_forms_are_not_detected(self):
        compiled = {r: re2.compile(r) for r in context_rules.detectors()}
        techs = {'T1', 'T2', 'T3'}
        for text, item in [('職歴：＿＿＿＿', 'job_history'), ('前科：****', 'criminal_record'),
                           ('既往歴：＿＿', 'medical_history'), ('民族学の講義', 'race'),
                           ('被保険者番号：1234-567890-1', 'private_insurance')]:
            self.assertIsNone(context_rules.detect(compiled, item, text, techs), (text, item))

    def test_context_examples(self):
        compiled = {r: re2.compile(r) for r in context_rules.detectors()}
        techs = {'T1', 'T2', 'T3'}
        self.assertTrue(context_rules.detect(compiled, 'individual', '氏名\t見本 花子\n番号\t1234 5678 9012', techs))
        # 業務番号の語があれば外す（T3）
        self.assertIsNone(context_rules.detect(compiled, 'individual', '顧客 見本様 注文番号 123456789012', techs))
        self.assertTrue(context_rules.detect(compiled, 'individual', '顧客 見本様 注文番号 123456789012', {'T1', 'T2'}))


class Flow(unittest.TestCase):
    SMALL = {'files': 1500, 'weeks': 10}

    def test_invalid_transition_rejected(self):
        c = flow.Case(1, 'owner')
        with self.assertRaises(ValueError):
            c.move('deleted', 0)

    def test_f1_deletes_only_after_confirmation_and_grace(self):
        res = flow.simulate('F1', {'tpr': 0.8, 'fpr': 0.05}, self.SMALL, seed=3, keep_cases=True)
        grace = flow.DEFAULT_SCENARIO['grace_weeks']
        deleted = [c for c in res['_cases'].values() if c.state == 'deleted']
        self.assertTrue(deleted)
        for c in deleted:
            states = [e['to'] for e in c.log]
            self.assertIn('confirmed', states)
            confirmed_week = next(e['week'] for e in c.log if e['to'] == 'confirmed')
            self.assertGreaterEqual(c.log[-1]['week'] - confirmed_week, grace)
        self.assertEqual(res['deletions_without_grace'], 0)

    def test_f1_every_open_case_has_assignee(self):
        res = flow.simulate('F1', {'tpr': 0.8, 'fpr': 0.05}, {**self.SMALL, 'departed_owner_rate': 0.3}, seed=1,
                            keep_cases=True)
        for c in res['_cases'].values():
            if c.state in ('proposed', 'escalated', 'enforced'):
                self.assertIn(c.assignee, ('owner', 'manager'))
        self.assertEqual(res['orphan_stuck'], 0)

    def test_f0_leaves_departed_owner_cases_stuck(self):
        res = flow.simulate('F0', {'tpr': 0.8, 'fpr': 0.05}, {**self.SMALL, 'departed_owner_rate': 0.3}, seed=1)
        self.assertGreater(res['orphan_stuck'], 0)

    def test_notification_has_no_matched_value(self):
        f = flow.File(7, True, True, 'external', False, False)
        self.assertEqual(set(flow.notification(f, 'G1')), {'file_id', 'group', 'exposure', 'action'})

    def test_deterministic(self):
        a = flow.simulate('F1', {'tpr': 0.7, 'fpr': 0.05}, self.SMALL, seed=5)
        b = flow.simulate('F1', {'tpr': 0.7, 'fpr': 0.05}, self.SMALL, seed=5)
        self.assertEqual(a['weekly'], b['weekly'])
        random.seed(0)


if __name__ == '__main__':
    unittest.main()
