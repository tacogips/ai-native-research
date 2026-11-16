"""宣言した形式が実構造に一致するか、本文抽出とは別に検証する。"""
import bz2
import gzip
import io
import json
import lzma
import tarfile
import zipfile
from email import policy
from email.parser import BytesParser
from xml.etree import ElementTree as ET

import fitz
import msoffcrypto
import py7zr
import xlrd
from PIL import Image

OFFICE={
    'DOCX':('word/document.xml','application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml','document'),
    'XLSX':('xl/workbook.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml','workbook'),
    'XLSM':('xl/workbook.xml','application/vnd.ms-excel.sheet.macroEnabled.main+xml','workbook'),
    'XLSB':('xl/workbook.bin','application/vnd.ms-excel.sheet.binary.macroEnabled.main','binary'),
    'PPTX':('ppt/presentation.xml','application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml','presentation'),
}


def validate(path,row):
    data=path.read_bytes();kind=row['format'];condition=row.get('condition','')
    if kind in OFFICE:
        if not zipfile.is_zipfile(io.BytesIO(data)):raise ValueError('宣言Office形式と実体が一致しません: '+row['path'])
        main,content_type,root_name=OFFICE[kind]
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            media=[n for n in package.namelist() if n.startswith(('word/media/','xl/media/','ppt/media/')) and not n.endswith('/')]
            if len(media)!=(1 if condition in ['image','embedded-image'] else 0):raise ValueError('Officeの画像個数が期待構造と異なります')
            embedded=[n for n in package.namelist() if n.startswith(('word/embeddings/','xl/embeddings/','ppt/embeddings/')) and not n.endswith('/')]
            if len(embedded)!=(1 if condition=='埋込み文書のみ' else 0):raise ValueError('Officeの埋込み文書数が期待構造と異なります')
            for part in ['[Content_Types].xml','_rels/.rels',main]:
                if part not in package.namelist():raise ValueError('Office必須部品がありません: '+part)
            types=ET.fromstring(package.read('[Content_Types].xml'))
            overrides={e.get('PartName'):e.get('ContentType') for e in types if e.tag.endswith('Override')}
            defaults={e.get('Extension'):e.get('ContentType') for e in types if e.tag.endswith('Default')}
            actual=overrides.get('/'+main,defaults.get(main.rsplit('.',1)[1]))
            if actual!=content_type:raise ValueError('Office文書種別が違います: '+row['path'])
            rels=ET.fromstring(package.read('_rels/.rels'))
            targets=[e.get('Target','').lstrip('/') for e in rels if e.get('Type','').endswith('/officeDocument')]
            if targets!=[main]:raise ValueError('Officeの主要部品への参照が違います')
            if root_name!='binary' and ET.fromstring(package.read(main)).tag.rsplit('}',1)[-1]!=root_name:raise ValueError('主要XMLの種別が違います')
    elif kind=='XLSX-encrypted':
        office=msoffcrypto.OfficeFile(io.BytesIO(data))
        if not office.is_encrypted():raise ValueError('暗号化Officeではありません')
    elif kind=='XLS':xlrd.open_workbook(file_contents=data)
    elif kind in ['PDF','PDF-text','PDF-image','PDF-protected']:
        if not data.startswith(b'%PDF'):raise ValueError('PDFではありません')
        pdf=fitz.open(stream=data,filetype='pdf')
        if pdf.needs_pass:pdf.authenticate('DlpTest-2026')
        if pdf.page_count<1:raise ValueError('PDFページがありません')
        images=sum(len(page.get_images()) for page in pdf)
        if images!=(1 if kind=='PDF-image' or condition=='mixed' else 0):raise ValueError('PDFの画像個数が期待構造と異なります')
        if pdf.embfile_count()!=(1 if condition=='attachment' else 0):raise ValueError('PDFの添付数が期待構造と異なります')
        pdf.close()
    elif kind.startswith('ZIP'):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names=[n for n in archive.namelist() if not n.endswith('/')]
            if 'members' in row and names!=row['members']:raise ValueError('ZIP内の項目が正解と違います')
    elif kind=='TAR':
        with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as archive:
            if [m.name for m in archive.getmembers() if m.isfile()]!=row['members']:raise ValueError('TAR内の項目が違います')
    elif kind=='7z':
        with py7zr.SevenZipFile(io.BytesIO(data),password='DlpTest-2026') as archive:
            if archive.getnames()!=row['members']:raise ValueError('7z内の項目が違います')
    elif kind in ['GZ','BZ2','XZ']:{'GZ':gzip.decompress,'BZ2':bz2.decompress,'XZ':lzma.decompress}[kind](data)
    elif kind in ['PNG','JPEG','TIFF']:
        with Image.open(io.BytesIO(data)) as image:
            if image.format!=kind:raise ValueError('画像形式が違います')
            image.load()
    elif kind=='XML':ET.fromstring(data)
    elif kind in ['JSON','JSONL']:
        text=data.decode('utf-8')
        if kind=='JSON':json.loads(text)
        else:
            for line in text.splitlines():json.loads(line)
    elif kind=='EML':
        msg=BytesParser(policy=policy.default).parsebytes(data)
        if not msg.get('MIME-Version') or not msg.get('Content-Type'):raise ValueError('MIMEメッセージではありません')
    elif kind=='HTML':
        if not data.lower().startswith(b'<!doctype html>'):raise ValueError('生成対象のHTML構造ではありません')
    elif kind=='invalid':
        if row.get('expected_read_state')=='破損':
            expected=b'%PDF-1.7\n' if condition=='truncated.pdf' else b'PK\x03\x04'
            if data!=expected:raise ValueError('意図した破損資料から変わっています')
        else:data.decode('utf-8')
    elif kind in ['TXT','Markdown','CSV','TSV']:
        data.decode(condition if condition in ['utf-16','cp932'] else 'utf-8')
    else:raise ValueError('形式検証が未対応: '+kind)
