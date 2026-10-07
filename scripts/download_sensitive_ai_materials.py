#!/usr/bin/env python3
"""企業の機微データ利用・秘密計算の一次資料を取得する。"""
import concurrent.futures
import json
import urllib.parse
import download_privacy_materials as base

base.RAW = base.ROOT / 'research/disclosures/raw/enterprise_sensitive_ai_20261007'
base.RECORD = base.ROOT / 'research/technology/enterprise_sensitive_ai_sources_20261007.json'
SOURCES = [
 ('sensitivity_classical_benchmark','Benchmarking Classical and Transformer-Based Models for Document Sensitivity Classification','https://arxiv.org/pdf/2608.16928'),
 ('torchsight_local','Security Document Classification with a Fine-Tuned Local Large Language Model','https://arxiv.org/pdf/2605.20368'),
 ('sensitive_exposure_thesis', 'Threat Detection in Program Execution and Network Traffic 博士論文 第5章', 'https://vtechworks.lib.vt.edu/bitstream/handle/10919/71463/Shu_X_D_2016.pdf'),
 ('sensitivity_middleware_2026', 'A Privacy-Preserving Middleware Architecture for Detecting Prompt Injection and Sensitive Data Exposure in Large Language Model Interactions', 'https://www.preprints.org/manuscript/202607.1897'),
 ('purview_encrypted_processing', 'SharePoint OneDrive 保護文書の処理', 'https://learn.microsoft.com/en-us/purview/sensitivity-labels-sharepoint-onedrive-files'),

 ('privft', 'PrivFT: Private and Fast Text Classification with Homomorphic Encryption', 'https://arxiv.org/pdf/1908.06972'),
 ('bert_encrypted_classification', 'Privacy-Preserving Text Classification on BERT Embeddings with Homomorphic Encryption', 'https://arxiv.org/pdf/2210.02574'),
 ('mpc_text_classification', 'Privacy-Preserving Classification of Personal Text Messages with Secure Multi-Party Computation: An Application to Hate-Speech Detection', 'https://arxiv.org/pdf/1906.02325'),

 ('apple_he', 'Apple 機械学習と準同型暗号', 'https://machinelearning.apple.com/research/homomorphic-encryption'),
 ('edge_he', 'Microsoft Edge Password Monitor', 'https://www.microsoft.com/en-us/research/blog/password-monitor-safeguarding-passwords-in-microsoft-edge/'),

 ('fhe_llama', 'Scaling up Privacy-Preserving ML: A CKKS Implementation of Llama-2-7B', 'https://arxiv.org/pdf/2601.18511'),
 ('rosetta', 'ROSETTA: Efficient and Accurate Privacy-Preserving LLM Decoding via Hybrid CKKS/TFHE Evaluation', 'https://arxiv.org/pdf/2609.16915'),
 ('edbt_fhe', 'Private LLM Inference with Homomorphic Encryption', 'https://www.openproceedings.org/2026/conf/edbt/paper-T1.pdf'),
 ('microsoft_governance', 'Microsoft 社内 Copilot 情報管理', 'https://www.microsoft.com/insidetrack/blog/how-were-tackling-microsoft-365-copilot-governance-internally-at-microsoft/'),
 ('ntt_cases', '秘密計算活用事例集 第2版', 'https://secihi.ntt.com/lp/cases/秘密計算活用事例集.pdf'),
 ('ntt_overview', '秘密計算ガイドライン 概説編', 'https://secihi.ntt.com/lp/guideline/概説編.pdf'),
 ('ntt_process', '秘密計算ガイドライン 実現プロセス編', 'https://secihi.ntt.com/lp/guideline/秘密計算プロジェクトの実現プロセス編.pdf'),
 ('ntt_security', '秘密計算ガイドライン データ管理とセキュリティ編', 'https://secihi.ntt.com/lp/guideline/秘密計算におけるデータ管理とセキュリティ編.pdf'),
 ('ntt_checklist', '秘密計算サービスの個人情報保護法適合性チェックリスト', 'https://secihi.ntt.com/lp/guideline/秘密計算サービスの個人情報保護法適合性チェックリスト.pdf'),
 ('ntt_interop', '秘密計算技術における相互運用性確保に向けた基本方針', 'https://secihi.ntt.com/lp/guideline/秘密計算技術における相互運用性確保に向けた基本方針.pdf'),
 ('ntt_requirements', '秘密計算システムを活用したデータ共有のための推奨要件', 'https://secihi.ntt.com/lp/guideline/秘密計算システムを活用したデータ共有のための推奨要件.pdf'),
 ('melloddy_paper', 'Industry-scale orchestrated federated learning for drug discovery', 'https://arxiv.org/pdf/2210.08871'),
 ('microsoft_internal', 'Deploying Microsoft 365 Copilot in four chapters', 'https://www.microsoft.com/insidetrack/blog/uploads/prod/2024/10/Deploying-Microsoft-365-Copilot-in-four-chapters_EBOOK.pdf'),
 ('ntt_ai', '析秘MPC 分析AI 提供開始 2026-06-24', 'https://www.ntt.com/about-us/press-releases/news/article/2026/0624.html'),
 ('nict_2025_june', 'DeepProtect 不正口座検知 実証', 'https://www.nict.go.jp/press/2025/06/10-1.html'),
 ('nict_2025_july', 'DeepProtect eFL-Boost 不正送金検知 実証', 'https://www.nict.go.jp/press/2025/07/22-1.html'),
 ('nict_structure', 'DeepProtect 暗号化差分による連合学習', 'https://deepprotect.nict.go.jp/'),
 ('intesa_fhe', 'Intesa Sanpaolo IBM FHE 実証', 'https://www.ibm.com/case-studies/blog/intesa-sanpaolo-ibm-secure-digital-transactions-fhe'),
 ('apple_pcc', 'Private Cloud Compute 原設計', 'https://security.apple.com/blog/private-cloud-compute/'),
 ('apple_2026', 'Expanding Private Cloud Compute 2026-06-08', 'https://security.apple.com/blog/expanding-pcc/'),
 ('google_2026', 'Confidential Computing 2026-06-23', 'https://cloud.google.com/blog/products/identity-security/verifiable-trust-in-the-ai-era-whats-new-in-confidential-computing'),
 ('morgan_debrief', 'Morgan Stanley Debrief 導入', 'https://www.morganstanley.com/press-releases/ai-at-morgan-stanley-debrief-launch'),
 ('bbva_2026', 'BBVA 全社AI利用事例', 'https://openai.com/index/bbva/'),
 ('avilen_mask', '国内大手銀行 機密情報マスキング', 'https://avilen.co.jp/ai-case-article/finance-data-masking-ai/'),
 ('aws_redaction', 'Bedrock Data Automation と Guardrails 個人情報削除の構成例', 'https://aws.amazon.com/blogs/machine-learning/detect-and-redact-personally-identifiable-information-using-amazon-bedrock-data-automation-and-guardrails/'),
 ('openai_data', 'OpenAI API データ保持条件', 'https://developers.openai.com/api/docs/guides/your-data'),
 ('openai_private', 'OpenAI Private Safety Processing', 'https://developers.openai.com/api/docs/guides/private-safety-processing'),
]

def main():
    base.RAW.mkdir(parents=True, exist_ok=True)
    encoded = [(i,t,urllib.parse.quote(u, safe=':/?=&%')) for i,t,u in SOURCES]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(base.fetch, encoded))
    base.RECORD.write_text(json.dumps({'research_date':'2026-10-07', 'note':'原本・抽出本文はGit管理外。公開一次資料の発表内容であり独立監査ではない。', 'documents':records},ensure_ascii=False,indent=2)+'\n')
    for r in records:
        print(r['id'], r['status'], r.get('pages','HTML'),r.get('error',''), flush=True)
if __name__ == '__main__':
    main()
