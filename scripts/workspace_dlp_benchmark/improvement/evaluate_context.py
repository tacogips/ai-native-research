"""文脈補強（v4-context）と既存の独自正規表現（v3）を、同じ資料でRE2により比較する。

  評価資料1: 既存v3の生成物（開発資料。改善規則の作成時に参照したので楽観的）
  評価資料2: 独立に作成した保留資料 holdout_cases.json（改善規則の固定後に初めて照合）

Workspaceの標準検知器・語句一覧・実際のラベル付与は測らない。結果はローカルのRE2検査であり、
Google実環境の検知精度ではない。
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'extended'))
sys.path.insert(0, str(HERE))
from catalog import GROUPS, ITEMS, LIMITS  # noqa: E402
import context_rules  # noqa: E402

RULES_SHA256 = hashlib.sha256((HERE / 'context_rules.py').read_bytes()).hexdigest()


def engine():
    try:
        import re2
    except ImportError as exc:  # RE2と同じ動作が必要
        raise SystemExit('google-re2 が必要です（extended/README.md の手順で導入）') from exc
    return re2


def baseline_regex(item):
    parts = []
    for r in ITEMS[item]['regex']:
        parts.append('(?i:' + r[4:] + ')' if r.startswith('(?i)') else '(?:' + r + ')')
    return '|'.join(parts)


def counts(pairs):
    c = Counter()
    for truth, found in pairs:
        if truth is None:
            c['held'] += 1
        else:
            c[('TP' if found else 'FN') if truth else ('FP' if found else 'TN')] += 1
    tp, fp, fn, tn = (c[k] for k in ('TP', 'FP', 'FN', 'TN'))
    div = lambda a, b: round(a / b, 4) if b else None  # noqa: E731
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn, 'held': c['held'],
            'precision': div(tp, tp + fp), 'recall': div(tp, tp + fn),
            'accuracy': div(tp + tn, tp + fp + fn + tn), 'f1': div(2 * tp, 2 * tp + fp + fn)}


def load_v3(dataset):
    dataset = Path(dataset)
    rows = json.loads((dataset / 'ground_truth.json').read_text(encoding='utf-8'))
    cases = []
    for r in rows:
        text = (dataset / 'drive_upload' / r['file']).read_text(encoding='utf-8')
        cases.append({'case_id': r['case_id'], 'item': r['item'], 'style': r['variant'], 'text': text,
                      'truth': dict(r['expected_by_item']), 'split': r['split']})
    return cases


def load_holdout(path):
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    cases = []
    for r in raw:
        unknown = (set(r['present']) | set(r.get('ambiguous', []))) - set(ITEMS)
        if unknown:
            raise ValueError(f"{r['case_id']}: 未知の項目 {sorted(unknown)}")
        truth = {i: (1 if i in r['present'] else (None if i in r.get('ambiguous', []) else 0)) for i in ITEMS}
        cases.append({'case_id': r['case_id'], 'item': r['item'], 'style': r['style'], 'kind': r['kind'],
                      'text': r['text'], 'truth': truth, 'split': 'holdout'})
    return cases


def run(cases, re2):
    """構成ごとに 資料×項目 の判定を返す。"""
    base = {i: re2.compile(baseline_regex(i)) for i in ITEMS}
    compiled = {rx: re2.compile(rx) for rx in context_rules.detectors()}
    found = {}
    for name, techs in context_rules.configurations().items():
        found[name] = {}
        for c in cases:
            if techs is None:
                found[name][c['case_id']] = {i: bool(base[i].search(c['text'])) for i in ITEMS}
            else:
                found[name][c['case_id']] = {i: context_rules.detect(compiled, i, c['text'], techs) is not None
                                             for i in ITEMS}
    return found


def group_truth(truths):
    return 1 if 1 in truths else (None if None in truths else 0)


def summarize(cases, found):
    out = {}
    for name, f in found.items():
        per_item = {i: counts([(c['truth'][i], f[c['case_id']][i]) for c in cases]) for i in ITEMS}
        per_group = {}
        for g in GROUPS:
            members = [i for i in ITEMS if ITEMS[i]['group'] == g]
            if members:
                per_group[g] = counts([(group_truth([c['truth'][i] for i in members]),
                                        any(f[c['case_id']][i] for i in members)) for c in cases])
        cells = counts([(c['truth'][i], f[c['case_id']][i]) for c in cases for i in ITEMS])
        files = counts([(group_truth(list(c['truth'].values())), any(f[c['case_id']].values())) for c in cases])
        groups_micro = counts([(group_truth([c['truth'][i] for i in ITEMS if ITEMS[i]['group'] == g]),
                                any(f[c['case_id']][i] for i in ITEMS if ITEMS[i]['group'] == g))
                               for c in cases for g in GROUPS if g != 'G8'])
        by_style = {}
        for style in sorted({c['style'] for c in cases}):
            sel = [c for c in cases if c['style'] == style]
            by_style[style] = counts([(c['truth'][c['item']], f[c['case_id']][c['item']]) for c in sel])
        errors = {'FP': [], 'FN': []}
        for c in cases:
            for i in ITEMS:
                t, d = c['truth'][i], f[c['case_id']][i]
                if t == 0 and d:
                    errors['FP'].append(f"{c['case_id']}:{i}")
                elif t == 1 and not d:
                    errors['FN'].append(f"{c['case_id']}:{i}")
        out[name] = {'cells': cells, 'group_cells': groups_micro, 'files': files, 'per_group': per_group,
                     'per_item': per_item, 'primary_item_by_style': by_style, 'errors': errors}
    return out


def limits():
    rx = context_rules.detectors()
    return {'custom_regex_detectors': len(rx), 'limit_custom_detectors_in_rules': LIMITS['custom_detectors_in_rules'],
            'max_regex_chars': max(len(r) for r in rx), 'limit_regex_chars': LIMITS['regex_chars'],
            'within_limits': len(rx) <= LIMITS['custom_detectors_in_rules'] and max(len(r) for r in rx) <= LIMITS['regex_chars']}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--v3-dataset', help='extended/build.py make の出力先')
    ap.add_argument('--holdout', default=str(HERE / 'holdout_cases.json'))
    ap.add_argument('--report', required=True)
    a = ap.parse_args(argv)
    re2 = engine()
    for rx in context_rules.detectors():
        re2.compile(rx)
    result = {'rules': 'v4-context', 'rules_sha256': RULES_SHA256, 'engine': 'google-re2',
              'limits': limits(), 'datasets': {}}
    if a.v3_dataset:
        cases = [c for c in load_v3(a.v3_dataset)]
        result['datasets']['v3_all_development'] = {'files': len(cases), 'metrics': summarize(cases, run(cases, re2))}
    holdout_path = Path(a.holdout)
    if not holdout_path.exists():
        print('保留資料がないため開発資料だけを評価します', file=sys.stderr)
    else:
        cases = load_holdout(holdout_path)
        result['datasets']['holdout'] = {'files': len(cases),
                                         'sha256': hashlib.sha256(holdout_path.read_bytes()).hexdigest(),
                                         'kinds': dict(Counter(c['kind'] for c in cases)),
                                         'metrics': summarize(cases, run(cases, re2))}
    Path(a.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for ds, body in result['datasets'].items():
        print(f'== {ds} ({body["files"]} files)')
        for name, m in body['metrics'].items():
            g, f = m['group_cells'], m['files']
            print(f"  {name:10s} group P={g['precision']} R={g['recall']} F1={g['f1']} (TP{g['TP']} FP{g['FP']} FN{g['FN']})"
                  f" | file P={f['precision']} R={f['recall']}")
    print('limits', result['limits'])
    return result


if __name__ == '__main__':
    main()
