/**
 * Drive DLP 検知 × ファイルサイズ 抽出（Google スプレッドシート + Apps Script のみ）
 *
 * 1. Admin SDK Reports API（applicationName=rules）から Drive DLP 規則の内容一致イベントを取得する。
 *    実環境(2026-11)では内容一致は content_matched として記録された(公開文書の一覧は rule_match)。
 *    イベント名は設定 EVENT_NAME で変えられる。
 * 2. 設定シートで指定した規則名に絞り込む。複数規則の AND（すべての規則に一致）も選べる。
 * 3. Drive API(高度なサービスとして有効化し、並列取得は UrlFetchApp.fetchAll)でファイルサイズを取得し、最小サイズ以上のものだけを結果シートへ追記する。
 * 4. 処理済みの期間（透かし）をスクリプトのプロパティに保存し、次回は前回以降の検知だけを処理する。
 *    時間切れのときは Reports API のページ位置を保存し、続きの実行で再開する（数十万件向け）。
 */

var SHEET = {
  CONFIG: '設定',
  RESULT: '検知結果',
  FAILED: '取得失敗',
  PARTIAL: '_部分一致',
  LOG: '実行履歴'
};

var HEADERS = {
  RESULT: ['記録日時', 'DLP検知日時', 'ファイルID', 'ファイル名', 'サイズ(byte)', 'サイズ(MB)', 'MIMEタイプ',
    '所有者', '一致したDLP規則', '規則ID', 'URL'],
  FAILED: ['記録日時', 'DLP検知日時', 'ファイルID', 'ファイル名(監査ログ)', '所有者', '一致したDLP規則', '理由'],
  PARTIAL: ['ファイルID', '一致済みの規則(改行区切り)', '最初の検知日時', '最後の検知日時'],
  LOG: ['開始', '終了', '対象期間の開始', '対象期間の終了', '取得イベント数', '規則に一致', '新規の候補ファイル',
    '追記', 'サイズ未満', '取得失敗', '状態', 'メモ']
};

var DEFAULT_CONFIG = [
  ['MIN_SIZE_BYTES', 1048576, 'この値(byte)以上のファイルだけを記録する。例: 1048576 = 1MB'],
  ['RULE_NAMES', '', '対象とするDLP規則名(表示名)。改行またはカンマ区切り。空なら全てのDrive DLP規則'],
  ['REQUIRE_ALL_RULES', false, 'TRUE: RULE_NAMES のすべての規則に一致したファイルだけ記録(AND)。FALSE: いずれか(OR)'],
  ['INITIAL_LOOKBACK_DAYS', 7, '初回実行時に遡る日数(Reports API の保持期間内)'],
  ['OVERLAP_MINUTES', 180, '監査ログの到着遅延に備え、前回の終了時刻からこの分だけ重ねて再取得する(重複は除外)'],
  ['TRIGGER_INTERVAL_MINUTES', 60, '定期実行の間隔(分)。1,5,10,15,30 または 60の倍数'],
  ['MAX_RUNTIME_SECONDS', 300, '1回の実行で処理する最大秒数。超えたらページ位置を保存して続きの実行へ回す'],
  ['DRIVE_FETCH_BATCH', 50, 'Drive API を並列に呼ぶ件数'],
  ['EVENT_NAME', 'content_matched', 'Reports API rules のイベント名。DLPの内容一致は content_matched']
];

var PROP = {
  WATERMARK: 'DLPSIZE_WATERMARK',          // 処理完了した期間の終了時刻(ISO)
  WINDOW: 'DLPSIZE_WINDOW',                // 処理中の期間 {start,end,pageToken,stats}
  SA_EMAIL: 'DLPSIZE_SA_EMAIL',            // 任意: ドメイン全体の委任を持つサービスアカウント
  SA_KEY: 'DLPSIZE_SA_PRIVATE_KEY'         // 任意: 上記の秘密鍵(PEM)。シートには置かない
};

var CONTINUE_HANDLER = 'continueDetection';
var PERIODIC_HANDLER = 'runDetection';

// ---------------------------------------------------------------- UI / 公開関数

function onOpen() {
  SpreadsheetApp.getUi().createMenu('DLPサイズ抽出')
    .addItem('初期設定(シート作成・定期実行の登録)', 'setup')
    .addItem('今すぐ実行', 'runDetection')
    .addItem('状態をリセット(次回は初回扱い)', 'resetState')
    .addToUi();
}

/** シートと既定設定を作り、定期実行トリガーを登録する。 */
function setup() {
  var ss = SpreadsheetApp.getActive();
  ensureSheet_(ss, SHEET.CONFIG, ['キー', '値', '説明'], function (sh) {
    sh.getRange(2, 1, DEFAULT_CONFIG.length, 3).setValues(DEFAULT_CONFIG);
    sh.setColumnWidth(2, 260); sh.setColumnWidth(3, 520);
  });
  ensureSheet_(ss, SHEET.RESULT, HEADERS.RESULT);
  ensureSheet_(ss, SHEET.FAILED, HEADERS.FAILED);
  ensureSheet_(ss, SHEET.PARTIAL, HEADERS.PARTIAL).hideSheet();
  ensureSheet_(ss, SHEET.LOG, HEADERS.LOG);
  installPeriodicTrigger_(readConfig_().TRIGGER_INTERVAL_MINUTES);
  return 'setup done';
}

/** 定期実行の入口。処理中の期間があれば続きから、なければ前回以降の新しい期間を処理する。 */
function runDetection() {
  return runWithLock_();
}

/** 時間切れ後の続き実行(一回限りのトリガーから呼ばれる)。 */
function continueDetection() {
  deleteTriggers_(CONTINUE_HANDLER);
  return runWithLock_();
}

function resetState() {
  var p = PropertiesService.getScriptProperties();
  p.deleteProperty(PROP.WATERMARK);
  p.deleteProperty(PROP.WINDOW);
  return 'reset';
}

/** 動作確認用: Web アプリ(実行者=自分、アクセス=自分のみ)として配置した場合の入口。 */
function doGet(e) {
  var action = (e && e.parameter && e.parameter.action) || 'status';
  var out;
  if (action === 'setup') out = setup();
  else if (action === 'run') out = runDetection();
  else if (action === 'reset') out = resetState();
  else if (action === 'config') out = setConfigFromParams_(e.parameter);
  else out = status_();
  return ContentService.createTextOutput(JSON.stringify(out, null, 2)).setMimeType(ContentService.MimeType.JSON);
}

// ---------------------------------------------------------------- 本体

function runWithLock_() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) return { skipped: 'another run is in progress' };
  try {
    return detect_(new Date());
  } finally {
    lock.releaseLock();
  }
}

function detect_(startedAt) {
  var deadline = startedAt.getTime() + readConfig_().MAX_RUNTIME_SECONDS * 1000;
  var cfg = readConfig_();
  var ss = SpreadsheetApp.getActive();
  var props = PropertiesService.getScriptProperties();
  var resultSheet = ensureSheet_(ss, SHEET.RESULT, HEADERS.RESULT);
  var failedSheet = ensureSheet_(ss, SHEET.FAILED, HEADERS.FAILED);
  var partialSheet = ensureSheet_(ss, SHEET.PARTIAL, HEADERS.PARTIAL);

  // 処理中の期間を復元、なければ新しい期間を作る
  var win = JSON.parse(props.getProperty(PROP.WINDOW) || 'null');
  if (!win) {
    var wm = props.getProperty(PROP.WATERMARK);
    var start = wm ? new Date(new Date(wm).getTime() - cfg.OVERLAP_MINUTES * 60000)
      : new Date(startedAt.getTime() - cfg.INITIAL_LOOKBACK_DAYS * 86400000);
    win = { start: start.toISOString(), end: startedAt.toISOString(), pageToken: null,
      stats: { events: 0, ruleMatched: 0, candidates: 0, appended: 0, belowSize: 0, failed: 0 } };
    props.setProperty(PROP.WINDOW, JSON.stringify(win));
  }

  var seen = loadColumnSet_(resultSheet, 3);           // 記録済みファイルID
  loadColumnSet_(failedSheet, 3, seen);                 // 取得失敗として記録済みのファイルID
  var partial = cfg.REQUIRE_ALL_RULES ? loadPartial_(partialSheet) : null;
  var ruleSet = cfg.RULE_NAMES.length ? toSet_(cfg.RULE_NAMES) : null;
  var finished = false, note = '';

  while (true) {
    if (Date.now() > deadline) break;
    var page;
    try {
      page = listRuleMatches_(win.start, win.end, win.pageToken, cfg.EVENT_NAME);
    } catch (err) {
      if (win.pageToken && /token/i.test(String(err))) {   // 期限切れのページ位置: 期間の先頭からやり直す(重複は除外される)
        win.pageToken = null; note = 'pageToken expired, restarted window'; continue;
      }
      throw err;
    }
    var candidates = collectCandidates_(page.items, ruleSet, cfg, partial, seen, win.stats);
    if (candidates.length) {
      var res = resolveAndFilter_(candidates, cfg, deadline);
      appendRows_(resultSheet, res.rows);
      appendRows_(failedSheet, res.failed);
      res.rows.forEach(function (r) { seen[r[2]] = true; });
      res.failed.forEach(function (r) { seen[r[2]] = true; });
      win.stats.appended += res.rows.length;
      win.stats.failed += res.failed.length;
      win.stats.belowSize += res.belowSize;
      if (res.unprocessed.length) {        // 時間切れでサイズ未確認のものが残った: 同じページを次回もう一度読む
        note = 'deadline during size lookup';
        props.setProperty(PROP.WINDOW, JSON.stringify(win));
        break;
      }
    }
    if (partial) savePartial_(partialSheet, partial);
    win.pageToken = page.nextPageToken || null;
    props.setProperty(PROP.WINDOW, JSON.stringify(win));
    if (!win.pageToken) { finished = true; break; }
  }

  if (finished) {
    props.setProperty(PROP.WATERMARK, win.end);
    props.deleteProperty(PROP.WINDOW);
  } else {
    scheduleContinuation_();
  }
  var s = win.stats;
  appendRows_(ensureSheet_(ss, SHEET.LOG, HEADERS.LOG), [[startedAt, new Date(), new Date(win.start), new Date(win.end),
    s.events, s.ruleMatched, s.candidates, s.appended, s.belowSize, s.failed, finished ? '完了' : '継続', note]]);
  return { finished: finished, window: { start: win.start, end: win.end }, stats: s, note: note };
}

/** Reports API から DLP の内容一致イベントを1ページ取得する。 */
function listRuleMatches_(startIso, endIso, pageToken, eventName) {
  var opt = { startTime: startIso, endTime: endIso, eventName: eventName, maxResults: 1000 };
  if (pageToken) opt.pageToken = pageToken;
  var resp = AdminReports.Activities.list('all', 'rules', opt);
  return { items: resp.items || [], nextPageToken: resp.nextPageToken };
}

function eventParams_(ev) {
  var o = {};
  (ev.parameters || []).forEach(function (p) {
    o[p.name] = p.value !== undefined ? p.value : p.multiValue !== undefined ? p.multiValue
      : p.intValue !== undefined ? p.intValue : p.boolValue;
  });
  return o;
}

/**
 * ページ内のイベントを規則名で絞り、ファイル単位にまとめる。
 * AND 指定時は、ファイルごとに一致済みの規則を蓄積し、すべてそろったものだけ候補にする。
 */
function collectCandidates_(items, ruleSet, cfg, partial, seen, stats) {
  var byFile = {};
  items.forEach(function (act) {
    (act.events || []).forEach(function (ev) {
      if (ev.name !== cfg.EVENT_NAME) return;
      stats.events++;
      var p = eventParams_(ev);
      if (p.data_source && p.data_source !== 'DRIVE') return;
      if (p.rule_type && p.rule_type !== 'DLP') return;
      var fileId = p.resource_id;
      if (!fileId || !p.rule_name) return;
      if (ruleSet && !ruleSet[p.rule_name]) return;
      stats.ruleMatched++;
      if (seen[fileId]) return;
      var t = act.id && act.id.time;
      var c = byFile[fileId] || (byFile[fileId] = { fileId: fileId, title: p.resource_title || '',
        owner: p.resource_owner_email || '', rules: {}, ruleIds: {}, time: t });
      c.rules[p.rule_name] = true;
      var rid = p.rule_resource_name || p.rule_id;
      if (rid) c.ruleIds[rid] = true;
      if (t && (!c.time || t < c.time)) c.time = t;
    });
  });
  var out = [];
  Object.keys(byFile).forEach(function (id) {
    var c = byFile[id];
    if (partial) {
      var prev = partial[id] || { rules: {}, first: c.time, last: c.time };
      Object.keys(c.rules).forEach(function (r) { prev.rules[r] = true; });
      if (c.time && (!prev.first || c.time < prev.first)) prev.first = c.time;
      if (c.time && (!prev.last || c.time > prev.last)) prev.last = c.time;
      partial[id] = prev;
      var all = cfg.RULE_NAMES.every(function (r) { return prev.rules[r]; });
      if (!all) return;
      c.rules = prev.rules; c.time = prev.first;
      delete partial[id];
    }
    out.push(c);
  });
  stats.candidates += out.length;
  return out;
}

/** Drive API でサイズを取得し、閾値以上を結果行に、取得できないものを失敗行にする。 */
function resolveAndFilter_(candidates, cfg, deadline) {
  var rows = [], failed = [], belowSize = 0, now = new Date();
  var fields = 'id,name,mimeType,size,owners(emailAddress),webViewLink,trashed';
  for (var i = 0; i < candidates.length; i += cfg.DRIVE_FETCH_BATCH) {
    if (Date.now() > deadline) return { rows: rows, failed: failed, belowSize: belowSize, unprocessed: candidates.slice(i) };
    var batch = candidates.slice(i, i + cfg.DRIVE_FETCH_BATCH);
    var reqs = batch.map(function (c) {
      return { url: 'https://www.googleapis.com/drive/v3/files/' + encodeURIComponent(c.fileId) +
        '?supportsAllDrives=true&fields=' + encodeURIComponent(fields),
        headers: { Authorization: 'Bearer ' + driveToken_(c.owner) }, muteHttpExceptions: true };
    });
    var resps = fetchAllWithRetry_(reqs);
    batch.forEach(function (c, k) {
      var r = resps[k], code = r.getResponseCode();
      var ruleNames = Object.keys(c.rules).sort().join('\n');
      if (code !== 200) {
        var text = String(r.getContentText());
        // 設定不備・認証切れ等の全体エラーは、ファイルを処理済みにせず実行を中断する(期間もページ位置も進めない)
        if (code === 401 || code === 429 || code >= 500 || /SERVICE_DISABLED|accessNotConfigured|has not been used/.test(text)) {
          throw new Error('Drive API ' + code + ': ' + text.slice(0, 300));
        }
        failed.push([now, isoToDate_(c.time), c.fileId, c.title, c.owner, ruleNames, 'Drive API ' + code + ': ' +
          text.slice(0, 200)]);
        return;
      }
      var f = JSON.parse(r.getContentText());
      if (f.size === undefined) {       // Google ドキュメント等はバイナリのサイズを持たない
        failed.push([now, isoToDate_(c.time), c.fileId, f.name, c.owner, ruleNames, 'サイズなし(' + f.mimeType + ')']);
        return;
      }
      var size = Number(f.size);
      if (size < cfg.MIN_SIZE_BYTES) { belowSize++; return; }
      rows.push([now, isoToDate_(c.time), f.id, f.name, size, Math.round(size / 1048576 * 100) / 100, f.mimeType,
        (f.owners && f.owners[0] && f.owners[0].emailAddress) || c.owner, ruleNames,
        Object.keys(c.ruleIds).join('\n'), f.webViewLink || '']);
    });
  }
  return { rows: rows, failed: failed, belowSize: belowSize, unprocessed: [] };
}

function fetchAllWithRetry_(reqs) {
  var resps = UrlFetchApp.fetchAll(reqs);
  for (var attempt = 1; attempt <= 4; attempt++) {
    var retry = [];
    resps.forEach(function (r, i) { var c = r.getResponseCode(); if (c === 429 || c >= 500) retry.push(i); });
    if (!retry.length) break;
    Utilities.sleep(Math.min(1000 * Math.pow(2, attempt), 16000));
    var again = UrlFetchApp.fetchAll(retry.map(function (i) { return reqs[i]; }));
    retry.forEach(function (i, k) { resps[i] = again[k]; });
  }
  return resps;
}

// ---------------------------------------------------------------- 認証(任意のサービスアカウント)

/**
 * 既定は実行者(管理者)のトークン。実行者が読めない他人のファイルが多い場合は、
 * ドメイン全体の委任を設定したサービスアカウントの鍵をスクリプトのプロパティに置くと、
 * 監査ログの所有者になりすまして drive.readonly で取得する。
 */
function driveToken_(ownerEmail) {
  var p = PropertiesService.getScriptProperties();
  var sa = p.getProperty(PROP.SA_EMAIL), key = p.getProperty(PROP.SA_KEY);
  if (!sa || !key || !ownerEmail) return ScriptApp.getOAuthToken();
  var cache = CacheService.getScriptCache(), ck = 'tok:' + ownerEmail;
  var hit = cache.get(ck);
  if (hit) return hit;
  var now = Math.floor(Date.now() / 1000);
  var enc = function (o) { return Utilities.base64EncodeWebSafe(JSON.stringify(o)).replace(/=+$/, ''); };
  var unsigned = enc({ alg: 'RS256', typ: 'JWT' }) + '.' + enc({ iss: sa, sub: ownerEmail,
    scope: 'https://www.googleapis.com/auth/drive.readonly', aud: 'https://oauth2.googleapis.com/token',
    iat: now, exp: now + 3600 });
  var sig = Utilities.base64EncodeWebSafe(Utilities.computeRsaSha256Signature(unsigned, key.replace(/\\n/g, '\n')))
    .replace(/=+$/, '');
  var resp = UrlFetchApp.fetch('https://oauth2.googleapis.com/token', { method: 'post', muteHttpExceptions: true,
    payload: { grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion: unsigned + '.' + sig } });
  if (resp.getResponseCode() !== 200) return ScriptApp.getOAuthToken();
  var tok = JSON.parse(resp.getContentText()).access_token;
  cache.put(ck, tok, 3000);
  return tok;
}

// ---------------------------------------------------------------- シート・設定の補助

function readConfig_() {
  var sh = SpreadsheetApp.getActive().getSheetByName(SHEET.CONFIG);
  var map = {};
  DEFAULT_CONFIG.forEach(function (r) { map[r[0]] = r[1]; });
  if (sh && sh.getLastRow() > 1) {
    sh.getRange(2, 1, sh.getLastRow() - 1, 2).getValues().forEach(function (r) { if (r[0]) map[String(r[0]).trim()] = r[1]; });
  }
  var num = function (v, d) { var n = Number(v); return isFinite(n) && v !== '' ? n : d; };
  return {
    MIN_SIZE_BYTES: num(map.MIN_SIZE_BYTES, 1048576),
    RULE_NAMES: String(map.RULE_NAMES || '').split(/[\n,]/).map(function (s) { return s.trim(); }).filter(String),
    REQUIRE_ALL_RULES: map.REQUIRE_ALL_RULES === true || String(map.REQUIRE_ALL_RULES).toUpperCase() === 'TRUE',
    INITIAL_LOOKBACK_DAYS: num(map.INITIAL_LOOKBACK_DAYS, 7),
    OVERLAP_MINUTES: num(map.OVERLAP_MINUTES, 180),
    TRIGGER_INTERVAL_MINUTES: num(map.TRIGGER_INTERVAL_MINUTES, 60),
    MAX_RUNTIME_SECONDS: Math.min(num(map.MAX_RUNTIME_SECONDS, 300), 330),
    DRIVE_FETCH_BATCH: Math.max(1, Math.min(num(map.DRIVE_FETCH_BATCH, 50), 100)),
    EVENT_NAME: String(map.EVENT_NAME || 'content_matched').trim()
  };
}

function setConfigFromParams_(params) {
  var sh = SpreadsheetApp.getActive().getSheetByName(SHEET.CONFIG);
  var keys = sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues().map(function (r) { return r[0]; });
  Object.keys(params).forEach(function (k) {
    var i = keys.indexOf(k);
    if (i >= 0) sh.getRange(i + 2, 2).setValue(params[k]);
  });
  return readConfig_();
}

function ensureSheet_(ss, name, headers, init) {
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
    sh.setFrozenRows(1);
    if (init) init(sh);
  }
  return sh;
}

function appendRows_(sh, rows) {
  if (!rows.length) return;
  var start = sh.getLastRow() + 1, need = start + rows.length - 1 - sh.getMaxRows();
  if (need > 0) sh.insertRowsAfter(sh.getMaxRows(), need);
  sh.getRange(start, 1, rows.length, rows[0].length).setValues(rows);
}

function loadColumnSet_(sh, col, set) {
  set = set || {};
  var n = sh.getLastRow() - 1;
  if (n > 0) sh.getRange(2, col, n, 1).getValues().forEach(function (r) { if (r[0]) set[r[0]] = true; });
  return set;
}

function loadPartial_(sh) {
  var map = {}, n = sh.getLastRow() - 1;
  if (n > 0) sh.getRange(2, 1, n, 4).getValues().forEach(function (r) {
    if (!r[0]) return;
    var rules = {};
    String(r[1]).split('\n').filter(String).forEach(function (x) { rules[x] = true; });
    map[r[0]] = { rules: rules, first: r[2] ? new Date(r[2]).toISOString() : null, last: r[3] ? new Date(r[3]).toISOString() : null };
  });
  return map;
}

function savePartial_(sh, map) {
  var rows = Object.keys(map).map(function (id) {
    var m = map[id];
    return [id, Object.keys(m.rules).sort().join('\n'), isoToDate_(m.first), isoToDate_(m.last)];
  });
  var n = sh.getLastRow() - 1;
  if (n > 0) sh.getRange(2, 1, n, 4).clearContent();
  appendRowsAt2_(sh, rows);
}

function appendRowsAt2_(sh, rows) {
  if (!rows.length) return;
  var need = rows.length + 1 - sh.getMaxRows();
  if (need > 0) sh.insertRowsAfter(sh.getMaxRows(), need);
  sh.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}

function toSet_(arr) { var s = {}; arr.forEach(function (x) { s[x] = true; }); return s; }
function isoToDate_(iso) { return iso ? new Date(iso) : ''; }

// ---------------------------------------------------------------- トリガー

function installPeriodicTrigger_(minutes) {
  deleteTriggers_(PERIODIC_HANDLER);
  var b = ScriptApp.newTrigger(PERIODIC_HANDLER).timeBased();
  if (minutes >= 60) b.everyHours(Math.max(1, Math.round(minutes / 60)));
  else b.everyMinutes([1, 5, 10, 15, 30].filter(function (m) { return m <= minutes; }).pop() || 1);
  b.create();
}

function scheduleContinuation_() {
  if (ScriptApp.getProjectTriggers().some(function (t) { return t.getHandlerFunction() === CONTINUE_HANDLER; })) return;
  ScriptApp.newTrigger(CONTINUE_HANDLER).timeBased().after(60 * 1000).create();
}

function deleteTriggers_(handler) {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === handler) ScriptApp.deleteTrigger(t);
  });
}

function status_() {
  var p = PropertiesService.getScriptProperties();
  return {
    watermark: p.getProperty(PROP.WATERMARK),
    window: JSON.parse(p.getProperty(PROP.WINDOW) || 'null'),
    triggers: ScriptApp.getProjectTriggers().map(function (t) { return t.getHandlerFunction(); }),
    config: readConfig_()
  };
}

if (typeof module !== 'undefined') {
  module.exports = { detect_: detect_, collectCandidates_: collectCandidates_, readConfig_: readConfig_ };
}
