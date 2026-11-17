"""生成全体の固定基準一致と、欠落・追加・内容変更・構造変更の検出。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build
import reproduce


class ReproduceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dataset = self.root / 'dataset'
        build.make(self.dataset)

    def test_fixed_reference_and_structure(self):
        result = reproduce.verify(self.dataset)
        self.assertEqual(result['cases'], 385)
        self.assertEqual(result['files'], 387)
        self.assertEqual(result['directories'], ['drive_upload'])
        self.assertEqual(reproduce.snapshot(self.dataset)['split_counts'], {'開発': 93, '評価': 292})

    def test_detect_changes(self):
        file = next((self.dataset / 'drive_upload').glob('*.txt'))
        original = file.read_bytes()
        for change in ('body', 'missing', 'extra', 'directory', 'truth'):
            with self.subTest(change=change):
                if change == 'body': file.write_bytes(original + b'changed')
                if change == 'missing': file.unlink()
                if change == 'extra': (self.dataset / 'extra.txt').write_bytes(b'extra')
                if change == 'directory': (self.dataset / 'empty').mkdir()
                if change == 'truth':
                    truth = self.dataset / 'ground_truth.json';saved = truth.read_bytes();truth.write_bytes(saved + b' ')
                with self.assertRaises(ValueError): reproduce.verify(self.dataset)
                file.write_bytes(original)
                if change == 'extra': (self.dataset / 'extra.txt').unlink()
                if change == 'directory': (self.dataset / 'empty').rmdir()
                if change == 'truth': truth.write_bytes(saved)

    def test_hash_seed_and_new_destination(self):
        other = self.root / 'other'
        run = subprocess.run([sys.executable, str(reproduce.HERE / 'reproduce.py'), 'make', '--output', str(other)],
                             env={**os.environ, 'PYTHONHASHSEED': '123'}, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(reproduce.snapshot(self.dataset), reproduce.snapshot(other))
        with self.assertRaises(FileExistsError): build.make(other)

    def test_reference_source_mismatch_and_symlink(self):
        reference = json.loads(reproduce.BASELINE.read_text())
        reference['sources']['samples.py'] = 'changed'
        custom = self.root / 'reference.json';custom.write_text(json.dumps(reference))
        with self.assertRaisesRegex(ValueError, 'sources'): reproduce.verify(self.dataset, custom)
        (self.dataset / 'linked.txt').symlink_to(self.dataset / 'ground_truth.json')
        with self.assertRaisesRegex(ValueError, 'シンボリックリンク'): reproduce.verify(self.dataset)
