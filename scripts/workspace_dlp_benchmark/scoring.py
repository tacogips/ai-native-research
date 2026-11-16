"""型・保護・番号妥当性を分離した資料×全規則×閾値の採点。"""
from collections import Counter, defaultdict
from pathlib import Path

from common import digest, input_file, read_json, write_private

ENTITY_KINDS = {'メール': 'email', '電話': 'phone', 'パスポート': 'passport',
                '運転免許証': 'license', 'マイナンバー': 'individual',
                '銀行口座': 'bank', 'カード番号': 'card'}
KINDS = tuple(ENTITY_KINDS.values())
DECIDED = {'detected', 'not_detected'}
STATES = DECIDED | {'pending', 'conditional_not_detected', 'unsupported', 'error',
                    'timeout', 'conflict', 'stale', 'unscorable'}
AXES = {'content': 'expected_by_kind', 'protection': 'protection_expected_by_kind',
        'valid_number': 'valid_number_expected_by_kind'}


def load_truth(dataset, profile=None):
    dataset = Path(dataset)
    source = dataset / 'ground_truth.json'
    if source.exists():
        rows = read_json(source)
    else:
        source = dataset / 'ground_truth/files.json'
        mapping = dict(ENTITY_KINDS)
        if profile:
            mapping.update(profile.get('entity_type_to_kind', {}))
        rows = []
        for item in read_json(source):
            # 出現表にない種類や条件付き結合を自動で有効化しない。
            present = {mapping[e['type']] for e in (item.get('entities') or [])
                       if e.get('type') in mapping}
            kinds = set(mapping.values())
            content = {kind: int(kind in present) if isinstance(item.get('entities'), list) else None
                       for kind in kinds}
            rows.append(dict(item, case_id=item['path'], file=item['path'],
                kind=mapping.get(item.get('primary_type')), format=item['format'].lower(),
                condition=item.get('condition', item.get('group', '拡張形式')),
                split=(profile or {}).get('split_by_source', {}).get(item['source_id'], '拡張'),
                evaluation_track='format_coverage', expected_by_kind=content,
                # 個人との関係や番号の検査数字はこの出現表だけでは決まらない。
                protection_expected_by_kind={kind: None for kind in kinds},
                valid_number_expected_by_kind={kind: None for kind in kinds}))
    if not isinstance(rows, list) or not rows:
        raise ValueError('空または不正な正解表です')
    ids = [r['case_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('正解識別子が重複しています')
    for row in rows:
        if digest(input_file(dataset, row['file'])) != row['sha256']:
            raise ValueError('作成後に検査対象が変更されています: ' + row['case_id'])
        # 旧正解には他分類の不存在や基本/回避の独立軸を追加で推定しない。
        row.setdefault('expected_by_kind', {row['kind']: row.get('expected')})
        row.setdefault('protection_expected_by_kind', {})
        row.setdefault('valid_number_expected_by_kind', {})
        row.setdefault('evaluation_track', 'legacy_unseparated')
    return rows, source


def metrics(rows):
    """未知を陰性にせず、全体の点推定と判定済み部分を別々に返す。"""
    counts = Counter()
    unresolved_positive = unresolved_negative = 0
    for truth, observation in rows:
        expected = truth['expected']
        state = observation['status']
        if expected not in (0, 1) or isinstance(expected, str):
            counts['unscorable'] += 1
            continue
        if state not in DECIDED:
            counts[state] += 1
            unresolved_positive += expected == 1
            unresolved_negative += expected == 0
            continue
        found = state == 'detected'
        counts['TP' if expected and found else 'FN' if expected else 'FP' if found else 'TN'] += 1
    tp, fp, fn, tn = (counts[k] for k in ('TP', 'FP', 'FN', 'TN'))
    for key in ('TP', 'FP', 'FN', 'TN'):
        counts.setdefault(key, 0)
    div = lambda a, b: a / b if b else None
    scored = tp + fp + fn + tn
    eligible = len(rows) - counts['unscorable']
    subset = {'precision': div(tp, tp+fp), 'recall': div(tp, tp+fn),
              'accuracy': div(tp+tn, scored), 'f1': div(2*tp, 2*tp+fp+fn),
              'false_positive_rate': div(fp, fp+tn)}
    eligible_point = subset if scored == eligible and eligible else None
    point = eligible_point if not counts['unscorable'] else None
    pos = tp + fn + unresolved_positive
    neg = fp + tn + unresolved_negative
    bounds = {'recall': [div(tp, pos), div(tp+unresolved_positive, pos)],
              'accuracy': [div(tp+tn, eligible), div(tp+tn+unresolved_positive+unresolved_negative, eligible)],
              'f1': [div(2*tp, 2*tp+fp+fn+unresolved_positive+unresolved_negative),
                     div(2*(tp+unresolved_positive), 2*(tp+unresolved_positive)+fp+fn)]}
    return {'total': len(rows), 'eligible': eligible, 'evaluated': scored,
            'counts': dict(counts), 'coverage': div(scored, eligible),
            'truth_definition_rate': div(eligible, len(rows)),
            'overall_judged_fraction': div(scored, len(rows)),
            'expected_positive': pos, 'expected_negative': neg,
            'adjudicated_subset_metrics': subset, 'full_cohort_point_metrics': point,
            'eligible_subset_point_metrics': eligible_point,
            'full_cohort_bounds': bounds if not counts['unscorable'] else None,
            'eligible_subset_bounds': bounds,
            **{key: point[key] if point else None for key in subset}}


def load_observations(observations):
    from common import private_path
    private_path(observations)
    bundle = read_json(observations)
    if isinstance(bundle, list):
        if any(o.get('status') != 'pending' for o in bundle):
            raise ValueError('自由記述だけの判定は採点しません。import-auditで元記録を照合してください')
        return {'profiles': [], 'rows': bundle, 'provenance': {'legacy_pending_only': True}}
    if bundle.get('schema_version') != 2 or not isinstance(bundle.get('rows'), list):
        raise ValueError('観測の形式が不正です')
    # インポート後に元証拠や対応表を差し替えた報告は採用しない。
    proof = bundle.get('provenance', {})
    for key in ('raw', 'manifest'):
        ref = proof.get(key)
        if ref and ref.get('path'):
            private_path(ref['path'])
        if not ref or digest(ref['path']) != ref['sha256']:
            raise ValueError('元証拠の参照・指紋が一致しません')
    # 決定済み状態は元証拠から再導出する。行の手書き書換えを信頼しない。
    from observations import convert
    rebuilt = convert(read_json(proof['manifest']['path']), proof['raw']['path'])
    if bundle['profiles'] != rebuilt['profiles'] or bundle['rows'] != rebuilt['rows']:
        raise ValueError('観測行が元記録からの導出結果と一致しません')
    return bundle


def score(dataset, observations, report, axis='content', truth_profile=None):
    if axis not in AXES:
        raise ValueError('未知の正解軸です')
    truth, source = load_truth(dataset, read_json(truth_profile) if truth_profile else None)
    bundle = load_observations(observations)
    if (not bundle['provenance'].get('legacy_pending_only')
            and bundle['provenance'].get('truth_sha256') != digest(source)):
        raise ValueError('観測を作った正解表と採点時の正解表が違います')
    if (not bundle['provenance'].get('legacy_pending_only')
        and bundle['provenance'].get('truth_profile_sha256') != (digest(truth_profile) if truth_profile else None)):
        raise ValueError('観測と採点で種類の対応・評価分割の設定が違います')
    profiles = bundle['profiles'] or [{'kind': k, 'threshold': 'legacy'} for k in KINDS]
    profile_keys = [(p['kind'], p['threshold']) for p in profiles]
    if len(set(profile_keys)) != len(profile_keys):
        raise ValueError('種類と閾値の組が重複しています')
    truth_ids = {r['case_id'] for r in truth}
    lookup = {}
    for obs in bundle['rows']:
        key = (obs['case_id'], obs.get('kind'), obs.get('threshold'))
        if obs['case_id'] not in truth_ids or key in lookup or obs['status'] not in STATES:
            raise ValueError('未知・重複または不正な観測です')
        if key[1:] not in profile_keys and not bundle['provenance'].get('legacy_pending_only'):
            raise ValueError('宣言されていない規則の観測です')
        lookup[key] = obs
    matrix = []
    grouped = defaultdict(list)
    for row in truth:
        for kind, threshold in profile_keys:
            obs = lookup.get((row['case_id'], kind, threshold), {'status': 'pending'})
            if obs.get('artifact_sha256', row['sha256']) != row['sha256']:
                raise ValueError('観測と資料の指紋が一致しません')
            expected = row[AXES[axis]].get(kind)
            item = dict(row, expected=expected)
            pair = (item, obs)
            identity = f'{kind}:{threshold}'
            grouped['all:' + identity].append(pair)
            for field in ('format', 'condition', 'split', 'evaluation_track'):
                grouped[f'{field}:{row[field]}:{identity}'].append(pair)
            if row['split'] == '評価' and row['format'] == 'txt':
                if row['evaluation_track'] == 'basic':
                    grouped['primary:' + identity].append(pair)
                elif row['evaluation_track'] == 'adversarial':
                    grouped['adversarial:' + identity].append(pair)
            matrix.append({'case_id': row['case_id'], 'source_id': row['source_id'],
                           'kind': kind, 'threshold': threshold, 'expected': expected,
                           'status': obs['status'], 'evidence': obs.get('evidence', {}),
                           'evaluation_track': row['evaluation_track']})
    result = {'schema_version': 2, 'axis': axis, 'truth_sha256': digest(source),
              'observations_sha256': digest(observations), 'unique_files': len(truth),
              'source_families': len({r['source_id'] for r in truth}),
              'profiles': profiles, 'matrix': matrix,
              'groups': {key: metrics(rows) for key, rows in sorted(grouped.items())},
              'primary': {key[8:]: metrics(rows) for key, rows in sorted(grouped.items()) if key.startswith('primary:')},
              'limitations': ['主指標は基本表記の評価用TXT。回避表現・拡張形式は別集合。',
                  '同値の変形・複数規則・閾値・形式変換を独立人物として数えない。',
                  '全体点推定は全対象セル判定時だけ表示。判定済み部分と未知を含む上下限を併記。',
                  '対照と否定規則による非検知は条件付き推論であり内部走査版の直接証明ではない。']}
    write_private(report, result)
    return result
