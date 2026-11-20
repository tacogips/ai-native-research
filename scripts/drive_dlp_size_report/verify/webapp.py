"""HEAD 配置(/dev)の Web アプリを OAuth トークン付きで呼ぶ。
例: python3 webapp.py action=setup / action=run / action=status / action=reset
    python3 webapp.py action=config MIN_SIZE_BYTES=1000000 "RULE_NAMES=規則1,規則2" """
import sys, urllib.error, urllib.parse, urllib.request
from common import access_token, call, load, save

ids = load('ids.json')
if not ids.get('head'):
    d = call('GET', f"https://script.googleapis.com/v1/projects/{ids['script']}/deployments")
    ids['head'] = [x['deploymentId'] for x in d['deployments'] if not x['deploymentConfig'].get('versionNumber')][0]
    save('ids.json', ids)
q = dict(a.split('=', 1) for a in sys.argv[1:])
url = f"https://script.google.com/macros/s/{ids['head']}/dev?" + urllib.parse.urlencode(q)
try:
    print(urllib.request.urlopen(urllib.request.Request(url, headers={'Authorization': 'Bearer ' + access_token()}),
                                 timeout=400).read().decode())
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:1500])
