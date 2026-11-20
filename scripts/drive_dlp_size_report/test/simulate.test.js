// Apps Script のサービスを模擬し、Code.js を Node.js で実行する規模・差分の試験。
// 実行: node --test scripts/drive_dlp_size_report/test/
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const CODE = fs.readFileSync(path.join(__dirname, '..', 'src', 'Code.js'), 'utf8');

function makeEnv(opts) {
  const clock = { now: Date.parse('2026-11-20T00:00:00Z') };
  const RealDate = Date;
  class VDate extends RealDate {
    constructor(...a) { if (a.length) super(...a); else super(clock.now); }
    static now() { return clock.now; }
  }
  const counters = { reportCalls: 0, driveCalls: 0, runs: 0 };

  // --- Spreadsheet
  class Range {
    constructor(sh, r, c, nr, nc) { Object.assign(this, { sh, r, c, nr: nr || 1, nc: nc || 1 }); }
    getValues() {
      const out = [];
      for (let i = 0; i < this.nr; i++) {
        const row = this.sh.data[this.r - 1 + i] || [];
        const o = [];
        for (let j = 0; j < this.nc; j++) { const v = row[this.c - 1 + j]; o.push(v === undefined ? '' : v); }
        out.push(o);
      }
      return out;
    }
    setValues(v) {
      if (this.r - 1 + v.length > this.sh.maxRows) throw new Error('range outside sheet');
      v.forEach((row, i) => { const t = this.sh.data[this.r - 1 + i] || (this.sh.data[this.r - 1 + i] = []);
        row.forEach((x, j) => { t[this.c - 1 + j] = x; }); });
      return this;
    }
    setValue(x) { return this.setValues([[x]]); }
    clearContent() { for (let i = 0; i < this.nr; i++) { const t = this.sh.data[this.r - 1 + i]; if (t) for (let j = 0; j < this.nc; j++) t[this.c - 1 + j] = ''; } return this; }
    setFontWeight() { return this; }
  }
  class Sheet {
    constructor(name) { this.name = name; this.data = []; this.maxRows = 1000; }
    getRange(r, c, nr, nc) { return new Range(this, r, c, nr, nc); }
    getLastRow() { for (let i = this.data.length - 1; i >= 0; i--) if (this.data[i] && this.data[i].some((x) => x !== '' && x !== undefined)) return i + 1; return 0; }
    getMaxRows() { return this.maxRows; }
    insertRowsAfter(_, n) { this.maxRows += n; }
    setFrozenRows() {} setColumnWidth() {} hideSheet() { return this; }
  }
  const sheets = {};
  const ss = { getSheetByName: (n) => sheets[n] || null, insertSheet: (n) => (sheets[n] = new Sheet(n)) };

  const props = {};
  const triggers = [];
  const ctx = {
    Date: VDate, JSON, Math, Object, String, Number, isFinite, encodeURIComponent, console,
    SpreadsheetApp: { getActive: () => ss, getUi: () => ({}) },
    PropertiesService: { getScriptProperties: () => ({
      getProperty: (k) => (k in props ? props[k] : null), setProperty: (k, v) => { props[k] = String(v); },
      deleteProperty: (k) => { delete props[k]; } }) },
    LockService: { getScriptLock: () => ({ tryLock: () => true, releaseLock: () => {} }) },
    CacheService: { getScriptCache: () => ({ get: () => null, put: () => {} }) },
    Utilities: { sleep: (ms) => { clock.now += ms; } },
    ScriptApp: {
      getOAuthToken: () => 'tok', getProjectTriggers: () => triggers.slice(),
      deleteTrigger: (t) => triggers.splice(triggers.indexOf(t), 1),
      newTrigger: (h) => { const t = { getHandlerFunction: () => h }; const b = { timeBased: () => b,
        everyHours: () => b, everyMinutes: () => b, after: () => b, create: () => { triggers.push(t); return t; } }; return b; }
    },
    AdminReports: { Activities: { list: (user, app, o) => {
      counters.reportCalls++; clock.now += opts.reportLatencyMs;
      assert.equal(app, 'rules'); assert.equal(o.eventName, 'content_matched');
      // 監査ログは到着順でなく時刻の降順。期間 [start, end) に入るもの(到着済みのみ)を返す
      const s = Date.parse(o.startTime), e = Date.parse(o.endTime);
      const rows = opts.events.filter((x) => x.arrived <= clock.now && x.t >= s && x.t < e).sort((a, b) => b.t - a.t);
      const off = o.pageToken ? Number(o.pageToken) : 0;
      const page = rows.slice(off, off + o.maxResults);
      return { items: page.map((x) => ({ id: { time: new RealDate(x.t).toISOString(), uniqueQualifier: x.q },
        events: [{ name: 'content_matched', parameters: [
          { name: 'rule_type', value: 'DLP' },
          { name: 'data_source', value: x.source || 'DRIVE' }, { name: 'resource_id', value: x.file },
          { name: 'rule_name', value: x.rule }, { name: 'rule_resource_name', value: 'policies/' + x.rule },
          { name: 'resource_title', value: 'title-' + x.file }, { name: 'resource_owner_email', value: 'u@example.test' }] }] })),
        nextPageToken: off + o.maxResults < rows.length ? String(off + o.maxResults) : undefined };
    } } },
    UrlFetchApp: { fetchAll: (reqs) => { counters.driveCalls += reqs.length; clock.now += opts.driveBatchLatencyMs;
      return reqs.map((r) => { const id = decodeURIComponent(r.url.split('/files/')[1].split('?')[0]);
        const f = opts.files[id];
        if (!f) return { getResponseCode: () => 404, getContentText: () => 'not found' };
        return { getResponseCode: () => 200, getContentText: () => JSON.stringify({ id, name: 'name-' + id,
          mimeType: 'text/plain', size: f.native ? undefined : String(f.size), owners: [{ emailAddress: 'u@example.test' }], webViewLink: 'https://drive/' + id }) }; }); } },
    ContentService: {}
  };
  vm.createContext(ctx);
  vm.runInContext(CODE, ctx);
  vm.runInContext('setup()', ctx);
  const setCfg = (k, v) => { const sh = sheets['設定']; const i = sh.data.findIndex((r) => r && r[0] === k); sh.data[i][1] = v; };
  const run = (fn) => { counters.runs++; return vm.runInContext(fn + '()', ctx); };
  const resultIds = () => sheets['検知結果'].data.slice(1).filter((r) => r && r[2]).map((r) => r[2]);
  return { ctx, clock, counters, sheets, props, triggers, setCfg, run, resultIds };
}

function expectedIds(events, files, rules, n, upTo) {
  const ids = new Set();
  events.forEach((e) => { if (e.t < upTo && (e.source || 'DRIVE') === 'DRIVE' && (!rules || rules.includes(e.rule)) && files[e.file] && !files[e.file].native && files[e.file].size >= n) ids.add(e.file); });
  return ids;
}

test('数十万件: 時間切れで継続し、全期間を重複なく処理する', () => {
  const N_FILES = 200000, N_EVENTS = 300000, MIN = 1000000;
  const base = Date.parse('2026-11-14T00:00:00Z');
  let seed = 7; const rnd = () => { seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const files = {};
  for (let i = 0; i < N_FILES; i++) files['f' + i] = { size: Math.floor(rnd() * 3000000), native: rnd() < 0.02 };
  const rules = ['R-card', 'R-mynumber', 'R-other'];
  const events = [];
  for (let i = 0; i < N_EVENTS; i++) events.push({ q: 'q' + i, file: 'f' + Math.floor(rnd() * (N_FILES + 500)),
    rule: rules[Math.floor(rnd() * 3)], t: base + Math.floor(rnd() * 5.5 * 86400000), arrived: 0, source: rnd() < 0.01 ? 'GMAIL' : 'DRIVE' });
  const env = makeEnv({ events, files, reportLatencyMs: 800, driveBatchLatencyMs: 300 });
  env.setCfg('MIN_SIZE_BYTES', MIN);
  env.setCfg('RULE_NAMES', 'R-card\nR-mynumber');
  const firstEnd = env.clock.now;
  let r, loops = 0;
  do { r = env.run(loops === 0 ? 'runDetection' : 'continueDetection'); env.clock.now += 60000; loops++; } while (!r.finished && loops < 500);
  assert.ok(r.finished, 'finished');
  assert.ok(loops > 1, '時間切れによる継続が発生する: ' + loops);
  const got = env.resultIds();
  const exp = expectedIds(events, files, ['R-card', 'R-mynumber'], MIN, firstEnd);
  assert.equal(new Set(got).size, got.length, '重複なし');
  assert.deepStrictEqual(new Set(got), exp);
  assert.equal(env.props.DLPSIZE_WATERMARK, new Date(firstEnd).toISOString());
  console.log(`runs=${loops} results=${got.length} reportCalls=${env.counters.reportCalls} driveCalls=${env.counters.driveCalls}`);

  // 2回目: 新しい検知と、遅れて到着した古い時刻の検知(重ね取得の範囲内)だけを追加する
  const before = got.length;
  const now = env.clock.now;
  const newFiles = [];
  for (let i = 0; i < 50; i++) { const id = 'n' + i; files[id] = { size: i % 2 ? 2000000 : 10 }; newFiles.push(id);
    events.push({ q: 'nq' + i, file: id, rule: 'R-card', t: now - 30000, arrived: now - 1000 }); }
  files.late1 = { size: 5000000 };
  events.push({ q: 'late', file: 'late1', rule: 'R-mynumber', t: firstEnd - 3600000, arrived: now - 1000 }); // 1時間前の時刻で遅着
  events.push({ q: 'dup', file: got[0], rule: 'R-card', t: now - 20000, arrived: now - 1000 }); // 記録済みファイルの再検知
  r = env.run('runDetection');
  assert.ok(r.finished);
  const after = env.resultIds();
  const added = after.slice(before);
  assert.deepStrictEqual(new Set(added), new Set(newFiles.filter((_, i) => i % 2).concat(['late1'])));
  assert.equal(new Set(after).size, after.length);
});

test('複数規則のAND: すべての規則に一致したファイルだけを、別の実行にまたがっても記録する', () => {
  const files = { a: { size: 5e6 }, b: { size: 5e6 }, c: { size: 10 }, d: { size: 5e6 } };
  const t0 = Date.parse('2026-11-19T00:00:00Z');
  const events = [
    { q: 1, file: 'a', rule: 'R1', t: t0, arrived: 0 }, { q: 2, file: 'a', rule: 'R2', t: t0 + 1, arrived: 0 },
    { q: 3, file: 'b', rule: 'R1', t: t0, arrived: 0 },
    { q: 4, file: 'c', rule: 'R1', t: t0, arrived: 0 }, { q: 5, file: 'c', rule: 'R2', t: t0, arrived: 0 },
    { q: 6, file: 'd', rule: 'R3', t: t0, arrived: 0 }];
  const env = makeEnv({ events, files, reportLatencyMs: 10, driveBatchLatencyMs: 10 });
  env.setCfg('RULE_NAMES', 'R1, R2'); env.setCfg('REQUIRE_ALL_RULES', true); env.setCfg('MIN_SIZE_BYTES', 1000);
  assert.ok(env.run('runDetection').finished);
  assert.deepStrictEqual(env.resultIds(), ['a']);
  // b は R1 のみ一致で保留。次の実行で R2 が来たら記録する
  env.clock.now += 3600000;
  events.push({ q: 7, file: 'b', rule: 'R2', t: env.clock.now - 60000, arrived: env.clock.now - 60000 });
  assert.ok(env.run('runDetection').finished);
  assert.deepStrictEqual(env.resultIds(), ['a', 'b']);
  const row = env.sheets['検知結果'].data[2];
  assert.equal(row[8], 'R1\nR2');
});
