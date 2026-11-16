#!/usr/bin/env python3
"""同じ設定で作った二つのセットの実バイト・復号後の内容を比較する。"""
import argparse
import hashlib
import io
import json
import tempfile
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path

import fitz
import msoffcrypto
import py7zr
import pyzipper

PASSWORD='DlpTest-2026'


def sha(data):return hashlib.sha256(data).hexdigest()


def semantic(data,name,depth=0):
    if depth>8:raise ValueError('入れ子が検証上限を超過')
    if data.startswith(b'\xd0\xcf\x11\xe0') and name.endswith('.xlsx'):
        office=msoffcrypto.OfficeFile(io.BytesIO(data));office.load_key(password=PASSWORD,verify_password=True)
        stream=io.BytesIO();office.decrypt(stream);return ['Office-encrypted',semantic(stream.getvalue(),'document.xlsx',depth+1)]
    if data.startswith(b'%PDF'):
        pdf=fitz.open(stream=data,filetype='pdf')
        encrypted=pdf.needs_pass
        if encrypted and not pdf.authenticate(PASSWORD):raise ValueError('PDFを復号できない')
        pages=[]
        for page in pdf:
            images=[]
            for item in page.get_images():
                pix=fitz.Pixmap(pdf,item[0]);images.append([pix.width,pix.height,sha(pix.samples)])
            pages.append({'text':page.get_text(),'images':images,
                          'widgets':[(w.field_name,w.field_value) for w in page.widgets() or []],
                          'annotations':[(a.type,a.info.get('content')) for a in page.annots() or []]})
        attachments=[semantic(pdf.embfile_get(k),pdf.embfile_info(k)['filename'],depth+1) for k in range(pdf.embfile_count())]
        result=['PDF',encrypted,pdf.permissions,pages,attachments]
        pdf.close();return result
    if data.startswith(b'7z\xbc\xaf\x27\x1c'):
        hidden=False
        try:
            with py7zr.SevenZipFile(io.BytesIO(data)) as archive:archive.getnames()
        except py7zr.exceptions.PasswordRequired:hidden=True
        with tempfile.TemporaryDirectory(prefix='pii-repro-') as folder:
            with py7zr.SevenZipFile(io.BytesIO(data),password=PASSWORD) as archive:
                for member in archive.getnames():
                    if not (Path(folder)/member).resolve().is_relative_to(Path(folder).resolve()):raise ValueError('範囲外の書庫メンバー')
                archive.extractall(folder)
            return ['7z',hidden,[(p.relative_to(folder).as_posix(),semantic(p.read_bytes(),p.name,depth+1)) for p in sorted(Path(folder).rglob('*')) if p.is_file()]]
    if zipfile.is_zipfile(io.BytesIO(data)):
        parts=[]
        with pyzipper.AESZipFile(io.BytesIO(data)) as archive:
            password='Outer-Dlp-2026' if name.endswith('.two-keys.zip') else PASSWORD
            for info in sorted(archive.infolist(),key=lambda i:i.filename):
                if info.filename.endswith('/'):continue
                raw=archive.read(info.filename,pwd=password.encode())
                parts.append([info.filename,info.compress_type,bool(info.flag_bits&1),semantic(raw,info.filename,depth+1)])
        return ['ZIP',parts]
    if name.endswith('.eml'):
        mail=BytesParser(policy=policy.default).parsebytes(data)
        parts=[]
        for part in mail.walk():
            if part.is_multipart():continue
            raw=part.get_payload(decode=True) or b''
            parts.append([part.get_content_type(),semantic(raw,part.get_filename() or 'body.txt',depth+1)])
        return ['EML',[(k,str(v)) for k,v in mail.items() if k.lower()!='content-type'],parts]
    return ['bytes',sha(data)]


def compare(first,second):
    rows=json.loads((first/'ground_truth/files.json').read_text())
    other={r['path']:r for r in json.loads((second/'ground_truth/files.json').read_text())}
    if {r['path'] for r in rows}!=set(other):raise ValueError('ファイル配置が異なる')
    exact=0;semantic_equal=[]
    for r in rows:
        peer=other[r['path']]
        if {k:v for k,v in r.items() if k!='sha256'}!={k:v for k,v in peer.items() if k!='sha256'}:raise ValueError('正解が異なる: '+r['path'])
        a=(first/'drive_upload'/r['path']).read_bytes();b=(second/'drive_upload'/r['path']).read_bytes()
        if a==b:exact+=1;continue
        if semantic(a,Path(r['path']).name)!=semantic(b,Path(r['path']).name):raise ValueError('内容が異なる: '+r['path'])
        semantic_equal.append(r['path'])
    # ハッシュを含まない条件・作成器・設定の記録も同じであることを確認。
    for relative in ['generation.json','ground_truth/directories.json','ground_truth/comparisons.json','ground_truth/read_conditions.json','ground_truth/coverage.json','ground_truth/conditional_expectations.json']:
        if json.loads((first/relative).read_text())!=json.loads((second/relative).read_text()):raise ValueError('設定・条件が異なる: '+relative)
    result={'files':len(rows),'byte_identical':exact,'semantic_identical':len(semantic_equal),'semantic_comparison_files':semantic_equal}
    print(json.dumps(result,ensure_ascii=False));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--first',type=Path,required=True);p.add_argument('--second',type=Path,required=True)
    a=p.parse_args();compare(a.first,a.second)
