"""業務番号の合成評価資料を生成し、固定した正規表現をローカルで採点する。"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from common import input_file
from scoring import metrics

LABELS = {
    'employee': ('社員番号', '従業員コード', '人事台帳'),
    'contract': ('契約番号', '契約管理ID', '法務台帳'),
    'order': ('注文番号', '発注ID', '購買台帳'),
    'invoice': ('請求番号', '請求書ID', '経理台帳'),
}
FOCUS = ('employee', 'contract')
VERSION = 'business-identifiers-v1'
VALUE = r'(?:[A-Z]{1,3}[-/]?)?[0-9]{5,9}(?:-[0-9]{2,4})?'
SHAPE = rf'\b{VALUE}\b'
DEFAULT_RULES = {
    'format_only': dict.fromkeys(LABELS, SHAPE),
    'canonical_label': {
        kind: rf'{name}[ \t]*[:：][ \t]*{SHAPE}'
        for kind, (name, _, _) in LABELS.items()
    },
}
FULL_WIDTH = str.maketrans(
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/',
    'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９－／',
)


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def number(index):
    value = int(digest(f'{VERSION}:{index}')[:12], 16) % 1000
    prefix = ('AB', 'K', 'BIZ', 'ZT')[(index // 8) % 4]
    # 同じ桁数では重複のない置換を使い、ゼロ埋めの連番に偏らせない。
    shuffled = index * 731729 + 519417
    code5 = f'{shuffled % 10**5:05d}'
    code6 = f'{shuffled % 10**6:06d}'
    code7 = f'{shuffled % 10**7:07d}'
    code9 = f'{shuffled % 10**9:09d}'
    forms = (
        code5, code7, code9, f'{prefix}{code6}', f'{prefix}-{code7}',
        f'{prefix}/{code6}', f'{value:03d}-{shuffled % 10**4:04d}',
        code7.translate(FULL_WIDTH),
    )
    return forms[(index - 1) % len(forms)]


def cases():
    rows = []

    def add(scenario, family, body, present=(), unknown=(), origin=None):
        case_id = 'doc-' + digest(f'{VERSION}:{len(rows)}')[:16]
        text = body + '\n'
        rows.append(({
            'case_id': case_id, 'file': case_id + '.txt', 'scenario': scenario,
            'value_family': family, 'sha256': digest(text),
            'expected_by_kind': {
                kind: None if kind in unknown else int(kind in present) for kind in LABELS
            },
            'provenance_kind': origin,
        }, text))

    for family in range(1, 49):
        value = number(family)
        for index, (kind, (name, alias, register)) in enumerate(LABELS.items()):
            other_kind = list(LABELS)[(index + 1) % len(LABELS)]
            other_name = LABELS[other_kind][0]
            templates = {
                'explicit': f'更新対象\n{name}：{value}\n状態：承認済',
                'alternate_name': f'引継ぎ：{alias} は {value} を参照。',
                'table': f'{alias},拠点,状態\n{value},第二,確認済',
                'context_only': f'{register}の更新依頼\n対象行の識別子は「{value}」。',
                'two_lines': f'{name}\n（登録値）\n{value}\n変更なし',
                'misleading_label': f'{name}：{value} は入力例。登録値はありません。',
                'different_number': f'{name}：未入力\n{other_name}：{value}',
            }
            for scenario, body in templates.items():
                if scenario == 'misleading_label':
                    add(scenario, family, body)
                elif scenario == 'different_number':
                    add(scenario, family, body, (other_kind,))
                else:
                    add(scenario, family, body, (kind,))
        second_value = number(48 + family)
        add('mixed', family, f'社員番号：{value}\n契約番号：{second_value}', FOCUS)
        add('other_numbers', family, f'棚卸しメモ\n在庫管理番号：{value}\n照合済')
        # 資料に含まれない台帳上の意味だけを入れ替える、観測内容が同一の対。
        for origin in ('employee', 'order'):
            add('no_context_pair', family, value, unknown=LABELS, origin=origin)
    return sorted(rows, key=lambda pair: pair[0]['case_id'])


def make(output):
    output.mkdir(parents=True, exist_ok=False)
    uploads = output / 'drive_upload'
    uploads.mkdir()
    rows = cases()
    for row, text in rows:
        (uploads / row['file']).write_bytes(text.encode('utf-8'))
    (output / 'ground_truth.json').write_text(
        json.dumps([row for row, _ in rows], ensure_ascii=False, indent=2) + '\n', encoding='utf-8',
    )


def evaluate(dataset, rule_sets, compile_regex):
    manifest = dataset / 'ground_truth.json'
    manifest_text = manifest.read_text(encoding='utf-8')
    rows = json.loads(manifest_text)
    if rows != [row for row, _ in cases()]:
        raise ValueError('正解表が固定された生成仕様と一致しません')
    documents = []
    for row in rows:
        text = input_file(dataset, row['file']).read_bytes().decode('utf-8')
        if digest(text) != row['sha256']:
            raise ValueError('本文が正解表の検査値と一致しません: ' + row['case_id'])
        documents.append((row, text))
    report = {
        'dataset': VERSION, 'engine': 'RE2', 'workspace_measured': False,
        'document_count': len(documents), 'truth_sha256': digest(manifest_text), 'min_matches': 1,
        'likelihood_threshold': None, 'rule_sets': {},
    }
    for name, rules in rule_sets.items():
        if set(rules) != set(LABELS):
            raise ValueError('4種類すべての正規表現を指定してください: ' + name)
        compiled = {kind: compile_regex(pattern) for kind, pattern in rules.items()}
        results = defaultdict(list)
        strata = defaultdict(lambda: defaultdict(list))
        pair_results = defaultdict(list)
        for row, text in documents:
            expected = row['expected_by_kind']
            found = {kind: bool(rule.search(text)) for kind, rule in compiled.items()}
            for kind in (*LABELS, 'employee_or_contract'):
                if kind in LABELS:
                    truth, match = expected[kind], found[kind]
                else:
                    truth = None if expected[FOCUS[0]] is None else int(any(expected[k] for k in FOCUS))
                    match = any(found[k] for k in FOCUS)
                point = ({'expected': truth}, {'status': 'detected' if match else 'not_detected'})
                results[kind].append(point)
                strata[row['scenario']][kind].append(point)
            if row['scenario'] == 'no_context_pair':
                pair_results[row['value_family']].append((row['provenance_kind'], found['employee']))
        for pair in pair_results.values():
            if len(pair) != 2 or {x[0] for x in pair} != {'employee', 'order'} or pair[0][1] != pair[1][1]:
                raise ValueError('番号だけの診断対の出自または判定が不整合です')
        report['rule_sets'][name] = {
            'patterns': rules,
            'by_item': {kind: metrics(points) for kind, points in results.items()},
            'by_scenario': {
                scenario: {kind: metrics(points) for kind, points in items.items()}
                for scenario, items in strata.items()
            },
            'no_context_diagnostic': {
                'pairs': len(pair_results),
                'correct_employee_decisions': len(pair_results),
                'total_employee_decisions': 2 * len(pair_results),
            },
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    make_parser = sub.add_parser('make')
    make_parser.add_argument('--output', required=True, type=Path)
    score_parser = sub.add_parser('evaluate')
    score_parser.add_argument('--dataset', required=True, type=Path)
    score_parser.add_argument('--rules', type=Path, help='構成名 → 種類 → RE2正規表現のJSON')
    score_parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.command == 'make':
        make(args.output)
    else:
        import re2
        rules = json.loads(args.rules.read_text(encoding='utf-8')) if args.rules else DEFAULT_RULES
        report = evaluate(args.dataset, rules, re2.compile)
        with args.report.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')


if __name__ == '__main__':
    main()
