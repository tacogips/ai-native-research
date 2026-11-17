"""標準検知器の私有対応表を、通信せず証拠へ結び付ける試験。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import audit
from catalog import ITEMS
from common import digest, object_digest
from test_audit import fixture
from test_support import write


class StandardMappingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.f = fixture(self.root)
        self.table = {'schema_version': 1,
                      'detectors_by_item': {item: list(audit.STANDARD.get(item, [])) for item in ITEMS}}
        self.source = self.root / 'standard-detectors.json'

    def bind(self):
        write(self.source, self.table)
        self.f.manifest['standard_detector_map'] = {'path': str(self.source), 'sha256': digest(self.source)}
        mapping, _ = audit.standard_mapping(self.f.manifest)
        for profile in self.f.profiles:
            policies = {p['name']: p for p in self.f.policy_before['policies']}
            conditions = audit.expected_conditions(profile, policies, mapping)
            for role, reference in profile['roles'].items():
                for snapshot in (self.f.policy_before, self.f.policy_after):
                    policy = next(p for p in snapshot['policies'] if p['name'] == reference['id'])
                    policy['setting']['value']['condition'] = {'contentCondition': conditions[role]}
                reference['policy_sha256'] = object_digest(policy)
        self.f.flush()

    def imported(self):
        self.f.flush()
        return audit.import_audit(self.f.dataset, self.f.raw_path, self.f.manifest_path, self.f.bundle_path)

    def test_default_table_keeps_existing_candidates_and_records_semantic_hash(self):
        bundle = self.imported()
        mapping, proof = audit.standard_mapping({})
        self.assertEqual(mapping['email'], audit.STANDARD['email'])
        self.assertEqual(mapping['assets'], [])
        self.assertEqual(bundle['standard_detector_map'], proof)
        self.assertEqual(proof['source'], 'default')

    def test_explicit_table_drives_conditions_and_score_provenance(self):
        self.table['detectors_by_item']['email'] = ['SYNTHETIC_EMAIL_DETECTOR']
        self.bind()
        self.f.add('positive', profile=0)
        bundle = self.imported()
        result = audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)
        reference = bundle['standard_detector_map']
        self.assertEqual(reference['source'], 'file')
        self.assertEqual(reference['path'], str(self.source.resolve()))
        self.assertEqual(reference['sha256'], digest(self.source))
        self.assertEqual(reference['mapping_sha256'], object_digest(self.table['detectors_by_item']))
        self.assertEqual(result['standard_mapping_sha256'], reference['mapping_sha256'])
        self.assertEqual(result['observation_sources'][0]['standard_detector_map'], reference)
        self.assertEqual(result['by_threshold']['POSSIBLE']['evaluation_by_item']['standard']['email']['counts']['TP'], 1)

    def test_supported_but_unobserved_item_is_pending_not_unsupported(self):
        self.table['detectors_by_item']['assets'] = ['SYNTHETIC_ASSETS']
        self.bind()
        self.imported()
        result = audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)
        metric = result['by_threshold']['POSSIBLE']['evaluation_by_item']['standard']['assets']
        self.assertEqual(metric['counts']['pending'], 3)
        self.assertNotIn('unsupported', metric['counts'])

    def test_explicit_empty_list_is_unsupported_and_not_negative(self):
        self.table['detectors_by_item']['email'] = []
        self.f.profiles = self.f.profiles[1:]
        self.f.manifest['profiles'] = self.f.profiles
        self.bind()
        self.imported()
        result = audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)
        metric = result['by_threshold']['POSSIBLE']['evaluation_by_item']['standard']['email']
        self.assertEqual(metric['counts']['unsupported'], 3)
        self.assertEqual(metric['counts']['FN'], 0)
        self.assertIsNone(metric['primary_metrics'])

    def test_changed_file_is_rejected_when_scoring(self):
        self.bind()
        self.imported()
        self.source.write_text(self.source.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, '指紋'):
            audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)

    def test_resigned_mapping_cannot_replace_imported_evidence(self):
        self.bind()
        self.imported()
        self.table['detectors_by_item']['assets'] = ['SYNTHETIC_ASSETS']
        self.bind()
        # 対応表を変更し、その指紋も観測のprovenanceへ書き直す攻撃を模擬する。
        bundle = json.loads(self.f.bundle_path.read_text())
        bundle['provenance']['manifest']['sha256'] = digest(self.f.manifest_path)
        write(self.f.bundle_path, bundle)
        with self.assertRaises(ValueError):
            audit.score(self.f.dataset, self.f.bundle_path, self.f.report_path)

    def test_missing_or_wrong_hash_rejected_before_import(self):
        self.bind()
        self.f.manifest['standard_detector_map']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, '指紋'):
            self.imported()
        self.f.manifest['standard_detector_map'].pop('sha256')
        with self.assertRaises(ValueError):
            self.imported()

    def test_mapping_file_cannot_be_inside_public_repository(self):
        manifest = {'standard_detector_map': {'path': str(HERE / 'synthetic-table.json'), 'sha256': '0' * 64}}
        with self.assertRaisesRegex(ValueError, 'リポジトリ外'):
            audit.standard_mapping(manifest)

    def test_partial_unknown_duplicate_and_unsafe_mapping_rejected(self):
        mutations = [lambda t: t['detectors_by_item'].pop('email'),
                     lambda t: t['detectors_by_item'].update(unknown=[]),
                     lambda t: t['detectors_by_item'].update(email=['X', 'X']),
                     lambda t: t['detectors_by_item'].update(email=["X') || true || ('"]),
                     lambda t: t['detectors_by_item'].update(email='X'),
                     lambda t: t['detectors_by_item'].update(email=[None]),
                     lambda t: t.update(schema_version=True)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                table = copy.deepcopy(self.table)
                mutate(table)
                with self.assertRaises(ValueError):
                    audit.validate_standard_mapping(table)

    def test_duplicate_json_keys_are_rejected(self):
        self.source.write_text('{"schema_version":1,"schema_version":1,"detectors_by_item":{}}')
        with self.assertRaisesRegex(ValueError, '重複'):
            audit.standard_mapping({'standard_detector_map': {'path': str(self.source), 'sha256': digest(self.source)}})

    def test_different_mapping_tables_are_not_combined(self):
        self.bind()
        self.imported()
        first_path = self.root / 'first-observations.json'
        # 第1入力の原票・対応表・参照表を独立パスへ固定する。
        first_table = self.root / 'first-standard.json'
        first_table.write_bytes(self.source.read_bytes())
        first_manifest = copy.deepcopy(self.f.manifest)
        first_manifest['standard_detector_map']['path'] = str(first_table)
        first_manifest_path = self.root / 'first-manifest.json'
        write(first_manifest_path, first_manifest)
        audit.import_audit(self.f.dataset, self.f.raw_path, first_manifest_path, first_path)
        self.table['detectors_by_item']['assets'] = ['SYNTHETIC_ASSETS']
        self.f.profiles = self.f.profiles[1:]
        self.f.manifest['profiles'] = self.f.profiles
        self.bind()
        self.imported()
        with self.assertRaisesRegex(ValueError, '異なる標準検知器表'):
            audit.score(self.f.dataset, [first_path, self.f.bundle_path], self.f.report_path)


if __name__ == '__main__':
    unittest.main()
