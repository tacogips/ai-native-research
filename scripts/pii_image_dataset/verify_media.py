#!/usr/bin/env python3
"""内包画像を元画像と画素単位で照合し、文字抽出の検証と区別する。"""
import argparse
import io
import json
import zipfile
from pathlib import Path

import fitz
from PIL import Image, ImageChops


def verify(root):
    rows=json.loads((root/'ground_truth/files.json').read_text())
    source={r['source_id']:r for r in rows if r['format']=='PNG' and r['path'].startswith('files/')}
    checked=[]
    for r in rows:
        condition=r.get('condition','')
        if r['format']!='PDF-image' and condition not in ['image','embedded-image','multipage','mixed','複数ページ','image-pdf']:
            continue
        path=root/'drive_upload'/r['path']
        expected=Image.open(root/'drive_upload'/source[r['source_id']]['path']).convert('RGB')
        images=[]
        if path.suffix=='.zip':
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if not member.endswith('.pdf'):continue
                    pdf=fitz.open(stream=archive.read(member),filetype='pdf')
                    for page in pdf:
                        for item in page.get_images():
                            data=pdf.extract_image(item[0])['image']
                            images.append(Image.open(io.BytesIO(data)).convert('RGB'))
                    pdf.close()
        elif path.suffix=='.pdf':
            pdf=fitz.open(path)
            for page in pdf:
                for item in page.get_images():
                    data=pdf.extract_image(item[0])['image']
                    images.append(Image.open(io.BytesIO(data)).convert('RGB'))
            pdf.close()
            if condition=='multipage':continue  # 文字だけの複数ページは本文の検証へ。
        elif path.suffix in ['.xlsx','.docx','.pptx']:
            with zipfile.ZipFile(path) as z:
                for member in z.namelist():
                    if '/media/' in member and member.lower().endswith(('.png','.jpg','.jpeg','.tiff')):
                        images.append(Image.open(io.BytesIO(z.read(member))).convert('RGB'))
        elif path.suffix=='.tiff':
            im=Image.open(path)
            for k in range(im.n_frames):im.seek(k);images.append(im.convert('RGB'))
        if not images:raise ValueError('内包画像がない: '+r['path'])
        if not all(im.size==expected.size and ImageChops.difference(im,expected).getbbox() is None for im in images):raise ValueError('内包画像の画素が元資料と異なる: '+r['path'])
        checked.append(r['path'])
    print(json.dumps({'embedded_media_checked':len(checked),'files':checked},ensure_ascii=False))
    return checked


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True)
    verify(p.parse_args().dataset)
