#!/usr/bin/env python3
"""秘密データの条件証明・検証可能な計算に関する一次資料を取得する。"""
import concurrent.futures
import json
import download_privacy_materials as base
base.RAW=base.ROOT/'research/disclosures/raw/zero_knowledge_20261007'
base.RECORD=base.ROOT/'research/technology/zero_knowledge_sources_20261007.json'
SOURCES=[
 ('deco','DECO Liberating Web Data Using Decentralized Oracles for TLS','https://arxiv.org/pdf/1909.00938'),
 ('tlsnotary_faq','TLSNotary 通信内容の出所証明・選択開示','https://tlsnotary.org/docs/faq/'),
 ('tlsnotary_quickstart','TLSNotary 年齢条件等の公開例','https://tlsnotary.org/docs/quick_start/'),
 ('swiss_incident_2026','スイス連邦官房 2026年電子投票復号不能と措置','https://www.bk.admin.ch/de/newnsb/Py-Tle6KOgfLZ0xglFMEz'),
 ('longfellow_reviews','Longfellow 公開暗号監査・学術評価','https://google.github.io/longfellow-zk/docs/reviews/'),
 ('eu_recommendation_pdf','EU 2026/1035 年齢確認勧告 原文','https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A32026H1035'),
 ('google_age', 'Google Sparkasse 年齢証明 公開実装2025', 'https://blog.google/innovation-and-ai/technology/safety-security/opening-up-zero-knowledge-proof-technology-to-promote-privacy-in-age-assurance/'),
 ('eu_blueprint', 'EU 年齢証明 技術設計2026', 'https://digital-strategy.ec.europa.eu/en/factpages/blueprint-age-verification-solution-help-protect-minors-online'),
 ('eu_age_specs', 'EU Age Verification Technical Specification', 'https://github.com/eu-digital-identity-wallet/av-doc-technical-specification'),
 ('zkcnn', 'zkCNN Zero Knowledge Proofs for CNN Predictions and Accuracy', 'https://eprint.iacr.org/2021/673.pdf'),

 ('swiss_current', 'Swiss Federal Chancellery e-voting current trials', 'https://www.bk.admin.ch/en/e-voting'),
 ('ezkl_system', 'EZKL 推論・分析の証明と外部証明生成サービス', 'https://docs.ezkl.xyz/'),
 ('swiss_protocol_review', 'EPFL Swiss Post e-voting protocol analysis 2021', 'https://www.epfl.ch/labs/dedis/wp-content/uploads/2022/02/report-2021-3-kummer-ella_swisspostevoting.pdf'),
 ('medical_eligibility_code', '医療保険適格性証明の論文 公開実装', 'https://github.com/wwarodom/zk_code'),

 ('nist_zkp','NIST WPEC2024 Zero Knowledge Proofs 概説','https://csrc.nist.gov/csrc/media/presentations/2024/wpec2024-3b1/images-media/wpec2024-3b1-slides-akira-tjerand--ZKP-Overview.pdf'),
 ('nist_pec','NIST Privacy Enhancing Cryptography 技術の分類','https://csrc.nist.gov/Projects/pec/pec-tools'),
 ('edps_wallet','EDPS Digital Identity Wallets 2025-12-16','https://www.edps.europa.eu/system/files/2025-12/25-12-16_techdispatch-digital-identity-wallet_en.pdf'),
 ('eu_age','European Commission EU-wide Age Verification 2026','https://digital-strategy.ec.europa.eu/en/library/commission-sets-out-common-approach-eu-wide-age-verification-technologies'),
 ('w3c_bbs','W3C BBS Cryptosuites 2026-09-10 Candidate Recommendation Draft','https://www.w3.org/TR/2026/CRD-vc-di-bbs-20260910/'),
 ('ing_range','ING Zero Knowledge Range Proof 2017発表','https://ing.com/news/2020/07/blockchain-transactions-just-got-a-whole-lot-safer.html'),
 ('swiss_review','Swiss Federal Chancellery e-voting system examination','https://www.bk.admin.ch/en/examination-of-systems'),
 ('swiss_post','Swiss Post Electronic vote casting for Switzerland','https://www.post.ch/-/media/portal-opp/k/dokumente/positionspapiere/positionspapier-e-voting.pdf?hash=E60A68CB5D462C4025FF84DEBF5CC8B2&sc_lang=en&vs=6'),
 ('ezkl','EZKL 推論の正しさを証明する公開実装','https://github.com/zkonduit/ezkl'),
 ('ezkl_docs','EZKL 医療等の用途例 文書','https://github.com/zkonduit/ezkl-docs/blob/main/default.md'),
 ('zkllm','zkLLM Zero Knowledge Proofs for Large Language Models','https://arxiv.org/pdf/2404.16109'),
 ('zktorch','ZKTorch Compiling ML Inference to Zero Knowledge Proofs','https://arxiv.org/pdf/2507.07031'),
 ('zkml_survey','A Survey of Zero Knowledge Proof Based Verifiable Machine Learning','https://arxiv.org/pdf/2502.18535'),
 ('zkfl_health','zkFL-Health Blockchain Enabled Zero Knowledge Federated Learning for Medical AI Privacy','https://arxiv.org/pdf/2512.21048'),
 ('medical_eligibility','Privacy Preserving Health Insurance Eligibility Verification on Blockchain Using zk-SNARKs','https://www.mdpi.com/2410-387X/10/5/66'),
 ('medical_eligibility_pdf','Privacy Preserving Health Insurance Eligibility Verification PDF','https://www.mdpi.com/2410-387X/10/5/66/pdf'),
 ('erc7992','ERC7992 Verifiable ML Model Inference Draft','https://eips.ethereum.org/EIPS/eip-7992'),
 ('ethereum_rollups','Ethereum Zero knowledge rollups 説明','https://ethereum.org/developers/docs/scaling/zk-rollups/'),
 ('ethereum_privacy','Ethereum Privacy roadmap 2026','https://ethereum.org/roadmap/privacy'),
]
def main():
 base.RAW.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(base.fetch,SOURCES))
 previous=json.loads(base.RECORD.read_text()) if base.RECORD.exists() else {}
 previous.update(research_date='2026-10-07',note='原本・抽出本文はGit管理外。提供者発表、試用、研究、標準草案を区別する。',documents=records)
 base.RECORD.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
 for r in records:print(r['id'],r['status'],r.get('pages','HTML'),r.get('error',''),flush=True)
if __name__=='__main__':main()
