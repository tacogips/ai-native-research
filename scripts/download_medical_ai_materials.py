#!/usr/bin/env python3
"""医療データのローカル・外部LLM利用に関する公開一次資料を保存する。"""
import concurrent.futures
import json
import download_privacy_materials as base
base.RAW = base.ROOT / 'research/disclosures/raw/medical_llm_20261007'
base.RECORD = base.ROOT / 'research/technology/medical_llm_sources_20261007.json'
SOURCES = [
 ('korean_bert_comparison','Korean medical de-identification BERT LLM comparison','https://www.nature.com/articles/s44401-025-00036-1.pdf'),
 ('stanford_journal_pmc','Stanford Secure基盤 査読済論文2025 PMC本文','https://pmc.ncbi.nlm.nih.gov/articles/PMC11833461/'),
 ('imperial_pmc','Imperial退院要約 論文PMC全文','https://pmc.ncbi.nlm.nih.gov/articles/PMC13379688/'),
 ('stanford_journal','Stanford Secure基盤 査読済論文2025','https://academic.oup.com/jamia/article/32/3/586/7979332'),
 ('imperial_accepted','Imperial退院要約 著者受理原稿','https://s3.ca-central-1.amazonaws.com/assets.jmir.org/assets/preprints/preprint-88816-accepted.pdf'),
 ('mhlw_overview', '厚生労働省 安全管理 第7.0版 概説編', 'https://www.mhlw.go.jp/content/10808000/001716290.pdf'),
 ('mhlw_planning', '厚生労働省 安全管理 第7.0版 企画管理編', 'https://www.mhlw.go.jp/content/10808000/001716292.pdf'),
 ('mhlw_operations', '厚生労働省 安全管理 第7.0版 システム運用編', 'https://www.mhlw.go.jp/content/10808000/001716295.pdf'),
 ('mhlw_qa', '厚生労働省 安全管理 Q&A 2026年9月', 'https://www.mhlw.go.jp/content/10808000/001752355.pdf'),

 ('local_small_html', 'Small Large Language Models in the Hospital 論文HTML', 'https://www.jmir.org/2026/1/e86453/'),
 ('imperial_sde_html', 'Imperial 医療要約の保護環境 論文HTML', 'https://ai.jmir.org/2026/1/e88816/'),
 ('hhs_deid', '米国HHS PHI非識別化の指針', 'https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/understanding/coveredentities/De-identification/hhs_deid_guidance.pdf'),
 ('mhlw_medical_security', '厚生労働省 医療情報システムの安全管理ガイドライン 第7.0版 公開ページ', 'https://www.mhlw.go.jp/stf/shingi/0000516275_00006.html'),

 ('stanford_secure','Development of Secure Infrastructure for Advancing Generative AI Research in Healthcare at an Academic Medical Center','https://pmc.ncbi.nlm.nih.gov/articles/PMC11469521/'),
 ('oncology_pipeline','A software pipeline for medical information extraction with large language models, open source and suitable for oncology','https://www.nature.com/articles/s41698-025-01103-4'),
 ('oncology_pipeline_pdf','A software pipeline for medical information extraction with large language models, open source and suitable for oncology PDF','https://www.nature.com/articles/s41698-025-01103-4.pdf'),
 ('llm_anonymizer','Deidentifying Medical Documents with Local, Privacy-Preserving Large Language Models: The LLM-Anonymizer','https://ai.nejm.org/doi/full/10.1056/AIdbp2400537'),
 ('llm_anonymizer_preprint','LLM-Anonymizer 2024年公開原稿','https://www.medrxiv.org/content/10.1101/2024.06.11.24308355v1.full.pdf'),
 ('local_small','Small Large Language Models in the Hospital','https://www.jmir.org/2026/1/e86453/PDF'),
 ('imperial_sde','Real-World Implementation of Large Language Models for Writing Clinical Discharge Summaries Within a Secure Data Environment','https://ai.jmir.org/2026/1/e88816/PDF'),
 ('urology_privacy','Privacy-by-Design Framework for Large Language Model Chatbots in Urology','https://pmc.ncbi.nlm.nih.gov/articles/PMC12688312/'),
 ('multimodal_anonymizer','The Multimodal Anonymizer: a fully local multi-agent AI system for medical data deidentification v2','https://www.medrxiv.org/content/10.64898/2026.05.28.26353952v2.full.pdf'),
 ('temporal_phi','Leveraging Large Language Models for Temporal PHI De-identification in Real-World Clinical Notes','https://www.medrxiv.org/content/10.64898/2026.09.22.26360316v1.full.pdf'),
 ('yokosuka','横須賀共済病院 生成AI医療文書作成','https://www.txpmedical.jp/case-study/sbir-ai-1-ai/'),
 ('fujita','藤田医科大学 退院サマリー作成支援','https://www.fujita-hu.ac.jp/news/vsfo8q000000286b.html'),
 ('deidentifier_code','KatherLab 医療文書非識別化 公開実装','https://github.com/KatherLab/deidentifier'),
]
def main():
 base.RAW.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(base.fetch,SOURCES))
 previous=json.loads(base.RECORD.read_text()) if base.RECORD.exists() else {}
 previous.update(research_date='2026-10-07',note='公開原本と抽出本文はGit管理外。査読前原稿・提供者事例・研究実装を区別する。',documents=records)
 base.RECORD.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n')
 for r in records: print(r['id'],r['status'],r.get('pages','HTML'),r.get('error',''),flush=True)
if __name__=='__main__': main()
