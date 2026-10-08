#!/usr/bin/env python3
"""大規模な個人情報事故の公表資料を保存する。漏えいした個人データは取得しない。"""
import concurrent.futures
import json
import download_privacy_materials as base

SOURCES = [
 ('moneyforward_first','Money Forward GitHub不正アクセス第一報','https://corp.moneyforward.com/news/info/20260501-mf-press-1/'),
 ('moneyforward_second','Money Forward GitHub調査・安全性確認第二報','https://corp.moneyforward.com/news/info/20260511-mf-press-1/'),
 ('moneyforward_third','Money Forward銀行連携の順次再開第三報','https://corp.moneyforward.com/news/info/20260512-mf-press-1/'),
 ('moneyforward_fourth','Money Forward調査完了・再発防止第四報','https://corp.moneyforward.com/news/info/20260623-mf-press-1/'),
 ('moneyforward_faq','Money Forward ME GitHub事件の質問と回答','https://support.me.moneyforward.com/hc/ja/articles/57548547365145'),
 ('moneyforward_bank_resume','Money Forward銀行連携の再開状況','https://toho.x.moneyforward.com/faq/24'),
 ('ntt_ppc','NTTグループ不正持出し・PPC詳細調査','https://www.ppc.go.jp/files/pdf/240124_houdou.pdf'),
 ('ntt_followup','PPC勧告等に対する是正状況','https://www.ppc.go.jp/files/pdf/240911_shiryou-2-2.pdf'),
 ('line_incident','LINEヤフー影響範囲の最終調査','https://www.lycorp.co.jp/ja/news/announcements/007712/'),
 ('line_remediation','LINEヤフー再発防止策の実施結果・2026年7月','https://www.lycorp.co.jp/ja/privacy-security/recurrence-prevention/ppc/'),
 ('line_complete','LINEヤフー当局への報告完了・2026年7月','https://www.lycorp.co.jp/ja/news/announcements/020659/'),
 ('toyota_incident','トヨタ215万人のクラウド公開設定','https://global.toyota/jp/newsroom/corporate/39174380.html'),
 ('toyota_remediation','トヨタ再発防止策','https://global.toyota/jp/newsroom/corporate/39529198.html'),
 ('toyota_ppc','トヨタPPC行政対応','https://www.ppc.go.jp/files/pdf/230712_01_houdou.pdf'),
 ('kadokawa_report','KADOKAWA調査・影響範囲・2024年8月','https://group.kadokawa.co.jp/information/media-download/1356/d3f77b589c58d083/'),
 ('iseto_report','イセトー調査完了・原因と再発防止','https://www.iseto.co.jp/news/news_202410.html'),
 ('iseto_ppc','イセトーPPC詳細調査・2025年3月','https://www.ppc.go.jp/files/pdf/250319_houdou.pdf'),
 ('askul_report','アスクル調査結果・原因と再発防止・2025年12月','https://pdf.irpocket.com/C0032/PDLX/O3bg/N4O3.pdf'),
 ('asahi_report','アサヒ原因と再発防止・2026年2月','https://www.asahigroup-holdings.com/en/newsroom/detail/20260218-0101.html'),
 ('asahi_update','アサヒ影響範囲更新・2026年7月','https://www.asahigroup-holdings.com/en/newsroom/detail/20260717-0201.html'),
 ('kaikatsu_report','快活フロンティア最終調査・再発防止','https://www.kaikatsu.jp/info/detail/ddos.html'),
 ('kaikatsu_pdf','快活フロンティア第五報PDF','https://kaikatsufrontier.co.jp/release/442651d2bbc1f4eb782ef496d1e3349c_2.pdf'),
 ('amagasaki_report','尼崎市USB紛失・第三者調査報告','https://www.city.amagasaki.hyogo.jp/_res/projects/default_project/_page_/001/030/947/1128houkokusyo.pdf'),
 ('amagasaki_response','尼崎市調査後の市の対応','https://www.city.amagasaki.hyogo.jp/_res/projects/default_project/_page_/001/030/947/221128.pdf'),
 ('robinhood_notice','Robinhood 2021年11月事故公表','https://investors.robinhood.com/static-files/f15cea1a-1fd4-4634-b2a4-3b7523b48c11'),
 ('robinhood_sec','Robinhood SEC 2025年調査結果','https://www.sec.gov/newsroom/press-releases/2025-5'),
 ('optus_oaic','Optus OAIC調査・提訴と改善の指針','https://www.oaic.gov.au/news/media-centre/australian-information-commissioner-takes-civil-penalty-action-against-optus'),
 ('medibank_oaic','Medibank OAIC提訴','https://www.oaic.gov.au/news/media-centre/oaic-takes-civil-penalty-action-against-medibank'),
 ('medibank_statement','Medibank規制当局の裁判所提出資料','https://www.oaic.gov.au/__data/assets/pdf_file/0025/221974/Australian-Information-Commissioner-v-Medibank-Private-Limited-concise-statement.pdf'),
 ('medibank_review','Medibank Deloitte事後調査の説明','https://www.medibank.com.au/livebetter/newsroom/post/cybercrime-update-deloitte-incident-review'),
 ('tmobile_notice','T-Mobile 2023年事故公表','https://www.t-mobile.com/news/business/customer-information'),
 ('tmobile_scope','T-Mobile 2024年第1四半期報告書・3700万アカウント','https://investor.t-mobile.com/files/doc_financials/2024/q1/Q1-2024-10-Q_vFinal.pdf'),
 ('tmobile_fcc','FCC T-Mobile再発防止合意','https://docs.fcc.gov/public/attachments/DOC-405937A1.pdf'),
 ('tmobile_order','FCC T-Mobile合意本文','https://docs.fcc.gov/public/attachments/DA-24-860A1.pdf'),
 ('genetic_ico','23andMe ICO調査結果','https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2025/06/23andme-fined-for-failing-to-protect-uk-users-genetic-data/'),
 ('genetic_opc','23andMe英加共同調査全文','https://www.priv.gc.ca/en/opc-actions-and-decisions/investigations/investigations-into-businesses/2025/pipeda-2025-001/'),
 ('genetic_penalty','23andMe ICO制裁通知全文','https://ico.org.uk/media2/kclbljpo/23andme-penalty-notice.pdf'),
 ('capita_ico','Capita ICO原因分析','https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2025/10/capita-fined-14m-for-data-breach-affecting-over-6m-people/'),
 ('capita_penalty','Capita ICO制裁通知全文','https://ico.org.uk/media2/pv5nhks4/capita-plc-and-cpsl-monetary-penalty-notice.pdf'),
 ('moveit_advisory','CISA FBI MOVEit脆弱性・対策勧告','https://content.govdelivery.com/accounts/USDHSCISA/bulletins/35ecb08'),
 ('moveit_louisiana','Louisiana MOVEit事故・対応経緯FAQ','https://nextsteps.la.gov/faqs/'),
 ('moveit_omv','Louisiana OMV事故公表','https://www.expresslane.la.gov/omv/alerts/'),
 ('change_hhs','Change Healthcare HHS・影響人数更新','https://www.hhs.gov/hipaa/for-professionals/special-topics/change-healthcare-cybersecurity-incident-frequently-asked-questions/index.html'),
 ('change_testimony','UnitedHealth Group CEO議会証言','https://d1dth6e84htgma.cloudfront.net/Witty_Testimony_OI_Hearing_05_01_24_5ff52a2d11.pdf'),
 ('att_filing','AT&T 2024年7月SEC届出','https://www.sec.gov/Archives/edgar/data/732717/000073271724000046/t-20240506.htm'),
 ('snowflake_investigation','Mandiant Snowflake顧客侵害の調査','https://cloud.google.com/blog/topics/threat-intelligence/unc5537-snowflake-data-theft-extortion?hl=en'),
 ('france_initial','France Travail 2024年初報・4300万人の可能性','https://www.cnil.fr/fr/france-travail-la-cnil-enquete-sur-la-fuite-de-donnees-et-donne-des-conseils-pour-se-proteger'),
 ('france_cnil','France Travail CNIL 2026年原因分析・制裁','https://www.cnil.fr/en/data-breach-5million-fine-france-travail'),
 ('france_response','France Travail CNIL制裁への対応','https://www.francetravail.org/accueil/communiques/2026/france-travail-prend-acte-de-la-sanction-de-la-cnil-et-rappelle-que-la-cybersecurite-et-la-protection-des-donnees-sont-des-enjeu.html?type=article'),
 ('skt_korean','SK Telecom PIPC韓国語原文','https://pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS074&nttId=11453'),
 ('skt_english','SK Telecom PIPC英訳','https://pipc.go.kr/eng/user/ltn/new/noticeDetail.do?bbsId=BBSMSTR_000000000001&nttId=2877'),
 ('coupang_pipc','Coupang PIPC 2026年6月最終調査・制裁','https://pipc.go.kr/eng/user/ltn/new/noticeDetail.do?bbsId=null&nttId=3071'),
 ('coupang_msit','Coupang MSIT技術調査・2026年2月','https://msit.go.kr/eng/bbs/view.do?bbsSeqNo=42&mId=4&mPid=2&nttSeqNo=1221&sCode=eng'),
 ('library_report','British Library公開事後調査・18頁','https://www.bl.uk/home/british-library-cyber-incident-review-8-march-2024.pdf/'),
 ('library_intro','British Library調査公表の説明','https://www.bl.uk/stories/blogs/posts/learning-lessons-from-the-cyber-attack'),
 ('psni_ico','PSNI表計算ファイルの事故・ICO最終制裁','https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2024/10/what-price-privacy-poor-psni-procedures-culminate-in-750k-fine/'),
 ('psni_penalty','PSNI ICO詳細調査全文','https://ico.org.uk/media2/migrated/4031177/psni-penalty-notice.pdf'),
 ('qantas_oaic','Qantas OAIC 2026年予備調査全文','https://www.oaic.gov.au/privacy/privacy-assessments-and-decisions/privacy-decisions/Investigation-inquiry-reports/report-into-preliminary-inquiries-of-qantas'),
 ('moveit_maximus','Maximus MOVEit影響範囲・SEC届出','https://investor.maximus.com/sec-filings/all-sec-filings/content/0001032220-23-000061/0001032220-23-000061.pdf'),
 ('powerschool_opc','PowerSchool OPC改善約束','https://www.priv.gc.ca/en/opc-news/news-and-announcements/2025/let_powerschool_20250715/'),
 ('powerschool_ontario','PowerSchool Ontario詳細事後調査・55頁','https://www.ipc.on.ca/media/5990/download'),
 ('ticketmaster_filing','Live Nation Ticketmaster事故公表','https://investors.livenationentertainment.com/sec-filings/all-sec-filings/content/0001335258-24-000081/0001335258-24-000081.pdf'),
 ('coop_ico','ICO小売企業の事故報告受領','https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2025/05/statement-on-cyber-incidents-impacting-retailers/'),
 ('coop_notice','Co-op事故公表','https://www.co-operative.coop/media/news-releases/cyber-incident-update'),
 ('qantas_notice','Qantas 2025年7月事故通知','https://www.qantas.com/agencyconnect/global/en/agency-news/agency-news-july-25/qantas-cyber-incident.html'),
]

def main():
 base.RAW=base.ROOT/'research/disclosures/raw/personal_data_incidents_20261008'
 base.RAW.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  records=list(pool.map(base.fetch,SOURCES))
 for record in records:
  if record.get("text_file"):
   content=(base.ROOT/record["text_file"]).read_text()
   if "Pardon Our Interruption" in content or "Incapsula incident ID" in content:
    record["status"]="取得失敗"
    record["error"]="アクセス遮断画面であり資料本文ではない"
 target=base.ROOT/'research/technology/personal_data_incident_sources_20261008.json'
 target.write_text(json.dumps({'research_date':'2026-10-08','period_start':'2021-10-08','period_end':'2026-10-08','raw_storage':str(base.RAW.relative_to(base.ROOT)), 'note':'公開された事故公表・事後調査・規制当局資料のみを取得。流出データや攻撃者の配布先は取得しない。人数と件数、流出確認と可能性、当局の主張と確定判断を区別。原本と抽出本文はGit管理外。','documents':records},ensure_ascii=False,indent=2)+'\n')
 for r in records: print(r['id'],r['status'],r.get('pages','HTML'),r.get('text_characters',''),r.get('error',''),flush=True)

if __name__=='__main__': main()
