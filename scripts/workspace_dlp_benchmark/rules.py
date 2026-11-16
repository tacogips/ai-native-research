"""公開Policy API仕様から試験規則を計画し、明示実行時だけ適用する。"""
import copy
import json
import math
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    from .common import digest, now, object_digest, private_path, read_json, timestamp, write_private
except ImportError:
    from common import digest, now, object_digest, private_path, read_json, timestamp, write_private

BASE = 'https://cloudidentity.googleapis.com/v1/'
TRIGGER = 'google.workspace.drive.file.v1.share'
DETECTORS = {'email': 'EMAIL_ADDRESS', 'phone': 'PHONE_NUMBER',
             'passport': 'JAPAN_PASSPORT', 'license': 'JAPAN_DRIVERS_LICENSE_NUMBER',
             'individual': 'JAPAN_INDIVIDUAL_NUMBER', 'bank': 'JAPAN_BANK_ACCOUNT',
             'card': 'CREDIT_CARD_NUMBER'}
THRESHOLDS = ('UNLIKELY', 'POSSIBLE', 'LIKELY')
AUDIT = {'driveAction': {'auditOnly': {}}}
SOURCES = {
    'settings': 'https://docs.cloud.google.com/identity/docs/concepts/supported-policy-api-settings',
    'create': 'https://docs.cloud.google.com/identity/docs/how-to/create-patch-delete-policies',
    'policy': 'https://docs.cloud.google.com/identity/docs/reference/rest/v1/policies',
    'operation': 'https://docs.cloud.google.com/identity/docs/reference/rest/Shared.Types/Operation',
    'limits': 'https://knowledge.workspace.google.com/admin/security/view-dlp-content-and-rule-size-limits',
    'word_list': 'https://knowledge.workspace.google.com/admin/security/custom-content-detectors',
}


class PolicyExecutionError(RuntimeError):
    """詳細は非公開のチェックポイントへ保持する。トークンは含めない。"""


class ApiError(PolicyExecutionError):
    def __init__(self, code, status=None):
        super().__init__('Policy API request failed')
        self.code, self.status = code, status


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, stream, code, message, headers, new_url):
        return None  # 別hostへのBearer転送を含め、APIからのredirectを追わない。


def _resource(value):
    if not isinstance(value, str) or not re.fullmatch(r'policies/[A-Za-z0-9_-]+', value):
        raise ValueError('ポリシー名の形式が不正です')
    return value


def _query(org_unit):
    identifier = org_unit.split('/', 1)[1]
    return {'orgUnit': org_unit,
            'query': "entity.org_units.exists(orgUnit, orgUnit.org_unit_id == orgUnitId('" + identifier + "'))"}


def _scope(config):
    customer, org_unit, namespace = config['customer'], config['org_unit'], config['namespace']
    if not re.fullmatch(r'customers/C[A-Za-z0-9_-]+', customer):
        raise ValueError('customerはcustomers/C...形式が必要です')
    if not re.fullmatch(r'orgUnits/[A-Za-z0-9_-]+', org_unit):
        raise ValueError('org_unitの形式が不正です')
    if not re.fullmatch(r'(?:DLPTEST|DLPBENCH|dlptest|dlpbench)-[A-Za-z0-9][A-Za-z0-9_-]{2,48}', namespace):
        raise ValueError('試験専用namespaceにはDLPTEST-またはDLPBENCH-を使ってください')
    return customer, org_unit, namespace


def _payload(customer, query, setting_type, value):
    return {'customer': customer, 'policyQuery': copy.deepcopy(query),
            'setting': {'type': setting_type, 'value': value}}


def expected_conditions(profile):
    """観測取込側がGETの条件と照合する、役割ごとの確定したCEL式。"""
    roles = profile['roles']
    controls = {}
    for role in ('head', 'tail'):
        item = roles[role]
        detector = item['detector_id']
        # 計画時のlocalrefはAPIへ送らず、適用時に確定名へ解決する。
        if not detector.startswith('localref:'):
            _resource(detector)
        method = {'word_list': 'matches_word_list', 'regular_expression': 'matches_regex_detector'}[item.get('control_kind', 'word_list')]
        counts = '{minimum_match_count: 1, minimum_unique_match_count: 1}' if method == 'matches_word_list' else '{minimum_match_count: 1}'
        controls[role] = f"body.{method}('{detector}', {counts})"
    threshold = profile['threshold']
    if threshold not in THRESHOLDS:
        raise ValueError('未対応の閾値です')
    predicate = f"body.matches_dlp_detector('{DETECTORS[profile['kind']]}', google.privacy.dlp.v2.Likelihood.{threshold}, {{minimum_match_count: 1, minimum_unique_match_count: 1}})"
    both = f"({controls['head']}) && ({controls['tail']})"
    return {**controls, 'positive': f'{both} && ({predicate})', 'negative': f'{both} && !({predicate})'}


def _rule(name, description, condition, action):
    return {'displayName': name, 'description': description, 'state': 'ACTIVE',
            'triggers': [TRIGGER], 'condition': {'contentCondition': condition},
            'action': copy.deepcopy(action),
            'ruleTypeMetadata': {'dlpRuleMetadata': {'alertSeverity': 'LOW'}}}


def _positive_action(config):
    mode = config.get('mode', 'audit')
    if mode not in ('audit', 'native_remediation'):
        raise ValueError('modeはauditまたはnative_remediationです')
    action = config.get('positive_action', {'auditOnly': {}})
    if not isinstance(action, dict) or len(action) != 1:
        raise ValueError('positive_actionはDrive動作1個のオブジェクトです')
    key = next(iter(action))
    if key not in ('auditOnly', 'blockAccess', 'warnUser', 'restrictCopyPrintDownload', 'applyLabels') or not isinstance(action[key], dict):
        raise ValueError('未対応のDrive動作です')
    if mode == 'audit' and action != {'auditOnly': {}}:
        raise ValueError('是正動作はnative_remediationを明示してください')
    return mode, {'driveAction': copy.deepcopy(action)}


def _word_lists(truth):
    words = {}
    for role, prefix in (('head', 'DLPHEAD'), ('tail', 'DLPTAIL')):
        values = [row['scan_control'][role + '_token'] for row in truth]
        if len(set(values)) != len(values):
            raise ValueError('各ファイルの対照語が重複しています')
        if not values or len(values) > 950:
            raise ValueError('対照語数が1〜950語の範囲外です。自動分割しません')
        if any(not re.fullmatch(prefix + r'[A-Z]+', value) or len(value) > 40 for value in values):
            raise ValueError('対照語は英字のみ、1語40字以下が必要です')
        # UTF-8の語を改行で連結したサイズ。JSONの転送サイズとは区別する。
        if len(('\n'.join(values)).encode()) > 60 * 1024:
            raise ValueError('対照語集が60KBを超えます')
        words[role] = values
    return words


def plan_rules(dataset, config_path, output):
    dataset, config_path, output = private_path(dataset), private_path(config_path), private_path(output)
    config = read_json(config_path)
    customer, org_unit, namespace = _scope(config)
    query = _query(org_unit)
    mode, action = _positive_action(config)
    kinds, thresholds = config.get('kinds', list(DETECTORS)), config.get('thresholds', list(THRESHOLDS))
    if not kinds or len(set(kinds)) != len(kinds) or any(k not in DETECTORS for k in kinds):
        raise ValueError('kindsに未知の型または重複があります')
    if not thresholds or len(set(thresholds)) != len(thresholds) or any(t not in THRESHOLDS for t in thresholds):
        raise ValueError('thresholdsに未知の閾値または重複があります')
    token_env = config.get('token_env', 'GOOGLE_WORKSPACE_CLI_TOKEN')
    if not re.fullmatch(r'[A-Z][A-Z0-9_]+', token_env):
        raise ValueError('token_envの形式が不正です')
    truth = read_json(dataset / 'ground_truth.json')
    words = _word_lists(truth)
    if len({r['case_id'] for r in truth}) != len(truth):
        raise ValueError('資料識別子が重複しています')
    generation = read_json(dataset / 'generation.json')
    operations = []
    description = f'workspace_dlp_benchmark managed test; namespace={namespace}'
    scope_key = object_digest({'customer': customer, 'policyQuery': query})
    for role in ('head', 'tail'):
        value = {'displayName': f'{namespace}-{role}-detector', 'description': description,
                 'wordList': {'words': words[role]}}
        operations.append({'key': role + '_detector', 'action': 'create',
                           'payload': _payload(customer, query, 'settings/detector.word_list', value)})
    profiles = []
    controls = {r: {'id': 'localref:' + r + '_rule', 'detector_id': 'localref:' + r + '_detector',
                    'control_kind': 'word_list'} for r in ('head', 'tail')}
    for kind in kinds:
        for threshold in thresholds:
            roles = copy.deepcopy(controls)
            for role in ('positive', 'negative'):
                roles[role] = {'id': f'localref:{kind}_{threshold}_{role}'}
            profile = {'kind': kind, 'threshold': threshold, 'mode': mode,
                       'scope_key': scope_key, 'roles': roles}
            conditions = expected_conditions(profile)
            if not profiles:
                for role in ('head', 'tail'):
                    value = _rule(f'{namespace}-{role}-control', description, conditions[role], AUDIT)
                    operations.append({'key': role + '_rule', 'action': 'create',
                                       'payload': _payload(customer, query, 'settings/rule.dlp', value)})
            for role in ('positive', 'negative'):
                value = _rule(f'{namespace}-{kind}-{threshold}-{role}', description,
                              conditions[role], action if role == 'positive' else AUDIT)
                operations.append({'key': f'{kind}_{threshold}_{role}', 'action': 'create',
                                   'payload': _payload(customer, query, 'settings/rule.dlp', value)})
            profiles.append(profile)
    # 更新・削除は自動生成しない。必要時にこの計画へ明示し、保存許可表も指定する。
    plan = {'schema_version': 1, 'created_at': now(), 'customer': customer,
            'org_unit': org_unit, 'namespace': namespace, 'scope_key': scope_key,
            'token_env': token_env, 'mode': mode, 'operations': operations, 'profiles': profiles,
            'input_paths': {'ground_truth': str(dataset / 'ground_truth.json'),
                            'generation': str(dataset / 'generation.json'), 'config': str(config_path)},
            'input_sha256': {'ground_truth': digest(dataset / 'ground_truth.json'),
                             'generation': digest(dataset / 'generation.json'), 'config': digest(config_path)},
            'control_patterns': generation['control_patterns'], 'control_kind': 'word_list',
            'source_urls': SOURCES,
            'limits': ['APIの実作成・読み戻しは未検証。モック成功は製品での成功ではない。',
                       'この作成計画は既存規則の更新・削除を拒否する。変更用許可表を黙って推定しない。',
                       '是正動作の内部オブジェクトは明示した外部設定。未公開の内部構造を推定しない。',
                       'Cloud Identityの公開discoveryにはOperation取得専用resourceがない。既定HTTP対応でserver nameをGETし、未対応・失敗は保留停止する。',
                       '同namespaceを別の実行台帳で重ねて適用しない。未知結果後も新しい台帳でPOSTをやり直さない。',
                       '先頭末尾と肯定/否定は条件付き観測。内部走査完了の直接証明ではない。']}
    plan['plan_sha256'] = object_digest(plan)
    write_private(output, plan)
    return plan


def _validate_plan(plan):
    """実行前に全操作を調べ、途中まで作ってから未知操作に気付くのを避ける。"""
    _scope(plan)
    if plan.get('schema_version') != 1 or plan.get('control_kind') != 'word_list':
        raise ValueError('未対応の計画形式です')
    if plan.get('mode') not in ('audit', 'native_remediation'):
        raise ValueError('未対応の試験モードです')
    for key, path in plan['input_paths'].items():
        if digest(private_path(path)) != plan['input_sha256'][key]:
            raise ValueError('計画後に入力が変更されました')
    operations = plan['operations']
    keys = [step['key'] for step in operations]
    if len(set(keys)) != len(keys) or any(not re.fullmatch(r'[A-Za-z0-9_]+', key) for key in keys):
        raise ValueError('操作keyの重複または形式誤り')
    mapping = {step['key']: step for step in operations}
    profiles = plan['profiles']
    if not profiles or len({(p['kind'], p['threshold']) for p in profiles}) != len(profiles):
        raise ValueError('規則列の重複または欠落')
    expected_keys = {'head_detector', 'tail_detector', 'head_rule', 'tail_rule'}
    for step in operations:
        if step['action'] != 'create':
            raise ValueError('既存ポリシーの変更・削除はこの作成計画では実行しません')
        _guard_payload(step['payload'], plan)
    for profile in profiles:
        conditions = expected_conditions(profile)
        if profile.get('mode') != plan['mode'] or profile.get('scope_key') != plan['scope_key']:
            raise ValueError('規則列のモードまたは範囲が不一致です')
        if set(profile['roles']) != {'head', 'tail', 'positive', 'negative'}:
            raise ValueError('規則の役割が不正です')
        for role in ('head', 'tail'):
            item = profile['roles'][role]
            if item != {'id': f'localref:{role}_rule', 'detector_id': f'localref:{role}_detector', 'control_kind': 'word_list'}:
                raise ValueError('対照規則の参照が不正です')
        for role in ('positive', 'negative', 'head', 'tail'):
            key = (f'{profile["kind"]}_{profile["threshold"]}_{role}'
                   if role in ('positive', 'negative') else role + '_rule')
            expected_keys.add(key)
            if profile['roles'][role]['id'] != 'localref:' + key:
                raise ValueError('規則の識別子が不一致です')
            payload = mapping[key]['payload']
            value = payload['setting']['value']
            if payload['setting']['type'] != 'settings/rule.dlp' or value['condition'] != {'contentCondition': conditions[role]}:
                raise ValueError('規則の条件が意図した肯定/否定/対照と異なります')
            if value.get('state') != 'ACTIVE' or value.get('triggers') != [TRIGGER]:
                raise ValueError('試験規則の状態または契機が不正です')
            if role != 'positive' or plan['mode'] == 'audit':
                if value.get('action') != AUDIT:
                    raise ValueError('対照/否定/検知専用は監査のみです')
            else:
                if set(value['action']) != {'driveAction'}:
                    raise ValueError('Drive以外の動作は使用しません')
                _positive_action({'mode': plan['mode'], 'positive_action': value['action']['driveAction']})
    if set(keys) != expected_keys:
        raise ValueError('計画に余分な操作または不足があります')
    head = mapping['head_detector']['payload']['setting']
    tail = mapping['tail_detector']['payload']['setting']
    for setting in (head, tail):
        if setting['type'] != 'settings/detector.word_list' or set(setting['value']) != {'displayName', 'description', 'wordList'} or set(setting['value']['wordList']) != {'words'}:
            raise ValueError('対照検知器の形式が不正です')
    heads, tails = head['value']['wordList']['words'], tail['value']['wordList']['words']
    if len(heads) != len(tails):
        raise ValueError('先頭末尾の対照語数が違います')
    _word_lists([{'scan_control': {'head_token': h, 'tail_token': t}} for h, t in zip(heads, tails)])


def _resolve(value, resources):
    if isinstance(value, str):
        def replace(match):
            key = match.group(1)
            if key not in resources:
                raise ValueError('未解決のlocalref: ' + key)
            return resources[key]['policy']['name']
        return re.sub(r'localref:([A-Za-z0-9_]+)', replace, value)
    if isinstance(value, dict):
        return {key: _resolve(item, resources) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, resources) for item in value]
    return value


def _guard_payload(payload, plan):
    if set(payload) != {'customer', 'policyQuery', 'setting'}:
        raise ValueError('予期しない要求フィールド')
    if payload['customer'] != plan['customer'] or payload['policyQuery'] != _query(plan['org_unit']):
        raise ValueError('試験範囲が異なります')
    setting = payload['setting']
    if set(setting) != {'type', 'value'} or setting['type'] not in ('settings/rule.dlp', 'settings/detector.word_list'):
        raise ValueError('未対応の設定です')
    value = setting['value']
    if not value.get('displayName', '').startswith(plan['namespace'] + '-'):
        raise ValueError('試験namespaceの外です')
    if value.get('description') != f"workspace_dlp_benchmark managed test; namespace={plan['namespace']}":
        raise ValueError('試験所有タグが異なります')


def _compare_policy(actual, expected):
    """公開のoutput-onlyだけ除外し、未指定の未知既定値を許容しない。"""
    candidate = copy.deepcopy(actual)
    name = _resource(candidate.pop('name', None))
    if candidate.pop('type', None) != 'ADMIN':
        raise ValueError('管理者ポリシーではありません')
    query = candidate.get('policyQuery', {})
    if 'sortOrder' in query:
        sort_order = query.pop('sortOrder')
        if isinstance(sort_order, bool) or not isinstance(sort_order, (int, float)) or not math.isfinite(sort_order):
            raise ValueError('不正なsortOrder')
    if query.get('group') == '' and 'group' not in expected['policyQuery']:
        query.pop('group')  # 公開仕様で空が既定と定義されたhelper。
    value = candidate.get('setting', {}).get('value', {})
    created, updated = value.pop('createTime', None), value.pop('updateTime', None)
    if not created or not updated or timestamp(updated) < timestamp(created):
        raise ValueError('作成・更新時刻の根拠がありません')
    if object_digest(candidate) != object_digest(expected):
        raise ValueError('読み戻した設定に差分があります')
    return name


class Client:
    def __init__(self, token):
        self.token = token
        self.last_end = 0.0

    def request(self, method, path, body=None):
        # 同サービスの相対パスに限定。Operation応答を外部URLへ追従しない。
        if not re.fullmatch(r'(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+', path) or '..' in path:
            raise ValueError('APIパスが不正です')
        time.sleep(max(0, 1.1 - (time.monotonic() - self.last_end)))
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(BASE + path, data=data, method=method,
                                        headers={'Authorization': 'Bearer ' + self.token,
                                                 'Content-Type': 'application/json'})
        try:
            with urllib.request.build_opener(_NoRedirect()).open(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            status = None
            try:
                status = json.loads(error.read()).get('error', {}).get('status')
            except (ValueError, AttributeError):
                pass
            raise ApiError(error.code, status) from None
        finally:
            self.last_end = time.monotonic()


def _poll(client, operation, checkpoint, save, timeout=120):
    deadline = time.monotonic() + timeout
    while True:
        checkpoint['operation'] = operation
        checkpoint['status'] = 'operation_pending'
        save()
        if operation.get('done') is True:
            if 'error' in operation:
                checkpoint['status'] = 'operation_failed'
                save()
                raise PolicyExecutionError('Operationがエラーを返しました')
            if not isinstance(operation.get('response'), dict):
                raise PolicyExecutionError('Operation完了にresponseがありません')
            return operation['response']
        if operation.get('done') is not False and operation.get('done') is not None:
            raise ValueError('Operation.doneの型が不正です')
        name = operation.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'(?:[A-Za-z0-9_-]+/)*operations/[A-Za-z0-9_-]+', name):
            raise ValueError('Operationの同サービス名を確認できません')
        if time.monotonic() >= deadline:
            checkpoint['status'] = 'operation_timeout'
            save()
            raise TimeoutError('Operationは未完了です。再作成しません')
        time.sleep(0.1)
        operation = client.request('GET', name)


def _usec(value):
    from datetime import datetime, timezone
    delta = timestamp(value) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return str((delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds)


def _bindings(plan, state):
    profiles = _resolve(plan['profiles'], state['resources'])
    by_id = {entry['policy']['name']: entry['policy'] for entry in state['resources'].values()}
    for profile in profiles:
        for role in profile['roles'].values():
            policy = by_id[role['id']]
            role.update(policy_sha256=object_digest(policy),
                        update_time_usec=_usec(policy['setting']['value']['updateTime']),
                        event_aliases=[])  # 別名は実ログで確認するまで仮定しない。
            if 'detector_id' in role:
                role['detector_sha256'] = object_digest(by_id[role['detector_id']])
    return profiles


def apply_rules(plan_path, output, execute=False):
    """同じ台帳への同時実行を排他し、未確定POSTの上書きを防ぐ。"""
    import fcntl
    output = private_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lock_path = output.with_name(output.name + '.lock')
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _apply_rules(plan_path, output, execute)
    finally:
        os.close(descriptor)


def _apply_rules(plan_path, output, execute=False):
    plan_path, output = private_path(plan_path), private_path(output)
    plan = read_json(plan_path)
    expected_hash = plan.pop('plan_sha256')
    if object_digest(plan) != expected_hash:
        raise ValueError('計画の指紋が一致しません')
    _validate_plan(plan)
    if not execute:
        preview = {'schema_version': 1, 'status': 'dry_run', 'plan_sha256': expected_hash,
                   'network_calls': 0, 'operations': plan['operations'], 'profiles': plan['profiles']}
        write_private(output, preview)
        return preview
    # dry-run出力を実行台帳と共用しない。既存の未確定POSTも上書きしない。
    if output.exists():
        state = read_json(output)
        if state.get('plan_sha256') != expected_hash or state.get('status') == 'dry_run':
            raise ValueError('出力の種類または計画が違います。別の実行台帳を使ってください')
    else:
        state = {'schema_version': 1, 'status': 'started', 'plan_sha256': expected_hash,
                 'started_at': now(), 'customer': plan['customer'],
                 'customer_id': plan['customer'].split('/', 1)[1], 'org_unit': plan['org_unit'],
                 'namespace': plan['namespace'], 'scope_key': plan['scope_key'], 'mode': plan['mode'],
                 'resources': {}, 'steps': {}, 'network_calls': 0}
    if state['status'] == 'complete':
        return state
    token = os.environ.get(plan['token_env'])
    if not token:
        raise ValueError('指定の環境変数にアクセストークンがありません')
    client = Client(token)
    original = client.request
    def request(method, path, body=None):
        state['network_calls'] += 1
        save()
        return original(method, path, body)
    client.request = request
    def save():
        write_private(output, state)
    save()
    try:
        for step in plan['operations']:
            key = step['key']
            saved = state['steps'].setdefault(key, {'status': 'not_started'})
            if saved['status'] == 'verified':
                continue
            if saved['status'] in ('posting', 'uncertain_mutation', 'operation_failed'):
                raise PolicyExecutionError('未確定または失敗済みの変更です。手動確認が必要です')
            if step['action'] != 'create':
                raise ValueError('この作成計画は既存ポリシーの変更・削除を実行しません')
            payload = _resolve(step['payload'], state['resources'])
            _guard_payload(payload, plan)
            saved['expected'] = payload
            if 'operation' not in saved:
                saved['status'] = 'posting'
                save()  # POST直前の永続記録。戻り値が不明なら再POST禁止。
                try:
                    saved['operation'] = client.request('POST', 'policies', payload)
                except Exception:
                    saved['status'] = 'uncertain_mutation'
                    save()
                    raise
            response = _poll(client, saved['operation'], saved, save)
            name = _resource(response.get('name'))
            saved['status'] = 'reading_back'
            save()
            policy = client.request('GET', name)
            saved['readback'] = policy
            saved['readback_sha256'] = object_digest(policy)
            save()
            try:
                if policy.get('name') != name:
                    raise ValueError('GETの返却名が要求と異なります')
                _compare_policy(policy, payload)
            except ValueError:
                saved['status'] = 'readback_failed'
                saved['readback_difference'] = 'expectedとreadbackの全文・型・値を比較してください。未知の追加既定値は自動承認しません。'
                save()
                raise
            state['resources'][key] = {'policy': policy, 'policy_sha256': object_digest(policy)}
            saved.update(status='verified', resource_name=name, policy_sha256=object_digest(policy))
            save()
        state.update(status='complete', completed_at=now(), profiles=_bindings(plan, state),
                     policies=[r['policy'] for r in state['resources'].values()])
        save()
        return state
    except Exception as error:
        state.update(status='stopped', stopped_at=now(), error_type=type(error).__name__,
                     message='完了とは扱いません。保存したOperationと読み戻しを確認し、未確定変更を再送しないでください。')
        save()
        raise PolicyExecutionError(state['message']) from None
