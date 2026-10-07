#!/usr/bin/env python3
"""文字層のない日本語入門資料を全頁OCRし、頁区切りを保持する。"""
import concurrent.futures
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECORD = ROOT / 'research/disclosures/privacy_retrieval_20261007.json'
LANG_URL = 'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/jpn.traineddata'

def main():
    data = json.loads(RECORD.read_text())
    raw = ROOT / data['raw_storage']
    tess = raw / 'ocr_resources'
    tess.mkdir(exist_ok=True)
    lang = tess / 'jpn.traineddata'
    if not lang.exists():
        with urllib.request.urlopen(LANG_URL, timeout=60) as response:
            lang.write_bytes(response.read())
    for doc in data['documents']:
        if doc['id'] not in ('ppc_simple', 'ppc_handbook'):
            continue
        source = ROOT / doc['local_file']
        def page(number):
            with tempfile.TemporaryDirectory(dir=raw) as temp:
                prefix = pathlib.Path(temp) / 'page'
                subprocess.run(['pdftoppm', '-f', str(number), '-l', str(number), '-singlefile',
                    '-r', '180', '-png', str(source), str(prefix)], check=True, capture_output=True)
                result = subprocess.run(['tesseract', str(prefix) + '.png', 'stdout',
                    '--tessdata-dir', str(tess), '-l', 'jpn', '--psm', '3'], check=True,
                    capture_output=True, text=True, env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
                return result.stdout
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            texts = list(executor.map(page, range(1, doc['pages'] + 1)))
        path = raw / (doc['id'] + '_ocr.txt')
        path.write_text('\f'.join(texts), encoding='utf-8')
        doc['ocr'] = {'method': 'pdftoppm 180dpi と Tesseract jpn', 'pages': len(texts),
                      'text_file': str(path.relative_to(ROOT)), 'text_characters': len(path.read_text()),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'language_source_url': LANG_URL,
                      'language_sha256': hashlib.sha256(lang.read_bytes()).hexdigest(),
                      'note': '検索補助。図表や文字の認識誤りは原本画像で確認する。'}
        RECORD.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(doc['id'], len(texts), '頁OCR完了', flush=True)

if __name__ == '__main__':
    main()
