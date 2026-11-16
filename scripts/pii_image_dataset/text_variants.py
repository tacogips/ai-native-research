"""文字表現・構造化データ・メール格納箇所の比較を作る。"""
import json
import unicodedata
from email.message import EmailMessage
import html
from generate import name_reading


def create(root,pairs,register,dest):
    for row in pairs:
        sid=row['source_id']
        # 実際の値の中へゼロ幅文字・改行を入れる。ラベルだけを変える試験にしない。
        for variant,separator in [('value-zero-width','\u200b'),('value-linebreak','\n')]:
            text=row['text'];entities=[]
            for e in row['entities']:
                value=e['value'];mid=max(1,len(value)//2)
                changed=value[:mid]+separator+value[mid:]
                text=text.replace(value,changed)
                entities.append(dict(e,value=changed,canonical_value=value))
            p=dest('features',sid+'.'+variant+'.txt');p.write_text(text,encoding='utf-8')
            register(p,dict(row,text=text,entities=entities),'TXT',variant)
        if row['positive']:
            e=next(e for e in row['entities'] if e['type']=='氏名')
            reading=name_reading(e['value'])
            kana=unicodedata.normalize('NFD',reading)
            text='氏名（カナ）：'+kana
            ent=[dict(e,value=kana,canonical_value=reading,source_value=e['value'],relation='氏名の読み')]
        else:text=unicodedata.normalize('NFD','機器のデータを確認する。');ent=[]
        p=dest('features',sid+'.nfd.txt');p.write_text(text,encoding='utf-8');register(p,dict(row,text=text,entities=ent),'TXT','Unicode NFD')
        nested={'資料':{'ページ':[{'行番号':k,'値':line} for k,line in enumerate(row['text'].splitlines())]}}
        p=dest('structured',sid+'.nested.json');p.write_text(json.dumps(nested,ensure_ascii=False),encoding='utf-8');register(p,row,'JSON','入れ子と離れた見出し')
        # CSVの引用符に入る改行、引用符自身、先頭0を含む一般番号。
        import csv
        p=dest('structured',sid+'.quoted.csv')
        with p.open('w',encoding='utf-8',newline='') as f:csv.writer(f,lineterminator='\n').writerows([['内容','管理用の数値文字列'],[row['text'],'0000123'],['引用符を含む説明','"確認"']])
        register(p,row,'CSV','引用符内改行・先頭0')
        p=dest('structured',sid+'.hidden.html');p.write_text('<!doctype html><meta charset="utf-8"><p>資料の確認</p><div hidden>'+html.escape(row['text'])+'</div>',encoding='utf-8');register(p,row,'HTML','非表示の要素')
        msg=EmailMessage();msg['Subject']='資料の確認'
        emails=[e for e in row['entities'] if e['type']=='メール']
        if emails:msg['To']=emails[0]['value']
        msg.set_content('資料を確認してください。')
        p=dest('mail',sid+'.headers.eml');p.write_bytes(msg.as_bytes())
        register(p,dict(row,text=emails[0]['value'] if emails else '',entities=emails[:1]),'EML','宛先のみ')
        msg=EmailMessage();msg['Subject']='資料の確認';msg.set_content('資料を確認してください。\n\n署名\n'+row['text'])
        p=dest('mail',sid+'.signature.eml');p.write_bytes(msg.as_bytes());register(p,row,'EML','署名・引用')
    # 複数人物を同じファイルへまとめる。派生元を両方記録する。
    positive=[r for r in pairs if r['positive']]
    negative=[r for r in pairs if not r['positive']]
    for group in [positive,negative]:
        text='\n\n'.join(r['text'] for r in group)
        entities=[e for r in group for e in r['entities']]
        p=dest('structured',group[0]['source_id']+'.multiple-persons.json')
        p.write_text(json.dumps({'資料':[r['text'] for r in group]},ensure_ascii=False),encoding='utf-8')
        record=register(p,dict(group[0],text=text,entities=entities),'JSON','複数人物')
        record['source_ids']=[r['source_id'] for r in group]
