"""生成仕様の原稿と、文字形式の実本文を独立して比較する。"""
import csv
import io
import json
from extract import extract


def validate(path,row):
    kind=row['format'];condition=row.get('condition','本文')
    if kind not in ['TXT','Markdown','CSV','TSV','JSON','JSONL','XML','HTML']:return '対象外'
    expected=row['text'];raw=path.read_bytes()
    if kind in ['TXT','Markdown']:
        actual=raw.decode(condition if condition in ['utf-16','cp932'] else 'utf-8')
        if condition in ['ファイル名','ディレクトリ名']:expected=row.get('expected_body','資料を確認してください。')
    elif kind in ['CSV','TSV']:
        actual=list(csv.reader(io.StringIO(raw.decode()),delimiter=',' if kind=='CSV' else '\t'))
        expected=([['内容','管理用の数値文字列'],[expected,'0000123'],['引用符を含む説明','"確認"']]
                  if condition=='引用符内改行・先頭0' else [[line] for line in expected.splitlines()])
    elif kind in ['JSON','JSONL']:
        if condition=='入れ子と離れた見出し':
            actual=json.loads(raw);expected={'資料':{'ページ':[{'行番号':k,'値':line} for k,line in enumerate(expected.splitlines())]}}
        else:
            expected=({'資料':expected.split('\n\n')} if condition=='複数人物' else {'内容':expected})
            if kind=='JSONL':actual=[json.loads(line) for line in raw.decode().splitlines()];expected=[expected]
            else:actual=json.loads(raw)
    else:
        actual=extract(raw,path.name)
        if condition=='非表示の要素':expected='資料の確認\n'+expected
    # 抽出経路による改行の追加だけを許し、文字の追記は許さない。
    if isinstance(actual,str) and isinstance(expected,str):
        equal=''.join(actual.split())==''.join(expected.split())
    else:equal=actual==expected
    if not equal:raise ValueError('原稿から期待した本文と異なります: '+row['path'])
    return '原稿と照合済み'
