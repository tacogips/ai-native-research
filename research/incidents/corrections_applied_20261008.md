# 深掘りによる既存記述の訂正適用記録（2026-10-08）

`research/incidents/` の11件の深掘りファイルにある「既存記述の訂正候補」を、既存の調査資料へ反映した記録である。各候補について深掘り本文の根拠表と、必要に応じて保存済みの一次資料（`research/disclosures/raw/incidents/`）を確認した。一次資料、または引用元との明示的な不一致で裏付けられる候補だけを適用した。解釈を含む部分や根拠の弱い部分は反映せず、理由欄に記した。攻撃手順・命令・攻撃用入力は記載していない。

集計: 適用 72件（うちリーダー適用2件）、保留 2件、除外 6件（合計 80件）。

変更したファイル:

- `research/technology/autonomous_agent_risks_papers_incidents.md`
- `research/technology/ai_incident_reports_20261006.md`
- `research/technology/personal_data_incidents_postmortem_20261008.md`
- `research/technology/personal_data_incident_cases_20261008.json`（各事例に `correction_20261008` を追加）
- `research/technology/ransomware_damage_and_ai_era_trends_20261008.md`
- `research/technology/ransomware_cases_20261008.json`（各事例に `correction_20261008` を追加。取得失敗を解消した出典は `download_status` を更新し `saved_path_20261008` を追加）

変更した Markdown の末尾には「2026-10-08 深掘りによる訂正」節を追加した。

## 候補一覧

| # | 深掘りファイル | 対象ファイル | 内容 | 結果 | 理由 |
|---|---|---|---|---|---|
| 1 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Replit: 削除日07-17と最終的な完全復元（07-29公表）、一次出典 | 適用 | Replit公式ブログ・当事者投稿（保存済み・SHA-256あり）と一致 |
| 2 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | PocketOS: 削除日04-24、Railwayによる全データ復元、バックアップ消失は初報の主張、規則列挙は削除後の回答 | 適用 | 当事者投稿とRailway公式ブログ（一次）で確認 |
| 3 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | PocketOSの教訓（第2節）に、実際の復旧は事業者の拠点外バックアップと補足 | 適用 | Railway公式ブログ |
| 4 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | OpenClaw CVE-2026-25253の日付の意味（報告・勧告・NVD公開）とGHSA併記 | 適用 | GHSA・NVD（一次） |
| 5 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | ClawHavoc 約12%は2026-02-01時点、02-16時点は約7.7% | 適用 | Koi原報告（Wayback保存版） |
| 6 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Hermes CVE-2026-7396を開発元が「脆弱性ではない」として閉鎖 | 適用 | GitHub Issue #8733（一次） |
| 7 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Hermes 7397・6829の修正版 | 適用 | 開発元のコミット・リリース、NVD |
| 8 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Auto Mode 60〜80%の小標本とInformative閉鎖 | 適用 | 研究者の原報告（研究者の記述と明記） |
| 9 | [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | 第2節項目6の比較対象（Trajectory Labs評価とシステムカードは別） | 適用 | 研究者原報告とAnthropic発表 |
| 10 | [ai_frontier_and_ai_enabled_attacks.md](ai_frontier_and_ai_enabled_attacks.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | C1: Hugging Face侵入の原因の単一化と動機の訂正 | 適用 | OpenAI技術報告・続報、METR分析 |
| 11 | [ai_frontier_and_ai_enabled_attacks.md](ai_frontier_and_ai_enabled_attacks.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | C2: Anthropic評価事故の四事例・七実行への更新、中止要求の失敗、初期解釈の修正 | 適用 | Anthropic 2026-09-09分析（一次）。ただし「停止した内部研究モデルも再実行実験で攻撃を続けた」は深掘り本文に根拠記載がなく反映せず |
| 12 | [ai_frontier_and_ai_enabled_attacks.md](ai_frontier_and_ai_enabled_attacks.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | C3: 「バックアップが同じ影響範囲」をHF・Anthropic事例の原因とした記述の削除（C3再掲は同一候補） | 適用 | 両事例の一次資料に記載がないことを深掘りが確認 |
| 13 | [ai_frontier_and_ai_enabled_attacks.md](ai_frontier_and_ai_enabled_attacks.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | C4: メキシコ政府機関事例の一次出典をGambit報告へ、SAT・INEの否定説明を併記 | 適用 | Gambit技術報告（一次）、SAT・INE公式説明 |
| 14 | [ai_frontier_and_ai_enabled_attacks.md](ai_frontier_and_ai_enabled_attacks.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | GTG-1002の80〜90%は企業推計で分母の明記が必要（補足事項） | 保留 | 深掘り自身が訂正候補に計上しておらず、既存記述の誤りではないため |
| 15 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | GitHub MCP toxic agent flowの原因（3要素の組合せ）と一次出典 | 適用 | Invariant Labs原報告 |
| 16 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | EchoLeak CVSS 9.3はMicrosoft評価、NVDは7.5、謝辞2者 | 適用 | MSRC・NVD（一次） |
| 17 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | ForcedLeak CVSS 9.4は自社評価、流出は研究者環境での実証 | 適用 | Noma原報告 |
| 18 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/ai_incident_reports_20261006.md` | Reprompt: 報告2025-08-31、修正・公表2026-01-14 | 適用 | 報告日は報道（BleepingComputer）だが、既存の「発見日不明」との明示的な差。報道由来と明記 |
| 19 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/ai_incident_reports_20261006.md` | SearchLeak: CVE公表2026-06-04、MSRC自身が緩和済みと登録 | 適用 | MSRC（一次） |
| 20 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | GitLost: 原報告07-06、実証04-02、GitHub修正07-08・07-13 | 適用 | Noma原報告、GitHub PR（一次） |
| 21 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/ai_incident_reports_20261006.md` | RovoBlast: 報告・修正・公開日 | 適用 | Bugcrowd公開記録（一次） |
| 22 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/ai_incident_reports_20261006.md` | RovoBlastの持ち出し経路（実証は画像取得、外部調査機能は追加経路） | 適用 | Bugcrowd公開記録 |
| 23 | [ai_prompt_injection_exfiltration.md](ai_prompt_injection_exfiltration.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | RovoBlastの報告日・P2・報奨金・修正日・公開日 | 適用 | Bugcrowd公開記録 |
| 24 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/ai_incident_reports_20261006.md` | Nx: 発生と配布開始の区別、「指示文への注入」の誤読防止 | 適用 | Nx勧告 GHSA-cxm3-wv7p-598c |
| 25 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Salesloft Drift「700超の組織から流出」の出典と性格、Mandiantの侵入経路 | 適用 | FBI FLASH PDF（保存済み、組織数の記載なし）、Salesloft・Mandiant要約 |
| 26 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/ai_incident_reports_20261006.md` | Salesloft Driftの侵入期間2025-03-22〜09-05の追記 | 適用 | Mandiant調査要約（Salesloft掲載） |
| 27 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Amazon Q「95万インストールに配布」を「1.84.0の導入数は未公表」へ | 適用 | AWS-2025-015・GitHub勧告・NVDに配布数の記載なし |
| 28 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Amazon Qの不正コミット日07-13 | 適用 | GitHubのコミット記録 |
| 29 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | postmark-mcpの原因（公式を装った配布物の導入）と「初の」はKoiの主張 | 適用 | Koi・Postmark（一次）。ただし「版を固定しても防げなかった」は深掘りの解釈のため反映せず、版固定を補助的統制と表現 |
| 30 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Bitwarden「約334ダウンロード」は利用者投稿の数字 | 適用 | Bitwarden声明スレッド（保存済み） |
| 31 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Bitwarden: AI設定ファイルの収集はJFrog解析で確認済み（222行・365行） | 適用 | JFrog解析（保存済み・SHA-256あり） |
| 32 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | Bitwarden: npm登録情報の公開時刻17:22 ET | 適用 | npm登録情報 |
| 33 | [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) | `research/technology/autonomous_agent_risks_papers_incidents.md` | node-ipc 参考文献[93]: GHSA-pvh2-rg5g-69v7の対象は9.1.6のみ | 適用 | GitHub勧告API |
| 34 | [global_consumer_data_breaches.md](global_consumer_data_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F01 Robinhood: SEC認定は和解上の認定、2021年6月14日の同種事故と是正不完全 | 適用 | SEC和解命令 34-102170 ¶74–77 |
| 35 | [global_consumer_data_breaches.md](global_consumer_data_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F02 Optus: ACMAの2024年5月提訴と流出期間、950万人（OAIC）と980万件（会社）の単位差 | 適用 | ACMA声明、Optus支援ページ、OAIC |
| 36 | [global_consumer_data_breaches.md](global_consumer_data_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F04 T-Mobile: 原因をFCC同意判決¶24の「人為的ミスによる権限設定の誤り」へ | 適用 | FCC DA 24-860 ¶24（既存資料自身の根拠と不一致） |
| 37 | [global_consumer_data_breaches.md](global_consumer_data_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` | F09 AT&T: 本件を対象とするFCC和解を追記しないこと | 除外 | 既存記述に誤りはなく、変更不要との注意書き |
| 38 | [global_consumer_data_breaches.md](global_consumer_data_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F12 Coupang: 台湾利用者204,552人の確認を別項目で補足 | 適用 | 台湾數位產業署 2026-02-26（一次） |
| 39 | [global_consumer_data_breaches.md](global_consumer_data_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F05 23andMe: 2段階認証の義務化は2023年11月6日（補足） | 適用 | 23andMe 8-K/A（一次） |
| 40 | [japan_data_leaks.md](japan_data_leaks.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` | J01 NTT西日本: 自社顧客約120万件、逮捕、行政指導、2026年9月30日進捗などの補足 | 保留 | 既存記述に誤りはなく補足のみ。複数の数値を個別に一次資料で照合する作業を本適用の範囲外とした |
| 41 | [japan_data_leaks.md](japan_data_leaks.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J02 LINEヤフー: 起点の委託先への不正アクセス2023年8月10日・24日 | 適用 | PPC 2024-03-28 詳細資料 p.4 |
| 42 | [japan_data_leaks.md](japan_data_leaks.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J03 トヨタ: 215万人は5月12日公表分、PPC集計の約230万人分を併記 | 適用 | PPC 2023-07-12 指導 p.2 |
| 43 | [japan_data_leaks.md](japan_data_leaks.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J08 快活CLUB: 2025年12月4日の容疑者逮捕を追記 | 適用 | 快活フロンティア公表PDF（一次） |
| 44 | [japan_data_leaks.md](japan_data_leaks.md) | （既存ファイルなし） | J08 快活CLUB: 検知日「2024年→2025年1月18日」 | 除外 | 依頼文側の誤りで、既存ファイルに2024年とする記述はない（リーダー指示により除外） |
| 45 | [japan_data_leaks.md](japan_data_leaks.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` | J09 尼崎市: BIPROGY第三者委員会報告書を根拠に追加 | 適用 | BIPROGY 2022-12-12資料（一次） |
| 46 | [japan_data_leaks.md](japan_data_leaks.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_sources_20261008.json` | J10 Money Forward: 誤保管の説明は「根拠未取得」とした従前候補 | 除外 | 深掘り自身が公式FAQで確認し候補を撤回済み |
| 47 | [japan_data_leaks.md](japan_data_leaks.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` | J10 Money Forward: ME銀行連携再開6月5日10時50分の従前候補 | 除外 | 深掘り自身が再開状況告知で確認し候補を撤回済み |
| 48 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J04 KADOKAWA: 254,241人に261,956人（2024-11-01時点）を併記 | 適用 | KADOKAWA第2四半期決算説明資料（一次） |
| 49 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J04 KADOKAWA: 会社の推測原因（フィッシング等によるアカウント情報窃取） | 適用 | KADOKAWA 2024-08-05 PDF2頁 |
| 50 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J04 KADOKAWA: 有価証券報告書の是正確認と対策記載 | 適用 | 2025年・2026年3月期有価証券報告書 |
| 51 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/ransomware_cases_20261008.json` | R11 KADOKAWA: 特別損失、会社推計の業績影響、復旧時期、人数更新 | 適用 | 決算短信・通期決算説明資料（一次） |
| 52 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J05 イセトー: 「PPC調査」を「2025年3月19日PPC指導（法147条）」へ | 適用 | PPC 2025-03-19 報道発表 |
| 53 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J05 イセトー: コピーの範囲をPPC認定（56部署中3部署）へ | 適用 | PPC資料2頁、イセトー2024-10-04 |
| 54 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J06 アスクル: EDR未導入はサーバー（端末は記載外） | 適用 | アスクル第13報4頁 |
| 55 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` ・ `research/technology/ransomware_cases_20261008.json` | J06/R14 アスクル: 完全復旧の節目と損失額 | 適用 | 第17報・第18報・2026年5月期決算短信 |
| 56 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | J07 アサヒ: 「おそれ」件数の時点と2025年11月からの変化 | 適用 | アサヒ 2025-11-27・2026-07-17 公表 |
| 57 | [japan_major_ransomware.md](japan_major_ransomware.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/ransomware_cases_20261008.json` | R13 アサヒ: 一時費用約170億円と2026年見込み約95億円 | 適用 | アサヒ 2025年12月期決算説明資料 |
| 58 | [kadokawa_dwango_gakuen_leak.md](kadokawa_dwango_gakuen_leak.md) | `research/incidents/japan_major_ransomware.md` | 学園の8月19日通知を実績から予告へ | 除外 | 深掘りファイル内で既に訂正済み（同ファイル末尾の「同一ファイル内の訂正」） |
| 59 | [kadokawa_dwango_gakuen_leak.md](kadokawa_dwango_gakuen_leak.md) | `research/incidents/japan_major_ransomware.md` | 147行: 6月10日復旧の根拠を学園8月1日発表へ、N/S高とN中等部の区別 | 適用（リーダー） | 学園2024-08-01発表（一次）。二次分析への依拠を一次資料へ置換 |
| 60 | [kadokawa_dwango_gakuen_leak.md](kadokawa_dwango_gakuen_leak.md) | `research/incidents/japan_major_ransomware.md` | 68行: 2024年9月11日以降の公式発表に学園の事後自己評価を補足 | 適用（リーダー） | N高・S高2024年度自己点検・評価報告書（一次） |
| 61 | [ransomware_healthcare_infrastructure.md](ransomware_healthcare_infrastructure.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` | 半田病院「記録の不足」を「ログ保全の不足（経時活動記録は作成）」へ | 適用 | 半田病院報告書本編18頁3.4.2節 |
| 62 | [ransomware_healthcare_infrastructure.md](ransomware_healthcare_infrastructure.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/ransomware_cases_20261008.json` | UKG復旧日2022年1月22日の従前候補 | 除外 | UKG公式報告書55頁で再確認でき、訂正不要と深掘りが結論 |
| 63 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F06 Capita: 「悪意あるファイルを実行」を取得経路未確定の表現へ | 適用 | ICO制裁金通知§38–39 |
| 64 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/ransomware_cases_20261008.json` | R07 British Library: 原本の取得失敗を解消 | 適用 | bl_review.pdf を保存済み（SHA-256一致を確認） |
| 65 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F13 British Library: 起点はターミナルサーバー（2020年2月設置） | 適用 | 事後報告6頁 |
| 66 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F13 British Library: 2026年7月年次報告の新目録稼働と復帰見込み | 適用 | 年次報告2025/26（保存済み） |
| 67 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F14 PSNI: 「当初案と区別」を算定額560万ポンドとの区別へ | 適用 | ICO制裁金通知§3・§12 |
| 68 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F14 PSNI: 補償原資1億1,900万ポンド | 適用 | 北アイルランド警察委員会声明 |
| 69 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/ransomware_cases_20261008.json` | R10 Synnovis: NHS Q&Aと議会答弁の取得失敗を解消 | 適用 | Wayback保存版と議会公開APIの保存ファイルを確認 |
| 70 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/ransomware_cases_20261008.json` | R12 M&S: 議会証言の取得失敗を解消 | 適用 | 議会委員会公開APIの保存ファイルを確認 |
| 71 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/ransomware_cases_20261008.json` | R12 M&S: 2025/26年度の事案関連費用と保険収入 | 適用 | M&S 2025/26年度決算（保存済み） |
| 72 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | A02 Co-op: 侵入経路（なりすましによるアカウント再設定） | 適用 | 議会証言Q197（保存済み） |
| 73 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | A02 Co-op: 会社本文のWayback確認と財務影響1億700万ポンド | 適用 | Wayback保存版・年次報告（保存済み） |
| 74 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F10 France Travail: 確定人数36,820,828人・25GB | 適用 | CNIL決定 SAN-2026-003 §14（Légifrance、ウェブページ取得ツールで閲覧。保存ファイルはない） |
| 75 | [uk_europe_incidents.md](uk_europe_incidents.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F10 France Travail: 決定全文はLégifranceで確認可能 | 適用 | 同上 |
| 76 | [us_supply_chain_breaches.md](us_supply_chain_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F07: Louisiana OMVアラートページは根拠にならず、NextSteps FAQで確認 | 適用 | 保存本文の照合（moveit_omv.txtにMOVEitの記載なし）、Wayback 2023-09-09版 |
| 77 | [us_supply_chain_breaches.md](us_supply_chain_breaches.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/ransomware_cases_20261008.json` | R08 Change: 7.99億ドルは貸付等の回収見込みに対する引当金 | 適用 | UHG 10-K FY2025 注記 |
| 78 | [us_supply_chain_breaches.md](us_supply_chain_breaches.md) | `research/technology/ransomware_damage_and_ai_era_trends_20261008.md` ・ `research/technology/ransomware_cases_20261008.json` | R08 Change: 身代金2,200万ドル（補足） | 適用 | 上院記録 S. Hrg. 118-785（保存済み） |
| 79 | [us_supply_chain_breaches.md](us_supply_chain_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F15 Qantas: 予備調査期間と報告公表日の区別 | 適用 | OAIC報告 |
| 80 | [us_supply_chain_breaches.md](us_supply_chain_breaches.md) | `research/technology/personal_data_incidents_postmortem_20261008.md` ・ `research/technology/personal_data_incident_cases_20261008.json` | F16 PowerSchool: 2024年8〜9月の接続の書き分け | 適用 | CrowdStrike最終報告5頁、起訴状5頁 |

## 訂正候補なしとされた事例（参考、集計外）

- [ai_agent_operations_incidents.md](ai_agent_operations_incidents.md) の Moltbook：既存記述は Wiz の一次報告と一致。
- [ai_frontier_and_ai_enabled_attacks.md](ai_frontier_and_ai_enabled_attacks.md) の英国AISI事例と OpenAI 推論抽出事例：既存記述は一次資料と整合。
- [ai_supply_chain_incidents.md](ai_supply_chain_incidents.md) の s1ngularity の「1,079リポジトリから2,349件」：GitGuardian と一致。
- [global_consumer_data_breaches.md](global_consumer_data_breaches.md) の Medibank、SK Telecom、T-Mobile の2021年事件の除外判断：既存記述は妥当。
- [japan_major_ransomware.md](japan_major_ransomware.md) のアサヒ：既存記述は一次資料と整合（補足2件は上表で適用）。
- [ransomware_healthcare_infrastructure.md](ransomware_healthcare_infrastructure.md) の大阪急性期・総合医療センター、名古屋港、ブリヂストン：既存記述は一次資料と一致。
- [us_supply_chain_breaches.md](us_supply_chain_breaches.md) の Ticketmaster：一次資料と食い違う事実なし。
