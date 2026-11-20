"""シートの内容を期待値(uploads.json)と照合する。--json で観測をファイルに保存。"""
import json, sys, time, urllib.parse
from common import call, load, save

ids = load('ids.json'); up = {u['id']: u for u in load('uploads.json', [])}


def sheet(name):
    return call('GET', f"https://sheets.googleapis.com/v4/spreadsheets/{ids['ss']}/values/{urllib.parse.quote(name)}").get('values', [])


res, failed, log, partial = sheet('検知結果'), sheet('取得失敗'), sheet('実行履歴'), sheet('_部分一致')
got = [r[2] for r in res[1:] if len(r) > 2]
exp = {i for i, u in up.items() if u['expect'].startswith('expect')}
summary = {'results': [{'name': r[3], 'size': r[4], 'rules': r[8].split('\n')} for r in res[1:] if len(r) > 8],
           'match_expected_or_mode': set(got) == exp,
           'extra': [up.get(i, {}).get('name', i) for i in set(got) - exp],
           'missing': [up[i]['name'] for i in exp - set(got)],
           'duplicates': len(got) - len(set(got)), 'failed': failed[1:], 'partial_rows': len(partial) - 1 if partial else 0,
           'run_log': log}
print(json.dumps(summary, ensure_ascii=False, indent=1))
if '--json' in sys.argv:
    save(f"observation_{time.strftime('%Y%m%dT%H%M%S')}.json", summary)
