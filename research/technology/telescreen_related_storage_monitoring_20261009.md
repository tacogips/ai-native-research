# 保存された機密データの監視と警告管理：ストレージ中心の比較

調査日：2026-10-09。公開一次資料による調査。比較の問いは、利用者が構想する「ストレージ等を検査し、機密データの不適切な保存をSentryのように警告・集約・追跡するもの」。特定の非公開実装の記述や比較は含まない。本文の製品仕様は提供者の公開説明であり、有償環境の操作試験や通信監査の結果ではない。

## 結論

**この分野には既存製品が複数ある。中心となる名称はDSPM（Data Security Posture Management：データの所在・機密性・アクセス権・危険な保存状態を把握する管理）である。** 保存内容の分類だけでなく、権限・公開範囲・保管場所の方針と組み合わせ、問題を管理して修正につなげる。Sentra、Rubrik DSPM、IBM Guardium Exposure Manager、Concentric AI、Symmetry DataGuard、Securiti、Cortex Cloud、Wizは直接または強く関連する比較対象。Datadog Sensitive Data Scannerも現在はS3検査を提供し、「監視製品に機密データ検査を追加する」という構想に近い。

ただし、機密情報を発見すること、不適切な保存だと判断すること、重複した警告を一つの問題にすること、担当者に依頼すること、修正を確認することは別の機能。通知先にSlackがあるだけではSlackの本文検査を意味せず、Jira連携だけでは修正の再確認を意味しない。

[Sentra AWS](https://sentra.io/platforms/aws)、[Rubrik policies](https://docs.rubrik.com/en-us/saas/dspm/dsp_policies.html)、[IBM問題管理](https://www.ibm.com/docs/en/exposure-manager?topic=managing-issues)、[Datadog S3検査](https://docs.datadoghq.com/security/sensitive_data_scanner/setup/cloud_storage/)

## 保存先・警告運用・原文処理の比較

「未確認」は公開資料で条件を確定できない意味であり、機能が存在しないという断定ではない。クラウド対応という一般説明から任意のデータベース・全ファイル形式・全履歴の対応を推測しない。

| 製品・機構 | 保存データの対象と検出 | 問題の運用として確認した内容 | 原文の処理と確認の限界 |
|---|---|---|---|
| Sentra | S3、DynamoDB等のクラウド保存先、データベース、業務クラウド、自社保存先。機密分類と権限・公開・所在の危険 | 警告状態・コメント・履歴、保存先/資産の再検査、外部業務連携。差分検査と検査範囲表示 | 顧客環境内の検査、分類結果等の属性を送信と説明。全量と標本検査を保存先ごとに選べる。状態変更が修正証明になる条件は未確認 |
| Concentric AI Semantic Intelligence | S3、自社保存先、構造化/非構造化データ。意味が似た文書を集約し、人事・法務・財務等の分類とアクセス異常を判定 | 同種文書の通常の権限との差から危険を見つけ、修正につなげる | 2025年FAQは自社SaaS内の自社モデルで本文処理後に抽出原文を破棄。氏名・メールは伏字保存の例外。顧客内検査とは異なる |
| Symmetry DataGuard | クラウド、自社保存先、データと利用者/機械の権限・利用の関連 | 危険の可視化と修正。問題集約・再発識別の詳細契約は未確認 | AWS配置例は顧客アカウント内に検査器を置く。外部と切り離した配置の公開説明もある。機能/配置ごとの全通信は未監査 |
| Securiti DSPM | 保存内容の発見・分類と公開・権限・所在等の危険 | 方針と修正支援。期限・再発・担当の具体的状態遷移は未確認 | 配置・一致値・補助AI等の全処理経路は未確定。「成熟度モデル」の推奨手順を搭載済み仕様としない |
| Rubrik DSPM | クラウド、自社保存先、Microsoft 365等。誤った場所、過剰公開、古い残存、保護設定の不足 | 方針を継続評価して新規違反と既存違反の解消を判定。修正案・外部連携 | ラベル管理、ライブ保存先のDSPM、バックアップのSensitive Data Monitoringは別機構。原文非送信を全製品共通と断定できない |
| IBM Guardium Exposure Manager | 保存先・端末資産と方針違反、データの流れとアクセス | 未解決/再検査待ち/解決済み、担当者、履歴、Jira/ServiceNow依頼。保存先側は完了操作後の予定評価で残存違反なら再び未解決 | Guardium DSPMとは機構名を区別。データ内容の分析に必要な読み取り権限がある。「検査器が本文を読まない」方式ではない |
| Cortex Cloud Data Security / Cortex Data Security | バケット・ファイル保存・管理/自社管理DB、業務クラウド等。機密分類・危険・データ移動の検知 | 危険の優先化とXSOAR等による修正手順。2026-09-15にCortex Data Securityの一般提供を発表 | 古いPrisma Cloud Data Securityの販売終了と現行DSPMを混同しない。10月提供予定の機能は提供済みと数えない |
| Wiz DSPM | クラウドの保存データ、分類とアクセス・公開・攻撃経路の関連 | クラウドの他の危険とまとめて優先化し対応。Matillionの公開顧客事例がある | 全件/標本、全対象の原文保持、再発と修正後の再検査の仕様は本資料で未確定 |
| Netwrix Auditor + Data Classification | Windows/NAS系、SharePoint/Online、SQL Server | 分類結果から検索・報告・警告。分類更新には別処理の時間差がある | 接続用DBと権限が必要。属性の更新前は変更の警告に分類が付かないことがある。原文ゼロ保持の保証は未確認 |
| Netwrix Access AnalyzerのSensitive Data Discovery | AWS、Dropbox、複数DB、Exchange、ファイル、SharePoint等を別対応表で説明 | 内容検査をアクセス監査と組み合わせる | Auditorとは別製品系統。名前の似た製品の対応先を合成しない |
| Datadog Sensitive Data Scanner：Cloud Storage | 顧客AWS内のEC2検査器でS3のCSV/JSON等のテキストを検査。提供者の検出規則群 | 検出保存先・ファイルと所有者を表示。関連する設定不備では状態・担当・Jira・自動手順・履歴を利用 | S3本文は顧客内で読み、検出種・位置をDatadogへ送信と説明。S3原本を自動で伏字化する機能ではない。ログ側の事例保存/集約をS3へ一般化しない |

各行の出典：Sentra [保存先](https://sentra.io/integrations)、[検査深度](https://sentra.io/blog/dspm/full-data-scan-or-sampled)、[警告・再検査API](https://sentra.io/learn/sentra-mcp-server-ai-driven-data-security-operations)。Concentric [製品](https://concentric.ai/platform/)、[S3](https://concentric.ai/integrations/aws-s3/)、[AI FAQ](https://concentric.ai/wp-content/uploads/2025/06/AI_FAQs_June2025-Mary-B.pdf)。Symmetry [AWS配置](https://aws.amazon.com/blogs/apn/cloud-native-data-security-posture-management-deployments-on-aws-with-symmetry-systems/)、[2026年資料](https://www.symmetry-systems.com/wp-content/uploads/2026/02/Symmetry-Systems-DataGuard-DataSheet-202602.pdf)。Securiti [製品](https://securiti.ai/dspm/)、[成熟度の提案](https://securiti.ai/dspm-maturity-model/)。Rubrik [方針](https://docs.rubrik.com/en-us/saas/dspm/dsp_policies.html)、[対応表](https://docs.rubrik.com/en-us/compat_matrix/compat_matrix/cm_rsc_products.html)。IBM [問題管理](https://www.ibm.com/docs/en/exposure-manager?topic=managing-issues)、[製品](https://www.ibm.com/products/guardium/guardium-exposure-manager)。Cortex [管理ガイド](https://docs-cortex.paloaltonetworks.com/r/Cortex-CLOUD/Cortex-Cloud-Posture-Management-Documentation/What-is-Cortex-Cloud-Data-Security)、[一般提供発表](https://www.paloaltonetworks.com/blog/security-operations/cortex-data-security-ga-dlp-ddr/)、[業務クラウド対象拡大](https://www.paloaltonetworks.com/blog/cloud-security/expanding-cloud-data-footprint/)。Wiz [DSPM](https://www.wiz.io/blog/wiz-becomes-first-cnapp-to-deliver-integrated-data-security-posture-management)、[顧客事例](https://www.wiz.io/customers/matillion)。Netwrix [Auditor 10.8](https://docs.netwrix.com/docs/auditor/10_8/admin/settings/sensitivedatadiscovery)、[Access Analyzer](https://docs.netwrix.com/docs/accessanalyzer/11_6/sensitivedatadiscovery/overview)。Datadog [S3接続](https://docs.datadoghq.com/security/sensitive_data_scanner/setup/cloud_storage/)、[問題調査](https://docs.datadoghq.com/security/sensitive_data_scanner/guide/investigate_sensitive_data_findings/?lang_pref=en)。

## Sentryのような運用に近い具体例

### IBM：完了操作と再評価を分ける

公式操作文書は、担当・変更履歴・外部依頼に加え、保存先側の問題では完了操作後に再検査待ちへ進み、予定された方針評価で違反があれば未解決へ戻ると説明する。これは単なる手動終了より比較の参考になる。ただし、端末側の状態遷移は異なる。また、許可するデータ種を方針に追加して違反を消す操作もあるため、「解決済み」は秘密の削除を必ず意味しない。[IBM問題管理](https://www.ibm.com/docs/en/exposure-manager?topic=managing-issues)

### Rubrik：継続評価はあるが方針の停止でも閉じる

既存の違反が解消したか継続評価する仕様がある。一方、方針の無効化や削除でも、その方針の違反は閉じられる。状態と実データへの修正を別に記録する必要がある。[方針評価](https://docs.rubrik.com/en-us/saas/dspm/dsp_policies.html)、[方針操作](https://docs.rubrik.com/en-us/saas/dspm/actions_available_data_security_policies.html)

### Sentra：検査範囲の可視化と検査要求

全量と標本検査、ファイルの選択率と読取り深度を区別し、保存先ごとに設定する。変更したファイルの差分検査、各資産の実検査範囲表示を説明している。2026年の公開操作説明には警告状態・コメント・再検査要求がある。状態の変更と、実データの修正後検査を同義としない。全量検査の能力は提供者説明であり、独立した負荷/全形式試験ではない。[検査範囲](https://sentra.io/blog/dspm/full-data-scan-or-sampled)、[操作](https://sentra.io/learn/sentra-mcp-server-ai-driven-data-security-operations)

### Datadog：ストレージとログの管理は別の画面・経路

S3は顧客AWS内に検査器を配置し、内容ではなく検出種・位置を送る。管理画面から所有者に適切な保存か確認し、必要なら移動・削除を行う。関連する設定不備の警告では担当、状態、修正案、Jira、手順実行、履歴を扱う。ログの側は規則・ログ形式・サービスによる集約と傾向表示があり、代表ログは最大5件、既定7日保存される。このログ仕様をS3の原文保持に当てはめない。逆にS3の原文非送信説明をDatadog全製品に広げない。[S3検査](https://docs.datadoghq.com/security/sensitive_data_scanner/setup/cloud_storage/)、[調査画面](https://docs.datadoghq.com/security/sensitive_data_scanner/guide/investigate_sensitive_data_findings/?lang_pref=en)

## AI、局所処理、暗号文分類を区別する

Concentricの2025年FAQでは、公開資料で学習した表現モデルによる意味分類を、自社SaaS内で実行すると説明している。第三者のAIサービスは使わないが、原文を同社処理基盤で読む。抽出原文は処理後破棄、検出値は伏字で保存する一方、氏名・メールは例外とする。生成AIではないという製品説明から、個人情報を保存しないと結論づけてはいけない。[AI FAQ](https://concentric.ai/wp-content/uploads/2025/06/AI_FAQs_June2025-Mary-B.pdf)

SentraやSymmetry、Datadog S3の局所検査も、信頼する検査器が平文を読む方式である。「外部LLMに原文を送らない」「原文を長期保持しない」「信頼境界内で読む」「暗号文のまま計算する」は違う条件。今回の直接候補の公開資料から、任意企業秘密を暗号文だけで意味分類する標準商用機能は確認できなかった。不在の証明ではない。秘密計算やゼロ知識証明の適用条件は[既存関連調査](zero_knowledge_sensitive_data_research_20261007.md)、[平文非開示分類](confidentiality_classification_without_plaintext_20261007.md)を参照。

## 隣接：ログ保護とSentryそのもの

- **CloudWatch Logs data protection**：ログ取込み時の機密検出と表示遮蔽、監査結果と件数の監視。既に取り込んだログを遡って検査するものではない。`logs:Unmask`権限で値を見られるため不可逆な削除と異なる。[仕様](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html)
- **Datadog Observability Pipelines**：自社側でログを伏字化してから外へ送る方式を選べる。クラウド側検査は原文が先に到達する。不可逆なRedactと、復元権限を持つMaskを区別する。保存S3の巡回とは別の処理。[局所処理](https://docs.datadoghq.com/observability_pipelines/processors/sensitive_data_scanner/)、[ログ設定](https://docs.datadoghq.com/security/sensitive_data_scanner/setup/telemetry_data/)
- **Sentry**：発生の集約、問題状態、解決後の再発という操作の参照先。アプリのエラー等を対象とし、任意ストレージの機密内容を巡回分類する直接代替ではない。送信前SDK、サーバ側、顧客内Relayの除去は異なる処理地点。[状態](https://docs.sentry.io/product/issues/states-triage/)、[情報除去](https://www.sentry.help/en/articles/13964268-what-are-sentry-s-data-scrubbing-options)

## 資料保存と取得制限

[取得台帳](telescreen_related_storage_sources_20261009.json)にURL・取得日時・SHA-256・HTTP失敗を記録し、原本を[保存先](../disclosures/raw/telescreen_related_20261009/storage/)に置いた。圧縮応答は原バイト列を維持し、解凍した本文を派生ファイルとして保存した。**Rubrik文書の直接取得はログイン画面に転送されるものがあり、本文取得成功とは数えない。** IBMの一部はHTTP403。これらは検索サービスが表示する公開公式文書本文で確認できた範囲に依拠し、完全なHTML原本を保存できたと表現しない。古いNetwrix URLの404は現行10.8文書で補った。

公開説明から実装の非保持保証や精度の優劣は確定できない。取得資料の版・地域・契約・試験提供条件、対応形式、読取り量、検査失敗、更新遅延、状態再開条件を導入試験で確かめる必要がある。
