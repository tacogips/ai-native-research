# 保存データを継続検査する SaaS DLP 製品の比較

調査日: 2026-10-09。公開されている公式製品説明、操作文書、処理環境の説明、顧客事例を新たに取得して確認した。既存の調査は資料を探す導線としてだけ利用した。比較対象は、利用者の構想である「ストレージ等にある秘密鍵・個人情報・企業秘密を継続検出し、問題を集約して、人への修正依頼と解決確認を進める仕組み」。ローカルの Telescreen リポジトリや非公開実装は閲覧・比較・記載していない。

原本は `research/disclosures/raw/telescreen_related_20261009/saas/` に保存した。[取得台帳・機能別根拠](telescreen_related_saas_sources_20261009.json) に URL、取得日、本文、ハッシュ、成功・失敗、機能ごとの根拠を記録した。以下の「提供」は公開資料上の提供説明であり、契約や実操作の検証結果ではない。

## 1. 最も近い候補

**保存データの問題を Sentry のように集約して解決へつなぐ観点では、Teleskope と Nightfall が最も具体的な公開操作仕様を持つ。** Teleskope はストレージ・データベース・業務クラウドを横断する問題管理と修正手順、Nightfall は検出イベントの重複抑制とサービス別の自動解決条件を説明している。elba は所有者への依頼・未完了作業の追跡が近い。Strac は秘密・個人情報の検出と多様な保存先の修正、自社配置が近い。Metomic には保存データを伏字化・アクセス修正する機能があるが、2026 年の現行サイトは AI とデータの間の通信制御へ重心を移している。

[DLP（情報の持ち出し防止）と保存データ管理を扱う Nightfall](https://www.nightfall.ai/dlp-for-data-at-rest)、[Teleskope Policy Maker](https://docs.teleskope.ai/the-platform/policy-maker)、[elba Data Protection](https://www.elba.security/platform/data-protection)、[Strac SaaS DLP](https://www.strac.io/saas-dlp)、[Metomic の現行 DSPM 説明](https://www.metomic.io/solution/data-security-posture-management/)

どの製品も、名称に DLP や DSPM（保存データの所在・権限・危険性を継続把握する管理）とあるだけで、Sentry 型の再発管理や修正後の再検査まで同一とは判断できない。次の区別を保った。

- **検出対象の集約:** ファイルやメッセージ単位に複数の検出をまとめる。
- **重複抑制:** 同じ問題の再検出で別の警告を増やさない。
- **再発管理:** 一度解決した問題の再出現を同じ問題へ関連付ける。
- **解決確認:** 人が「修正した」と回答すること、状態を Resolved へ変えること、原本を再検査して問題が消えたことを別々に扱う。
- **期限:** 通知の繰返し、待機ノード、業務の期限・超過時の上申を混同しない。

## 2. 10 社・製品系統の位置付け

| 製品 | 保存データ監視との近さ | 具体的に確認した対象 | 修正・人の関与 | 今回確認できていない主な点 |
|---|---|---|---|---|
| Teleskope | 最も近い。ストレージを含む問題管理・自動修正 | S3、データベース、SMB 等の自社ファイル、Google Drive、Slack、GitHub 等 | 統合 Findings、所有者への Slack/メール、Jira、待機、アクセス解除、伏字化・隔離、状態管理 | 解決後再発の識別規則、全対象の修正後再検査保証 |
| Nightfall | 最も近い。イベント集約と重複・自動解決の操作文書 | Slack、Drive、GitHub、Microsoft 365、Jira、Confluence 等。独自保存先は API | 複数 findings を Event へ集約、重複管理、サービス別自動解決、利用者の修正、外部通知 | 現行の管理された S3 継続接続、担当・期限の汎用課題管理 |
| elba | 所有者への修正依頼と未完了作業の管理が近い | Google Workspace、Microsoft 365、Dropbox、Confluence、Slack 公開チャンネル | Checklist、管理者画面、Playbook、通知・再通知、権限解除等 | S3/任意ファイルシステム、日本語、内容検査・修正ができる個々の対象 |
| Strac | 検出種別・保存先・修正操作・自社配置が近い | Drive の Docs/Sheets、Slack、GitHub、S3、DynamoDB、Snowflake 等 | 伏字化、削除、隔離、共有制限、一括修正、通知・承認 | 重複鍵、再発状態、担当・期限、修正後再検査の詳細 |
| Metomic | 保存データ DLP に実績。現行の重点は移動中 AI データ | Drive、Slack、Box、Dropbox、Notion、Jira、Confluence 等 | 発見・分類・伏字化、アクセス制御、利用者通知。現在は AI の要求承認も | 保存データの課題状態・再発規則、S3/任意保存先の現行接続、機能別保存期間 |
| MIND | 保存と移動をまとめた DLP。問題調査・共同修正が関連 | Drive、OneDrive、Box、Slack、Teams、自社ファイル共有等 | 危険度を付けた incident、所有者通知、権限解除・削除・ラベル変更、監査履歴 | 個々の S3 等の保存先、GitHub の現行接続仕様、重複・再検査条件 |
| Polymer | 保存状態と人の利用を合わせた DLP が関連 | Slack、Slack Enterprise、Drive、Teams。現行サイトは AI も対象 | 自動伏字化、アクセス解除、人の確認を含む独自手順、自社配置の説明 | 公開操作仕様の十分な裏付け、重複・再発・期限、原文保存の詳細 |
| Candor Security | 利用者の行動と機密情報を関連付けた調査に近い | Google/Microsoft、認証、端末、ServiceNow、HR、SIEM 等の説明 | ケースと人物の調査、優先順位付け、説明・監査可能な AI 出力 | 独立した保存先の定期全件検査、内容修正、Sentry 型の再検査 |
| Harmonic Security | 隣接。AI に向かう通信・エージェント操作が中心 | ブラウザー、端末、MCP、AI 利用観測 | 利用者へ助言・警告・遮断、操作の管理 | 保存データ全件巡回、既存ファイルの問題・修正管理 |
| Gamma.AI → Palo Alto Networks | 独立企業ではなく統合済みの製品系統 | 2022 年公式発表で Next-Gen CASB と DLP への統合を確認 | 機械学習による業務クラウドのデータ保護という系統 | Gamma 単体の現在の機能・販売、現行統合製品の全課題管理仕様 |

対象の列に載せたサービス名は、個別接続資料または製品説明に基づく。サービス名が書かれていても、全ファイル形式・チャンネル・履歴・操作が同じ範囲で検査できるとは限らない。根拠と限界を以下で示す。10 行は 9 社の現行サービスと 1 つの買収済み製品系統であり、「新興企業 10 社が現在独立して競争している」と数えない。

## 3. Teleskope: ストレージと問題管理の両方が近い

### 3.1 保存先と検査権限

接続一覧は業務クラウドだけでなく、S3、EFS、DynamoDB、RDS、Redshift、GCP Cloud Storage/BigQuery/Cloud SQL、Azure Blob Storage、Snowflake 等を含む。自社の SQL・SMB ファイル共有・私設ファイルシステムは、局所作業機である Outpost から検査できる。[接続一覧](https://www.teleskope.ai/product/integrations)、[Outpost](https://docs.teleskope.ai/setup/deployment/outpost.md)

S3 操作文書は、読取り権限で検査できること、対象 bucket/object に絞った方針で検査範囲を狭められること、修正の書込み権限を別に追加することを明示する。標準例の `AmazonS3ReadOnlyAccess` はアカウント全体に広いため、導入時は対象を限定する必要がある。Inventory の利用は一覧取得の負荷軽減であり、全本文を常時再検査する証拠ではない。[S3 接続仕様](https://docs.teleskope.ai/connectors/clouds/aws/s3.md)

GitHub は Enterprise Cloud と Enterprise Server の両方。標準 App の `Contents(read)` と `Metadata(read)` で組織・リポジトリ・ファイルを検査する。検出対象として secrets と sensitive data を説明しているが、この読取り接続からコードの自動修正、鍵の失効、履歴の抹消まで推定しない。[GitHub 接続仕様](https://docs.teleskope.ai/connectors/saas/github.md)

### 3.2 問題の状態と手順

Policy Maker の取得本文は、感度・アクセス範囲・古さを条件に、対象サービスごとに手順を組む仕様を説明する。Findings は Open、In Progress、Resolved、Ignored の 4 状態を持つ。In Progress の例には利用者の回答待ちがある。データ所有者への Slack DM/メール、Jira 課題、複数の通知先、待機時間、権限解除・伏字化・隔離・ラベル、状態変更をつなげられる。対応する修正操作は接続先ごとに異なる。[Policy Maker 操作仕様](https://docs.teleskope.ai/the-platform/policy-maker)

問題をデータ保存先・資源単位でまとめて見られ、判定件数と権限も表示する。方針の版・変更者・時刻を記録し、方針を変更して条件から外れた findings は自動で保管済み扱いになる。**これは原本の秘密が消えたことの証明ではない。** 状態ノードや手動 Resolved も、元データの再検査成功と同義にしない。再発時に同じ問題へ戻す規則、期限超過の上申、修正後の全件再検査保証は今回の公開資料では未確認である。

### 3.3 「原文を外へ出さない」か

配置文書は SaaS、自社管理、ネットワークを外部から切り離した完全自社管理、Outpost を区別する。Outpost が自社内にあっても、**標準の遠隔分類では抽出平文を顧客専用の Teleskope 処理先へ送る**。原ファイル自体を複製しないことと、抽出テキストを送らないことは別である。[配置](https://docs.teleskope.ai/setup/deployment.md)、[構成とデータの流れ](https://docs.teleskope.ai/setup/deployment/architecture.md)

局所分類は NVIDIA GPU がある Outpost で個別調整により利用でき、外へ出るものは資源の属性と検出結果と説明する。ただし、管理者が preview を求めた場合は一致箇所の文脈を返す。公式文書自身が、findings も機密情報を含み得ると注意している。局所 LLM 解析も個別調整であり、すべての処理が既定で局所実行されるものではない。完全な自社配置と、SaaS に接続する Outpost を同一視しない。[Outpost の分類モード・preview](https://docs.teleskope.ai/setup/deployment/outpost.md)

伏字・指紋だけを長期保存する構想に近い配置は選べるが、画面の AI 要約、文脈表示、検出値、運用ログの保存を別途確認する必要がある。第三者 LLM への送信先・保持条件と日本語性能は今回未確認である。

### 3.4 顧客事例と将来機能

Ramp の公式事例は Slack と Drive の既存・新規データを把握し、伏字化・隔離・利用者通知を自動化したと報告する。検出速度 2 秒未満等は、当該顧客の会社発表であり全環境の保証ではない。Aprio の事例は自社保存先・業務クラウドの秘密・古い記録・公開 PII の自動対処を説明する。[Ramp](https://www.teleskope.ai/case-studies/how-ramp-achieves-real-time-data-redaction-with-teleskope)、[Aprio](https://www.teleskope.ai/case-studies/how-aprio-operationalized-data-security-with-teleskope)

取得したサイトには **10 月 14 日に Kosmo 修正エージェントの first look** を行う告知がある。調査日は 10 月 9 日なので、これを利用可能な現行機能の証拠として数えていない。

## 4. Nightfall: 重複と自動解決の条件が具体的

### 4.1 対象とイベント管理

Data at Rest は Slack の公開・非公開チャンネル・DM、Drive の共有/個人領域、Jira、Salesforce 等の既存データ検査を説明する。接続操作文書は GitHub、Confluence、OneDrive、Teams、Gmail、Notion 等も列挙する。API で独自の保存先を扱うことはできるが、独自接続を作れることを管理済み接続と数えない。[Data at Rest](https://www.nightfall.ai/dlp-for-data-at-rest)、[接続一覧・API の範囲](https://help.nightfall.ai/nightfall_integrations)

ひとつの検出値を Finding、ファイル等の検査による複数 finding の集合を Event とする。Event には危険度、利用者、方針、状態、実施操作、資源の属性・履歴がある。False positive の指定や一括操作、外部通知・Jira 課題も提供説明がある。[Events](https://help.nightfall.ai/dashboard/sdp_events)、[操作](https://help.nightfall.ai/dashboard/sdp_events/event_actions)、[Slack の通知・Jira](https://help.nightfall.ai/slack/integration_alerts)

### 4.2 重複と解決は対象別

Deduplication 文書は「既に活動中の Event で扱う検出について冗長な Event を減らす」と説明する。Drive では、同じ値を同じファイルへ追加すると既存 Event に finding を追加するが、別のファイルなら新しい Event を作る。**全保存先で同じ秘密の指紋を共有する一つの問題へまとめる、という仕様ではない。**[重複・自動解決仕様](https://help.nightfall.ai/dashboard/sdp_events/deduplication)

Drive の秘密を本文から除くと自動解決し、ファイルをゴミ箱へ入れただけでは自動解決しない。完全削除なら資源削除として自動解決する。文書は、Notion のページ・コメント・添付や Teams の添付など、自動解決しない場合も明示する。再検査・編集検知により原本の変更を反映する具体例はあるが、全接続先の一律保証へ広げない。

担当者の割当てと汎用的な期限・超過管理、一度解決した問題の再発を同じ ID へ再関連付けする条件は今回未確認である。「再検出を抑える」「履歴を見る」「解決済みにする」を、それぞれ独立した根拠で採点する必要がある。

### 4.3 原文・検出値の保持

Events 操作文書は、管理者が伏字前の findings を閲覧・出力できる範囲を **30 日以内** とし、それ以前は伏字と説明する。これは全原文ファイルの 30 日保存を意味しないが、**検出値も保存しない指紋のみの製品、とは言えない**。エクスポートの期限も出力物の利用可能期限であり、元の保持期間ではない。[Events の Export and Share](https://help.nightfall.ai/dashboard/sdp_events)

Developer Platform の説明では、アップロードしたファイルを暗号化して保管し **24 時間後に削除** する。これは API のファイル処理の説明であり、全 SaaS 接続の保存期間ではない。API の `findingsURL` は知っている人が取得できる署名付きリンクであり、警告先・リンク自体も機密情報として扱う。[API ファイル保持](https://help.nightfall.ai/developer-api/faqs/unique_features)、[API 通知](https://help.nightfall.ai/developer-api/key-concepts/alerting)

現在の管理された S3 継続接続は今回確定できなかった。2025 年の公式記事に S3 経由の検査・API を使う手順は残るため、独自保存先の検査という隣接機能は確認できる。ローカルから API を呼ぶ手順を局所分類と誤解しない。[公式の保存データ検査手順](https://www.nightfall.ai/blog/data-loss-prevention-jira-confluence-data-center-server)

## 5. Strac: 多様な保存先の検出と修正、自社配置

### 5.1 対象と分類

個別の Drive ページは Docs、Sheets、PDF、画像を扱い、公開共有・特定宛先への共有を検出すると説明する。Slack は公開/非公開チャンネル、DM、Slack Connect の既存 messages/files に対する DSPM と、新規投稿の DLP を分けて説明する。PII、PHI、決済情報、API secrets、ソースコード、独自検出を列挙する。GitHub、S3、DynamoDB、Snowflake 等も個別の接続一覧がある。[Drive](https://www.strac.io/integration/google-drive-dlp)、[Slack](https://www.strac.io/integration/slack-dlp)、[接続一覧](https://www.strac.io/integrations)、[GitHub](https://www.strac.io/integrations/github-dlp)

S3 ページは継続監視、アクセス制御、伏字化・置換・隔離等の修正を提供すると説明する。RDS/Redshift/DynamoDB と MCP の通信検査も述べるが、**保存中のオブジェクト検査と AI が読む瞬間の検査を同じ機能と扱わない**。同一データによる精度評価や、形式・サイズ・圧縮/暗号化・版管理ごとの保証は未検証である。[S3 の製品説明](https://www.strac.io/integrations/aws-dlp-s3)

### 5.2 修正と作業管理

Drive の説明には、一括で共有を Restricted に変える、不要な利用者の権限を解除する、ラベルを付ける、所有者の承認を条件に共有する等がある。Slack では通知・直接の伏字化・非表示化・削除・保管庫への隔離・担当部門への上申、遅延させた伏字化を説明する。[Drive 修正](https://www.strac.io/integration/google-drive-dlp)、[Slack 修正](https://www.strac.io/integration/slack-dlp)

インシデント追跡や監査記録の説明はあるが、同一検出の重複鍵、解決後の再発、個々の担当者と期限、修正後の再検査による状態遷移の公開仕様は今回確認できていない。修正操作が豊富であることを Sentry 型の問題ライフサイクルの完成と数えない。

### 5.3 配置・保管

Strac は自社施設または顧客の AWS/Azure の自社配置を説明し、計算資源・保存・ログを顧客が持ち、データ・属性・ログを外部へ送らないと表明する。これは会社の提供説明であり、本調査で全通信を実測したものではない。[自社配置](https://www.strac.io/integrations/dlp-on-premise)

SaaS 版の原文・一致箇所・保管庫・再検査用データの保持を、自社配置の無送信説明から推定しない。Vault や tokenization（秘密値を代替識別子へ置換し別保管する処理）の機能も、秘密値が製品全体から消えるという意味ではない。自社で外部の検出器を自由に差し込む仕様と、独自検出条件/API を設定する仕様は別であり、前者は未確認である。

公式の匿名顧客事例にはクラウド保存データの検出と協働ツールの保護がある。実名利用者の証言や一般化可能な測定とは区別し、対象機能の導入例として扱う。[クラウド保存事例](https://www.strac.io/case-studies/sensitive-data-discovery-and-protection-in-cloud-storage)、[協働ツール事例](https://www.strac.io/case-studies/data-security-for-collaboration-tools)

## 6. elba: 人への依頼と未完了作業の追跡

Data Protection は、資源・共有相手・所有者・機密種別をまとめ、問題を所有者へ配布し、修正と業務上の例外を記録する。従業員の Checklist と管理者画面で未完了の作業を追跡する。Playbook は共有範囲・機密区分・危険度・古さで条件を作り、接続先が対応する操作だけを自動化する。[製品](https://www.elba.security/platform/data-protection)、[作業の流れ](https://www.elba.security/how-it-works)

公式操作文書には、従業員が共有を維持するか権限を変えるかを選び、対象の権限を実際に解除する手順、週次のまとめ通知、管理者による行動の追跡を説明する。SharePoint のフォルダの権限解除と子資源への影響も区別する。これは所有者への依頼を警告から切り離さず管理する実装例として近い。[Data protection 操作文書](https://documentation.elba.security/articles/data-protection)

**Slack の通知接続と検査接続は別。** 通知接続はメールの一致する利用者へ DM を送り、対応しない場合はメールへ戻る。別の Slack Data Protection 接続は利用可能な公開チャンネルを分析し、現行権限では非公開チャンネルの履歴を読めない。対応するメッセージだけが修正対象になる。[Slack の境界](https://www.elba.security/integrations/slack)

Google も利用者一覧の同期、OAuth 権限・Drive の危険把握が別の許可として説明される。接続があることと、自動修正が有効であることは別。Playbook と操作が対象資源で提供されることを確認する必要がある。[Google Workspace の境界](https://www.elba.security/integrations/google-workspace)

プライバシー文書はサービス提供中に顧客データを保持し、契約終了時に削除要求があれば直ちに、なければサービス終了 30 日後に全顧客データを削除すると説明する。Google の利用者データも同条件である。これは終了時の削除規則であり、運用中の原文一致箇所や監査ログの保持期間を確定するものではない。各内容検査に使う第三者モデル、日本語性能も今回未確認である。**監査ログの保持と原本文面の保持は別に確認する**。[プライバシー方針](https://www.elba.security/privacy-policy)

S3、一般の自社ファイルシステム、企業の任意の検査器追加は確認できていない。通知の再送や週次まとめは確認できるが、課題ごとの厳密な期限・超過管理と、秘密値単位の再発を一つの ID へ集約する規則は未確認である。

## 7. Metomic: 保存データの実績と 2026 年の重点変更

Drive の個別製品ページは、保存されたデータの発見、既成/独自分類、危険度の把握、伏字化、アクセス制御、従業員通知を説明する。Box ページも PII と company secrets の所在・アクセスを検査すると説明する。Slack Enterprise の発表は伏字化、データ保持方針、隔離、従業員通知を列挙する。[Drive](https://www.metomic.io/integration/metomic-for-google-drive/)、[Box](https://www.metomic.io/integration/metomic-for-box)、[Slack Enterprise の機能発表](https://www.metomic.io/resource-centre/metomic-for-slack-up-levels-data-security-and-compliance-for-one-of-the-worlds-most-popular-collaborative-work-apps/)

Oyster の 2026 年 1 月の公式事例は、Slack/Drive の機密データを把握し、利用者と協力して保護する用途を説明する。SaaS の既存保存状態を改善する比較対象として十分関連する。[Oyster](https://www.metomic.io/resource-centre/oyster-case-study/)

一方、取得した現行の DSPM・Human Firewall・Response ページは、MCP 経由で AI の要求・道具の応答を検査し、伏字化・承認待ち・遮断する機能へ重点を移している。これは保存データを後から検査する機能と異なる。**旧資料の Human Firewall をそのまま現行の保存データ修正画面と説明しない。** 保存データ機能が廃止されたとも確認していない。[現行 DSPM](https://www.metomic.io/solution/data-security-posture-management/)、[現行 Human Firewall](https://www.metomic.io/solution/human-firewall)、[現行 Response](https://www.metomic.io/solution/response-and-remediation/)

Security Center はデータを暗号学的にハッシュ化して機密性を減らす、最小化と不要時の破棄を説明する。現行の Response は「移動中の内容を検査し保存しない」と述べる。これらは有力な情報だが、**全保存データ接続の原文・通知・例外・診断・一時処理がすべて非保存であるとの保証まで広げない**。どの値のハッシュを何に使うか、検出値のプレビュー、保持期間、第三者 LLM、顧客単位の処理場所は個別確認が必要である。[Security Center](https://www.metomic.io/security-center/)

現在の一覧から S3・一般の自社保存先の接続は確認できていない。AWS Marketplace にあることを AWS 内のすべての保存先への接続と扱わない。問題の重複抑制、再発管理、担当・期限、原本の再検査による自動解決の詳細も今回未確認である。

## 8. その他 5 製品系統

### MIND

製品説明は非構造化データの継続発見・分類、アクセスと業務文脈による危険の優先順位、incident 調査、権限解除・ファイル削除・ラベル変更・所有者通知と監査履歴を説明する。Drive、OneDrive、Box、Slack、Teams、NAS/自社ファイル共有等が比較対象になる。[製品](https://mind.io/product)、[修正](https://mind.io/solutions/streamline-data-remediation)

ThoughtSpot の公式事例は、Google Workspace、OneDrive、Box 等へ配置し、知られていなかった credentials/secrets を見つけたと説明する。顧客が調査したい対象として GitHub 等を挙げる文章を、GitHub の現在の個別接続仕様の証拠へ拡張しない。[ThoughtSpot](https://mind.io/customers/thoughtspot)

Autonomous DLP Analyst は最初の提供機能を Custom Classifier と Issue Investigator と明記し、後続の技能は将来とする。自律エージェントという名称だけで期限管理・全再検査・自動修正の完全性を推定しない。[現行・将来の区別](https://mind.io/solutions/autonomous-dlp-analyst)

S3/GCP/Azure Blob の個別接続、保存結果の伏字・原値・指紋の内訳、日本語、第三者モデル、局所検査と集中管理の通信仕様は今回未確認である。2026 年 9 月の資金調達は既存の投資調査に記録済みであり、今回の機能順位へ調達額を反映していない。

### Polymer

現行ホームページは保存中と移動中のデータ監視、伏字化、アクセス解除、人の確認を含む手順、cloud/self-hosted single-tenant 配置を説明する。個別 SaaS ページは Slack 公開チャンネルと Slack Enterprise を分け、Drive の権限修正を説明する。[現行製品](https://www.polymerhq.io/)、[サービス別説明](https://www.polymerhq.io/polymer-for-free/)

Routefusion の PDF 事例は、Slack/Drive の状態をまず観測し、その後に権限と内容の修正を有効にしたと報告する。これは古い顧客資料であり、現行の画面・契約・精度を証明するものではない。[事例 PDF](https://www.polymerhq.io/wp-content/uploads/2021/09/Case-Study_-Polymer-DLP-for-Banking.pdf)

プライバシー文書は transaction log の限定期間の保存と、その後の削除を説明するが具体日数は示さず、米国と第三者処理も説明する。指紋だけで運用するという確認はできていない。[プライバシー](https://www.polymerhq.io/privacy/)

取得したホームページ HTML には製品説明とは無関係な外部リンクも混在した。そのリンク先は製品の証拠として使用せず、公式の個別製品ページと PDF を合わせて照合した。混在の原因やサイトの侵害を本調査で断定していない。詳細な重複・状態・再検査の公開仕様が薄いため、提供表明の確度と操作仕様の確認を分ける。

### Candor Security

現行の説明は、Google/Microsoft、認証、端末、ITSM、HR、SIEM の情報を統合し、誰が何をしたかと機密データを関連付け、重要なケースへ絞る方向である。自社/クラウド配置、私設隔離環境での推論、顧客の領域からデータを出さない、学習しないと表明する。[現行製品・FAQ](https://candor.security/)

2026 年 9 月発効のプライバシー説明は従業員の属性、活動・監査イベント、調査要約、人物の優先順位等の処理と、顧客が設定する保持を明示する。したがって、原文を持たず問題の指紋だけという構想とは、少なくとも調査情報の種類が異なる。保存データの全件検査、各サービスの原文修正、期限・再検証は未確認。[プライバシー](https://candor.security/privacy-policy)

同名の個人金融サービス `candor.money` や法律向け `candor.legal` は本製品と混ぜていない。

### Harmonic Security

2026 年の現行製品は、ブラウザー・端末・MCP の AI 利用観測、分類、利用者へ助言・警告・遮断する制御が中心である。保存済みのストレージを巡回して問題を集約する主競合というより、AI へ送る瞬間を保護する隣接製品として扱う。[現行製品](https://www.harmonic.security/)

利用許諾は顧客の内容を自社または第三者の AI 学習・微調整へ使わないと説明する。ただし、**学習しないことは、推論で誰も読まないことや一時保存しないことの保証ではない**。第三者処理の一覧に AWS、ClickHouse、Sentry 等があり、Sentry は顧客データを既定で除外すると説明する。原本文面の全保持と具体的な分類用モデルの処理場所は別途確認する。[利用許諾](https://www.harmonic.security/harmonic-end-user-license-agreement)、[第三者処理](https://www.harmonic.security/subprocessors)

### Gamma.AI / Palo Alto Networks

公式の 2022 年 4 月 27 日の記事は Gamma.AI 技術の買収と Next-Gen CASB・DLP への統合完了を述べる。文中の「acquired late August」は買収時期についての別の記述であり、記事の 2022 年の日付を買収日としない。独立する最新ベンチャーとして扱うのは不適切である。[統合発表](https://www.paloaltonetworks.com/blog/2022/04/next-gen-casb-gamma-ai-data-protection/)

今回、現行の SaaS Security API の修正操作文書の推測 URL は取得に失敗したため、Gamma の歴史的な説明から現在の課題管理・担当・再検査機能を復元していない。Palo Alto Networks の現行製品全体との比較は、別の DSPM/大手製品調査と接続すべきである。

## 9. 「原文不保存」「自社配置」「外部検出器追加」の比較

| 製品 | 原文・一致値の扱いで確認できた点 | 自社配置・分散実行 | 外部検出器を差し込めるか |
|---|---|---|---|
| Teleskope | 属性と findings 保存。標準 Outpost は抽出原文を送信。局所分類も preview/機密を含む findings に注意 | 完全自社管理と air-gap、Outpost。局所 GPU/LLM は個別調整 | 分類/伏字 API、独自データ要素はあるが、任意外部検出器の登録仕様は未確認 |
| Nightfall | API upload は24時間、伏字前 findings は30日以内閲覧。全部指紋のみではない | 独自 API クライアントを局所で動かすことと局所推論は別。全面自社配置は未確認 | Developer API と通知連携はある。任意の第三者分類器の内部追加は未確認 |
| Strac | SaaS の元値/保管庫/通知の詳細は未確認。自社版は外部送信なしと表明 | 顧客 AWS/Azure または自社施設への配置を説明 | 独自検出条件/API と、他社エンジンを自由登録する機構は別。後者未確認 |
| Metomic | ハッシュ化・最小化。AI の移動中内容の非保存説明は対象限定 | 全面的な自社配置は未確認 | 独自分類と接続設定は説明。任意の局所検出器登録は未確認 |
| elba | 属性・作業結果等の保存。内容の指紋のみという確認なし | EU/US の保存環境は説明。自社配置は未確認 | 任意検出器追加は未確認 |
| MIND | 分類・incident 文脈・監査履歴。原文保持は未確認 | 自社ファイル共有対応はあるが全製品自社配置とは別 | Custom Classifier と任意外部検出器は別。後者未確認 |
| Polymer | 限定期間のログ保存、米国処理。具体日数・元値の内訳は未確認 | 自社 single-tenant 配置の製品表明あり | 独自手順と任意検出器追加は別。後者未確認 |
| Candor | 活動・人物・調査要約等を処理。保持は顧客設定 | 自社/私設隔離環境を説明 | 外部検出器登録は未確認 |
| Harmonic | 学習しない規定。保存・推論経路は別途確認 | ブラウザー/端末での部品配置と全面局所推論は別 | API/観測接続と第三者検査器追加は別。後者未確認 |
| Gamma 系統 | 現行処理仕様はこの調査では未確認 | 現行配置仕様はこの調査では未確認 | 未確認 |

これらの「未確認」は機能が存在しないという断定ではない。日本語の住所・人名・文脈・社内略称について、同条件で測った性能や網羅的な公式対応保証は **全製品で今回未確認**。世界中の言語を扱う、AI を使う、独自分類があるという説明から日本語で同じ精度を推定しない。

## 10. 開発構想の差別化を確認する質問

以下は公開比較からの設計観点であり、Telescreen の実装説明ではない。

1. 保存先ごとに、全件の初期検査・増分検査・定期再検査・失敗時の再実行をどこまで保証するか。API のイベントが落ちた時に巡回で拾えるか。
2. 同じ秘密を複数の保存先へ複製した場合、ひとつの問題と複数の所在を結び付けるか。保存先ごとの別警告にするか。
3. 一度解決した問題の再出現で、同じ問題を再開して履歴と担当へ戻すか。新規警告との違いを説明できるか。
4. 所有者への依頼と、セキュリティ担当の割当て、回答待ち、期限、期限超過、業務上の例外を別の状態として管理するか。
5. 修正操作の成功ではなく、原本の最新版を再検査したことを解決の条件にするか。削除・アクセス失効で読めない場合も区別するか。
6. 検査用の原文、一致値、通知、preview、例外、要約、ログを分けて最小化するか。指紋も、短い値を推測されない鍵付きの設計や鍵の版管理を必要に応じて使うか。
7. 元データの検査は自社内、問題管理だけは集中する構成で、外へ何が出るかを明示できるか。任意の第三者検査器は送信先・ログ・失敗時の挙動まで制約できるか。

差別化候補は「AI を使うこと」より、**問題の同一性と再発、期限を含む人との協働、再検査による解決、原文を収集しない管理境界、検査器を安全に差し替える仕様**にある。ただし、これらが競合に無いと断定するには、実機の評価と契約仕様の確認が必要である。

## 11. 検証範囲

公開説明と操作文書の比較であり、実環境へ接続せず、精度・遅延・通信・自動修正を実行評価していない。資金調達の一覧は本稿の主目的ではない。過去の [新興企業・投資家調査](sensitive_data_startups_and_investors_20261007.md) から機能をそのまま移さず、現行資料で再確認した。将来発表、古い顧客事例、製品提供表明、具体的な操作仕様を分離した。直接取得失敗は台帳に残し、成功扱いにしていない。
