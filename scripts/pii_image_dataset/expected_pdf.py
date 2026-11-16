"""PDFの各格納面を、原稿と条件から作る期待値へ照合する。"""
import fitz


def validate(path,row):
    if row['format'] not in ['PDF','PDF-text','PDF-image','PDF-protected']:return
    with fitz.open(path) as pdf:
        if pdf.needs_pass:pdf.authenticate('DlpTest-2026')
        text=row['text'];condition=row.get('condition','本文')
        expected=[text]
        if row['format']=='PDF-image' or condition in ['annotation','attachment']:expected=['']
        elif condition=='form':expected=['登録用フォーム'+text]
        elif condition=='multipage':expected=[text]*3
        elif condition=='mixed':expected=[text,'',text]
        elif condition=='last-page':expected=['資料の案内','資料の案内',text]
        norm=lambda value:''.join(value.split())
        if [norm(page.get_text()) for page in pdf]!=[norm(value) for value in expected]:
            raise ValueError('PDF本文が原稿からの期待値と異なります: '+row['path'])
        for key,value in pdf.metadata.items():
            if key not in ['format','encryption'] and value:
                raise ValueError('PDFに期待しない属性があります: '+row['path'])
        annotations=[str(a.info.get('content','')) for page in pdf for a in page.annots() or []]
        widgets=[str(w.field_value) for page in pdf for w in page.widgets() or []]
        if annotations!=([text] if condition=='annotation' else []):raise ValueError('PDF注釈が期待値と異なります')
        if widgets!=([text] if condition=='form' else []):raise ValueError('PDFフォームが期待値と異なります')
        if condition=='attachment':
            if norm(pdf.embfile_get(0).decode('utf-8'))!=norm(text):raise ValueError('PDF添付本文が期待値と異なります')
