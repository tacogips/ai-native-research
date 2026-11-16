#!/usr/bin/env python3
"""独自の合成資料。型の表現・保護方針・検査数字の正解を分離する。"""
import hashlib
import html
import json
from pathlib import Path

# 呼出し側との互換用。第3要素は表示例であり、全資料へ反復しない。
KINDS = {
    'email': ('Email address', 'メールアドレス', 'sample@example.test'),
    'phone': ('Phone number', '電話番号', '+81 90 4826 5739'),
    'passport': ('Japan / Passport', '日本の旅券番号', 'TZ4836275'),
    'license': ("Japan / Driver's License Number", '日本の運転免許証番号', '483627519204'),
    'individual': ('Japan / Individual Number', '日本の個人番号', '483627519207'),
    'bank': ('Japan / Bank Account Number', '日本の銀行口座番号', '4836275'),
    'card': ('Credit card number', 'カード番号', '検査数字を計算した合成値'),
}
CONTROL_PATTERNS = {'head': 'DLPHEAD[A-Z]+', 'tail': 'DLPTAIL[A-Z]+'}
SOURCES = {
    'individual_checksum': 'https://laws.e-gov.go.jp/law/426M60000008085',
    'individual_checksum_api': 'https://laws.e-gov.go.jp/api/2/law_data/426M60000008085?law_full_text_format=json',
    'luhn': 'https://www.pcisecuritystandards.org/faqs/1137/',
}
FULLWIDTH = str.maketrans('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@.+-',
                         '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ＠．＋－')


def _ascii_digits(value, length):
    return isinstance(value, str) and len(value) == length and all('0' <= c <= '9' for c in value)


def luhn_valid(value):
    """Luhnの算式だけを確認。発行済み・利用可能なカードとは判定しない。"""
    if not isinstance(value, str) or not value or not all('0' <= c <= '9' for c in value):
        return False
    total = 0
    for i, char in enumerate(reversed(value)):
        digit = int(char)
        if i % 2:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def luhn_append(prefix):
    if not isinstance(prefix, str) or not prefix or not all('0' <= c <= '9' for c in prefix):
        raise ValueError('Luhnの元桁はASCII数字列が必要です')
    return prefix + next(str(d) for d in range(10) if luhn_valid(prefix + str(d)))


def individual_check_digit(prefix):
    """個人番号の第5条算式。右端からの重みは2,3,4,5,6,7,2,3,4,5,6。"""
    if not _ascii_digits(prefix, 11):
        raise ValueError('個人番号の元桁はASCII数字11桁が必要です')
    weighted = sum(int(c) * (n + 1 if n <= 6 else n - 5)
                   for n, c in enumerate(reversed(prefix), 1))
    remainder = weighted % 11
    return str(0 if remainder <= 1 else 11 - remainder)


def individual_valid(value):
    return _ascii_digits(value, 12) and value[-1] == individual_check_digit(value[:-1])


def wrong_check_digit(value):
    """対の先頭部分を変えず、検査数字だけ1桁変える。"""
    if not value or not all('0' <= c <= '9' for c in value):
        raise ValueError('ASCII数字列が必要です')
    return value[:-1] + str((int(value[-1]) + 1) % 10)


def _digits(kind, number, length):
    raw = hashlib.sha256(f'workspace-dlp-public-v2:{kind}:{number}'.encode()).digest()
    return ''.join(str(b % 10) for b in raw)[:length]


def values_for(kind, count=6):
    """開発2値・評価4値。派生文脈は同じvalue_idへ結び付ける。"""
    values = []
    for number in range(count):
        digits = _digits(kind, number, 16)
        if kind == 'email':
            value = f'person.{number}.{digits[:5]}@example.test'
        elif kind == 'phone':
            value = '+81 ' + ('90', '80', '70')[number % 3] + ' ' + digits[:4] + ' ' + digits[4:8]
        elif kind == 'passport':
            value = ('TZ', 'AB', 'CD', 'EF', 'GH', 'JK')[number % 6] + digits[:7]
        elif kind == 'license':
            value = digits[:12]
        elif kind == 'individual':
            value = digits[:11] + individual_check_digit(digits[:11])
        elif kind == 'bank':
            value = str(1 + int(digits[0]) % 9) + digits[1:7]
        elif kind == 'card':
            value = luhn_append('4' + digits[:14])
        else:
            raise ValueError('未知の分類')
        values.append(value)
    if len(set(values)) != count:
        raise ValueError('生成値が重複しました')
    return values


def _tokens(case_id):
    # 数字・@・記号を含まない一意な対照。PII候補の数字列を足さない。
    # 語句一覧の一語40文字上限以内（接頭辞7＋128bit相当32文字）。
    digest = hashlib.sha256(case_id.encode()).hexdigest()[:32]
    suffix = ''.join(chr(ord('A') + int(c, 16)) for c in digest)
    return 'DLPHEAD' + suffix, 'DLPTAIL' + suffix


def _context(kind):
    if kind == 'bank':
        return '銀行口座情報。架空見本銀行 試験支店 普通預金 口座番号: '
    return KINDS[kind][1] + ': '


def _records(kind, value):
    context = _context(kind)
    title = KINDS[kind][1]
    base = [
        ('heading', '標準見出し', context + value),
        ('bare', '見出しなしの値だけ', value),
        ('paragraph', '文章中', f'申込者の{title}は {value} です。'),
        ('table', '表の値', f'項目\t登録値\n{title}\t{value}'),
        ('ending', '長い前置きの末尾', '手続きの説明文。\n' * 100 + context + value),
    ]
    for variant, condition, body in base:
        yield variant, condition, body, 1, 1, 'basic', 'regular'
    for variant, condition, transformed in [
        ('fullwidth', '全角表記', value.translate(FULLWIDTH)),
        ('newline', '途中改行', value[:len(value)//2] + '\n' + value[len(value)//2:]),
        ('zero_width', 'ゼロ幅文字', value[:len(value)//2] + '\u200b' + value[len(value)//2:]),
    ]:
        yield variant, condition, context + transformed, 1, 1, 'adversarial', 'regular'
    yield 'empty', '空欄', context + '________', 0, 0, 'basic', 'easy_negative'
    yield 'masked', '伏字', context + '********', 0, 0, 'basic', 'easy_negative'
    yield 'short', '形式不足', context + ('abc@' if kind == 'email' else '12'), 0, 0, 'basic', 'format_invalid'
    # 出所が明確な非個人の数字列。型が曖昧なセルは後段でnullにする。
    order = _digits('order-' + kind, value, 12)
    if individual_valid(order):
        order = wrong_check_digit(order)
    yield 'order', '12桁の注文番号', '商品注文番号: ' + order, 0, 0, 'basic', 'order_number'
    yield 'date', '日付の数字列', '処理日: 20261217 / 処理時刻: 20261217142835', 0, 0, 'basic', 'date_number'
    yield 'seven_digits', '銀行の語を伴わない7桁', '倉庫管理番号: ' + _digits('stock-' + kind, value, 7), 0, 0, 'basic', 'stock_number'
    # 同じ型の表現はあるが、この合成保護方針では非個人の商品例は保護しない。
    yield 'product', '同じ値を商品仕様の公開例として記載', '公開商品の入力例（個人の記録ではない）\n' + context + value, 1, 0, 'basic', 'protection_negative'
    if kind in ('card', 'individual'):
        yield 'bad_checksum', '検査数字だけ誤った番号', context + wrong_check_digit(value), 1, 0, 'basic', 'checksum_invalid'


def _truth(kind, value, variant, expected, protected, role):
    content = dict.fromkeys(KINDS, 0)
    protection = dict.fromkeys(KINDS, 0)
    valid = dict.fromkeys(KINDS, 0)
    content[kind] = expected
    protection[kind] = protected
    valid[kind] = expected
    ambiguous = []
    if kind == 'license' and expected:
        valid[kind] = None
    if variant == 'bad_checksum':
        valid[kind] = 0
    if variant == 'bare' and kind in ('license', 'individual'):
        other = 'individual' if kind == 'license' else 'license'
        content[other] = None
        valid[other] = None
        protection[other] = None
        ambiguous.append(other)
    if role == 'order_number':
        for other in ('license', 'individual'):
            content[other] = None
        valid['individual'] = 0  # 構成時に検査数字が合わないことを保証。
        valid['license'] = None
        ambiguous.extend(['license', 'individual'])
    if role == 'stock_number':
        content['bank'] = None
        valid['bank'] = None
        ambiguous.append('bank')
    return content, protection, valid, sorted(set(ambiguous))


def _write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    upload = output / 'drive_upload'
    upload.mkdir()
    rows = []
    for kind, (detector, _, _) in KINDS.items():
        for number, value in enumerate(values_for(kind)):
            split = '開発' if number < 2 else '評価'
            value_id = f'{kind}-value-{number + 1:02d}'
            for variant, condition, body, expected, protected, track, role in _records(kind, value):
                source_id = f'{value_id}-{variant}'
                formats = ['txt', 'html'] if variant in ('heading', 'empty', 'bad_checksum') else ['txt']
                content, protection, valid, ambiguous = _truth(kind, value, variant, expected, protected, role)
                for fmt in formats:
                    case_id = f'{source_id}-{fmt}'
                    head, tail = _tokens(case_id)
                    text = head + '\n架空の検知試験資料。実際の手続きには使用できません。\n' + body + '\n' + tail + '\n'
                    payload = text if fmt == 'txt' else '<!doctype html><meta charset="utf-8"><body><pre>' + html.escape(text) + '</pre></body>'
                    filename = case_id + '.' + fmt
                    path = upload / filename
                    path.write_text(payload, encoding='utf-8')
                    row = {'case_id': case_id, 'source_id': source_id, 'family_id': value_id,
                           'value_id': value_id, 'synthetic_value': value, 'file': filename,
                           'format': fmt, 'kind': kind, 'detector': detector, 'condition': condition,
                           'variant': variant, 'role': role, 'evaluation_track': track,
                           'expected': expected, 'split': split,
                           'expected_by_kind': content.copy(),
                           'protection_expected_by_kind': protection.copy(),
                           'valid_number_expected_by_kind': valid.copy(),
                           'ambiguous_kinds': ambiguous.copy(),
                           'scan_control': {'head_token': head, 'tail_token': tail},
                           'checksum_status': (('invalid' if variant == 'bad_checksum' else 'valid')
                                               if kind in ('card', 'individual') and expected else
                                               'unverified' if kind == 'license' and expected else 'not_applicable'),
                           'validation_scope': 'format_only_checksum_unverified' if kind == 'license' else 'checksum_only' if kind in ('card', 'individual') else 'synthetic_format',
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                    if variant == 'bad_checksum':
                        row['paired_case_id'] = f'{value_id}-heading-{fmt}'
                        row['mutated_value'] = wrong_check_digit(value)
                    rows.append(row)
    _write_json(output / 'ground_truth.json', rows)
    _write_json(output / 'observations.template.json', [
        {'case_id': row['case_id'], 'status': 'pending', 'evidence': '',
         'rule_id': '', 'file_id': '', 'revision': '', 'observed_at': ''} for row in rows])
    _write_json(output / 'ground_truth.matrix.json', [
        {'case_id': row['case_id'], 'kind': kind,
         'expected': row['expected_by_kind'][kind],
         'protection_expected': row['protection_expected_by_kind'][kind],
         'valid_number_expected': row['valid_number_expected_by_kind'][kind]}
        for row in rows for kind in KINDS])
    _write_json(output / 'observations.matrix.template.json', [
        {'case_id': row['case_id'], 'kind': kind, 'status': 'pending', 'evidence': '',
         'rule_id': '', 'file_id': '', 'revision': '', 'observed_at': ''}
        for row in rows for kind in KINDS])
    _write_json(output / 'generation.json', {
        'version': 2, 'count': len(rows), 'values_per_kind': 6,
        'source_count': len({row['source_id'] for row in rows}),
        'value_count': len({row['value_id'] for row in rows}),
        'split_policy': '各分類の独立値6個を開発2・評価4へ固定。文脈・形式の派生は同じ値の相関群として扱う。',
        'control_patterns': CONTROL_PATTERNS,
        'axis_definitions': {'content': '合成した型の表現。検査数字が不正でも表現は存在し得る。曖昧な型はnull。',
                             'protection': '独自の保護方針。公開商品例・注文・管理番号・検査数字不正を保護対象外とする。',
                             'valid_number': '合成した形式と計算可能な検査数字のみ。免許証の検査数字は未検証でnull。実発行・割当・本人への帰属は未確認。'},
        'scan_control_limit': '先頭末尾の一致は本文読取の補助証拠。対象PII検知器の内部走査完了・同一版・全箇所検査を直接証明しない。',
        'warning': '全て独自合成。番号の未発行・未割当を保証せず、外部照会・決済・本人確認には使用しない。形式や検査数字が合っても実製品の検知成功は保証しない。',
        'sources': SOURCES})
    print(f'作成: {len(rows)}資料、独立値42個。Driveへ渡すのは {upload} のみ。')
    return rows
