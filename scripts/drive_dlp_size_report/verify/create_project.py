"""スプレッドシートとコンテナバインドの Apps Script を作り(初回のみ)、src/ のコードを送る。
事前に https://script.google.com/home/usersettings で Apps Script API をオンにし、
OAuth クライアントの Cloud プロジェクトで Apps Script API を有効にしておく。"""
import os
from common import call, load, save

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
ids = load('ids.json', {})
if not ids.get('ss'):
    ss = call('POST', 'https://sheets.googleapis.com/v4/spreadsheets', {
        'properties': {'title': 'DLP×サイズ抽出 動作確認', 'locale': 'ja_JP', 'timeZone': 'Asia/Tokyo'}})
    ids.update(ss=ss['spreadsheetId'], url=ss['spreadsheetUrl'])
if not ids.get('script'):
    p = call('POST', 'https://script.googleapis.com/v1/projects', {'title': 'DLPサイズ抽出', 'parentId': ids['ss']})
    if 'scriptId' not in p:
        raise SystemExit(p)
    ids['script'] = p['scriptId']
save('ids.json', ids)
files = [{'name': 'appsscript', 'type': 'JSON', 'source': open(os.path.join(SRC, 'appsscript.json')).read()},
         {'name': 'Code', 'type': 'SERVER_JS', 'source': open(os.path.join(SRC, 'Code.js')).read()}]
r = call('PUT', f"https://script.googleapis.com/v1/projects/{ids['script']}/content", {'files': files})
print('push', r.get('_error') or 'ok', ids['url'])
print('次に Apps Script エディタで setup を一度実行し、権限を承認する')
