"""検知結果・取得失敗・_部分一致 の各シートの2行目以降を消す(実行履歴は残す)。"""
import urllib.parse
from common import call, load

ids = load('ids.json')
for n in ['検知結果!A2:Z', '取得失敗!A2:Z', '_部分一致!A2:Z']:
    call('POST', f"https://sheets.googleapis.com/v4/spreadsheets/{ids['ss']}/values/{urllib.parse.quote(n)}:clear", {})
print('cleared')
