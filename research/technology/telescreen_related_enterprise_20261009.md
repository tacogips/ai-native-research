# 機密データの保存状態を監視する企業基盤・国内製品の比較

調査基準日: 2026-10-09。公開公式文書・製品資料・公開API解説を取得して比較した。非公開の実装、顧客画面、社内情報を含まない。「telescreen」は比較の問いの名称であり、本稿はその非公開仕様や実装を記述しない。企業基盤の対象は、機密データが保存された場所・公開範囲・権限を調べ、検出結果を問題として運用する仕組みである。

## 結論と比較範囲

**保存状態の継続検査を、Sentryのような問題管理へ結び付ける既存製品はある。** AWS中心ならMacie、Google Cloud中心ならSensitive Data Protection、多種の保存先をまとめるならBigID・Cyera・Varonisが直接比較対象となる。Microsoft Purviewも候補だが、Data Map、DSPM、DLP、顧客内のInformation Protection scanner（顧客内検査器）は別機構であり、同じ名前の下にあることだけで対象や問題管理が共通とはいえない。国内ではP-Pointer File Securityが、端末・ファイルサーバの更新検出と利用者による対処まで比較的近い。

送信時の遮断を中心とするNetskope・Forcepoint・Proofpointは隣接する比較対象である。Cyberhavenは2026年の公開DSPM提供情報を踏まえ、以前の端末DLP専用という扱いを更新した。Log360も公式に保存データ探索を示すが、セキュリティログの集約・行動異常と、保存ファイルの問題管理を混同しない。AeyeScanはWebの脆弱性診断であり、保存データを分類する直接の代替ではない。以下の出典と限界を伴う比較は製品推奨順位や実測精度順位ではない。

DSPM（Data Security Posture Management）は、データの所在・機密性とアクセス権・公開状態を合わせて危険な保存状態を見つける分野。DLP（Data Loss Prevention）は、機密データの利用・移動・共有を検査し、規則違反を通知または阻止する分野。findingは検出結果、caseは複数検出をまとめて扱う問題、remediationは権限変更・移動・削除など実データや設定への修正を指す。本稿の「未確認」は機能が存在しないという断定ではなく、取得した公開資料では保証条件を確定できないという意味である。

## 1. 保存先と展開方式

| 製品・機構 | 公開資料で確認した保存先・検出 | 継続性と展開境界 | この比較での位置付け |
|---|---|---|---|
| Microsoft Purview Data Map / DSPM / DLP | Data MapはAzure Blob・ADLS・Azure Files・SQL等を個別対応表で区別。DSPMはMicrosoft 365・Azure・Fabric・接続された第三者SaaS（外部サービス型の提供）の危険を集約。オンプレミスDLPはファイル共有・SharePoint Serverを別検査器で検査 | Data Mapの接続・分類・保護は保存先別。新DSPMとclassicの資料を区別。Microsoft Sentinel データ統合保存基盤経由の非Microsoft情報は一部試験提供。顧客内検査器はWindows Server・SQL・資格情報が必要 | 直接候補だが、Data Mapの分類結果がすべてDLP 警告/問題になるという仕様ではない。[MS01](https://learn.microsoft.com/en-us/purview/data-map-data-sources)、[MS02](https://learn.microsoft.com/en-us/purview/data-security-posture-management-learn-about)、[MS09](https://learn.microsoft.com/en-us/purview/dlp-on-premises-scanner-learn) |
| Google Cloud Sensitive Data Protection（SDP） | Cloud Storage・BigQuery・Datastoreの保存検査。別途探索によるデータ概要、APIへの直接入力、Google外のデータを送る外部データ送信型検査 | 保存検査の検査処理、定期起動、組織/フォルダ/プロジェクトの概要生成を区別。外部データ送信型もGoogleへの本文送信を伴う方式 | Google Cloudの直接候補。単独で全ファイルサーバ/全DBを現地検査する製品ではない。[GO02](https://docs.cloud.google.com/sensitive-data-protection/docs/inspecting-storage)、[GO07](https://docs.cloud.google.com/sensitive-data-protection/docs/concepts-method-types) |
| Google Workspace Drive DLP | Driveファイルと共有を規則で検査。事前定義検出器、語句、正規表現等 | Driveのファイル変更が検査契機。規則反映に最大24時間、未対応ファイル・誤検出/見逃しがある。Workspaceの対象契約プランが必要 | Driveに限定した直接候補。SDPのGoogle Cloud 検査処理/APIとは別サービス。[GO05](https://knowledge.workspace.google.com/admin/security/dlp-for-drive-faq) |
| Amazon Macie | 対応するS3 汎用バケットのオブジェクト。個人情報・支払情報・AWS資格情報・カスタム識別器 | 自動探索は日次の代表標本選択。別の探索検査処理で対象・周期等を設計。複数AWSアカウントは委任管理者、リージョンごと。DB、GCS、Azure Blob、任意NASの直接検査器ではない | AWS S3の直接候補。標本検査を全件即時検査と扱わない。[AW01](https://docs.aws.amazon.com/macie/latest/user/discovery-asdd-how-it-works.html)、[AW06](https://aws.amazon.com/macie/pricing/) |
| BigID | 構造化DB、非構造化ファイル、Google Drive等を接続機構で統一。PII（個人識別情報）・企業機密・資格情報などの秘密値の分類を公式資料が説明 | 検査器はDockerコンテナ。BigID クラウド、顧客内、顧客クラウドアカウントに配置可能。REST接続先は検査器からの着信が必要、Java接続は検査器が直接アクセス | 多種の保存先・分散検査器の直接候補。接続方式ごとの権限・送る結果を要確認。[BI01](https://developer.bigid.com/connectors/what-is-a-bigid-connector/)、[BI06](https://home.bigid.com/hubfs/whitepapers-and-data-sheets/CISO-Guide-to-AI.pdf) |
| Cyera | AWS・Azure・GCPの公開ストレージ/DBと、Drive・OneDrive・Salesforce・Box等の公開機密ファイルを対象とする説明。PIIから業界特有の企業機密まで | フルSaaSと顧客アカウント内Outpostが選択肢。変更監視・分類とDLPを組み合わせる。全接続先の同一周期・全件検査は未確認 | 多種の保存先と修正の直接候補。[CY01](https://www.cyera.com/contact-us)、[CY04](https://www.cyera.com/solutions/public-exposure)、[CY05](https://www.cyera.com/blog/a-leap-forward-cyera-enhances-its-market-leading-llms-with-industry-specific-precision) |
| Varonis | S3・Azure Blob・RDS/EC2 DB・Google Cloud、NAS/ファイル共有、Microsoft 365、SaaS等。保存内容と有効な権限・実アクセスを関連付ける | Collectorを顧客内に置く方式とDatAdvantage Cloudを区別。IaaS資料は標本だけに依存せずバケット・Blob・ファイルを追跡すると説明。ただし全形式・全サイズ・全版の検出保証ではない | 保存状態・過剰権限・権限修正までの直接候補。[VA04](https://www.varonis.com/coverage/iaas)、[VA05](https://www.varonis.com/coverage) |
| Cyberhaven DSPM | 端末の保存ファイル、クラウド保存先、SaaS/PaaS/IaaS。本文分類と、由来・複製・変更を表すdata lineage（データの由来と移動の履歴）を組み合わせる | 2026年の公開提供情報がある。端末/クラウド 監視プログラムとSaaS管理。接続先別の権限・原文送信・検査周期の詳細仕様は未確認 | 保存データ監視へ範囲を広げた候補。宣伝上の「即時」を任意保存先の即時全件処理保証としない。[CH02](https://events.cyberhaven.com/on-demand/winter-2026-launch/)、[CH04](https://www.cyberhaven.com/product/dspm) |
| ManageEngine Log360 | 公式利用例はネットワーク内の保存PIIを数値構造・語句・カスタム規則で探索し、該当フォルダへのアクセスを監視 | ログ管理・問題管理・利用者行動分析を組み合わせる。現行契約で必要な探索構成要素、Log360 Cloudとの機能差、保存先別接続は未確認 | 部分的に直接候補。一般SIEM（セキュリティログの統合管理）機能だけで本文分類を保証しない。[LO01](https://download.manageengine.com/log-management/use-cases/discover-sensitive-data-in-the-network-log360.pdf) |
| P-Pointer File Security（アララ） | PC・ファイルサーバの住所・メール・マイナンバー等。保管ルールに沿って移動/削除 | 顧客内管理サーバとWindowsの検査プログラム。差分検査・ファイル更新時検査・予約実行。非WindowsファイルサーバはWindows 検査プログラムからネットワーク越しに検査 | 国内の直接候補。任意SaaS/API/DB接続は公開資料で未確認。[JP01](https://www.ppointer.jp/product)、[JP02](https://www.ppointer.jp/operation) |
| InterSafe ILP + PIS（ALSI） | Windows PC/サーバの個人情報・マイナンバー。FileProtectionと組み合わせて検出・暗号化 | PISは追加選択機能。顧客内で動き、すみずみ君の検出機構を使用。WorkFlow/DeviceControl等は別の組合せ | 国内の直接検出+保護候補。承認機構の存在と、保存状態findingの期限管理を区別する。[JP04](https://www.alsi.co.jp/solution/cybersecurity/ilp/alliance/)、[JP05](https://www.alsi.co.jp/security/data/ISFPv8.1_brochure.pdf) |
| すみずみ君（三菱電機ソフトウエア） | マイナンバー辞書、固定語句・正規表現辞書、Windowsから読めるファイルやUSB等 | コマンドラインをWindowsタスクスケジューラへ登録可能。集中運用製品は別途仕様を確認する | 検出器の比較候補。PISと独立した検出性能実績として二重計上しない。[JP06](https://www.sumizumikun.jp/sumizumikun/qa.html) |

## 2. Sentryに近い問題管理はどこまであるか

通知先がSlackであることと、Slack内容を検査できることは別である。同様にJira/ServiceNowへ書き出せることと、元データの修正・再検査が確認されることも別である。

| 機構 | 集約・通知・担当 | 修正と状態 | 再発・重複・期限・再検査について確認できた境界 |
|---|---|---|---|
| Macie → EventBridge/Security Hub/外部管理 | findingをAPI取得、EventBridgeからLambda/SNS等へ配信。AWS通知やSIEMへの連携を構築可能 | Lambdaで権限制限等を実装可能。Macieの抑制・管理上の保管済み状態への変更は実データの修正ではない | **機密データfindingは毎回新規で一意、`count=1`（出現回数1）。既存の設定違反検出の再発更新と異なる。** 保存先と規則を基に外側で重複/再発を設計。配送は配信成功を必ず保証する方式ではないためAPIによる回収も受入試験する。[AW07](https://docs.aws.amazon.com/macie/latest/user/findings-publish-event-schemas.html)、[AW08](https://docs.aws.amazon.com/macie/latest/user/findings-monitor-events-eventbridge.html)、[AW09](https://docs.aws.amazon.com/eventbridge/latest/ref/events-ref-macie.html) |
| Google SDP → Pub/Sub/Security Command Center/外部管理 | データ概要の重大な変更をPub/Sub通知。保存検査処理の結果を保存/発行 | 外部処理で修正・担当・期限を組み立てる。検査と匿名化されたコピーの生成は別操作 | 概要変更通知は全文一致箇所のfinding一覧と同じではない。Pub/Sub 通知イベントを受け取っただけで全データ再検査完了とはいえない。[GO03](https://docs.cloud.google.com/sensitive-data-protection/docs/dp-receive-pubsub-messages)、[GO04](https://cloud.google.com/security/products/sensitive-data-protection) |
| Workspace Drive DLP + Alert center | 規則による管理者通知。Alert centerは1警告につき1担当、未着手/進行中/Closed（処理終了）等 | 調査機構の利用と共有対策。Closed（処理終了）は管理上の状態変更 | 関連警告・履歴を見られる。閉じた同一ファイルの再発時再開や期限超過通知、原データの再検査成功との連動はこの資料では未確認。[GO06](https://support.google.com/a/answer/9275024?hl=en)、[GO10](https://knowledge.workspace.google.com/admin/security/view-and-change-alert-assignees) |
| Purview DLP alerts / DSPM | DLPは単一・集約警告、担当、コメント、作業の流れ履歴。DSPMは危険の分析と対策推奨。AIによる警告の優先化は試験提供を区別 | DLPの状態をResolved（解決済み）へ変更可能。DSPMの推奨から保護規則を作成 | DLP集約には契約条件がある。Resolved（解決済み）を再検査で機密データが消えた証明と扱わない。Data Map 検査との全連動は未確認。[MS03](https://learn.microsoft.com/en-us/purview/dlp-alerts-get-started)、[MS04](https://learn.microsoft.com/en-us/purview/dlp-alerts-dashboard-get-started)、[MS05](https://learn.microsoft.com/en-us/purview/deploymentmodels/depmod-dspm-intro) |
| BigID Data Posture API | caseLabel、policyName、severityLevel、assignee、dataSourceNameを外部問題へ写せる。ServiceNow IRM連携 | GET `/api/v1/actionable-insights/all-cases`、PATCH `.../case-status/{caseId}`、一括更新。resolvedとauditReasonを設定 | **公式操作解説は外部への書出し後resolvedにする例を示し、再検査を必須化していない。** 実運用では外部問題の登録を「修正完了」に写さない。期限や再発openの詳細条件は未確認。[BI02](https://developer.bigid.com/api/data-posture-api-tutorial/)、[BI03](https://home.bigid.com/demo-bigid-servicenow) |
| Cyera remediation / integrations | データ所有者へ振り分け、利用者の意思決定、上位責任者への依頼。Slack通知、ServiceNow incidents、Jira/SOAR等 | 公開共有撤回・権限制限・mask・MIP label・削除等を人の確認/自動作業の流れで実行。修正前の内容確認と監査履歴を記載 | 修正前の内容確認・監査と、修正後の同一保存オブジェクト再検査は区別する。全接続先の再開・期日・結果状態のAPI契約は未確認。[CY02](https://www.cyera.com/solutions/remediation)、[CY03](https://www.cyera.com/integrations) |
| Varonis | 保存内容とアクセス・公開リンク・危険な権限を統合。危険を優先化 | Salesforceの公開リンクや過剰権限をUI/継続処理で取り消す。IaaS設定修正 | 公開リンク撤回は実修正として具体的。すべての保存先で所有者依頼・期限・同一finding再発が同じ仕様とは未確認。[VA02](https://www.varonis.com/coverage/salesforce)、[VA04](https://www.varonis.com/coverage/iaas) |
| Cyberhaven / Log360 | Cyberhavenは本文分類とデータの由来・移動を結び付け、保存状態の危険を検出。Log360はPII探索+フォルダアクセス警告 | DLPによる利用制御や問題対応と組合せる | Cyberhavenの所有者への依頼・期限・問題APIの仕様は未確認。Log360の行動異常の解決と、残存PIIの再検査は別。[CH04](https://www.cyberhaven.com/product/dspm)、[LO01](https://download.manageengine.com/log-management/use-cases/discover-sensitive-data-in-the-network-log360.pdf) |
| P-Pointer / InterSafe / すみずみ君 | P-Pointerは利用者に違反を見せ、グループ/タスク結果CSVと対処結果を管理者が確認。InterSafeは申請・承認 | P-Pointerは承諾後の自動処理・手動移動/削除。InterSafeは暗号化や持出し承認。すみずみ君は検出結果を運用に組み込む | 更新監視・定期検査はあるが、Sentry型の1問題再開、担当者依頼の期限、督促、修正証明の公開APIは未確認。[JP01](https://www.ppointer.jp/product)、[JP04](https://www.alsi.co.jp/solution/cybersecurity/ilp/alliance/)、[JP06](https://www.sumizumikun.jp/sumizumikun/qa.html) |

## 3. 原文・一致文字列・通知の保存を分ける

**「検査後原ファイルを破棄」「一致文字列を返さない」「付随情報のみ保存」「原文を外へ送らない」は四つの異なる性質である。** 暗号化保存や内容閲覧権限は安全性の制御だが、原文の非収集・非保存にはならない。ファイル名、保存オブジェクトの識別名、DB列名、所有者名にも機密が入るため、付随情報という名だけで無害とはいえない。以下は公式資料の仕様またはベンダーの公開説明であり、契約環境の実通信・保存を監査した結果ではない。

| 製品/機構 | 検査対象本文 | 検出原文・証拠保存 | 原文最小化を評価する際の注意 |
|---|---|---|---|
| Macie | S3 保存オブジェクトを取得・分析し、そのコピーは分析終了後破棄 | finding/探索結果は型・位置を記録。finding90日、探索結果は顧客S3に保存可能。Revealは元S3から一致値を再取得し、各型1〜10件、各1〜128文字、最大100型を返す | 追加の原文取得用の役割/暗号鍵権限を分離できる。元保存オブジェクトが変更/不可読なら検出値の標本取得不能。通知側で勝手にRevealを呼ばない。[AW01](https://docs.aws.amazon.com/macie/latest/user/discovery-asdd-how-it-works.html)、[AW02](https://docs.aws.amazon.com/macie/latest/user/findings.html)、[AW03](https://docs.aws.amazon.com/macie/latest/user/findings-retrieve-sd-proc.html)、[AW04](https://docs.aws.amazon.com/macie/latest/user/findings-retrieve-sd-options.html)、[AW10](https://docs.aws.amazon.com/macie/latest/user/findings-investigate-sd.html) |
| Google SDP | 本文を直接送るAPIは本文をGoogleへ送るが要求本文を継続保持しない処理、要求本文は保存しない。保存検査/外部データ送信型/探索は別処理 | quote（一致文字列）は既定で返さず位置を返す。`InspectConfig.include_quote=true`かつBigQuery findings保存を有効にすると一致原文をBigQueryへ複製。検査処理の状態・処理量・型別概要も保存 | 本文を直接送るAPIの非保存説明を、保存検査処理の全結果・通知・ログに一般化しない。一致文字列が不要なら明示設定/回帰確認を行う。[GO01](https://docs.cloud.google.com/sensitive-data-protection/docs/quote)、[GO07](https://docs.cloud.google.com/sensitive-data-protection/docs/concepts-method-types) |
| Workspace DLP snippets | Google内の本文をDLPで検査。SDPと設定が異なる | Sensitive content storageをOnにすると一致値と前後各100Unicode文字を収集。一致値と周辺文字の抜粋500文字上限、ログ180日。**元内容の削除・変更でも一致値と周辺文字の抜粋は残る。** Offなら新規一致値と周辺文字の抜粋記録停止 | 閲覧権限・管理者設定を分離。削除・復元・BigQuery 外部への書出しも別管理対象。設定の既定値は本資料から断定しない。[GO09](https://knowledge.workspace.google.com/admin/security/view-content-that-triggers-dlp-rules) |
| Purview | Microsoft処理、Data Mapの検査基盤、顧客内検査器を対象別に区別 | DLP 警告は一致内容・周辺文脈・内容確認の閲覧権限が別。検査器は一時ファイル用保存領域と構成/運用SQLが必要 | 内容閲覧権限を付けなければ非収集になるとはいえない。DLP・DSPM・Data Mapの原文保存期間や一致値と周辺文字の抜粋属性を一律保証しない。[MS03](https://learn.microsoft.com/en-us/purview/dlp-alerts-get-started)、[MS08](https://learn.microsoft.com/en-us/purview/deploy-scanner-prereqs) |
| BigID | 検査器配置を選べる。接続機構は本文の連続データを検査器へ返す | 検査地と問題 APIは確認したが、一致値の標本・照合用索引・処理の記録の無効化/保存期間は未確認 | 顧客内検査器だけを根拠に「原文が一切クラウドに出ない」と断定できない。返す分類結果と検出値の標本のデータ項目の仕様を契約前に取得する。[BI01](https://developer.bigid.com/connectors/what-is-a-bigid-connector/) |
| Cyera | FAQはOutpost内検査とフルSaaS、Data Insights SaaSへ付随情報のみ送信と説明 | 付随情報の具体データ項目の仕様、検出値の標本の定義、AI入力/補助保存の全範囲は公開FAQで確定できない | 「付随情報のみ」を、フルSaaSの検査器も本文を読まない意味にしない。保存先/モデル/機能ごとの詳しい設計資料は要依頼。[CY01](https://www.cyera.com/contact-us) |
| Varonis | 顧客内Collectorは顧客内で本文処理。DatAdvantage Cloudは原文をクラウドへ取得して分類 | 通常の分類経路では原文は持続保存しない/分類後破棄、付随情報・分類結果はクラウド保存。File Analysis権限で特定原文の取寄せも可能。**例外としてAI Monitoringを利用者が有効化すると、Copilot・AgentForce・ChatGPT Enterprise等の監査ログ中の質問文・回答文をSaaSへ収集・分析・保存する。質問文の契約上の保存期間は180日、閲覧にはAI Prompt auditor（AI質問文の監査者）権限が必要。** | SaaSの一時原文取得と顧客内本文処理を区別。「no persistent storage」は「no transfer」と異なる。[VA01](https://www.varonis.com/trust/security) |
| Cyberhaven | 端末/クラウド 監視プログラムが非構造化/半構造化データを提供しSaaS処理 | 公開安全管理方針は顧客別GCP資源、北米保存（他地域は依頼）、顧客SaaSから派生した情報の保存を説明 | この安全管理方針は原文ゼロ保存の保証ではない。由来と移動履歴/証拠/本文の具体データ項目の仕様・保存期間は未確認。暗号化と非保存を混同しない。[CH01](https://www.cyberhaven.com/legal/security-policy) |
| 国内検出器 | P-Pointerは検査プログラム内検査・管理サーバへの結果報告。PIS/すみずみ君はWindows上で本文検査 | P-Pointerには結果容量と圧縮ファイル一時展開領域。管理サーバへ返す一致原文の有無・結果消去保証は未確認 | 自社配置は外部SaaSへの送信を避ける設計候補だが、結果・一時展開・CSVも機密になり得る。未公開データ項目の仕様を補わない。[JP02](https://www.ppointer.jp/operation)、[JP04](https://www.alsi.co.jp/solution/cybersecurity/ilp/alliance/) |

## 4. 隣接製品を使うなら何が増えるか

| 製品 | 直接近い部分 | 原文・展開・契約境界 | 保存状態監視との違い |
|---|---|---|---|
| Netskope DLP / AISecOps | クラウド/web/email検出を問題に集約・重複低減・人のreviewと修正へ接続。API Data Protectionもある | Forensicsは違反保存オブジェクトを顧客指定の保存先に置く。原ファイルへのアクセスを有効にすると問題に関する証拠ファイルを取得可能。クラウドストレージ推奨、China 利用組織の環境では当該証拠保存機能不可という資料上の差 | 問題集約の比較は有用。全ストレージ/DBの保存時全件検査、AI 問題機能の契約・本文処理仕様は別確認。[NE01](https://docs.netskope.com/en/forensics)、[NE02](https://docs.netskope.com/en/downloading-dlp-incident-files)、[NE03](https://www.netskope.com/netskope-one/agentskope/dlp-aisecops-agent) |
| Forcepoint DLP | 探索とemail/web/端末の違反を問題として扱う | v9文書は問題データベースをSQLに保存、証拠記録は本文・From/To/Cc・添付等を含む。v10.3削除操作は証拠記録も消し監査を残す。版差を維持 | 原文を残さない軽量警告基盤とは異なる設計。v9のDB説明を現行クラウド版全部へ一般化しない。[FO01](https://help.forcepoint.com/dlp/90/dlphelp/034A81A6-7D55-46B1-8B41-92A37085D7FF.html)、[FO02](https://help.forcepoint.com/dlp/10.3.0/dlphelp/57B64CC0-C480-42E4-B0A6-851594E0AF06.html) |
| Proofpoint Enterprise DLP | email/クラウド/端末の検出と統合問題管理、ServiceNow等との連携 | Endpoint DLP/ITMの個人情報処理の説明資料は任意画面取得/本文を含み得る。保存期間は30/90/120/366日選択、アクセス権制御。文書更新2024-05-15で、全製品の現行共通仕様とはしない | 送信・行動の文脈が中心。DSPM等の別製品のデータ項目の仕様や処理場所をEndpoint文書から推論しない。[PR01](https://www.proofpoint.com/us/products/data-loss-prevention)、[PR02](https://www.proofpoint.com/us/legal/trust/endpoint-dlp-and-itm) |
| AeyeScan | 定期Web脆弱性検査と修正方法の報告 | SaaS、日本AWSリージョン保存、価格は個別見積。OWASP/ASVS/IPA等の脆弱性診断 | 保存オブジェクトのPII/企業機密分類の直接証拠は本資料にない。アラートの見た目やAI採用だけで同種製品としない。[JP07](https://www.aeyescan.jp/) |

ランサムウェア検知・端末攻撃検知（EDR）、バックアップ、秘密保管庫は、機密データの所在発見とは別の目的を持つ。多機能な製品では併設されるが、暗号化・秘密の保管・侵入検知だけで「機密データが不適切な場所に残っている」を分類し問題管理するとはいえない。

## 5. 国内向け検出・ライセンス・検査の限界

P-Pointerの公開説明は住所・メール・マイナンバーを挙げ、国内ファイル監査の実用的な対象を示す。日本語の製品であることと、日本語の任意機密文脈を高精度に理解することは別である。FAQでは画像、暗号化/パスワード保護ファイルの内容検査は不可とし、保護ファイルの所在を結果に載せると説明する。これは「未検査」を「個人情報なし」へ写してはいけない例である。[JP01](https://www.ppointer.jp/product)、[JP03](https://www.ppointer.jp/faq)。InterSafe PISは個人情報/マイナンバー、同製品の暗号化済みファイルの検出を説明するが、任意方式の暗号文を直接分類する技術ではない。すみずみ君FAQはマイナンバー辞書・辞書追加・定期起動を示す。[JP04](https://www.alsi.co.jp/solution/cybersecurity/ilp/alliance/)、[JP06](https://www.sumizumikun.jp/sumizumikun/qa.html)。

Google SDPの公開検出器には日本関連識別子もあるため、海外製品=日本情報を一切検出できないとはいえない。ただし、infoTypeの搭載と実データに対する適合率・再現率は別であり、住所表記、氏名、マイナンバーの周辺語、顧客独自の企業機密を評価する必要がある。[GO08](https://docs.cloud.google.com/sensitive-data-protection/docs/infotypes-reference?hl=ja)。Cyeraの企業機密分類やBigIDの資格情報などの秘密値分類はベンダー説明として記載し、全日本語資料の精度・秘密の有効性検証・資格情報の自動失効まで保証しない。[CY05](https://www.cyera.com/blog/a-leap-forward-cyera-enhances-its-market-leading-llms-with-industry-specific-precision)、[CY06](https://www.cyera.com/blog/secure-m365-files-that-sensitivity-labels-cant-reach-with-cyera-omni-dlp)、[BI06](https://home.bigid.com/hubfs/whitepapers-and-data-sheets/CISO-Guide-to-AI.pdf)。

費用は基本契約だけでなく、検査量・保存量・連携先・AI運用を分ける。Macieはバケット評価と検査の費用があり、S3のAPI等も考慮する。Purviewは対象機能ごとの利用者契約、Data Map等の別課金、Security Copilotの処理量を区別する。Posture Agentは試験提供、Microsoft 365 E5とSCU（Security Compute Unit: AI処理量の課金単位）を要求する資料がある。これを標準DLP全部の必要条件としない。[AW06](https://aws.amazon.com/macie/pricing/)、[MS05](https://learn.microsoft.com/en-us/purview/deploymentmodels/depmod-dspm-intro)、[MS06](https://learn.microsoft.com/en-us/purview/copilot-in-purview-posture-agent-get-started)。Workspaceは対応契約プランを確認し、Drive DLPと調査機構の権限/契約プランを別に確定する。[GO05](https://knowledge.workspace.google.com/admin/security/dlp-for-drive-faq)、[GO09](https://knowledge.workspace.google.com/admin/security/view-content-that-triggers-dlp-rules)。BigID・Cyera・Varonis・Cyberhaven等は、本調査で一律価格や必要契約構成の全条件を確定していない。

## 6. 公開情報から導く評価・設計案

以下は公開比較をもとにした設計上の提案であり、特定の非公開製品の仕様ではない。

1. **問題の同一性**を決める。利用組織の環境・保存先・保存オブジェクト/レコード識別子・版・規則版を保持し、同じ通知イベントの再配送、同じ保存オブジェクトの残存、修正後の再発、同じ秘密の別コピーを別に表す。機密値そのものを集約キーにせず、必要なら顧客内鍵付きHMACを使う。鍵や低エントロピー値の推測耐性は別評価する。
2. **問題状態と実データ状態を分ける。** `assigned`（担当確定）、`exported`（書出し済み）、`accepted risk`（危険受容）、`remediation requested`（修正依頼）、`remediation executed`（修正実行）、`verified`（再検査済み）を区別する。新しい版の再検査が成功した時だけverifiedへ進め、検査不能・権限切れ・標本未選択を安全判定にしない。
3. **最小の証拠を返す。** 規則ID、機密種別、数、位置、保存資源への参照、処理時刻、検査範囲、判定理由の限定コードを基本にする。元の保存オブジェクトの識別名、利用者名、監査理由や自由記述も機密になり得るため通知を最小化する。原文の内容確認は別権限・短い保存期間・閲覧監査付きの追加経路にする。
4. **通信と保存の実測を行う。** 検査器現地配置、集中管理基盤、モデル呼出し、検出値の標本、詳細ログ、退避ファイル、CSV、問題票/Slackを別に調べる。「原文非保存」は、一時ファイル・外部通知・バックアップ・削除後の残存も含め試験する。
5. **機械的通知の信頼性を確認する。** イベント欠落の回収、再配送の冪等性、検査器停止・期限超過・取消し・規則変更の扱いを試験する。メール/Slack通知の成功をデータ検査の成功に代用しない。
6. **人へ依頼しやすくする。** 所有者が分からない時の代理責任者、期限、督促、誤検出の理由と再評価、削除に必要な承認を設ける。表示上のClosed（処理終了）と危険の受容・削除完了を区別する。

これらのうち公開資料で最も具体的に比較できたのは、Macie/Googleの結果データ項目の仕様と証拠収集、BigIDの問題API、Cyera/Varonisの実権限修正、P-Pointerの利用者による対処である。**期限・修正後再検査・再発再開の全条件を、一つの公開資料で証明できた製品は本稿にはない。** 不在の断定ではなく、導入評価で埋めるべき不足である。

## 7. 原本保存・検証・未完の境界

原本は [enterprise保存先](../disclosures/raw/telescreen_related_20261009/enterprise/)、取得URL・取得日時・HTTP結果・SHA-256は [取得台帳](telescreen_related_enterprise_sources_20261009.json) に保存した。HTML/PDFの取得と、その内容に依拠する分類・分析を区別する。動的なページのHTTP 200や紹介文は、非公開機能の安全性証明ではない。推測URLの404や一般ページへの転送は台帳に残し、本文の根拠には使用しない。

未確認事項: 有償利用組織の環境での操作、全保存先のAPI権限と形式/サイズ/暗号化制限、BigID/Cyera等の一致値の標本やモデル処理経路の詳細、全製品の期限/再発/再検査API、削除後バックアップの残存、日本語実測精度と任意資格情報などの秘密値の有効性確認、現行契約構成見積、変更検査の最大遅延。公開資料の最終更新日が古い場合は、その版の説明として使用し現行全版へ広げない。機能の販売・試験提供・契約提供は本番導入前に再確認する。

## 独立レビュー後の改善

2026-10-09の[独立レビュー](telescreen_review_oss_to_enterprise_20261009.md)を受け、Varonisの通常分類経路とAI Monitoringの質問文・回答文保存を同じ比較欄で区別した。VA01の取得本文を再照合済み。GO06の転送先は台帳に保持し、問題の状態仕様はGO10も併記する。
