"""管理者アカウントでループバック OAuth を行い、DLPSIZE_STATE_DIR/token.json に保存する。
使い方: python3 oauth_flow.py <ログインするメールアドレス>  → 表示された URL をブラウザで開いて同意する。"""
import base64, hashlib, http.server, json, secrets, sys, urllib.parse, urllib.request
from common import client, save, path

c = client()
SCOPES = ' '.join('https://www.googleapis.com/auth/' + s for s in [
    'drive', 'spreadsheets', 'script.projects', 'script.deployments', 'script.processes', 'script.scriptapp',
    'admin.reports.audit.readonly', 'cloud-identity.policies', 'admin.directory.orgunit.readonly',
    'admin.directory.customer.readonly', 'userinfo.email']) + ' openid'
PORT = 8765; redirect = f'http://localhost:{PORT}'
ver = secrets.token_urlsafe(64)
chal = base64.urlsafe_b64encode(hashlib.sha256(ver.encode()).digest()).rstrip(b'=').decode()
state = secrets.token_urlsafe(16)
url = c['auth_uri'] + '?' + urllib.parse.urlencode(dict(
    client_id=c['client_id'], redirect_uri=redirect, response_type='code', scope=SCOPES, access_type='offline',
    prompt='consent', login_hint=sys.argv[1] if len(sys.argv) > 1 else '', code_challenge=chal,
    code_challenge_method='S256', state=state))
print(url, flush=True)


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(s.path).query)
        if 'code' not in q or q.get('state', [''])[0] != state:
            s.send_response(400); s.end_headers(); return
        tok = json.load(urllib.request.urlopen(c['token_uri'], urllib.parse.urlencode(dict(
            code=q['code'][0], client_id=c['client_id'], client_secret=c['client_secret'], redirect_uri=redirect,
            grant_type='authorization_code', code_verifier=ver)).encode()))
        save('token.json', tok, private=True)
        s.send_response(200); s.end_headers(); s.wfile.write(b'OK: authorization complete.')
        print('saved', path('token.json'), flush=True); s.server.done = True


srv = http.server.HTTPServer(('127.0.0.1', PORT), H); srv.done = False
while not srv.done:
    srv.handle_request()
