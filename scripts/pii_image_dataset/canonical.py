"""暗号化以外の生成物の保存日時等を固定する。"""
import io
import hashlib
from pathlib import PurePosixPath
from lxml import etree
import re
import zipfile
from pathlib import Path


def normalize_package(path):
    # Officeは作成日時とZIP格納時刻を固定。暗号化コンテナーには適用しない。
    if path.suffix.lower() not in ['.docx','.xlsx','.pptx','.xlsm','.xlsb']:
        return
    try:
        with zipfile.ZipFile(path) as z:
            parts={n:z.read(n) for n in z.namelist()}
    except zipfile.BadZipFile:return
    # 関係IDは生成器がランダムに付ける場合がある。参照を保って決定的なIDへ置換する。
    for relname in sorted(n for n in parts if n.endswith('.rels')):
        relpath=PurePosixPath(relname)
        owner='' if relname=='_rels/.rels' else str(relpath.parent.parent/relpath.name[:-5])
        if owner and not owner.endswith('.xml'):continue  # BIFF12の参照IDは変更しない。
        relations=etree.fromstring(parts[relname])
        mapping={}
        for index,relation in enumerate(relations):
            original=relation.get('Id')
            if not original:continue
            key=relname+'|'+str(index)+'|'+relation.get('Type','')+'|'+relation.get('Target','')
            replacement='rId'+hashlib.sha256(key.encode()).hexdigest()[:16]
            mapping[original]=replacement;relation.set('Id',replacement)
        parts[relname]=etree.tostring(relations,encoding='utf-8',xml_declaration=True)
        if owner in parts:
            document=etree.fromstring(parts[owner])
            for element in document.iter():
                for key,value in list(element.attrib.items()):
                    if value in mapping and (key.startswith('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}') or key=='{urn:schemas-microsoft-com:office:office}relid'):
                        element.set(key,mapping[value])
            parts[owner]=etree.tostring(document,encoding='utf-8',xml_declaration=True)
    core='docProps/core.xml'
    if core in parts:
        raw=parts[core].decode('utf-8')
        raw=re.sub(r'(<dcterms:(?:created|modified)[^>]*>).*?(</dcterms:(?:created|modified)>)',r'\g<1>2000-01-01T00:00:00Z\2',raw)
        parts[core]=raw.encode()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(parts.items()):
            entry=zipfile.ZipInfo(name,(2000,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o600<<16
            z.writestr(entry,raw)
    # 4KiB未満のOfficeでは暗号化ライブラリの小容量ストリーム処理に失敗する。
    # ZIPの正規の無圧縮方式で保存し、本文を変えず通常ストリームのサイズへ広げる。
    if path.suffix.lower()=='.xlsx' and len(buf.getvalue())<4096:
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
            for name,raw in sorted(parts.items()):
                entry=zipfile.ZipInfo(name,(2000,1,1,0,0,0));entry.compress_type=zipfile.ZIP_STORED;entry.external_attr=0o600<<16
                z.writestr(entry,raw)
        if len(buf.getvalue())<4096:raise ValueError('小容量XLSXを暗号化可能な構造へ保存できません')
    path.write_bytes(buf.getvalue())


def normalize_zip(path):
    if path.suffix.lower()!='.zip' or path.name.endswith('.zip64.zip') or not zipfile.is_zipfile(path):return
    with zipfile.ZipFile(path) as source:
        if any(i.flag_bits & 1 for i in source.infolist()):return
        parts=[(i.filename,source.read(i.filename),i.compress_type) for i in source.infolist()]
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as target:
        for name,raw,method in parts:
            entry=zipfile.ZipInfo(name,(2000,1,1,0,0,0));entry.compress_type=method;entry.external_attr=0o600<<16;target.writestr(entry,raw)
    path.write_bytes(buf.getvalue())
