#!/usr/bin/env python3
"""v3監査の条件照合と、証拠から再導出して採点する通信なしの入口。"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from build import combined_regex
from catalog import ITEMS
from common import digest, object_digest, private_path, read_json, write_private
from evaluation import CONFIGURATIONS, load_truth, reduce_matrix
from rules import THRESHOLDS, _resource
from controls import control_expressions

# 公開されたinfoType名による照合候補。Workspaceでの作成成功や日本語対応は別途実測する。
# Documents/Resumeは文書分類であり、職歴・学歴そのものの検出とは同義でない。
STANDARD = {
    'individual': ['JAPAN_INDIVIDUAL_NUMBER'], 'license': ['JAPAN_DRIVERS_LICENSE_NUMBER'],
    'passport': ['JAPAN_PASSPORT', 'PASSPORT'], 'card': ['CREDIT_CARD_NUMBER'],
    'bank': ['JAPAN_BANK_ACCOUNT'], 'job_history': ['DOCUMENT_TYPE/HR/RESUME'],
    'education': ['DOCUMENT_TYPE/HR/RESUME'],
    'medical_history': ['MEDICAL_TERM', 'ICD9_CODE', 'ICD10_CODE'],
    'health_checkup': ['MEDICAL_TERM'], 'race': ['ETHNIC_GROUP'],
    'password_plain': ['PASSWORD'], 'password_hash': ['WEAK_PASSWORD_HASH'],
    'email': ['EMAIL_ADDRESS'], 'phone': ['PHONE_NUMBER'], 'name': ['PERSON_NAME'],
}


def validate_standard_mapping(value):
    """標準検知器の完全表を検証する。空一覧は計画上の非対応を表す。"""
    if (not isinstance(value, dict) or type(value.get('schema_version')) is not int
            or value['schema_version'] != 1
            or set(value) != {'schema_version', 'detectors_by_item'}):
        raise ValueError('標準検知器表はschema_version=1とdetectors_by_itemが必要です')
    mapping = value['detectors_by_item']
    if not isinstance(mapping, dict) or set(mapping) != set(ITEMS):
        raise ValueError('標準検知器表には全31項目を明示してください。非対応は空一覧です')
    result = {}
    for item, detectors in mapping.items():
        if (not isinstance(detectors, list)
                or any(not isinstance(detector, str)
                       or not re.fullmatch(r'[A-Za-z0-9_./:-]+', detector) for detector in detectors)
                or len(detectors) != len(set(detectors))):
            raise ValueError('標準検知器IDは重複しない識別子・資源名の文字列一覧が必要です')
        result[item] = list(detectors)
    return result


def _unique_json_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('標準検知器表に同名のJSON項目が重複しています')
        result[key] = value
    return result


def standard_mapping(manifest):
    """私有の対応表とその指紋を読み、既定候補とは区別して証拠へ結ぶ。"""
    reference = manifest.get('standard_detector_map')
    if reference is None:
        mapping = validate_standard_mapping({'schema_version': 1,
            'detectors_by_item': {item: STANDARD.get(item, []) for item in ITEMS}})
        return mapping, {'source': 'default', 'mapping_sha256': object_digest(mapping)}
    if (not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}
            or not isinstance(reference.get('path'), str)
            or not isinstance(reference.get('sha256'), str)
            or not re.fullmatch(r'[0-9a-f]{64}', reference['sha256'])):
        raise ValueError('標準検知器表は私有のpathとsha256で参照してください')
    source = private_path(reference['path'])
    payload = source.read_bytes()
    if hashlib.sha256(payload).hexdigest() != reference['sha256']:
        raise ValueError('標準検知器表の指紋が一致しません')
    value = json.loads(payload.decode('utf-8'), object_pairs_hook=_unique_json_fields)
    mapping = validate_standard_mapping(value)
    return mapping, {'source': 'file', 'path': str(source), 'sha256': reference['sha256'],
                     'mapping_sha256': object_digest(mapping)}


def regex_string(value):
    """読み戻したStructに単一の文字列だけがある場合に限り抽出する。

    内部のフィールド名を推測してAPI要求を作らない。未知のフラグや複数値は拒否。
    """
    while isinstance(value, dict) and len(value) == 1:
        value = next(iter(value.values()))
    if not isinstance(value, str):
        raise ValueError('正規表現の内部構造を一意に照合できません')
    return value


def expected_conditions(profile, policies, standard=None):
    if standard is None:
        standard, _ = standard_mapping({})
    kind, configuration = profile['kind'], profile.get('configuration')
    if (profile.get('benchmark') != 'v3-extended' or kind not in ITEMS
            or configuration not in CONFIGURATIONS or profile['threshold'] not in THRESHOLDS):
        raise ValueError('v3の項目・構成・閾値を明示してください')
    if profile.get('mode', 'audit') != 'audit':
        raise ValueError('v3検知の採点は監査専用規則で行います')
    controls = control_expressions(profile['roles'])
    predicates = []
    if configuration in ('standard', 'combined'):
        for detector in standard.get(kind, []):
            predicates.append(f"body.matches_dlp_detector('{detector}', google.privacy.dlp.v2.Likelihood.{profile['threshold']}, {{minimum_match_count: 1, minimum_unique_match_count: 1}})")
    custom = profile.get('custom_detectors', [])
    expected_types = ['regular_expression'] + (['word_list'] if ITEMS[kind].get('word_list') else [])
    if configuration == 'standard':
        if custom:
            raise ValueError('標準のみの構成へ独自検知器を混ぜません')
    else:
        if (not isinstance(custom, list) or sorted(d.get('kind', '') for d in custom) != sorted(expected_types)
                or len({d['id'] for d in custom}) != len(custom)):
            raise ValueError('項目の正規表現と語句一覧の対応が不足・重複しています')
        positive = policies[profile['roles']['positive']['id']]
        for reference in custom:
            _resource(reference['id'])
            detector = policies.get(reference['id'])
            if (not detector or object_digest(detector) != reference.get('sha256')
                    or detector.get('customer') != positive.get('customer')
                    or detector.get('policyQuery') != positive.get('policyQuery')
                    or detector.get('setting', {}).get('type') != 'settings/detector.' + reference['kind']):
                raise ValueError('独自検知器の全文・顧客・適用範囲が違います')
            value = detector['setting']['value']
            if reference['kind'] == 'regular_expression':
                if regex_string(value.get('regularExpression')) != combined_regex(kind):
                    raise ValueError('独自正規表現がv3の定義と違います')
                predicates.append(f"body.matches_regex_detector('{reference['id']}', {{minimum_match_count: 1}})")
            else:
                if value.get('wordList') != {'words': ITEMS[kind]['word_list']}:
                    raise ValueError('語句一覧がv3の定義と違います')
                predicates.append(f"body.matches_word_list('{reference['id']}', {{minimum_match_count: 1, minimum_unique_match_count: 1}})")
    if not predicates:
        raise ValueError('標準検知器のない項目に標準規則を作りません。非対応として明示してください')
    predicate = ' || '.join('(' + p + ')' for p in predicates)
    both = f"({controls['head']}) && ({controls['tail']})"
    return {**controls, 'positive': f'{both} && ({predicate})', 'negative': f'{both} && !({predicate})'}


def import_audit(dataset, raw, manifest, output):
    from observations import import_audit as common_import
    if read_json(private_path(manifest)).get('benchmark') != 'v3-extended':
        raise ValueError('v3の対応表が必要です')
    return common_import(dataset, raw, manifest, output)


def score(dataset, observations, output):
    from scoring import load_observations
    truth, source = load_truth(dataset)
    paths = observations if isinstance(observations, (list, tuple)) else [observations]
    profiles, all_rows, inputs, seen_profiles = [], [], [], set()
    mapping = None
    mapping_sha256 = None
    for path in paths:
        bundle = load_observations(path)
        proof = bundle['provenance']
        if proof.get('truth_sha256') != digest(source) or proof.get('truth_profile_sha256') is not None:
            raise ValueError('v3の正解表と観測が結び付いていません')
        manifest = read_json(private_path(proof['manifest']['path']))
        if manifest.get('benchmark') != 'v3-extended':
            raise ValueError('v3の証拠照合を通した観測が必要です')
        current_mapping, mapping_reference = standard_mapping(manifest)
        if bundle.get('standard_detector_map') != mapping_reference:
            raise ValueError('観測と標準検知器表の結び付けが違います')
        if mapping_sha256 is not None and mapping_sha256 != mapping_reference['mapping_sha256']:
            raise ValueError('異なる標準検知器表を同じ比較へ混ぜません')
        mapping, mapping_sha256 = current_mapping, mapping_reference['mapping_sha256']
        for profile in bundle['profiles']:
            key = (profile['kind'], profile['configuration'], profile['threshold'])
            if key in seen_profiles:
                raise ValueError('同じ項目・構成・閾値の観測窓が重複しています。自動で選択しません')
            seen_profiles.add(key)
            profiles.append(profile)
        all_rows.extend(bundle['rows'])
        inputs.append({'path': str(private_path(path)), 'sha256': digest(path),
                       'standard_detector_map': mapping_reference})
    # 閾値ごとに別の資料×項目×構成の行列を出す。欠損セルは集計側でpending。
    thresholds = sorted({p['threshold'] for p in profiles})
    if not thresholds:
        raise ValueError('採点する規則列がありません')
    reports = {}
    for threshold in thresholds:
        rows = []
        for obs in all_rows:
            if obs['threshold'] == threshold:
                rows.append(dict(obs, item=obs['kind']))
        # 「標準規則のない項目」は負例でなく、定義上の非対応として明示する。
        for row in truth:
            for item in ITEMS:
                if not mapping[item]:
                    rows.append({'case_id': row['case_id'], 'item': item,
                                 'configuration': 'standard', 'status': 'unsupported'})
        reports[threshold] = reduce_matrix(truth, rows)
    result = {'schema_version': 1, 'benchmark': 'v3-extended',
              'truth_sha256': digest(source), 'observation_sources': inputs,
              'standard_mapping_sha256': mapping_sha256,
              'by_threshold': reports,
              'primary': {threshold: report['evaluation_by_group'] for threshold, report in reports.items()},
              'limits': ['標準infoTypeの対応は照合候補。Workspaceでの利用成功・日本語性能を保証しない。',
                         '監査専用の項目規則を採点する。ラベル出力用14規則とは別。',
                         '内部再検査の1回目・2回目との対応は推論しない。']}
    write_private(output, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    imp = sub.add_parser('import-audit')
    imp.add_argument('--dataset', required=True, type=Path)
    imp.add_argument('--raw', required=True, type=Path)
    imp.add_argument('--manifest', required=True, type=Path)
    imp.add_argument('--output', required=True, type=Path)
    scoring = sub.add_parser('score')
    scoring.add_argument('--dataset', required=True, type=Path)
    scoring.add_argument('--observations', required=True, type=Path, nargs='+')
    scoring.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == 'import-audit':
        result = import_audit(args.dataset, args.raw, args.manifest, args.output)
        print('取込み行数:', len(result['rows']))
    else:
        result = score(args.dataset, args.observations, args.output)
        print('採点した閾値:', len(result['by_threshold']))


if __name__ == '__main__':
    main()
