"""外部接続せず、実主体・規則範囲と外部読取の誤判定を確認する。"""
import copy
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from xml.etree import ElementTree as ET

import google_drive


class Request:
    def __init__(self,value):self.value=value
    def execute(self):return copy.deepcopy(self.value)


class FakeDrive:
    def __init__(self,email='owner@example.test',shared_drive_id=None):
        self.email=email;self.shared_drive_id=shared_drive_id
        self.rows={};self.permissions_log=[];self.created=[];self.revoked=set();self.metadata={};self.permission_rows={}
        self.metadata['test-parent']=self.file_metadata('test-parent',{'mimeType':google_drive.MIME_FOLDER,'parents':[]})
    def file_metadata(self,ident,body):
        result={'id':ident,'mimeType':body.get('mimeType','application/octet-stream'),'parents':body.get('parents',[]),
                'capabilities':{'canAddChildren':True},'trashed':False,'version':'1','createdTime':'2026-01-01T00:00:00Z','modifiedTime':'2026-01-01T00:00:00Z','appProperties':body.get('appProperties',{})}
        if self.shared_drive_id:result['driveId']=self.shared_drive_id
        else:result['owners']=[{'emailAddress':self.email}]
        return result
    def files(self):return self
    def permissions(self):return self
    def create(self,**kw):
        body=kw['body']
        if 'role' in body:
            self.permissions_log.append(body);self.permission_rows[kw['fileId']]=[{'id':'permission-1',**body}]
            return Request({'id':'permission-1'})
        ident='file-'+str(len(self.created));self.created.append(kw)
        metadata=self.file_metadata(ident,body);self.metadata[ident]=metadata
        if body.get('mimeType')==google_drive.MIME_SHEET:
            media=kw['media_body'];raw=media.getbytes(0,media.size())
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                root=ET.fromstring(archive.read('xl/sharedStrings.xml'))
                self.rows[ident]='\n'.join(''.join(item.itertext()) for item in root)
        return Request(dict(metadata,webViewLink='https://example.test/'+ident))
    def about(self):return self
    def get(self,**kw):
        if kw['fields'].startswith('user'):return Request({'user':{'emailAddress':self.email}})
        return Request(self.metadata[kw['fileId']])
    def list(self,**kw):return Request({'permissions':self.permission_rows.get(kw['fileId'],[])})
    def delete(self,**kw):
        self.permissions_log.append(kw);self.revoked.add(kw['fileId']);self.permission_rows[kw['fileId']]=[]
        return Request({})
    def export_media(self,**kw):return Request(b'fake export for request testing only')


class ReaderDrive:
    def __init__(self,email):self.email=email
    def about(self):return self
    def get(self,**kw):return Request({'user':{'emailAddress':self.email}})


def http_error(status,reason=None):
    import httplib2
    from googleapiclient.errors import HttpError
    detail={'message':'The caller does not have permission' if reason is None else 'API unavailable'}
    if reason:detail['errors']=[{'reason':reason}]
    return HttpError(httplib2.Response({'status':status}),json.dumps({'error':detail}).encode())


class FakeSheets:
    def __init__(self,drive,missing=False):self.drive=drive;self.missing=missing;self.requests=[];self.allow_after_revoke=False
    def spreadsheets(self):return self
    def get(self,spreadsheetId,**kw):
        if spreadsheetId in self.drive.revoked and not self.allow_after_revoke:raise http_error(403)
        text='' if self.missing else self.drive.rows[spreadsheetId]
        return Request({'sheets':[{'properties':{'sheetId':0},'data':[{'rowData':[{'values':[{'formattedValue':text}]}]}]}]})
    def batchUpdate(self,**kw):self.requests.append(kw);return Request({})


class DriveTests(unittest.TestCase):
    @contextmanager
    def api(self,drive,sheets,reader_email='reader@example.test',credentials=None):
        owner_credentials=credentials or SimpleNamespace();reader_credentials=object()
        reader=ReaderDrive(reader_email)
        def build(name,*args,**kwargs):
            if name=='sheets':return sheets
            return reader if kwargs['credentials'] is reader_credentials else drive
        with patch('google.auth.default',return_value=(owner_credentials,None)),patch('google.auth.load_credentials_from_file',return_value=(reader_credentials,None)),patch('googleapiclient.discovery.build',side_effect=build):yield

    def make_dataset(self,folder):
        import xlsxwriter
        root=Path(folder)/'dataset';(root/'ground_truth').mkdir(parents=True);(root/'drive_upload/office').mkdir(parents=True)
        records=[]
        for i in range(4):
            positive=i<2;text='氏名：山田 太郎' if positive else '機器の仕様'
            path=root/'drive_upload/office'/f'case-{i}.xlsx';w=xlsxwriter.Workbook(path);s=w.add_worksheet();s.write('A1',text);w.close()
            records.append({'path':'office/'+path.name,'source_id':f'case-{i}','format':'XLSX','positive':positive,'entities':[{'type':'氏名','value':'山田 太郎'}] if positive else []})
        (root/'ground_truth/files.json').write_text(json.dumps(records,ensure_ascii=False))
        return root

    def scope(self,temp,drive_kind='my_drive',creator='owner@example.test',parent='test-parent',shared_drive_id='shared-test',target_kind=None):
        target_kind=target_kind or ('user' if drive_kind=='my_drive' else 'shared_drive')
        proof={'schema_version':1,'kind':'workspace_dlp_scope_evidence','verified_at':google_drive.utc_now(),
               'rule_scope_checks':[{'rule_id':'rule-test','active':True,'service':'drive','matches':True,
                 'target_kind':target_kind,'target_id':creator if target_kind=='user' else shared_drive_id,
                 'scope_kind':'org_unit','scope_id':'synthetic-ou','basis':'合成した管理者読戻し証跡。実製品の検証ではない。'}]}
        evidence=Path(temp)/'scope-readback.json';evidence.write_text(json.dumps(proof))
        config={'schema_version':1,'creator_email':creator,'drive_kind':drive_kind,'parent_id':parent,'rule_ids':['rule-test'],
                'scope_readback':{'path':evidence.name,'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}}
        if drive_kind=='shared_drive':config['shared_drive_id']=shared_drive_id
        path=Path(temp)/'scope.json';path.write_text(json.dumps(config));return path

    def run_fixture(self,temp,drive=None,sheets=None):
        root=self.make_dataset(temp);drive=drive or FakeDrive();sheets=sheets or FakeSheets(drive);report=Path(temp)/'report.json'
        scope=self.scope(temp,drive_kind='shared_drive' if drive.shared_drive_id else 'my_drive',creator=drive.email,shared_drive_id=drive.shared_drive_id)
        with self.api(drive,sheets):google_drive.execute(root,'test-parent',report,reader='reader@example.test',scope_evidence=scope)
        return drive,sheets,report,scope

    def test_private_import_and_permission_removal(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp)
            result=json.loads(report.read_text());self.assertEqual(len(result['sheets']),4)
            self.assertIn('root_creation',result)
            self.assertTrue(all(r['create_observation']['server_created_at']==r['createdTime'] for r in result['sheets']))
            self.assertTrue(all(r['import_values_verified'] for r in result['sheets']));self.assertEqual(len(drive.permissions_log),4)
            self.assertFalse(drive.revoked);self.assertFalse(result['dlp_remediation_verified'])
            self.assertEqual(result['permission_test_kind'],'owner_managed_permission_lifecycle')
            with self.api(drive,sheets):
                granted=google_drive.advance_permissions(report,'verify-granted',Path(temp)/'reader.json')
                self.assertTrue(all(r['granted_read_verified'] for r in granted['sheets']))
                self.assertTrue(all(r['access_observations'][-1]['http_status']==200 for r in granted['sheets']))
                google_drive.advance_permissions(report,'revoke')
                final=google_drive.advance_permissions(report,'verify-revoked',Path(temp)/'reader.json')
            self.assertTrue(all(r['revoked_read_denied_verified'] for r in final['sheets']));self.assertEqual(len(drive.permissions_log),8)
            sample=final['sheets'][0]['access_observations'][-1]
            self.assertEqual(sample['outcome'],'denied');self.assertTrue(sample['same_revision_during_probe'])
            self.assertEqual(sample['http_status'],403);self.assertEqual(sample['denial_reason'],'forbidden_permission')
            self.assertEqual(sample['dlp_causality'],'not_established');self.assertFalse(sample['permission_mutation_by_probe'])
            self.assertFalse(any(call['body'].get('type')=='anyone' for call in drive.created))
            self.assertEqual(report.stat().st_mode & 0o777,0o600)

    def test_missing_import_value_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive();sheets=FakeSheets(drive,missing=True)
            with self.api(drive,sheets):
                with self.assertRaisesRegex(ValueError,'欠落'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp))

    def test_no_scope_stops_before_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive()
            with self.api(drive,FakeSheets(drive)):
                with self.assertRaisesRegex(ValueError,'scope-evidence'):google_drive.execute(root,'test-parent',Path(temp)/'report.json')
            self.assertFalse(drive.created)

    def test_creator_mismatch_stops_before_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive(email='other@example.test')
            with self.api(drive,FakeSheets(drive)):
                with self.assertRaisesRegex(ValueError,'実主体'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp))
            self.assertFalse(drive.created)

    def test_direct_service_account_my_drive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);email='robot@synthetic.iam.gserviceaccount.com';drive=FakeDrive(email=email)
            with self.api(drive,FakeSheets(drive),credentials=SimpleNamespace(service_account_email=email,_subject=None)):
                with self.assertRaisesRegex(ValueError,'サービスアカウント'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp,creator=email))
            self.assertFalse(drive.created)

    def test_parent_owner_is_not_assumed_from_actor(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive();drive.metadata['test-parent']['owners']=[{'emailAddress':'other@example.test'}]
            with self.api(drive,FakeSheets(drive)):
                with self.assertRaisesRegex(ValueError,'所有者'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp))
            self.assertFalse(drive.created)

    def test_delegated_subject_must_match_actual_actor(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive()
            credentials=SimpleNamespace(service_account_email='robot@synthetic.iam.gserviceaccount.com',_subject='other@example.test')
            with self.api(drive,FakeSheets(drive),credentials=credentials):
                with self.assertRaisesRegex(ValueError,'subject'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp))
            self.assertFalse(drive.created)

    def test_delegated_workspace_user_can_own_my_drive_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive()
            credentials=SimpleNamespace(service_account_email='robot@synthetic.iam.gserviceaccount.com',_subject='owner@example.test')
            with self.api(drive,FakeSheets(drive),credentials=credentials):
                result=google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp))
            self.assertEqual(result['preflight']['delegated_subject'],'owner@example.test')

    def test_shared_drive_requires_drive_scope_not_creator_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive(shared_drive_id='shared-test')
            scope=self.scope(temp,drive_kind='shared_drive',target_kind='user')
            with self.api(drive,FakeSheets(drive)):
                with self.assertRaisesRegex(ValueError,'適用主体'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=scope)
            self.assertFalse(drive.created)

    def test_shared_drive_mismatch_stops_before_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);drive=FakeDrive(shared_drive_id='other-shared')
            with self.api(drive,FakeSheets(drive)):
                with self.assertRaisesRegex(ValueError,'共有ドライブID'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp,drive_kind='shared_drive'))
            self.assertFalse(drive.created)

    def test_shared_drive_scope_ids_are_case_sensitive(self):
        with tempfile.TemporaryDirectory() as temp:
            scope=self.scope(temp,drive_kind='shared_drive',shared_drive_id='shared-test')
            config=json.loads(scope.read_text());config['shared_drive_id']='SHARED-TEST';scope.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'適用主体'):google_drive.scope_configuration(scope)

    def test_shared_drive_has_no_individual_owner_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            drive=FakeDrive(shared_drive_id='shared-test');drive,sheets,report,scope=self.run_fixture(temp,drive=drive)
            result=json.loads(report.read_text());self.assertEqual(result['preflight']['drive_kind'],'shared_drive')
            self.assertTrue(all(r['driveId']=='shared-test' and 'owners' not in r for r in result['sheets']))

    def test_readback_hash_is_checked_before_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);scope=self.scope(temp);(Path(temp)/'scope-readback.json').write_text('{}');drive=FakeDrive()
            with self.api(drive,FakeSheets(drive)):
                with self.assertRaisesRegex(ValueError,'SHA-256'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=scope)
            self.assertFalse(drive.created)

    def test_stale_scope_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            scope=self.scope(temp);proof=Path(temp)/'scope-readback.json';obj=json.loads(proof.read_text());obj['verified_at']=(datetime.now(timezone.utc)-timedelta(hours=73)).isoformat();proof.write_text(json.dumps(obj));config=json.loads(scope.read_text());config['scope_readback']['sha256']=hashlib.sha256(proof.read_bytes()).hexdigest();scope.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'72時間'):google_drive.scope_configuration(scope)

    def test_changed_scope_cannot_authorize_later_revoke(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp);config=json.loads(scope.read_text());config['extra']='changed';scope.write_text(json.dumps(config));before=len(drive.permissions_log)
            with self.api(drive,sheets):
                with self.assertRaisesRegex(ValueError,'証跡が変わ'):google_drive.advance_permissions(report,'revoke')
            self.assertEqual(len(drive.permissions_log),before)

    def test_foreign_run_cannot_authorize_revoke(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp);drive.metadata['file-0']['appProperties']={'pii_dlp_run':'another-run'};before=len(drive.permissions_log)
            with self.api(drive,sheets):
                with self.assertRaisesRegex(ValueError,'結び付け'):google_drive.advance_permissions(report,'revoke')
            self.assertEqual(len(drive.permissions_log),before)

    def test_reader_must_be_distinct_from_owner(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp)
            with self.api(drive,sheets,reader_email='owner@example.test'):
                with self.assertRaisesRegex(ValueError,'別主体'):google_drive.advance_permissions(report,'observe-access',Path(temp)/'reader.json')

    def test_api_disabled_is_not_revocation_success(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp)
            with self.api(drive,sheets):
                google_drive.advance_permissions(report,'verify-granted',Path(temp)/'reader.json');google_drive.advance_permissions(report,'revoke')
                with patch.object(sheets,'get',side_effect=http_error(403,'accessNotConfigured')):
                    with self.assertRaisesRegex(ValueError,'未確認'):google_drive.advance_permissions(report,'verify-revoked',Path(temp)/'reader.json')
            rows=json.loads(report.read_text())['sheets'];self.assertFalse(any(r.get('revoked_read_denied_verified') for r in rows));self.assertEqual(rows[0]['access_observations'][-1]['outcome'],'error')

    def test_404_is_denied_observation_not_dlp_attribution(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp);before=len(drive.permissions_log)
            with self.api(drive,sheets),patch.object(sheets,'get',side_effect=http_error(404)):
                result=google_drive.advance_permissions(report,'observe-access',Path(temp)/'reader.json')
            observed=result['sheets'][0]['access_observations'][-1]
            self.assertEqual(observed['outcome'],'denied');self.assertEqual(observed['dlp_causality'],'not_established');self.assertEqual(len(drive.permissions_log),before)
            self.assertEqual(observed['http_status'],404);self.assertEqual(observed['denial_reason'],'notFound')

    def test_readable_after_revoke_is_not_success(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp);sheets.allow_after_revoke=True
            with self.api(drive,sheets):
                google_drive.advance_permissions(report,'revoke')
                with self.assertRaisesRegex(ValueError,'取消後も読取'):google_drive.advance_permissions(report,'verify-revoked',Path(temp)/'reader.json')
            self.assertFalse(any(r.get('revoked_read_denied_verified') for r in json.loads(report.read_text())['sheets']))

    def test_revision_change_is_unverified(self):
        with tempfile.TemporaryDirectory() as temp:
            drive,sheets,report,scope=self.run_fixture(temp);original=sheets.get
            def changed(spreadsheetId,**kw):
                drive.metadata[spreadsheetId]['version']='2';return original(spreadsheetId,**kw)
            with self.api(drive,sheets),patch.object(sheets,'get',side_effect=changed):result=google_drive.advance_permissions(report,'observe-access',Path(temp)/'reader.json')
            self.assertTrue(all(r['access_observations'][-1]['outcome']=='unverified' for r in result['sheets']))

    def test_permission_snapshot_collects_all_pages(self):
        drive=FakeDrive()
        with patch.object(drive,'list',side_effect=[Request({'permissions':[{'id':'one'}],'nextPageToken':'next'}),Request({'permissions':[{'id':'two'}]})]) as call:
            result=google_drive.permission_snapshot(drive,'file-test')
        self.assertEqual([p['id'] for p in result['permissions']],['one','two']);self.assertTrue(result['complete']);self.assertEqual(call.call_args_list[1].kwargs['pageToken'],'next')

    def test_permission_page_cycle_is_not_complete(self):
        drive=FakeDrive()
        with patch.object(drive,'list',return_value=Request({'permissions':[],'nextPageToken':'loop'})):
            with self.assertRaisesRegex(ValueError,'循環'):google_drive.permission_snapshot(drive,'file-test')

    def test_scope_evidence_is_not_uploaded_as_test_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);scope=self.scope(temp);target=root/'drive_upload/scope.json'
            config=json.loads(scope.read_text());config['scope_readback']['path']=str(Path(temp)/'scope-readback.json');target.write_text(json.dumps(config));drive=FakeDrive()
            with self.api(drive,FakeSheets(drive)):
                with self.assertRaisesRegex(ValueError,'アップロード対象'):google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=target)
            self.assertFalse(drive.created)

    def test_creation_interval_is_distinct_from_server_time(self):
        drive=FakeDrive()
        with patch.object(google_drive,'utc_now',side_effect=['2025-12-31T23:59:59Z','2026-01-01T00:00:01Z']):
            created,observed=google_drive.create_file_observed(drive,body={'name':'synthetic','mimeType':google_drive.MIME_FOLDER},fields=google_drive.FILE_FIELDS)
        self.assertEqual(observed['request_started_at'],'2025-12-31T23:59:59Z')
        self.assertEqual(observed['response_completed_at'],'2026-01-01T00:00:01Z')
        self.assertEqual(observed['server_created_at'],'2026-01-01T00:00:00Z')
        self.assertEqual(created['createdTime'],observed['server_created_at'])
        self.assertFalse(observed['single_trigger_time_inferred'])
        self.assertFalse(observed['server_client_clock_alignment_verified'])

    def test_missing_server_creation_time_is_not_invented(self):
        drive=FakeDrive()
        with patch.object(drive,'create',return_value=Request({'id':'synthetic-created'})):
            _,observed=google_drive.create_file_observed(drive,body={'name':'synthetic'},fields=google_drive.FILE_FIELDS)
        self.assertIsNone(observed['server_created_at'])
        self.assertFalse(observed['single_trigger_time_inferred'])

    def test_every_uploaded_item_has_creation_observation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=self.make_dataset(temp);(root/'drive_upload/empty').mkdir();drive=FakeDrive();sheets=FakeSheets(drive)
            with self.api(drive,sheets):
                result=google_drive.execute(root,'test-parent',Path(temp)/'report.json',scope_evidence=self.scope(temp),upload_all=True)
            records=result['sheets']+result['uploads']+result['folders']
            self.assertEqual(len(records)+1,len(drive.created))
            self.assertEqual(len(result['uploads']),4)
            self.assertTrue(any(item['path']=='empty' for item in result['folders']))
            for record in records:
                observation=record['create_observation']
                self.assertLessEqual(datetime.fromisoformat(observation['request_started_at']),datetime.fromisoformat(observation['response_completed_at']))
                self.assertEqual(observation['server_created_at'],record['createdTime'])

    def test_public_report_path_is_rejected_before_api_use(self):
        with self.assertRaisesRegex(ValueError,'公開リポジトリ'):google_drive.execute(Path('/not-used'), 'root',google_drive.REPOSITORY/'not-written.json')


if __name__=='__main__':unittest.main()
