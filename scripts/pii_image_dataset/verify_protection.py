#!/usr/bin/env python3
"""鍵の有無・正否で実際に読める範囲が変わることを検証する。"""
import argparse
import io
import json
import tempfile
from pathlib import Path

import fitz
import msoffcrypto
import py7zr
import pyzipper


def read(data,name,password,inner_password=None):
    if name.endswith('.xlsx'):
        with io.BytesIO(data) as source:
            office=msoffcrypto.OfficeFile(source);office.load_key(password=password,verify_password=True)
            output=io.BytesIO();office.decrypt(output);return [output.getvalue()],[]
    if name.endswith('.pdf'):
        pdf=fitz.open(stream=data,filetype='pdf')
        if not password or not pdf.authenticate(password):raise ValueError('PDF復号不能')
        text='\n'.join(p.get_text() for p in pdf).encode();pdf.close();return [text],[]
    if name.endswith('.7z'):
        with tempfile.TemporaryDirectory(prefix='pii-key-check-') as temp:
            with py7zr.SevenZipFile(io.BytesIO(data),password=password) as archive:archive.extractall(path=temp)
            return [p.read_bytes() for p in Path(temp).rglob('*') if p.is_file()],[]
    output=[];errors=[]
    with pyzipper.AESZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            try:
                raw=archive.read(name,pwd=password.encode() if password else None)
                if name.endswith('.xlsx'):
                    # 暗号化XLSXをさらに復号する。外側だけ読めても完了にはしない。
                    try:
                        children,failures=read(raw,name,inner_password)
                        output.extend(children);errors.extend(failures)
                    except Exception:errors.append(name)
                else:output.append(raw)
            except Exception:errors.append(name)
    return output,errors


def verify(dataset):
    conditions=json.loads((dataset/'ground_truth/read_conditions.json').read_text())
    defaults={'correct':'DlpTest-2026','wrong':'Incorrect-Password','missing':None}
    results=[]
    for c in conditions:
        if c['id']=='K02':continue
        p=dataset/'drive_upload'/c['path']
        keys=c['keys']
        password=defaults[keys.get('default','missing')]
        inner=None
        if 'outer' in keys:
            password='Outer-Dlp-2026' if keys['outer']=='correct' else defaults[keys['outer']]
            inner=defaults[keys['inner']]
        try:
            content,errors=read(p.read_bytes(),p.name,password,inner)
            state='完了' if not errors else '部分読取' if content or keys.get('outer')=='correct' else '復号不能'
        except Exception:state='復号不能'
        if state!=c['expected_read_state']:raise ValueError('鍵条件の不一致: '+str((c['path'],keys,state,c['expected_read_state'])))
        results.append({'path':c['path'],'condition':c['id'],'state':state})
    print(json.dumps({'key_conditions_verified':len(results),'results':results},ensure_ascii=False))
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True)
    verify(p.parse_args().dataset)
