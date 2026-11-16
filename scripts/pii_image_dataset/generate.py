#!/usr/bin/env python3
"""架空の日本語PII画像とDrive配置用ディレクトリを生成する。"""
import argparse
import hashlib
import json
import platform
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

# 設計上の検知分類。日本法上の確定分類や実在性を表すものではない。
FIELDS = [
    ('氏名', '氏名', '山田 太郎'), ('メール', 'メール', 'taro@example.test'),
    ('電話', '電話', '090-1234-5678'), ('住所', '住所', '東京都架空市見本町1丁目2番3号'),
    ('性別', '性別', '男性'), ('生年月日', '生年月日', '1990年4月12日'),
    ('マイナンバー', '個人番号', '123456789018'), ('会員ID', '会員ID', 'MEM-TEST-00421'),
    ('運転免許証', '運転免許証番号', '123456789012'), ('パスポート', '旅券番号', 'TS1234567'),
    ('カード番号', 'カード番号', '4242 4242 4242 4242'),
    ('銀行口座', '振込先口座', '見本銀行 試験支店 普通 0123456'),
    ('職歴', '職歴', '見本工業に入社し製造業務に従事'), ('学歴', '学歴', '架空大学工学部卒業'),
    ('年収', '年収', '520万円'), ('家族構成', '家族構成', '配偶者と子ども2人'),
    ('購買', '購入記録', '書籍を2冊購入'), ('予約', '予約記録', '宿泊施設を1泊予約'),
    ('閲覧', '閲覧記録', '商品案内ページを閲覧'), ('検索', '検索記録', '通勤用の靴を検索'),
    ('応募', '応募記録', '事務職の求人に応募'),
    ('要配慮:病歴', '病歴', '糖尿病の診断を受けた'),
    ('要配慮:障害', '障害', '聴覚障害がある'),
    ('要配慮:検査結果', '健康診断', '血糖検査で異常を指摘された'),
    ('要配慮:診療', '診療記録', '高血圧の治療薬を処方された'),
    ('要配慮:人種', '本人の申告', '人種について黒人であると申告'),
    ('要配慮:信条', '本人の申告', '宗教上の信仰は仏教であると申告'),
    ('要配慮:社会的身分', '相談記録', '被差別部落出身であるとの本人申告'),
    ('要配慮:犯罪歴', '本人の申告', '窃盗罪で有罪判決を受けた'),
    ('要配慮:犯罪被害', '相談記録', '詐欺事件の被害を受けた'),
    ('要配慮:刑事手続', '手続記録', '被疑者として逮捕された'),
    ('要配慮:少年手続', '手続記録', '少年の保護事件として審判を受けた'),
]
NEGATIVE = [
    ('製品仕様', '材質はアルミニウム', '幅は300ミリメートル'),
    ('作業手順', '部品を固定する', 'ねじを締め付ける'),
    ('空欄の申込書', '氏名：＿＿＿＿', '住所：＿＿＿＿'),
    ('空欄の支払届', '口座番号：＿＿＿＿', 'カード番号：＿＿＿＿'),
    ('健康の一般解説', '糖尿病は疾患の名称', '個別の診療事例は記載しない'),
    ('商品一覧', '机　在庫あり', '椅子　在庫あり'),
    ('空き予約枠', '午前の枠　空き', '午後の枠　空き'),
    ('制度の一般説明', '刑事手続についての一般的な解説', '特定の事件の記載はない'),
    ('機器の検査', '動作確認　正常', '外観検査　正常'),
    ('設計情報', '図面の改訂番号：REV-03', '部品コード：PART-1234-5678'),
    ('採用条件', '募集職種：事務職', '仕事内容：資料整理'),
    ('統計表', '製品の分類：工具', '年間の出荷個数：5000'),
]


SURNAME_READINGS = dict(zip(
    ['山田','佐藤','鈴木','田中','高橋','伊藤','渡辺','中村','小林','加藤','吉田','山本'],
    ['ヤマダ','サトウ','スズキ','タナカ','タカハシ','イトウ','ワタナベ','ナカムラ','コバヤシ','カトウ','ヨシダ','ヤマモト']))
GIVEN_READINGS = dict(zip(
    ['太郎','花子','次郎','美咲','健太','陽子','直人','恵美','翔太','明子'],
    ['タロウ','ハナコ','ジロウ','ミサキ','ケンタ','ヨウコ','ナオト','エミ','ショウタ','アキコ']))


def name_reading(value):
    surname,given=value.split()
    return SURNAME_READINGS[surname]+' '+GIVEN_READINGS[given]

# LIGHT計画の資料群ごとの配分。整数はFIELDS/NEGATIVEの添字。
POSITIVE_GROUPS = (
    [('C01', k) for k in list(range(6))*2 + [16,17,18,19]*2]
    + [('C02', k) for k in [6,7]*8]
    + [('C03', k) for k in [12,13]*7+[20]*2]
    + [('C04', k) for k in [14,15]*6]
    + [('C05', k) for k in [10,11]*8]
    + [('C06', k) for k in [8,9]*6]
    + [('C07', k) for k in [21,22,23,24]*3+[21,22]]
    + [('C08', k) for k in list(range(25,32))*2]
)
NEGATIVE_GROUPS = (
    [('N01', k) for k in [0,1,8]*12]
    + [('N02', k) for k in [2,3]*10]
    + [('N03',9)]*28
    + [('N04', k) for k in [4,7]*8]
    + [('N05', k) for k in [5,6,10,11]*3]
    + [('N06',None)]*8
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def generate(output, font_path, seed):
    # 既存出力を削除せず、誤った同期先指定で資料を壊さない。
    if output.exists():
        raise ValueError('出力先は存在しない新しいディレクトリを指定してください')
    font_hash = digest(font_path)
    font = ImageFont.truetype(str(font_path), 32, index=0)
    title_font = ImageFont.truetype(str(font_path), 42, index=0)
    output.mkdir(parents=True)
    inputs = output / 'drive_upload'
    files = inputs / 'files'
    files.mkdir(parents=True)
    truth = output / 'ground_truth'
    truth.mkdir()
    rng = random.Random(seed)
    cases = [(True, i) for i in range(120)] + [(False, i) for i in range(120)]
    rng.shuffle(cases)
    records = []
    for n, (positive, i) in enumerate(cases):
        case_id = f'case-{n:04d}'
        image = Image.new('RGB', (1400, 1000), 'white')
        draw = ImageDraw.Draw(image)
        # 陽性・陰性とも同じ見本表示。形式・配置をラベルの代わりにしない。
        header = '架空資料・検知試験用'
        layout = n % 6
        left = [60, 120, 80, 160, 100, 70][layout]
        top = [210, 250, 290, 230, 270, 310][layout]
        spacing = [100, 110, 120, 130, 105, 115][layout]
        if layout % 2:
            draw.rectangle((left - 15, top - 25, 1320, top + spacing * 3), outline='#999999', width=2)
        draw.text((left, 30), header, font=title_font, fill='black')
        entities = []
        lines = []
        if positive:
            group, kind_index = POSITIVE_GROUPS[i]
            kind, label, value = FIELDS[kind_index]
            # 値の変化を持たせるが、架空設定であること以外の実在性保証はしない。
            surnames = ['山田', '佐藤', '鈴木', '田中', '高橋', '伊藤', '渡辺', '中村', '小林', '加藤', '吉田', '山本']
            given = ['太郎', '花子', '次郎', '美咲', '健太', '陽子', '直人', '恵美', '翔太', '明子']
            name = surnames[i // 10] + ' ' + given[i % 10]
            if kind == 'メール':
                value = f'contact{i:03d}@example.test'
            elif kind == '電話':
                value=f'090-1234-{i:04d}'
            elif kind == 'マイナンバー':
                body='1234567'+f'{i:04d}'
                remainder=sum(int(d)*w for d,w in zip(body,[6,5,4,3,2,7,6,5,4,3,2]))%11
                check=11-remainder
                value=body+str(0 if check>=10 else check)
            elif kind == '運転免許証':value=f'{123456780000+i:012d}'
            elif kind == 'パスポート':value='TS'+f'{1000000+i:07d}'
            elif kind == '銀行口座':value=f'見本銀行 試験支店 普通 {1234000+i:07d}'
            elif kind == '会員ID':
                value = f'MEM-TEST-{i:05d}'
            elif kind == '年収':
                value = f'{320 + i * 3}万円'
            elif kind == 'カード番号':
                base='400000'+f'{i:09d}'
                digits=[int(d) for d in reversed(base+'0')]
                total=sum((d*2-9 if d*2>9 else d*2) if n%2 else d for n,d in enumerate(digits))
                pan=base+str((-total)%10)
                value=' '.join(pan[n:n+4] for n in range(0,16,4))
            elif kind == '生年月日':
                value = f'{1970 + i % 35}年{i % 12 + 1}月{i % 27 + 1}日'
            lines = [('氏名', name, '氏名')]
            if kind != '氏名':
                lines.append((label, value, kind))
            lines.append(('メール', f'person{i:03d}@example.test', 'メール'))
            if kind=='氏名':lines=[('氏名',name,'氏名')]
            elif kind=='メール':lines=[(label,value,kind)]
            elif kind in ['電話','住所','マイナンバー','会員ID','カード番号','銀行口座'] and (i//2)%2==0:
                lines=[(label,value,kind)]
            title = ['申告内容', '受付資料', '確認事項', '登録内容', '連絡票', '内容確認票', '申請控え', '照会への回答', '相談記録', '届出内容', '取扱情報一覧', '受付内容の確認'][i % 12]
            if group=='C06':
                title='運転免許証（架空見本）' if kind=='運転免許証' else '旅券（架空見本）'
                lines += [('生年月日',f'{1970+i%35}年{i%12+1}月{i%27+1}日','生年月日'),('住所','東京都架空市見本町1丁目2番3号','住所')]
                draw.rectangle((40,160,1360,940),outline='#666666',width=3)
                draw.rectangle((1080,200,1300,480),outline='#777777',width=2)
                draw.ellipse((1140,230,1240,330),fill='#aaaaaa')
                draw.rounded_rectangle((1100,340,1280,460),radius=50,fill='#aaaaaa')
        else:
            group, kind_index = NEGATIVE_GROUPS[i]
            title, a, b = NEGATIVE[kind_index if kind_index is not None else 0]
            contexts = ['仕様確認', '作業準備', '品質点検', '資料整理', '在庫確認', '手順確認', '運用案内', '設備点検', '改訂確認', '定期確認']
            title = contexts[i // 12] + '・' + title
            conditions = ['屋内で保管する', '湿気を避けて保管する', '使用後に清掃する', '部品の摩耗を確認する', '異音がないことを確認する', '梱包に破損がないことを確認する', '寸法を再確認する', '工具を所定の場所へ戻す', '説明書の版を確認する', '電源を切って点検する']
            lines = [('', a, None), ('', b + '。' + conditions[i // 12], None), ('管理記号', f'DOC-{i:04d}', None)]
        if not positive and group=='N06':
            image=Image.new('RGB',(1400,1000),'white');draw=ImageDraw.Draw(image)
            header='';title='';lines=[]
        draw.text((left, 110), title, font=font, fill='black')
        rendered = [header, title] if header or title else []
        primary_type=kind if positive else None
        y = top
        for label, value, kind in lines:
            prefix = label + '：' if label else ''
            full = prefix + value
            box = draw.textbbox((left, y), full, font=font)
            if box[2] >= 1340 or box[3] >= 940:
                raise ValueError(f'文字が領域外: {case_id}')
            draw.text((left, y), full, font=font, fill='black')
            if kind:
                x = left + draw.textlength(prefix, font=font)
                bbox = draw.textbbox((x, y), value, font=font)
                entities.append({'type': kind, 'value': value, 'bbox': list(bbox), 'person_id': f'person-{i:03d}'})
            rendered.append(full)
            y += spacing
        for ext, fmt, kwargs in [('png', 'PNG', {}), ('jpg', 'JPEG', {'quality': 95, 'subsampling': 0}),
                                 ('tiff', 'TIFF', {'compression': 'tiff_lzw'})]:
            path = files / f'{case_id}.{ext}'
            image.save(path, format=fmt, **kwargs)
            records.append({'path': path.relative_to(inputs).as_posix(), 'source_id': case_id,
                            'positive': positive, 'persona':{'person_id':f'person-{i:03d}','name':name,'reading':name_reading(name)} if positive else None, 'group':group, 'primary_type':primary_type, 'layout': layout, 'entities': [dict(e,location={'scope':'画像','frame':0,'bbox':e['bbox'],'unit':'pixel'},occurrence_id=f'occurrence-{k:04d}') for k,e in enumerate(entities)], 'text': '\n'.join(rendered),
                            'sha256': digest(path), 'format': fmt, 'width': 1400, 'height': 1000})
    # 構成の答えを名前に入れない。正解はアップロード範囲の外に保管。
    trees = inputs / 'trees'
    configs = [('tree-01', False), ('tree-02', True), ('tree-03', None)]
    directory_truth = []
    for folder, selection in configs:
        target = trees / folder
        target.mkdir(parents=True)
        candidates = [r for r in records if r['format'] == 'PNG' and r['path'].startswith('files/')]
        if selection is None:
            selected = [r for r in candidates if r['positive']][:6] + [r for r in candidates if not r['positive']][:6]
        else:
            selected = [r for r in candidates if r['positive'] == selection][:12]
        paths = []
        for k, r in enumerate(selected):
            sub = target / ('nested' if k % 2 else 'root')
            sub.mkdir(exist_ok=True)
            dest = sub / f'item-{k:03d}.png'
            shutil.copyfile(inputs / r['path'], dest)
            clone = dict(r, path=dest.relative_to(inputs).as_posix())
            records.append(clone)
            paths.append(clone['path'])
        directory_truth.append({'path': target.relative_to(inputs).as_posix(), 'files': paths,
                                'positive': any(r['positive'] for r in records if r['path'] in paths)})
    (trees / 'tree-04').mkdir()
    directory_truth.append({'path': 'trees/tree-04', 'files': [], 'positive': False})
    total = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    dump(truth / 'files.json', records)
    dump(truth / 'directories.json', directory_truth)
    dump(output / 'generation.json', {'schema': 1, 'seed': seed, 'font_sha256': font_hash,
         'pillow': pillow_version, 'python': platform.python_version(), 'source_documents': 240,
         'input_files': len(records), 'image_degradation': False, 'layouts': 6, 'personas': 120, 'distinct_person_names': len({e['value'] for r in records for e in r['entities'] if e['type']=='氏名'}),
         'scope': 'LIGHT画像部分。全形式LIGHTの完成を意味しない。'})
    # 台帳込みの容量を最終確認。
    total = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    if total > 660_000_000:
        raise ValueError(f'許容上限660MB超過: {total}')
    if total > 600_000_000:
        print(f'容量目安600MBを超過: {total}バイト（生成は継続）')
    print(json.dumps({'output': str(output), 'files': len(records), 'bytes': total}, ensure_ascii=False))


def verify(output):
    inputs = output / 'drive_upload'
    rows = json.loads((output / 'ground_truth/files.json').read_text())
    seen = set()
    for r in rows:
        path = inputs / r['path']
        if not path.resolve().is_relative_to(inputs.resolve()) or r['path'] in seen:
            raise ValueError('経路が不正または重複')
        seen.add(r['path'])
        assert digest(path) == r['sha256'], path
        with Image.open(path) as im:
            im.load()
            assert im.format == r['format'] and im.size == (1400, 1000)
        assert r['positive'] == bool(r['entities'])
        for e in r['entities']:
            x0, y0, x1, y1 = e['bbox']
            assert 0 <= x0 < x1 < 1400 and 0 <= y0 < y1 < 1000
            assert e['value'] in r['text']
    actual = {p.relative_to(inputs).as_posix() for p in inputs.rglob('*') if p.is_file()}
    assert actual == seen
    source = {r['source_id']: r for r in rows}
    assert len(source) == 240 and sum(r['positive'] for r in source.values()) == 120
    assert len({r['text'] for r in source.values()}) >= 233
    from collections import Counter
    assert Counter(r['group'] for r in source.values()) == {'C01':20,'C02':16,'C03':16,'C04':12,'C05':16,'C06':12,'C07':14,'C08':14,'N01':36,'N02':20,'N03':28,'N04':16,'N05':12,'N06':8}
    assert len({r['persona']['person_id'] for r in source.values() if r['positive']}) == 120
    for positive in (True, False):
        assert {r['layout'] for r in source.values() if r['positive'] == positive} == set(range(6))
    assert {k for k, _, _ in FIELDS} <= {e['type'] for r in rows for e in r['entities']}
    for d in json.loads((output / 'ground_truth/directories.json').read_text()):
        members = [r for r in rows if r['path'].startswith(d['path'] + '/')]
        assert {r['path'] for r in members} == set(d['files'])
        assert any(r['positive'] for r in members) == d['positive']
    total = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    if total > 660_000_000:
        raise ValueError(f'許容上限660MB超過: {total}')
    if total > 600_000_000:
        print(f'容量目安600MBを超過: {total}バイト')
    print('検証成功: 実形式・ハッシュ・240元文書・全分類・陰性・配置・容量')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate', 'verify'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--font', type=Path)
    parser.add_argument('--seed', type=int, default=20261113)
    args = parser.parse_args()
    if args.command == 'verify':
        verify(args.output)
    else:
        if not args.font:
            parser.error('generateには--fontが必要です')
        generate(args.output, args.font, args.seed)
