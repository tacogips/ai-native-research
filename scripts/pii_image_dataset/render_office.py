#!/usr/bin/env python3
"""LibreOffice本体を使い、形式・条件ごとの代表資料をPDFへ描画する。"""
import argparse
import json
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from xml.sax.saxutils import escape
import fitz


def inspect_pdf(pdf,row):
    """変換成功と、表示対象の文字の一致を分ける。目視確認の代用ではない。"""
    visible={'本文','マクロなし','header','footer','textbox','脚注','formula','merged',
             'sheet-protection','structure-protection','変更用パスワード','hidden-slide'}
    if row.get('condition','本文') not in visible:
        return {'state':'別経路で確認','reason':'非表示・属性・画像などの条件はPDF本文だけでは判定できない'}
    with fitz.open(pdf) as document:
        text=''.join(''.join(page.get_text().split()) for page in document)
        missing=[e['value'] for e in row['entities'] if ''.join(e['value'].split()) not in text]
        outside=[]
        for number,page in enumerate(document):
            for word in page.get_text('words'):
                if not page.rect.contains(fitz.Rect(word[:4])):
                    outside.append({'page':number,'text':word[4]})
        return {'state':'一致' if not missing and not outside else '不一致',
                'missing_values':missing,'outside_page':outside,'pages':len(document),
                'limit':'抽出可能な文字とページ範囲を確認。字形・重なり・画像内文字の目視確認は含まない'}


def render(dataset,output,font_dirs):
    if output.exists():raise ValueError('描画先は新規ディレクトリを指定してください')
    executable=shutil.which('soffice')
    if not executable:raise ValueError('LibreOffice本体（soffice）が必要です')
    rows=json.loads((dataset/'ground_truth/files.json').read_text())
    samples={}
    for r in rows:
        if r['format'] not in ['DOCX','XLSX','XLS','XLSM','XLSB','PPTX']:continue
        key=(r['format'],r.get('condition','本文'),r['positive'])
        samples.setdefault(key,r)
    output.mkdir(parents=True)
    results=[]
    with tempfile.TemporaryDirectory(prefix='pii-office-render-') as temp:
        temp=Path(temp);config=temp/'fonts.conf'
        config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'+''.join('<dir>'+escape(str(p.resolve()))+'</dir>' for p in font_dirs)+'<cachedir>'+escape(str(temp/'cache'))+'</cachedir></fontconfig>')
        env=dict(os.environ,FONTCONFIG_FILE=str(config))
        for index,(key,row) in enumerate(sorted(samples.items())):
            folder=output/f'view-{index:03d}';folder.mkdir()
            profile=(temp/f'profile-{index:03d}').as_uri()
            export_format='pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}' if key[1]=='hidden-slide' else 'pdf'
            result=subprocess.run([executable,'-env:UserInstallation='+profile,'--headless','--convert-to',export_format,'--outdir',str(folder.resolve()),str((dataset/'drive_upload'/row['path']).resolve())],env=env,capture_output=True,text=True,timeout=90)
            pdf=folder/(Path(row['path']).stem+'.pdf')
            converted=result.returncode==0 and pdf.exists()
            content=inspect_pdf(pdf,row) if converted else {'state':'変換失敗'}
            results.append({'source':row['path'],'format':key[0],'condition':key[1],'positive':key[2],
                            'conversion_success':converted,'content_check':content,
                            'success':converted and content['state']!='不一致',
                            'visual_review':'未実施','inspection_hidden_slides':key[1]=='hidden-slide','pdf':str(pdf.relative_to(output))})
    (output/'render-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    failed=[r for r in results if not r['success']]
    print(json.dumps({'samples':len(results),'failed':failed},ensure_ascii=False))
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--font-dir',type=Path,action='append',required=True)
    a=p.parse_args();results=render(a.dataset,a.output,a.font_dir)
    if any(not r['success'] for r in results):raise SystemExit(1)
