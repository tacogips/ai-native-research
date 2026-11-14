# coding: utf-8
"""保存原本の一致と今回の調査稿の参照を検証する。保護機構の実機試験ではない。"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'research/technology'

def nodes(value, base=None, repo_url=None, commit=None):
    if isinstance(value, dict):
        candidate = value.get('local_checkout', value.get('local_directory', value.get('local_file')))
        if candidate and (ROOT / candidate).is_dir():
            base = candidate
            repo_url = value.get('url', repo_url)
            commit = value.get('commit', commit)
        node = dict(value)
        if node.get('path') and node.get('sha256') and not node.get('local_file') and base:
            node['local_file'] = str(Path(base) / node['path'])
            if not node.get('url') and repo_url and commit:
                node['url'] = repo_url.removesuffix('.git') + '/blob/' + commit + '/' + node['path']
        yield node
        for child in value.values():
            yield from nodes(child, base, repo_url, commit)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child, base, repo_url, commit)

def main():
    errors, records, urls, failures = [], {}, {}, []
    manifests = sorted(REPORTS.glob('harness_*sources_20261008.json'))
    for manifest in manifests:
        data = json.loads(manifest.read_text())
        for node in nodes(data):
            if node.get('status') in ('failed', '取得失敗', 'error'):
                failures.append({'manifest': manifest.name, 'url': node.get('url', node.get('source_url')), 'status': node['status']})
            if not node.get('local_file') or not node.get('sha256'):
                continue
            file = ROOT / node['local_file']
            if not file.is_file():
                errors.append(f'{manifest.name}: missing {node["local_file"]}')
                continue
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            if digest != node['sha256']:
                errors.append(f'{manifest.name}: hash mismatch {node["local_file"]}')
            records[str(file)] = digest
            for key in ('url', 'source_url', 'resolved_url'):
                if node.get(key):
                    urls[node[key].split('#')[0]] = file
    reports = sorted(REPORTS.glob('harness_*20261008.md')) + [REPORTS / 'ai_harness_privacy_security_master_20261008.md']
    links_count, anchors_count = 0, 0
    for report in reports:
        text = report.read_text()
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            target = target.split('#')[0]
            if target and not (report.parent / target).exists():
                errors.append(f'{report.name}: broken link {target}')
            links_count += 1
        for url, first, last in re.findall(r'(https://github\.com/[^\s)]+?)#L(\d+)(?:-L(\d+))?', text):
            file = urls.get(url)
            if file is None:
                errors.append(f'{report.name}: code citation absent from source manifest {url}')
                continue
            line_count = len(file.read_text().splitlines())
            if not (1 <= int(first) <= int(last or first) <= line_count):
                errors.append(f'{report.name}: invalid line citation {url}#L{first}')
            anchors_count += 1
    result = {
        '確認日': '2026-10-08',
        '確認方法': '一次資料台帳のSHA-256と原本、コード参照の保存対応と行範囲、調査稿の相対参照を検査。主張の意味のレビューと実機試験は別。',
        '台帳数': len(manifests), '重複を除く原本数': len(records),
        '調査・レビュー稿数': len(reports), '相対参照数': links_count,
        'コード行参照数': anchors_count, '台帳に記録した取得失敗': failures,
        '整合エラー': errors, '判定': '合格' if not errors else '要修正',
    }
    output = REPORTS / 'harness_evidence_verification_20261008.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k!='台帳に記録した取得失敗'}, ensure_ascii=False, indent=2))
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
