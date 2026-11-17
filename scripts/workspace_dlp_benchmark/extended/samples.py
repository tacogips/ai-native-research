"""v3の陽性・陰性の本文。値はすべて独自の架空例。

各項目は値3種（開発1・評価2）×文脈3種（見出しあり・見出しなしの文・表）の陽性と、
項目固有の陰性・境界例、全項目共通の空欄・伏字を持つ。expected=Noneは判断保留で主指標から除く。
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset import individual_check_digit, luhn_append  # noqa: E402

NAMES = ['山田 太郎', '佐藤 花子', '鈴木 次郎', '高橋 美咲', '伊藤 健太', '渡辺 陽子']


def _digits(key, n):
    raw = hashlib.sha256(('v3:' + key).encode()).hexdigest()
    return ''.join(str(int(c, 16) % 10) for c in raw)[:n]


def _hex(key, n):
    return (hashlib.sha256(('v3hex:' + key).encode()).hexdigest() * 3)[:n]


def _b64(key, n):
    alphabet = './ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    raw = hashlib.sha512(('v3b64:' + key).encode()).digest() * 2
    return ''.join(alphabet[b % 64] for b in raw)[:n]


def _letters(key, n):
    return ''.join(chr(ord('A') + int(c, 16) % 26) for c in _hex(key, n))


def values(item):
    """(見出し, 値, 見出しなしの文の雛形)の3組。雛形の{n}は氏名。"""
    v = []
    for i in range(3):
        k = f'{item}-{i}'
        if item == 'individual':
            p = _digits(k, 11); val = p + individual_check_digit(p)
            v.append(('個人番号', val, '{n}さんの番号は ' + val + ' です。'))
        elif item == 'license':
            val = _digits(k, 12); v.append(('運転免許証番号', val, '{n}さんの登録番号は ' + val + ' です。'))
        elif item == 'passport':
            val = ['TR', 'TS', 'TZ'][i] + _digits(k, 7); v.append(('旅券番号', val, '{n}さんの番号は ' + val + ' です。'))
        elif item == 'residence_card':
            val = _letters(k + 'a', 2) + _digits(k, 8) + _letters(k + 'b', 2)
            v.append(('在留カード番号', val, '{n}さんのカードの番号は ' + val + ' です。'))
        elif item == 'health_insurance':
            val = f'記号 {_digits(k, 4)} 番号 {_digits(k + "n", 3)}'
            v.append(('保険証', val + '（枝番 0' + str(i + 1) + '）', '{n}さんの資格は保険者番号 ' + _digits(k + 'h', 8) + ' で確認した。'))
        elif item == 'pension':
            val = _digits(k, 4) + '-' + _digits(k + 'p', 6); v.append(('基礎年金番号', val, '{n}さんの年金の番号は ' + val + ' です。'))
        elif item == 'employment_insurance':
            val = f'{_digits(k, 4)}-{_digits(k + "e", 6)}-{_digits(k + "c", 1)}'
            v.append(('被保険者番号', val, '{n}さんの雇用保険の番号は ' + val + ' です。'))
        elif item == 'card':
            val = luhn_append('4' + _digits(k, 14)); val = ' '.join(val[j:j + 4] for j in range(0, 16, 4))
            v.append(('カード番号', val, '{n}さんの決済に ' + val + ' を使った。'))
        elif item == 'bank':
            val = '架空見本銀行 試験支店 普通 ' + _digits(k, 7)
            v.append(('振込先口座', val, '{n}さんへの振込は ' + val + ' へ行う。'))
        elif item == 'assets':
            val = ['普通預金残高 3,482,000円', '見本電機の保有株式 1,200株（評価額 4,560,000円）', '住宅ローン残高 18,400,000円'][i]
            v.append(('資産', val, '{n}さんの' + val + '。'))
        elif item == 'annual_income':
            val = ['年収 520万円', '給与支給総額 6,480,000円', '年間所得 3,900,000円'][i]
            v.append(('所得', val, '{n}さんの' + val + '。'))
        elif item == 'private_insurance':
            val = f'証券番号 LP-{_digits(k, 4)}-{_digits(k + "s", 5)}、死亡保険金 2,000万円'
            v.append(('保険契約', val, '{n}さんは架空生命の終身保険に加入し、受取人：配偶者としている。'))
        elif item == 'job_history':
            val = ['2015年4月 見本工業株式会社 入社', '2020年3月 架空商事株式会社 退社', '2018年10月 試験物流へ転職'][i]
            v.append(('職歴', val, '{n}さんは' + ['2015年に見本工業へ入社した', '2020年に架空商事を退社した', '2018年に試験物流へ転職した'][i] + '。'))
        elif item == 'education':
            val = ['2011年3月 架空大学工学部 卒業', '2009年3月 見本高等学校 卒業', '2016年3月 試験大学大学院 修了'][i]
            v.append(('学歴', val, '{n}さんは' + val.split(' ', 1)[1] + 'した。'))
        elif item == 'employer':
            val = ['見本商事株式会社 営業部', '架空電機株式会社 品質管理課', '試験運輸有限会社 本社'][i]
            v.append(('勤務先', val, '{n}さんは' + val.split(' ')[0] + 'に勤務している。'))
        elif item == 'family':
            val = ['配偶者と長男（8歳）、長女（5歳）の4人家族', '扶養親族 2人（父・母と同居）', '配偶者と次男（3歳）'][i]
            v.append(('家族構成', val, '{n}さんは' + val + 'である。'))
        elif item == 'medical_history':
            val = ['糖尿病（2019年に診断、通院中）', 'うつ病で休職中', '高血圧で降圧薬を処方'][i]
            v.append(('病歴', val, '{n}さんは' + ['2019年に糖尿病と診断され通院している', 'うつ病のため休職している', '高血圧の治療薬を処方されている'][i] + '。'))
        elif item == 'health_checkup':
            val = ['血圧 152/96、判定：要精密検査', 'HbA1c 7.2%、要再検査', 'BMI 31.4、特定保健指導の対象'][i]
            v.append(('健康診断', val, '{n}さんの今年の健診は' + val + 'であった。'))
        elif item == 'disability':
            val = ['身体障害者手帳 4級（聴覚障害）', '療育手帳 B2', '精神障害者保健福祉手帳 2級'][i]
            v.append(('障害', val, '{n}さんは' + ['聴覚障害がある', '知的障害と診断されている', '発達障害の診断がある'][i] + '。'))
        elif item == 'race':
            val = ['黒人（本人申告）', 'アイヌ民族（本人申告）', '朝鮮民族（本人申告）'][i]
            v.append(('民族', val, '{n}さんは自身が' + val.split('（')[0] + 'であると申告した。'))
        elif item == 'creed':
            val = ['キリスト教（本人申告）', '架空党（党員）', '仏教（本人申告）'][i]
            v.append(('信仰', val, '{n}さんは' + ['キリスト教の信者である', '架空党の党員である', '仏教に入信している'][i] + '。'))
        elif item == 'social_status':
            val = ['被差別部落の出身（本人申告）', '部落出身であると相談', '被差別部落の出身と記載'][i]
            v.append(('相談内容', val, '{n}さんから被差別部落の出身であるとの申告があった。'))
        elif item == 'criminal_record':
            val = ['窃盗罪で懲役1年、執行猶予3年（2018年）', '傷害罪で罰金刑（2016年）', '詐欺罪で有罪判決（2021年）'][i]
            v.append(('前科', val, '{n}さんは' + val + 'を受けた。'))
        elif item == 'criminal_procedure':
            val = ['被疑者として逮捕され、同年6月に起訴された', '少年審判で保護観察処分', '書類送検された（2024年）'][i]
            v.append(('手続記録', val, '{n}さんは' + val + '。'))
        elif item == 'crime_victim':
            val = ['特殊詐欺の被害を受け、被害届を提出', 'ストーカーの被害を相談', '空き巣の被害に遭った'][i]
            v.append(('被害記録', val, '{n}さんは' + val + '。'))
        elif item == 'password_plain':
            val = ['Kx7#mQ2vR9', 'Hanako2026!', 'blue-river-4821'][i]
            v.append(('パスワード', val, ['DB_PASSWORD=' + val, '{n}さんの初期 password: ' + val, 'Wi-Fi pwd=' + val][i]))
        elif item == 'password_hash':
            val = ['$2b$12$' + _b64(k, 53), '$argon2id$v=19$m=65536,t=3,p=4$' + _b64(k, 22) + '$' + _b64(k + 'h', 43),
                   'pbkdf2_sha256$600000$' + _b64(k, 12) + '$' + _b64(k + 'h', 44)][i]
            v.append(('password_hash', val, '{n}:' + val + ':19000:0:99999:7:::'))
        elif item == 'email':
            val = f'user{_digits(k, 3)}.sample@example.test'; v.append(('メールアドレス', val, '{n}さんの連絡先は ' + val + ' です。'))
        elif item == 'phone':
            val = ['090', '080', '070'][i] + '-' + _digits(k, 4) + '-' + _digits(k + 'p', 4)
            v.append(('電話番号', val, '{n}さんには ' + val + ' へ連絡する。'))
        elif item == 'address':
            val = ['東京都架空市見本町1丁目2番3号', '大阪府試験市例示町4-5-6', '北海道見本郡架空町7番地'][i]
            v.append(('住所', val, '{n}さんは' + val + 'に住んでいる。'))
        elif item == 'name':
            val = NAMES[i + 1]; v.append(('氏名', val, '本件は担当の' + val + 'が対応する。'))
        else:
            raise KeyError(item)
    return v


# (variant, 本文, expected, 説明)。expected=Noneは判断保留。
NEGATIVES = {
    'individual': [('order', '商品注文番号 ' + _digits('o-ind', 12), 0, '12桁の注文番号')],
    'license': [('order', '受付番号 ' + _digits('o-lic', 12), 0, '12桁の受付番号')],
    'passport': [('model', '製品型番 TZ' + _digits('m-pas', 7), 0, '旅券と同形式の型番')],
    'residence_card': [('serial', 'シリアル番号 AB' + _digits('s-res', 8) + 'CD', 0, '同形式の製品シリアル'),
                       ('general', '在留資格の種類と在留期間は法務省令で定められている。', 0, '制度の一般説明')],
    'health_insurance': [('rate', '健康保険料率は10.00%、介護保険料率は1.60%。', 0, '保険料率表')],
    'pension': [('part', '部品番号 ' + _digits('p-pen', 4) + '-' + _digits('p-pen2', 6), 0, '同形式の部品番号')],
    'employment_insurance': [('part', '管理番号 ' + _digits('p-emp', 4) + '-' + _digits('p-emp2', 6) + '-1', 0, '同形式の管理番号')],
    'card': [('part', '部品コード 4242-4242-4242-4243', 0, '検査数字が合わない部品コード')],
    'bank': [('stock', '倉庫管理番号 ' + _digits('s-bank', 7), 0, '銀行の語を伴わない7桁')],
    'assets': [('corporate', '当社連結の資産合計 1,234,000,000円（2025年度）', 0, '法人の資産'),
               ('product', '定期預金の金利は年0.3%です。', 0, '商品案内')],
    'annual_income': [('stat', '事務職の平均年収は380万円（統計）。', 0, '職種別の統計')],
    'private_insurance': [('pamphlet', '終身保険の保険金額は300万円から選べます。', 0, '商品案内')],
    'job_history': [('posting', '応募資格：実務経験3年以上。2026年4月入社予定の募集。', 0, '求人票')],
    'education': [('school', '架空大学工学部の入学定員は200名。卒業生の進路は製造業が多い。', 0, '学校案内')],
    'employer': [('profile', '会社概要　見本商事株式会社　設立1985年　従業員300名', 0, '個人の帰属がない会社概要')],
    'family': [('stat', '1世帯当たりの平均人員は2.2人（統計）。', 0, '世帯統計')],
    'medical_history': [('general', '糖尿病は血糖値が高い状態が続く疾患である。', 0, '疾患の一般解説'),
                        ('denial', '既往歴：なし', None, '否定。法的扱いが分かれ得る'),
                        ('family', '父が高血圧で通院している。', 1, '家族の病歴（家族本人の要配慮情報）')],
    'health_checkup': [('reference', 'HbA1cの基準値は5.6%未満とされる。', 0, '基準値の一般表'),
                       ('normal', '健診結果：異常なし', None, '異常なしの結果。法的扱いが分かれ得る')],
    'disability': [('outage', 'サーバーの通信障害が発生し、復旧した。', 0, '同じ語の別の意味'),
                   ('policy', '当社は障害者雇用促進法に基づき採用を行っている。', 0, '制度の一般説明')],
    'race': [('nationality', '国籍：日本', None, '国籍だけの記載（指針の再確認が必要）'),
             ('lecture', '民族学の講義では言語と文化の関係を扱う。', 0, '一般説明')],
    'creed': [('tour', '見本寺の拝観時間は9時から17時まで。', 0, '観光案内'),
              ('purchase', '購入記録：聖書を1冊購入', None, '推知させるだけの情報')],
    'social_status': [('position', '役職：部長', 0, '職業上の地位')],
    'criminal_record': [('law', '窃盗罪の法定刑は10年以下の懲役又は50万円以下の罰金である。', 0, '法令の解説'),
                        ('none', '犯罪歴：なし', None, '否定')],
    'criminal_procedure': [('law', '刑事訴訟法は捜査と公判の手続を定める。', 0, '法令の解説')],
    'crime_victim': [('notice', '特殊詐欺に注意しましょう。不審な電話はすぐに切ってください。', 0, '防犯の一般案内')],
    'password_plain': [('policy', 'パスワードは12文字以上にしてください。', 0, '規則の説明'),
                       ('masked', 'パスワード：********', 0, '伏字'),
                       ('placeholder', 'password=<password>', 0, '置換用の表記')],
    'password_hash': [('checksum', 'ファイルのSHA-256：' + _hex('cs', 64), 0, 'ファイルの検査値'),
                      ('commit', 'commit ' + _hex('git', 40), 0, 'gitのコミット識別子'),
                      ('digest', 'image digest sha256:' + _hex('img', 64), 0, 'コンテナイメージの識別子')],
    'email': [('none', 'メールアドレス：未登録', 0, '値なし')],
    'phone': [('none', '電話番号：未登録', 0, '値なし')],
    'address': [('move', '本社移転のお知らせ（新所在地は未定）', 0, '値なし')],
    'name': [('company', '山田製作所の製品カタログ（2026年版）', 0, '姓を含む社名')],
}
