"""通常XLSXの作成器を、全資料の生成や通信なしで検証する。"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
import generate_all


class XlsxEngineTests(unittest.TestCase):
    def test_auto_uses_available_artifact(self):
        authored = {'engine': 'Artifact Tool', 'version': 'test'}
        with patch('artifact_xlsx.author', return_value=authored) as author:
            result = generate_all.select_xlsx_engine([], Path('output'), Path('font'))
        author.assert_called_once_with([], Path('output'), Path('font'))
        self.assertEqual(result, {'requested': 'auto', 'actual': 'artifact', 'author': authored})

    def test_auto_unavailable_preserves_fallback(self):
        with patch('artifact_xlsx.author', return_value=False):
            result = generate_all.select_xlsx_engine([], None, None)
        self.assertEqual(result['actual'], 'xlsxwriter')
        self.assertEqual(result['author']['engine'], 'XlsxWriter (Artifact Tool unavailable)')

    def test_explicit_xlsxwriter_never_calls_artifact(self):
        with patch('artifact_xlsx.author', side_effect=AssertionError('呼び出してはいけません')) as author:
            result = generate_all.select_xlsx_engine([], None, None, 'xlsxwriter')
        author.assert_not_called()
        self.assertEqual(result['actual'], 'xlsxwriter')
        self.assertEqual(result['author']['engine'], 'XlsxWriter')

    def test_explicit_artifact_unavailable_does_not_fallback(self):
        with patch('artifact_xlsx.author', return_value=False):
            with self.assertRaisesRegex(RuntimeError, '代替の作成器を使いません'):
                generate_all.select_xlsx_engine([], None, None, 'artifact')

    def test_explicit_artifact_keeps_author_version(self):
        with patch('artifact_xlsx.author', return_value={'engine': 'Artifact Tool', 'version': 'test'}):
            result = generate_all.select_xlsx_engine([], None, None, 'artifact')
        self.assertEqual(result['requested'], 'artifact')
        self.assertEqual(result['actual'], 'artifact')
        self.assertEqual(result['author']['version'], 'test')

    def test_artifact_failure_is_not_hidden(self):
        with patch('artifact_xlsx.author', side_effect=RuntimeError('作成失敗')):
            with self.assertRaisesRegex(RuntimeError, '作成失敗'):
                generate_all.select_xlsx_engine([], None, None, 'auto')

    def test_invalid_selection_rejected_before_authoring(self):
        with patch('artifact_xlsx.author') as author:
            with self.assertRaises(ValueError):
                generate_all.select_xlsx_engine([], None, None, 'invalid')
        author.assert_not_called()

    def test_generation_record_keeps_requested_and_actual(self):
        for requested, actual in [('auto', 'artifact'), ('auto', 'xlsxwriter'),
                                  ('artifact', 'artifact'), ('xlsxwriter', 'xlsxwriter')]:
            selected = {'requested': requested, 'actual': actual,
                        'author': {'engine': actual, 'version': 'test'}}
            result = generate_all.generation_metadata({'seed': 1}, 0, selected)
            # JSONへ保存できる形と、要求/実選択・作成器版の記録を確認する。
            saved = json.loads(json.dumps(result))
            self.assertEqual(saved['xlsx_engine'], {'requested': requested, 'actual': actual})
            self.assertEqual(saved['baseline_xlsx_author'], selected['author'])
            self.assertEqual(saved['image_source'], {'seed': 1})

    def test_standalone_cli_accepts_engine_and_default(self):
        args = ['--images', 'images', '--output', 'output', '--font', 'font']
        self.assertEqual(generate_all.parse_args(args).xlsx_engine, 'auto')
        self.assertEqual(generate_all.parse_args(args + ['--xlsx-engine', 'artifact']).xlsx_engine,
                         'artifact')

    def test_build_cli_propagates_engine_without_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            font = root / 'font.ttf'
            font.write_bytes(b'test fixture only')
            for requested in (None, 'auto', 'xlsxwriter', 'artifact'):
                args = ['--output', str(root / 'new'), '--font', str(font)]
                if requested is not None:
                    args += ['--xlsx-engine', requested]
                with patch.object(build.shutil, 'which', return_value='/mock/tool'), \
                     patch.object(build.subprocess, 'run') as node, \
                     patch.object(build.generate, 'generate') as images, \
                     patch.object(build.generate_all, 'main') as all_formats, \
                     patch.dict(build.os.environ, {'PII_XLSX_MODULE': 'mock-module'}), \
                     contextlib.redirect_stdout(io.StringIO()):
                    build.main(args)
                self.assertEqual(all_formats.call_args.args[0].xlsx_engine, requested or 'auto')
                self.assertEqual(images.call_args.args[2], 20261113)
                node.assert_called_once()
                self.assertFalse((root / 'new').exists())


if __name__ == '__main__':
    unittest.main()
