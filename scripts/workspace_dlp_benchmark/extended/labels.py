#!/usr/bin/env python3
"""v3分類ラベルの読取りと照合。既定は計画のみ。検知完了は推論しない。"""
import argparse
import copy
import hashlib
import re
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from catalog import ITEMS
from common import digest, now, private_path, read_json, write_private
from evaluation import summary

GROUP_IDS = sorted({item['group'] for item in ITEMS.values()})
CONFIGURATIONS = ('standard', 'custom', 'combined')
META_FIELDS = 'id,version,modifiedTime,trashed,mimeType,md5Checksum'


def validate_mapping(mapping):
    """識別子は私有設定で渡す。構成の混在、欠損・重複を拒否する。"""
    if mapping.get('schema_version') != 1 or mapping.get('configuration') not in CONFIGURATIONS:
        raise ValueError('schema_version=1とstandard/custom/combinedの構成が必要です')
    files = mapping.get('files', [])
    for key in ('case_id', 'file_id'):
        values = [row.get(key) for row in files]
        if not values or any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
            raise ValueError('資料とファイルIDには空でない一意の文字列が必要です')
    groups = mapping.get('groups', {})
    if set(groups) != set(GROUP_IDS):
        raise ValueError('対象の7グループすべてのラベル対応が必要です')
    label_ids = []
    for value in groups.values():
        for key in ('label_id', 'field_id'):
            if not isinstance(value.get(key), str) or not value[key]:
                raise ValueError('ラベルIDとフィールドIDが必要です')
        choices = value.get('selection_ids')
        if (not isinstance(choices, list) or not choices or
                any(not isinstance(v, str) or not v for v in choices) or len(choices) != len(set(choices))):
            raise ValueError('照合する選択肢IDの一覧が必要です')
        label_ids.append(value['label_id'])
    if len(label_ids) != len(set(label_ids)):
        raise ValueError('v3はグループごとに異なるラベルを使います')
    return mapping


def plan(mapping):
    validate_mapping(mapping)
    return {'configuration': mapping['configuration'], 'file_count': len(mapping['files']),
            'operations': ['files.get（取得前）', 'files.listLabels（全ページ）', 'files.get（取得後）'],
            'readonly': True, 'network_executed': False,
            'limit': '現在の参照可能なラベルの読取り。DLP検査完了・付与原因を証明しない。'}


def bind_content(mapping, dataset):
    """正解表と資料SHA-256を検証し、DriveのMD5との照合値をローカルから導出。"""
    from evaluation import load_truth
    from common import input_file
    truth, _ = load_truth(dataset)
    by_case = {row['case_id']: row for row in truth}
    bound = copy.deepcopy(validate_mapping(mapping))
    for target in bound['files']:
        if target['case_id'] not in by_case:
            raise ValueError('正解に存在しない資料です')
        payload = input_file(dataset, by_case[target['case_id']]['file']).read_bytes()
        if hashlib.sha256(payload).hexdigest() != by_case[target['case_id']]['sha256']:
            raise ValueError('内容の読取り中に正解資料が変更されました')
        expected = hashlib.md5(payload, usedforsecurity=False).hexdigest()
        if target.get('expected_md5', expected) != expected:
            raise ValueError('対応表と正解資料のMD5が違います')
        target['expected_md5'] = expected
    return bound


def collect(drive, mapping):
    """注入したDriveクライアントの読取りのみを利用。ページの再循環は失敗とする。"""
    validate_mapping(mapping)
    if any(not re.fullmatch(r'[0-9a-f]{32}', target.get('expected_md5', '')) for target in mapping['files']):
        raise ValueError('読取り前にbind_contentで資料とMD5を結び付けてください')
    results = []
    for target in mapping['files']:
        row = dict(target, started_at=now(), pages=[], status='error')
        try:
            before = drive.files().get(fileId=target['file_id'], fields=META_FIELDS,
                                       supportsAllDrives=True).execute()
            row['before'] = before
            token, seen = None, set()
            while True:
                args = {'fileId': target['file_id'], 'maxResults': 100}
                if token:
                    args['pageToken'] = token
                page = drive.files().listLabels(**args).execute()
                if not isinstance(page, dict) or not isinstance(page.get('labels', []), list):
                    raise ValueError('ラベル応答の形式が不正です')
                row['pages'].append(page)
                token = page.get('nextPageToken')
                if not token:
                    break
                if not isinstance(token, str) or token in seen:
                    raise ValueError('ページ継続トークンが不正です')
                seen.add(token)
            after = drive.files().get(fileId=target['file_id'], fields=META_FIELDS,
                                      supportsAllDrives=True).execute()
            row['after'] = after
            row['status'] = snapshot_status(row)
        except Exception as exc:
            # API例外本文には識別子が含まれ得る。失敗は陰性へ変換しない。
            row['error_type'] = type(exc).__name__
        row['completed_at'] = now()
        results.append(row)
    return {'schema_version': 1, 'kind': 'v3_label_snapshot', 'mapping': mapping,
            'collected_at': now(), 'files': results,
            'limit': '一覧取得は原子的ではない。ファイル版が同じでも検査完了・ラベル版の安定・付与原因は保証しない。'}


def snapshot_status(row):
    before, after = row.get('before', {}), row.get('after', {})
    if not before or not after or not row.get('pages'):
        return 'error'
    if any(m.get('id') != row['file_id'] or not m.get('version') or
           not isinstance(m.get('trashed'), bool) for m in (before, after)):
        return 'error'
    if before['trashed'] or after['trashed']:
        return 'pending'
    if (any(m.get('mimeType') != 'text/plain' or not m.get('md5Checksum') for m in (before, after))
            or not row.get('expected_md5')):
        return 'error'
    if (before['md5Checksum'] != row['expected_md5'] or after['md5Checksum'] != row['expected_md5']):
        return 'stale'
    if before['version'] != after['version'] or before.get('modifiedTime') != after.get('modifiedTime'):
        return 'stale'
    if row['pages'][-1].get('nextPageToken'):
        return 'error'
    return 'observed'


def group_truth(row, group):
    values = [row['expected_by_item'][key] for key, item in ITEMS.items() if item['group'] == group]
    return 1 if 1 in values else None if None in values else 0


def label_value(row, binding):
    """不在はラベルの現在状態に限った不在。DLP未検知とは扱わない。"""
    state = snapshot_status(row) if row.get('status') == 'observed' else row.get('status', 'error')
    if state != 'observed':
        return None, state
    labels = [label for page in row['pages'] for label in page.get('labels', [])
              if label.get('id') == binding['label_id']]
    if not labels:
        return False, 'absent'
    if len(labels) != 1:
        return None, 'conflict'
    field = labels[0].get('fields', {}).get(binding['field_id'])
    if field is None:
        return False, 'field_absent'
    selected = field.get('selection', [])
    if field.get('valueType') != 'selection' or not isinstance(selected, list) or len(selected) > 1:
        return None, 'error'
    if not selected:
        return False, 'selection_absent'
    if selected[0] not in binding['selection_ids']:
        return None, 'unexpected_selection'
    return True, 'present'


def compare(truth, snapshot):
    mapping = validate_mapping(snapshot['mapping'])
    if snapshot.get('kind') != 'v3_label_snapshot' or snapshot.get('schema_version') != 1:
        raise ValueError('v3ラベル観測が必要です')
    expected = {row['case_id']: row for row in truth}
    if len(expected) != len(truth):
        raise ValueError('正解資料IDが重複しています')
    for row in truth:
        if set(row['expected_by_item']) != set(ITEMS) or any(v not in (0, 1, None) for v in row['expected_by_item'].values()):
            raise ValueError('31項目の正解行列が必要です')
    bindings = {r['case_id']: r for r in mapping['files']}
    if set(bindings) - set(expected):
        raise ValueError('正解に存在しない資料です')
    observed = {}
    for row in snapshot['files']:
        case = row['case_id']
        if (case in observed or case not in bindings
                or bindings[case]['file_id'] != row['file_id']
                or bindings[case].get('expected_md5') != row.get('expected_md5')):
            raise ValueError('観測と資料・ファイルの対応が違います')
        observed[case] = row
    rows, grouped = [], {g: [] for g in GROUP_IDS}
    for case, target in expected.items():
        for group in GROUP_IDS:
            value, state = label_value(observed[case], mapping['groups'][group]) if case in observed else (None, 'pending')
            result = {'case_id': case, 'group': group, 'expected': group_truth(target, group),
                      'label_present': value, 'label_state': state,
                      'detection_status': 'pending'}
            rows.append(result)
            if target['split'] == '評価':
                grouped[group].append(({'expected': result['expected']},
                                       {'status': 'pending' if value is None else 'detected' if value else 'not_detected'}))
    return {'configuration': mapping['configuration'], 'rows': rows,
            'evaluation_label_snapshot_metrics': {g: summary(v) for g, v in grouped.items()},
            'limit': '指標は参照可能なラベルの現在状態との一致。DLP検知精度・検査完了・自動付与の成功率ではない。'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mapping', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--snapshot', type=Path, help='保存した観測を通信せず照合する')
    parser.add_argument('--dataset', type=Path)
    args = parser.parse_args(argv)
    mapping = read_json(private_path(args.mapping))
    description = plan(mapping)
    if args.snapshot or args.execute:
        if not args.dataset:
            parser.error('観測と照合には--datasetが必要です')
        mapping = bind_content(mapping, args.dataset)
    if args.snapshot:
        if args.execute or not args.dataset or not args.output:
            parser.error('オフライン照合には--datasetと--outputが必要。--executeとは併用不可')
        snapshot = read_json(private_path(args.snapshot))
        if snapshot['mapping'] != mapping:
            raise ValueError('観測時の対応表と違います')
        truth_file = args.dataset / 'ground_truth.json'
        if snapshot.get('truth_sha256') != digest(truth_file):
            raise ValueError('観測時の正解表と違います')
        write_private(args.output, compare(read_json(truth_file), snapshot))
    elif args.execute:
        if not args.output or not args.dataset:
            parser.error('--executeには--outputと--datasetが必要です')
        output = private_path(args.output)
        if output.exists():
            raise ValueError('既存の観測は上書きしません')
        truth_file = args.dataset / 'ground_truth.json'
        truth_hash = digest(truth_file)
        compare(read_json(truth_file), {'schema_version': 1, 'kind': 'v3_label_snapshot',
                                       'mapping': mapping, 'files': []})
        if output.is_relative_to(args.dataset.resolve()):
            raise ValueError('実行観測はデータセットの外へ保存してください')
        import google.auth
        from googleapiclient.discovery import build
        credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'])
        snapshot = collect(build('drive', 'v3', credentials=credentials, cache_discovery=False), mapping)
        snapshot['truth_sha256'] = truth_hash
        write_private(output, snapshot)
    else:
        print(json.dumps(description, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
