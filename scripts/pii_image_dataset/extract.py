"""生成器とは別の読取経路で、全形式の格納内容を抽出する。"""
import bz2
import gzip
import io
import json
import lzma
import subprocess
import tarfile
import tempfile
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz
import msoffcrypto
import py7zr
import pyzipper
import xlrd
from PIL import Image

PASSWORD='DlpTest-2026'


def xml_text(raw):
    root=ET.fromstring(raw)
    # 値はテキストだけでなく名前定義・属性等にも入り得る。
    return '\n'.join(list(root.itertext())+[v for e in root.iter() for v in e.attrib.values()])


def extract(data, name, depth=0):
    if depth>8:raise ValueError('検証時の入れ子上限超過')
    lower=name.lower()
    stream=io.BytesIO(data)
    if data.startswith(b'%PDF'):
        pdf=fitz.open(stream=data,filetype='pdf')
        if pdf.needs_pass:
            if pdf.authenticate('incorrect'):raise ValueError('誤った鍵で復号できた')
            if not pdf.authenticate(PASSWORD):raise ValueError('PDF復号失敗')
        parts=[p.get_text() for p in pdf]
        parts += [v for v in pdf.metadata.values() if isinstance(v,str)]
        for page in pdf:
            parts += [str(a.info.get('content','')) for a in page.annots() or []]
            parts += [str(w.field_value) for w in page.widgets() or []]
        for i in range(pdf.embfile_count()):parts.append(extract(pdf.embfile_get(i),pdf.embfile_info(i)['filename'],depth+1))
        pdf.close();return '\n'.join(parts)
    if data.startswith(b'\xd0\xcf\x11\xe0'):
        if lower.endswith('.xls'):
            book=xlrd.open_workbook(file_contents=data)
            return '\n'.join(str(cell.value) for sheet in book.sheets() for row in sheet.get_rows() for cell in row)
        office=msoffcrypto.OfficeFile(stream);office.load_key(password=PASSWORD);buf=io.BytesIO();office.decrypt(buf)
        return extract(buf.getvalue(),'document.xlsx',depth+1)
    if data.startswith(b'7z\xbc\xaf\x27\x1c'):
        with tempfile.TemporaryDirectory(prefix='pii-verify-') as folder:
            with py7zr.SevenZipFile(stream,'r',password=PASSWORD) as archive:
                for member in archive.getnames():
                    if not (Path(folder)/member).resolve().is_relative_to(Path(folder).resolve()):raise ValueError('範囲外の圧縮メンバー')
                archive.extractall(path=folder)
            return '\n'.join(extract(p.read_bytes(),p.name,depth+1) for p in sorted(Path(folder).rglob('*')) if p.is_file())
    if zipfile.is_zipfile(stream):
        with zipfile.ZipFile(stream) as z:
            if 'xl/workbook.bin' in z.namelist():
                with tempfile.TemporaryDirectory(prefix='pii-xlsb-') as folder:
                    p=Path(folder)/'document.xlsb';p.write_bytes(data)
                    result=subprocess.run(['node',str(Path(__file__).with_name('native_formats.cjs')),str(p),'-','read'],capture_output=True,text=True,check=True,timeout=60)
                    return result.stdout
        parts=[]
        with pyzipper.AESZipFile(io.BytesIO(data),'r') as z:
            for member in z.namelist():
                if member.endswith('/'):continue
                raw=z.read(member,pwd=('Outer-Dlp-2026' if lower.endswith('.two-keys.zip') else PASSWORD).encode())
                if member.endswith(('.xml','.rels')):
                    try:parts.append(xml_text(raw))
                    except ET.ParseError:pass
                elif member.startswith(('word/media/','xl/media/','ppt/media/')):
                    # 画像の本文はOCR試験側で確認。ここでは内容を勝手に文字へ変換しない。
                    continue
                elif member.startswith(('word/embeddings/','xl/embeddings/','ppt/embeddings/')) or '[Content_Types].xml' not in z.namelist():
                    parts.append(extract(raw,member,depth+1))
        return '\n'.join(parts)
    stream.seek(0)
    if lower.endswith('.eml'):
        msg=BytesParser(policy=policy.default).parsebytes(data);parts=[]
        for part in msg.walk():
            parts.extend(str(v) for _,v in part.items())
            if part.is_multipart():continue
            raw=part.get_payload(decode=True) or b''
            if part.get_filename():parts.append(extract(raw,part.get_filename(),depth+1))
            else:parts.append(raw.decode(part.get_content_charset() or 'utf-8'))
        return '\n'.join(parts)
    if lower.endswith(('.tar','.tar.gz','.tar.bz2','.tar.xz')):
        with tarfile.open(fileobj=stream,mode='r:*') as archive:
            return '\n'.join(extract(archive.extractfile(m).read(),m.name,depth+1) for m in archive.getmembers() if m.isfile())
    for suffix,decode in [('.gz',gzip.decompress),('.bz2',bz2.decompress),('.xz',lzma.decompress)]:
        if lower.endswith(suffix):return extract(decode(data),name[:-len(suffix)],depth+1)
    if data.startswith((b'\x89PNG',b'\xff\xd8',b'II*\x00',b'MM\x00*')):
        with Image.open(stream) as image:
            return '\n'.join(v for v in image.info.values() if isinstance(v,str))
    for enc in (['utf-16'] if data.startswith((b'\xff\xfe',b'\xfe\xff')) else ['utf-8','cp932']):
        try:
            text=data.decode(enc)
            if lower.endswith(('.json','.jsonl')):

                def flatten(value):
                    if isinstance(value,dict):return '\n'.join(flatten(v) for v in value.values())
                    if isinstance(value,list):return '\n'.join(flatten(v) for v in value)
                    return str(value)
                return '\n'.join(flatten(json.loads(line)) for line in text.splitlines())
            if lower.endswith('.xml'):return xml_text(data)
            if lower.endswith('.html'):
                from html.parser import HTMLParser
                class Parser(HTMLParser):
                    def __init__(self):super().__init__();self.parts=[]
                    def handle_data(self,d):self.parts.append(d)
                p=Parser();p.feed(text);return '\n'.join(p.parts)
            return text
        except UnicodeDecodeError:continue
    raise ValueError('抽出未対応: '+name)
