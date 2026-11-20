"""架空の試験ファイルを Drive に配置する。使い方: python3 upload.py 1 (第1陣) / 2 (第2陣)"""
import sys, uuid, json
from common import call, load, save

MARK = 'DLPSIZEMARKQZRT'
CARD = 'クレジットカード番号: 4111 1111 1111 1111 有効期限 12/29'   # 公開されている試験用番号
SECRET = '【社外秘】'
EMAIL = '連絡先メールアドレス: taro.yamada@example.co.jp'
WORD = '【取扱注意】'
FILL = 'これはDLPとファイルサイズの組合せ抽出を確認するための埋め草の文章です。個人情報は含みません。\n'.encode()
SPECS = {
    '1': [('A_card_secret_big', [MARK, SECRET, CARD], 2_000_000, 'expect'),
          ('A_card_secret_small', [MARK, SECRET, CARD], 8_000, 'below_size'),
          ('A_card_only_big', [MARK, CARD], 2_000_000, 'no_rule(AND不成立)'),
          ('B_email_big', [MARK, EMAIL], 1_500_000, 'expect'),
          ('B_word_big', [MARK, WORD], 1_200_000, 'expect(OR)'),
          ('B_email_small', [MARK, EMAIL], 6_000, 'below_size'),
          ('AB_all_big', [MARK, SECRET, CARD, EMAIL], 3_000_000, 'expect(両規則)'),
          ('N_plain_big', [MARK], 2_000_000, 'no_rule'),
          ('X_nomarker_big', [SECRET, CARD, EMAIL], 2_000_000, 'no_rule(対照語なし)')],
    '2': [('A2_card_secret_big', [MARK, SECRET, CARD], 1_100_000, 'expect'),
          ('B2_email_small', [MARK, EMAIL], 5_000, 'below_size'),
          ('AB2_all_big', [MARK, SECRET, CARD, EMAIL], 1_050_000, 'expect(両規則)')]}

ids = load('ids.json', {})
if not ids.get('folder'):
    ids['folder'] = call('POST', 'https://www.googleapis.com/drive/v3/files', {
        'name': 'DLP×サイズ抽出 試験', 'mimeType': 'application/vnd.google-apps.folder'})['id']
    save('ids.json', ids)
log = load('uploads.json', [])
for name, parts, size, exp in SPECS[sys.argv[1]]:
    head = ('\n'.join(parts) + '\n').encode()
    data = head + FILL * max(0, (size - len(head)) // len(FILL))
    bd = 'b' + uuid.uuid4().hex
    meta = json.dumps({'name': name + '.txt', 'parents': [ids['folder']], 'mimeType': 'text/plain'})
    payload = (f'--{bd}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n--{bd}\r\n'
               'Content-Type: text/plain; charset=UTF-8\r\n\r\n').encode() + data + f'\r\n--{bd}--'.encode()
    r = call('POST', 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,size',
             payload, ctype='multipart/related; boundary=' + bd)
    print(r.get('name'), r.get('size'))
    log.append({'batch': sys.argv[1], 'name': r.get('name'), 'id': r.get('id'), 'size': int(r.get('size', 0)), 'expect': exp})
save('uploads.json', log)
