"""Astraが再現した検証の抜け穴を、隔離した小さな資料で検査する。"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from generate import digest,dump
from content_digest import digest as content_digest
from verify_all import verify


class ValidationTests(unittest.TestCase):
    def fixture(self,temp):
        root=Path(temp);(root/'drive_upload').mkdir();(root/'ground_truth').mkdir()
        p=root/'drive_upload/item.txt';p.write_text('機器の仕様を確認する。',encoding='utf-8')
        row={'path':'item.txt','source_id':'test','positive':False,'entities':[],
             'text':p.read_text(),'format':'TXT','condition':'本文','sha256':digest(p),
             'content_sha256':content_digest(p.read_bytes(),p.name,'TXT')}
        dump(root/'ground_truth/files.json',[row]);dump(root/'ground_truth/directories.json',[])
        return root,p,row
    def test_unchanged_negative_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root,p,row=self.fixture(temp)
            with contextlib.redirect_stdout(io.StringIO()):result=verify(root)
            self.assertEqual(result['text_checked'],1)
    def test_negative_injection_even_with_new_file_hash_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root,p,row=self.fixture(temp)
            p.write_text(p.read_text()+'\n氏名：山田 太郎',encoding='utf-8');row['sha256']=digest(p)
            dump(root/'ground_truth/files.json',[row])
            with self.assertRaisesRegex(ValueError,'復元内容|期待した本文'):verify(root)
    def test_text_disguised_as_docx_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root,p,row=self.fixture(temp);target=p.with_suffix('.docx');p.rename(target)
            row.update(path=target.name,format='DOCX',sha256=digest(target))
            dump(root/'ground_truth/files.json',[row])
            with self.assertRaisesRegex(ValueError,'Office形式'):verify(root)
    def test_negative_injection_with_recomputed_content_hash_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root,p,row=self.fixture(temp)
            p.write_text(p.read_text()+'\n氏名：山田 太郎',encoding='utf-8')
            row.update(sha256=digest(p),content_sha256=content_digest(p.read_bytes(),p.name,'TXT'))
            dump(root/'ground_truth/files.json',[row])
            with self.assertRaisesRegex(ValueError,'期待した本文'):verify(root)
    def test_pdf_unregistered_page_occurrences_fail(self):
        import fitz
        from occurrences import validate
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'item.pdf';pdf=fitz.open()
            for _ in range(3):pdf.new_page().insert_text((30,40),'TokenA')
            pdf.save(p);pdf.close()
            row={'path':p.name,'format':'PDF','condition':'multipage','entities':[{'value':'TokenA','location':{'scope':'文字','page':0}}]}
            with self.assertRaisesRegex(ValueError,'出現数'):validate(p,row)
    def test_pdf_unexpected_image_fails_even_with_new_hashes(self):
        import fitz
        from PIL import Image
        from formats import validate
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'item.pdf';pdf=fitz.open();page=pdf.new_page()
            image=io.BytesIO();Image.new('RGB',(10,10),'white').save(image,format='PNG')
            page.insert_image(fitz.Rect(20,20,60,60),stream=image.getvalue());pdf.save(p);pdf.close()
            with self.assertRaisesRegex(ValueError,'画像個数'):validate(p,{'path':p.name,'format':'PDF-text'})
    def test_negative_office_unexpected_text_fails(self):
        from docx import Document
        from expected_office import validate
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'item.docx';document=Document();document.add_paragraph('機器の仕様');document.add_paragraph('氏名：山田 太郎');document.save(p)
            row={'path':p.name,'format':'DOCX','positive':False,'text':'機器の仕様'}
            with self.assertRaisesRegex(ValueError,'期待しない文字'):validate(p,row)
    def test_tiff_missing_frame_entities_fail(self):
        from PIL import Image
        from occurrences import validate
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'item.tiff';image=Image.new('RGB',(10,10),'white');image.save(p,save_all=True,append_images=[image.copy()])
            row={'path':p.name,'format':'TIFF','condition':'複数ページ','entities':[{'type':'氏名','value':'架空例','location':{'frame':0}}]}
            with self.assertRaisesRegex(ValueError,'対象集合'):validate(p,row)
    def test_negative_archive_initial_contamination_fails(self):
        import zipfile
        from expected_containers import validate
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'item.zip'
            with zipfile.ZipFile(p,'w') as archive:archive.writestr('document.txt','機器の仕様\n氏名：山田 太郎')
            row={'path':p.name,'format':'ZIP','positive':False,'text':'機器の仕様'}
            with self.assertRaisesRegex(ValueError,'期待値'):validate(p,row)
    def test_json_key_contamination_fails(self):
        from expected_content import validate
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'item.json';p.write_text(json.dumps({'山田 太郎':'機器の仕様'},ensure_ascii=False))
            with self.assertRaisesRegex(ValueError,'期待した本文'):validate(p,{'path':p.name,'format':'JSON','text':'機器の仕様'})
    def test_deleted_revision_contamination_fails(self):
        import zipfile
        from docx import Document
        from expected_office import validate
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'item.docx';document=Document();document.add_paragraph('機器の仕様');document.save(p)
            with zipfile.ZipFile(p) as package:parts={name:package.read(name) for name in package.namelist()}
            parts['word/document.xml']=parts['word/document.xml'].replace(b'</w:body>','<w:p><w:del><w:r><w:delText>氏名：山田 太郎</w:delText></w:r></w:del></w:p></w:body>'.encode())
            with zipfile.ZipFile(p,'w') as package:
                for name,data in parts.items():package.writestr(name,data)
            with self.assertRaisesRegex(ValueError,'期待しない文字'):validate(p,{'path':p.name,'format':'DOCX','positive':False,'text':'機器の仕様'})
    def test_nonexistent_empty_directory_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root,p,row=self.fixture(temp)
            dump(root/'ground_truth/directories.json',[{'path':'missing','files':[],'positive':False}])
            with self.assertRaisesRegex(ValueError,'実在しません'):verify(root)
    def test_wrong_directory_membership_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root,p,row=self.fixture(temp)
            dump(root/'ground_truth/directories.json',[{'path':'.','files':[],'positive':False}])
            with self.assertRaisesRegex(ValueError,'集合'):verify(root)


if __name__=='__main__':unittest.main()
