"""生成した資料の正解・対・分割・対照を実際の出力から検証する。"""
import contextlib
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

try:
    from . import dataset
except ImportError:
    import dataset


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


class CheckDigitTests(unittest.TestCase):
    def test_known_luhn_values_and_one_digit_error(self):
        self.assertTrue(dataset.luhn_valid('79927398713'))
        self.assertFalse(dataset.luhn_valid('79927398714'))
        self.assertEqual(dataset.luhn_append('7992739871'), '79927398713')
        self.assertTrue(dataset.luhn_valid('4111111111111111'))
        self.assertFalse(dataset.luhn_valid('４１１１１１１１１１１１１１１１'))

    def test_individual_formula_known_example_and_zero_exception(self):
        # 第5条の重みで12345678901は総和212、余り3、検査数字8。
        self.assertEqual(dataset.individual_check_digit('12345678901'), '8')
        self.assertTrue(dataset.individual_valid('123456789018'))
        self.assertFalse(dataset.individual_valid('123456789019'))
        self.assertEqual(dataset.individual_check_digit('00000000000'), '0')
        self.assertEqual(dataset.individual_check_digit('00000000006'), '0')
        with self.assertRaises(ValueError):
            dataset.individual_check_digit('1234567890')
        self.assertFalse(dataset.individual_valid('１２３４５６７８９０１８'))


class GeneratedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='workspace-dlp-dataset-test-')
        cls.root = Path(cls.tmp.name) / 'first'
        with contextlib.redirect_stdout(io.StringIO()):
            cls.rows = dataset.make(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_disjoint_value_families_and_no_sequential_single_value(self):
        for kind in dataset.KINDS:
            rows = [row for row in self.rows if row['kind'] == kind]
            development = {row['synthetic_value'] for row in rows if row['split'] == '開発'}
            evaluation = {row['synthetic_value'] for row in rows if row['split'] == '評価'}
            self.assertEqual(len(development), 2)
            self.assertEqual(len(evaluation), 4)
            self.assertFalse(development & evaluation)
            self.assertEqual(len({row['value_id'] for row in rows}), 6)
        self.assertNotIn('4111111111111111', dataset.values_for('card'))
        self.assertNotIn('1234567', dataset.values_for('bank'))

    def test_every_written_file_has_unique_visible_head_and_tail(self):
        tokens = set()
        for row in self.rows:
            payload = (self.root / 'drive_upload' / row['file']).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), row['sha256'])
            text = payload.decode('utf-8')
            if row['format'] == 'html':
                parser = VisibleText()
                parser.feed(text)
                text = ''.join(parser.parts)
            head = row['scan_control']['head_token']
            tail = row['scan_control']['tail_token']
            self.assertEqual(text.splitlines()[0], head)
            self.assertEqual(text.splitlines()[-1], tail)
            self.assertEqual(text.count(head), 1)
            self.assertEqual(text.count(tail), 1)
            self.assertRegex(head, '^' + dataset.CONTROL_PATTERNS['head'] + '$')
            self.assertRegex(tail, '^' + dataset.CONTROL_PATTERNS['tail'] + '$')
            self.assertFalse(re.search(r'[0-9@]', head + tail))
            self.assertNotIn(head, tokens)
            self.assertNotIn(tail, tokens)
            tokens.update((head, tail))

    def test_bad_checksum_pairs_separate_presence_and_validity(self):
        lookup = {row['case_id']: row for row in self.rows}
        cases = [row for row in self.rows if row['variant'] == 'bad_checksum']
        self.assertTrue(cases)
        for row in cases:
            original = lookup[row['paired_case_id']]
            changed = row['mutated_value']
            self.assertEqual(changed[:-1], original['synthetic_value'][:-1])
            self.assertNotEqual(changed[-1], original['synthetic_value'][-1])
            check = dataset.luhn_valid if row['kind'] == 'card' else dataset.individual_valid
            self.assertTrue(check(original['synthetic_value']))
            self.assertFalse(check(changed))
            self.assertEqual(row['expected_by_kind'][row['kind']], 1)
            self.assertEqual(row['valid_number_expected_by_kind'][row['kind']], 0)
            self.assertEqual(row['protection_expected_by_kind'][row['kind']], 0)
            self.assertIn(changed, (self.root / 'drive_upload' / row['file']).read_text())

    def test_basic_bare_adversarial_and_confusable_cases_are_separate(self):
        for kind in dataset.KINDS:
            rows = [row for row in self.rows if row['kind'] == kind]
            bare = [row for row in rows if row['variant'] == 'bare']
            self.assertEqual(len(bare), 6)
            self.assertTrue(all(row['expected'] == 1 and row['evaluation_track'] == 'basic' for row in bare))
            self.assertTrue(all(row['evaluation_track'] == 'adversarial' for row in rows if row['variant'] in ('fullwidth', 'newline', 'zero_width')))
            roles = {row['role'] for row in rows}
            self.assertTrue({'order_number', 'stock_number', 'date_number', 'protection_negative'} <= roles)
        for row in self.rows:
            if row['kind'] == 'license' and row['expected']:
                self.assertIsNone(row['valid_number_expected_by_kind']['license'])
                self.assertEqual(row['checksum_status'], 'unverified')
            if row['variant'] == 'bare' and row['kind'] == 'individual':
                self.assertIsNone(row['expected_by_kind']['license'])

    def test_full_rule_matrix_and_reproducible_output(self):
        matrix = json.loads((self.root / 'ground_truth.matrix.json').read_text())
        self.assertEqual(len(matrix), len(self.rows) * len(dataset.KINDS))
        self.assertEqual(len({(r['case_id'], r['kind']) for r in matrix}), len(matrix))
        output = Path(self.tmp.name) / 'second'
        with contextlib.redirect_stdout(io.StringIO()):
            dataset.make(output)
        for path in self.root.rglob('*'):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (output / path.relative_to(self.root)).read_bytes())
        with self.assertRaises(FileExistsError):
            dataset.make(self.root)


if __name__ == '__main__':
    unittest.main()
