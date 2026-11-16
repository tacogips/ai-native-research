"""是正採点の独立回帰試験。合成原票だけを一時領域へ保存し、通信しない。"""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from common import digest
from remediation import (contains_fragment, evaluate_case, exposure,
                         plan_remediation, score_remediation)


class RemediationEvidenceTests(unittest.TestCase):
    FILE = 'SYNTHETIC-FILE-A'
    RULE = 'policies/SYNTHETIC-RULE-A'
    CUSTOMER = 'CEXAMPLE'
    EMAIL = 'reader@example.net'
    DOMAINS = ['example.test']
    ROUTE = 'sheets.spreadsheets.get'
    UPDATE_USEC = '1794787200000000'  # 2026-11-16T00:00:00Z

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dlp-remediation-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = 0
        self.case = {
            'case_id': 'block_sharing/external_user/owner/edit',
            'action': 'block_sharing', 'prior_sharing': 'external_user',
            'operator_role': 'owner', 'trigger_kind': 'edit',
            'should_protect': True, 'expected_outcome': 'denied',
            'mechanism': 'native_dlp',
        }
        self.policy = {
            'name': self.RULE, 'customer': 'customers/' + self.CUSTOMER,
            'type': 'ADMIN',
            'policyQuery': {'orgUnit': 'orgUnits/TESTOU'},
            'setting': {'type': 'settings/rule.dlp', 'value': {
                'displayName': 'DLPTEST-synthetic-remediation', 'state': 'ACTIVE',
                'createTime': '2026-11-15T00:00:00Z',
                'updateTime': '2026-11-16T00:00:00Z',
                'triggers': ['google.workspace.drive.file.v1.share'],
                'condition': {'contentCondition': "body.contains('SYNTHETIC')"},
                'action': {'driveAction': {'blockAccess': {}}},
            }},
        }
        self.raw = self.raw_activity()
        self.baseline = self.probe('readable', '00:00:05', '00:00:06', version='1')
        self.after = self.probe('denied', '00:02:00', '00:02:01')
        self.policies = {'file_id': self.FILE, 'rule_id': self.RULE,
                         'before_at': '2026-11-16T00:00:00Z',
                         'after_at': '2026-11-16T00:05:00Z',
                         'before': copy.deepcopy(self.policy),
                         'after': copy.deepcopy(self.policy)}
        self.obs = {
            'case_id': self.case['case_id'], 'mechanism': 'native_dlp',
            'file_id': self.FILE, 'rule_id': self.RULE, 'customer_id': self.CUSTOMER,
            'rule_update_time_usec': self.UPDATE_USEC,
            'trigger_at': '2026-11-16T00:01:00Z',
            'observation_end': '2026-11-16T00:04:00Z',
            'external_email': self.EMAIL, 'probe_route': self.ROUTE,
            'baseline_file_id': self.FILE,
            'scope_evidence': self.ref({'bindings': [{
                'file_id': self.FILE, 'rule_id': self.RULE, 'applies': True}]}),
            'baseline_control': self.ref({'probes': [self.baseline]}),
            'probe_report': self.ref({'probes': [self.after]}),
            'policy_readbacks': self.ref(self.policies),
            'audit': self.ref(self.raw),
            'expected_action_fragment': {'parameter': [
                {'name': 'action', 'value': 'blockAccess'}]},
        }
        self.case['expected_action_fragment'] = copy.deepcopy(self.obs['expected_action_fragment'])
        self.bind_context(self.case, self.obs)

    def ref(self, value):
        self.serial += 1
        path = self.root / ('evidence-%03d.json' % self.serial)
        path.write_text(json.dumps(value), encoding='utf-8')
        return {'path': str(path), 'sha256': digest(path)}

    def probe(self, outcome, start, finish, file_id=None, version='2', route=None):
        file_id = file_id or self.FILE
        owner = {'id': file_id, 'version': version, 'trashed': False,
                 'mimeType': 'application/vnd.google-apps.spreadsheet',
                 'modifiedTime': ('2026-11-16T00:00:01Z' if version == '1'
                                  else '2026-11-16T00:01:00Z'),
                 'owners': [{'emailAddress': 'owner@example.test'}]}
        permissions = {'complete': True, 'permissions': [
            {'id': 'owner-id', 'type': 'user', 'role': 'owner',
             'emailAddress': 'owner@example.test'},
            {'id': 'reader-id', 'type': 'user', 'role': 'reader',
             'emailAddress': self.EMAIL}]}
        started_at, finished_at = ('2026-11-16T' + start + 'Z', '2026-11-16T' + finish + 'Z')
        before_permissions = dict(copy.deepcopy(permissions), started_at=started_at, finished_at=started_at)
        after_permissions = dict(copy.deepcopy(permissions), started_at=finished_at, finished_at=finished_at)
        return {'schema_version': 1, 'test_kind': 'external_access_probe', 'file_id': file_id,
                'actor_role': 'external_reader',
                'actor_email': self.EMAIL, 'mechanism': route or self.ROUTE,
                'started_at': started_at, 'finished_at': finished_at,
                'snapshot_started_at': started_at, 'snapshot_finished_at': finished_at,
                'access_started_at': started_at, 'access_finished_at': finished_at,
                'owner_before_observed_at': started_at, 'owner_after_observed_at': finished_at,
                'atomic_snapshot': False,
                'owner_before': copy.deepcopy(owner), 'owner_after': copy.deepcopy(owner),
                'permissions_before': before_permissions, 'permissions_after': after_permissions,
                'same_revision_during_probe': True,
                'permission_mutation_by_probe': False, 'outcome': outcome,
                'http_status': 403 if outcome == 'denied' else 200,
                'denial_reason': 'insufficientFilePermissions' if outcome == 'denied' else None}

    def raw_activity(self):
        parameters = [
            {'name': 'resource_id', 'value': self.FILE},
            {'name': 'rule_resource_name', 'value': self.RULE},
            {'name': 'data_source', 'value': 'DRIVE'},
            {'name': 'rule_type', 'value': 'DLP'},
            {'name': 'rule_update_time_usec', 'intValue': self.UPDATE_USEC},
            {'name': 'triggered_actions', 'messageValue': {
                'parameter': [{'name': 'action', 'value': 'blockAccess'}]}},
        ]
        return {'items': [{'id': {'time': '2026-11-16T00:02:00Z',
                'uniqueQualifier': 'synthetic-action-1', 'applicationName': 'rules',
                'customerId': self.CUSTOMER},
                'events': [{'name': 'action_complete', 'parameters': parameters}]}]}

    def bind_context(self, case, obs, *, actor_email=None):
        """事前ACLと別保存の操作記録へ、計画の3因子を結ぶ。"""
        candidates = []
        for key in ('baseline_control', 'probe_report'):
            report = json.loads(Path(obs[key]['path']).read_text())
            candidates.extend(p for p in report.get('probes', [])
                              if p['file_id'] == obs['file_id']
                              and p['finished_at'] < obs['trigger_at'])
        if actor_email is None:
            actor_email = {'owner': 'owner@example.test', 'editor': 'editor@example.test',
                           'external_reader': self.EMAIL}.get(case.get('operator_role'), 'owner@example.test')
        record = {'schema_version': 1, 'source': 'synthetic_fixture',
                  'case_id': case['case_id'], 'file_id': obs['file_id'],
                  'rule_id': obs['rule_id'], 'kind': case['trigger_kind'],
                  'at': obs['trigger_at'], 'actor_email': actor_email}
        context = {'schema_version': 1, 'case_id': case['case_id'],
                   'file_id': obs['file_id'], 'trigger_at': obs['trigger_at'],
                   'baseline_probe': self.ref({'probes': candidates}),
                   'trigger_record': self.ref(record)}
        for key in ('prior_sharing', 'operator_role', 'trigger_kind'):
            if key in case:
                context[key] = case[key]
        obs['case_context'] = self.ref(context)
        return obs

    def action_evidence(self, action, drive_action):
        """対象動作と原票・規則を合わせる。動作の内部表現は合成の対応表。"""
        fragment = {'parameter': [{'name': 'action', 'value': action}]}
        raw = copy.deepcopy(self.raw)
        raw['items'][0]['events'][0]['parameters'][-1]['messageValue'] = fragment
        policies = copy.deepcopy(self.policies)
        for key in ('before', 'after'):
            policies[key]['setting']['value']['action']['driveAction'] = drive_action
        self.case['expected_action_fragment'] = copy.deepcopy(fragment)
        self.obs.update(expected_action_fragment=fragment, audit=self.ref(raw),
                        policy_readbacks=self.ref(policies))

    def release_fixture(self, kind):
        """過去の遮断動作、事前拒否、解除後可読を分離した合成証拠。"""
        case = dict(self.case, case_id='release/' + kind, action='release',
                    trigger_kind=kind, expected_outcome='readable',
                    expected_action_fragment=self.obs['expected_action_fragment'])
        raw = copy.deepcopy(self.raw)
        raw['items'][0]['id']['time'] = '2026-11-16T00:00:40Z'
        prior = self.probe('denied', '00:00:50', '00:00:51', version='1')
        after = self.probe('readable', '00:02:00', '00:02:01')
        control = self.probe('readable', '00:00:05', '00:00:06', file_id='CONTROL-A')
        policies = copy.deepcopy(self.policies)
        change = {'file_id': self.FILE, 'rule_id': self.RULE,
                  'kind': kind, 'changed_at': self.obs['trigger_at']}
        if kind == 'rule_disabled':
            policies['after']['setting']['value'].update(
                state='INACTIVE', updateTime='2026-11-16T00:01:00Z')
        elif kind == 'rule_deleted':
            policies['after'] = None
            change['complete_policy_list'] = self.ref({
                'customer': 'customers/' + self.CUSTOMER, 'complete': True,
                'observed_at': '2026-11-16T00:01:05Z', 'policies': []})
        elif kind == 'content_removed':
            case['removed_values'] = ['SYNTHETIC-PII-A', 'SYNTHETIC-PII-B']
            change['before_text'] = self.ref({'file_id': self.FILE, 'revision': '1',
                                           'text': 'SYNTHETIC-PII-A SYNTHETIC-PII-B'})
            change['after_text'] = self.ref({'file_id': self.FILE, 'revision': '2',
                                          'text': '検証用本文を削除済み'})
        obs = dict(self.obs, case_id=case['case_id'], baseline_file_id='CONTROL-A',
                   baseline_control=self.ref({'probes': [control]}),
                   probe_report=self.ref({'probes': [prior, after]}),
                   policy_readbacks=self.ref(policies), audit=self.ref(raw),
                   change_evidence=self.ref(change))
        self.bind_context(case, obs)
        return case, obs, policies, change

    def confirmed_negative_fixture(self):
        """原票から再導出可能な検知陰性と、是正の可読観測を結ぶ。"""
        from test_support import AuditFixture, UPDATED, UPDATE_USEC
        from rules import expected_conditions
        audit = AuditFixture(self.root / 'negative-audit', kinds=('email',), thresholds=('POSSIBLE',))
        audit.negative(case='negative')
        def shift(value):
            if isinstance(value, str):
                return value.replace('2026-01-01', '2026-11-16')
            if isinstance(value, list):
                return [shift(item) for item in value]
            if isinstance(value, dict):
                return {key: shift(item) for key, item in value.items()}
            return value
        for name in ('files', 'pages', 'manifest', 'policy_before', 'policy_after'):
            setattr(audit, name, shift(getattr(audit, name)))
        audit.imported()
        target = next(f for f in audit.files if f['case_id'] == 'negative')
        self.FILE = target['file_id']
        policy = copy.deepcopy(self.policy)
        policy.update(customer='customers/CSYNTHETIC', policyQuery=copy.deepcopy(audit.query))
        policy['setting']['value'].update(updateTime=UPDATED,
            condition={'contentCondition': expected_conditions(audit.profiles[0])['positive']})
        policies = dict(self.policies, file_id=self.FILE, before=policy, after=copy.deepcopy(policy))
        baseline = self.probe('readable', '00:00:05', '00:00:06', version='prior-version')
        after = self.probe('readable', '00:02:00', '00:02:01', version=target['revision'])
        obs = dict(self.obs, file_id=self.FILE, customer_id='CSYNTHETIC',
                   rule_update_time_usec=UPDATE_USEC, baseline_file_id=self.FILE,
                   trigger_at='2026-11-16T00:00:30Z', observation_end='2026-11-16T00:10:00Z',
                   scope_evidence=self.ref({'bindings': [{'file_id': self.FILE,
                                          'rule_id': self.RULE, 'applies': True}]}),
                   baseline_control=self.ref({'probes': [baseline]}),
                   probe_report=self.ref({'probes': [after]}),
                   policy_readbacks=self.ref(dict(policies, after_at='2026-11-16T00:11:00Z')),
                   audit=self.ref({'items': []}),
                   evaluation_confirmation={'path': str(audit.bundle_path), 'sha256': digest(audit.bundle_path)})
        case = dict(self.case, case_id='overblocking/block_sharing',
                    should_protect=False, expected_outcome='readable')
        self.bind_context(case, obs)
        return case, obs, policies, after

    def evaluate(self, case=None, obs=None):
        return evaluate_case(case or self.case, obs or self.obs, self.DOMAINS)

    def assertNotSuccess(self, case=None, obs=None):
        # 不整合を明示拒否する実装と保留する実装をともに許容する。
        try:
            result = self.evaluate(case, obs)
        except (ValueError, KeyError, TypeError):
            return
        self.assertNotEqual(result['status'], 'succeeded', result)

    def test_plan_contains_180_core_and_16_supplemental_cases(self):
        plan = plan_remediation(self.root / 'plan.json')
        self.assertEqual(len(plan['cases']), 196)
        self.assertEqual(len({c['case_id'] for c in plan['cases']}), 196)
        self.assertEqual(sum(c.get('execution') == 'requires_environment'
                             and not c['case_id'].startswith('overblocking/')
                             for c in plan['cases']), 180)
        self.assertEqual(sum(c['case_id'].startswith('overblocking/') for c in plan['cases']), 4)
        self.assertTrue(all(c.get('expected_outcome') is None for c in plan['cases']
                            if c['case_id'].startswith(('bypass/', 'conflict/'))))

    def test_plan_cannot_change_fixed_expected_outcome_but_can_resolve_unknown(self):
        invalid = self.ref({'bindings': {self.case['case_id']: {'expected_outcome': 'readable'}}})
        with self.assertRaises(ValueError):
            plan_remediation(self.root / 'invalid-plan.json', invalid['path'])
        same = self.ref({'bindings': {self.case['case_id']: {'expected_outcome': 'denied'}}})
        plan = plan_remediation(self.root / 'same-plan.json', same['path'])
        self.assertEqual(next(c for c in plan['cases'] if c['case_id'] == self.case['case_id'])['expected_outcome'], 'denied')
        resolved = self.ref({'bindings': {'bypass/copy': {'expected_outcome': 'denied'}}})
        plan = plan_remediation(self.root / 'resolved-plan.json', resolved['path'])
        self.assertEqual(next(c for c in plan['cases'] if c['case_id'] == 'bypass/copy')['expected_outcome'], 'denied')

    def test_nested_reports_message_and_label_arrays_match(self):
        self.assertTrue(contains_fragment({'parameter': [{'name': 'a', 'value': 'x'}]},
                                          {'parameter': [{'name': 'a', 'value': 'x'}]}))
        self.assertTrue(contains_fragment({'fields': {'f': {'selection': ['v1', 'v2']}}},
                                          {'fields': {'f': {'selection': ['v1']}}}))
        self.assertFalse(contains_fragment({'fields': {'f': {'selection': ['v1']}}},
                                           {'fields': {'f': {'selection': ['v2']}}}))

    def test_complete_native_transition_succeeds_and_retains_potential_acl_count(self):
        result = self.evaluate()
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertEqual(result['residual_external_permissions'], 1)
        self.assertTrue(result['triggered_action_event_ids'])

    def test_owner_manual_never_becomes_native_success(self):
        self.obs['mechanism'] = 'owner_manual'
        self.assertEqual(self.evaluate()['status'], 'owner_manual_only')

    def test_custom_acl_without_executor_evidence_cannot_claim_remediation(self):
        # 別規則の遮断や既存ACL拒否を、自作の権限取消の成功にしない。
        self.assertNotSuccess(obs=dict(self.obs, mechanism='custom_acl'))

    def test_api_error_unverified_or_unknown_404_cannot_prove_blocking(self):
        for outcome, status, reason in [('error', 500, 'backendError'),
                                        ('unverified', 404, 'notFound'),
                                        ('denied', 404, 'unknown')]:
            with self.subTest(outcome=outcome, status=status):
                probe = copy.deepcopy(self.after)
                probe.update(outcome=outcome, http_status=status, denial_reason=reason)
                obs = dict(self.obs, probe_report=self.ref({'probes': [probe]}))
                self.assertNotSuccess(obs=obs)

    def test_baseline_requires_target_readable_not_only_unrelated_control(self):
        control = self.probe('readable', '00:00:05', '00:00:06', file_id='UNRELATED-CONTROL')
        self.obs.update(baseline_file_id='UNRELATED-CONTROL',
                        baseline_control=self.ref({'probes': [control]}))
        self.assertNotSuccess()

    def test_missing_baseline_or_incomplete_acl_or_revision_change_is_pending(self):
        variants = []
        denied_baseline = copy.deepcopy(self.baseline)
        denied_baseline['outcome'] = 'denied'
        variants.append(dict(self.obs, baseline_control=self.ref({'probes': [denied_baseline]})))
        for key in ('permissions_before', 'permissions_after'):
            probe = copy.deepcopy(self.after)
            probe[key]['complete'] = False
            variants.append(dict(self.obs, probe_report=self.ref({'probes': [probe]})))
        probe = copy.deepcopy(self.after)
        probe['owner_after']['version'] = '3'
        variants.append(dict(self.obs, probe_report=self.ref({'probes': [probe]})))
        for obs in variants:
            with self.subTest(obs=obs):
                self.assertNotSuccess(obs=obs)

    def test_customer_file_rule_type_and_version_mixing_cannot_supply_action(self):
        for field, value in [('resource_id', 'OTHER-FILE'),
                              ('rule_resource_name', 'policies/OTHER-RULE'),
                              ('rule_type', 'OTHER'), ('rule_update_time_usec', '1')]:
            with self.subTest(field=field):
                raw = copy.deepcopy(self.raw)
                param = next(p for p in raw['items'][0]['events'][0]['parameters'] if p['name'] == field)
                param['intValue' if field == 'rule_update_time_usec' else 'value'] = value
                self.assertNotSuccess(obs=dict(self.obs, audit=self.ref(raw)))
        raw = copy.deepcopy(self.raw)
        raw['items'][0]['id']['customerId'] = 'OTHER-CUSTOMER'
        self.assertNotSuccess(obs=dict(self.obs, audit=self.ref(raw)))

    def test_action_without_rule_version_uses_explicit_conditional_readback_binding(self):
        raw = copy.deepcopy(self.raw)
        event = raw['items'][0]['events'][0]
        event['parameters'] = [p for p in event['parameters']
                               if p['name'] != 'rule_update_time_usec']
        result = self.evaluate(obs=dict(self.obs, audit=self.ref(raw)))
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertEqual(result.get('version_binding'), 'policy_readback_bracket', result)

    def test_suppressed_action_or_rule_trigger_is_not_executed_action(self):
        for variant in ('suppressed', 'rule_trigger'):
            raw = copy.deepcopy(self.raw)
            event = raw['items'][0]['events'][0]
            if variant == 'suppressed':
                event['parameters'][-1]['name'] = 'suppressed_actions'
            else:
                event['name'] = 'rule_trigger'
            self.assertNotSuccess(obs=dict(self.obs, audit=self.ref(raw)))

    def test_empty_or_wrong_policy_and_scope_binding_cannot_supply_identity(self):
        for policy in ({}, dict(self.policy, name='policies/OTHER'),
                       dict(self.policy, customer='customers/OTHER')):
            value = dict(self.policies, before=policy, after=copy.deepcopy(policy))
            self.assertNotSuccess(obs=dict(self.obs, policy_readbacks=self.ref(value)))
        self.assertNotSuccess(obs=dict(self.obs, scope_evidence=self.ref({'bindings': [{
            'file_id': 'OTHER', 'rule_id': self.RULE, 'applies': True}]})))

    def test_referenced_evidence_hash_and_complete_audit_pages_are_required(self):
        for key in ('audit', 'scope_evidence', 'policy_readbacks', 'probe_report', 'baseline_control'):
            with self.subTest(key=key):
                obs = copy.deepcopy(self.obs)
                obs[key]['sha256'] = '0' * 64
                self.assertNotSuccess(obs=obs)
        for raw in ({'items': [], 'nextPageToken': 'still-more'},
                    {'pages': [{'items': [], 'nextPageToken': 'repeat'},
                               {'items': [], 'nextPageToken': 'repeat'}, {'items': []}]}):
            self.assertNotSuccess(obs=dict(self.obs, audit=self.ref(raw)))

    def test_irm_cannot_be_proven_by_sheets_read_denial(self):
        case = dict(self.case, action='restrict_copy_print_download', expected_outcome='operation_denied')
        self.assertNotSuccess(case=case)

    def test_irm_operation_specific_external_probe_can_be_evaluated(self):
        case = dict(self.case, action='restrict_copy_print_download',
                    expected_outcome='operation_denied')
        self.action_evidence('restrictCopyPrintDownload',
                             {'restrictCopyPrintDownload': {'scope': 'VIEWERS_AND_COMMENTERS'}})
        case.update(operator_role='external_reader',
                    expected_action_fragment=self.case['expected_action_fragment'])
        baseline = dict(copy.deepcopy(self.baseline), mechanism='download')
        after = dict(copy.deepcopy(self.after), mechanism='download')
        obs = dict(self.obs, probe_route='download',
                   baseline_control=self.ref({'probes': [baseline]}),
                   probe_report=self.ref({'probes': [after]}))
        self.bind_context(case, obs)
        result = self.evaluate(case, obs)
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertNotSuccess(dict(case, operator_role='owner'), obs)

    def test_warning_decision_is_retained_and_requires_matching_operator(self):
        case = dict(self.case, action='warn_external', expected_outcome='warning')
        self.action_evidence('warnUser', {'warnUser': {}})
        case['expected_action_fragment'] = self.case['expected_action_fragment']
        for decision in ('cancel', 'override'):
            state = {'file_id': self.FILE, 'rule_id': self.RULE,
                     'observed_at': '2026-11-16T00:02:02Z', 'warning_shown': True,
                     'decision': decision, 'actor_role': 'owner'}
            probe = copy.deepcopy(self.after)
            probe['outcome'] = 'denied' if decision == 'cancel' else 'readable'
            probe['http_status'] = 403 if decision == 'cancel' else 200
            obs = dict(self.obs, state_readback=self.ref(state),
                       probe_report=self.ref({'probes': [probe]}))
            result = self.evaluate(case, obs)
            self.assertEqual(result.get('warning_decision'), decision, result)
            self.assertEqual(result['status'], 'succeeded', result)
            state['actor_role'] = 'editor'
            self.assertNotSuccess(case, dict(self.obs, state_readback=self.ref(state)))

    def test_standard_label_selection_metadata_and_action_record_are_required(self):
        case = dict(self.case, action='apply_label', expected_outcome='label_present')
        self.action_evidence('applyLabels', {'applyLabels': {}})
        case['expected_action_fragment'] = self.case['expected_action_fragment']
        label = {'id': 'LABEL-A', 'fields': {'FIELD-A': {'selection': ['OPTION-A']}}}
        case['expected_label'] = label
        state = {'file_id': self.FILE, 'rule_id': self.RULE,
                 'observed_at': '2026-11-16T00:02:02Z', 'labels': [label]}
        obs = dict(self.obs, expected_label=label, state_readback=self.ref(state))
        self.assertEqual(self.evaluate(case, obs)['status'], 'succeeded')
        self.assertNotSuccess(case, dict(obs, audit=self.ref({'items': []})))
        state['labels'] = [{'id': 'LABEL-A', 'fields': {'FIELD-A': {'selection': ['OTHER']}}}]
        self.assertNotSuccess(case, dict(obs, state_readback=self.ref(state)))

    def test_exposure_is_interval_censored_not_exact_and_reports_reexposure(self):
        probes = [self.probe('readable', '00:01:10', '00:01:11'),
                  self.probe('denied', '00:01:20', '00:01:21')]
        result = exposure(probes, self.obs['trigger_at'], self.obs['observation_end'])
        self.assertEqual((result['lower_seconds'], result['upper_seconds']), (10, 21))
        self.assertFalse(result['right_censored'])
        self.assertFalse(result['continuous_monitoring'])
        probes.append(self.probe('readable', '00:02:10', '00:02:11'))
        result = exposure(probes, self.obs['trigger_at'], self.obs['observation_end'])
        self.assertTrue(result.get('reexposure_observed'), result)
        self.assertTrue(result['right_censored'])
        self.assertIsNone(result['upper_seconds'])
        self.assertEqual(result['lower_seconds'], 70)

    def test_release_requires_prior_protection_and_actual_release_trigger(self):
        probe = copy.deepcopy(self.after)
        probe.update(outcome='readable', http_status=200)
        obs = dict(self.obs, probe_report=self.ref({'probes': [probe]}))
        for trigger in ('content_removed', 'rule_disabled', 'rule_deleted'):
            with self.subTest(trigger=trigger):
                case = dict(self.case, case_id='release/' + trigger, action='release',
                            trigger_kind=trigger, expected_outcome='readable')
                # 事前readable、規則ACTIVEのまま、本文修復の証拠もない。
                # 単に事後readableであるだけでは解除試験は成立しない。
                self.assertNotSuccess(case, obs)

    def test_release_after_content_removal_disabling_and_deletion_succeeds(self):
        for kind in ('content_removed', 'rule_disabled', 'rule_deleted'):
            with self.subTest(kind=kind):
                case, obs, _, _ = self.release_fixture(kind)
                result = self.evaluate(case, obs)
                self.assertEqual(result['status'], 'succeeded', result)
                self.assertEqual(result['latest_access_outcome'], 'readable')
                self.assertTrue(result['triggered_action_event_ids'])

    def test_release_requires_historical_native_action_record(self):
        for kind in ('content_removed', 'rule_disabled', 'rule_deleted'):
            case, obs, _, _ = self.release_fixture(kind)
            self.assertNotSuccess(case, dict(obs, audit=self.ref({'items': []})))

    def test_disabled_rule_must_actually_be_inactive(self):
        case, obs, policies, _ = self.release_fixture('rule_disabled')
        policies['after']['setting']['value']['state'] = 'ACTIVE'
        self.assertNotSuccess(case, dict(obs, policy_readbacks=self.ref(policies)))

    def test_deleted_rule_requires_complete_same_customer_absence_readback(self):
        case, obs, _, change = self.release_fixture('rule_deleted')
        for listing in (
            {'customer': 'customers/' + self.CUSTOMER, 'complete': False,
             'observed_at': '2026-11-16T00:01:05Z', 'policies': []},
            {'customer': 'customers/OTHER', 'complete': True,
             'observed_at': '2026-11-16T00:01:05Z', 'policies': []},
            {'customer': 'customers/' + self.CUSTOMER, 'complete': True,
             'observed_at': '2026-11-16T00:01:05Z', 'policies': [self.policy]},
            {'customer': 'customers/' + self.CUSTOMER, 'complete': True,
             'observed_at': '2026-11-16T00:00:59Z', 'policies': []},
        ):
            invalid = dict(change, complete_policy_list=self.ref(listing))
            self.assertNotSuccess(case, dict(obs, change_evidence=self.ref(invalid)))

    def test_content_removal_requires_all_fixed_values_and_current_new_revision(self):
        case, obs, _, change = self.release_fixture('content_removed')
        for after in (
            {'file_id': self.FILE, 'revision': '2', 'text': 'SYNTHETIC-PII-B'},
            {'file_id': self.FILE, 'revision': '1', 'text': ''},
            {'file_id': self.FILE, 'revision': 'OTHER', 'text': ''},
            {'file_id': 'OTHER', 'revision': '2', 'text': ''},
        ):
            invalid = dict(change, after_text=self.ref(after))
            self.assertNotSuccess(case, dict(obs, change_evidence=self.ref(invalid)))
        self.assertNotSuccess(dict(case, removed_values=[]), obs)

    def test_content_removal_old_revision_must_match_the_previously_blocked_file(self):
        case, obs, _, change = self.release_fixture('content_removed')
        invalid = dict(change, before_text=self.ref({
            'file_id': self.FILE, 'revision': 'UNRELATED-REVISION',
            'text': 'SYNTHETIC-PII-A SYNTHETIC-PII-B'}))
        self.assertNotSuccess(case, dict(obs, change_evidence=self.ref(invalid)))

    def test_readable_before_release_change_is_not_release_success(self):
        for kind in ('content_removed', 'rule_disabled', 'rule_deleted'):
            with self.subTest(kind=kind):
                case, obs, _, change = self.release_fixture(kind)
                change['changed_at'] = '2026-11-16T00:03:00Z'
                if kind == 'rule_deleted':
                    change['complete_policy_list'] = self.ref({
                        'customer': 'customers/' + self.CUSTOMER, 'complete': True,
                        'observed_at': '2026-11-16T00:03:05Z', 'policies': []})
                self.assertNotSuccess(case, dict(obs, change_evidence=self.ref(change)))

    def test_disabled_policy_update_must_not_predate_the_release_operation(self):
        case, obs, policies, _ = self.release_fixture('rule_disabled')
        policies['after']['setting']['value']['updateTime'] = '2026-11-16T00:00:00Z'
        self.assertNotSuccess(case, dict(obs, policy_readbacks=self.ref(policies)))

    def test_user_changed_label_is_preserved_after_content_removal(self):
        self.action_evidence('applyLabels', {'applyLabels': {}})
        # 元の規則・原票を使うfixtureへ、事前固定のラベル動作対応を反映する。
        case, obs, policies, change = self.release_fixture('content_removed')
        case.update(case_id='release/user_changed_label', action='release_label',
                    expected_outcome='label_preserved')
        label = {'id': 'LABEL-A', 'fields': {'FIELD-A': {'selection': ['USER-OPTION']}}}
        case['expected_label'] = label
        raw = self.raw_activity()
        raw['items'][0]['id']['time'] = '2026-11-16T00:00:40Z'
        raw['items'][0]['events'][0]['parameters'][-1]['messageValue'] = self.obs['expected_action_fragment']
        for key in ('before', 'after'):
            policies[key]['setting']['value']['action']['driveAction'] = {'applyLabels': {}}
        state = {'file_id': self.FILE, 'rule_id': self.RULE,
                 'observed_at': '2026-11-16T00:02:02Z', 'labels': [label]}
        obs.update(case_id=case['case_id'], audit=self.ref(raw),
                   policy_readbacks=self.ref(policies), state_readback=self.ref(state))
        self.bind_context(case, obs)
        result = self.evaluate(case, obs)
        self.assertEqual(result['status'], 'succeeded', result)
        state['labels'] = []
        self.assertNotSuccess(case, dict(obs, state_readback=self.ref(state)))

    def test_app_properties_are_not_classification_label_metadata(self):
        self.action_evidence('applyLabels', {'applyLabels': {}})
        case = dict(self.case, action='apply_label', expected_outcome='label_present')
        custom_mark = {'appProperties': {'sensitive': 'true'}}
        case['expected_label'] = custom_mark
        state = {'file_id': self.FILE, 'rule_id': self.RULE,
                 'observed_at': '2026-11-16T00:02:02Z', 'labels': [custom_mark]}
        self.assertNotSuccess(case, dict(self.obs, expected_label=custom_mark,
                                        state_readback=self.ref(state)))

    def test_observations_cannot_override_preplanned_action_or_label(self):
        case = dict(self.case, expected_action_fragment=self.obs['expected_action_fragment'])
        raw = copy.deepcopy(self.raw)
        changed = {'parameter': [{'name': 'action', 'value': 'auditOnly'}]}
        raw['items'][0]['events'][0]['parameters'][-1]['messageValue'] = changed
        self.assertNotSuccess(case, dict(self.obs, expected_action_fragment=changed,
                                        audit=self.ref(raw)))
        self.action_evidence('applyLabels', {'applyLabels': {}})
        original_label = {'id': 'LABEL-A', 'fields': {'FIELD-A': {'selection': ['ORIGINAL']}}}
        changed_label = {'id': 'LABEL-A', 'fields': {'FIELD-A': {'selection': ['CHANGED']}}}
        case = dict(self.case, action='apply_label', expected_outcome='label_present',
                    expected_label=original_label)
        state = {'file_id': self.FILE, 'rule_id': self.RULE,
                 'observed_at': '2026-11-16T00:02:02Z', 'labels': [changed_label]}
        self.assertNotSuccess(case, dict(self.obs, expected_label=changed_label,
                                        state_readback=self.ref(state)))

    def test_runtime_only_action_and_label_expectations_cannot_be_scored(self):
        case = dict(self.case)
        case.pop('expected_action_fragment')
        self.assertNotSuccess(case)
        self.action_evidence('applyLabels', {'applyLabels': {}})
        label = {'id': 'LABEL-A', 'fields': {'FIELD-A': {'selection': ['OPTION-A']}}}
        case = dict(self.case, action='apply_label', expected_outcome='label_present')
        state = {'file_id': self.FILE, 'rule_id': self.RULE,
                 'observed_at': '2026-11-16T00:02:02Z', 'labels': [label]}
        self.assertNotSuccess(case, dict(self.obs, expected_label=label,
                                        state_readback=self.ref(state)))

    def test_planned_remediation_mechanism_cannot_be_reassigned_in_observations(self):
        case = dict(self.case, mechanism='custom_acl')
        self.assertNotSuccess(case, self.obs)

    def test_external_identity_and_probe_route_cannot_be_substituted(self):
        for email in ('owner@example.test', 'unknown@example.net'):
            self.assertNotSuccess(obs=dict(self.obs, external_email=email))
        for route in ('drive.files.get', 'download'):
            self.assertNotSuccess(obs=dict(self.obs, probe_route=route))
        probe = copy.deepcopy(self.after)
        probe['permission_mutation_by_probe'] = True
        self.assertNotSuccess(obs=dict(self.obs, probe_report=self.ref({'probes': [probe]})))

    def test_out_of_window_action_and_probe_cannot_establish_success(self):
        for at in ('2026-11-16T00:00:59Z', '2026-11-16T00:04:01Z'):
            raw = copy.deepcopy(self.raw)
            raw['items'][0]['id']['time'] = at
            self.assertNotSuccess(obs=dict(self.obs, audit=self.ref(raw)))
        for start, end in (('00:00:58', '00:00:59'), ('00:04:00', '00:04:01')):
            probe = self.probe('denied', start, end)
            self.assertNotSuccess(obs=dict(self.obs, probe_report=self.ref({'probes': [probe]})))

    def test_exposure_without_denial_is_right_censored_and_reclosure_is_separate(self):
        probes = [self.probe('readable', '00:01:10', '00:01:11')]
        result = exposure(probes, self.obs['trigger_at'], self.obs['observation_end'])
        self.assertEqual(result['lower_seconds'], 10)
        self.assertIsNone(result['upper_seconds'])
        self.assertTrue(result['right_censored'])
        probes.extend([self.probe('denied', '00:01:20', '00:01:21'),
                       self.probe('readable', '00:02:10', '00:02:11'),
                       self.probe('denied', '00:02:20', '00:02:21')])
        result = exposure(probes, self.obs['trigger_at'], self.obs['observation_end'])
        self.assertTrue(result.get('reexposure_observed'), result)
        self.assertEqual((result['lower_seconds'], result['upper_seconds']), (70, 81))
        self.assertFalse(result['right_censored'])

    def test_negative_blocked_and_readable_cases_have_explicit_overblocking(self):
        case = dict(self.case, case_id='overblocking/block_sharing',
                    should_protect=False, expected_outcome='readable')
        obs = self.bind_context(case, dict(self.obs))
        blocked = self.evaluate(case, obs)
        self.assertEqual(blocked['status'], 'failed', blocked)
        self.assertTrue(blocked['overblocked'])
        probe = copy.deepcopy(self.after)
        probe['outcome'] = 'readable'
        probe['http_status'] = 200
        readable = self.evaluate(case, dict(obs, probe_report=self.ref({'probes': [probe]})))
        self.assertEqual(readable['status'], 'succeeded', readable)
        self.assertFalse(readable['overblocked'])

    def test_no_action_negative_requires_raw_derived_matching_evaluation(self):
        case, obs, _, _ = self.confirmed_negative_fixture()
        result = self.evaluate(case, obs)
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertFalse(result['overblocked'])
        self.assertEqual(result['triggered_action_event_ids'], [])
        missing = dict(obs)
        missing.pop('evaluation_confirmation')
        self.assertNotSuccess(case, missing)

    def test_no_action_negative_rejects_wrong_revision_condition_or_hash(self):
        case, obs, policies, after = self.confirmed_negative_fixture()
        wrong = copy.deepcopy(after)
        for key in ('owner_before', 'owner_after'):
            wrong[key]['version'] = 'OTHER-REVISION'
        self.assertNotSuccess(case, dict(obs, probe_report=self.ref({'probes': [wrong]})))
        for key in ('before', 'after'):
            policies[key]['setting']['value']['condition'] = {'contentCondition': 'false'}
        self.assertNotSuccess(case, dict(obs, policy_readbacks=self.ref(policies)))
        altered = copy.deepcopy(obs)
        altered['evaluation_confirmation']['sha256'] = '0' * 64
        self.assertNotSuccess(case, altered)

    def test_negative_confirmation_from_another_customer_cannot_be_reused(self):
        case, obs, policies, _ = self.confirmed_negative_fixture()
        for key in ('before', 'after'):
            policies[key]['customer'] = 'customers/OTHER-CUSTOMER'
        policies['after_at'] = obs['observation_end']
        self.assertNotSuccess(case, dict(obs, customer_id='OTHER-CUSTOMER',
                                        policy_readbacks=self.ref(policies)))

    def test_release_interval_measures_recovery_and_marks_later_reblocking(self):
        case, obs, _, _ = self.release_fixture('rule_disabled')
        result = self.evaluate(case, obs)
        interval = result['release_interval']
        self.assertEqual((interval['lower_seconds'], interval['upper_seconds']), (0, 61))
        self.assertFalse(interval['right_censored'])
        self.assertFalse(interval['reblock_observed'])
        probes = [self.probe('denied', '00:00:50', '00:00:51', version='1'),
                  self.probe('readable', '00:02:00', '00:02:01'),
                  self.probe('denied', '00:03:00', '00:03:01')]
        result = self.evaluate(case, dict(obs, probe_report=self.ref({'probes': probes})))
        self.assertEqual(result['status'], 'failed', result)
        self.assertTrue(result['release_interval']['reblock_observed'])
        self.assertTrue(result['release_interval']['right_censored'])

    def test_case_context_is_required_and_hash_checked(self):
        obs = dict(self.obs)
        obs.pop('case_context')
        self.assertNotSuccess(obs=obs)
        obs = copy.deepcopy(self.obs)
        obs['case_context']['sha256'] = '0' * 64
        self.assertNotSuccess(obs=obs)

    def test_case_factors_cannot_be_changed_without_matching_origin_evidence(self):
        context = json.loads(Path(self.obs['case_context']['path']).read_text())
        for key, value in [('prior_sharing', 'external_group'),
                            ('operator_role', 'editor'), ('trigger_kind', 'rule_change')]:
            with self.subTest(factor=key):
                case = dict(self.case, **{key: value})
                self.assertNotSuccess(case)
                changed = dict(context, **{key: value})
                # 文脈の表示だけ変えても、元ACL・実操作者・契機は変わらない。
                self.assertNotSuccess(case, dict(self.obs, case_context=self.ref(changed)))

    def test_case_context_cannot_rebind_file_case_or_time(self):
        context = json.loads(Path(self.obs['case_context']['path']).read_text())
        for key, value in [('file_id', 'OTHER'), ('case_id', 'OTHER'),
                            ('trigger_at', '2026-11-16T00:01:01Z')]:
            with self.subTest(field=key):
                self.assertNotSuccess(obs=dict(self.obs,
                    case_context=self.ref(dict(context, **{key: value}))))

    def test_trigger_origin_fields_and_real_unimplemented_adapter_are_rejected(self):
        context = json.loads(Path(self.obs['case_context']['path']).read_text())
        record = json.loads(Path(context['trigger_record']['path']).read_text())
        for key, value in [('file_id', 'OTHER'), ('rule_id', 'policies/OTHER'),
                            ('case_id', 'OTHER'), ('kind', 'rule_change'),
                            ('at', '2026-11-16T00:01:01Z'),
                            ('actor_email', 'editor@example.test'),
                            ('source', 'google_reports')]:
            with self.subTest(field=key):
                changed = dict(context, trigger_record=self.ref(dict(record, **{key: value})))
                self.assertNotSuccess(obs=dict(self.obs, case_context=self.ref(changed)))

    def test_complete_baseline_acl_binds_editor_and_external_reader_roles(self):
        for role, actor in [('editor', 'editor@example.test'), ('external_reader', self.EMAIL)]:
            with self.subTest(role=role):
                baseline = copy.deepcopy(self.baseline)
                if role == 'editor':
                    for key in ('permissions_before', 'permissions_after'):
                        baseline[key]['permissions'].append({'id': 'editor-id', 'type': 'user',
                                                           'role': 'writer', 'emailAddress': actor})
                case = dict(self.case, operator_role=role)
                obs = dict(self.obs, baseline_control=self.ref({'probes': [baseline]}))
                self.bind_context(case, obs, actor_email=actor)
                self.assertEqual(self.evaluate(case, obs)['status'], 'succeeded')

    def test_mixed_sharing_and_incomplete_context_snapshot_are_not_single_factor(self):
        context = json.loads(Path(self.obs['case_context']['path']).read_text())
        for variant in ('mixed', 'incomplete'):
            baseline = copy.deepcopy(self.baseline)
            for key in ('permissions_before', 'permissions_after'):
                if variant == 'mixed':
                    baseline[key]['permissions'].append({'id': 'public', 'type': 'anyone', 'role': 'reader'})
                else:
                    baseline[key]['complete'] = False
            changed = dict(context, baseline_probe=self.ref({'probes': [baseline]}))
            self.assertNotSuccess(obs=dict(self.obs, case_context=self.ref(changed)))

    def test_new_creation_without_creation_adapter_remains_pending(self):
        case = dict(self.case, case_id='block_sharing/external_user/owner/create',
                    trigger_kind='create')
        obs = self.bind_context(case, dict(self.obs, case_id=case['case_id']))
        self.assertNotSuccess(case, obs)

    def test_synthetic_success_is_not_reported_as_product_measurement(self):
        result = self.evaluate()
        self.assertEqual(result['status'], 'succeeded')
        self.assertEqual(result.get('evidence_domain'), 'synthetic')
        plan_ref = self.ref({'schema_version': 1, 'cases': [self.case]})
        bundle_ref = self.ref({'plan_sha256': plan_ref['sha256'],
                              'organization_domains': self.DOMAINS, 'observations': [self.obs]})
        report = score_remediation(plan_ref['path'], bundle_ref['path'], self.root / 'synthetic-report.json')
        self.assertIsNone(report['product_measured_success_rate'])
        self.assertIsNone(report['full_plan_success_rate'])
        group = report['groups']['native_dlp:block_sharing']
        self.assertEqual(group['planned'], 1)
        self.assertIsNone(group['adjudicated_success_rate'])
        self.assertEqual(group['by_evidence_domain']['synthetic']['adjudicated_success_rate'], 1)

    def test_observation_plan_hash_duplicate_case_and_unknown_case_are_rejected(self):
        plan_ref = self.ref({'schema_version': 1, 'cases': [self.case]})
        for bundle in (
            {'plan_sha256': '0' * 64, 'observations': []},
            {'plan_sha256': plan_ref['sha256'], 'observations': [self.obs, self.obs]},
            {'plan_sha256': plan_ref['sha256'], 'observations': [{'case_id': 'UNKNOWN'}]},
        ):
            bundle['organization_domains'] = self.DOMAINS
            bundle_ref = self.ref(bundle)
            with self.assertRaises(ValueError):
                score_remediation(plan_ref['path'], bundle_ref['path'], self.root / 'invalid-report.json')

    def test_missing_and_unsupported_cases_remain_in_plan_denominator(self):
        second = dict(self.case, case_id='pending-case')
        third = dict(self.case, case_id='unsupported-case', should_protect=False)
        plan = {'schema_version': 1, 'planned_mechanism': 'native_dlp',
                'cases': [self.case, second, third]}
        plan_ref = self.ref(plan)
        bundle = {'plan_sha256': plan_ref['sha256'], 'organization_domains': self.DOMAINS,
                  'planned_mechanism': 'native_dlp', 'observations': [self.obs,
                   {'case_id': 'unsupported-case', 'mechanism': 'native_dlp', 'status': 'unsupported'}]}
        bundle_ref = self.ref(bundle)
        result = score_remediation(plan_ref['path'], bundle_ref['path'], self.root / 'report.json')
        group = result['groups']['native_dlp:block_sharing']
        self.assertEqual(group['planned'], 3)
        self.assertEqual(group['evaluated'], 1)
        self.assertAlmostEqual(group['coverage'], 1 / 3)
        self.assertIsNone(group['full_plan_success_rate'])
        self.assertIsNone(group['overblocking_rate'])


if __name__ == '__main__':
    unittest.main()
