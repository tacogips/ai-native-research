#!/usr/bin/env python3
"""機密情報管理の新興企業・投資会社の公開一次資料を保存する。"""
import concurrent.futures
import json
import download_privacy_materials as base

SOURCES = [
 ('yc_strac','YC Strac採択情報','https://www.ycombinator.com/companies/strac'),
 ('strac_product','Strac AI利用の統制','https://www.strac.io/ai-governance'),
 ('strac_seed','Strac資金調達の会社説明','https://www.ycombinator.com/companies/strac/jobs'),
 ('fuse_strac','FUSE投資先Strac','https://careers.fuse.vc/companies/strac'),
 ('yc_candor','YC Candor Security採択情報','https://www.ycombinator.com/companies/candor-security'),
 ('candor_product','Candor Security製品・処理環境','https://candor.security/'),
 ('yc_superagent','YC Superagent採択情報','https://www.ycombinator.com/companies/superagent'),
 ('superagent_product','Superagent現行製品','https://www.superagent.sh/'),
 ('yc_promptarmor','YC PromptArmor採択情報','https://www.ycombinator.com/companies/promptarmor'),
 ('promptarmor_product','PromptArmor現行製品','https://www.promptarmor.com/'),
 ('yc_compliant','YC compliant-llm採択情報','https://www.ycombinator.com/companies/compliant-llm'),
 ('compliant_product','CompliantLLM公式サイト','https://www.compliantllm.com/'),
 ('yc_deal','YC標準投資条件','https://www.ycombinator.com/deal'),
 ('harmonic_product','Harmonic Security製品','https://www.harmonic.security/'),
 ('harmonic_about','Harmonic Security会社沿革','https://www.harmonic.security/about'),
 ('n47_harmonic','N47のHarmonic Security投資発表','https://www.n47.com/insights/data-protection-in-the-age-of-ai-next47-leads-harmonic-securitys-series-a'),
 ('teleskope_about','Teleskope会社沿革','https://www.teleskope.ai/company/about'),
 ('teleskope_product','Teleskope Data Reasoning Layer','https://www.teleskope.ai/products/data-reasoning-layer'),
 ('teleskope_funding','Teleskope 2500万米ドル調達発表','https://www.businesswire.com/news/home/20251031409379/en/Teleskope-Raises-%2425-Million-to-Accelerate-Adoption-of-the-Industrys-First-Agentic-Data-Security-Platform'),
 ('m13_teleskope','M13のTeleskope投資説明','https://www.m13.co/article/meet-teleskope-moving-data-security-from-alerts-to-remediation'),
 ('sentra_funding','SentraシリーズB調達発表','https://sentra.io/news/sentra-closes-50-million-series-b-amid-surging-demand-for-securing-data-for-ai-adoption'),
 ('sentra_ai','Sentra Copilot・Gemini向けデータ管理','https://sentra.io/learn/evaluate-dspm-dlp-copilot-gemini'),
 ('confident_product','Confident Security製品','https://confident.security/'),
 ('confident_sdk','Confident Security Python SDKと検証設定','https://docs.confident.security/sdks/python'),
 ('confident_funding','Confident Security OpenPCC・500万米ドル調達','https://www.businesswire.com/news/home/20251105013372/en/Confident-Security-Launches-OpenPCC-an-Open-Source-Standard-that-Protects-Data-Shared-with-AI-Models'),
 ('almure_company','Almureシード調達の会社発表','https://prtimes.jp/main/html/rd/p/000000004.000179806.html'),
 ('genesia_almure','Genesia VenturesのAlmure投資発表','https://www.genesiaventures.com/investment-almure/'),
 ('acompany_equity','Acompany 11億円シリーズB','https://www.acompany.tech/news/25-0514-1'),
 ('acompany_debt','Acompany 9.6億円融資調達','https://prtimes.jp/main/html/rd/p/000000130.000046917.html'),
 ('bonfy_product','Bonfy.AI現行製品と連携先','https://www.bonfy.ai/'),
 ('bonfy_seed','Bonfy.AI公開開始・シード調達発表','https://blog.bonfy.ai/news-room/press-release-bonfy.ai-launches-from-stealth-to-guard-against-genai-risks-with-adaptive-content-security-platform'),
 ('tlv_bonfy','TLV PartnersのBonfy.AI投資理由','https://www.tlv.partners/why-we-invested-in-bonfy/'),
 ('kiteworks_bonfy','KiteworksによるBonfy.AI買収発表','https://www.kiteworks.com/company/press-releases/kiteworks-acquires-bonfy-ai/'),
 ('cyberhaven_funding','Cyberhaven 1億米ドルシリーズD','https://www.cyberhaven.com/press-releases/cyberhaven-raises-100-million-series-d-at-1-billion-valuation'),
 ('nightfall_funding','Nightfall AI 4000万米ドルシリーズB','https://www.nightfall.ai/blog/nightfall-ai-raises-40-million-series-b-to-expand-cloud-data-protection-platform'),
 ('prompt_security_acquisition','SentinelOneのPrompt Security買収契約発表','https://www.sentinelone.com/press/sentinelone-to-acquire-prompt-security-to-advance-genai-security/'),
 ('sentinelone_annual','SentinelOne年次報告書・買収完了日','https://www.sec.gov/Archives/edgar/data/1583708/000158370826000035/sentineloneincfy2026annuala.pdf'),
 ('eaglys_partnership','EAGLYS BIPROGY資本業務提携','https://eaglys.co.jp/resource/news/250904'),
 ('biprogy_pdf','BIPROGY EAGLYS資本業務提携発表PDF','https://www.biprogy.com/pdf/news/nr_250904.pdf'),
]

def main():
 base.RAW = base.ROOT/'research/disclosures/raw/startup_sensitive_data_20261007'
 base.RAW.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  records = list(pool.map(base.fetch,SOURCES))
 target = base.ROOT/'research/technology/sensitive_data_startup_sources_20261007.json'
 target.write_text(json.dumps({'research_date':'2026-10-07','raw_storage':str(base.RAW.relative_to(base.ROOT)), 'note':'会社、YC、投資会社、買収企業、SECの公表資料。会社による製品説明は独立した性能評価ではない。資金調達の公表日とページ更新日を区別する。原本・抽出本文はGit管理外。','documents':records},ensure_ascii=False,indent=2)+'\n')
 for record in records:
  print(record['id'],record['status'],record.get('pages','HTML'),record.get('text_characters',''),record.get('error',''),flush=True)

if __name__ == '__main__':
 main()
