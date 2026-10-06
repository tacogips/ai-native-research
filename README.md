# 企業AI基盤の調査

機密情報を扱い、自律的に業務を実行・改善する企業AI基盤の設計に向けた調査集。説明は日本語とし、製品名・論文の原題・コードの識別子は原表記を保持する。[専門用語の日本語説明](research/glossary_ja.md)を参照。

## 企業と法務・経理・人事の事例（2026年10月6日）

| 資料 | 内容 |
|---|---|
| [Harperから広げた企業比較](research/benchmarks/ai_native_company_cases_expanded_20261006.md) | 35の企業・サービス群。保険、法律、会計、医療事務、物流、顧客対応、人材、営業、日本の管理業務。提供形態・人の判断・料金・改善の記録を比較 |
| [法務・経理・人事の20事例](research/benchmarks/enterprise_legal_finance_hr_cases_20261006.md) | 法務7件、経理7件、人事6件。国内6件・海外14件。対象工程、成果の分母、目標と実績、人の承認、認可・監査に必要な情報を整理 |

企業比較と部門事例には重複があるため、35と20を合計した社数とは扱わない。一次資料の本文を確認し、3回・9問の追加調査を[問いの記録](research/ai_native_recursive_research_log_20261005.md)へ追記した。

## 今回の重点調査（2026年10月6日）

[検索認可・漏えい防止・知識構造・自己改善の監査と説明可能性](research/technology/enterprise_data_authorization_audit_xai_20261006.md)

検索認可から派生資料の認可へ、漏えい防止から業務の知識構造へ、作業記録から独立した監査と説明の検証へ、問いを発展させる調査を3回・12問実施した。論文、製品の公式資料、標準を比較し、データ項目、監査項目、検証条件を整理した。

## 論文の取得と日本語解説

[最近のAI関連事故・攻撃・脆弱性](research/technology/ai_incident_reports_20261006.md)。2026年10月1日の対応続報まで確認し、14の事例群を実侵入、阻止された攻撃、データ露出、研究での再現に分け、企業AI基盤の認可・監査・自己改善への教訓を整理した。

[論文索引・取得方法](research/papers/README.md)。引用したarXiv論文148本を全て取得し、各論文の概要・重要点・限界・企業設計への示唆を日本語で説明した。PDFの要旨と本文の関連箇所を確認したが、全付録の精読や実験の再現は行っていない。

PDF原本と抽出本文、全頁OCRによる検索可能なPDFと認識本文は `research/papers/arxiv/` にローカル保存する。Gitでは日本語解説、取得・OCR台帳、再取得・OCR用スクリプトを管理する。保存した版・容量・頁数・ハッシュ値・OCRの処理状態は台帳で確認できる。

## 問いを反復する拡張調査（2026年10月5日）

| 資料 | 内容 |
|---|---|
| [拡張調査](research/strategy/ai_native_recursive_expansion_20261005.md) | 3回・15問。顧客対応・調達・人事・医療周辺・支払い、企業成果、組織、契約、例外処理、採算、退出 |
| [問いと出典の記録](research/ai_native_recursive_research_log_20261005.md) | 問いの親子関係、一次資料、検証深度、訂正、検算、次の問い。重点調査・事故調査・企業事例の追加を含め合計12回・42問 |

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
