"""監査原票の欠落・版違い・矛盾を、陰性の完成値に変えない回帰試験。"""
import copy
import json
import tempfile
import unittest
from unittest.mock import patch

import common
import observations
from common import object_digest
from test_support import AuditFixture, EVENT, UPDATE_USEC, write


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f = AuditFixture(self.temp.name, kinds=('email',), thresholds=('POSSIBLE',))

    def row(self):
        return next(r for r in self.f.convert()['rows'] if r['case_id'] == 'basic')

    def resign(self, role):
        name = self.f.profiles[0]['roles'][role]['id']
        policy = next(p for p in self.f.policy_before['policies'] if p['name'] == name)
        self.f.profiles[0]['roles'][role]['policy_sha256'] = object_digest(policy)

    def edit_policy(self, role, edit):
        name = self.f.profiles[0]['roles'][role]['id']
        for saved in [self.f.policy_before, self.f.policy_after]:
            edit(next(p for p in saved['policies'] if p['name'] == name))
        self.resign(role)

    def edit_detector(self, role, edit):
        name = self.f.profiles[0]['roles'][role]['detector_id']
        for saved in [self.f.policy_before, self.f.policy_after]:
            edit(next(p for p in saved['policies'] if p['name'] == name))
        before = next(p for p in self.f.policy_before['policies'] if p['name'] == name)
        self.f.profiles[0]['roles'][role]['detector_sha256'] = object_digest(before)

    def test_strong_positive_is_detected(self):
        self.f.add('positive');row = self.row()
        self.assertEqual(row['status'], 'detected')
        self.assertEqual(row['detection_delay_seconds'], 90)
        self.assertFalse(row['scan_version_directly_observed'])

    def test_false_content_match_is_not_a_detection(self):
        self.f.add('positive', match=False)
        self.assertEqual(self.row()['status'], 'pending')

    def test_missing_content_match_is_not_a_detection(self):
        self.f.add('positive', match=None)
        self.assertEqual(self.row()['status'], 'pending')

    def test_string_true_is_not_boolean_match(self):
        self.f.add('positive', match='true')
        self.assertEqual(self.row()['status'], 'pending')

    def test_both_controls_and_negative_allow_conditional_inference(self):
        self.f.negative();row = self.row()
        self.assertEqual(row['status'], 'not_detected')
        self.assertTrue(all(row['evidence'][role] for role in ['negative', 'head', 'tail']))
        self.assertFalse(row['scan_version_directly_observed'])

    def test_controls_alone_are_not_point_negative(self):
        self.f.add('head');self.f.add('tail')
        self.assertEqual(self.row()['status'], 'conditional_not_detected')

    def test_one_control_does_not_prove_scan(self):
        self.f.add('head');self.f.add('negative')
        self.assertEqual(self.row()['status'], 'pending')

    def test_missing_rule_version_is_not_point_negative(self):
        self.f.add('head');self.f.add('tail');self.f.add('negative', version=None)
        self.assertEqual(self.row()['status'], 'conditional_not_detected')

    def test_missing_positive_rule_version_remains_pending(self):
        self.f.add('positive', version=None)
        self.assertEqual(self.row()['status'], 'pending')

    def test_old_rule_version_does_not_match(self):
        self.f.add('positive', version=int(UPDATE_USEC)-1)
        self.assertEqual(self.row()['status'], 'pending')

    def test_wrong_customer_does_not_match(self):
        self.f.add('positive', customer='COTHER')
        self.assertEqual(self.row()['status'], 'pending')

    def test_wrong_service_does_not_match(self):
        self.f.add('positive', data_source='GMAIL')
        self.assertEqual(self.row()['status'], 'pending')

    def test_wrong_rule_type_does_not_match(self):
        self.f.add('positive', rule_type='OTHER')
        self.assertEqual(self.row()['status'], 'pending')

    def legacy_activity(self, role='positive', name=None, version=UPDATE_USEC, number='901'):
        activity = self.f.add(role, version=version)
        rule = next(p for p in self.f.policy_before['policies'] if p['name'] == self.f.profiles[0]['roles'][role]['id'])
        activity['events'][0]['parameters'] = [
            {'name': 'resource_id', 'value': 'synthetic-file-basic'},
            {'name': 'application', 'value': 'drive'},
            {'name': 'rule_id', 'intValue': number},
            {'name': 'rule_name', 'value': name if name is not None else rule['setting']['value']['displayName']},
            {'name': 'has_content_match', 'boolValue': True}]
        if version is not None:activity['events'][0]['parameters'].append({'name': 'rule_update_time_usec', 'intValue': str(version)})
        return activity

    def test_public_legacy_application_and_numeric_rule_id(self):
        self.legacy_activity()
        self.assertEqual(self.row()['status'], 'detected')

    def test_legacy_numeric_id_needs_matching_name(self):
        self.f.profiles[0]['roles']['positive']['event_aliases'] = ['901']
        self.legacy_activity(name='different-rule')
        self.assertEqual(self.row()['status'], 'pending')

    def test_legacy_numeric_id_needs_exact_rule_version(self):
        self.legacy_activity(version=str(int(UPDATE_USEC)-1))
        self.assertEqual(self.row()['status'], 'pending')

    def test_legacy_numeric_id_without_version_is_pending(self):
        self.legacy_activity(version=None)
        self.assertEqual(self.row()['status'], 'pending')

    def test_match_taxonomy_cannot_be_redefined_to_action_complete(self):
        self.f.manifest['match_event_names'] = ['action_complete']
        activity = self.f.add('positive');activity['events'][0]['name'] = 'action_complete'
        with self.assertRaises(ValueError):self.row()

    def test_rule_taxonomy_cannot_be_redefined_to_other(self):
        self.f.manifest['dlp_rule_type_values'] = ['OTHER'];self.f.add('positive', rule_type='OTHER')
        with self.assertRaises(ValueError):self.row()

    def test_policy_customer_must_match_audit_collection_customer(self):
        for saved in [self.f.policy_before, self.f.policy_after]:
            for policy in saved['policies']:policy['customer'] = 'customers/COTHER'
        for role in ['positive', 'negative', 'head', 'tail']:self.resign(role)
        for edge in ['head', 'tail']:
            name = self.f.profiles[0]['roles'][edge]['detector_id']
            policy = next(p for p in self.f.policy_before['policies'] if p['name'] == name)
            self.f.profiles[0]['roles'][edge]['detector_sha256'] = object_digest(policy)
        self.f.add('positive')
        with self.assertRaises(ValueError):self.row()

    def test_action_complete_is_not_content_match(self):
        activity = self.f.add('positive');activity['events'][0]['name'] = 'action_complete'
        self.assertEqual(self.row()['status'], 'pending')

    def test_later_event_is_not_in_observation_window(self):
        self.f.add('positive', at='2026-01-01T00:10:01Z')
        self.assertEqual(self.row()['status'], 'pending')

    def test_changed_revision_is_stale(self):
        self.f.add('positive');self.f.files[0]['after']['revision'] = 'different'
        self.assertEqual(self.row()['status'], 'stale')

    def test_changed_sha_is_stale(self):
        self.f.add('positive');self.f.files[0]['after']['sha256'] = '0'*64
        self.assertEqual(self.row()['status'], 'stale')

    def test_changed_owner_is_stale(self):
        self.f.add('positive');self.f.files[0]['after']['owner_id'] = 'another@example.test'
        self.assertEqual(self.row()['status'], 'stale')

    def test_changed_shared_drive_is_stale(self):
        self.f.add('positive');file = self.f.files[0]
        file.update(drive_kind='shared_drive', drive_id='synthetic-drive-one', owner_id='synthetic-drive-one')
        file['before'].update(drive_kind='shared_drive', drive_id='synthetic-drive-one', owner_id='synthetic-drive-one')
        file['after'].update(drive_kind='shared_drive', drive_id='synthetic-drive-two', owner_id='synthetic-drive-two')
        self.f.scope['bindings'][0].update(drive_kind='shared_drive', drive_id='synthetic-drive-one', owner_id='synthetic-drive-one')
        self.assertEqual(self.row()['status'], 'stale')

    def test_trashed_before_is_not_stable(self):
        self.f.add('positive');self.f.files[0]['before']['trashed'] = True
        self.assertEqual(self.row()['status'], 'stale')

    def test_scope_binding_for_other_owner_cannot_decide(self):
        self.f.add('positive');self.f.scope['bindings'][0]['owner_id'] = 'another@example.test'
        self.assertEqual(self.row()['status'], 'pending')

    def test_scope_binding_for_other_scope_cannot_decide(self):
        self.f.add('positive');self.f.scope['bindings'][0]['scope_key'] = 'another-scope'
        self.assertEqual(self.row()['status'], 'pending')

    def test_scope_proof_for_other_policy_query_cannot_decide(self):
        self.f.add('positive');self.f.scope['bindings'][0]['policy_query_sha256'] = '0'*64
        self.assertEqual(self.row()['status'], 'pending')

    def test_manifest_rule_version_must_match_readback(self):
        self.f.profiles[0]['roles']['positive']['update_time_usec'] = str(int(UPDATE_USEC)-1)
        with self.assertRaises(ValueError):self.row()

    def test_positive_and_negative_same_revision_are_conflict(self):
        self.f.add('positive');self.f.negative()
        self.assertEqual(self.row()['status'], 'conflict')

    def test_incomplete_page_collection_is_rejected(self):
        self.f.pages[0]['nextPageToken'] = 'not-fetched'
        with self.assertRaisesRegex(ValueError, 'ページ'):self.row()

    def test_duplicate_identical_activity_is_not_double_counted(self):
        activity = self.f.add('positive');self.f.pages.append({'items': [copy.deepcopy(activity)]})
        self.f.pages[0]['nextPageToken'] = 'second';self.f.manifest['collection']['page_count'] = 2
        self.assertEqual(len(self.row()['evidence']['positive']), 1)

    def test_duplicate_activity_with_changed_event_is_rejected(self):
        activity = self.f.add('positive');changed = copy.deepcopy(activity)
        changed['events'][0]['parameters'][-2]['boolValue'] = False
        self.f.pages[0]['items'].append(changed)
        with self.assertRaisesRegex(ValueError, '矛盾'):self.row()

    def test_duplicate_activity_with_changed_actor_is_rejected(self):
        activity = self.f.add('positive');changed = copy.deepcopy(activity)
        changed['actor']['email'] = 'different@example.test';self.f.pages[0]['items'].append(changed)
        with self.assertRaisesRegex(ValueError, '矛盾'):self.row()

    def test_duplicate_parameter_is_rejected(self):
        activity = self.f.add('positive');activity['events'][0]['parameters'].append({'name': 'resource_id', 'value': 'another'})
        with self.assertRaisesRegex(ValueError, '重複'):self.row()

    def test_rule_queries_must_agree(self):
        self.edit_policy('negative', lambda p: p['policyQuery'].update(query='false'))
        with self.assertRaisesRegex(ValueError, '適用範囲'):self.row()

    def test_resigned_but_semantically_weakened_condition_is_rejected(self):
        self.edit_policy('negative', lambda p: p['setting']['value'].update(condition={'contentCondition': 'true'}))
        with self.assertRaises(ValueError):self.row()

    def test_marker_list_cannot_omit_file_tail(self):
        self.edit_detector('tail', lambda p: p['setting']['value']['wordList']['words'].remove('DLPTAILBASIC'))
        with self.assertRaises(ValueError):self.row()

    def test_detector_hash_tampering_is_rejected(self):
        self.f.profiles[0]['roles']['head']['detector_sha256'] = '0'*64
        with self.assertRaises(ValueError):self.row()

    def test_same_head_and_tail_detector_is_rejected(self):
        profile = self.f.profiles[0]
        profile['roles']['tail']['detector_id'] = profile['roles']['head']['detector_id']
        profile['roles']['tail']['detector_sha256'] = profile['roles']['head']['detector_sha256']
        from rules import expected_conditions
        conditions = expected_conditions(profile)
        for role in ['positive', 'negative', 'head', 'tail']:
            self.edit_policy(role, lambda p, role=role: p['setting']['value'].update(condition={'contentCondition': conditions[role]}))
        with self.assertRaises(ValueError):self.row()

    def test_scope_readback_hash_tampering_is_rejected(self):
        self.f.flush();write(self.f.scope_path, {})
        with self.assertRaisesRegex(ValueError, '指紋'):observations.convert(self.f.manifest, self.f.raw_path)

    def test_scope_proof_must_be_outside_repository(self):
        self.f.flush()
        with patch.object(common, 'REPOSITORY', self.f.root.resolve()):
            with self.assertRaises(ValueError):observations.checked_reference(self.f.manifest['scope_evidence'])

    def test_import_rejects_marker_different_from_registered_truth(self):
        self.f.files[0]['scan_control']['head_token'] = 'DLPHEADOTHER'
        self.edit_detector('head', lambda p: p['setting']['value']['wordList']['words'].append('DLPHEADOTHER'))
        self.f.negative()
        with self.assertRaises(ValueError):self.f.imported()

    def test_timezone_is_required(self):
        self.f.add('positive', at='2026-01-01T00:02:00')
        with self.assertRaisesRegex(ValueError, '時刻'):self.row()


if __name__ == '__main__':unittest.main()
