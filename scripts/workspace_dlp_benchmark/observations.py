"""公開Reports形式の原票を、版と範囲を結び付けた条件付き観測へ変換。"""
import json
from collections import defaultdict
from pathlib import Path

from common import digest, object_digest, private_path, read_json, timestamp, write_private


def read_pages(path):
    text = Path(path).read_text(encoding='utf-8')
    try:
        data = json.loads(text)
        pages = data.get('pages') if isinstance(data, dict) and isinstance(data.get('pages'), list) else [data]
    except json.JSONDecodeError:
        pages = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not pages or any(not isinstance(p, dict) for p in pages):
        raise ValueError('監査原票にはAPI応答のページ列が必要です')
    tokens = [p.get('nextPageToken') for p in pages]
    if tokens[-1] or any(not t for t in tokens[:-1]):
        raise ValueError('ページ列が途中で切れた、または途中ページの継続情報がありません')
    if len(set(tokens[:-1])) != len(tokens[:-1]):
        raise ValueError('継続トークンが重複しています')
    return pages


def parameters(event):
    result = {}
    for field in event.get('parameters', []):
        name = field['name']
        if name in result:
            raise ValueError('同名の監査項目が重複しています')
        variants = [k for k in ('value', 'intValue', 'boolValue', 'multiValue',
                                'multiIntValue', 'messageValue', 'multiMessageValue') if k in field]
        if len(variants) != 1:
            raise ValueError('監査項目の値形式が不明です')
        result[name] = field[variants[0]]
    return result


def normalize_events(pages):
    events, seen, activities = [], {}, {}
    for page in pages:
        for activity in page.get('items', []):
            aid = activity.get('id', {})
            if aid.get('applicationName') != 'rules' or not aid.get('uniqueQualifier'):
                raise ValueError('Rules原票の活動識別子が不足しています')
            at = timestamp(aid['time'])
            activity_key = (aid.get('customerId'), aid['applicationName'], aid['time'], str(aid['uniqueQualifier']))
            activity_hash = object_digest(activity)
            if activity_key in activities and activities[activity_key] != activity_hash:
                raise ValueError('同一活動識別子の元活動が矛盾しています')
            activities[activity_key] = activity_hash
            for index, item in enumerate(activity.get('events', [])):
                key = (aid.get('customerId'), aid['applicationName'], aid['time'],
                       str(aid['uniqueQualifier']), index)
                signature = object_digest(item)
                if key in seen:
                    if seen[key] != signature:
                        raise ValueError('同一活動識別子の内容が矛盾しています')
                    continue
                seen[key] = signature
                p = parameters(item)
                events.append({'event_id': ':'.join(str(k) for k in key),
                    'at': aid['time'], 'time': at,
                    'customer': aid.get('customerId'), 'name': item['name'],
                    'file_id': p.get('resource_id'),
                    'rule_id': str(p.get('rule_resource_name', p.get('rule_id', ''))),
                    'rule_name': p.get('rule_name'),
                    'rule_update_time_usec': str(p.get('rule_update_time_usec', '')),
                    'has_content_match': p.get('has_content_match'),
                    'data_source': p.get('data_source', 'DRIVE' if p.get('application') == 'drive' else None),
                    'rule_type': p.get('rule_type'),
                    'parameters': p})
    return events


def checked_reference(ref):
    if not isinstance(ref, dict) or not ref.get('path'):
        raise ValueError('照合用の保存証拠がありません')
    private_path(ref['path'])
    if digest(ref['path']) != ref.get('sha256'):
        raise ValueError('照合用の保存証拠が欠ける、または指紋が違います')
    return read_json(ref['path'])


def convert(manifest, raw):
    private_path(raw)
    if manifest.get('schema_version') != 2:
        raise ValueError('実行対応表はschema_version=2が必要です')
    if (manifest.get('match_event_names', ['rule_match']) != ['rule_match']
        or manifest.get('dlp_rule_type_values', ['DLP']) != ['DLP']):
        raise ValueError('この取込器が確認していないイベント契約へ変更できません')
    pages = read_pages(raw)
    collection = manifest['collection']
    if collection.get('complete') is not True or collection.get('page_count') != len(pages):
        raise ValueError('全ページ収集の確認がありません')
    start, end = timestamp(collection['start_time']), timestamp(collection['end_time'])
    fetched = timestamp(collection['fetched_at'])
    if not start <= end <= fetched:
        raise ValueError('取得期間の順序が不正です')
    events = normalize_events(pages)
    scope = checked_reference(manifest['scope_evidence'])
    before_policy = checked_reference(manifest['policy_before'])
    after_policy = checked_reference(manifest['policy_after'])
    # GETの全文そのものを記録し、版の変化を任意の説明文で打ち消さない。
    if before_policy['policies'] != after_policy['policies']:
        raise ValueError('観測前後で規則設定が変わっています。別の観測窓に分けてください')
    policy_index = {p['name']: p for p in before_policy['policies']}
    if len(policy_index) != len(before_policy['policies']):
        raise ValueError('設定読み戻しに重複があります')
    rule_names = [p['setting']['value']['displayName'] for p in policy_index.values()
                  if p['setting']['type'] == 'settings/rule.dlp']
    if len(rule_names) != len(set(rule_names)):
        raise ValueError('規則名が重複しており旧監査形式と一意に結べません')
    profiles, rows = manifest['profiles'], []
    if len({(p['kind'], p['threshold']) for p in profiles}) != len(profiles):
        raise ValueError('規則列が重複しています')
    files = manifest['files']
    if len({f['case_id'] for f in files}) != len(files) or len({f['file_id'] for f in files}) != len(files):
        raise ValueError('ファイル対応表が重複しています')
    indexed = defaultdict(list)
    for event in events:
        indexed[event['file_id']].append(event)
    for file in files:
        left, right = file['before'], file['after']
        identity_keys = ('owner_id', 'drive_kind', 'drive_id')
        if (not left.get('owner_id') or left.get('drive_kind') not in ('my_drive', 'shared_drive')
            or any(k not in left or k not in right for k in identity_keys)
            or (left['drive_kind'] == 'shared_drive' and not left.get('drive_id'))):
            raise ValueError('所有者とマイドライブ/共有ドライブの照合が不足しています')
        stable = (left.get('revision') == right.get('revision') == file['revision']
                  and left.get('sha256') == right.get('sha256') == file['sha256']
                  and all(left[k] == right[k] for k in identity_keys)
                  and not left.get('trashed', False)
                  and not right.get('trashed', False))
        left_at, right_at = timestamp(left['observed_at']), timestamp(right['observed_at'])
        trigger = file['trigger']
        if trigger['kind'] not in ('create', 'edit', 'rule_change'):
            raise ValueError('新規作成・編集・規則変更の契機を指定してください')
        triggered_at = timestamp(trigger['at'])
        if not start <= triggered_at <= left_at <= end <= right_at:
            raise ValueError('契機と版の読戻し時刻が不正です')
        if not (timestamp(before_policy['observed_at']) <= left_at
                and timestamp(after_policy['observed_at']) >= end):
            raise ValueError('設定の読戻しが観測期間を挟んでいません')
        for profile in profiles:
            roles = profile['roles']
            if set(roles) != {'positive', 'negative', 'head', 'tail'}:
                raise ValueError('肯定・否定・先頭・末尾の規則対応が必要です')
            canonical_ids = [r['id'] for r in roles.values()]
            if len(set(canonical_ids)) != 4:
                raise ValueError('肯定・否定・対照には異なる規則が必要です')
            rule_records = []
            from rules import expected_conditions
            conditions = expected_conditions(profile)
            for role_name, role in roles.items():
                policy = policy_index.get(role['id'])
                if not policy or object_digest(policy) != role['policy_sha256']:
                    raise ValueError('規則の読み戻しと対応表が一致しません')
                value = policy['setting']['value']
                if policy.get('customer') != 'customers/' + manifest['customer_id']:
                    raise ValueError('規則と観測の顧客が違います')
                updated = timestamp(value['updateTime'])
                from datetime import datetime, timezone
                epoch_delta = updated - datetime(1970, 1, 1, tzinfo=timezone.utc)
                usec = epoch_delta.days * 86400000000 + epoch_delta.seconds * 1000000 + epoch_delta.microseconds
                if str(usec) != str(role['update_time_usec']):
                    raise ValueError('設定の更新時刻と監査版の対応が違います')
                action = value.get('action')
                native_positive = (role_name == 'positive' and profile.get('mode') == 'native_remediation'
                    and isinstance(action, dict) and set(action) == {'driveAction'}
                    and isinstance(action['driveAction'], dict) and len(action['driveAction']) == 1
                    and next(iter(action['driveAction'])) in ('blockAccess', 'warnUser', 'restrictCopyPrintDownload', 'applyLabels'))
                if (policy['setting']['type'] != 'settings/rule.dlp'
                    or value.get('state') != 'ACTIVE'
                    or value.get('condition') != {'contentCondition': conditions[role_name]}
                    or (action != {'driveAction': {'auditOnly': {}}} and not native_positive)
                    or value.get('triggers') != ['google.workspace.drive.file.v1.share']):
                    raise ValueError('対象・否定・対照の定義が試験の意味と一致しません')
                rule_records.append(policy)
            if roles['head']['detector_id'] == roles['tail']['detector_id']:
                raise ValueError('先頭と末尾には異なる対照検知器が必要です')
            for edge in ('head', 'tail'):
                role = roles[edge]
                detector = policy_index.get(role['detector_id'])
                if (not detector or object_digest(detector) != role.get('detector_sha256')
                    or detector['setting']['type'] != 'settings/detector.word_list'
                    or detector['policyQuery'] != rule_records[0]['policyQuery']
                    or detector.get('customer') != rule_records[0].get('customer')):
                    raise ValueError('対照検知器の全文・範囲が一致しません')
                words = detector['setting']['value'].get('wordList', {}).get('words', [])
                marker = file.get('scan_control', {}).get(edge + '_token')
                if (not marker or marker not in words or len(set(words)) != len(words)
                    or len(words) > 950 or any(len(w) > 40 for w in words)):
                    raise ValueError('資料の一意な対照語と検知器定義が一致しません')
            queries = [p['policyQuery'] for p in rule_records]
            if any(q != queries[0] for q in queries):
                raise ValueError('対照と対象規則の適用範囲が異なります')
            scope_key = profile['scope_key']
            covered = any(s.get('case_id') == file['case_id'] and s.get('file_id') == file['file_id']
                          and s.get('scope_key') == scope_key and s.get('applies') is True
                          and s.get('policy_query_sha256') == object_digest(queries[0])
                          and all(s.get(k) == left[k] for k in identity_keys)
                          for s in scope.get('bindings', []))
            relevant = {role: [] for role in roles}
            weak = {role: [] for role in roles}
            since = max(start, triggered_at, left_at,
                        *(timestamp(p['setting']['value']['updateTime']) for p in rule_records))
            until = min(end, right_at)
            for event in indexed[file['file_id']]:
                if (event['customer'] != manifest['customer_id'] or event['data_source'] != 'DRIVE'
                    or event['name'] not in manifest.get('match_event_names', ['rule_match'])
                    or event['has_content_match'] is not True
                    or event['rule_type'] not in (None, 'DLP')
                    or not since <= event['time'] <= until):
                    continue
                for name, role in roles.items():
                    legacy_name_version = (event['rule_id'].isdigit()
                        and event['rule_name'] == policy_index[role['id']]['setting']['value']['displayName']
                        and event['rule_update_time_usec'] == str(role['update_time_usec']))
                    if event['rule_id'] == role['id'] or legacy_name_version:
                        # 更新版が返る旧形式ではその値も照合する。欠落を同版と仮定しない。
                        version = event['rule_update_time_usec']
                        if version and version != str(role['update_time_usec']):
                            continue
                        (relevant if version else weak)[name].append(event)
            state = 'pending'
            if not stable:
                state = 'stale'
            elif covered and relevant['positive'] and relevant['negative']:
                state = 'conflict'
            elif covered and relevant['positive']:
                state = 'detected'
            elif covered and relevant['negative'] and relevant['head'] and relevant['tail']:
                state = 'not_detected'
            elif covered and weak['positive'] and (relevant['negative'] or weak['negative']):
                state = 'conflict'
            elif covered and (weak['positive'] or weak['negative']
                              or (relevant['head'] and relevant['tail'])):
                state = 'conditional_not_detected' if not weak['positive'] else 'pending'
            evidence = {name: [e['event_id'] for e in relevant[name]] for name in roles}
            evidence['version_missing_events'] = {name: [e['event_id'] for e in weak[name]] for name in roles}
            timings = [e['time'] for role in relevant.values() for e in role]
            first_positive = min((e['time'] for e in relevant['positive']), default=None)
            rows.append({'case_id': file['case_id'], 'file_id': file['file_id'],
                'revision': file['revision'], 'artifact_sha256': file['sha256'],
                'kind': profile['kind'], 'threshold': profile['threshold'], 'status': state,
                'scope_verified': covered, 'evidence': evidence,
                'trigger': trigger, 'first_record_at': min(timings).isoformat() if timings else None,
                'detection_delay_seconds': (first_positive-triggered_at).total_seconds() if first_positive else None,
                'collection_fetched_at': collection['fetched_at'],
                'scan_version_directly_observed': False})
    return {'schema_version': 2, 'profiles': profiles, 'rows': rows,
            'method': '対照・肯定/否定・前後設定/本文読戻しに依存する条件付き観測',
            'raw_page_count': len(pages)}


def import_audit(dataset, raw, manifest_path, output, truth_profile=None):
    from scoring import load_truth
    private_path(raw)
    manifest = read_json(private_path(manifest_path))
    if truth_profile:
        private_path(truth_profile)
    truth, truth_path = load_truth(dataset, read_json(truth_profile) if truth_profile else None)
    files = {f['case_id']: f for f in manifest['files']}
    if set(files) != {r['case_id'] for r in truth}:
        raise ValueError('実行対応表が正解の全ファイルを含んでいません')
    for row in truth:
        if row['sha256'] != files[row['case_id']]['sha256']:
            raise ValueError('ローカル資料と実行対応表の指紋が違います')
        if row.get('scan_control') != files[row['case_id']].get('scan_control'):
            raise ValueError('正解資料と対照語の実行対応が違います')
    result = convert(manifest, raw)
    result['provenance'] = {'raw': {'path': str(Path(raw).resolve()), 'sha256': digest(raw)},
        'manifest': {'path': str(Path(manifest_path).resolve()), 'sha256': digest(manifest_path)},
        'truth_sha256': digest(truth_path)}
    result['provenance']['truth_profile_sha256'] = digest(truth_profile) if truth_profile else None
    write_private(output, result)
    return result
