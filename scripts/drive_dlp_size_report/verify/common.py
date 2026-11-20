"""検証スクリプトの共通処理。トークン・ID・観測結果はリポジトリ外の DLPSIZE_STATE_DIR に置く。"""
import json, os, time, urllib.error, urllib.parse, urllib.request

STATE = os.environ.get('DLPSIZE_STATE_DIR')
if not STATE:
    raise SystemExit('DLPSIZE_STATE_DIR(リポジトリ外の保存先)を指定してください')
os.makedirs(STATE, exist_ok=True)


def path(name):
    return os.path.join(STATE, name)


def client():
    p = os.environ.get('DLPSIZE_OAUTH_CLIENT')
    if not p:
        raise SystemExit('DLPSIZE_OAUTH_CLIENT(デスクトップ型 OAuth クライアントの JSON)を指定してください')
    return json.load(open(os.path.expanduser(p)))['installed']


def load(name, default=None):
    return json.load(open(path(name))) if os.path.exists(path(name)) else default


def save(name, obj, private=False):
    fd = os.open(path(name), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if private else 0o644)
    os.write(fd, json.dumps(obj, ensure_ascii=False, indent=1).encode()); os.close(fd)


def access_token():
    t = load('token.json')
    if not t:
        raise SystemExit('先に oauth_flow.py で認証してください')
    if t.get('_exp', 0) > time.time() + 60:
        return t['access_token']
    if '_exp' in t:
        c = client()
        r = json.load(urllib.request.urlopen(c['token_uri'], urllib.parse.urlencode(dict(
            client_id=c['client_id'], client_secret=c['client_secret'],
            refresh_token=t['refresh_token'], grant_type='refresh_token')).encode()))
        t['access_token'] = r['access_token']; t['_exp'] = time.time() + r['expires_in']
    else:
        t['_exp'] = time.time() + t['expires_in']
    save('token.json', t, private=True)
    return t['access_token']


def call(method, url, body=None, ctype='application/json'):
    data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={'Authorization': 'Bearer ' + access_token(), 'Content-Type': ctype})
    try:
        b = urllib.request.urlopen(req, timeout=400).read()
        return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {'_error': e.code, '_body': e.read().decode()[:2000]}
