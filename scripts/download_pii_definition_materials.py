#!/usr/bin/env python3
"""PII定義の一次資料と取得記録を保存する。既存の原本は再利用する。"""
import concurrent.futures
import json
import download_privacy_materials as base

SOURCES = [
    ('ppc_definition_html', '個人情報保護委員会 通則編', 'https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/'),
    ('ppc_loan_example', '個人情報保護委員会 住宅ローン残高の照合例', 'https://www.ppc.go.jp/all_faq_index/faq2-q2-2/'),
    ('nist_pii', 'NIST SP 800-122', 'https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-122.pdf'),
    ('ec_personal_data', '欧州委員会 個人データの解説', 'https://commission.europa.eu/law/law-topic/data-protection/data-protection-explained_en'),
    ('ccpa_ag', 'California司法長官 CCPA解説', 'https://oag.ca.gov/privacy/ccpa'),
    ('ccpa_statute', 'California Civil Code 1798.140', 'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.140.&lawCode=CIV'),
    ('hhs_deidentification', 'HHS HIPAA非識別化指針', 'https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/understanding/coveredentities/De-identification/hhs_deid_guidance.pdf'),
    ('hhs_deidentification_html', 'HHS HIPAA非識別化指針 HTML版', 'https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html'),
]

if __name__ == '__main__':
    base.RAW = base.ROOT / 'research/disclosures/raw/pii_20261008'
    base.RAW.mkdir(parents=True, exist_ok=True)
    old = json.loads((base.ROOT / 'research/disclosures/privacy_retrieval_20261007.json').read_text())
    reused = [dict(r, reused_from='research/disclosures/privacy_retrieval_20261007.json') for r in old['documents'] if r['id'] in ('ppc_general', 'ppc_anonymization', 'gdpr', 'gdpr_ja', 'gdpr_preface_ja')]
    target = base.ROOT / 'research/technology/pii_definition_sources_20261008.json'
    prior = json.loads(target.read_text())['documents'] if target.exists() else []
    saved = {r['id']: r for r in prior if r.get('status') == '取得済み' and (base.ROOT / r.get('local_file', '')).is_file()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        fetched = list(pool.map(base.fetch, [s for s in SOURCES if s[0] not in saved]))
    by_id = {r['id']: r for r in fetched}
    records = [saved[s[0]] if s[0] in saved else by_id[s[0]] for s in SOURCES]
    target.write_text(json.dumps({'as_of': '2026-10-08', 'note': '原本と抽出本文はGit管理外。法令本文と説明資料を区別。取得失敗も記録。', 'documents': reused + records}, ensure_ascii=False, indent=2) + '\n')
    for rec in records:
        print(rec['id'], rec.get('status'), rec.get('pages', ''), rec.get('error', ''))
