"""公開Reports形式と独立した架空の正解を組む、通信なし試験用の補助。"""
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

from common import object_digest
from rules import expected_conditions

START = '2026-01-01T00:00:00Z'
TRIGGER = '2026-01-01T00:00:30Z'
BEFORE = '2026-01-01T00:01:00Z'
EVENT = '2026-01-01T00:02:00Z'
END = '2026-01-01T00:10:00Z'
AFTER = '2026-01-01T00:11:00Z'
FETCHED = '2026-01-01T00:12:00Z'
UPDATED = '2025-12-31T23:58:00Z'
UPDATE_USEC = str(int(datetime.fromisoformat(UPDATED.replace('Z', '+00:00')).timestamp()) * 1000000)


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class AuditFixture:
    def __init__(self, directory, kinds=('email', 'card'), thresholds=('POSSIBLE', 'LIKELY')):
        self.root = Path(directory)
        self.dataset = self.root / 'dataset'
        self.raw_path = self.root / 'raw.json'
        self.manifest_path = self.root / 'manifest.json'
        self.bundle_path = self.root / 'observations.json'
        self.report_path = self.root / 'metrics.json'
        self.scope_path = self.root / 'scope.json'
        self.before_path = self.root / 'policy-before.json'
        self.after_path = self.root / 'policy-after.json'
        self.query = {'orgUnit': 'orgUnits/synthetic-ou', 'query': "entity.org_units.exists(unit, unit.org_unit_id == orgUnitId('synthetic-ou'))"}
        self.truth = []
        self.files = []
        self.scope = {'bindings': []}
        for name, expected, track in [('basic', 1, 'basic'), ('adversarial', 1, 'adversarial'), ('negative', 0, 'basic')]:
            head_token='DLPHEAD'+name.upper();tail_token='DLPTAIL'+name.upper()
            content = head_token + '\n' + ('contact: sample@example.test' if expected else 'synthetic order 20482048') + '\n' + tail_token
            path = self.dataset / 'drive_upload' / (name + '.txt')
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            self.truth.append({'case_id': name, 'source_id': 'family-positive' if expected else 'family-negative',
                'file': name + '.txt', 'format': 'txt', 'kind': 'email', 'condition': track, 'split': '評価',
                'evaluation_track': track, 'expected': expected, 'sha256': sha,
                'expected_by_kind': {'email': expected, 'card': 0},
                'protection_expected_by_kind': {'email': expected, 'card': 0},
                'valid_number_expected_by_kind': {'email': None, 'card': 0},
                'scan_control': {'head_token': head_token, 'tail_token': tail_token}})
            metadata = {'revision': 'synthetic-revision-' + name, 'sha256': sha, 'trashed': False,
                        'drive_kind': 'my_drive', 'drive_id': None, 'owner_id': 'owner@example.test'}
            self.files.append({'case_id': name, 'file_id': 'synthetic-file-' + name,
                'revision': metadata['revision'], 'sha256': sha, 'drive_kind': 'my_drive',
                'drive_id': None, 'owner_id': 'owner@example.test',
                'scan_control': {'head_token': head_token, 'tail_token': tail_token},
                'before': dict(metadata, observed_at=BEFORE), 'after': dict(metadata, observed_at=AFTER),
                'trigger': {'kind': 'create', 'at': TRIGGER}})
            self.scope['bindings'].append({'case_id': name, 'file_id': 'synthetic-file-' + name,
                'scope_key': 'synthetic-scope', 'applies': True, 'drive_kind': 'my_drive',
                'drive_id': None, 'owner_id': 'owner@example.test', 'policy_query_sha256': object_digest(self.query)})
        self.profiles = []
        self.policies = []
        detectors={}
        for role in ['head','tail']:
            detectors[role]={'name':'policies/synthetic-'+role,'customer':'customers/CSYNTHETIC','type':'ADMIN',
                'policyQuery':copy.deepcopy(self.query),'setting':{'type':'settings/detector.word_list','value':{
                    'displayName':'synthetic-'+role,'description':'synthetic marker list',
                    'wordList':{'words':[row['scan_control'][role+'_token'] for row in self.truth]}}}}
            self.policies.append(detectors[role])
        for kind in kinds:
            for threshold in thresholds:
                roles = {role: {'id': f'policies/synthetic-{kind}-{threshold.lower()}-{role}',
                    'update_time_usec': UPDATE_USEC} for role in ['positive', 'negative', 'head', 'tail']}
                for role in ['head', 'tail']:
                    roles[role].update(detector_id='policies/synthetic-' + role, detector_sha256=object_digest(detectors[role]), control_kind='word_list')
                profile = {'kind': kind, 'threshold': threshold, 'scope_key': 'synthetic-scope',
                           'control_kind': 'word_list', 'roles': roles}
                conditions = expected_conditions(profile)
                for role, item in roles.items():
                    policy = {'name': item['id'], 'customer': 'customers/CSYNTHETIC', 'type': 'ADMIN',
                        'policyQuery': copy.deepcopy(self.query), 'setting': {'type': 'settings/rule.dlp', 'value': {
                            'state': 'ACTIVE', 'displayName': 'synthetic-' + kind + '-' + threshold.lower() + '-' + role,
                            'createTime': UPDATED, 'updateTime': UPDATED,
                            'triggers': ['google.workspace.drive.file.v1.share'],
                            'condition': {'contentCondition': conditions[role]},
                            'action': {'driveAction': {'auditOnly': {}}}}}}
                    item['policy_sha256'] = object_digest(policy)
                    self.policies.append(policy)
                self.profiles.append(profile)
        self.policy_before = {'observed_at': START, 'policies': copy.deepcopy(self.policies)}
        self.policy_after = {'observed_at': AFTER, 'policies': copy.deepcopy(self.policies)}
        self.pages = [{'items': []}]
        self.manifest = {'schema_version': 2, 'customer_id': 'CSYNTHETIC',
            'collection': {'complete': True, 'page_count': 1, 'start_time': START, 'end_time': END, 'fetched_at': FETCHED},
            'profiles': self.profiles, 'files': self.files}
        self.flush()

    def flush(self):
        write(self.dataset / 'ground_truth.json', self.truth)
        write(self.scope_path, self.scope)
        write(self.before_path, self.policy_before); write(self.after_path, self.policy_after)
        for key, path in [('scope_evidence', self.scope_path), ('policy_before', self.before_path), ('policy_after', self.after_path)]:
            self.manifest[key] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        write(self.manifest_path, self.manifest); write(self.raw_path, {'pages': self.pages})

    def add(self, role, case='basic', profile=0, match=True, version=UPDATE_USEC,
            customer='CSYNTHETIC', data_source='DRIVE', at=EVENT, rule_type='DLP'):
        p = self.profiles[profile]
        params = [{'name': 'resource_id', 'value': 'synthetic-file-' + case},
            {'name': 'rule_resource_name', 'value': p['roles'][role]['id']},
            {'name': 'data_source', 'value': data_source}, {'name': 'rule_type', 'value': rule_type}]
        if match is not None:params.append({'name': 'has_content_match', 'boolValue': match})
        if version is not None:params.append({'name': 'rule_update_time_usec', 'intValue': str(version)})
        activity = {'id': {'applicationName': 'rules', 'customerId': customer, 'time': at,
                          'uniqueQualifier': str(sum(len(page['items']) for page in self.pages) + 1)},
                    'actor': {'email': 'operator@example.test'},
                    'events': [{'name': 'rule_match', 'type': 'DLP', 'parameters': params}]}
        self.pages[-1]['items'].append(activity)
        return activity

    def negative(self, case='basic', profile=0):
        for role in ['head', 'tail', 'negative']:self.add(role, case, profile)

    def populate(self):
        for row in self.truth:
            for index, p in enumerate(self.profiles):
                if row['expected_by_kind'].get(p['kind']):self.add('positive', row['case_id'], index)
                else:self.negative(row['case_id'], index)

    def convert(self):
        from observations import convert
        self.flush()
        return convert(self.manifest, self.raw_path)

    def imported(self):
        from observations import import_audit
        self.flush()
        return import_audit(self.dataset, self.raw_path, self.manifest_path, self.bundle_path)
