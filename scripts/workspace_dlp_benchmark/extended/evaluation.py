"""v3の資料×31項目×3構成を集計する純粋関数。

ここへ渡す観測は証拠照合済みであることが前提。自由記述の実測取込みには使わない。
監査原票・設定・版との照合を行う取込器は別の境界である。
"""
from collections import defaultdict
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from catalog import GROUPS, ITEMS, UNSUPPORTED
from common import digest, input_file, read_json
from scoring import STATES, metrics

CONFIGURATIONS = ('standard', 'custom', 'combined')


def validate_truth(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('空ではないv3正解表が必要です')
    seen = set()
    for row in rows:
        case = row.get('case_id')
        if not isinstance(case, str) or not case or case in seen:
            raise ValueError('正解資料IDは空でない一意の文字列が必要です')
        seen.add(case)
        if row.get('item') not in ITEMS or row.get('group') != ITEMS[row['item']]['group']:
            raise ValueError('主項目とグループの対応が違います')
        if row.get('split') not in ('開発', '評価'):
            raise ValueError('開発・評価の分割が必要です')
        matrix = row.get('expected_by_item')
        if not isinstance(matrix, dict) or set(matrix) != set(ITEMS):
            raise ValueError('31項目すべての正解行列が必要です')
        if any(v is not None and (type(v) is not int or v not in (0, 1)) for v in matrix.values()):
            raise ValueError('正解は0・1・Noneのいずれかです')
        if matrix[row['item']] != row.get('expected'):
            raise ValueError('主項目の正解と行列が一致しません')
    return rows


def load_truth(dataset):
    source = Path(dataset) / 'ground_truth.json'
    rows = validate_truth(read_json(source))
    for row in rows:
        if digest(input_file(dataset, row['file'])) != row['sha256']:
            raise ValueError('資料の内容が生成時から変更されています')
    return rows, source


def expected_group(row, group):
    values = [row['expected_by_item'][key] for key, item in ITEMS.items() if item['group'] == group]
    return 1 if 1 in values else None if None in values else 0


def union_state(states):
    """グループのどれかで検知なら陽性。全項目の否定確認が揃うまで陰性にしない。"""
    if not states or any(state not in STATES for state in states):
        raise ValueError('空または未知の観測状態です')
    if 'detected' in states:
        return 'detected'
    if all(s == 'not_detected' for s in states):
        return 'not_detected'
    # 未完了の理由は元の項目行にも残す。複数ある場合は代表状態を一意にする。
    for state in ('conflict', 'error', 'stale', 'timeout', 'pending',
                  'conditional_not_detected', 'unsupported', 'unscorable'):
        if state in states:
            return state
    raise ValueError('空または未知の観測状態です')


def summary(pairs):
    result = metrics(pairs)
    # 判断保留の正解は主指標の母数から除外。未観測は母数から除外しない。
    result['primary_metrics'] = result['eligible_subset_point_metrics']
    return result


def reduce_matrix(truth, observations):
    """証拠照合済み観測を集計する内部処理。通信・ファイル書出しは行わない。

    この関数単体は観測の証明をしないため、任意JSONを実測として読むCLIを設けない。
    standard/custom/combinedと項目ごとの支持範囲は取込器が明示する。
    欠損を非対応と推定せず、常にpendingにする。
    """
    validate_truth(truth)
    ids = {row['case_id'] for row in truth}
    indexed = {}
    for obs in observations:
        key = (obs['case_id'], obs['item'], obs['configuration'])
        if (key[0] not in ids or key[1] not in ITEMS or key[2] not in CONFIGURATIONS
                or obs['status'] not in STATES or key in indexed):
            raise ValueError('未知・重複または不正な観測です')
        indexed[key] = obs
    matrix, group_matrix = [], []
    item_pairs, group_pairs = defaultdict(list), defaultdict(list)
    primary_item_pairs, primary_group_pairs = defaultdict(list), defaultdict(list)
    groups = sorted({item['group'] for item in ITEMS.values()})
    for row in truth:
        for configuration in CONFIGURATIONS:
            states = {}
            for item in ITEMS:
                obs = indexed.get((row['case_id'], item, configuration), {'status': 'pending'})
                if obs.get('artifact_sha256', row['sha256']) != row['sha256']:
                    raise ValueError('観測と資料の内容の検査値が違います')
                states[item] = obs['status']
                value = row['expected_by_item'][item]
                pair = ({'expected': value}, obs)
                item_pairs[configuration, item].append(pair)
                if row['split'] == '評価':
                    primary_item_pairs[configuration, item].append(pair)
                matrix.append({'case_id': row['case_id'], 'item': item, 'configuration': configuration,
                               'expected': value, 'status': obs['status'], 'split': row['split'],
                               'evidence': obs.get('evidence', {})})
            for group in groups:
                members = [key for key, item in ITEMS.items() if item['group'] == group]
                status = union_state([states[key] for key in members])
                expected = expected_group(row, group)
                pair = ({'expected': expected}, {'status': status})
                group_pairs[configuration, group].append(pair)
                if row['split'] == '評価':
                    primary_group_pairs[configuration, group].append(pair)
                group_matrix.append({'case_id': row['case_id'], 'group': group, 'configuration': configuration,
                                     'expected': expected, 'status': status,
                                     'member_states': {key: states[key] for key in members}})
    def grouped(pairs):
        return {configuration: {key: summary(values) for (c, key), values in sorted(pairs.items())
                                if c == configuration} for configuration in CONFIGURATIONS}
    return {'schema_version': 1, 'kind': 'v3_derived_metrics', 'unique_files': len(truth),
            'matrix': matrix, 'group_matrix': group_matrix,
            'evaluation_by_item': grouped(primary_item_pairs), 'evaluation_by_group': grouped(primary_group_pairs),
            'all_by_item': grouped(item_pairs), 'all_by_group': grouped(group_pairs),
            'unsupported_not_generated': UNSUPPORTED, 'groups': GROUPS,
            'limit': '内部集計の出力。原票・規則・版・範囲との証拠照合と実測取込みは別途必要。'}
