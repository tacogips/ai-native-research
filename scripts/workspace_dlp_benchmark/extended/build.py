#!/usr/bin/env python3
"""拡張版（v3）データセットの生成、独自検知器のローカル検査、分類ラベル計画の作成。

標準検知器の結果はWorkspace実環境でしか得られないため、ローカルでは測らない（pending）。
ローカル検査はRE2（google-re2）で独自正規表現を評価する。RE2がなければ実行を拒否する。
"""
import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from catalog import GROUPS, ITEMS, LIMITS, UNSUPPORTED  # noqa: E402
from dataset import _tokens  # noqa: E402
from samples import NAMES, NEGATIVES, values  # noqa: E402

VERSION = 'v3-extended'
TRUTH_REVISION = 'r2'
CASE_TRUTH_OVERRIDES = {'medical_history-family': {'family': 1}}
# 他項目と重なる表現。主項目以外で判断保留にする。
CROSS_AMBIGUOUS = {'job_history': ['employer'], 'private_insurance': ['family'],
                   'disability': ['medical_history']}


def combined_regex(item):
    """項目の正規表現を1つの独自検知器にまとめる。(?i)は範囲付きの指定へ変える。"""
    parts = []
    for r in ITEMS[item]['regex']:
        parts.append('(?i:' + r[4:] + ')' if r.startswith('(?i)') else '(?:' + r + ')')
    return '|'.join(parts)


def check_limits():
    problems = []
    for item in ITEMS:
        if len(combined_regex(item)) > LIMITS['regex_chars']:
            problems.append(f'{item}: 正規表現が{LIMITS["regex_chars"]}文字を超える')
        words = ITEMS[item].get('word_list', [])
        if len(words) > LIMITS['word_list_words'] or len(','.join(words).encode()) > LIMITS['word_list_bytes']:
            problems.append(f'{item}: 語句一覧が上限を超える')
    detectors = len(ITEMS) + sum(1 for i in ITEMS.values() if i.get('word_list'))
    if detectors > LIMITS['custom_detectors_in_rules']:
        problems.append('規則で使う独自検知器が100を超える')
    return problems, detectors


def _truth(item, text, expected):
    truth = dict.fromkeys(ITEMS, 0)
    truth[item] = expected
    if any(n in text for n in NAMES) and item != 'name':
        truth['name'] = 1
    if expected == 1:
        for other in CROSS_AMBIGUOUS.get(item, []):
            truth[other] = None
    return truth


def make(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    upload = output / 'drive_upload'
    upload.mkdir()
    rows = []

    def add(item, variant, body, expected, split, note, value_id=None):
        case_id = f'{item}-{variant}'
        head, tail = _tokens(VERSION + case_id)
        text = head + '\n架空の検知試験資料。実際の手続きには使用できません。\n' + body + '\n' + tail + '\n'
        path = upload / (case_id + '.txt')
        path.write_bytes(text.encode('utf-8'))
        truth = _truth(item, body, expected)
        truth.update(CASE_TRUTH_OVERRIDES.get(case_id, {}))
        rows.append({'case_id': case_id, 'file': path.name, 'item': item, 'group': ITEMS[item]['group'],
                     'variant': variant.rsplit('-', 1)[0] if value_id else variant, 'value_id': value_id,
                     'truth_revision': TRUTH_REVISION,
                     'split': split, 'expected': expected, 'note': note, 'expected_by_item': truth,
                     'scan_control': {'head_token': head, 'tail_token': tail},
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

    for item in ITEMS:
        for i, (label, value, sentence) in enumerate(values(item)):
            name = NAMES[i]
            vid = f'{item}-v{i + 1}'
            split = '開発' if i == 0 else '評価'
            add(item, f'heading-{i + 1}', f'{label}：{value}', 1, split, '見出しあり', vid)
            add(item, f'sentence-{i + 1}', sentence.format(n=name), 1, split, '見出しなしの文', vid)
            add(item, f'table-{i + 1}', f'項目\t内容\n氏名\t{name}\n{label}\t{value}', 1, split, '表の行', vid)
        label = values(item)[0][0]
        add(item, 'shared_empty', f'{label}：＿＿＿＿', 0, '評価', '空欄（共通）')
        add(item, 'shared_masked', f'{label}：****', 0, '評価', '伏字（共通）')
        for variant, body, expected, note in NEGATIVES.get(item, []):
            add(item, variant, body, expected, '評価', note)
    (output / 'ground_truth.json').write_bytes((json.dumps(rows, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    (output / 'generation.json').write_bytes((json.dumps({
        'version': VERSION, 'truth_revision': TRUTH_REVISION, 'files': len(rows), 'items': len(ITEMS), 'groups': GROUPS,
        'unsupported_not_generated': UNSUPPORTED,
        'note': '独自の架空例。文字資料のみ。顔・音声・映像は本文検査の対象外のため生成しない。'},
        ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return rows


def _engine():
    try:
        import re2
    except ImportError as error:
        raise SystemExit('google-re2が必要です。RE2と異なる正規表現エンジンで代用しません') from error
    return re2


def _word_hits(words, text, mode):
    """語句一覧の一致。日本語の扱いは公式説明で確認できないため、2つの仮定を比較する。"""
    if mode == 'substring':
        return any(w in text for w in words)
    # 単語全体の一致を、前後が英数字・かな漢字でない場合に限ると仮定する。
    def boundary(c):
        return not (c.isalnum())
    for w in words:
        start = text.find(w)
        while start >= 0:
            before = text[start - 1] if start else ' '
            after = text[start + len(w)] if start + len(w) < len(text) else ' '
            if boundary(before) and boundary(after):
                return True
            start = text.find(w, start + 1)
    return False


def _counts(pairs):
    c = Counter()
    for truth, found in pairs:
        if truth is None:
            c['保留'] += 1
        else:
            c[('TP' if found else 'FN') if truth else ('FP' if found else 'TN')] += 1
    tp, fp, fn, tn = (c[k] for k in ('TP', 'FP', 'FN', 'TN'))
    div = lambda a, b: round(a / b, 4) if b else None
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn, '保留': c['保留'],
            'precision': div(tp, tp + fp), 'recall': div(tp, tp + fn),
            'accuracy': div(tp + tn, tp + fp + fn + tn), 'f1': div(2 * tp, 2 * tp + fp + fn)}


def evaluate(dataset, report):
    re2 = _engine()
    dataset = Path(dataset)
    rows = json.loads((dataset / 'ground_truth.json').read_text(encoding='utf-8'))
    revisions = {row.get('truth_revision', 'r1') for row in rows}
    if len(revisions) != 1:
        raise ValueError('異なる版の正解を混ぜません')
    compiled = {item: re2.compile(combined_regex(item)) for item in ITEMS}
    found = {}
    for row in rows:
        text = (dataset / 'drive_upload' / row['file']).read_text(encoding='utf-8')
        found[row['case_id']] = {item: bool(compiled[item].search(text)) for item in ITEMS}
        for mode in ('substring', 'token'):
            found[row['case_id']][f'medical_history:wordlist:{mode}'] = _word_hits(ITEMS['medical_history']['word_list'], text, mode)
    evaluation = [r for r in rows if r['split'] == '評価']
    per_item, by_variant, matches = {}, defaultdict(dict), defaultdict(list)
    for item in ITEMS:
        pairs = [(r['expected_by_item'][item], found[r['case_id']][item]) for r in evaluation]
        per_item[item] = _counts(pairs)
        own = [r for r in evaluation if r['item'] == item]
        for variant in sorted({r['variant'] for r in own}):
            sel = [r for r in own if r['variant'] == variant]
            by_variant[item][variant] = _counts([(r['expected_by_item'][item], found[r['case_id']][item]) for r in sel])
        for r in evaluation:
            if found[r['case_id']][item] and r['expected_by_item'][item] == 0:
                matches[item].append(r['case_id'])
    wordlist = {mode: _counts([(r['expected_by_item']['medical_history'], found[r['case_id']][f'medical_history:wordlist:{mode}'])
                               for r in evaluation]) for mode in ('substring', 'token')}
    per_group = {}
    for g in GROUPS:
        members = [i for i in ITEMS if ITEMS[i]['group'] == g]
        if not members:
            continue
        pairs = []
        for r in evaluation:
            truths = [r['expected_by_item'][i] for i in members]
            truth = 1 if 1 in truths else (None if None in truths else 0)
            pairs.append((truth, any(found[r['case_id']][i] for i in members)))
        per_group[g] = _counts(pairs)
    problems, detectors = check_limits()
    result = {'version': VERSION, 'truth_revision': next(iter(revisions)), 'engine': 'google-re2 ' + getattr(re2, '__version__', ''),
              'files': len(rows), 'evaluation_files': len(evaluation),
              'limits': {'problems': problems, 'custom_detectors': detectors,
                         'max_regex_chars': max(len(combined_regex(i)) for i in ITEMS)},
              'custom_regex': {'per_item': per_item, 'by_variant': by_variant, 'false_positive_cases': matches},
              'medical_word_list': wordlist, 'group_labels': per_group,
              'predefined': {i: {'detectors': ITEMS[i]['predefined'], 'status': 'pending（Workspace実環境が必要）'}
                             for i in ITEMS if ITEMS[i]['predefined']},
              'limitation': '独自正規表現は本データの雛形を見て作成したため楽観的。標準検知器と語句一覧の実際の一致方法は未測定。'}
    Path(report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def label_plan(output):
    """1グループ1ラベル、単一選択フィールド「検知」。上位の選択肢が競合時に優先される。"""
    labels = [{'label': f'PII-{g} {name}', 'field': '検知', 'options': ['確度高', '確度中'],
               'note': 'DLPは単一選択の選択肢型だけを付与できる。上位の確度高が競合時に優先'}
              for g, name in GROUPS.items() if g != 'G8']
    rules = []
    for g in GROUPS:
        members = [i for i in ITEMS if ITEMS[i]['group'] == g]
        if not members:
            continue
        high = [d for i in members for d in ITEMS[i]['predefined']]
        rules.append({'rule': f'PII-{g}-確度高', 'conditions_or': high or ['（標準検知器なし）'],
                      'action': {'label': f'PII-{g}', 'field': '検知', 'value': '確度高'}, 'mode': '監査＋ラベル付与'})
        rules.append({'rule': f'PII-{g}-確度中', 'conditions_or': [f'独自正規表現 v3-{i}' for i in members]
                      + ([f'独自語句一覧 v3-{i}' for i in members if ITEMS[i].get('word_list')]),
                      'action': {'label': f'PII-{g}', 'field': '検知', 'value': '確度中'}, 'mode': '監査＋ラベル付与'})
    # SelectionOptions.listOptionsを付けると複数選択になるため、省略する。
    # これは作成要求の計画だけ。IDの読み戻し・公開・権限確認は別工程。
    api_labels = [{'group': g, 'method': 'labels.create', 'parameters': {'useAdminAccess': True},
                   'body': {'labelType': 'ADMIN', 'properties': {'title': label['label']},
                            'fields': [{'properties': {'displayName': label['field']},
                                        'selectionOptions': {'choices': [
                                            {'properties': {'displayName': option}}
                                            for option in label['options']]}}]}}
                  for g, label in zip((g for g in GROUPS if g != 'G8'), labels)]
    plan = {'labels': labels, 'rules': rules, 'drive_labels_api_create_plan': api_labels,
            'api_execution': '未実装・未実行。作成後のID照合、公開と利用権限の確認が別途必要',
            'custom_detectors': {f'v3-{i}': combined_regex(i) for i in ITEMS},
            'word_lists': {f'v3-{i}': ITEMS[i]['word_list'] for i in ITEMS if ITEMS[i].get('word_list')},
            'unsupported': UNSUPPORTED,
            'constraints': ['同じ規則でラベルを条件と動作の両方に使わない',
                            '1規則で複数ラベルを付けられるかは公式資料に記載がないため、1規則1ラベルにする',
                            '試験の正解用ラベルとこの出力用ラベルを混ぜない']}
    Path(output).write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return plan


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    m = sub.add_parser('make'); m.add_argument('--output', required=True, type=Path)
    e = sub.add_parser('evaluate'); e.add_argument('--dataset', required=True, type=Path); e.add_argument('--report', required=True, type=Path)
    lp = sub.add_parser('label-plan'); lp.add_argument('--output', required=True, type=Path)
    a = p.parse_args(argv)
    if a.command == 'make':
        print('作成:', len(make(a.output)), '資料')
    elif a.command == 'evaluate':
        r = evaluate(a.dataset, a.report)
        print(json.dumps({'limits': r['limits'], 'group_labels': r['group_labels']}, ensure_ascii=False, indent=2))
    else:
        print('規則:', len(label_plan(a.output)['rules']))


if __name__ == '__main__':
    main()
