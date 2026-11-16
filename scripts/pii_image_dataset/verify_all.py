#!/usr/bin/env python3
"""全形式版の実ファイル・正解と、解析可能な本文の一致を検証する。"""
import argparse
import io
import json
import zipfile
from pathlib import Path

import fitz
import msoffcrypto
from PIL import Image
from generate import digest


def verify(root):
    inputs=root/'drive_upload'
    rows=json.loads((root/'ground_truth/files.json').read_text())
    paths=set()
    checked=0
    deferred=[]
    for r in rows:
        path=inputs/r['path']
        if not path.resolve().is_relative_to(inputs.resolve()):raise ValueError('範囲外の経路')
        if r['path'] in paths:raise ValueError('重複経路')
        paths.add(r['path'])
        if digest(path)!=r['sha256']:raise ValueError('ハッシュ不一致: '+r['path'])
        if r['positive']!=bool(r['entities']):raise ValueError('内容正解の不整合')
        from formats import validate as validate_format
        validate_format(path,r)
        from expected_content import validate as validate_expected_content
        validate_expected_content(path,r)
        from expected_office import validate as validate_expected_office
        validate_expected_office(path,r)
        from expected_pdf import validate as validate_expected_pdf
        validate_expected_pdf(path,r)
        from expected_containers import validate as validate_expected_containers
        validate_expected_containers(path,r)
        from occurrences import validate as validate_occurrences
        validate_occurrences(path,r)
        from content_digest import digest as content_digest
        if not r.get('content_sha256'):raise ValueError('復元内容の参照指紋がありません: '+r['path'])
        if content_digest(path.read_bytes(),path.name,r['format'])!=r['content_sha256']:raise ValueError('期待した復元内容と異なります: '+r['path'])
        fmt=r['format'];text=None
        condition=r.get('condition','')
        if r.get('expected_read_state')=='破損':
            # 破損資料に本文の正解があることにしない。
            if r['entities']:raise ValueError('破損資料の正解が未定義')
            continue
        if condition in ['ファイル名','ディレクトリ名']:
            text=path.name if condition=='ファイル名' else str(path.relative_to(inputs).parent)
        elif fmt in ['PNG','JPEG','TIFF'] and condition!='画像属性':
            with Image.open(path) as im:
                im.load()
                if im.format!=fmt:raise ValueError('画像形式の不一致')
                if condition=='複数ページ' and im.n_frames!=2:raise ValueError('複数ページがない')
            # 画像本文はOCR・目視で確認する。ここで原稿だけの一致を証明しない。
            deferred.append({'path':r['path'],'reason':'画像本文はOCR/描画確認'})
            continue
        elif fmt=='PDF-image' or condition in ['image','embedded-image','image-pdf']:
            deferred.append({'path':r['path'],'reason':'内包画像の文字はOCR/描画確認'})
            continue
        else:
            from extract import extract
            text=extract(path.read_bytes(),path.name)
        if text is not None:
            normalize=lambda t:''.join(t.split())
            for e in r['entities']:
                if normalize(e['value']) not in normalize(text):raise ValueError('対象値の欠落: '+r['path']+' '+e['value'])
            checked+=1
    directories=json.loads((root/'ground_truth/directories.json').read_text())
    rowmap={r['path']:r for r in rows}
    for directory in directories:
        folder=inputs/directory['path']
        if not folder.resolve().is_relative_to(inputs.resolve()):raise ValueError('範囲外のディレクトリ')
        if not folder.is_dir():raise ValueError('ディレクトリが実在しません: '+directory['path'])
        actual_members={p.relative_to(inputs).as_posix() for p in folder.rglob('*') if p.is_file()}
        if actual_members!=set(directory['files']):raise ValueError('配下ファイルの集合が違います: '+directory['path'])
        if any(rowmap[p]['positive'] for p in actual_members)!=directory['positive']:raise ValueError('ディレクトリの内容正解が違います')
    actual={p.relative_to(inputs).as_posix() for p in inputs.rglob('*') if p.is_file()}
    if actual!=paths:raise ValueError('台帳と実配置に差異')
    total=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if total>660_000_000:raise ValueError('許容上限660MB超過')
    result={'files':len(rows),'bytes':total,'text_checked':checked,
            'content_checks_pending':deferred,
            'note':'台帳・形式検証済み。本文を検証していない形式は別途検証が必要。'}
    print(json.dumps(result,ensure_ascii=False))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True)
    verify(p.parse_args().dataset)
