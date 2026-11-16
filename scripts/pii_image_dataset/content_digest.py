"""信頼する正解側で、復元内容の参照指紋を保持する。改ざん耐性の署名ではない。"""
import hashlib
import io
import json
from PIL import Image
from extract import extract


def digest(data,name,kind):
    if kind in ['PNG','JPEG','TIFF']:
        frames=[]
        with Image.open(io.BytesIO(data)) as image:
            for k in range(getattr(image,'n_frames',1)):
                image.seek(k)
                frames.append([image.size,hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()])
            info={key:hashlib.sha256(value).hexdigest() if isinstance(value,bytes) else str(value) for key,value in image.info.items()}
        text=json.dumps([frames,info],ensure_ascii=False,sort_keys=True)
    elif kind=='invalid':return hashlib.sha256(data).hexdigest()
    else:
        from verify_repro import semantic
        # 本文抽出が見ない画像・Office部品も参照内容に含める。
        text=json.dumps([extract(data,name),semantic(data,name)],ensure_ascii=False,sort_keys=True)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
