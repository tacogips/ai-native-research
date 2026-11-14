#!/usr/bin/env python3
"""ランサムウェアの被害・動向を扱う公開資料と抽出本文を保存する。"""
import concurrent.futures
import json
import download_privacy_materials as base
SOURCES = [
 ('ukg_2021_esg_uk','UKG2021年報告英国配布版','https://www.ukg.co.uk/sites/default/files/2022-06/UKG_2021_ESG_Report_Final-6-24-22_2.pdf'),
 ('uhg_2024_results','UHG2024年決算とサイバー攻撃費用','https://www.unitedhealthgroup.com/content/dam/UHG/PDF/investors/2024/2025-16-01-uhg-reports-fourth-quarter-results.pdf'),
 ('uhg_2025_results','UHG2025年決算と追加費用','https://www.unitedhealthgroup.com/content/dam/UHG/PDF/investors/2025/unh-reports-2025-results-and-issues-2026-outlook.pdf'),
 ('ukg_2021_esg','UKG2021年報告・事件からの復旧','https://www.ukg.com/sites/default/files/2024-06/2021-UKG-ESG-Report.pdf'),
 ('sophos_2023_blog','Sophos2023年調査の解説','https://www.sophos.com/en-us/blog/the-state-of-ransomware-2023'),
 ('sophos_2024_press','Sophos2024年調査公表','https://www.sophos.com/en-us/press/press-releases/2024/04/ransomware-payments-increase-500-last-year-finds-sophos-state'),
 ('bridgestone_2022','ブリヂストン米州事件2022年3月18日','https://www.bridgestone.co.jp/corporate/news/2022031801.html'),
 ('synnovis_parliament_2026','Synnovis患者安全影響の英国政府答弁','https://questions-statements.parliament.uk/written-questions/detail/2026-06-26/13479'),
 ('npa_2024','警察庁2024年情勢','https://www.npa.go.jp/publications/statistics/cybersecurity/data/R6/R06_cyber_jousei.pdf'),
 ('npa_2025h1','警察庁2025年上半期情勢','https://www.npa.go.jp/publications/statistics/cybersecurity/data/R7kami/R07_kami_cyber_jyosei.pdf'),
 ('dbir_2024','Verizon DBIR 2024','https://www.verizon.com/business/resources/reports/2024-dbir-data-breach-investigations-report.pdf'),
 ('dbir_2025','Verizon DBIR 2025','https://www.verizon.com/business/resources/reports/2025-dbir-data-breach-investigations-report.pdf'),
 ('ic3_2022','FBI IC3 2022年報告','https://www.ic3.gov/AnnualReport/Reports/2022_IC3Report.pdf'),
 ('ic3_2023','FBI IC3 2023年報告','https://www.ic3.gov/AnnualReport/Reports/2023_IC3Report.pdf'),
 ('ic3_2024','FBI IC3 2024年報告','https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf'),
 ('handa_main','半田病院調査報告書','https://www.handa-hospital.jp/topics/2022/0616/report_01.pdf'),
 ('handa_technical','半田病院調査報告書技術編','https://www.handa-hospital.jp/topics/2022/0616/report_02.pdf'),
 ('osaka_report','大阪急性期・総合医療センター調査報告書','https://www.gh.opho.jp/pdf/report_v01.pdf'),
 ('nagoya_port','名古屋港NUTS障害経緯報告','https://meikoukyo.com/wp-content/uploads/2023/07/0bb9d9907568e832da8f400e529efc99.pdf'),
 ('synnovis_nhs','NHS Synnovis事件の説明','https://www.england.nhs.uk/synnovis-cyber-incident/questions-and-answers/'),
 ('synnovis_june20','NHS Synnovis診療影響2024年6月20日','https://www.england.nhs.uk/london/2024/06/20/update-on-cyber-incident-clinical-impact-in-south-east-london-thursday-20-june/'),
 ('ms_parliament','M&S英国議会証言2025年7月8日','https://committees.parliament.uk/oralevidence/16268/html/'),
 ('ms_results_2025','M&S2025年決算時の損失見積もり','https://corporate.marksandspencer.com/sites/marksandspencer/files/05-2025/fy25-rns.pdf'),
 ('ms_halfyear_2025','M&S2025年中間決算','https://corporate.marksandspencer.com/newsroom/press-releases/half-year-results-26-weeks-ended-27-september-2025'),
 ('sophos_2022_press','Sophos2022年調査公表','https://www.sophos.com/en-us/press/press-releases/2022/04/ransomware-hit-66-percent-of-organizations-surveyed-for-sophos-annual-state-of-ransomware-2022'),
 ('sophos_2026_jp','Sophos2026年調査日本語公表','https://www.sophos.com/ja-jp/press/press-releases/2026/07/79-percent-ransomware-attacks-originate-from-compromised-identities'),
 ('ai_ransomware_paper','Ransomware attacks in the context of generative artificial intelligence—an experimental study','https://link.springer.com/article/10.1365/s43439-023-00094-x'),
 ('ai_ransomware_paper_pdf','同論文の公開PDF','https://link.springer.com/content/pdf/10.1365/s43439-023-00094-x.pdf'),
 ('google_ai_2026','Google GTIG AI悪用観測2026年2月','https://cloud.google.com/blog/topics/threat-intelligence/distillation-experimentation-integration-ai-adversarial-use'),
 ('google_ai_2026_sep','Google GTIG AI悪用観測2026年9月','https://cloud.google.com/blog/topics/threat-intelligence/from-prompting-to-autonomy-the-evolution-of-adversarial-ai'),
 ('chatgpt_launch','ChatGPT公開日','https://openai.com/index/chatgpt/'),
 ('npa_2021','警察庁2021年情勢','https://www.npa.go.jp/publications/statistics/cybersecurity/data/R03_cyber_jousei.pdf'),
 ('npa_2022','警察庁2022年情勢','https://www.npa.go.jp/publications/statistics/cybersecurity/data/R04_cyber_jousei.pdf'),
 ('npa_2023','警察庁2023年情勢','https://www.npa.go.jp/publications/statistics/cybersecurity/data/R5/R05_cyber_jousei.pdf'),
 ('npa_2025','警察庁2025年情勢','https://www.npa.go.jp/publications/statistics/cybersecurity/data/R7/R07_cyber_jousei.pdf'),
 ('npa_2026h1','警察庁2026年上半期情勢','https://www.npa.go.jp/publications/statistics/cybersecurity/data/R8kami/R08_kami_cyber_jousei.pdf'),
 ('npa_index','警察庁年次情勢の一覧','https://www.npa.go.jp/publications/statistics/cybersecurity/'),
 ('dbir_2022','Verizon DBIR 2022','https://www.verizon.com/business/resources/reports/2022-dbir-data-breach-investigations-report.pdf'),
 ('dbir_2023','Verizon DBIR 2023','https://www.verizon.com/business/resources/reports/2023-data-breach-investigations-report-dbir.pdf'),
 ('dbir_2026','Verizon DBIR 2026','https://www.verizon.com/business/resources/T1e0/reports/2026-dbir-data-breach-investigations-report.pdf'),
 ('dbir_2026_index','Verizon DBIR 2026案内','https://www.verizon.com/business/resources/reports/dbir/'),
 ('sophos_2026','Sophos State of Ransomware 2026解説','https://www.sophos.com/en-us/blog/sophos-state-of-ransomware-2026'),
 ('sophos_2025_pdf','Sophos State of Ransomware 2025','https://assets.sophos.com/X24WTUEQ/at/9brgj5n44hqvgsp5f5bqcps/sophos-state-of-ransomware-2025.pdf'),
 ('sophos_active_2025','Sophos Active Adversary 2025','https://news.sophos.com/wp-content/uploads/2025/04/It-Takes-Two-2025-Sophos-Active-Adversary-Report.pdf'),
 ('chainalysis_2026','Chainalysis 2026年ランサムウェア分析','https://www.chainalysis.com/blog/crypto-ransomware-2026/'),
 ('chainalysis_2025','Chainalysis 2025年ランサムウェア分析','https://www.chainalysis.com/blog/crypto-crime-ransomware-victim-extortion-2025/'),
 ('ncsc_2024','NCSC AIの脅威への短期影響2024','https://www.ncsc.gov.uk/report/impact-of-ai-on-cyber-threat'),
 ('ncsc_2025','NCSC 2027年までのAIの脅威への影響','https://www.ncsc.gov.uk/pdfs/report/impact-ai-cyber-threat-now-2027.pdf'),
 ('ic3_2025','FBI IC3 2025年報告','https://www.ic3.gov/AnnualReport/Reports/2025_IC3Report.pdf'),
]
def main():
 base.RAW=base.ROOT/'research/disclosures/raw/ransomware_20261008'
 base.RAW.mkdir(parents=True,exist_ok=True)
 target=base.ROOT/'research/technology/ransomware_sources_20261008.json'
 existing=json.loads(target.read_text())['documents'] if target.exists() else []
 known={r['id'] for r in existing}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  records=list(pool.map(base.fetch,[s for s in SOURCES if s[0] not in known]))
 for r in records:
  if r.get('text_file'):
   text=(base.ROOT/r['text_file']).read_text()
   if 'Pardon Our Interruption' in text or 'Incapsula incident ID' in text:
    r.update(status='取得失敗',error='資料本文ではなくアクセス遮断画面')
 target.write_text(json.dumps({'research_date':'2026-10-08','period_start':'2021-10-08','period_end':'2026-10-08','raw_storage':str(base.RAW.relative_to(base.ROOT)),'note':'公開資料のみ。観測年と発行年、件数・被害割合・費用・支払額、AI利用の観測と因果推論を区別する。原本・抽出本文はGit管理外。既存取得記録を保持し未取得IDのみ追加。','documents':existing+records},ensure_ascii=False,indent=2)+'\n')
 for r in records:print(r['id'],r['status'],r.get('pages'),r.get('text_characters'),r.get('error',''),flush=True)
if __name__=='__main__':main()
