#!/usr/bin/env python3
"""LIGHTの全形式作成処理。画像生成済みディレクトリを入力にする。"""
import argparse
import bz2
import csv
import gzip
import hashlib
import html
import io
import json
import lzma
import shutil
import subprocess
import tarfile
import zipfile
from email.message import EmailMessage
from pathlib import Path

import fitz
from pdf_fonts import write as pdf_text
import msoffcrypto
import py7zr
import pyzipper
import xlwt
import xlsxwriter
from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt
from PIL import Image
from pypdf import PdfReader

from generate import digest, dump

PASSWORD = 'DlpTest-2026'


def main(args):
    from pdf_fonts import configure
    configure(args.font)
    out = args.output
    if out.exists():
        raise ValueError('出力先は新しいディレクトリを指定してください')
    if args.images.resolve()==out.resolve():raise ValueError('入力と出力は別ディレクトリを指定してください')
    from generate import verify as verify_images
    verify_images(args.images)
    source_rows = json.loads((args.images / 'ground_truth/files.json').read_text())
    shutil.copytree(args.images, out)
    root = out / 'drive_upload'
    truth = out / 'ground_truth'
    records = source_rows.copy()
    source = [r for r in source_rows if r['format'] == 'PNG' and r['path'].startswith('files/')]
    # 各分類を最低2元文書に広げ、陰性も同数を取る。
    picked = []
    counts = {}
    for r in source:
        key = r.get('primary_type') or (r['entities'][1]['type'] if len(r['entities']) == 3 else '氏名')
        if r['positive'] and counts.get(key, 0) < 2:
            picked.append(r)
            counts[key] = counts.get(key, 0) + 1
    from generate import FIELDS
    if set(counts)!={kind for kind,_,_ in FIELDS} or any(n!=2 for n in counts.values()):
        raise ValueError('各形式へ配分する32分類・各2元文書を確保できません')
    picked += [r for r in source if not r['positive']][:len(picked)]
    if not getattr(args,'exhaustive_formats',False):
        # LIGHTでは全分類×全形式を反復しない。各資料群から2例を採り、陰性も同数にする。
        groups={}
        selected=[]
        for r in source:
            group=r.get('group','')
            if groups.get(group,0)<2:
                selected.append(r);groups[group]=groups.get(group,0)+1
        positives=[r for r in selected if r['positive']]
        negatives=[r for r in selected if not r['positive']]
        used={r['source_id'] for r in negatives}
        negatives += [r for r in source if not r['positive'] and r['source_id'] not in used][:len(positives)-len(negatives)]
        picked=positives+negatives
    coverage = []
    from artifact_xlsx import author as author_xlsx
    artifact_xlsx_used=author_xlsx(picked,root,args.font)

    def register(path, row, fmt, condition='本文', members=None):
        from canonical import normalize_package, normalize_zip
        normalize_package(path)
        normalize_zip(path)
        from occurrences import annotate
        entities=annotate(path,row,fmt,condition)
        record = {'path': path.relative_to(root).as_posix(), 'source_id': row['source_id'],
                  'positive': bool(entities), 'entities': entities, 'text': row['text'],
                  'sha256': digest(path), 'format': fmt, 'condition': condition}
        if 'expected_body' in row:record['expected_body']=row['expected_body']
        if members is not None:
            record['members'] = members
        if fmt.startswith('ZIP'):
            with zipfile.ZipFile(path) as archive:record['members']=[n for n in archive.namelist() if not n.endswith('/')]
        elif fmt=='TAR':
            with tarfile.open(path) as archive:record['members']=[n.name for n in archive.getmembers() if n.isfile()]
        records.append(record)
        return record

    def dest(folder, name):
        p = root / folder / name
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    for row in source:
        p = dest('text', row['source_id'] + '.txt')
        p.write_text(row['text'], encoding='utf-8')
        register(p, row, 'TXT')
    for row in picked:
        sid = row['source_id']
        text = row['text']
        for ext, encoding in [('md', 'utf-8'), ('utf16.txt', 'utf-16'), ('cp932.txt', 'cp932')]:
            p = dest('text', sid + '.' + ext)
            p.write_text(text, encoding=encoding)
            register(p, row, 'Markdown' if ext == 'md' else 'TXT', encoding)
        for ext, sep in [('csv', ','), ('tsv', '\t')]:
            p = dest('structured', sid + '.' + ext)
            with p.open('w', encoding='utf-8', newline='') as f:
                csv.writer(f, delimiter=sep, lineterminator='\n').writerows([[line] for line in text.splitlines()])
            register(p, row, ext.upper())
        for ext, content in [('json', json.dumps({'内容': text}, ensure_ascii=False)),
                             ('jsonl', json.dumps({'内容': text}, ensure_ascii=False)+'\n'),
                             ('xml', '<?xml version="1.0" encoding="utf-8"?><document><body>'+html.escape(text)+'</body></document>'),
                             ('html', '<!doctype html><meta charset="utf-8"><pre>'+html.escape(text)+'</pre>')]:
            p = dest('structured', sid + '.' + ext)
            p.write_text(content, encoding='utf-8')
            register(p, row, ext.upper())
        msg = EmailMessage()
        # 陰性にも個人アドレスを持つメールヘッダーを付けない。
        msg['Subject'] = '資料の確認'
        msg.set_content(text)
        p = dest('mail', sid + '.eml'); p.write_bytes(msg.as_bytes()); register(p, row, 'EML')
        d = Document()
        d.core_properties.author = ''
        d.core_properties.last_modified_by = ''
        for line in text.splitlines():
            d.add_paragraph(line)
        p = dest('office', sid + '.docx'); d.save(p); register(p, row, 'DOCX')
        p = dest('office', sid + '.xlsx')
        if not artifact_xlsx_used:
            # Artifact Toolのない再実行環境のみ、公開ライブラリへ切り替える。
            w = xlsxwriter.Workbook(p)
            w.set_properties({'author': '', 'created': __import__('datetime').datetime(2000,1,1)})
            ws = w.add_worksheet('内容'); ws.set_column(0, 0, 100)
            for k, line in enumerate(text.splitlines()): ws.write_string(k, 0, line)
            w.close()
        register(p, row, 'XLSX')
        p = dest('office', sid + '.xls')
        w = xlwt.Workbook(); ws = w.add_sheet('内容'); ws.col(0).width = 256 * 100
        for k, line in enumerate(text.splitlines()): ws.write(k, 0, line)
        w.save(str(p)); register(p, row, 'XLS')
        prs = Presentation(); prs.core_properties.author = ''; prs.core_properties.last_modified_by = ''
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        box = slide.shapes.add_textbox(Inches(.4), Inches(.4), Inches(9), Inches(6))
        for k, line in enumerate(text.splitlines()):
            para = box.text_frame.paragraphs[0] if k == 0 else box.text_frame.add_paragraph()
            para.text = line; para.font.size = Pt(16)
        p = dest('office', sid+'.pptx'); prs.save(p); register(p, row, 'PPTX')
        # 日本語フォント内蔵のPDF。文字PDFと画像PDFを分離。
        pdf = fitz.open(); page = pdf.new_page(width=700, height=500)
        for k, line in enumerate(text.splitlines()): pdf_text(page,(30,40+k*45),line,fontname='japan',fontsize=13)
        pdf.subset_fonts()
        p = dest('pdf', sid+'.pdf'); pdf.save(p, garbage=4, deflate=True, no_new_id=True); pdf.close(); register(p,row,'PDF-text')
        pdf = fitz.open(); page = pdf.new_page(width=700,height=500)
        page.insert_image(page.rect,filename=str(root/row['path']))
        p = dest('pdf',sid+'.image.pdf'); pdf.save(p, garbage=4, deflate=True, no_new_id=True); pdf.close(); register(p,row,'PDF-image')
    coverage.append({'group':'baseline','status':'generated','sources':len(picked)})
    # 陽性・陰性それぞれ2例で保護・圧縮・周辺領域を作成する。
    pairs = [r for r in picked if r['positive'] and any(e['type']=='氏名' for e in r['entities'])][:2] + [r for r in picked if not r['positive']][:2]
    for r in pairs:
        sid=r['source_id']; payload=(root/'text'/f'{sid}.txt').read_bytes()
        for ext, fn in [('gz',gzip.compress),('bz2',bz2.compress),('xz',lzma.compress)]:
            p=dest('archives',sid+'.txt.'+ext)
            p.write_bytes(fn(payload,mtime=0) if ext=='gz' else fn(payload)); register(p,r,ext.upper(),members=['document.txt'])
        rawtar=io.BytesIO()
        with tarfile.open(fileobj=rawtar,mode='w') as t:
            info=tarfile.TarInfo('document.txt');info.size=len(payload);info.mtime=0;t.addfile(info,io.BytesIO(payload))
        raw=rawtar.getvalue()
        for ext,content in [('tar',raw),('tar.gz',gzip.compress(raw,mtime=0)),('tar.bz2',bz2.compress(raw)),('tar.xz',lzma.compress(raw))]:
            p=dest('archives',sid+'.'+ext);p.write_bytes(content)
            register(p,r,'TAR',members=['document.txt'])
        for suffix,method in [('store',zipfile.ZIP_STORED),('deflate',zipfile.ZIP_DEFLATED)]:
            p=dest('archives',sid+'.'+suffix+'.zip')
            with zipfile.ZipFile(p,'w',compression=method) as z:z.writestr('document.txt',payload)
            register(p,r,'ZIP',members=['document.txt'])
        p=dest('archives',sid+'.aes.zip')
        with pyzipper.AESZipFile(p,'w',compression=pyzipper.ZIP_DEFLATED,encryption=pyzipper.WZ_AES) as z:
            z.setpassword(PASSWORD.encode());z.writestr('document.txt',payload)
        register(p,r,'ZIP-AES','暗号化',members=['document.txt'])
        for hidden in [False,True]:
            p=dest('archives',sid+('.names-encrypted' if hidden else '')+'.7z')
            with py7zr.SevenZipFile(p,'w',password=PASSWORD,header_encryption=hidden) as z:z.writestr(payload,'document.txt')
            register(p,r,'7z','暗号化',members=['document.txt'])
        # XLSXの開封用暗号化と編集保護は別ファイル。
        src=root/'office'/f'{sid}.xlsx'
        p=dest('protected',sid+'.encrypted.xlsx')
        with src.open('rb') as f, p.open('wb') as g:msoffcrypto.OfficeFile(f).encrypt(PASSWORD,g)
        register(p,r,'XLSX-encrypted','暗号化')
        for mode in ['hidden','veryHidden','comment','formula','header','white','hidden-row','hidden-column','filter','format-hidden','merged','image','sheet-protection','structure-protection']:
            p=dest('features',sid+'.'+mode+'.xlsx');w=xlsxwriter.Workbook(p);w.set_properties({'author':''})
            if mode in ['hidden','veryHidden']:
                ws=w.add_worksheet('案内');ws.write('A1','資料の確認');ws.set_column(0,0,100)
            data=w.add_worksheet('内容');data.set_column(0,0,100)
            lines=r['text'].splitlines()
            for k,line in enumerate(lines):
                if mode=='merged':break
                if mode=='comment':data.write_comment(k,0,line,{'author':''})
                elif mode=='formula':data.write_formula(k,0,'="'+line.replace('"','""')+'"',None,line)
                elif mode=='header':data.set_header('&L'+r['text'].replace('\n',' ')) ;break
                elif mode=='image':data.insert_image('A1',str(root/r['path']));break
                else:data.write_string(k,0,line,w.add_format({'font_color':'white'}) if mode=='white' else w.add_format({'num_format':';;;'}) if mode=='format-hidden' else None)
            if mode=='hidden':data.hide()
            if mode=='veryHidden':data.very_hidden()
            if mode=='hidden-row':
                for k in range(len(lines)):data.set_row(k,None,None,{'hidden':True})
            if mode=='hidden-column':data.set_column(0,0,None,None,{'hidden':True})
            if mode=='filter':data.autofilter(0,0,len(lines),0);data.filter_column(0,'x == 除外');[data.set_row(k,None,None,{'hidden':True}) for k in range(1,len(lines))]
            if mode=='merged':
                data.set_column(2,5,25);data.set_row(1,140)
                data.merge_range('C2:F2',r['text'],w.add_format({'text_wrap':True,'valign':'top','font_size':12}))
            if mode=='sheet-protection':data.protect(PASSWORD)
            if mode=='structure-protection':
                # workbookProtectionは後段のOOXML編集で付与。
                pass
            w.close()
            if mode=='structure-protection':
                from openpyxl import load_workbook
                from openpyxl.workbook.protection import WorkbookProtection
                book=load_workbook(p);book.security=WorkbookProtection(workbookPassword=PASSWORD,lockStructure=True);book.save(p)
            register(p,r,'XLSX',mode)
        # 開封保護と権限制限PDF。
        for mode,owner,user in [('open',PASSWORD,PASSWORD),('permissions',PASSWORD,'')]:
            pdf=fitz.open(root/'pdf'/f'{sid}.pdf');p=dest('protected',sid+'.'+mode+'.pdf')
            pdf.save(p,encryption=fitz.PDF_ENCRYPT_AES_256,owner_pw=owner,user_pw=user,permissions=0);pdf.close();register(p,r,'PDF-protected',mode)
    from extra_features import create
    create(root, pairs, register, dest)
    from text_variants import create as create_text_variants
    create_text_variants(root,pairs,register,dest)
    from embedded import create as create_embedded
    create_embedded(root, pairs, register, dest)
    from coverage_cases import create as create_coverage
    create_coverage(root, picked, records, register, dest)
    from comparisons import create as create_comparisons
    create_comparisons(root, picked, register, dest)
    from read_conditions import create as create_read_conditions
    create_read_conditions(root,pairs,records,register,dest)
    from conditional_truth import attach as attach_conditional_truth
    attach_conditional_truth(root,records)
    from content_digest import digest as content_digest
    for record in records:
        p=root/record['path']
        record['content_sha256']=content_digest(p.read_bytes(),p.name,record['format'])
    dump(truth/'files.json',records)
    dump(truth/'coverage.json',coverage)
    dump(out/'generation.json', {'schema':2,'scope':'LIGHT全形式・条件の作成中','image_source':json.loads((args.images/'generation.json').read_text()),'files':len(records),'generator_sha256':{p.name:digest(p) for p in Path(__file__).parent.iterdir() if p.is_file() and (p.suffix in ['.py','.cjs','.mjs','.gs'] or p.name.startswith(('requirements','package')) or p.name=='appsscript.json')},'baseline_xlsx_author':artifact_xlsx_used or {'engine':'XlsxWriter (Artifact Tool unavailable)','version':xlsxwriter.__version__},'format_sampling':'全資料群から2元文書ずつ・陽性陰性同数','capacity_target_bytes':600_000_000,'capacity_allowed_bytes':660_000_000})
    from sheets_bundle import write as write_sheets_bundle
    write_sheets_bundle(out)
    from coverage import audit as audit_coverage
    audit_coverage(out)
    total=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    if total > 660_000_000:raise ValueError(f'許容上限660MB超過: {total}')
    if total>600_000_000:print(f'容量目安600MBを超過: {total}バイト（生成は継続）')
    print(json.dumps({'files':len(records),'bytes':total},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--images',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True)
    p.add_argument('--exhaustive-formats',action='store_true',help='全32分類を各形式へ展開する追加試験。LIGHTでは既定で無効')
    main(p.parse_args())
