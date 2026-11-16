"""陰性の書庫・メールを開き、内部の原稿と格納面も仕様へ照合する。"""
import bz2
import gzip
import io
import lzma
import tarfile
import tempfile
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path

import fitz
import msoffcrypto
import py7zr
import pyzipper


def validate(path,row):
    if row['positive'] or row['format'] not in ['EML','7z','TAR','GZ','BZ2','XZ','ZIP','ZIP-AES']:return
    source=row['text']
    def check(data,name,depth=0):
        if depth>8:raise ValueError('期待本文の検証上限超過')
        if data.startswith(b'%PDF'):
            from expected_pdf import validate as pdf_validate
            from formats import validate as format_validate
            with tempfile.TemporaryDirectory() as temp:
                target=Path(temp)/'document.pdf';target.write_bytes(data)
                with fitz.open(target) as pdf:image=any(p.get_images() for p in pdf)
                record=dict(row,format='PDF-image' if image else 'PDF-text',condition='本文')
                format_validate(target,record);pdf_validate(target,record)
            return
        if data.startswith(b'\xd0\xcf\x11\xe0'):
            office=msoffcrypto.OfficeFile(io.BytesIO(data));office.load_key(password='DlpTest-2026')
            stream=io.BytesIO();office.decrypt(stream);check(stream.getvalue(),'document.xlsx',depth+1);return
        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:office='[Content_Types].xml' in archive.namelist()
            if office:
                from expected_office import validate as office_validate
                from formats import validate as format_validate
                with tempfile.TemporaryDirectory() as temp:
                    target=Path(temp)/name;target.write_bytes(data)
                    record=dict(row,format='XLSX',condition='本文')
                    format_validate(target,record);office_validate(target,record)
                return
            with pyzipper.AESZipFile(io.BytesIO(data)) as archive:
                for item in archive.infolist():
                    if not item.is_dir():check(archive.read(item,pwd=('Outer-Dlp-2026' if name.endswith('.two-keys.zip') else 'DlpTest-2026').encode()),item.filename,depth+1)
            return
        if data.startswith(b'7z\xbc\xaf\x27\x1c'):
            with tempfile.TemporaryDirectory() as temp:
                with py7zr.SevenZipFile(io.BytesIO(data),password='DlpTest-2026') as archive:
                    for member in archive.getnames():
                        if not (Path(temp)/member).resolve().is_relative_to(Path(temp).resolve()):raise ValueError('範囲外の書庫項目')
                    archive.extractall(temp)
                for target in Path(temp).rglob('*'):
                    if target.is_file():check(target.read_bytes(),target.name,depth+1)
            return
        if name.endswith('.eml'):
            mail=BytesParser(policy=policy.default).parsebytes(data)
            for part in mail.walk():
                for key,value in part.items():
                    if key.lower()=='subject':
                        if str(value) not in ['資料の確認','記録']:raise ValueError('陰性メールに期待しない件名')
                    elif key.lower() not in ['mime-version','content-type','content-disposition','content-transfer-encoding']:
                        raise ValueError('陰性メールに期待しないヘッダー')
                if not part.is_multipart():check(part.get_payload(decode=True) or b'',part.get_filename() or 'body.txt',depth+1)
            return
        if name.endswith(('.tar','.tar.gz','.tar.bz2','.tar.xz')):
            with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as archive:
                for item in archive.getmembers():
                    if item.isfile():check(archive.extractfile(item).read(),item.name,depth+1)
            return
        for suffix,decode in [('.gz',gzip.decompress),('.bz2',bz2.decompress),('.xz',lzma.decompress)]:
            if name.endswith(suffix):check(decode(data),name[:-len(suffix)],depth+1);return
        text=data.decode('utf-8');norm=lambda value:''.join(value.split())
        allowed=[source,'資料の案内','資料を確認してください。','添付資料を確認してください。','資料を確認してください。\n\n署名\n'+source]
        if norm(text) not in [norm(value) for value in allowed]:raise ValueError('陰性の内部本文が原稿からの期待値と異なります: '+row['path']+' '+name)
    check(path.read_bytes(),path.name)
