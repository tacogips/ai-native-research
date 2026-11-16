#!/usr/bin/env python3
"""公開仕様と独自合成資料によるDLP検知・是正試験。既定で外部変更しない。"""
import argparse
import json
from pathlib import Path

from dataset import KINDS, make
from observations import import_audit
from remediation import plan_remediation, score_remediation
from rules import apply_rules, plan_rules
from scoring import metrics, score


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('make', help='新しい保存先に複数値と正解行列を作る')
    create.add_argument('--output', required=True, type=Path)
    evaluate = sub.add_parser('score', help='原票から再導出した観測を採点する')
    evaluate.add_argument('--dataset', required=True, type=Path)
    evaluate.add_argument('--observations', required=True, type=Path)
    evaluate.add_argument('--report', required=True, type=Path)
    evaluate.add_argument('--axis', choices=['content', 'protection', 'valid_number'], default='content')
    evaluate.add_argument('--truth-profile', type=Path)
    audit = sub.add_parser('import-audit', help='Rules監査原票と保存済み対応証拠を照合する')
    audit.add_argument('--dataset', required=True, type=Path)
    audit.add_argument('--raw', required=True, type=Path)
    audit.add_argument('--manifest', required=True, type=Path)
    audit.add_argument('--output', required=True, type=Path)
    audit.add_argument('--truth-profile', type=Path)
    plan = sub.add_parser('plan-rules', help='識別子を別保存した設定からAPI作成計画を作る')
    plan.add_argument('--dataset', required=True, type=Path)
    plan.add_argument('--config', required=True, type=Path)
    plan.add_argument('--output', required=True, type=Path)
    apply = sub.add_parser('apply-rules', help='既定は通信なし。--executeで新規試験規則のみ作成')
    apply.add_argument('--plan', required=True, type=Path)
    apply.add_argument('--output', required=True, type=Path)
    apply.add_argument('--execute', action='store_true')
    remed = sub.add_parser('plan-remediation', help='共有状態・操作者・契機ごとの事前計画を作る')
    remed.add_argument('--output', required=True, type=Path)
    remed.add_argument('--config', type=Path, help='私有の対象・期待値対応を事前固定する')
    remed_score = sub.add_parser('score-remediation', help='別主体の読取とDLP動作記録を別軸で採点')
    remed_score.add_argument('--plan', required=True, type=Path)
    remed_score.add_argument('--observations', required=True, type=Path)
    remed_score.add_argument('--report', required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == 'make':
        return make(args.output)
    if args.command == 'score':
        result = score(args.dataset, args.observations, args.report, args.axis, args.truth_profile)
        print(json.dumps(result['primary'], ensure_ascii=False, indent=2))
    elif args.command == 'import-audit':
        result = import_audit(args.dataset, args.raw, args.manifest, args.output, args.truth_profile)
        print('取り込んだ観測行:', len(result['rows']))
    elif args.command == 'plan-rules':
        result = plan_rules(args.dataset, args.config, args.output)
        print('計画した新規資源:', len(result['operations']))
    elif args.command == 'apply-rules':
        result = apply_rules(args.plan, args.output, execute=args.execute)
        print('規則適用状態:', result['status'])
    elif args.command == 'plan-remediation':
        result = plan_remediation(args.output, args.config)
        print('計画した状態遷移:', len(result['cases']))
    else:
        result = score_remediation(args.plan, args.observations, args.report)
        print(json.dumps(result['groups'], ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    main()
