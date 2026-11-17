#!/usr/bin/env python3
"""v3のTXTだけを新規試験フォルダーへ作成。既定は計画表示で通信しない。"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from common import digest, input_file, now, private_path, write_private
from evaluation import load_truth


def drive_support():
    source = HERE.parent.parent / 'pii_image_dataset' / 'google_drive.py'
    spec = importlib.util.spec_from_file_location('v3_drive_support', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plan(dataset):
    rows, source = load_truth(dataset)
    files = [row['file'] for row in rows]
    if len(files) != len(set(files)) or any(Path(name).name != name or not name.endswith('.txt') for name in files):
        raise ValueError('重複しない直下のTXTだけをアップロードします')
    return {'schema_version': 1, 'version': 'v3-extended', 'truth_sha256': digest(source),
            'file_count': len(rows), 'new_folder': True, 'network_executed': False,
            'files': [{'case_id': row['case_id'], 'file': row['file'], 'sha256': row['sha256']}
                      for row in rows],
            'excluded': ['ground_truth.json', 'generation.json', '規則計画', '既存資料', '共有権限の変更'],
            'requires': ['所有者と適用範囲の確認証跡', '明示された親フォルダー', '非公開の新規実行報告']}


def validate_output(dataset, output):
    output = private_path(output)
    if output.is_relative_to(Path(dataset).resolve()):
        raise ValueError('実行報告はデータセットの外へ保存してください')
    if output.exists():
        raise ValueError('既存の実行報告は上書きしません。再試行による二重作成は自動で行いません')
    return output


def execute(dataset, parent, output, scope_evidence, drive, credentials, media_factory,
            *, pre_activation_placement=False):
    """クライアントを注入して試験する。作成以外の変更APIは呼ばない。"""
    description = plan(dataset)
    output = validate_output(dataset, output)
    support = drive_support()
    # 古い証跡、所有範囲不一致等を最初の通信より前に検証する。
    config, binding = support.scope_configuration(scope_evidence, allow_inactive_rules=pre_activation_placement)
    if config['parent_id'] != parent:
        raise ValueError('親フォルダーと適用範囲証跡が一致しません')
    upload_root = (Path(dataset) / 'drive_upload').resolve()
    if any(Path(binding[key]).resolve().is_relative_to(upload_root) for key in ('path', 'readback_path')):
        raise ValueError('適用範囲の証跡はアップロード対象の外へ保存してください')
    result = {'schema_version': 1, 'kind': 'v3_upload', 'run_id': uuid.uuid4().hex,
              'truth_sha256': description['truth_sha256'], 'phase': 'preflight',
              'started_at': now(), 'uploads': [], 'inflight': None,
              'network_executed': False, 'complete': False,
              'pre_activation_placement': pre_activation_placement,
              'rule_activation': {'basis': '保存された適用範囲証跡。現在のPolicyの独立確認ではない。',
                                  'all_rules_active': binding.get('all_rules_active', True),
                                  'rule_states': binding.get('rule_states', [
                                      {'rule_id': ident, 'active': True} for ident in binding['rule_ids']]),
                                  'activation_performed': False},
              'limit': '作成・所有範囲・内容の確認記録。DLP検査完了や検知結果ではない。'}
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    def checkpoint():
        write_private(output, result)
    def create(body, media=None):
        result['inflight'] = {'name': body['name'], 'started_at': now(),
                              'outcome': 'unknown_until_response'}
        checkpoint()
        args = {'body': body, 'fields': support.FILE_FIELDS, 'supportsAllDrives': True}
        if media is not None:
            args['media_body'] = media
        created, timing = support.create_file_observed(drive, **args)
        # 応答を検証する前にIDを保存。検証失敗でも作成済み資料を見失わない。
        result['inflight'].update(response=created, timing=timing)
        checkpoint()
        return created, timing
    def check_created(created, expected_parent, mime):
        support.check_file_scope(created, config, result['preflight']['creator_email'])
        if (not created.get('id') or created.get('mimeType') != mime
                or created.get('parents') != [expected_parent]
                or created.get('appProperties', {}).get('pii_dlp_run') != result['run_id']):
            raise ValueError('作成した資料の種類・親・試験IDを確認できません')
    try:
        result['network_executed'] = True
        result['preflight'] = support.preflight(drive, credentials, parent, scope_evidence,
                                               allow_inactive_rules=pre_activation_placement)
        # 事前確認と保存設定の間に変更があった場合にも停止する。
        if result['preflight']['binding'] != binding:
            raise ValueError('適用範囲証跡が途中で変更されました')
        checkpoint()
        folder, timing = create({'name': 'DLP-v3-test-' + result['run_id'],
                                 'mimeType': support.MIME_FOLDER, 'parents': [parent],
                                 'appProperties': {'pii_dlp_run': result['run_id']}})
        result.update(folder=folder, folder_creation=timing)
        check_created(folder, parent, support.MIME_FOLDER)
        result.update(phase='upload', inflight=None)
        checkpoint()
        for row in description['files']:
            # 検証済みバイト列をそのまま送る。読取り後のパスの差替えを送信へ反映しない。
            payload = input_file(dataset, row['file']).read_bytes()
            if hashlib.sha256(payload).hexdigest() != row['sha256']:
                raise ValueError('計画後にアップロード資料が変更されました')
            media = media_factory(io.BytesIO(payload), mimetype='text/plain', resumable=False)
            created, timing = create({'name': row['file'], 'mimeType': 'text/plain',
                                      'parents': [folder['id']],
                                      'appProperties': {'pii_dlp_run': result['run_id'],
                                                        'dlp_case_id': row['case_id']}}, media)
            record = dict(row, metadata=created, create_observation=timing,
                          content_verified=False)
            result['uploads'].append(record)
            checkpoint()
            check_created(created, folder['id'], 'text/plain')
            expected_md5 = hashlib.md5(payload, usedforsecurity=False).hexdigest()
            if (created.get('md5Checksum') != expected_md5 or
                    created.get('appProperties', {}).get('dlp_case_id') != row['case_id']):
                raise ValueError('作成したTXTの内容または資料IDが一致しません')
            record['content_verified'] = True
            result['inflight'] = None
            checkpoint()
        result.update(phase='complete', complete=True, completed_at=now())
        checkpoint()
        return result
    except Exception as exc:
        result.update(phase='failed', error_type=type(exc).__name__, failed_at=now())
        checkpoint()
        raise RuntimeError('作成を停止しました。非公開の実行報告を確認してください。自動再試行はしません') from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--parent')
    parser.add_argument('--scope-evidence', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--pre-activation-placement', action='store_true',
                        help='有効化前の配置として、証跡にactive=falseと記録された規則を許可する。有効化や検査完了を示さない。')
    args = parser.parse_args(argv)
    description = plan(args.dataset)
    description['pre_activation_placement'] = args.pre_activation_placement
    if not args.execute:
        print(json.dumps(description, ensure_ascii=False, indent=2))
        return
    if not args.parent or not args.scope_evidence or not args.output:
        parser.error('--executeには--parent・--scope-evidence・--outputが必要です')
    validate_output(args.dataset, args.output)
    config, _ = drive_support().scope_configuration(args.scope_evidence,
                                                   allow_inactive_rules=args.pre_activation_placement)
    if config['parent_id'] != args.parent:
        raise ValueError('親フォルダーが適用範囲証跡と一致しません')
    import google.auth
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
    execute(args.dataset, args.parent, args.output, args.scope_evidence,
            build('drive', 'v3', credentials=credentials, cache_discovery=False),
            credentials, MediaIoBaseUpload, pre_activation_placement=args.pre_activation_placement)


if __name__ == '__main__':
    main()
