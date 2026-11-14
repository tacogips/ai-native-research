#!/usr/bin/env python3
"""取得台帳の全PDFへ、既存の文字層の有無にかかわらずOCRを実行する。"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/papers/arxiv_manifest.json'
DEST = ROOT / 'research/papers/ocr_manifest.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(stream.read()).hexdigest()


def page_count(path):
    info = subprocess.check_output(['pdfinfo', str(path)], text=True)
    return int(re.search(r'^Pages:\s*(\d+)', info, re.M)[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--language', default='eng')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs は1以上を指定する')
    for tool in ('ocrmypdf', 'tesseract', 'pdfinfo', 'pdftotext', 'pdftoppm', 'gs'):
        if not shutil.which(tool):
            parser.error(f'{tool} が必要。macOSでは brew install ocrmypdf poppler')
    engine = subprocess.check_output(['ocrmypdf', '--version'], text=True).strip()
    if int(engine.split('.')[0]) < 17:
        parser.error('描画解像度を制限する拡張にはOCRmyPDF 17以上が必要')
    tesseract_version = subprocess.check_output(['tesseract', '--version'], text=True).splitlines()[0]
    previous = json.loads(DEST.read_text()) if DEST.exists() else {'papers': []}
    records = {item['id']: item for item in previous['papers']}
    papers = json.loads(SOURCE.read_text())['papers']

    def save():
        data = {'updated_at': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
                'method': 'force-ocr-all-pages', 'language': args.language,
                'papers': [records[item['id']] for item in papers if item['id'] in records]}
        # 手動の全件照合・代表頁確認は、再処理後の現状と区別して履歴へ残す。
        prior_verification = previous.get('verification') or previous.get('previous_verification')
        if prior_verification:
            data['previous_verification'] = prior_verification
        temp = DEST.with_suffix('.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        temp.replace(DEST)

    for index, item in enumerate(papers, 1):
        source = ROOT / item['pdf_path']
        output = source.with_name('paper_ocr.pdf')
        text = source.with_name('paper_ocr.txt')
        log = source.with_name('ocr.log')
        record = {'id': item['id'], 'source_pdf_path': item['pdf_path']}
        try:
            source_hash = digest(source)
            if source_hash != item['sha256']:
                raise ValueError('原本のSHA-256が取得台帳と一致しない')
            cached = records.get(item['id'], {})
            if (cached.get('status') == 'completed' and cached.get('source_sha256') == source_hash
                    and cached.get('ocr_pages') == item['pages']
                    and cached.get('language') == args.language and output.exists() and text.exists()
                    and digest(output) == cached.get('ocr_sha256') and digest(text) == cached.get('text_sha256')):
                print(f'再利用 {index}/{len(papers)} {item["id"]}', flush=True)
                continue
            if shutil.disk_usage(source.parent).free < 2 * 1024**3:
                raise RuntimeError('空き容量が2 GiB未満。原本を保持したまま停止する')
            record.update(status='running', source_sha256=source_hash, language=args.language,
                          engine='OCRmyPDF ' + engine, tesseract=tesseract_version,
                          rendering_plugin_sha256=digest(ROOT / 'scripts/ocr_dpi_limit.py'),
                          started_at=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat())
            records[item['id']] = record
            save()
            pending_pdf = source.with_name('paper_ocr.pending.pdf')
            pending_text = source.with_name('paper_ocr.pending.txt')
            for pending in (pending_pdf, pending_text):
                pending.unlink(missing_ok=True)
            command = ['ocrmypdf', '--force-ocr', '--output-type', 'pdf', '--optimize', '1',
                       '--plugin', str(ROOT / 'scripts/ocr_dpi_limit.py'),
                       '--jobs', str(args.jobs), '--language', args.language,
                       '--tesseract-timeout', '3600', '--sidecar', str(pending_text), str(source), str(pending_pdf)]
            print(f'OCR開始 {index}/{len(papers)} {item["id"]} ({item["pages"]}頁)', flush=True)
            with log.open('w') as stream:
                subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True,
                               env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
            pages = page_count(pending_pdf)
            body = pending_text.read_text()
            page_texts = body.split('\f')
            if pages != item['pages'] or len(page_texts) != pages or not body.strip():
                raise ValueError('PDF・OCR本文の頁数が一致しない、またはOCR本文が空')
            if re.search(r'\[(?:skipped page|OCR skipped[^\]]*)\]', body, re.I):
                raise ValueError('OCRを省略した頁がある')
            searchable = subprocess.check_output(['pdftotext', str(pending_pdf), '-'], text=True)
            if not searchable.strip():
                raise ValueError('OCR版PDFの検索用文字層が空')
            if digest(source) != source_hash:
                raise ValueError('処理中に原本が変更された')
            pending_pdf.replace(output)
            pending_text.replace(text)
            record.update(status='completed', ocr_pdf_path=str(output.relative_to(ROOT)),
                          ocr_text_path=str(text.relative_to(ROOT)), pages=pages, ocr_pages=len(page_texts), ocr_bytes=output.stat().st_size,
                          ocr_sha256=digest(output), text_sha256=digest(text), text_characters=len(body),
                          searchable_text_characters=len(searchable),
                          completed_at=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(), command=command[:command.index(str(pending_text))] + ['<本文保存先>', '<原本>', '<OCR版PDF>'])
            record['recognition_warnings'] = [line.strip() for line in log.read_text().splitlines()
                                              if '[tesseract]' in line and ('poor OCR' in line or 'skipping' in line)]
            print(f'OCR完了 {index}/{len(papers)} {item["id"]} ({pages}頁)', flush=True)
        except Exception as exc:
            record.update(status='failed', error=f'{type(exc).__name__}: {exc}')
            print(f'OCR失敗 {item["id"]}: {record["error"]}（詳細: {log}）', flush=True)
        records[item['id']] = record
        save()
        if record.get('status') == 'failed':
            raise SystemExit(1)
    print(f'全{len(papers)}本のOCRを完了', flush=True)


if __name__ == '__main__':
    main()
