#!/usr/bin/env python3
"""各陽性分類と陰性の画像を日本語OCRで確認する。DLP精度の測定ではない。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import subprocess
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--tessdata', type=Path, required=True)
p.add_argument('--report', type=Path, required=True)
a = p.parse_args()
rows = json.loads((a.output / 'ground_truth/files.json').read_text())
chosen = []
seen = set()
for r in rows:
    if not r['path'].startswith('files/'):
        continue
    key = (r['format'], tuple(e['type'] for e in r['entities']), (r['text'].splitlines()[1] if len(r['text'].splitlines())>1 else '') if not r['positive'] else '')
    if key not in seen:
        seen.add(key)
        chosen.append(r)

def run(r):
    result = subprocess.run(['tesseract', str((a.output / 'drive_upload' / r['path']).resolve()), 'stdout',
        '--tessdata-dir', str(a.tessdata.resolve()), '-l', 'jpn', '--psm', '6'], capture_output=True, text=True, errors="replace", timeout=60)
    normalize = lambda s: ''.join(s.split())
    found = [e['value'] for e in r['entities'] if normalize(e['value']) in normalize(result.stdout)]
    return {'path': r['path'], 'returncode': result.returncode, 'expected': len(r['entities']),
            'error': result.stderr if result.returncode else '', 'matched': len(found), 'missing': [e['value'] for e in r['entities'] if e['value'] not in found],
            'ocr': result.stdout}

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(run, chosen))
report = {'scope': '分類・形式ごとの代表画像。空白を除去した対象値の一致。DLP評価ではない。',
          'tesseract': subprocess.run(['tesseract', '--version'], capture_output=True, text=True).stdout.splitlines()[0],
          'jpn_sha256': hashlib.sha256((a.tessdata / 'jpn.traineddata').read_bytes()).hexdigest(),
          'images': len(results), 'expected': sum(r['expected'] for r in results),
          'matched': sum(r['matched'] for r in results), 'results': results}
a.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'}, ensure_ascii=False))
