#!/usr/bin/env python3
"""引用されたarXiv論文を取得し、本文抽出・全頁OCRと検証台帳を保存する。"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'research/papers/arxiv'
MANIFEST = ROOT / 'research/papers/arxiv_manifest.json'


def inventory():
    found = {}
    for path in sorted((ROOT / 'research').rglob('*.md')):
        if 'papers' in path.parts:
            continue
        for match in re.finditer(r'https?://arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})(v\d+)?', path.read_text()):
            item = found.setdefault(match[1], {'id': match[1], 'references': [], 'versions': []})
            rel = str(path.relative_to(ROOT))
            if rel not in item['references']:
                item['references'].append(rel)
            if match[2] and match[2] not in item['versions']:
                item['versions'].append(match[2])
    return found


def main():
    missing = [name for name in ('pdftotext', 'pdfinfo', 'ocrmypdf', 'tesseract') if not shutil.which(name)]
    if missing:
        raise SystemExit('必要な道具がない: ' + ', '.join(missing) + '。macOSでは brew install poppler ocrmypdf')
    today = datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
    DEST.mkdir(parents=True, exist_ok=True)
    previous = {}
    if MANIFEST.exists():
        previous = {x['id']: x for x in json.loads(MANIFEST.read_text())['papers']}
    entries = []
    for identifier, item in sorted(inventory().items()):
        version = max(item['versions'], key=lambda x: int(x[1:]), default='')
        item['requested_version'] = version or 'latest-at-retrieval'
        item['url'] = f'https://arxiv.org/pdf/{identifier}{version}'
        folder = DEST / identifier
        folder.mkdir(exist_ok=True)
        pdf = folder / 'paper.pdf'
        txt = folder / 'paper.txt'
        try:
            cached = previous.get(identifier, {})
            if not pdf.exists() or cached.get('requested_version') != item['requested_version']:
                # 公開資料の配布元へ負荷をかけないよう、順番に取得する。
                time.sleep(3)
                request = urllib.request.Request(item['url'], headers={'User-Agent': 'ai-native-research/1.0 (personal literature review)'})
                with urllib.request.urlopen(request, timeout=45) as response:
                    data = response.read()
                    item['resolved_url'] = response.geturl()
                if not data.startswith(b'%PDF-'):
                    raise ValueError('Response is not a PDF')
                pdf.write_bytes(data)
                retrieved_date = today
            else:
                item['resolved_url'] = previous.get(identifier, {}).get('resolved_url', item['url'])
                retrieved_date = cached.get('retrieved_date', today)
            result = subprocess.run(['pdftotext', '-layout', str(pdf), str(txt)], capture_output=True, text=True)
            if result.returncode:
                raise ValueError(result.stderr.strip())
            info = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True, check=True).stdout
            pages = re.search(r'^Pages:\s*(\d+)', info, re.M)
            text_body = txt.read_text()
            pdf_version = re.search(r'arXiv:\s*' + re.escape(identifier) + r'(v\d+)', text_body)
            item['pdf_version'] = pdf_version[1] if pdf_version else 'not-detected'
            item.update(status='downloaded', pdf_path=str(pdf.relative_to(ROOT)), text_path=str(txt.relative_to(ROOT)), bytes=pdf.stat().st_size, sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(), pages=int(pages[1]) if pages else None, text_characters=len(txt.read_text()), retrieved_date=retrieved_date)
            print(f'取得完了 {identifier} {item["pages"]}頁 {item["bytes"]}バイト', flush=True)
        except Exception as exc:
            item.update(status='failed', error=f'{type(exc).__name__}: {exc}', attempted_date=today)
            print(f'取得失敗 {identifier}: {item["error"]}', flush=True)
        entries.append(item)
        MANIFEST.write_text(json.dumps({'checked_date': today, 'papers': entries}, ensure_ascii=False, indent=2) + '\n')
    print(f'取得結果: {sum(x["status"] == "downloaded" for x in entries)}/{len(entries)}本', flush=True)
    if any(x['status'] != 'downloaded' for x in entries):
        raise SystemExit('取得失敗があるためOCR開始前に停止。再実行すると取得を再試行する。')
    subprocess.run([sys.executable, str(ROOT / 'scripts/ocr_arxiv_papers.py')], check=True)


if __name__ == '__main__':
    main()
