#!/usr/bin/env python3
"""固定した上流関数を抽出して検査失敗の局所挙動を確認。外部APIは呼ばない。"""
import ast
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import time

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'research/disclosures/raw/harness_20261008/guardrails'


class QuietLog:
    def info(self, *args, **kwargs):
        pass
    debug = info
    error = info


def methods(path, class_name, names):
    tree = ast.parse(path.read_text())
    parent = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return [n for n in parent.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]


def execute(nodes, namespace):
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    module = ast.Module(body=[future] + nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), '<固定した上流関数>', 'exec'), namespace)


def pii_error_probe():
    base = RAW / 'llamafirewall/LlamaFirewall/src/llamafirewall/scanners'
    pii = base / 'experimental/piicheck_scanner.py'
    custom = base / 'custom_check_scanner.py'
    selected = methods(custom, 'CustomCheckScanner', {'_evaluate_with_llm'})
    selected += methods(pii, 'PIICheckScanner', {'_get_default_error_response', '_convert_llm_response_to_score', 'scan'})
    assert len(selected) == 4
    cls = ast.ClassDef(name='UpstreamProbe', bases=[], keywords=[], body=selected, decorator_list=[])
    namespace = {'LOG': QuietLog(), 'PIICheckOutputSchema': SimpleNamespace,
                 'ScanResult': SimpleNamespace,
                 'ScanDecision': SimpleNamespace(ALLOW='allow', BLOCK='block'),
                 'ScanStatus': SimpleNamespace(SUCCESS='success')}
    execute([cls], namespace)
    probe = namespace['UpstreamProbe']()
    class UnavailableTransport:
        async def call(self, **kwargs):
            raise RuntimeError('合成した通信障害。外部通信は行わない。')
    probe.llm = UnavailableTransport()
    probe.system_prompt = '説明用'; probe.output_schema = SimpleNamespace
    probe.temperature = 0.0; probe.block_threshold = 0.7
    result = asyncio.run(probe.scan(SimpleNamespace(content='実在者に対応しない試験文')))
    assert result.decision == 'allow' and result.score == 0.0 and result.status == 'success'
    return {'probe': 'LlamaFirewall PIICheckの評価中例外',
            'observed': vars(result), 'source_files': [str(pii.relative_to(ROOT)), str(custom.relative_to(ROOT))],
            'scope': '上流4メソッドは未変更。通信部・結果型・ログだけをローカル代替。完全なライブラリ起動やAPI試験ではない。'}


def invalid_scanner_probe():
    path = RAW / 'llmguard/llm_guard/evaluate.py'
    tree = ast.parse(path.read_text())
    selected = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'scan_prompt')
    namespace = {'time': time, 'LOGGER': QuietLog()}
    execute([selected], namespace)
    class RejectingScanner:
        def scan(self, text):
            return text, False, 0.99
    result = namespace['scan_prompt']([RejectingScanner()], '完全な合成試験文', fail_fast=True)
    assert result[0] == '完全な合成試験文' and result[1] == {'RejectingScanner': False}
    return {'probe': 'LLM Guard fail_fastの不合格', 'observed': result,
            'source_files': [str(path.relative_to(ROOT))],
            'scope': '上流scan_promptは未変更。scannerとログのみローカル代替。アプリの送信停止処理は別。'}


if __name__ == '__main__':
    results = [pii_error_probe(), invalid_scanner_probe()]
    for result in results:
        result['source_sha256'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in result['source_files']}
    path = ROOT / 'research/technology/harness_guardrail_probe_results_20261008.json'
    path.write_text(json.dumps({'as_of': '2026-10-08', 'external_model_calls': 0,
                               'note': '依存を代替した局所的な上流関数の意味確認。全システムの耐性試験ではない。',
                               'results': results}, ensure_ascii=False, indent=2) + '\n')
    print('局所確認2件成功。外部モデル呼出し0件。', path.relative_to(ROOT))
