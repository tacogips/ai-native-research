"""是正の状態遷移計画と、別主体の読取・動作記録を使う採点。外部変更は行わない。"""
from collections import Counter, defaultdict
from itertools import product

from common import digest, read_json, timestamp, write_private, private_path
from observations import checked_reference, normalize_events, read_pages

ACTIONS = ('block_sharing', 'warn_external', 'restrict_copy_print_download', 'apply_label')
SHARING = ('restricted', 'external_user', 'external_group', 'anyone_link', 'shared_drive')
ACTORS = ('owner', 'editor', 'external_reader')
TRIGGERS = ('create', 'edit', 'rule_change')


def plan_remediation(output, config=None):
    cases = []
    for action, sharing, actor, trigger in product(ACTIONS, SHARING, ACTORS, TRIGGERS):
        cases.append({'case_id': '/'.join((action, sharing, actor, trigger)),
            'action': action, 'prior_sharing': sharing, 'operator_role': actor,
            'trigger_kind': trigger, 'should_protect': True,
            'mechanism': 'native_dlp', 'execution': 'requires_environment', 'expected_outcome': {
                'block_sharing': 'denied', 'warn_external': 'warning',
                'restrict_copy_print_download': 'operation_denied', 'apply_label': 'label_present'}[action],
            'required_evidence': ['scope', 'policy_readbacks', 'baseline_control',
                                  'external_probes', 'action_record', 'permission_readbacks']})
    supplements = [
        ('release/content_removed', 'release', 'content_removed', True, 'readable'),
        ('release/rule_disabled', 'release', 'rule_disabled', True, 'readable'),
        ('release/rule_deleted', 'release', 'rule_deleted', True, 'readable'),
        ('release/user_changed_label', 'release_label', 'content_removed', True, 'label_preserved'),
        ('bypass/copy', 'bypass', 'copy', True, None),
        ('bypass/export', 'bypass', 'export', True, None),
        ('bypass/move_shared_drive', 'bypass', 'move', True, None),
        ('bypass/change_owner', 'bypass', 'owner_change', True, None),
        ('bypass/apps_script', 'bypass', 'apps_script', True, None),
        ('bypass/external_app', 'bypass', 'external_app', True, None),
        ('conflict/actions', 'conflict', 'edit', True, None),
        ('two_stage/label_then_block', 'two_stage', 'edit', True, 'denied'),
    ]
    for name, action, trigger, protect, expected in supplements:
        cases.append({'case_id': name, 'action': action, 'trigger_kind': trigger,
            'should_protect': protect, 'expected_outcome': expected, 'mechanism': 'native_dlp',
            'execution': 'manual_or_adapter_required'})
    for action in ACTIONS:
        cases.append({'case_id': 'overblocking/' + action, 'action': action,
            'trigger_kind': 'edit', 'should_protect': False,
            'expected_outcome': 'readable', 'mechanism': 'native_dlp', 'execution': 'requires_environment'})
    if config:
        config = private_path(config)
        bindings = read_json(config).get('bindings', {})
        if set(bindings) - {c['case_id'] for c in cases}:
            raise ValueError('未知の是正計画へ対応情報を指定しています')
        for case in cases:
            # 試験因子は変えず、実行前に期待する具体値だけを固定する。
            binding = bindings.get(case['case_id'], {})
            if set(binding) - {'expected_label', 'expected_action_fragment', 'removed_values', 'expected_outcome'}:
                raise ValueError('是正計画の未知の対応項目です')
            if 'expected_outcome' in binding:
                fixed = case['expected_outcome']
                allowed = {'bypass': {'denied'},
                           'conflict': {'denied', 'warning', 'operation_denied', 'label_present'}}.get(case['action'], set())
                if ((fixed is not None and binding['expected_outcome'] != fixed)
                    or (fixed is None and binding['expected_outcome'] not in allowed)):
                    raise ValueError('既定の期待結果は変更できません。未定義の行だけ対応する結果を固定できます')
            case.update(binding)
    plan = {'schema_version': 1, 'cases': cases,
        'mechanisms': ['native_dlp', 'custom_acl', 'owner_manual'],
        'notes': ['状態遷移の事前計画であり製品での実行結果ではない。',
                  '未対応の経路はunsupported、未実行はpendingとして分母へ残す。',
                  '迂回・競合で期待結果が未定義の行は、公開仕様と適用範囲を確認して別の事前計画へ固定する。',
                  'Driveの読取拒否、権限削除、IRM、警告、ラベルを異なる結果として採点する。']}
    write_private(output, plan)
    return plan


def contains_fragment(value, fragment):
    if isinstance(fragment, list):
        if not isinstance(value, list):
            return False
        unused = list(value)
        for expected in fragment:
            index = next((i for i, actual in enumerate(unused) if contains_fragment(actual, expected)), None)
            if index is None:
                return False
            unused.pop(index)
        return True
    if isinstance(value, list):
        return any(contains_fragment(v, fragment) for v in value)
    if isinstance(fragment, dict):
        return isinstance(value, dict) and all(k in value and contains_fragment(value[k], v) for k, v in fragment.items())
    return value == fragment


def external_probes(reference, file_id, email, domains):
    report = checked_reference(reference)
    probes = list(report.get('probes', []))
    for sheet in report.get('sheets', []):
        probes.extend(sheet.get('access_observations', []))
    if '@' not in email or email.rsplit('@', 1)[1].casefold() in {d.casefold() for d in domains}:
        raise ValueError('観測主体は指定組織外の別アカウントにしてください')
    result = []
    for probe in probes:
        if probe.get('file_id') != file_id or probe.get('actor_email', '').casefold() != email.casefold():
            continue
        before, after = probe.get('owner_before', {}), probe.get('owner_after', {})
        stable = (before.get('id') == after.get('id') == file_id
                  and bool(before.get('version')) and not after.get('trashed', False)
                  and all(before.get(k) == after.get(k) for k in ('version', 'headRevisionId', 'md5Checksum', 'modifiedTime')))
        full = all(probe.get(k, {}).get('complete') is True for k in ('permissions_before', 'permissions_after'))
        if (probe.get('test_kind') != 'external_access_probe' or not stable or not full
            or probe.get('same_revision_during_probe') is not True
            or probe.get('permission_mutation_by_probe') is not False):
            continue
        if probe.get('outcome') == 'denied':
            status, reason = probe.get('http_status'), probe.get('denial_reason')
            if not ((status == 403 and reason in ('insufficientFilePermissions', 'forbidden_permission'))
                    or (status == 404 and reason == 'notFound')):
                continue
        if probe.get('outcome') == 'readable' and probe.get('http_status', 200) != 200:
            continue
        if timestamp(probe['started_at']) > timestamp(probe['finished_at']):
            raise ValueError('外部読取の時刻順序が不正です')
        if probe['outcome'] in ('readable', 'denied', 'error', 'unverified'):
            result.append(probe)
    return sorted(result, key=lambda p: timestamp(p['started_at']))


def exposure(probes, trigger_at, until):
    start, end = timestamp(trigger_at), timestamp(until)
    sampled = [p for p in probes if start <= timestamp(p['started_at'])
               and timestamp(p['finished_at']) <= end]
    readable = [p for p in sampled if p['outcome'] == 'readable']
    last_read = max((timestamp(p['started_at']) for p in readable), default=start)
    denied = [p for p in sampled if p['outcome'] == 'denied' and timestamp(p['started_at']) > last_read]
    first = min((timestamp(p['finished_at']) for p in denied), default=None)
    first_denial_start = min((timestamp(p['started_at']) for p in sampled if p['outcome'] == 'denied'), default=None)
    return {'lower_seconds': max(0, (last_read-start).total_seconds()),
            'upper_seconds': (first-start).total_seconds() if first else None,
            'right_censored': first is None,
            'observed_until_seconds': (end-start).total_seconds(),
            'reexposure_observed': bool(first_denial_start and any(timestamp(p['started_at']) > first_denial_start for p in readable)),
            'continuous_monitoring': False}


def policy_version(policy, rule_id, customer):
    if (not isinstance(policy, dict) or policy.get('name') != rule_id
        or policy.get('customer') != 'customers/' + customer
        or policy.get('type') != 'ADMIN' or policy.get('setting', {}).get('type') != 'settings/rule.dlp'):
        raise ValueError('是正規則の実体・顧客・種別が一致しません')
    from datetime import datetime, timezone
    delta = timestamp(policy['setting']['value']['updateTime']) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return str(delta.days*86400000000 + delta.seconds*1000000 + delta.microseconds)


def negative_evaluation(obs, policy, latest):
    """単なる無動作でなく、同じ条件の否定規則まで元原票から再照合する。"""
    reference = obs.get('evaluation_confirmation')
    if not reference:
        return False
    checked_reference(reference)
    from scoring import load_observations
    from rules import expected_conditions
    bundle = load_observations(reference['path'])
    manifest = read_json(bundle['provenance']['manifest']['path'])
    if manifest.get('customer_id') != obs['customer_id']:
        return False
    policies = checked_reference(manifest['policy_before'])['policies']
    raw_events = normalize_events(read_pages(bundle['provenance']['raw']['path']))
    target_revision = latest['owner_after'].get('headRevisionId') or latest['owner_after']['version']
    for row in bundle['rows']:
        if (row['file_id'] != obs['file_id'] or row['revision'] != target_revision
            or row['status'] != 'not_detected'):
            continue
        profile = next(p for p in bundle['profiles'] if p['kind'] == row['kind'] and p['threshold'] == row['threshold'])
        source_policy = next(p for p in policies if p['name'] == profile['roles']['positive']['id'])
        negative_ids = set(row['evidence']['negative'])
        in_window = any(e['event_id'] in negative_ids and timestamp(obs['trigger_at']) <= e['time'] <= timestamp(obs['observation_end']) for e in raw_events)
        if (in_window and policy['customer'] == source_policy['customer']
            and policy['policyQuery'] == source_policy['policyQuery']
            and policy['setting']['value']['condition'] == {'contentCondition': expected_conditions(profile)['positive']}):
            return True
    return False


def label_shape(label):
    return (isinstance(label, dict) and bool(label.get('id')) and isinstance(label.get('fields'), dict)
            and bool(label['fields']) and all(isinstance(v, dict) and isinstance(v.get('selection'), list)
            and bool(v['selection']) and all(isinstance(x, str) and x for x in v['selection'])
            for v in label['fields'].values()))


def case_context(case, obs, domains):
    """組合せの根拠を別保存の合成記録へ結合する。実契機の収集器は未実装。"""
    reference = obs.get('case_context')
    if not reference:
        return None, '共有状態・操作者・契機の別保存証拠がない'
    context = checked_reference(reference)
    if (context.get('schema_version') != 1
        or any(context.get(k) != obs.get(k) for k in ('file_id', 'trigger_at'))
        or context.get('case_id') != case['case_id']):
        return None, '状態遷移の文脈と計画・対象・契機時刻が一致しない'
    for factor in ('prior_sharing', 'operator_role', 'trigger_kind'):
        if factor in case and context.get(factor) != case[factor]:
            return None, '事前計画の試験因子と別保存証拠が一致しない'
    if not context.get('baseline_probe') or not context.get('trigger_record'):
        return None, '事前状態または操作契機の原記録がない'
    record = checked_reference(context['trigger_record'])
    # この値は実製品の応答ではない。未実装の実収集器を手記で代用しない。
    if record.get('source') != 'synthetic_fixture':
        return None, '実契機の収集・照合アダプターは未実装'
    if (record.get('schema_version') != 1 or record.get('case_id') != case['case_id']
        or record.get('file_id') != obs['file_id'] or record.get('rule_id') != obs['rule_id']
        or record.get('kind') != case['trigger_kind']
        or timestamp(record['at']) != timestamp(obs['trigger_at'])):
        return None, '操作契機の原記録と計画・対象・規則・時刻が一致しない'
    prior = external_probes(context['baseline_probe'], obs['file_id'], obs['external_email'], domains)
    prior = [p for p in prior if p.get('mechanism') == obs['probe_route']
             and timestamp(p['finished_at']) < timestamp(obs['trigger_at'])]
    if not prior:
        return None, '対象資料の契機前の完全な状態記録がない'
    snapshot = prior[-1]
    owner = snapshot['owner_after']
    permissions = [p for p in snapshot['permissions_after']['permissions']
                   if not p.get('deleted') and p.get('role') != 'owner']
    internal = {d.casefold() for d in domains}
    def outside(email):
        return isinstance(email, str) and '@' in email and email.rsplit('@', 1)[1].casefold() not in internal
    has_anyone = any(p.get('type') == 'anyone' for p in permissions)
    has_group = any(p.get('type') == 'group' and outside(p.get('emailAddress')) for p in permissions)
    has_user = any(p.get('type') == 'user' and outside(p.get('emailAddress')) for p in permissions)
    # 混合共有を一つの因子へ勝手に分類しない。共有ドライブはdriveIdで識別する。
    if owner.get('driveId'):
        sharing = 'shared_drive'
    elif sum((has_anyone, has_group, has_user)) > 1:
        sharing = None
    elif has_anyone:
        sharing = 'anyone_link'
    elif has_group:
        sharing = 'external_group'
    elif has_user:
        sharing = 'external_user'
    elif any(p.get('type') == 'domain' or (p.get('type') in ('user', 'group') and not p.get('emailAddress')) for p in permissions):
        sharing = None
    else:
        sharing = 'restricted'
    if 'prior_sharing' in case and sharing != case['prior_sharing']:
        return None, '事前の完全ACL・ドライブ種別が計画の共有状態を裏付けない'
    actor = record.get('actor_email', '').casefold()
    owners = {p.get('emailAddress', '').casefold() for p in owner.get('owners', [])}
    roles = {p.get('role') for p in permissions if p.get('type') == 'user'
             and p.get('emailAddress', '').casefold() == actor}
    operator = ('owner' if actor and actor in owners else
                'editor' if roles & {'writer', 'organizer', 'fileOrganizer'} else
                'external_reader' if outside(actor) and 'reader' in roles else None)
    if 'operator_role' in case and operator != case['operator_role']:
        return None, '操作主体と事前所有者・権限の記録が計画の役割を裏付けない'
    return 'synthetic', None


def evaluate_case(case, obs, domains):
    for field in ('expected_action_fragment', 'expected_label'):
        if field in case and field in obs and case[field] != obs[field]:
            raise ValueError('事前固定した期待値を観測側で上書きできません')
    mechanism = obs.get('mechanism')
    if mechanism not in ('native_dlp', 'custom_acl', 'owner_manual'):
        raise ValueError('是正主体の区分が不正です')
    result = {'case_id': case['case_id'], 'action': case['action'], 'mechanism': mechanism,
              'status': 'pending', 'should_protect': case['should_protect'],
              'evidence_domain': 'unverified'}
    start, end = timestamp(obs['trigger_at']), timestamp(obs['observation_end'])
    if end < start or not domains:
        raise ValueError('観測期間または組織ドメインが不正です')
    if case['trigger_kind'] == 'create':
        return dict(result, reason='新規作成専用の事前対照・共有状態の収集アダプターは未実装')
    domain, reason = case_context(case, obs, domains)
    if reason:
        return dict(result, reason=reason)
    result['evidence_domain'] = domain
    scope = checked_reference(obs['scope_evidence'])
    if not any(b.get('file_id') == obs['file_id'] and b.get('rule_id') == obs['rule_id']
               and b.get('applies') is True for b in scope.get('bindings', [])):
        return dict(result, reason='適用範囲の証拠不足')
    baseline = external_probes(obs['baseline_control'], obs['baseline_file_id'], obs['external_email'], domains)
    if not any(p['outcome'] == 'readable' and p.get('mechanism') == obs['probe_route']
               and timestamp(p['finished_at']) <= start for p in baseline):
        return dict(result, reason='同じ外部主体・経路の事前対照が読めることを未確認')
    probes = external_probes(obs['probe_report'], obs['file_id'], obs['external_email'], domains)
    probes = [p for p in probes if p.get('mechanism') == obs['probe_route']
              and start <= timestamp(p['started_at']) and timestamp(p['finished_at']) <= end]
    baseline_routes = {p.get('mechanism') for p in baseline if p['outcome'] == 'readable'}
    if obs['probe_route'] not in baseline_routes or not probes:
        return dict(result, reason='同じ経路の外部読取記録がない')
    result['exposure_interval'] = exposure(probes, obs['trigger_at'], obs['observation_end'])
    latest = probes[-1]
    result['latest_access_outcome'] = latest['outcome']
    result['residual_external_permissions'] = sum(
        p.get('type') in ('anyone', 'group', 'domain') or
        (p.get('type') == 'user' and p.get('emailAddress', '').rsplit('@', 1)[-1].casefold() not in {d.casefold() for d in domains})
        for p in latest['permissions_after']['permissions'] if p.get('role') != 'owner' and not p.get('deleted'))
    result['permission_count_limit'] = 'group/domainは所属照会していない潜在権限。DLPによる論理遮断でもACLは残り得る。'
    expected = case.get('expected_outcome')
    if expected is None:
        return dict(result, reason='事前計画で期待結果が未確定')
    if latest['outcome'] not in ('readable', 'denied'):
        return dict(result, reason='外部読取が失敗または未確認')
    if mechanism == 'owner_manual':
        return dict(result, status='owner_manual_only', reason='所有者による手動権限操作はDLP是正の証拠ではない')
    if mechanism == 'custom_acl':
        return dict(result, status='unsupported', reason='自作是正の実行主体・削除応答との接続アダプターは未実装')
    if mechanism != case.get('mechanism', 'native_dlp'):
        return dict(result, reason='事前計画と観測の是正主体が異なる')
    release = case['action'] in ('release', 'release_label')
    all_target = external_probes(obs['probe_report'], obs['file_id'], obs['external_email'], domains)
    target_before = [p for p in baseline + all_target if p['file_id'] == obs['file_id']
                     and p.get('mechanism') == obs['probe_route'] and timestamp(p['finished_at']) < start]
    target_readable = [p for p in target_before + probes if p['outcome'] == 'readable'
                       and timestamp(p['finished_at']) < timestamp(latest['started_at'])]
    if release:
        if not any(p['outcome'] == 'denied' for p in target_before):
            return dict(result, reason='解除前の対象資料の拒否を未確認')
    elif not target_readable:
        return dict(result, reason='対象資料自体の事前可読性を未確認')
    policies = checked_reference(obs['policy_readbacks'])
    if (policies.get('file_id') != obs['file_id']
        or policies.get('rule_id') != obs['rule_id']
        or timestamp(policies['before_at']) > start or timestamp(policies['after_at']) < end):
        return dict(result, reason='是正規則と適用版の前後照合がない')
    before, after = policies.get('before'), policies.get('after')
    version = policy_version(before, obs['rule_id'], obs['customer_id'])
    if before['setting']['value'].get('state') != 'ACTIVE' or version != str(obs.get('rule_update_time_usec')):
        return dict(result, reason='是正前の有効な規則版を未確認')
    action_key = {'block_sharing': 'blockAccess', 'two_stage': 'blockAccess', 'bypass': 'blockAccess',
                  'warn_external': 'warnUser', 'restrict_copy_print_download': 'restrictCopyPrintDownload',
                  'apply_label': 'applyLabels', 'release': 'blockAccess', 'release_label': 'applyLabels'}.get(case['action'])
    if action_key and action_key not in before['setting']['value'].get('action', {}).get('driveAction', {}):
        return dict(result, reason='計画の是正動作と規則の動作が違う')
    if not release:
        policy_version(after, obs['rule_id'], obs['customer_id'])
        if before != after:
            return dict(result, reason='是正窓の途中で規則が変化')
    else:
        change = checked_reference(obs['change_evidence'])
        kind = case['trigger_kind']
        if (change.get('file_id') != obs['file_id'] or change.get('rule_id') != obs['rule_id']
            or change.get('kind') != kind or not start <= timestamp(change['changed_at']) <= end):
            return dict(result, reason='解除操作の対象・契機が一致しない')
        if kind == 'rule_disabled':
            policy_version(after, obs['rule_id'], obs['customer_id'])
            if (after['setting']['value'].get('state') != 'INACTIVE'
                or not start <= timestamp(after['setting']['value']['updateTime']) <= timestamp(change['changed_at'])
                or timestamp(after['setting']['value']['updateTime']) <= timestamp(before['setting']['value']['updateTime'])):
                return dict(result, reason='規則の無効化を未確認')
        elif kind == 'rule_deleted':
            listing = checked_reference(change['complete_policy_list'])
            if (after is not None or listing.get('complete') is not True
                or listing.get('customer') != before['customer']
                or timestamp(listing['observed_at']) < timestamp(change['changed_at'])
                or any(p.get('name') == obs['rule_id'] for p in listing['policies'])):
                return dict(result, reason='規則の完全一覧からの消失を未確認')
        elif kind == 'content_removed':
            policy_version(after, obs['rule_id'], obs['customer_id'])
            if before != after:
                return dict(result, reason='本文変更と同時に規則が変化')
            old_text, new_text = checked_reference(change['before_text']), checked_reference(change['after_text'])
            values = case.get('removed_values')
            protected_before = max((p for p in target_before if p['outcome'] == 'denied'),
                                   key=lambda p: timestamp(p['finished_at']))
            old_revision = protected_before['owner_after'].get('headRevisionId') or protected_before['owner_after']['version']
            new_revision = latest['owner_after'].get('headRevisionId') or latest['owner_after']['version']
            if (not values or old_text.get('file_id') != obs['file_id'] or new_text.get('file_id') != obs['file_id']
                or old_text.get('revision') == new_text.get('revision')
                or old_text.get('revision') != old_revision or new_text.get('revision') != new_revision
                or not all(v in old_text['text'] and v not in new_text['text'] for v in values)):
                return dict(result, reason='事前固定の対象値が現版の本文から除去されたことを未確認')
        else:
            return dict(result, reason='未対応の解除契機')
        if timestamp(latest['started_at']) < timestamp(change['changed_at']):
            return dict(result, reason='解除後の読取記録がない')
        inverted = [dict(p, outcome={'denied': 'readable', 'readable': 'denied'}.get(p['outcome'], p['outcome']))
                    for p in probes]
        result['release_interval'] = exposure(inverted, change['changed_at'], obs['observation_end'])
        result['release_interval']['reblock_observed'] = result['release_interval'].pop('reexposure_observed')
    events = normalize_events(read_pages(obs['audit']['path']))
    if digest(obs['audit']['path']) != obs['audit']['sha256']:
        raise ValueError('動作原票の指紋が一致しません')
    matched = [e for e in events if e['file_id'] == obs['file_id'] and e['rule_id'] == obs['rule_id']
               and e['customer'] == obs['customer_id'] and e['data_source'] == 'DRIVE'
               and e['rule_type'] == 'DLP' and e['rule_update_time_usec'] in ('', version)
               and (e['time'] <= start if release else start <= e['time'] <= end)
               and e['name'] == 'action_complete']
    fragment = case.get('expected_action_fragment')
    if not isinstance(fragment, dict) or not fragment:
        return dict(result, reason='監査動作の構造化対応が未定義')
    fired = [e for e in matched if contains_fragment(e['parameters'].get('triggered_actions'), fragment)]
    suppressed = [e for e in matched if contains_fragment(e['parameters'].get('suppressed_actions'), fragment)]
    result['triggered_action_event_ids'] = [e['event_id'] for e in fired]
    result['suppressed_action_event_ids'] = [e['event_id'] for e in suppressed]
    result['version_binding'] = ('event_and_policy' if fired and all(e['rule_update_time_usec'] for e in fired)
                                 else 'policy_readback_bracket')
    result['attribution'] = '動作記録と状態遷移の併存。他規則を排除した因果証明ではない。'
    evaluated_negative = not case['should_protect'] and negative_evaluation(obs, before, latest)
    if mechanism == 'native_dlp' and not fired and not evaluated_negative:
        return dict(result, status='suppressed' if suppressed else 'pending', reason='対象規則の動作実行記録がない')
    if case['action'] in ('block_sharing', 'two_stage', 'bypass', 'release'):
        passed = latest['outcome'] == expected
    elif case['action'] == 'restrict_copy_print_download':
        if obs['probe_route'] not in ('download', 'print', 'copy', 'export'):
            return dict(result, reason='Sheets本文の読取だけではIRMを判定できない')
        if latest.get('actor_role') != case.get('operator_role'):
            return dict(result, reason='持出し操作の実主体の役割が事前計画と違う')
        passed = latest['outcome'] == ('denied' if case['should_protect'] else 'readable')
    else:
        state = checked_reference(obs['state_readback'])
        if (state.get('file_id') != obs['file_id'] or state.get('rule_id') != obs['rule_id']
            or timestamp(state['observed_at']) < start or timestamp(state['observed_at']) > end):
            return dict(result, reason='警告・ラベルの状態照合がない')
        if case['action'] == 'warn_external':
            passed = (state.get('warning_shown') is True and state.get('decision') in ('cancel', 'override')
                      and state.get('actor_role') == case.get('operator_role')) if case['should_protect'] else state.get('warning_shown') is False
            result['warning_decision'] = state.get('decision')
        elif case['action'] in ('apply_label', 'release_label'):
            target = case.get('expected_label')
            if not label_shape(target):
                return dict(result, reason='期待するラベルID・値が未定義')
            present = contains_fragment(state.get('labels', []), target)
            passed = present if expected in ('label_present', 'label_preserved') else not present
        else:
            return dict(result, reason='この状態遷移の実行アダプターは未対応')
    if not case['should_protect'] and any(p['outcome'] == 'denied' for p in probes):
        passed = False
    return dict(result, status='succeeded' if passed else 'failed',
                overblocked=(not case['should_protect'] and not passed))


def score_remediation(plan_path, observations, report):
    private_path(plan_path)
    private_path(observations)
    plan, bundle = read_json(plan_path), read_json(observations)
    if bundle.get('plan_sha256') != digest(plan_path):
        raise ValueError('事前計画が実行後に変更されたか、別の計画です')
    cases = {c['case_id']: c for c in plan['cases']}
    if len(cases) != len(plan['cases']):
        raise ValueError('計画の識別子が重複しています')
    lookup = {}
    for item in bundle['observations']:
        if item['case_id'] not in cases or item['case_id'] in lookup:
            raise ValueError('未知または重複の状態遷移です')
        lookup[item['case_id']] = item
    rows = []
    for key, case in cases.items():
        item = lookup.get(key)
        if item is None or item.get('status') in ('pending', 'unsupported', 'error'):
            rows.append({'case_id': key, 'action': case['action'], 'mechanism': (item or {}).get('mechanism', 'unassigned'),
                         'should_protect': case['should_protect'], 'status': (item or {}).get('status', 'pending')})
        else:
            rows.append(evaluate_case(case, item, bundle['organization_domains']))
    groups = defaultdict(list)
    for row in rows:
        row['planned_mechanism'] = cases[row['case_id']].get('mechanism', 'native_dlp')
        row.setdefault('evidence_domain', 'unverified')
        groups[row['planned_mechanism'] + ':' + row['action']].append(row)
    summaries = {}
    for key, values in groups.items():
        counts = Counter(v['status'] for v in values)
        evaluated = counts['succeeded'] + counts['failed']
        by_domain = {}
        for domain in sorted({v['evidence_domain'] for v in values}):
            domain_rows = [v for v in values if v['evidence_domain'] == domain]
            judged_rows = [v for v in domain_rows if v['status'] in ('succeeded', 'failed')]
            negatives = [v for v in judged_rows if not v['should_protect']]
            successes = sum(v['status'] == 'succeeded' for v in judged_rows)
            by_domain[domain] = {
                'assigned': len(domain_rows), 'evaluated': len(judged_rows), 'succeeded': successes,
                'adjudicated_success_rate': successes / len(judged_rows) if judged_rows else None,
                'overblocking_rate': sum(v.get('overblocked', False) for v in negatives)/len(negatives) if negatives else None}
        summaries[key] = {'planned': len(values), 'evaluated': evaluated, 'counts': dict(counts),
            'coverage': evaluated / len(values),
            'adjudicated_success_rate': None,
            'full_plan_success_rate': None,
            'product_measured_success_rate': None,
            'overblocking_rate': None,
            'by_evidence_domain': by_domain}
    judged = sum(r['status'] in ('succeeded', 'failed') for r in rows)
    result = {'plan_sha256': digest(plan_path), 'observations_sha256': digest(observations),
              'planned': len(rows), 'evaluated': judged, 'coverage': judged / len(rows) if rows else None,
              'full_plan_success_rate': None,
              'product_measured_success_rate': None,
              'cases': rows, 'groups': summaries,
              'limits': ['是正・解除・警告・ラベルは別の指標。手動の権限取消をnative_dlpへ合算しない。',
                         '露出時間は標本間の区間または右打切り。正確な実行時刻・連続無露出の保証ではない。',
                         '未対応・未実行を成功にも過剰遮断なしにも変換しない。',
                         'syntheticは合成証拠の採点試験であり製品の成功率ではない。実契機の収集器は未実装。',
                         'source宣言・ファイル指紋はローカル証拠の結合であり、実データを合成と偽る操作を防ぐ署名ではない。']}
    write_private(report, result)
    return result
