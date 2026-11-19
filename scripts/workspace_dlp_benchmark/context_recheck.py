"""Drive DLP用の文脈対照を再生成し、既存の独自規則をRE2で採点する。"""
import argparse
import hashlib
import json
import string
from collections import defaultdict
from pathlib import Path

from common import input_file
from dataset import _tokens, individual_check_digit, individual_valid, luhn_append, wrong_check_digit
from improvement import evaluate_context as local
from rules import DETECTORS, THRESHOLDS
from scoring import metrics

VERSION = 'context-recheck-v1'
FAMILIES = 64
STANDARD = {
    **DETECTORS, 'iban': 'IBAN_CODE', 'swift': 'SWIFT_CODE',
    'name': 'NAME_OCCURRENCE', 'password_plain': 'PASSWORD', 'race': 'ETHNIC_GROUP',
}
SOURCES = {
    'email': ('連絡先メールアドレス', '返信先', 'ログイン名の入力例'),
    'phone': ('電話番号', '折返し先', '配送伝票番号'),
    'bank': ('架空見本銀行 普通預金 口座番号', '振込先の口座', '在庫管理番号'),
    'individual': ('マイナンバー（個人番号）', '個人番号の申告欄', '注文番号'),
    'license': ('運転免許証番号', '免許証の登録番号', '配送伝票番号'),
    'passport': ('旅券番号', '渡航書類の登録番号', '製品番号'),
    'card': ('クレジットカード番号', '決済カードの番号', '在庫管理番号'),
    'iban': ('IBAN', '海外送金先口座', '出荷管理番号'),
    'swift': ('SWIFTコード', '受取銀行の識別コード', '保守機材の型式'),
    'name': ('氏名', '申請した人', '架空小説の人物名の入力例'),
    'password_plain': ('パスワード', '認証に使う合言葉', '製品のシリアル番号'),
}
STANDARD_ONLY = set(STANDARD) | {'medical_history', 'clinical_care'}
COLLISIONS = {
    'individual': ('運転免許証番号', 'license'),
    'license': ('マイナンバー（個人番号）', 'individual'),
    'passport': ('契約番号', None),
    'bank': ('社員番号', None),
    'card': ('注文番号', None),
    'iban': ('国際取引の照会番号', None),
    'swift': ('機材型式', None),
}

SENSITIVE = {
    'medical_history': ('病歴', [
        ('喘息の治療を継続', '吸入薬を継続するよう医師から指示された', '病歴の記載例を確認'),
        ('糖尿病と診断された', '血糖値を下げる薬を医療機関で処方された', '糖尿病の患者数に関する統計'),
        ('心筋梗塞で入院した', '心臓の血管が詰まり救急搬送された', '心筋梗塞の初期症状を説明する教材'),
        ('高血圧のため通院', '降圧薬の処方を受けている', '高血圧の治療方針の一般的な解説'),
    ]),
    'clinical_care': ('診療記録', [
        ('喘息と診断した。吸入薬を処方', '本日の受診で医師は吸入薬を開始した', '喘息と診断した場合の一般的な手順'),
        ('高血圧の治療を開始', '診察後に降圧剤を初めて渡した', '高血圧の治療を開始する目安'),
        ('既往歴に糖尿病。今回の診療なし', '本日の受診ではなく過去の糖尿病だけの資料', '既往歴ページの記入方法'),
        ('喘息の既往歴。今月の受診記録なし', '以前の病歴のみが共有された', '喘息の既往歴を尋ねる問診書の説明'),
    ]),
    'health_checkup': ('健康診断結果', [
        ('血圧 152/96、要再検査', '定期測定後、もう一度受診するよう通知を受けた', '要再検査は所定の基準を超えた場合の分類名'),
        ('HbA1c 7.2、要精密検査', '定期採血で血糖の指標が高く、詳しい検査を勧められた', 'HbA1c 6.0 は医療研修で使う例'),
        ('聴力検査の所見あり', '定期健診で高い音を聞き取れなかったと伝えられた', '聴力検査を受ける際の一般的な手順'),
        ('LDLコレステロール 158', '検査票では悪玉の値が基準を上回っていた', 'LDLコレステロールの基準を説明する資料'),
    ]),
    'disability': ('障害', [
        ('聴覚障害の診断を受けた', '両耳とも音声による案内を聞き取れない', 'システム障害の診断を受けた'),
        ('身体障害者手帳を交付された', '下肢に永続的な機能の制限があると申告した', '身体障害者手帳の申請方法を告知'),
        ('療育手帳を受領した', '日常の意思決定に継続的な支援が必要と認定された', '療育手帳の更新制度を紹介'),
        ('視覚障害がある', '恒常的に光を感じられず点字が必要だと回答した', '視覚障害の定義と統計を解説'),
    ]),
    'race': ('民族的出自', [
        ('アイヌ民族', '自身の民族的ルーツはアイヌだと申告した', 'アイヌ民族の文化に関する展示案内'),
        ('琉球民族と自認', '家族に受け継がれた琉球の民族的出自を申告した', '琉球の民族文化に関する展示'),
        ('マオリと本人が申告', 'アオテアロア先住民の一員であると回答した', 'マオリ語を学ぶ公開講座'),
        ('クルド系と回答', '自らをクルド人として記録してほしいと回答した', 'クルドの音楽の演奏会情報'),
    ]),
    'creed': ('信仰', [
        ('仏教を信仰している', '本人は礼拝と読経を欠かさないと答えた', '仏教を信仰していると答える演習用の手順'),
        ('イスラム教徒である', '本人はムスリムであると申告した', 'イスラム教徒の文化を学ぶ公開講座'),
        ('カトリックの信者', '本人がカトリックを信奉していると回答した', 'カトリックの信者人口の統計'),
        ('無宗教である', '本人はどの宗教も信じていないと答えた', '宗教を信じていない場合の一般的な記入法'),
    ]),
    'social_status': ('社会的身分', [
        ('被差別部落の出身と本人が申告', '本人は同和地区出身であると申告した', '被差別部落の歴史に関する公開資料'),
        ('部落出身であると本人が申告', '出生時から同和地区の出身であると回答した', '部落出身に関する歴史用語の講義'),
    ]),
    'criminal_record': ('犯罪の経歴', [
        ('窃盗で有罪判決を受けた', '確定判決を受け服役した経緯を本人が伝えた', '有罪判決の一般的な定義'),
        ('器物損壊の罰金刑', '裁判が確定し裁判所から命じられた金銭を納付済みと申告した', '罰金刑の制度を説明する教材'),
        ('有罪の前科を申告', '本人は刑事裁判の確定後に刑を終えたと答えた', '前科について質問する場合の法的論点'),
        ('懲役刑が確定した', '本人は確定した刑事判決により刑務所に収容された', '懲役と拘禁刑の用語解説'),
    ]),
    'criminal_procedure': ('刑事事件の手続', [
        ('被疑者として書類送検された', '捜査結果が検察へ送られ本人に手続が通知された', '被疑者として書類送検された場合の案内文'),
        ('少年審判を受けた', '本人について家庭裁判所で少年事件の審理が行われた', '少年審判の一般的な流れ'),
        ('逮捕され勾留された', '刑事手続で身柄を拘束されていると本人の代理人が報告した', '逮捕され勾留された場合の制度解説'),
        ('起訴された', '本人を被告人とする公判の請求が検察から行われた', '起訴された場合の連絡先案内'),
    ]),
    'crime_victim': ('犯罪被害', [
        ('窃盗の被害を受け被害届を提出した', '店で財布を盗まれたことを本人が申し出た', '被害届の提出方法を掲載した一般向け案内'),
        ('詐欺の被害に遭った', '虚偽の請求で本人の預金を振り込まされた', '一般向けに詐欺の被害を相談する窓口を説明'),
        ('暴行の被害を受けた', '見知らぬ人に殴られて負傷したと本人が申告した', '暴行の被害に遭った場合の相談手順'),
        ('盗難の被害を相談した', '本人の自転車が鍵を壊されて持ち去られた', '研修で盗難の被害を相談する手順を確認'),
    ]),
}
NAMES = (('桐生', '小日向', '早瀬', '新藤', '朝倉', '大河内', '安西', '橘'),
         ('美咲', '直樹', '理奈', '航', '杏奈', '圭一', '梓', '颯太'))


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def ascii_number(kind, family, width):
    return str(int(sha(f'{VERSION}/{kind}/{family}'), 16) % 10**width).zfill(width)


def letters(kind, family, width):
    return ''.join(string.ascii_uppercase[int(c, 16) + (i % 10)]
                   for i, c in enumerate(sha(f'{VERSION}/{kind}/{family}')[:width]))


def iban_remainder(value):
    rearranged = value[4:] + value[:4]
    return int(''.join(str(ord(c) - 55) if 'A' <= c <= 'Z' else c for c in rearranged)) % 97


def variants(kind, family):
    n = ascii_number(kind, family, 24)
    a = letters(kind, family, 8)
    if kind == 'individual':
        value = n[:11] + individual_check_digit(n[:11])
        return value, wrong_check_digit(value), f'{value[:4]} {value[4:8]} {value[8:]}'
    if kind == 'card':
        width, prefix = ((15, '34'), (16, '4'), (16, '51'), (19, '4'))[family % 4]
        value = luhn_append(prefix + n[:width-len(prefix)-1])
        return value, wrong_check_digit(value), ' '.join(value[i:i+4] for i in range(0, width, 4))
    if kind == 'license':
        value = ('30', '43', '62', '90')[family % 4] + n[:10]
        return value, value[:-1] + 'X', value[:6] + '-' + value[6:]
    if kind == 'passport':
        value = a[:2] + n[:7]
        return value, value[:-1] + 'X', value[:2] + ' ' + value[2:]
    if kind == 'bank':
        value = n[:7]
        return value, value[:-1] + 'X', f'金融機関コード {n[7:11]} 支店 {n[11:14]} 普通 {value}'
    if kind == 'phone':
        prefix, parts = (
            ('090', (4, 4)), ('070', (4, 4)), ('03', (4, 4)), ('06', (4, 4)),
            ('045', (3, 4)), ('011', (3, 4)), ('050', (4, 4)), ('080', (4, 4)),
        )[family % 8]
        left, right = n[:parts[0]], n[parts[0]:sum(parts)]
        value = prefix + left + right
        formatted = f'+81 ({prefix[1:]}) {left}-{right}' if family % 2 else f'{prefix}-{left}-{right}'
        return value, value[:-1] + 'X', formatted
    if kind == 'email':
        localpart = (f'{a[:4]}.{n[:6]}', f'{a[:4]}+{n[:6]}', f'{a[:4]}_{n[:6]}')[family % 3].lower()
        domain = ('example.com', 'dept.example.org', 'example.net', 'example.test')[family % 4]
        value = localpart + '@' + domain
        return value, localpart + ' at ' + domain, f'<{value}>'
    if kind == 'iban':
        country, bban = (
            ('DE', n[:18]), ('GB', 'ZZZZ' + n[:14]), ('FR', n[:10] + a[:3] + n[10:20]),
        )[family % 3]
        value = country + f'{98 - iban_remainder(country + "00" + bban):02d}' + bban
        check = (int(value[2:4]) + 1) % 100
        return value, value[:2] + f'{check:02d}' + bban, ' '.join(value[i:i+4] for i in range(0, len(value), 4))
    if kind == 'swift':
        value = a[:4] + ('JP', 'GB', 'DE', 'FR')[family % 4] + n[:2]
        if family % 2:
            value += a[4:7]
        return value, value[:5] + '0' + value[6:], value[:4] + ' ' + value[4:]
    if kind == 'name':
        value = f'{NAMES[0][family // 8]} {NAMES[1][family % 8]}'
        return value, '見本機材', value.replace(' ', '')
    if kind == 'password_plain':
        value = (f'fixture-{a}{n[:6]}!', f'{a[:3]}_{n[:8]}#',
                 f'見本{a[:3]}{n[:5]}灯', f'fixture {a[:4]} {n[:5]}')[family % 4]
        return value, ('********', '未設定', '<pending>', '＿')[family % 4], '"' + value + '"'
    raise ValueError(kind)


def make_cases():
    rows = []

    def add(item, family, scenario, content, expected_role, expected_shape, **annotations):
        ident = sha(f'{VERSION}/{item}/{family}/{scenario}')[:18]
        head, tail = _tokens(ident)
        text = f'{head}\n\n{content}\n\n{tail}\n'
        rows.append(({
            'case_id': ident, 'file': f'test-{ident}.txt', 'item': item, 'family': family,
            'scenario': scenario, 'role_truth': expected_role, 'format_truth': expected_shape,
            'body_sha256': sha(text), 'scan_control': {'head_token': head, 'tail_token': tail},
            **annotations,
        }, text))

    for item, (heading, alternate, unrelated) in SOURCES.items():
        for family in range(FAMILIES):
            value, near, formatted = variants(item, family)
            verifiable = item not in ('name', 'password_plain')
            shape = 1 if verifiable else None
            add(item, family, 'heading', f'{heading}：{value}', 1, shape)
            add(item, family, 'bare', value, 1, shape)
            add(item, family, 'alternate', f'{alternate}は次のとおりです。\n{value}', 1, shape)
            add(item, family, 'formatted', f'{heading}\t{formatted}', 1, shape)
            add(item, family, 'unrelated', f'{unrelated}：{value}', 0, shape)
            add(item, family, 'near_miss', f'{heading}：{near}', 0, 0 if verifiable else None)
            if item == 'email':
                name = f'{NAMES[0][family // 8]}{NAMES[1][family % 8]}'
                add(item, family, 'internationalized', f'返信先：{name}@example.com', 1, 1)
            add(item, family, 'filled_example',
                f'{heading}：{value}\n操作研修の入力例。登録は行わない。', 0, shape)
            if item in COLLISIONS:
                field, other = COLLISIONS[item]
                cross = {}
                if other:
                    eligible_role = int(individual_valid(value)) if other == 'individual' else 1
                    cross[other] = eligible_role
                add(item, family, 'competing_identifier', f'{field}：{value}', 0, shape,
                    cross_role_truth=cross)
                add(item, family, 'competing_bare', value, 0, shape,
                    cross_role_truth=cross)
            if item == 'phone':
                prefix = ('080', '090', '0120', '1234')[family % 4]
                suffix_length = {'080': 8, '090': 8, '0120': 6, '1234': 0}[prefix]
                number = prefix + ascii_number('number-collision', family, 8)[:suffix_length]
                valid = int(suffix_length > 0)
                add(item, family, 'prefix_contact', f'電話番号：{number}', valid, valid,
                    employee_truth=0, number_prefix=prefix)
                add(item, family, 'prefix_employee', f'社員番号：{number}', 0, valid,
                    employee_truth=1, number_prefix=prefix)
                add(item, family, 'prefix_employee_alias', f'人事台帳の担当者コード\n{number}', 0, valid,
                    employee_truth=1, number_prefix=prefix)
                short = '080' + ascii_number('short-mobile', family, 7)
                add(item, family, 'short080_employee', f'社員番号：{short}', 0, 0,
                    employee_truth=1, number_prefix='080-short')
                add(item, family, 'short080_contact', f'電話番号：{short}', 0, 0,
                    employee_truth=0, number_prefix='080-short')


    templates = (
        '個別の申告記録（管理番号 {code}）\n対象者 {person}\n{description}',
        '個別面談メモ {code}\n担当者向け記録\n{person}の申告　{description}',
        '対象者\t記録番号\t記録内容\n{person}\t{code}\t{description}',
        '以下は案件 {code} の処理記録です。\n対象者は {person}。\n{description}',
    )
    neutral = ('運用資料', '管理部の参考メモ', '新人研修の資料', '公開説明の草案')
    for item, (heading, examples) in SENSITIVE.items():
        for family in range(FAMILIES):
            specific, indirect, contrast = examples[family % len(examples)]
            code = letters('record', family, 6)
            name, _, _ = variants('name', family)
            case = templates[family % len(templates)]
            expected = int(item != 'clinical_care' or family % len(examples) < 2)
            add(item, family, 'heading', case.format(code=code, person=name, description=f'{heading}：{specific}'), expected, None)
            add(item, family, 'indirect', case.format(code=code, person=name, description=indirect), expected, None)
            add(item, family, 'reference', f'{neutral[family % len(neutral)]} {code}\n{heading}：{specific}\n記入例。実際の申告は未提出。', 0, None)
            add(item, family, 'near_miss', f'{neutral[family % len(neutral)]} {code}\n{contrast}', 0, None)
    return sorted(rows, key=lambda row: row[0]['case_id'])


PROPERTY_TRIALS = [
    ('literal', '本文に指定語だけ', 'exact', True),
    ('literal', '引用中に同じ指定語', 'quoted', True),
    ('literal', '1文字違う別語', 'near', False),
    ('filename', '対象名に一致', 'name-hit.txt', True),
    ('filename', '本文だけに対象名あり', 'other.txt', False),
    ('filename', '指定名を接頭辞に含む別名', 'name-hit-copy.txt', False),
    ('extension', '拡張子はPDF・実体はテキスト', 'plain.pdf', True),
    ('extension', '拡張子はDAT・実体はPDF', 'document.dat', False),
    ('mime', '拡張子はPDF・実体はテキスト', 'plain.pdf', False),
    ('mime', '拡張子はDAT・実体はPDF', 'document.dat', True),
    ('label', '指定フィールドの指定値', 'target-field-value', True),
    ('label', '同じ表示名で別ラベル', 'other-definition', False),
    ('label', '同じラベルで別の選択肢', 'other-value', False),
    ('label', '本文だけにラベル名を記載', 'body-only', False),
]


def make(output):
    output.mkdir(parents=True, exist_ok=False)
    drive = output / 'drive_upload'
    drive.mkdir()
    rows = make_cases()
    for row, body in rows:
        (drive / row['file']).write_bytes(body.encode('utf-8'))
    for name, value in {
        'ground_truth.json': [row for row, _ in rows],
        'rule_plan.json': {
            'standard_body_audit': [
                {'item': item, 'detector': detector, 'threshold': level,
                 'minimum_match_count': 1, 'minimum_unique_match_count': 1, 'content_source': 'body'}
                for item, detector in STANDARD.items() for level in THRESHOLDS
            ],
            'local_regex_items': sorted((SOURCES.keys() | SENSITIVE.keys()) - STANDARD_ONLY),
            'external_scope_note': '標準検知器のある項目の正規表現は測定しない。',
            'extra_candidates_to_verify_in_admin': {
                'medical_history': ['Medical context', 'ICD 9-CM Lexicon', 'ICD 10-CM Lexicon'],
                'clinical_care': ['Medical context（語の検出として比較）'],
                'health_checkup': ['Medical context（語の検出として比較）'],
            },
            'literal_metadata_label_trials': PROPERTY_TRIALS,
            'control_note': '各資料の先頭・末尾の対照を検査の根拠とする。規則適用・観測が確認できなければ未判定。',
        },
    }.items():
        (output / name).write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))


def evaluate(dataset):
    re2 = local.engine()
    rows = json.loads((dataset / 'ground_truth.json').read_text(encoding='utf-8'))
    if rows != [row for row, _ in make_cases()]:
        raise ValueError('固定された正解表と一致しません')

    local_items = (SOURCES.keys() | SENSITIVE.keys()) - STANDARD_ONLY
    references = {kind: re2.compile(local.baseline_regex(kind)) for kind in local_items}
    patterns = {regex for kind in local_items for clause in local.context_rules.RULES[kind]
                for regex in clause['all'] + clause['not']}
    rules = {regex: re2.compile(regex) for regex in patterns}
    staff_shape = r'\b[0-9]{4,11}\b'
    staff_rules = {
        'employee_number_shape': re2.compile(staff_shape),
        'employee_number_heading': re2.compile(rf'社員番号[ \t]*[:：][ \t]*{staff_shape}'),
    }
    result = defaultdict(list)

    def record(name, kind, axis, scenario, truth, match):
        observation = {'status': 'detected' if match else 'not_detected'}
        point = ({'expected': truth}, observation)
        result[name, kind, axis, 'all'].append(point)
        result[name, kind, axis, scenario].append(point)

    for row in rows:
        body = input_file(dataset, row['file']).read_bytes().decode('utf-8')
        if sha(body) != row['body_sha256']:
            raise ValueError(f"本文の内容が正解表と一致しません: {row['case_id']}")
        kind = row['item']
        if kind in local_items:
            found = {
                'baseline': bool(references[kind].search(body)),
                'context': local.context_rules.detect(rules, kind, body, ('T1', 'T2', 'T3')) is not None,
            }
            for name, match in found.items():
                for axis in ('role', 'format'):
                    record(name, kind, axis, row['scenario'], row[f'{axis}_truth'], match)
        if 'employee_truth' in row:
            scenario = row['scenario'] + '/' + row['number_prefix']
            for name, rule in staff_rules.items():
                record(name, 'employee', 'role', scenario, row['employee_truth'], bool(rule.search(body)))
    report = {}
    for (name, kind, axis, scenario), points in sorted(result.items()):
        report.setdefault(name, {}).setdefault(kind, {}).setdefault(axis, {})[scenario] = metrics(points)
    return {'dataset': VERSION, 'files': len(rows), 'families_per_item': FAMILIES, 'engine': 'RE2',
            'likelihood_threshold': None, 'workspace_measured': False,
            'workspace_standard_only': sorted(STANDARD_ONLY), 'reports': report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('make').add_argument('--output', type=Path, required=True)
    score = commands.add_parser('evaluate')
    score.add_argument('--dataset', type=Path, required=True)
    score.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'make':
        make(args.output)
    else:
        report = evaluate(args.dataset)
        with args.report.open('x', encoding='utf-8') as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write('\n')


if __name__ == '__main__':
    main()
