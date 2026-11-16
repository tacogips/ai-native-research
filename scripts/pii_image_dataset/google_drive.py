#!/usr/bin/env python3
"""指定の試験用Driveへ画像・文書・ネイティブSheetsを配置する。

既定はローカルの作成計画だけを表示。--execute指定時のみ外部作成する。
"""
import argparse
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

MIME_SHEET='application/vnd.google-apps.spreadsheet'
MIME_FOLDER='application/vnd.google-apps.folder'
REPOSITORY=Path(__file__).resolve().parents[2]
FILE_FIELDS='id,mimeType,parents,driveId,owners(emailAddress),capabilities(canAddChildren),trashed,version,createdTime,modifiedTime,headRevisionId,md5Checksum,appProperties'
SCOPE_LIMIT='外部で確認した規則・OU/グループの証跡とDrive実主体/所有範囲の整合を確認する。DirectoryやPolicyの現在状態、製品内部の検査完了を独立に証明するものではない。'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def private_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(descriptor,'w') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
        temporary.replace(path)
    finally:
        if temporary.exists():temporary.unlink()


def outside_repository(path):
    path=Path(path).resolve()
    if path.is_relative_to(REPOSITORY):raise ValueError('識別子・認証・実行証跡は公開リポジトリの外へ置いてください')
    return path


def scope_configuration(path):
    if path is None:raise ValueError('作成前に --scope-evidence で所有者と規則範囲の確認証跡を指定してください')
    path=outside_repository(path);raw=path.read_bytes();config=json.loads(raw)
    if config.get('schema_version')!=1:raise ValueError('scope-evidenceのschema_versionは1が必要です')
    if config.get('drive_kind') not in {'my_drive','shared_drive'}:raise ValueError('my_driveとshared_driveを明示してください')
    if not config.get('creator_email') or not config.get('parent_id'):raise ValueError('作成主体と親IDが必要です')
    if config['drive_kind']=='shared_drive' and not config.get('shared_drive_id'):raise ValueError('共有ドライブ自体のIDが必要です')
    rules=config.get('rule_ids',[])
    if not rules or any(not isinstance(v,str) or not v for v in rules) or len(rules)!=len(set(rules)):raise ValueError('重複のない対象規則IDが必要です')
    reference=config.get('scope_readback',{})
    evidence=outside_repository(path.parent/reference.get('path',''))
    if evidence==path or not evidence.is_file():raise ValueError('別保存した適用範囲証跡のファイルが必要です')
    payload=evidence.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=reference.get('sha256'):raise ValueError('適用範囲証跡のSHA-256が不一致です')
    saved=json.loads(payload)
    if saved.get('schema_version')!=1 or saved.get('kind')!='workspace_dlp_scope_evidence':raise ValueError('適用範囲証跡の形式が違います')
    try:checked=datetime.fromisoformat(saved['verified_at'].replace('Z','+00:00'))
    except (KeyError,ValueError,TypeError):raise ValueError('適用範囲の確認時刻が必要です')
    now=datetime.now(timezone.utc)
    if checked.tzinfo is None or not now-timedelta(hours=72)<=checked<=now+timedelta(minutes=1):raise ValueError('適用範囲は72時間以内に確認した証跡を使ってください')
    target_kind='user' if config['drive_kind']=='my_drive' else 'shared_drive'
    target=config['creator_email'] if target_kind=='user' else config['shared_drive_id']
    checks=saved.get('rule_scope_checks',[])
    if not isinstance(checks,list):raise ValueError('規則ごとの範囲確認が必要です')
    for rule in rules:
        matches=[item for item in checks if item.get('rule_id')==rule]
        if len(matches)!=1:raise ValueError('規則ごとの適用証跡が一意ではありません')
        item=matches[0]
        if item.get('active') is not True or item.get('service')!='drive' or item.get('matches') is not True:raise ValueError('有効なDrive規則の適用範囲一致を確認してください')
        actual_target=item.get('target_id')
        same_target=isinstance(actual_target,str) and (actual_target.casefold()==target.casefold() if target_kind=='user' else actual_target==target)
        if item.get('target_kind')!=target_kind or not same_target:raise ValueError('規則の適用主体が所有者または共有ドライブと違います')
        if item.get('scope_kind') not in {'organization','org_unit','group'} or not item.get('scope_id') or not item.get('basis'):raise ValueError('組織・組織部門・グループのどの読戻しを根拠にしたか必要です')
    return config,{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'readback_path':str(evidence),'readback_sha256':hashlib.sha256(payload).hexdigest(),'verified_at':saved['verified_at'],'rule_ids':rules}


def check_file_scope(metadata,config,identity):
    if metadata.get('trashed') is not False:raise ValueError('資料または親のゴミ箱状態を確認できません')
    if config['drive_kind']=='shared_drive':
        if metadata.get('driveId')!=config['shared_drive_id']:raise ValueError('親または資料の共有ドライブIDが違います')
    else:
        if metadata.get('driveId'):raise ValueError('共有ドライブの資料をマイドライブ試験へ混ぜません')
        owners={str(o.get('emailAddress','')).casefold() for o in metadata.get('owners',[])}
        if owners!={identity.casefold()}:raise ValueError('マイドライブの所有者と作成主体が一致しません')


def create_file_observed(drive,**parameters):
    """要求区間とサーバーの作成時刻を分離し、検査開始の単一点を捏造しない。"""
    started=utc_now()
    created=drive.files().create(**parameters).execute()
    completed=utc_now()
    observation={'kind':'create','request_started_at':started,'response_completed_at':completed,
                 'server_created_at':created.get('createdTime'),'server_modified_at':created.get('modifiedTime'),
                 'single_trigger_time_inferred':False,'server_client_clock_alignment_verified':False}
    return created,observation


def preflight(drive,credentials,parent,scope_evidence):
    config,binding=scope_configuration(scope_evidence)
    if str(parent)!=config['parent_id']:raise ValueError('実行する親IDが確認証跡と違います')
    identity=drive.about().get(fields='user(emailAddress)').execute().get('user',{}).get('emailAddress')
    if not identity or identity.casefold()!=config['creator_email'].casefold():raise ValueError('Drive実主体と指定した作成主体が一致しません')
    service_email=getattr(credentials,'service_account_email',None)
    delegated_subject=getattr(credentials,'_subject',None)
    if delegated_subject and delegated_subject.casefold()!=identity.casefold():raise ValueError('委任subjectとDrive実主体が一致しません')
    if config['drive_kind']=='my_drive' and (identity.casefold().endswith('.gserviceaccount.com') or (service_email and not getattr(credentials,'_subject',None) and identity.casefold()==service_email.casefold())):
        raise ValueError('非委任サービスアカウントのマイドライブ所有を試験しません。組織利用者または共有ドライブを使ってください')
    metadata=drive.files().get(fileId=parent,fields=FILE_FIELDS,supportsAllDrives=True).execute()
    if metadata.get('mimeType')!=MIME_FOLDER or metadata.get('capabilities',{}).get('canAddChildren') is not True:raise ValueError('親フォルダーの種類と追加権限を確認できません')
    if not metadata.get('id'):raise ValueError('親フォルダーの実IDが取得できません')
    check_file_scope(metadata,config,identity)
    return {'checked_at':utc_now(),'creator_email':identity,'credential_service_account_email':service_email,'delegated_subject':delegated_subject,
            'drive_kind':config['drive_kind'],'parent':metadata,'binding':binding,'scope_configuration':config,'scope_proof_limit':SCOPE_LIMIT}


def bound_report_preflight(drive,credentials,report):
    old=report.get('preflight',{});binding=old.get('binding',{})
    if report.get('schema_version')!=2 or not report.get('run_id') or not binding.get('path'):raise ValueError('所有者・範囲・試験IDを結び付けた新形式の報告が必要です')
    current=preflight(drive,credentials,old.get('scope_configuration',{}).get('parent_id'),binding['path'])
    if current['binding']!=binding or current['scope_configuration']!=old.get('scope_configuration'):raise ValueError('作成時から適用範囲証跡が変わりました')
    root=drive.files().get(fileId=report['root_id'],fields=FILE_FIELDS,supportsAllDrives=True).execute()
    check_file_scope(root,current['scope_configuration'],current['creator_email'])
    if root.get('mimeType')!=MIME_FOLDER or root.get('appProperties',{}).get('pii_dlp_run')!=report['run_id'] or current['parent']['id'] not in root.get('parents',[]):raise ValueError('報告と専用フォルダーの結び付けが違います')
    return current


def bound_file(drive,report,record,verified):
    metadata=drive.files().get(fileId=record['id'],fields=FILE_FIELDS,supportsAllDrives=True).execute()
    check_file_scope(metadata,verified['scope_configuration'],verified['creator_email'])
    if report['root_id'] not in metadata.get('parents',[]) or metadata.get('appProperties',{}).get('pii_dlp_run')!=report['run_id']:
        raise ValueError('試験フォルダー外または別試験の資料の権限は変更しません')
    return metadata


def permission_snapshot(drive,file_id):
    rows=[];token=None;seen=set();started=utc_now()
    while True:
        params={'fileId':file_id,'supportsAllDrives':True,'fields':'nextPageToken,permissions(id,type,role,emailAddress,domain,allowFileDiscovery,deleted,permissionDetails)','pageSize':100}
        if token:params['pageToken']=token
        page=drive.permissions().list(**params).execute();rows.extend(page.get('permissions',[]));token=page.get('nextPageToken')
        if not token:return {'complete':True,'permissions':rows,'started_at':started,'finished_at':utc_now()}
        if token in seen:raise ValueError('権限一覧のページが循環しています')
        seen.add(token)


def permission_denial(error):
    if error.resp.status==404:return True
    if error.resp.status!=403:return False
    try:detail=json.loads(error.content)['error']
    except (ValueError,KeyError,TypeError):return False
    reasons={item.get('reason') for item in detail.get('errors',[])}
    reasons.update(item.get('reason') for item in detail.get('details',[]) if item.get('reason'))
    known={'forbidden','insufficientFilePermissions'}
    message=detail.get('message','').strip().rstrip('.').casefold()=='the caller does not have permission'
    return (not reasons or reasons<=known) and (message or reasons=={'insufficientFilePermissions'})


def observe_external_access(owner,reader_sheets,report,record,verified,reader_email,stage):
    """Sheets読取という一経路を観測。DLPの原因特定やdownload禁止の証明はしない。"""
    from googleapiclient.errors import HttpError
    snapshot_started=utc_now();before=bound_file(owner,report,record,verified);before_at=utc_now()
    permissions_before=permission_snapshot(owner,record['id'])
    result={'schema_version':1,'test_kind':'external_access_probe','stage':stage,'file_id':record['id'],'actor_email':reader_email,
            'mechanism':'sheets.spreadsheets.get','started_at':utc_now(),'snapshot_started_at':snapshot_started,
            'owner_before':before,'owner_before_observed_at':before_at,'permissions_before':permissions_before,
            'dlp_causality':'not_established','permission_mutation_by_probe':False}
    text=''
    try:
        data=reader_sheets.spreadsheets().get(spreadsheetId=record['id'],includeGridData=True).execute()
        text='\n'.join(str(c.get('formattedValue','')) for sheet in data.get('sheets',[]) for block in sheet.get('data',[]) for row in block.get('rowData',[]) for c in row.get('values',[]))
        result.update(outcome='readable',http_status=200)
    except HttpError as error:
        denied=permission_denial(error)
        result.update(outcome='denied' if denied else 'error',http_status=error.resp.status)
        if denied:
            if error.resp.status==404:result['denial_reason']='notFound'
            else:
                detail=json.loads(error.content)['error']
                reasons={item.get('reason') for item in detail.get('errors',[])}
                reasons.update(item.get('reason') for item in detail.get('details',[]) if item.get('reason'))
                result['denial_reason']='insufficientFilePermissions' if 'insufficientFilePermissions' in reasons else 'forbidden_permission'
    result['finished_at']=utc_now()
    result['access_started_at']=result['started_at'];result['access_finished_at']=result['finished_at']
    after=bound_file(owner,report,record,verified);result['owner_after']=after;result['owner_after_observed_at']=utc_now()
    result['permissions_after']=permission_snapshot(owner,record['id'])
    result['snapshot_finished_at']=utc_now()
    keys=['version','modifiedTime','headRevisionId','md5Checksum']
    stable=bool(before.get('version')) and all(before.get(k)==after.get(k) for k in keys)
    result['same_revision_during_probe']=stable
    if not stable:result['outcome']='unverified';result['unverified_reason']='観測中の版変更または版の確認不足'
    # 存在/配置は前後で確認したが、この二つの読取と外部読取は不可分な操作ではない。
    result['atomic_snapshot']=False
    return result,text


def build_plan(dataset):
    rows=json.loads((dataset/'ground_truth/files.json').read_text())
    xlsx=[r for r in rows if r['format']=='XLSX' and r['path'].startswith('office/')]
    chosen=[r for r in xlsx if r['positive']][:2]+[r for r in xlsx if not r['positive']][:2]
    if len(chosen)!=4:raise ValueError('Google Sheets用の陽性2・陰性2のXLSXが必要です')
    return {'native_sheets':[{'source':r['path'],'positive':r['positive'],'source_id':r['source_id']} for r in chosen],
            'upload_files':[r['path'] for r in rows],
            'conditions':['通常','非表示シート','保護範囲','指定利用者への読取権限付与・取消'],
            'permission_test_kind':'owner_managed_permission_lifecycle','dlp_remediation_verified':False,
            'requires_environment':['Driveで確認できる実作成主体','所有者または共有ドライブに一致する規則適用範囲の外部確認証跡','外部読取には作成者とは別の試験主体'],
            'optional_environment':['CSE:対応契約・管理者設定・外部鍵基盤・復号後の端末検査経路'],
            'cse_status':'LIGHT対象外の任意試験。通常Sheetsの作成APIで代用しない'}


def execute(dataset,parent,report_path,reader=None,upload_all=False,scope_evidence=None):
    import google.auth
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    dataset=Path(dataset);report_path=outside_repository(report_path)
    if report_path.exists():raise ValueError('実行報告は既存ファイルを上書きしません')
    if report_path.is_relative_to(dataset.resolve()):raise ValueError('実行報告はデータセットの外へ保存してください')
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/spreadsheets'])
    drive=build('drive','v3',credentials=credentials,cache_discovery=False)
    verified=preflight(drive,credentials,parent,scope_evidence)
    for key in ['path','readback_path']:
        if Path(verified['binding'][key]).is_relative_to((dataset/'drive_upload').resolve()):raise ValueError('適用範囲の確認証跡はアップロード対象の外へ置いてください')
    sheets=build('sheets','v4',credentials=credentials,cache_discovery=False)
    plan=build_plan(dataset)
    run_id=uuid.uuid4().hex
    # 親IDを明示し、毎回新規の試験フォルダを作る。他の資料の権限は変更しない。
    created_root,root_creation=create_file_observed(drive,body={'name':'PII検知試験資料','mimeType':MIME_FOLDER,'parents':[parent],'appProperties':{'pii_dlp_run':run_id}},fields=FILE_FIELDS,supportsAllDrives=True)
    folder=created_root['id']
    result={'schema_version':2,'root_id':folder,'root_creation':root_creation,'run_id':run_id,'preflight':verified,'sheets':[],'uploads':[],'folders':[],'cse_status':plan['cse_status'],
            'permission_test_kind':'owner_managed_permission_lifecycle','dlp_remediation_verified':False}
    # 外部状態は非公開の実行報告へ逐次保存。作成済みIDを失って重複作成しない。
    def checkpoint():
        private_json(report_path,result)
    checkpoint()
    check_file_scope(created_root,verified['scope_configuration'],verified['creator_email'])
    if created_root.get('appProperties',{}).get('pii_dlp_run')!=run_id or verified['parent']['id'] not in created_root.get('parents',[]):raise ValueError('作成した専用フォルダーの結び付けが一致しません')
    for item in plan['native_sheets']:
        local=dataset/'drive_upload'/item['source']
        created,creation=create_file_observed(drive,body={'name':item['source_id'],'mimeType':MIME_SHEET,'parents':[folder],'appProperties':{'pii_dlp_run':run_id}},media_body=MediaFileUpload(str(local),mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),fields=FILE_FIELDS+',webViewLink',supportsAllDrives=True)
        record=dict(item,**created,create_observation=creation,conditions=[]);result['sheets'].append(record);checkpoint()
        check_file_scope(created,verified['scope_configuration'],verified['creator_email'])
        if created.get('appProperties',{}).get('pii_dlp_run')!=run_id or folder not in created.get('parents',[]):raise ValueError('作成した資料と専用フォルダーの結び付けが違います')
        sid=created['id']
        metadata=sheets.spreadsheets().get(spreadsheetId=sid,includeGridData=True).execute()
        sheetid=metadata['sheets'][0]['properties']['sheetId']
        retrieved='\n'.join(str(cell.get('formattedValue','')) for sheet in metadata['sheets'] for block in sheet.get('data',[]) for row in block.get('rowData',[]) for cell in row.get('values',[]))
        local_rows=json.loads((dataset/'ground_truth/files.json').read_text())
        gold=next(r for r in local_rows if r['path']==item['source'])
        for entity in gold['entities']:
            if ''.join(entity['value'].split()) not in ''.join(retrieved.split()):raise ValueError('Google Sheets変換時に対象値が欠落')
        record['import_values_verified']=True
        record['expected_values']=[e['value'] for e in gold['entities']]
        sheets.spreadsheets().batchUpdate(spreadsheetId=sid,body={'requests':[
            {'addSheet':{'properties':{'title':'補足','hidden':True}}},
            {'addProtectedRange':{'protectedRange':{'range':{'sheetId':sheetid},'warningOnly':True,'description':'編集時の警告。本文の暗号化ではない'}}}
        ]}).execute()
        record['conditions']+=['XLSXからネイティブ変換','非表示シート','保護範囲の警告']
        # エクスポートは元資料と別の正解を付けるため、アップロード対象の外へ保存。
        exports=report_path.parent/(item['source_id']+'-exports');exports.mkdir(exist_ok=True)
        for ext,mime in [('xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),('ods','application/vnd.oasis.opendocument.spreadsheet'),('pdf','application/pdf'),('csv','text/csv'),('tsv','text/tab-separated-values'),('zip','application/zip')]:
            data=drive.files().export_media(fileId=sid,mimeType=mime).execute();(exports/('document.'+ext)).write_bytes(data)
        # 値の取得を記録するが、元資料への一致は呼出側で検証する。
        record['retrieved_sheet_count']=len(sheets.spreadsheets().get(spreadsheetId=sid).execute()['sheets'])
        if reader:
            permission=drive.permissions().create(fileId=sid,body={'type':'user','role':'reader','emailAddress':reader},sendNotificationEmail=False,fields='id',supportsAllDrives=True).execute()['id']
            record['reader_permission_id']=permission
            record['reader_email']=reader
            record['permission_stage']='付与済み・別主体の読取確認待ち'
            record['conditions'].append('読取権限を付与。permission-stageで読取確認・取消・拒否確認を続ける')
            checkpoint()
        checkpoint()
    if upload_all:
        folders={'':folder}
        root=dataset/'drive_upload'
        # 空ディレクトリも明示作成。
        for local in sorted(root.rglob('*'),key=lambda p:(len(p.parts),str(p))):
            rel=local.relative_to(root)
            parent_id=folders[rel.parent.as_posix() if str(rel.parent)!='.' else '']
            if local.is_dir():
                created,creation=create_file_observed(drive,body={'name':local.name,'mimeType':MIME_FOLDER,'parents':[parent_id],'appProperties':{'pii_dlp_run':run_id}},fields=FILE_FIELDS,supportsAllDrives=True)
                folders[rel.as_posix()]=created['id'];result['folders'].append({'path':rel.as_posix(),**created,'create_observation':creation});checkpoint()
                check_file_scope(created,verified['scope_configuration'],verified['creator_email'])
            else:
                created,creation=create_file_observed(drive,body={'name':local.name,'parents':[parent_id],'appProperties':{'pii_dlp_run':run_id}},media_body=MediaFileUpload(str(local)),fields=FILE_FIELDS,supportsAllDrives=True)
                result['uploads'].append({'path':rel.as_posix(),**created,'create_observation':creation});checkpoint()
                check_file_scope(created,verified['scope_configuration'],verified['creator_email'])
    return result


def advance_permissions(report_path,stage,reader_credentials=None):
    import google.auth
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    if stage not in {'verify-granted','revoke','verify-revoked','observe-access'}:raise ValueError('不明な権限確認の段階です')
    report_path=outside_repository(report_path)
    report=json.loads(report_path.read_text())
    def save_report():
        private_json(report_path,report)
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
    owner=build('drive','v3',credentials=credentials,cache_discovery=False)
    verified=bound_report_preflight(owner,credentials,report)
    records=[r for r in report['sheets'] if r.get('reader_permission_id')]
    if not records:raise ValueError('付与済みの権限試験がありません')
    for r in records:
        bound_file(owner,report,r,verified)
    if stage=='revoke':
        for r in records:
            if not r.get('permission_revoked'):
                try:
                    owner.permissions().delete(fileId=r['id'],permissionId=r['reader_permission_id'],supportsAllDrives=True).execute()
                    r['revoke_outcome']='delete_succeeded'
                except HttpError as error:
                    if error.resp.status!=404:raise
                    r['revoke_outcome']='already_absent_404'
            r['permission_revoked']=True;r['permission_stage']='所有者による取消済み・拒否確認待ち';r['permission_revoked_at']=utc_now();save_report()
    else:
        if reader_credentials is None:raise ValueError('別主体の認証ファイルを指定してください')
        reader_credentials=Path(reader_credentials)
        outside_repository(reader_credentials)
        readonly,_=google.auth.load_credentials_from_file(str(reader_credentials),scopes=['https://www.googleapis.com/auth/drive.readonly','https://www.googleapis.com/auth/spreadsheets.readonly'])
        reader_drive=build('drive','v3',credentials=readonly,cache_discovery=False)
        identity=reader_drive.about().get(fields='user(emailAddress)').execute()['user']['emailAddress']
        if identity.casefold()==verified['creator_email'].casefold():raise ValueError('所有者とは別主体の認証で確認してください')
        reader_sheets=build('sheets','v4',credentials=readonly,cache_discovery=False)
        for r in records:
            if identity.casefold()!=r['reader_email'].casefold():raise ValueError('指定した読取主体と認証の主体が違います')
            if stage=='verify-granted' and r.get('permission_revoked'):raise ValueError('権限はすでに取り消されています')
            if stage=='verify-revoked' and not r.get('permission_revoked'):raise ValueError('先に権限を取り消してください')
            observation,text=observe_external_access(owner,reader_sheets,report,r,verified,identity,stage)
            r.setdefault('access_observations',[]).append(observation);save_report()
            if stage=='observe-access':continue
            if observation['outcome']=='readable':
                if stage=='verify-revoked':raise ValueError('取消後も読取が可能です。継承権限等を確認してください')
                for value in r.get('expected_values',[]):
                    if ''.join(value.split()) not in ''.join(text.split()):raise ValueError('別主体による読取で値が欠落しました')
                r['granted_read_verified']=True;r['permission_stage']='付与中の読取を確認済み'
            elif stage=='verify-revoked' and observation['outcome']=='denied':
                r['revoked_read_denied_verified']=True
                r['permission_stage']='付与中読取と取消後拒否を確認済み' if r.get('granted_read_verified') else '取消後拒否のみ確認済み・付与中読取は未確認'
            else:raise ValueError('読取の期待状態を確認できません。API障害・版変更・原因不明は未確認です')
            save_report()
    save_report()
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path)
    p.add_argument('--parent')
    p.add_argument('--permission-stage',choices=['verify-granted','revoke','verify-revoked','observe-access'])
    p.add_argument('--scope-evidence',type=Path,help='リポジトリ外の所有者・共有ドライブ・規則適用範囲確認JSON。実作成には必須')
    p.add_argument('--reader-credentials',type=Path)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--upload-all',action='store_true')
    p.add_argument('--reader',help='権限試験専用アカウント。既存資料の共有には使わない')
    p.add_argument('--report',type=Path,help='リポジトリと検査対象の外にある新規の実行報告パス')
    a=p.parse_args()
    if a.permission_stage:
        if not a.execute or not a.report:p.error('権限試験の段階実行には--executeと既存の--reportが必要です')
        advance_permissions(a.report,a.permission_stage,a.reader_credentials)
        raise SystemExit(0)
    if a.dataset is None:p.error('--datasetが必要です')
    if not a.execute:print(json.dumps(build_plan(a.dataset),ensure_ascii=False,indent=2))
    else:
        if not a.parent or not a.report:p.error('--executeには--parentと--reportが必要です')
        if a.report.exists():p.error('実行報告は既存ファイルを上書きしません')
        if a.report.resolve().is_relative_to(a.dataset.resolve()):p.error('実行報告はデータセットの外へ保存してください')
        if a.report.resolve().is_relative_to(Path(__file__).resolve().parents[2]):p.error('非公開の実行報告はリポジトリの外へ保存してください')
        if not a.scope_evidence:p.error('--executeには--scope-evidenceが必要です')
        execute(a.dataset,a.parent,a.report,a.reader,a.upload_all,a.scope_evidence)
