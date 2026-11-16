#!/usr/bin/env python3
"""計画の形式・条件と実際の生成物を照合する。未実施を成功にしない。"""
import argparse
import json
from pathlib import Path
from generate import dump


def audit(dataset):
    rows=json.loads((dataset/'ground_truth/files.json').read_text())
    checks=[]
    def require(group,label,predicate):
        matching=[r for r in rows if predicate(r)]
        sources={True:set(),False:set()}
        for r in matching:sources[r['positive']].update(r.get('source_ids',[r['source_id']]))
        ok=all(len(v)>=2 for v in sources.values())
        checks.append({'group':group,'condition':label,'status':'作成済み' if ok else '不足',
                       'positive_sources':len(sources[True]),'negative_sources':len(sources[False]),
                       'files':[r['path'] for r in matching]})
    def fmt(f):return lambda r:r['format']==f
    def cond(c):return lambda r:r.get('condition')==c
    for f in ['TXT','Markdown']:require('F01',f,fmt(f))
    for c in ['utf-16','cp932']:require('F01',c,cond(c))
    for f in ['CSV','TSV','JSON','JSONL','XML']:require('F02',f,fmt(f))
    for c in ['入れ子と離れた見出し','引用符内改行・先頭0','複数人物']:require('F02',c,cond(c))
    for f in ['HTML','EML']:require('F03',f,fmt(f))
    for c in ['非表示の要素','宛先のみ','署名・引用','添付のみ']:require('F03',c,cond(c))
    for f in ['DOCX','XLSX','PPTX']:require('F04',f,fmt(f))
    require('F05','文字PDF',fmt('PDF-text'))
    for c in ['multipage','form','annotation','attachment','two-column','vertical']:require('F05',c,cond(c))
    for f in ['PNG','JPEG','TIFF','PDF-image']:require('F06',f,fmt(f))
    for c in ['複数ページ','mixed']:require('F06',c,cond(c))
    require('F08','通常ZIP',lambda r:r['format']=='ZIP' and r['path'].endswith('.deflate.zip'))
    require('F08','無圧縮ZIP',lambda r:r['path'].endswith('.store.zip'))
    for c in ['zipcrypto','zip64','nested','平文と暗号化の項目混在']:require('F08',c,cond(c))
    require('F08','AES ZIP',fmt('ZIP-AES'))
    for c in ['ファイル名','ディレクトリ名','properties','画像属性']:require('F09',c,cond(c))
    for c in ['no-extension','wrong.jpg','容量境界']:require('F10',c,cond(c))
    # 壊した資料は本文を失っており、読取不能の試験へ回す。陰性の精度標本にしない。
    invalid=[r for r in rows if r.get('expected_read_state')=='破損']
    checks.append({'group':'F10','condition':'破損・切断','status':'作成済み' if len(invalid)>=4 else '不足','files':[r['path'] for r in invalid]})
    for c in ['fullwidth','value-zero-width','value-linebreak','Unicode NFD']:require('F11',c,cond(c))
    for f in ['XLS','XLSM','XLSB']:require('F12',f,fmt(f))
    for c in ['hidden','veryHidden','hidden-row','hidden-column','filter','white','format-hidden','merged']:require('F13',c,cond(c))
    for c in ['formula','comment','header','名前定義','image','埋込み文書のみ']:require('F14',c,lambda r,c=c:r['format']=='XLSX' and r.get('condition')==c)
    require('F15','開封用暗号化',fmt('XLSX-encrypted'))
    for c in ['sheet-protection','structure-protection','変更用パスワード']:require('F15',c,cond(c))
    for group in ['F16','F17','F18']:
        checks.append({'group':group,'condition':'Google Sheets・出力物・権限','status':'実環境未実施','files':[],
                       'implementation':'google_drive.py','note':'ローカルXLSXをネイティブSheetsの成功に数えない。CSEは任意。'})
    require('F19','平文7z',lambda r:r['format']=='7z' and r.get('condition')=='平文')
    require('F19','暗号化7z',lambda r:r['format']=='7z' and r.get('condition')=='暗号化')
    for suffix in ['.tar','.tar.gz','.tar.bz2','.tar.xz','.txt.gz','.txt.bz2','.txt.xz']:require('F20',suffix,lambda r,suffix=suffix:r['path'].endswith(suffix))
    for c in ['open','permissions','overlay']:require('F26',c,cond(c))
    redacted=[r for r in rows if r.get('condition')=='実削除']
    checks.append({'group':'F26','condition':'実削除','status':'作成済み' if len(redacted)>=4 and not any(r['positive'] for r in redacted) else '不足','files':[r['path'] for r in redacted]})
    for c in ['header','footer','revision','textbox','脚注']:require('F27',c,lambda r,c=c:r['format']=='DOCX' and r.get('condition')==c)
    for c in ['notes','hidden-slide']:require('F27',c,cond(c))
    for suffix in ['.attachment-encrypted-xlsx.eml','.image-pdf.zip','.embedded-workbook.xlsx']:require('F28',suffix,lambda r,suffix=suffix:r['path'].endswith(suffix))
    require('F32','指示文',cond('instruction'))
    directories=json.loads((dataset/'ground_truth/directories.json').read_text())
    for i in [1,2,3,4,5,6,7,8,9,10,11,13,14,16]:
        key=f'D{i:02d}';present=[d for d in directories if d.get('id')==key]
        checks.append({'group':key,'condition':'ディレクトリ構成','status':'作成済み' if present else '不足','files':[d['path'] for d in present]})
    comparisons=json.loads((dataset/'ground_truth/comparisons.json').read_text())
    for i in range(1,9):
        key=f'V{i:02d}';present=[c for c in comparisons if c['id']==key]
        checks.append({'group':key,'condition':'文脈の比較2組','status':'作成済み' if len(present)>=2 else '不足','files':[p for c in present for p in c['files']]})
    conditions=json.loads((dataset/'ground_truth/read_conditions.json').read_text())
    for key in ['K02','K03','K04','K05','K06']:
        present=[c for c in conditions if c['id']==key]
        checks.append({'group':key,'condition':'鍵・保護の条件','status':'作成済み' if present else '不足','files':[c['path'] for c in present]})
    result={'checks':checks,'missing':[c for c in checks if c['status']=='不足'],
            'environment_pending':[c['group'] for c in checks if c['status']=='実環境未実施'],
            'note':'作成済みは検証合格を意味しない。本文・媒体・鍵・描画の検証結果と併用する。'}
    dump(dataset/'ground_truth/coverage.json',result)
    print(json.dumps({'conditions':len(checks),'missing':[(c['group'],c['condition']) for c in result['missing']],
                      'environment_pending':result['environment_pending']},ensure_ascii=False))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True)
    result=audit(p.parse_args().dataset)
    if result['missing']:raise SystemExit(1)
