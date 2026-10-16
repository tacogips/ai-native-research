# 企業AI基盤の調査

機密情報を扱い、自律的に業務を実行・改善する企業AI基盤の設計に向けた調査集。説明は日本語とし、製品名・論文の原題・コードの識別子は原表記を保持する。[専門用語の日本語説明](research/glossary_ja.md)を参照。

## 全社PCに常駐する機密データ監視（2026年10月16日）

[端末での探索・漏えい防止・操作記録の比較](research/technology/endpoint_resident_sensitive_data_monitoring_20261016.md)。Purview、Cyberhaven、MIND、Fortra、Netwrix、Incydr、CrowdStrike、P-Pointer、SKYSEA、LANSCOPEの10系統を比較。保存データ検査と持ち出し遮断、常駐と予約検査、端末処理と外部への証拠送信を区別する。

## 個人情報を端末へ配布しない集中管理（2026年10月15日）

[オンラインでの個人情報集中管理](research/technology/online_pii_centralized_management_20261015.md)。担当者の入力・閲覧・更新と、原文を見せない集計・AI処理を主用途に、個人情報保管庫、代理処理、遠隔画面、安全な分析環境、文書閲覧を比較。OTPによる認証と保存禁止、中央AIが原文を読む処理と集計結果だけを返す処理を分けた。[文書6系統](research/technology/online_pii_document_access_20261015.md)、[遠隔環境7群](research/technology/online_pii_remote_environments_20261015.md)、[保管庫・共同分析7系統](research/technology/online_pii_vaults_and_cleanrooms_20261015.md)、[2025〜2026年の論文と仕様](research/technology/online_pii_research_20261015.md)、[独立レビュー](research/technology/online_pii_reviews_20261015.md)。

## 企業LLMの国内保存と処理地域（2026年10月14日）

[TIMEWELL記事と公式仕様から整理する国内保存・処理地域](research/technology/enterprise_llm_japan_residency_20261014.md)。AWS・Azure・Google・Fireworksの地域指定、推論と追加学習、保存と計算、価格条件を分け、企業の機密情報管理で記録する確認項目を整理した。クラウド向けの個人情報保護法Q&AをLLMへそのまま適用しない条件も補足。[記事・一次資料の取得台帳](research/technology/enterprise_llm_japan_residency_sources_20261014.json)。

## 保護情報管理と鍵付きファイルの運用（2026年10月14日）

[鍵付きファイルと鍵の定期変更](research/technology/protected_information_file_and_key_management_20261014.md)。Bitwarden・1Password・Keeper・KeePass、秘密管理、暗号鍵管理、公開鍵暗号、PurviewとGoogleのDrive DLP・CSE・Secret Manager・Cloud KMSを比較。ファイルと鍵の版の対応、旧鍵の保持、変更後の開封確認、AIへ鍵や原文を渡す境界を整理した。Microsoft Purviewの統合ブランド発表は2022年4月19日、前身Azure Purviewの公開試験版発表は2020年12月3日。[公式資料の取得台帳](research/technology/protected_information_key_management_sources_20261014.json)。

## 個人データ保護の目的と匿名化の判断（2026年10月14日）

[高木浩光氏の動画シリーズと原資料から学ぶ個人データ保護](research/disclosures/takagi_personal_data_protection_ai_native_20261014.md)。『ずんだもんの個人情報保護法務日誌』第1〜3回の公開説明欄と元資料を確認し、省略された第3回の4出典URLを復元した。氏名削除・仮名加工・匿名加工・統計情報、容易照合性と提供元基準、情報の結合と本人の評価、学習済みモデルと集計結果の公開条件を整理。日本の公式解釈、高木氏の制度分析、欧州の判決・監督機関の見解、AI基盤への設計案を区別し、2026年改正の成立・公布と施行を分けた。[出典確認台帳](research/disclosures/takagi_privacy_sources_20261014.json)。動画の字幕本文は取得できておらず、発話の逐語検証は含まない。

## 保存された機密データの監視・警告管理（2026年10月9日）

[ストレージ等を監視し、Sentryのように警告するシステムの比較](research/technology/telescreen_related_systems_20261009.md)。S3等のオブジェクト保存、ファイル共有、データベース、業務クラウドを含めて調査。50行の製品・機構・部品・参考を整理し、内容分類とアクセス方針、問題集約、担当、修正後再検査、再発、原文の処理・保持を比較した。独立企業50社や実測精度順位を意味しない。[比較CSV](research/technology/telescreen_related_systems_comparison_20261009.csv)、[JSON](research/technology/telescreen_related_systems_comparison_20261009.json)、[レビュー記録](research/technology/telescreen_related_review_summary_20261009.md)。

[ストレージ中心](research/technology/telescreen_related_storage_monitoring_20261009.md)、[企業基盤・国内製品](research/technology/telescreen_related_enterprise_20261009.md)、[業務クラウドの10系統](research/technology/telescreen_related_saas_dlp_20261009.md)、[公開実装・関連研究](research/technology/telescreen_related_oss_and_research_20261009.md)。公開一次資料の原本と取得台帳を保存し、担当を入れ替えてレビュー・改善した。HTTP成功と本文取得成功、局所検査と外部送信、手動終了と修正確認を分ける。

## 個人情報を扱うAIハーネスの保護機構（2026年10月8日）

[統合調査と開発要件](research/technology/ai_harness_privacy_security_master_20261008.md)。入力・分類・道具認可・承認・OS隔離・通信・資格情報・逐次出力・履歴・子エージェント・拡張・組織管理・失敗時動作・評価まで20分野を比較。担当を分けて調査し、担当を入れ替えたレビューで改善した。公開固定コードの確認と実機試験の範囲を区別する。

[Codex](research/technology/harness_codex_security_20261008.md)、[Claude Code](research/technology/harness_claude_security_20261008.md)、[pi.dev](research/technology/harness_pi_security_20261008.md)、[その他7製品とOpenHands SDK](research/technology/harness_oss_security_20261008.md)、[ガードレール5基盤](research/technology/harness_guardrail_mechanisms_20261008.md)、[OpenAI Agents・LangChain・LangGraph・Deep Agents](research/technology/harness_sdk_security_20261008.md)、[情報フロー・認可・評価研究](research/technology/harness_information_flow_and_evaluation_20261008.md)。各稿に固定資料・取得ハッシュ・独立レビューへの参照を記載。

## PIIの定義と分類例（2026年10月8日）

[日本・EU・米国の定義と43例](research/technology/pii_definitions_and_classification_examples_20261008.md)。陽性20例、前提付きの陰性11例、文脈次第12例を比較。個人関連情報、公開情報、暗号化・仮名加工・匿名加工、医療情報の制度要件と、個人情報ではない企業秘密を区別する。[CSV](research/technology/pii_classification_examples_20261008.csv)、[JSON](research/technology/pii_classification_examples_20261008.json)、[一次資料の取得台帳](research/technology/pii_definition_sources_20261008.json)。

## 最近5年の大規模な個人情報流出・事故（2026年10月8日）

[日本・海外の事件、原因、事後調査、再発防止策](research/technology/personal_data_incidents_postmortem_20261008.md)。日本10事例・海外16事例と補足2事例を比較。流出確認・可能性・紛失、人数・件数・アカウント数、実施済み対策・命令・改善提案を区別する。[事件データ](research/technology/personal_data_incident_cases_20261008.json)、[出典・取得台帳](research/technology/personal_data_incident_sources_20261008.json)。

[ランサムウェアの業務被害と生成AI公開前後の動向](research/technology/ransomware_damage_and_ai_era_trends_20261008.md)。同じ5年間の14事例と警察庁、FBI、Verizon、Sophos、Chainalysisの年次比較。停止・復旧・費用を流出と分け、発行年と観測期間、暗号化しない恐喝の定義変更、AI悪用の観測と因果関係を整理した。[比較データ](research/technology/ransomware_trends_20261008.json)、[CSV](research/technology/ransomware_trends_20261008.csv)、[事例](research/technology/ransomware_cases_20261008.json)、[取得台帳](research/technology/ransomware_sources_20261008.json)。

## 個人情報・機密データの管理と秘密計算（2026年10月7日）

[機密情報管理の新興企業と投資会社](research/technology/sensitive_data_startups_and_investors_20261007.md)。YC採択5社、国内企業、文脈による機密分類、機密計算、メールの宛先との整合性、投資会社の出資理由を比較。17社を対象に、2026年10月8日にMINDの直近調達・医療機関での利用説明を追加。調達年月・出資と融資・買収済み企業を区別した。[取得台帳](research/technology/sensitive_data_startup_sources_20261007.json)。

[AIによるメール誤送信防止：Outlook・GmailとCC混入対策](research/technology/email_misdirection_ai_controls_20261007.md)。国内外の導入例、文脈・宛先の検査、警告と強制停止の違い、社内検査サーバの構成案を整理。[取得台帳](research/technology/email_misdirection_sources_20261007.json)。

[BERTとJev、手元で動く軽量判断モデル](research/technology/bert_jev_local_decision_models_20261007.md)。日本語ModernBERT、Laya、小型LLMを使うJev Local、AnyJev・Tacitを比較。固定区分と可変候補、確率の信頼性、非公式実装と公式モデルの違いを整理した。

[医療データとLLMの管理](research/technology/medical_data_llm_controls_20261007.md)。Stanfordの専用外部接続、施設内情報抽出、複数形式の非識別化、国内病院の文書作成、Imperialの退院要約を比較。公開実装の固定版を確認し、周辺制御とモデルが平文を読む範囲を整理した。[取得台帳](research/technology/medical_llm_sources_20261007.json)。

[ゼロ知識証明と関連技術](research/technology/zero_knowledge_sensitive_data_research_20261007.md)。EUの年齢確認、銀行の条件証明、スイスの電子投票、医療保険の公開実装、AI推論の証明を調査。証明する条件、公開される情報、実運用と模擬評価、機密性分類への適用を区別した。[取得台帳](research/technology/zero_knowledge_sources_20261007.json)。

[公的資料・書籍・論文の要約と日本／海外の比較](research/disclosures/privacy_data_management_reading_summary_20261007.md)。20件のPDFと9件のHTMLを保存し、重要箇所を頁番号付きで整理した。[取得記録](research/disclosures/privacy_retrieval_20261007.json)。

[企業のAI利用・秘密計算の事例調査](research/technology/enterprise_sensitive_data_ai_cases_20261007.md)。暗号文・秘密分散での学習と推論、銀行・製薬の共同学習、暗号化検索、TEEでの文章生成を比較。企業内の権限管理と機密情報削除、2026年の暗号化言語モデル研究、保護する主体と公開証拠の限界を整理した。[出典・取得記録](research/technology/enterprise_sensitive_ai_sources_20261007.json)。

[平文を開示せず機密性を判定する補足調査](research/technology/confidentiality_classification_without_plaintext_20261007.md)。秘密計算での文章分類、既知の秘密との照合、平文を読む前処理の有無を整理。企業内に限定せず研究機関等を含む。

## インシデントの深掘り（2026年10月8日）

[インシデント深掘りの索引と横断整理](research/incidents/README.md)。既存資料で概要だけだった約60件（国内外の個人情報流出、ランサムウェア、AI関連の事故・脆弱性）を一次資料で深掘りした。KADOKAWA／ドワンゴと[角川ドワンゴ学園の漏洩](research/incidents/kadokawa_dwango_gakuen_leak.md)を含む。漏洩人数・費用・原因・復元の有無など80件の訂正候補を見つけ、72件を既存資料へ反映した（[適用記録](research/incidents/corrections_applied_20261008.md)）。侵入経路は欠けていた統制の水準で書き、攻撃手順は記載しない。

## Master Report（最新版を保持し続ける統合資料）

| 資料 | 内容 |
|---|---|
| [業務基盤の Master Report](research/strategy/master_ai_native_operations_platform.md) | 既存大企業の業務の80%以上をAIが担う基盤に有効な技術・アプローチと課題。既存調査（基盤、事例、事故、論文155本）と2026年10月時点のウェブ調査（企業基盤、MCP・A2A・ID標準、企業の発表と決算、調査会社の報告、2026年の研究、EU・日本の規制）を統合。80%を「AIが実行し人が例外・承認・改善の採否を担う比率」として定義し直し、層別の技術選択、業務・組織のアプローチ、段階計画、受入条件を設計案として整理 |
| [指標・データ基盤・機能の Master Report](research/strategy/master_ai_native_metrics_data_platform.md) | AIを前提にしたことによる効率化を測る指標体系（投入・活動・成果の区別、四層と反証指標、二つの分母、監督の有効性、安全・採算・自己改善・組織）、構築するデータベース（知識系7層、運用記録系A〜N、記憶系の分離、最小スキーマ、設計原則）、提供する17機能と利用者別権限、受入条件 |

[AX Criteria（日本CTO協会、2026年10月5日公開）との対応表](research/strategy/ax_criteria_crosswalk.md)。50項目の成熟度基準と本調査の指標・データベース・機能・基盤の対応、双方の空白、使い方を整理した。設問本文・用語集・ガイドは公開APIから取得した。McKinsey「The State of AI in 2026」とAI事業者ガイドライン第1.2版のPDF原本と合わせ、原本はGitで管理せず、[取得記録](research/disclosures/retrieval_records_20261006.json)に参照元URL・取得日・ハッシュ値・照合結果だけを残す。

原本を持たない読者のために、重要情報を落とさない内容要約を置く: [McKinsey「The state of AI in 2026」要約](research/disclosures/mckinsey_state_of_ai_2026_summary.md)（18図表の数値を含む）、[AI事業者ガイドライン第1.2版 要約](research/disclosures/meti_ai_guidelines_v1_2_summary.md)、[AX Criteria 50項目・採点基準・用語集・ガイドの記録](research/disclosures/ax_criteria_items_summary.md)、[法務省 AI法務支援サービスと弁護士法72条の指針（令和8年・令和5年）とロードマップの要約](research/disclosures/moj_ai_legal_services_72_summary.md)、[日本政府のAI関連指針25文書の調査](research/disclosures/japan_gov_ai_guidelines_survey.md)（内閣府・AISI・経産省・総務省・デジタル庁・個人情報保護委員会・金融庁・公取委・文化庁）。

[リーガルテックを実務家視点で見る](research/legal_domain/legaltech_practitioner_perspectives.md)。企業法務（当事者）と法務事業者（ベンダー・法律事務所・AIネイティブ法律事務所）のブログ・note・調査・事例を国内外で集め、法務省72条新指針への反応、ハルシネーション制裁、報酬体系と若手育成の変化、法務業務のうちAIが担える範囲と企業AI基盤への示唆を整理した。

Master Report は日付付きの調査版ではなく、新しい一次資料や検証結果が出るたびに更新し、末尾の改訂履歴へ変更点を記録する。

## AIを前提に業務・組織を小さくする事例（2026年10月6日）

[Treasure AIと国内外15社の比較](research/benchmarks/treasure_ai_compact_organization_cases_20261006.md)。Fluentdの開発元Treasure Dataの文書作成・業務製品の集約を調べ、日本6社・海外9社の課題、技術、成果、人の確認、自己改善の記録を整理した。DeNAとShopifyの実装を掘り下げ、人員削減・作業時間の短縮・将来目標を区別する。[26出典の確認台帳](research/benchmarks/treasure_ai_compact_sources_20261006.json)。 Klarnaの2025年開示は再配信HTMLの全文取得で確認制限を解消した。[取得記録](research/benchmarks/klarna_2025_disclosure_retrieval_20261006.json)。

## 意味検索・関係検索・RAGの代替（2026年10月7日）

[最新研究と企業での比較案](research/technology/rag_semantic_graph_alternatives_20261007.md)。2026年10月6日のAutoRAG、9月のNexusRAG・G³RAG・ConRAG・TAGGRAPH等を、文書構造、長文、頁画像、DB集計、反復検索と比較。初稿と改訂の年代、関係抽出を省く技術、単純な検索に負ける条件、費用の分母、企業の認可・更新への未解決点を整理した。3回・9問の追加調査と、4公開実装の固定版確認を含む。[25出典の台帳](research/technology/rag_sources_20261007.json)。追加18論文・307頁を取得・全頁OCRし、[日本語解説13](research/papers/paper_notes_13.md)を追加した。

## AIの実行基盤と隔離技術（2026年10月7日）

[技術調査](research/technology/agent_os_sandbox_deep_dive_20261007.md)。17の技術・基盤を比較し、権限、外部通信、資格情報、共有領域、継続実行、復元、性能、自己変更、外部監査を調べた。4回・12問の追加調査を記録し、公開コードの固定版と初期設定まで照合した。[42出典の確認台帳](research/technology/agent_os_sandbox_sources_20261007.json)。新規12論文・206頁を取得し、全頁OCRと[日本語解説12](research/papers/paper_notes_12.md)を追加。最新の論文初稿は2026年10月5日。

## データの機密区分とアクセス権の申請・付与（2026年10月6日）

[事例・論文と業務手順の調査](research/technology/data_clearance_access_grant_workflows_20261006.md)で9つの導入・製品構成を比較し、Instacartの公開コードまで確認した。通常申請の自動付与と、規則変更・高リスク例外の人による承認を分け、承認と実行の一致、取消し、自己改善の監査を整理する。[出典台帳](research/technology/data_clearance_access_sources_20261006.json)。追加論文7本・88頁を取得し、全頁OCRと[日本語解説11](research/papers/paper_notes_11.md)を追加した。

## 企業と法務・経理・人事の事例（2026年10月6日）

| 資料 | 内容 |
|---|---|
| [Harperから広げた企業比較](research/benchmarks/ai_native_company_cases_expanded_20261006.md) | 35の企業・サービス群。保険、法律、会計、医療事務、物流、顧客対応、人材、営業、日本の管理業務。提供形態・人の判断・料金・改善の記録を比較 |
| [法務・経理・人事の20事例](research/benchmarks/enterprise_legal_finance_hr_cases_20261006.md) | 法務7件、経理7件、人事6件。国内6件・海外14件。対象工程、成果の分母、目標と実績、人の承認、認可・監査に必要な情報を整理 |
| [海外事例の課題と技術構成](research/benchmarks/overseas_ai_problem_technology_deep_dive_20261006.md) | 11構成。検索前と表示後の認可、外部操作、契約版の統合、会計の状態、人事の書戻し、作業領域、監査と評価。Brexの公開コードも固定版で確認。10月13日にHarperのBig Brotherの用途と公開出典を追記 |

企業比較と部門事例には重複があるため、35と20を合計した社数とは扱わない。一次資料の本文を確認し、企業事例と技術の深掘りで計6回・18問の追加調査を[問いの記録](research/ai_native_recursive_research_log_20261005.md)へ追記した。

## 今回の重点調査（2026年10月6日）

[検索認可・漏えい防止・知識構造・自己改善の監査と説明可能性](research/technology/enterprise_data_authorization_audit_xai_20261006.md)

検索認可から派生資料の認可へ、漏えい防止から業務の知識構造へ、作業記録から独立した監査と説明の検証へ、問いを発展させる調査を3回・12問実施した。論文、製品の公式資料、標準を比較し、データ項目、監査項目、検証条件を整理した。

## 論文の取得と日本語解説

[最近のAI関連事故・攻撃・脆弱性](research/technology/ai_incident_reports_20261006.md)。2026年10月1日の対応続報まで確認し、14の事例群を実侵入、阻止された攻撃、データ露出、研究での再現に分け、企業AI基盤の認可・監査・自己改善への教訓を整理した。

[論文索引・取得方法](research/papers/README.md)。引用したarXiv論文185本・4,407頁を全て取得し、各論文の概要・重要点・限界・企業設計への示唆を日本語で説明した。PDFの要旨と本文の関連箇所を確認したが、全付録の精読や実験の再現は行っていない。

PDF原本と抽出本文、全頁OCRによる検索可能なPDFと認識本文は `research/papers/arxiv/` にローカル保存する。Gitでは日本語解説、取得・OCR台帳、再取得・OCR用スクリプトを管理する。保存した版・容量・頁数・ハッシュ値・OCRの処理状態は台帳で確認できる。

## 問いを反復する拡張調査（2026年10月5日）

| 資料 | 内容 |
|---|---|
| [拡張調査](research/strategy/ai_native_recursive_expansion_20261005.md) | 3回・15問。顧客対応・調達・人事・医療周辺・支払い、企業成果、組織、契約、例外処理、採算、退出 |
| [問いと出典の記録](research/ai_native_recursive_research_log_20261005.md) | 問いの親子関係、一次資料、検証深度、訂正、検算、次の問い。重点調査・事故調査・企業事例の追加を含め合計21回・69問 |

## 写真の10テーマを再調査した資料（2026年10月5日）

| 資料 | 内容 |
|---|---|
| [共通基盤](research/technology/ai_native_company_platform_20261005.md) | 実行基盤、データ・検索・モデル、機密保護、本人確認、認可、記憶、監査 |
| [法務・業務設計](research/legal_domain/ai_native_operations_20261005.md) | 法務・評価、業務アプリ、自律度、自己改善、運用、経営・広報 |
| [企業事例](research/benchmarks/ai_native_companies_20261005.md) | Harper、Panta、Crosby、Basisなどの事例、全社展開、品質低下・撤回・製品停止 |
| [範囲と検証台帳](research/ai_native_research_audit_20261005.md) | 元写真との対応、出典の検証深度、限定、未実施の社内検証 |

## 前段の調査（2026年10月2日）

| 資料 | 内容 |
|---|---|
| [Hermes・dotsの企業適用](research/technology/hermes_openai_dots_enterprise.md) | 機能、実行権限、企業導入の課題、論文・事例 |
| [企業向け制御基盤](research/technology/enterprise_agent_control_plane.md) | 主要企業の制御機能、公開ソフトウェア、外部AIを包む構成、運用例 |
| [常駐・自己改善AIのリスク](research/technology/autonomous_agent_risks_papers_incidents.md) | 論文、実際の問題事例、本人性と委任、規制 |
| [隔離と機密計算](research/technology/agent_sandbox_isolation_confidential_computing.md) | 隔離環境、外部通信・資格情報の保護、計算中の機密保護 |
| [AI向けの実行基盤](research/technology/ai_os_agent_os.md) | OSとAIの統合、実行・記憶・道具・標準 |
| [概念体系と業務データ](research/technology/ontology_palantir_kinetic_layer.md) | Palantir、業務指標の意味の定義、関係図、研究・標準 |

別の `ai-native-company` リポジトリで行った、情報の流れの制御、長期記憶、Zanzibar・OpenFGA・Cedarによる認可、隔離と継続実行の調査を前提とする。別リポジトリの資料は、このリポジトリ内のファイルとしては扱わない。

## 読み方

製品機能の説明、企業の公表値、研究の結果、本調査の設計案、社内で未検証の条件を区別する。過去の報告は記載された日付・版の情報であり、現在の製品条件や性能へ自動的に適用しない。各資料の再検証・訂正も参照する。

認可・機密保護・監査はAIの外側で強制することを設計の出発点とする。実案件の品質、権限変更の反映時間、契約、費用、説明の忠実性は、公開資料だけでは自社への適合を立証できない。
