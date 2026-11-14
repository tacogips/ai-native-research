# BigIDのAPI対応と機密情報検知の制約

調査日：2026年11月11日。2026年10月9日の[企業基盤調査](telescreen_related_enterprise_20261009.md)を再確認し、今回のAPI・Drive・日本語・形式・許可運用の比較へ追加する。

**BigIDは今回の直接比較候補に含める。** Google Driveの内容検査、検知した資産の一覧、危険な状態の問題管理、検査設定・状態のAPIがある。公式の公開MCP連携資料には、分類結果の正誤判定、問題の通知抑制、分類器と方針の管理も記載される。ただし、これらを「指定フォルダーの氏名・電話を検知台帳に残し、将来の通知だけ止める」単一機能と同一視しない。

APIはプログラムからの呼出し口、MCPはAI等が外部の道具を呼び出す共通の接続規約、資産一覧は検査対象のファイル・表等と分類をまとめたもの。問題一覧は、分類された資産に対して保存場所・公開状態等の方針違反をまとめたもので、検知値の一覧とは異なる。

公開資料と固定版コードの説明を確認した結果であり、組織への接続・API呼出し・日本語の精度試験は行っていない。以下の「未確認」は公開資料から保証を確認できないことを表す。

## 今回の要件への対応

| 観点 | 公開資料で確認できるもの | 制約と今回の判断 |
|---|---|---|
| Google Drive | マイドライブ・共有フォルダー・共有ドライブ、本文と共有権限をAPI接続で検査する説明 [BI7] | 端末常駐は不要だが、クラウド側の検査器の配置は別問題。接続権限・変更検査の遅延保証は要確認 |
| 形式 | Google Docs・Sheets・Slides、PDF、文書・表・プレゼンテーション等 [BI7] | `.doc`と`.docx`等の拡張子別一覧、画像PDF、埋込み画像、圧縮内部、容量上限を同じ根拠だけで確定しない |
| 画像の文字読取り | 製品全体にOCR検査の説明あり [BI12] | Drive接続での画像・PDF形式別の有効化条件、日本語の読取り精度は未確認 |
| 検知種類 | 個人・金融・人事・規制対象・企業機密等。秘密鍵・トークン等の分類と独自規則の説明 [BI7,BI11] | 分類可能なカテゴリと、日本語氏名・国内電話表記・日本の個人番号の個別品質は別 |
| 日本語 | 多言語対応の製品説明はある [BI13,BI15] | 日本語の属性別適合率・再現率、対象資料、Driveの形式別評価は未確認。全言語という宣伝を数値保証へ変えない |
| 検知記録の取得 | 資産一覧・属性取得とData Postureの問題取得が別にある [BI1,BI4] | 問題だけ取得しても、許可場所にある正常な個人情報まで一覧化できるとは限らない。資産一覧も取り込む |
| 人の判定 | 公式MCP資料に、結果の正誤確認、問題の状態変更、`silenced`がある [BI9,BI10] | 誤検知判定、業務上の許可、問題の通知抑制、原本の修正を別項目にする |
| フォルダー×属性の許可 | 方針・分類器・資産タグの操作手段はある [BI9] | 子フォルダーを含む条件、値単位の例外、有効期限、内容変更時失効、再通知の継承条件は未確認 |
| 再検査 | 検査設定の作成、検査起動・停止等、検査状態取得の経路がある [BI2,BI3,BI6,BI9] | 設定作成・起動受付・検査停止・正常完了は別。Drive用の起動引数や全件検査の完了判定を契約環境で検証 |
| 原文と証拠 | 秘密情報検知の抜粋と周辺文脈を、利用者側のデータベースへ保存するSnippet Persisterの説明あり [BI11] | 配置選択やこの機能の存在だけで、全機能が原文無送信・無保存とは断定しない。標本と全文・全箇所も区別 |

適合率は「検知したうち正しかった割合」、再現率は「本当の対象を見つけた割合」。日本語の数値が未確認なので、他製品との精度順位は付けない。

## APIとMCPの対応範囲

下表のREST経路は、特記しない限り組織ごとの `/api/v1` 以下。資料の `developer.bigid.com` や `SAMPLE` は訓練用であり、組織の接続先・認証情報の代わりにはならない。

| 機能 | 公開されている経路・操作 | 取得・変更できる範囲 |
|---|---|---|
| 問題一覧 | `GET /actionable-insights/all-cases` | 問題識別子、方針、重要度、担当、対象保存先等。問題に含まれる資産の列挙は別 [BI1,BI10] |
| 個別の問題状態 | `PATCH /actionable-insights/case-status/{caseId}` | 状態と理由。公式の公開手順には`open`、`acknowledged`、`resolved`、`silenced`等 [BI1,BI10] |
| 一括の問題状態 | `PATCH /actionable-insights/cases:update`の公式例 | 指定した方針の問題等をまとめて変更。ただし例には仮定を示すコメントがあり、実環境の定義を確認 [BI1] |
| 資産一覧の全件出力 | `GET /data-catalog/objects/stream` | 継続位置を使って資産を取得。問題一覧とは別 [BI4] |
| 資産の属性 | `GET /data-catalog/object-details/attributes`等 | 検知分類・表の列等の詳細。全原文値・全位置を返す保証ではない [BI4] |
| 接続先一覧・検査設定 | `GET /ds-connections`、`POST /scanProfiles`、`GET /scanProfiles/{id}` | 対象の接続先を選んだ検査設定を作成・確認。作成済みだから検査完了ではない [BI2] |
| 検査起動・状態 | `POST /scans`の公開例、`GET /scans/parent-scans`、`GET /scans/{id}/status` | 起動例はデータ流の検査。公式MCPは一般の開始・一時停止・再開・取消しも説明 [BI3,BI6,BI9] |
| 結果の正誤判定 | MCPの`results_review_refine` | 検知の標本を見て正しい／誤検知と判定。具体的なREST要求形式、将来の同じ値への適用境界は今回未確認 [BI9] |
| 分類器・方針 | MCPの`classification_management`、`policy_management` | 分類器・方針の作成・更新等。MCP説明を、そのまま全REST操作の検証済み仕様へ読み替えない [BI9] |
| 直接組込み | BigID Embedded SDKの製品説明 | アプリ内で分類を行う別の組込み部品。対応言語・配布条件・詳細APIは今回未確定 [BI14] |

公式ポータルからリンクされたMCP連携リポジトリは `bigexchange/bigid-plugin-official`。取得版は `eaa78ae83c085b7e781022bc880a4342ef64b6ed`。ここで確認したのは公開された機能説明と操作手順で、MCPサーバーの実装や契約環境の動作ではない。AIによる任意の書込みをこの調査で許可・実行したものではない。[BI9,BI10]

## 取得漏れと状態の取り違え

| 注意点 | 仕様・確認結果 | 必要な扱い |
|---|---|---|
| 1万件での出力打切り | Elasticsearch方式の通常`/data-catalog`は検索窓1万件。超えてページを進めるとエラーではなく0件になる場合がある [BI4] | 全件出力は`/objects/stream`を使う |
| 版と設定 | 一覧の継続出力はBigID v250以降。MongoDB方式では追加の機能設定が必要 [BI4] | 利用版・内部方式を確認。継続位置と同じ並び順を保つ |
| 取得失敗と0件 | 問題取得の公式コード例は、HTTP失敗時も空配列を返す [BI1] | 失敗を「問題なし」に変換しない。状態・件数・継続取得の成否を別に保存 |
| 検査停止と正常完了 | 公式例の`status=false`は検査停止を表し、正常完了と断定していない [BI3] | 異常終了・取消し・対象の検査率を追加確認する |
| 問題と対象資産 | 問題APIは集約された件数等を返し、配下の実ファイルは資産一覧で取得する [BI10] | 問題を1件のファイルとして保存しない |
| resolvedと原本修正 | 公式例は外部への書出しを模擬した後にresolvedへ変更する [BI1] | 外部への転送・受領と、原本の修正・再検査を別の状態にする |
| silencedと恒久許可 | 公式手順では問題の抑制状態として扱われる [BI10] | その問題の抑制から、同一値・別ファイル・内容変更後の自動許可まで推定しない |
| 除外一覧 | 公式MCP説明では、除外した値を報告しなくする機能 [BI9] | 検知台帳へ残す要件では、検知器の除外を通知抑制の代用にしない |

`/data-catalog/object-details/attributes`は公式例の表記を確認した。一方、環境ごとの完全なAPI仕様へのリンクには取得できないものがあり、公開チュートリアルの要求例・MCPの操作名・実環境のAPI定義を区別する。推測で不足する引数や最大容量を補わない。

## 権限と費用の確認事項

認証の公式説明は、利用者用のトークンを `/api/v1/refresh-access-token` でセッション用へ交換する方式。トークンには期限があり、どの要求形式・ヘッダーを使うかは利用APIの定義に合わせる。公開例の認証文字列を固定して配布する構成にはしない。[BI5]

公式の公開操作手順には、問題管理にDSPM／Actionable Insightsの利用条件、原本の移動等の修正操作には別の契約・権限、各操作の`isEnabled`と`dsSupportedTypes`の確認が必要と記載される。契約があればDriveで全修正操作を使えるとは扱わない。[BI10]

検査器はBigID側・自社内・自社クラウドへ配置できる説明がある。接続のための本文取得、結果・抜粋・索引・操作記録の送信先と保持は別に確認する。[BI8,BI11]

## 指定フォルダーで氏名と電話だけ許可する設計案

1. 問題一覧だけでなく、資産一覧の分類も収集する。
2. Driveの実ファイル識別子と親階層を照合する。BigIDのパス表示があるだけで、移動後も自動追従すると仮定しない。
3. 検知の正誤と、フォルダー×属性×共有条件×期限の許可を別々に保存する。
4. 許可した氏名・電話は記録したまま通知を止め、同じファイルの秘密鍵等は通知対象にする。
5. 原本・場所・共有・規則が変わった場合、許可と問題の抑制を再評価する。

これは自作側で補う構成案。BigID標準だけで同条件を満たすかは、フォルダー配下・属性・期限を同時に指定した規則、`silenced`の失効・再発仕様、許可した検知のAPI取得可否を実環境で試験する。日本語資料は合成データで属性別・形式別の見逃しと誤検知を測る。

## 公開一次資料

[取得台帳](dlp_related_services_api_sources_20261111.json)のBI1〜BI15へ今回の取得を追加した。全文・組織のデータは収録しない。

| 番号 | 資料 |
|---|---|
| BI1 | [Data Posture API Tutorial](https://developer.bigid.com/api/data-posture-api-tutorial/) |
| BI2 | [Manage Scan Profiles](https://developer.bigid.com/api/scan-profiles-api-tutorial/) |
| BI3 | [Scan Insights API Tutorial](https://developer.bigid.com/api/scan-insights-api-tutorial/) |
| BI4 | [Export Metadata Tutorial](https://developer.bigid.com/api/bigid-api-metadata-export-tutorial/) |
| BI5 | [Token Authentication](https://developer.bigid.com/api/bigid-api-token-authentication/) |
| BI6 | [Scan Data in Motion Tutorial](https://developer.bigid.com/api/bigid-api-scan-data-in-motion-tutorial/) |
| BI7 | [Google Drive and Gmailの対応範囲](https://bigid.com/data-coverage/gdrive/) |
| BI8 | [What is a BigID Connector](https://developer.bigid.com/connectors/what-is-a-bigid-connector/) |
| BI9 | [公式MCP連携の機能説明 固定版](https://github.com/bigexchange/bigid-plugin-official/blob/eaa78ae83c085b7e781022bc880a4342ef64b6ed/README.md) |
| BI10 | [公式公開操作手順 固定版](https://github.com/bigexchange/bigid-plugin-official/blob/eaa78ae83c085b7e781022bc880a4342ef64b6ed/skills/bigid-security-posture/SKILL.md) |
| BI11 | [秘密情報検知とSnippet Persister](https://bigid.com/blog/hardcoded-secret-detection-with-bigid/) |
| BI12 | [検査方式とOCRの説明](https://bigid.com/blog/bigid-scanning-guide/) |
| BI13 | [多言語分類等の製品説明](https://bigid.com/solutions/privacy-and-compliance/) |
| BI14 | [BigID Embedded](https://bigid.com/embedded-bigid/) |
| BI15 | [分類の多言語対応等の説明](https://bigid.com/solutions/discovery-classification/) |
