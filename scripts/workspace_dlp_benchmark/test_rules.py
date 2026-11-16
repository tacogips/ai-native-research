"""Policy計画・適用の通信境界と不確定変更停止を、偽のサービスで検証する。"""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

try:
    from . import dataset, rules
except ImportError:
    import dataset
    import rules


class FakeService:
    def __init__(self, pending=False, unknown_default=False, uncertain_post=False):
        self.calls, self.policies, self.operations = [], {}, {}
        self.pending, self.unknown_default, self.uncertain_post = pending, unknown_default, uncertain_post

    def request(self, method, path, body=None):
        self.calls.append((method, path, copy.deepcopy(body)))
        if method == 'POST':
            number = len(self.policies) + 1
            name, operation_name = f'policies/resource_{number}', f'operations/create_{number}'
            policy = copy.deepcopy(body)
            policy.update(name=name, type='ADMIN')
            policy['policyQuery']['sortOrder'] = float(number)
            policy['policyQuery']['group'] = ''
            policy['setting']['value'].update(createTime='2026-11-16T00:00:00.123456Z',
                                               updateTime='2026-11-16T00:00:00.123456Z')
            if self.unknown_default:
                policy['setting']['value']['unknownServerDefault'] = True
            self.policies[name] = policy
            completed = {'name': operation_name, 'done': True, 'response': {'name': name}}
            self.operations[operation_name] = completed
            if self.uncertain_post:
                raise TimeoutError('秘密のtokenを含むかもしれない接続例外')
            return {'name': operation_name, 'done': False} if self.pending else completed
        if path in self.operations:
            return copy.deepcopy(self.operations[path])
        if path in self.policies:
            return copy.deepcopy(self.policies[path])
        raise rules.ApiError(404, 'NOT_FOUND')


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='workspace-dlp-rules-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dataset = self.root / 'dataset'
        with contextlib.redirect_stdout(io.StringIO()):
            dataset.make(self.dataset)
        self.config = {'customer': 'customers/CEXAMPLE', 'org_unit': 'orgUnits/TESTOU',
                       'namespace': 'DLPTEST-unit-suite', 'token_env': 'BENCHMARK_TOKEN'}
        self.config_path, self.plan_path = self.root / 'config.json', self.root / 'plan.json'

    def plan(self):
        self.config_path.write_text(json.dumps(self.config))
        return rules.plan_rules(self.dataset, self.config_path, self.plan_path)

    def apply(self, service, output=None):
        with mock.patch.dict('os.environ', {'BENCHMARK_TOKEN': 'NEVER_SAVE_THIS_SECRET'}), \
             mock.patch.object(rules, 'Client', return_value=service), \
             mock.patch.object(rules.time, 'sleep'):
            return rules.apply_rules(self.plan_path, output or self.root / 'run.json', execute=True)

    def test_default_plan_and_apply_dry_run_make_no_client(self):
        plan = self.plan()
        self.assertEqual(len(plan['operations']), 46)
        self.assertEqual(len(plan['profiles']), 21)
        self.assertEqual(plan['control_kind'], 'word_list')
        with mock.patch.object(rules, 'Client', side_effect=AssertionError('通信禁止')):
            preview = rules.apply_rules(self.plan_path, self.root / 'preview.json')
        self.assertEqual(preview['network_calls'], 0)
        self.assertEqual(preview['status'], 'dry_run')
        self.assertTrue(all('localref:' in p['roles']['head']['detector_id'] for p in plan['profiles']))

    def test_full_create_operation_poll_get_and_binding_hashes(self):
        plan = self.plan()
        service = FakeService(pending=True)
        result = self.apply(service)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(result['policies']), 46)
        self.assertEqual(sum(m == 'POST' for m, _, _ in service.calls), 46)
        self.assertEqual(sum(p.startswith('operations/') for _, p, _ in service.calls), 46)
        self.assertEqual(len(result['profiles']), 21)
        for profile in result['profiles']:
            self.assertNotIn('localref:', json.dumps(profile))
            for role_name, role in profile['roles'].items():
                policy = service.policies[role['id']]
                self.assertEqual(role['policy_sha256'], rules.object_digest(policy))
                self.assertEqual(role['update_time_usec'], '1794787200123456')
                if role_name in ('head', 'tail'):
                    self.assertEqual(role['detector_sha256'], rules.object_digest(service.policies[role['detector_id']]))
            conditions = rules.expected_conditions(profile)
            self.assertIn('&& !(', conditions['negative'])
            self.assertTrue(conditions['positive'].startswith('(' + conditions['head'] + ')'))
        saved = json.loads((self.root / 'run.json').read_text())
        self.assertNotIn('NEVER_SAVE_THIS_SECRET', json.dumps(saved))
        # 完了済み同一台帳への再呼出しで二重作成しない。
        with mock.patch.object(rules, 'Client', side_effect=AssertionError('再通信禁止')):
            self.assertEqual(rules.apply_rules(self.plan_path, self.root / 'run.json', True), saved)

    def test_native_remediation_only_changes_positive_action(self):
        self.config.update(mode='native_remediation', positive_action={'blockAccess': {}},
                           kinds=['card'], thresholds=['POSSIBLE'])
        plan = self.plan()
        self.assertEqual(len(plan['operations']), 6)
        actions = {step['key']: step['payload']['setting']['value']['action']
                   for step in plan['operations'] if step['payload']['setting']['type'] == 'settings/rule.dlp'}
        self.assertEqual(actions['card_POSSIBLE_positive'], {'driveAction': {'blockAccess': {}}})
        for key in ('card_POSSIBLE_negative', 'head_rule', 'tail_rule'):
            self.assertEqual(actions[key], rules.AUDIT)
        self.config['mode'] = 'audit'
        with self.assertRaises(ValueError):
            self.plan()

    def test_unknown_server_defaults_are_saved_and_not_accepted(self):
        self.plan()
        service = FakeService(unknown_default=True)
        with self.assertRaises(rules.PolicyExecutionError):
            self.apply(service)
        checkpoint = json.loads((self.root / 'run.json').read_text())
        self.assertEqual(checkpoint['status'], 'stopped')
        step = checkpoint['steps']['head_detector']
        self.assertEqual(step['status'], 'readback_failed')
        self.assertTrue(step['readback']['setting']['value']['unknownServerDefault'])
        self.assertIn('readback_difference', step)
        self.assertEqual(len(service.policies), 1)

    def test_ambiguous_post_result_never_reposts(self):
        self.plan()
        service = FakeService(uncertain_post=True)
        with self.assertRaises(rules.PolicyExecutionError):
            self.apply(service)
        checkpoint = json.loads((self.root / 'run.json').read_text())
        self.assertEqual(checkpoint['steps']['head_detector']['status'], 'uncertain_mutation')
        self.assertEqual(sum(m == 'POST' for m, _, _ in service.calls), 1)
        # 2回目は状態を読んで停止する。作成済みか不明なPOSTの再送はしない。
        second_service = FakeService()
        with self.assertRaises(rules.PolicyExecutionError):
            self.apply(second_service)
        self.assertEqual(sum(m == 'POST' for m, _, _ in service.calls), 1)
        self.assertEqual(second_service.calls, [])
        self.assertNotIn('NEVER_SAVE_THIS_SECRET', (self.root / 'run.json').read_text())

    def test_pending_operation_timeout_is_not_success(self):
        state, writes = {}, []
        service = FakeService()
        service.operations['operations/never_done'] = {'name': 'operations/never_done', 'done': False}
        with mock.patch.object(rules.time, 'monotonic', side_effect=[0, 0, 121]), \
             mock.patch.object(rules.time, 'sleep'):
            with self.assertRaises(TimeoutError):
                rules._poll(service, {'name': 'operations/never_done', 'done': False},
                            state, lambda: writes.append(copy.deepcopy(state)))
        self.assertEqual(state['status'], 'operation_timeout')
        self.assertFalse(any(m == 'POST' for m, _, _ in service.calls))
        self.assertTrue(writes)

    def test_scope_and_operation_validation_before_any_request(self):
        self.plan()
        plan = json.loads(self.plan_path.read_text())
        plan['operations'][0]['action'] = 'delete'
        plan.pop('plan_sha256')
        plan['plan_sha256'] = rules.object_digest(plan)
        self.plan_path.write_text(json.dumps(plan))
        with mock.patch.object(rules, 'Client', side_effect=AssertionError('通信禁止')):
            with self.assertRaises(ValueError):
                rules.apply_rules(self.plan_path, self.root / 'run.json', True)
        self.config['namespace'] = 'production'
        with self.assertRaises(ValueError):
            self.plan()

    def test_control_limits_fail_closed_and_input_change_invalidates_plan(self):
        self.plan()
        path = self.dataset / 'ground_truth.json'
        data = json.loads(path.read_text())
        data[0]['scan_control']['head_token'] += 'A' * 20
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.plan()
        with mock.patch.object(rules, 'Client', side_effect=AssertionError('通信禁止')):
            with self.assertRaises(ValueError):
                rules.apply_rules(self.plan_path, self.root / 'run.json', True)

    def test_operation_cannot_redirect_to_other_host_or_traverse(self):
        for name in ('https://attacker.example/operations/a', '../operations/a', 'operations/a?token=x'):
            with self.assertRaises(ValueError):
                rules._poll(FakeService(), {'name': name, 'done': False}, {}, lambda: None)

    def test_operation_error_and_wrong_boolean_never_become_success(self):
        state = {}
        with self.assertRaises(rules.PolicyExecutionError):
            rules._poll(FakeService(), {'done': True, 'error': {'code': 13}, 'response': {}}, state, lambda: None)
        self.assertEqual(state['status'], 'operation_failed')
        with self.assertRaises(ValueError):
            rules._poll(FakeService(), {'done': 0, 'name': 'operations/a'}, {}, lambda: None)

    def test_private_output_and_concurrent_run_guard(self):
        import fcntl
        self.plan()
        with self.assertRaises(ValueError):
            rules.apply_rules(self.plan_path, Path(__file__).parent / 'not-allowed.json')
        out = self.root / 'locked.json'
        with out.with_name(out.name + '.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with mock.patch.object(rules, 'Client', side_effect=AssertionError('通信禁止')):
                with self.assertRaises(BlockingIOError):
                    rules.apply_rules(self.plan_path, out, True)

    def test_more_than_950_control_words_is_rejected_without_splitting(self):
        rows = []
        for number in range(951):
            head, tail = dataset._tokens('unique-' + str(number))
            rows.append({'case_id': str(number), 'scan_control': {'head_token': head, 'tail_token': tail}})
        (self.dataset / 'ground_truth.json').write_text(json.dumps(rows))
        with self.assertRaisesRegex(ValueError, '950'):
            self.plan()

    def test_auth_header_is_not_redirected(self):
        # 実際にHTTPへ接続せず、Bearerを持つ要求に対するredirect拒否を検証。
        request = rules.urllib.request.Request(rules.BASE + 'policies', headers={'Authorization': 'Bearer SECRET'})
        self.assertIsNone(rules._NoRedirect().redirect_request(request, None, 302, 'redirect', {}, 'https://other.example/'))


if __name__ == '__main__':
    unittest.main()
