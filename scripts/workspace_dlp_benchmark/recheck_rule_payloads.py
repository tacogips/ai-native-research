"""対照試験の公開定義から、Cloud Identity Policy APIの作成要求を生成する。通信なし。"""
import argparse
import json
import re
from pathlib import Path

PLAN = Path(__file__).with_name('context_recheck_rules.json')
DETECTOR_TYPE = 'settings/detector.regular_expression'
PLACEHOLDER = re.compile(r'\{\{([^{}]+)\}\}')


def materialize(plan, phase, customer, org_unit, run_tag, marker, resources):
    if not re.fullmatch(r'customers/C[A-Za-z0-9_-]+', customer):
        raise ValueError('顧客のリソース名は customers/C... 形式です')
    if not re.fullmatch(r'orgUnits/[A-Za-z0-9_-]+', org_unit):
        raise ValueError('組織部門のリソース名は orgUnits/... 形式です')
    if not re.fullmatch(r'[A-Za-z0-9-]{3,24}', run_tag):
        raise ValueError('試験名には英数字とハイフンを3〜24文字で指定してください')
    if not re.fullmatch(r'DLPVERIFY[A-Z]{8,24}', marker):
        raise ValueError('対照文字列には DLPVERIFY に続けて英大文字を8〜24文字指定してください')
    if phase not in ('detectors', 'rules'):
        raise ValueError('作成段階を指定してください')
    if not isinstance(resources, dict) or any(
        not isinstance(resource, str) or not re.fullmatch(r'policies/[A-Za-z0-9_-]+', resource)
        for resource in resources.values()
    ):
        raise ValueError('検知器の対応表は、定義のキーから policies/... への対応です')
    replacements = {
        'CUSTOMER_RESOURCE': customer,
        'ORG_UNIT_RESOURCE': org_unit,
        'ORG_UNIT_ID': org_unit.split('/', 1)[1],
        'RUN_TAG': run_tag,
        'RUN_MARKER': marker,
    }
    replacements.update({f'RESOURCE:{key}': resource for key, resource in resources.items()})

    def replace(match):
        key = match[1]
        if key not in replacements:
            raise ValueError('設定値・リソース対応が不足しています: ' + key)
        return replacements[key]

    selected = [
        entry for entry in plan['rules_and_detectors'] if entry['replay']
        and (entry['create_payload']['setting']['type'] == DETECTOR_TYPE) == (phase == 'detectors')
    ]
    return [{
        'key': entry['key'],
        'body': json.loads(PLACEHOLDER.sub(replace, json.dumps(entry['create_payload'], ensure_ascii=False))),
    } for entry in selected]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('detectors', 'rules'))
    parser.add_argument('--customer', required=True)
    parser.add_argument('--org-unit', required=True)
    parser.add_argument('--run-tag', required=True)
    parser.add_argument('--marker', required=True)
    parser.add_argument('--resources', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    resources = json.loads(args.resources.read_text(encoding='utf-8')) if args.resources else {}
    result = materialize(plan, args.phase, args.customer, args.org_unit, args.run_tag, args.marker, resources)
    with args.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write('\n')


if __name__ == '__main__':
    main()
