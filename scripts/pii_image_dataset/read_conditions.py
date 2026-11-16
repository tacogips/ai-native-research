"""復号鍵の条件・入れ子と、その読取状態の正解を作成する。"""
import io
import zipfile

import py7zr
import pyzipper
from generate import dump

PASSWORD='DlpTest-2026'
OUTER_PASSWORD='Outer-Dlp-2026'


def create(root,pairs,records,register,dest):
    for r in pairs:
        sid=r['source_id']
        p=dest('archives',sid+'.plain.7z')
        with py7zr.SevenZipFile(p,'w') as archive:archive.writestr(r['text'].encode(),'document.txt')
        register(p,r,'7z','平文',members=['document.txt'])
        # ZIP内で暗号化された項目と、平文の項目が混在するもの。
        p=dest('archives',sid+'.mixed-entries.zip')
        with pyzipper.AESZipFile(p,'w',compression=pyzipper.ZIP_DEFLATED) as archive:
            archive.writestr('guide.txt','資料を確認してください。'.encode())
            archive.setpassword(PASSWORD.encode());archive.setencryption(pyzipper.WZ_AES,nbits=256)
            archive.writestr('document.txt',r['text'].encode())
        register(p,r,'ZIP-AES','平文と暗号化の項目混在',members=['guide.txt','document.txt'])
        p=dest('archives',sid+'.two-keys.zip')
        with pyzipper.AESZipFile(p,'w',compression=pyzipper.ZIP_DEFLATED,encryption=pyzipper.WZ_AES) as archive:
            archive.setpassword(OUTER_PASSWORD.encode())
            archive.write(root/'protected'/f'{sid}.encrypted.xlsx','document.xlsx')
        register(p,r,'ZIP-AES','内外で異なる鍵',members=['document.xlsx'])
    conditions=[]
    for r in records:
        encrypted=(r['format'] in ['ZIP-AES','XLSX-encrypted'] or
                   r['format']=='7z' and r.get('condition')!='平文' or
                   r.get('condition')=='zipcrypto' or
                   r['format']=='PDF-protected' and r.get('condition')=='open')
        if encrypted:
            for key,state in [('correct','完了'),('missing','復号不能'),('wrong','復号不能')]:
                conditions.append({'id':'K03' if key=='correct' else 'K04' if key=='missing' else 'K05',
                                   'path':r['path'],'keys':({'outer':key,'inner':key} if r.get('condition')=='内外で異なる鍵' else {'default':key}),'expected_read_state':('部分読取' if key!='correct' and r.get('condition')=='平文と暗号化の項目混在' else state),
                                   'content_positive':r['positive'],'pii_result_if_unread':'不明'})
            if r.get('condition')=='内外で異なる鍵':
                conditions.append({'id':'K06','path':r['path'],'keys':{'outer':'correct','inner':'missing'},
                                   'expected_read_state':'部分読取','content_positive':r['positive'],
                                   'pii_result_if_unread':'不明','note':'外側の項目名は読めるが内側本文は復号不能'})
        elif r.get('condition') in ['sheet-protection','structure-protection','変更用パスワード','permissions']:
            conditions.append({'id':'K02','path':r['path'],'keys':{},'expected_read_state':'完了','content_positive':r['positive']})
    dump(root.parent/'ground_truth/read_conditions.json',conditions)
    dump(root.parent/'ground_truth/keys.json',{'default':PASSWORD,'outer':OUTER_PASSWORD,'wrong':'Incorrect-Password'})
