"""日本語は指定フォントを埋め込み、ASCIIの文字対応表も保持する。"""
from pathlib import Path
import re
import fitz

FONT=None
FONT_METRICS=None


def configure(path):
    global FONT,FONT_METRICS
    path=Path(path)
    font=fitz.Font(fontfile=str(path))
    if not all(font.has_glyph(ord(c)) for c in '氏名住所病歴太郎'):raise ValueError('日本語グリフが不足しています')
    FONT=path;FONT_METRICS=font


def write(page,point,text,**kwargs):
    if FONT is None:raise ValueError('PDF用フォントが未設定です')
    page.insert_font(fontname='PIIJP',fontfile=str(FONT))
    fontsize=kwargs.get('fontsize',11)
    rotation=kwargs.get('rotate',0)
    x,y=point
    # CJKフォントではASCIIのハイフン等が同一グリフにまとまり、
    # ToUnicodeで別の文字になることがある。ASCIIは標準フォントへ分ける。
    for run in re.findall(r'[\x00-\x7f]+|[^\x00-\x7f]+',text):
        ascii_run=run.isascii()
        options=dict(kwargs,fontname='helv' if ascii_run else 'PIIJP')
        page.insert_text((x,y),run,**options)
        width=fitz.get_text_length(run,fontname='helv',fontsize=fontsize) if ascii_run else FONT_METRICS.text_length(run,fontsize=fontsize)
        if rotation==90:y-=width
        elif rotation==180:x-=width
        elif rotation==270:y+=width
        else:x+=width
