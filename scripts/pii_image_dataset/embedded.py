"""OOXMLの埋込みパッケージ・脚注・変更用パスワードを作成する。

埋込みパッケージの関係種別はECMA-376のpackageを使う。
https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/32be961f-d71a-4812-913f-b675c79aa88a
"""
import io
import zipfile
from lxml import etree as ET

from docx import Document
import xlsxwriter
from openpyxl.utils.protection import hash_password

REL='http://schemas.openxmlformats.org/package/2006/relationships'
OFF='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def rewrite(path, parts):
    with zipfile.ZipFile(path) as z:current={n:z.read(n) for n in z.namelist()}
    current.update(parts)
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in current.items():z.writestr(name,raw)
    path.write_bytes(buf.getvalue())


def tree(path,part):
    with zipfile.ZipFile(path) as z:return ET.fromstring(z.read(part))


def create(root,pairs,register,dest):
    for r in pairs:
        sid=r['source_id']
        # Wordの脚注だけに情報を置く。
        d=Document();d.core_properties.author='';d.core_properties.last_modified_by='';d.add_paragraph('補足を確認してください。')
        p=dest('features',sid+'.footnote.docx');d.save(p)
        document=tree(p,'word/document.xml');body=document.find('{'+W+'}body')
        para=ET.Element('{'+W+'}p');run=ET.SubElement(para,'{'+W+'}r');ET.SubElement(run,'{'+W+'}footnoteReference',{'{'+W+'}id':'2'});body.insert(0,para)
        notes=ET.Element('{'+W+'}footnotes');note=ET.SubElement(notes,'{'+W+'}footnote',{'{'+W+'}id':'2'})
        for line in r['text'].splitlines():
            para=ET.SubElement(note,'{'+W+'}p');run=ET.SubElement(para,'{'+W+'}r');ET.SubElement(run,'{'+W+'}t').text=line
        rel=tree(p,'word/_rels/document.xml.rels');ET.SubElement(rel,'{'+REL+'}Relationship',{'Id':'rIdFootnotes','Type':OFF+'/footnotes','Target':'footnotes.xml'})
        ct=tree(p,'[Content_Types].xml');ET.SubElement(ct,'{'+CT+'}Override',{'PartName':'/word/footnotes.xml','ContentType':'application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml'})
        rewrite(p,{'word/document.xml':ET.tostring(document),'word/footnotes.xml':ET.tostring(notes),'word/_rels/document.xml.rels':ET.tostring(rel),'[Content_Types].xml':ET.tostring(ct)})
        register(p,r,'DOCX','脚注')
        # 変更用パスワード。本文の暗号化ではない。
        p=dest('features',sid+'.write-password.xlsx');p.write_bytes((root/'office'/f'{sid}.xlsx').read_bytes())
        workbook=tree(p,'xl/workbook.xml')
        sharing=ET.Element('{'+S+'}fileSharing',{'readOnlyRecommended':'1','userName':'','reservationPassword':hash_password('DlpTest-2026')})
        workbook.insert(0,sharing);rewrite(p,{'xl/workbook.xml':ET.tostring(workbook)})
        register(p,r,'XLSX','変更用パスワード')
        # 外側にPIIなし、内側の実XLSXにだけPIIがあるパッケージ。
        p=dest('features',sid+'.embedded-workbook.xlsx')
        w=xlsxwriter.Workbook(p);ws=w.add_worksheet('案内');ws.write('A1','埋込み資料を確認してください。');w.close()
        sheet=tree(p,'xl/worksheets/sheet1.xml')
        objects=ET.SubElement(sheet,'{'+S+'}oleObjects')
        ET.SubElement(objects,'{'+S+'}oleObject',{'progId':'Excel.Sheet.12','dvAspect':'DVASPECT_ICON','shapeId':'1025','{'+OFF+'}id':'rIdPackage'})
        ET.SubElement(sheet,'{'+S+'}legacyDrawing',{'{'+OFF+'}id':'rIdVml'})
        rel=ET.Element('{'+REL+'}Relationships')
        ET.SubElement(rel,'{'+REL+'}Relationship',{'Id':'rIdPackage','Type':OFF+'/package','Target':'../embeddings/document.xlsx'})
        ET.SubElement(rel,'{'+REL+'}Relationship',{'Id':'rIdVml','Type':OFF+'/vmlDrawing','Target':'../drawings/vmlDrawing1.vml'})
        ct=tree(p,'[Content_Types].xml')
        ET.SubElement(ct,'{'+CT+'}Override',{'PartName':'/xl/embeddings/document.xlsx','ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
        ET.SubElement(ct,'{'+CT+'}Default',{'Extension':'vml','ContentType':'application/vnd.openxmlformats-officedocument.vmlDrawing'})
        vml=b'<xml xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><v:shape id="_x0000_s1025" style="position:absolute;width:100pt;height:40pt" o:ole=""><v:textbox><div>Document</div></v:textbox></v:shape></xml>'
        rewrite(p,{'xl/worksheets/sheet1.xml':ET.tostring(sheet),'xl/worksheets/_rels/sheet1.xml.rels':ET.tostring(rel),'xl/embeddings/document.xlsx':(root/'office'/f'{sid}.xlsx').read_bytes(),'xl/drawings/vmlDrawing1.vml':vml,'[Content_Types].xml':ET.tostring(ct)})
        register(p,r,'XLSX','埋込み文書のみ',members=['xl/embeddings/document.xlsx'])
