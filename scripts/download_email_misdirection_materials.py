#!/usr/bin/env python3
"""メール誤送信防止の公式仕様と公開導入事例を保存する。メール自体は扱わない。"""
import concurrent.futures
import json
import download_privacy_materials as base

SOURCES = [
 ('proofpoint_architecture','Proofpoint APIとAdaptive Email DLP技術説明（2025年7月）','https://www.proofpoint.com/sites/default/files/white-papers/pfpt-us-wp-understanding-core-email-protection-api-adaptive-email-dlp-July2025.pdf'),
 ('proofpoint_taylor','Taylor Vinters導入事例','https://www.proofpoint.com/sites/default/files/customer-stories/pfpt-us-cs-taylor-vinters.pdf'),
 ('proofpoint_product','Proofpoint Adaptive Email DLP','https://www.proofpoint.com/us/adaptive-email-dlp'),
 ('knowbe4_product','KnowBe4 Prevent宛先誤り検出','https://www.knowbe4.com/products/prevent/misdirected-emails'),
 ('knowbe4_rwk','RWK Goodman導入事例','https://www.knowbe4.com/case-study/legal/rwk-goodman'),
 ('knowbe4_technical','Prevent現行技術説明','https://support.knowbe4.com/hc/en-us/articles/49221871630355-Prevent-Technical-Overview'),
 ('knowbe4_modes','Prevent送信前確認とHybrid Mode','https://support.knowbe4.com/hc/en-us/articles/42984943371411-Understanding-Prevent-General-Settings'),
 ('knowbe4_datasheet','KnowBe4 Prevent仕様資料','https://www.knowbe4.com/hubfs/KnowBe4-Prevent-Datasheet_EN-US.pdf?hsLang=en'),
 ('ciphercraft_misumi','ミスミAI+導入事例','https://www.ciphercraft.jp/mail/usecase/misumi/'),
 ('ciphercraft_takenaka','竹中工務店AI+導入事例','https://www.ciphercraft.jp/mail/usecase/takenakakomuten/'),
 ('ciphercraft_okabe','岡部Google Workspace導入事例（AI採用は未確認）','https://www.ciphercraft.jp/mail/usecase/okabe/'),
 ('ciphercraft_features','CipherCraft/Mail現行機能とAI+対応メールソフト','https://www.ciphercraft.jp/mail/overview/'),
 ('exchange_rules','Exchange Onlineメールフロールール','https://learn.microsoft.com/en-us/exchange/security-and-compliance/mail-flow-rules/mail-flow-rules'),
 ('exchange_conditions','Exchange Online宛先・CCの判定条件','https://learn.microsoft.com/en-us/exchange/security-and-compliance/mail-flow-rules/conditions-and-exceptions'),
 ('exchange_order','Exchange Onlineルールの処理順と設計上の注意','https://learn.microsoft.com/en-us/exchange/security-and-compliance/mail-flow-rules/configuration-best-practices'),
 ('purview_exchange','Microsoft Purview Exchange DLP条件と動作','https://learn.microsoft.com/en-us/purview/dlp-exchange-conditions-and-actions'),
 ('outlook_smartalerts','Outlook Smart Alerts送信時判定','https://learn.microsoft.com/en-us/office/dev/add-ins/outlook/onmessagesend-onappointmentsend-events'),
 ('gmail_dlp','Gmail DLP公式仕様','https://knowledge.workspace.google.com/admin/security/prevent-data-leaks-in-email-and-attachments-gmail-dlp'),
 ('gmail_compliance','Gmail本文・ヘッダーの内容検査','https://knowledge.workspace.google.com/admin/gmail/advanced/set-up-rules-for-advanced-email-content-filtering'),
 ('gmail_routing','Google Workspaceメール経路の制御','https://knowledge.workspace.google.com/admin/gmail/advanced/email-routing-and-delivery-options-for-google-workspace'),
]

def main():
 base.RAW=base.ROOT/'research/disclosures/raw/email_misdirection_20261007'
 base.RAW.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  records=list(pool.map(base.fetch,SOURCES))
 target=base.ROOT/'research/technology/email_misdirection_sources_20261007.json'
 target.write_text(json.dumps({'research_date':'2026-10-07','raw_storage':str(base.RAW.relative_to(base.ROOT)), 'note':'公開公式資料の保存。導入事例は提供会社による公表。製品の精度や実環境での遮断を独立検証したものではない。原本はGit管理外。','documents':records},ensure_ascii=False,indent=2)+'\n')
 for r in records: print(r['id'],r['status'],r.get('pages','HTML'),r.get('text_characters',''),r.get('error',''),flush=True)

if __name__=='__main__': main()
