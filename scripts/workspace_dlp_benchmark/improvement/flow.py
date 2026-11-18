"""是正・削除フローの比較シミュレーション（現行案F0と改善案F1）。

事例調査の改善案のうち、運用フローに関わるものを状態遷移として実装し、同じ架空のドライブ在庫で
週単位に動かして比べる。結果は前提値に依存するモデル計算であり、Google実環境の測定ではない。

  F0 現行案: DLP検知 → 管理者が全件を確認 → 作成者へ削除・修正依頼 → 作成者が対応。
  F1 改善案:
    (1) 共有の棚卸しを先に行う。公開リンク・外部共有で1年以上更新のないファイルは、内容検知を待たず
        共有を解除する（可逆。所有者へ通知し、理由を付ければ戻せる）。
    (2) 検知結果は「提案」として所有者へ直接送る。優先度＝機微度×露出範囲。管理者の全件確認はしない。
    (3) 所有者が確定したものだけを是正（ラベル＋外部共有の制限）。削除は確定後の猶予期間の後だけ。
    (4) 所有者不在（退職等）は上長へ回す。期限切れは管理者へ。
    (5) 新規ファイルに安全側の既定ラベル（社内限）を付け、ラベルを条件に外部共有を制限する。
    (6) 通知・台帳には一致した値を載せない（ファイルID・項目種別・グループだけ）。
  段階導入（監査のみ→通知→是正）は両案で同じにし、差が出ないようにする。

状態遷移の不変条件（test_flow.pyで検査）
  - 削除は confirmed を経て猶予期間を過ぎたものだけ。
  - すべての未完了案件に担当者がいる（所有者・上長・管理者のいずれか）。
  - 事象記録は追記のみで、通知の本文に一致値を含めない。
"""
import argparse
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

SHARING = ('restricted', 'domain', 'external', 'public_link')
EXPOSED = ('external', 'public_link')           # 社外から読める
AI_REACH = ('domain', 'external', 'public_link')  # 社内の誰でも（生成AIの検索も）届く

# 前提値。根拠は README と報告書の表を参照。公開の事例・調査に幅があるため感度分析で振る。
DEFAULT_SCENARIO = {
    'files': 20000,
    'weeks': 12,
    'sensitive_rate': 0.15,          # 機微情報を含むファイルの割合
    'high_severity_share': 0.5,      # 機微ファイルのうち高機微（番号・健康・要配慮・認証情報）
    'sharing_mix': {'restricted': 0.68, 'domain': 0.17, 'external': 0.12, 'public_link': 0.03},
    'stale_rate': 0.45,              # 1年以上更新なし
    'departed_owner_rate': 0.06,     # 所有者が退職・異動済み
    'new_files_per_week': 0.01,      # 在庫に対する新規作成の割合
    'new_file_share_external_rate': 0.10,  # 新規ファイルのうち外部共有されるもの
    'default_label_downgrade_rate': 0.05,  # 既定ラベルを理由付きで下げて共有する割合（機微ファイル）
    'owner_response_per_week': 0.5,  # 在籍所有者が1週間以内に依頼へ応答する確率
    'manager_response_per_week': 0.4,
    'owner_wrong_reject_rate': 0.05, # 本当に機微なのに所有者が「該当なし」とする割合
    'reject_audit_rate': 0.10,       # 却下のうち管理者が抜き取り確認する割合
    'owner_delete_on_request': 0.5,  # F0で依頼を受けた所有者が修正ではなく削除を選ぶ割合
    'restore_request_rate': 0.05,    # 棚卸しで解除した非機微ファイルの再共有申請
    'admin_alerts_per_week': 300,    # 管理者が確認できる件数（1人・週）
    'audit_only_weeks': 2,           # 段階導入：監査のみの期間（両案共通）
    'grace_weeks': 4,
    'f1_inventory': True,        # F1の構成要素の切り分け用
    'f1_default_label': True,
    'inventory_include_domain': False,  # F1：組織全体共有で1年以上更新なしも棚卸しで解除（生成AI対策）                # F1：確定から削除までの猶予
    'escalate_after_weeks': 1,
    'minutes': {'triage': 4, 'request': 2, 'escalation': 10, 'restore': 8, 'reject_audit': 5, 'tracking_per_open': 0.5},
}

STATES = ('detected', 'proposed', 'confirmed', 'rejected', 'escalated', 'enforced', 'deleted', 'restored', 'closed')
ALLOWED = {
    'detected': {'proposed', 'closed'},
    'proposed': {'confirmed', 'rejected', 'escalated'},
    'escalated': {'confirmed', 'rejected', 'escalated'},
    'confirmed': {'enforced'},
    'rejected': {'closed', 'proposed'},
    'enforced': {'deleted', 'restored', 'closed'},
    'deleted': set(), 'restored': set(), 'closed': set(),
}


@dataclass
class File:
    fid: int
    sensitive: bool
    high: bool
    sharing: str
    stale: bool
    departed: bool
    detected: bool = False
    label: str | None = None
    deleted: bool = False
    deleted_week: int | None = None


@dataclass
class Case:
    fid: int
    assignee: str
    state: str = 'detected'
    since: int = 0
    log: list = field(default_factory=list)

    def move(self, to, week, note=''):
        if to not in ALLOWED[self.state]:
            raise ValueError(f'不正な遷移 {self.state}→{to}')
        self.log.append({'week': week, 'from': self.state, 'to': to, 'note': note})
        self.state, self.since = to, week


def notification(f, group):
    """通知の本文。一致した値は含めない（改善案6）。"""
    return {'file_id': f.fid, 'group': group, 'exposure': f.sharing, 'action': '確認してください'}


def make_inventory(sc, rng):
    files = []
    mix = sc['sharing_mix']
    for i in range(sc['files']):
        sensitive = rng.random() < sc['sensitive_rate']
        files.append(File(i, sensitive, sensitive and rng.random() < sc['high_severity_share'],
                          rng.choices(SHARING, [mix[s] for s in SHARING])[0],
                          rng.random() < sc['stale_rate'], rng.random() < sc['departed_owner_rate']))
    return files


def priority(f):
    return (2 if f.high else 1) * {'public_link': 4, 'external': 3, 'domain': 2, 'restricted': 1}[f.sharing]


def simulate(flow, detector, sc=None, seed=0, keep_cases=False):
    """detector={'tpr':..., 'fpr':...}（ファイル単位）。週ごとに進め、指標を返す。"""
    sc = {**DEFAULT_SCENARIO, **(sc or {})}
    rng = random.Random(seed)
    files = make_inventory(sc, rng)
    m = {k: 0 for k in ('admin_minutes', 'owner_requests', 'owner_requests_non_sensitive', 'wrongful_restrictions',
                        'wrongful_deletions', 'irreversible_deletions', 'deleted_sensitive', 'escalations',
                        'restore_tickets', 'inventory_unshared', 'missed_sensitive_rejected', 'reversible_unshare_non_sensitive', 'deletions_without_grace', 'default_label_downgrades')}
    exposure_weeks = 0
    cases, queue = {}, []
    weekly = []

    def detect(f):
        f.detected = rng.random() < (detector['tpr'] if f.sensitive else detector['fpr'])
        return f.detected

    # 段階0（F1のみ）：共有の棚卸し。内容検知を待たない（改善案1）。
    if flow == 'F1' and sc['f1_inventory']:
        for f in files:
            scope = AI_REACH if sc['inventory_include_domain'] else EXPOSED
            if f.sharing in scope and f.stale:
                f.sharing = 'restricted'
                m['inventory_unshared'] += 1
                m['reversible_unshare_non_sensitive'] += int(not f.sensitive)
                if not f.sensitive and not f.departed and rng.random() < sc['restore_request_rate']:
                    m['restore_tickets'] += 1
                    m['admin_minutes'] += sc['minutes']['restore']
                    f.sharing = 'external'  # 理由付きで戻す（可逆）

    for f in files:
        detect(f)
    pending = sorted([f for f in files if f.detected], key=lambda f: -priority(f) if flow == 'F1' else f.fid)

    next_id = len(files)
    for week in range(sc['weeks']):
        # 新規ファイル（既定ラベルは F1 のみ。改善案5）
        for _ in range(int(sc['files'] * sc['new_files_per_week'])):
            sensitive = rng.random() < sc['sensitive_rate']
            nf = File(next_id, sensitive, sensitive and rng.random() < sc['high_severity_share'], 'restricted', False, False)
            next_id += 1
            if rng.random() < sc['new_file_share_external_rate']:
                if flow == 'F1' and sc['f1_default_label']:
                    nf.label = '社内限'
                    if nf.sensitive and rng.random() < sc['default_label_downgrade_rate']:
                        nf.sharing = 'external'   # 理由付きで下げた
                        m['default_label_downgrades'] += 1
                    elif not nf.sensitive:
                        nf.sharing = 'external'   # 非機微は下げて共有できる（下げる手間は利用者側）
                        m['default_label_downgrades'] += 1
                else:
                    nf.sharing = 'external'
            files.append(nf)
            if detect(nf):
                pending.append(nf)
        if flow == 'F1':
            pending.sort(key=lambda f: -priority(f))

        audit_only = week < sc['audit_only_weeks']
        if not audit_only:
            if flow == 'F0':
                # 管理者が全件確認してから依頼する。容量を超えると滞留。
                capacity = sc['admin_alerts_per_week']
                take, pending = pending[:capacity], pending[capacity:]
                for f in take:
                    m['admin_minutes'] += sc['minutes']['triage']
                    if f.sensitive:
                        c = Case(f.fid, 'owner' if not f.departed else 'none')
                        c.move('proposed', week, 'admin_request')
                        cases[f.fid] = c
                        m['owner_requests'] += 1
                        m['admin_minutes'] += sc['minutes']['request']
                    # 非機微は管理者が閉じる（依頼しない）
            else:
                for f in pending:
                    c = Case(f.fid, 'manager' if f.departed else 'owner')
                    c.move('proposed', week, 'auto_proposal')
                    cases[f.fid] = c
                    m['owner_requests'] += 1
                    if not f.sensitive:
                        m['owner_requests_non_sensitive'] += 1
                    if f.departed:
                        m['escalations'] += 1
                        m['admin_minutes'] += sc['minutes']['escalation']
                pending = []

        # 案件の進行
        byid = {f.fid: f for f in files}
        for fid, c in list(cases.items()):
            f = byid[fid]
            if c.state in ('proposed', 'escalated'):
                if c.assignee == 'none':
                    continue  # F0：所有者不在は誰も動かない
                p = sc['manager_response_per_week'] if c.assignee == 'manager' else sc['owner_response_per_week']
                if rng.random() >= p:
                    if flow == 'F1' and week - c.since >= sc['escalate_after_weeks'] and c.assignee == 'owner':
                        c.assignee = 'manager'
                        c.move('escalated', week, 'timeout')
                        m['escalations'] += 1
                        m['admin_minutes'] += sc['minutes']['escalation']
                    continue
                if flow == 'F0':
                    # 所有者が対応：削除か共有解除
                    c.move('confirmed', week)
                    c.move('enforced', week)
                    if rng.random() < sc['owner_delete_on_request']:
                        f.deleted, f.deleted_week = True, week
                        c.move('deleted', week)
                        m['deletions_without_grace'] += 1
                        m['irreversible_deletions'] += 1
                        m['deleted_sensitive'] += int(f.sensitive)
                        m['wrongful_deletions'] += int(not f.sensitive)
                    else:
                        f.sharing = 'restricted'
                        c.move('closed', week)
                else:
                    wrong = f.sensitive and rng.random() < sc['owner_wrong_reject_rate']
                    if f.sensitive and not wrong:
                        c.move('confirmed', week)
                        c.move('enforced', week, 'label+restrict')
                        f.label, f.sharing = '機密', 'restricted'
                    else:
                        c.move('rejected', week)
                        if rng.random() < sc['reject_audit_rate']:
                            m['admin_minutes'] += sc['minutes']['reject_audit']
                            if f.sensitive:
                                c.move('proposed', week, 'audit_reopen')
                                continue
                        if f.sensitive:
                            m['missed_sensitive_rejected'] += 1
                        c.move('closed', week)
            elif c.state == 'enforced' and flow == 'F1' and week - c.since >= sc['grace_weeks']:
                # 猶予後も保持理由がないものだけ削除。ここでは確定済みの半数が削除を選ぶと置く。
                if rng.random() < sc['owner_delete_on_request']:
                    if c.log[-1]['from'] != 'confirmed':
                        raise AssertionError('確定を経ない削除')
                    f.deleted, f.deleted_week = True, week
                    c.move('deleted', week)
                    m['irreversible_deletions'] += 1
                    m['deleted_sensitive'] += int(f.sensitive)
                    m['wrongful_deletions'] += int(not f.sensitive)
                else:
                    c.move('closed', week)

        open_cases = sum(1 for c in cases.values() if c.state in ('proposed', 'escalated', 'enforced'))
        m['admin_minutes'] += open_cases * sc['minutes']['tracking_per_open'] if flow == 'F0' else 0
        live = [f for f in files if not f.deleted]
        exposed = sum(1 for f in live if f.sensitive and f.sharing in EXPOSED)
        exposure_weeks += exposed
        weekly.append({'week': week, 'exposed_sensitive': exposed,
                       'ai_reachable_sensitive': sum(1 for f in live if f.sensitive and f.sharing in AI_REACH),
                       'backlog_alerts': len(pending), 'open_cases': open_cases})

    live = [f for f in files if not f.deleted]
    orphan_stuck = sum(1 for c in cases.values() if c.assignee == 'none' and c.state == 'proposed')
    m['wrongful_restrictions'] = sum(1 for f in files if not f.sensitive and f.label == '機密')
    result = {
        'flow': flow, 'detector': detector, 'seed': seed,
        'exposed_sensitive_end': weekly[-1]['exposed_sensitive'],
        'exposed_sensitive_start': sum(1 for f in make_inventory(sc, random.Random(seed)) if f.sensitive and f.sharing in EXPOSED),
        'ai_reachable_sensitive_end': weekly[-1]['ai_reachable_sensitive'],
        'exposure_file_weeks': exposure_weeks,
        'backlog_alerts_end': weekly[-1]['backlog_alerts'],
        'orphan_stuck': orphan_stuck,
        'new_sensitive_exposed_end': sum(1 for f in live if f.fid >= sc['files'] and f.sensitive and f.sharing in EXPOSED),
        'open_cases_end': weekly[-1]['open_cases'],
        'admin_hours': round(m.pop('admin_minutes') / 60, 1),
        **m, 'weekly': weekly,
    }
    if keep_cases:
        result['_cases'] = cases
    return result


def summarize(runs):
    keys = [k for k, v in runs[0].items() if isinstance(v, (int, float)) and k != 'seed']
    out = {}
    for k in keys:
        vals = sorted(r[k] for r in runs)
        out[k] = {'mean': round(sum(vals) / len(vals), 1), 'p05': vals[int(0.05 * (len(vals) - 1))],
                  'p95': vals[int(0.95 * (len(vals) - 1))]}
    return out


def compare(detectors, seeds=20, overrides=None):
    table = {}
    for dname, det in detectors.items():
        for flow in ('F0', 'F1'):
            runs = [simulate(flow, det, overrides, seed=s) for s in range(seeds)]
            table[f'{flow}/{dname}'] = summarize(runs)
    return table


SENSITIVITY = {
    '管理者の確認容量 100件/週': {'admin_alerts_per_week': 100},
    '管理者の確認容量 1000件/週': {'admin_alerts_per_week': 1000},
    '所有者の応答率 0.3/週': {'owner_response_per_week': 0.3},
    '所有者の応答率 0.8/週': {'owner_response_per_week': 0.8},
    '外部共有が少ない（外部5%・公開1%）': {'sharing_mix': {'restricted': 0.79, 'domain': 0.15, 'external': 0.05, 'public_link': 0.01}},
    '退職者の所有が多い（15%）': {'departed_owner_rate': 0.15},
    '機微ファイルが多い（30%）': {'sensitive_rate': 0.30},
    '棚卸しに組織全体共有も含める（生成AI対策）': {'inventory_include_domain': True},
    '切り分け：F1から共有の棚卸しを除く': {'f1_inventory': False},
    '切り分け：F1から既定ラベルを除く': {'f1_default_label': False},
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--context-report', help='evaluate_context.py の出力。holdout のファイル単位の率を使う')
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--report', required=True)
    a = ap.parse_args(argv)
    detectors = {'baseline': {'tpr': 0.70, 'fpr': 0.10}, 'improved': {'tpr': 0.90, 'fpr': 0.05}}
    source = 'placeholder'
    if a.context_report:
        rep = json.loads(Path(a.context_report).read_text(encoding='utf-8'))['datasets']['holdout']['metrics']
        for name, cfg in (('baseline', 'baseline'), ('improved', 'T1+T2+T3')):
            f = rep[cfg]['files']
            detectors[name] = {'tpr': f['recall'], 'fpr': round(f['FP'] / (f['FP'] + f['TN']), 4) if f['FP'] + f['TN'] else 0.0}
        source = a.context_report
    result = {'scenario': DEFAULT_SCENARIO, 'detectors': detectors, 'detector_source': source, 'seeds': a.seeds,
              'main': compare(detectors, a.seeds),
              'sensitivity': {name: compare(detectors, a.seeds, ov) for name, ov in SENSITIVITY.items()},
              'note': '前提値に依存するモデル計算。Google実環境の測定ではない。'}
    Path(a.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    keys = ['new_sensitive_exposed_end', 'exposed_sensitive_start', 'exposed_sensitive_end', 'ai_reachable_sensitive_end', 'exposure_file_weeks',
            'backlog_alerts_end', 'orphan_stuck', 'admin_hours', 'owner_requests', 'owner_requests_non_sensitive',
            'irreversible_deletions', 'deletions_without_grace', 'wrongful_deletions', 'missed_sensitive_rejected', 'inventory_unshared', 'restore_tickets']
    for name, s in result['main'].items():
        print(name, {k: s[k]['mean'] for k in keys if k in s})
    return result


if __name__ == '__main__':
    main()
