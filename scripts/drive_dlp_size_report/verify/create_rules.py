"""試験用の監査のみ DLP 規則2つ(AND 条件・OR 条件)を Cloud Identity Policy API で作る。
使い方: python3 create_rules.py --customer customers/C... --org-unit orgUnits/... [--tag 20261120]"""
import argparse
from common import call, save

MARK = 'DLPSIZEMARKQZRT'


def det(name):
    return (f"body.matches_dlp_detector('{name}', google.privacy.dlp.v2.Likelihood.POSSIBLE, "
            "{minimum_match_count: 1, minimum_unique_match_count: 1})")


ap = argparse.ArgumentParser(); ap.add_argument('--customer', required=True)
ap.add_argument('--org-unit', required=True); ap.add_argument('--tag', default='20261120')
a = ap.parse_args()
ou = a.org_unit.split('/', 1)[1]
rules = {
    f'DLPSIZE-{a.tag}-card-AND-confidential': f"body.contains('{MARK}') && body.contains('社外秘') && {det('CREDIT_CARD_NUMBER')}",
    f'DLPSIZE-{a.tag}-email-OR-handlewithcare': f"body.contains('{MARK}') && ({det('EMAIL_ADDRESS')} || body.contains('取扱注意'))",
}
out = {}
for name, cond in rules.items():
    out[name] = call('POST', 'https://cloudidentity.googleapis.com/v1beta1/policies', {
        'customer': a.customer,
        'policyQuery': {'orgUnit': a.org_unit,
                        'query': f"entity.org_units.exists(org_unit, org_unit.org_unit_id == orgUnitId('{ou}'))"},
        'setting': {'type': 'settings/rule.dlp', 'value': {
            'displayName': name, 'description': 'DLP×サイズ抽出(Apps Script)の動作確認用。架空データのみ。監査のみ。',
            'triggers': ['google.workspace.drive.file.v1.share'], 'condition': {'contentCondition': cond},
            'action': {'driveAction': {'auditOnly': {}}}, 'state': 'ACTIVE',
            'ruleTypeMetadata': {'dlpRuleMetadata': {'alertSeverity': 'LOW'}}}}})
    print(name, out[name].get('done'), out[name].get('_error'))
save('rule_create.json', out)
