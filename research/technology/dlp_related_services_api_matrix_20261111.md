# 機密情報検知サービスのAPI対応比較

調査日：2026年11月11日。Google Workspace DLP、Box、Nightfall、Microsoft、Netskope、Strac、Teleskope、Amazon Macie、Palo Alto Networks、BigIDと、検知用の開発部品を比較する。16行は製品・機能の系統数であり、独立した16社を意味しない。

**API対応は「保存先との接続」「内容の検査」「検知記録の取得」「設定の変更」「人の判定と再通知抑制」に分けて評価する。** Nightfallは既存検知の取得・判定登録・自動適用まで公開仕様がある。Netskopeは検知記録・証拠・対応状況、Stracは検知一覧・監査記録・誤検知登録、Teleskopeは内容検査・分類記録・接続済み資源の再検査を確認できる。ただし、どれも任意の「フォルダー×属性の許可」を同じ操作で実現するとは限らない。

APIはソフトウェア同士の呼出し口、RESTはHTTPで資源を取得・操作する方式、CLIは端末のコマンドによる操作、SDKはプログラムから利用する開発用部品を指す。Webhookは発生した事象を相手側のURLへ通知する仕組み、CRUDは作成・取得・更新・削除の総称である。

公開一次資料・公開されたAPI定義・コードによる仕様確認であり、契約アカウントへの接続や実行試験は行っていない。「未確認」は公開資料から対応を証明できないもの。管理画面に機能があることだけではAPI対応と数えない。組織の検知内容・設定・原文・認証情報はこの公開リポジトリへ保存しない。

## 保存先を継続監視する製品

○＝対象操作の公開仕様あり、△＝範囲限定・別経路・追加実装が必要。判定登録の○は将来の通知停止まで保証する印ではない。

| 製品系統 | 検知・警告の取得 | 検知した値・位置の取得 | 設定の取得・変更 | 人の判定・抑制の操作 | 検査の起動 |
|---|---|---|---|---|---|
| 1. Google Workspace DLP | ○ Reports API、Alert Center API | △ 抜粋。完全一覧ではない | ○ Policy APIでDLP規則・独自検知器 | △ 場所別の許可と通知は独自台帳等で構成 | △ 規則変更による再評価。任意本文の検査とは別 [GW] |
| 2. Box Shield／Shield Pro | ○ Events API。脅威とアクセス制御の事象を区別 | △ 分類ラベル・対象は取得可能。氏名等の全検知値・位置は未確認 | △ 分類ラベルの定義・付与APIあり。自動分類規則全体のCRUDとは別 | △ ラベル変更は値単位の許可判定ではない。将来抑制APIは未確認 | 未確認。汎用の内容検査APIとして扱わない [B1–B4] |
| 3. Nightfall Native SaaS Apps | ○ violationsの一覧・検索・詳細・履歴 | ○ findingsの種別・信頼度・伏字・位置。ただし原文値の取得と別 | △ Drive規則の利用者・ドメイン範囲更新。規則全体のCRUDは未確認 | ○ annotate／unannotate、autoApply、違反へのIGNORE等。適用範囲に注意 | △ 任意データの検査は別のDeveloper API [NF1–NF4] |
| 4. Microsoft Purview DLP | ○ Management Activity API、Graph、PowerShellの別経路 | △ 権限付きの値・文脈、切詰め表示あり。Drive版の同等性は未確認 | ○ Security & Compliance PowerShellで規則・方針の取得・変更 | △ Graphで警告の分類・状態等を変更。将来の同一値許可ではない | △ 方針の配布・再評価と任意本文の検査を区別 [M1–M5,M7–M12] |
| 5. Defender for Cloud Apps旧File policies | ○ Alerts API | △ 警告情報。全箇所の抽出APIとは扱わない | △ 今回は警告APIを確認。方針の全操作は未確認 | ○ 警告を良性・誤検知・真の問題として終了。ファイルのAuthorizeとは別 | **2027年1月6日にFile policies廃止予定**。API全部の廃止を意味しない [D1,D2] |
| 6. Netskope | ○ REST API v2のDLP警告・incident | ○ forensicsに一致情報・位置等。伏字・収集設定に依存 | △ URL一覧等の一部を確認。Drive用DLP方針全体のCRUDは未確認 | ○ 状態・重要度・担当の更新。業務許可と将来抑制は未確認 | 未確認。保存データ検査と通信中検査を区別 [N1–N3] |
| 7. Strac | ○ Data Security Risk、監査記録 | △ 検知種別・documentId等。別のDetect APIは値を返すが保存先の全箇所と同一視しない | 未確認。検知一覧に方針情報があることとCRUDは別 | ○ 文書識別子による誤検知登録。ただし適用アプリ・将来の継承・取消しは要確認 | △ 送信内容の検査APIあり。Drive継続接続の再検査とは別 [S1] |
| 8. Teleskope | ○ Metadata APIで分類記録。汎用Findings一覧・状態APIは未確認 | ○ Classifyは要素と位置等、Classify-fileは形式別。保存先の全件記録は別評価 | △ Policy Makerの対象メール追加API。方針全体のCRUDは未確認 | 未確認。管理画面のIgnored／ResolvedからAPI対応を推定しない | ○ 登録済みDriveファイル・Drive等をv1/scanで非同期検査 [T1–T6] |
| 9. Amazon Macie | ○ ListFindings／GetFindings等 | ○ 種別・件数・場所。原文の標本は追加の取得API・権限 | ○ ジョブ、独自識別子、検出結果フィルター等 | ○ Findings FilterのARCHIVEで抑制。値の許可リストとは区別 | ○ S3検査ジョブ。Drive直接接続ではない [A1–A4] |
| 10. Palo Alto Networks Enterprise DLP | ○ incident一覧・詳細・報告 | △ 一致手法・件数等。全原文値・位置の完全取得は未確認 | ○ データパターン・分類方針等の管理API | ○ 担当・注記・対応状態。将来の同一値抑制は未確認 | △ 当該APIの検知経路はネットワーク等。Drive全体の巡回と同一視しない [PA1–PA3] |
| 11. BigID | ○ 問題一覧と資産一覧の別API | △ 属性・分類と標本。全原文値・位置の保証は未確認 | △ RESTで検査設定。分類器・方針の管理は公式MCP説明も確認 | ○ 問題の状態・silenced、MCPで正誤判定。場所限定の将来許可は未確認 | ○ 公開の起動例・状態取得、MCPの開始等。Drive用引数と正常完了の証明は要検証 [BI1–BI10] |

Google Driveへの接続可否・日本語・形式は[製品の制約比較](dlp_product_limitations_and_build_options_20261111.md)を参照。Palo Alto Networksは今回API比較に追加した対象であり、他製品と同じDrive継続検査を確認したものではない。

## 検知処理を組み込むAPIと部品

次のAPIは、完成した検知台帳を外から操作するAPIとは役割が異なる。

| 系統 | 提供する呼出し口 | 戻るもの | 自作する範囲 |
|---|---|---|---|
| 12. Google Cloud Sensitive Data Protection | REST／SDK。`content:inspect`、非同期検査等 | 種別・信頼度・場所・任意の一致抜粋。`findingsTruncated`あり | Drive取得、許可台帳、通知。Workspace DLPの規則・記録とは別製品 [G1–G3] |
| 13. Presidio | 自前で配置するRESTサービス。`POST /analyze`、`POST /anonymize`等 | 種別・開始終了位置・得点、伏字結果 | 原文抽出、日本語の検知構成、認証、台帳、許可、通知 [PR2,PR3] |
| 14. OpenAI Privacy Filter | 手元で動かすPython APIとCLI | 文字列内の検出箇所・分類と伏字化等 | HTTP提供、Drive巡回、抽出・画像読取り、許可台帳。OpenAIの一般APIと同じ専用REST提供を確認したものではない [O1] |
| 15. OpenAIの一般API／Agent Builder | モデル呼出しと処理途中の個人情報保護 | 指示に応じた分類・抽出等、保護機能の結果 | 検査漏れの評価、保存先監視、検知台帳・人の承認・通知。専用の既存DLP違反一覧APIではない [O2] |
| 16. Anthropic Claude | モデルAPIでPrivacy等の分類を組む公式例 | 独自基準に応じた分類等 | 同上。Claudeの利用記録を取得する仕組みや外部DLP連携とも区別 [AN1] |

## 主な取得先と変更操作

以下は経路・操作名の比較で、認証済みの実行結果ではない。変更操作には原本削除・共有解除等が含まれる場合があるため、検知結果の取得と同じ権限でまとめない。

| 製品 | 読み取りの代表例 | 変更の代表例と意味 |
|---|---|---|
| Google Workspace | Reports `activities.list(applicationName=rules)`、Policy `policies.list/get` | Policy `create/patch/delete`。gwsの対応は[別稿](google_workspace_dlp_cli_api_deep_dive_20261111.md) |
| Box | `GET /2.0/events`、分類のメタデータ取得 | 分類ラベルの定義・ファイル／フォルダーへの付与。内容中の個人情報判定とは別 |
| Nightfall | `GET /dlp/v1/violations`、`/violations/{id}/findings`、`/activity` | `POST /dlp/v1/findings/{id}/annotate`、`/unannotate`、`POST /dlp/v1/violations/actions` |
| Purview／Defender XDR | `GET /v1.0/security/alerts_v2`、Management Activity APIの`DLP.All`、`Export-ActivityExplorerData` | `PATCH /v1.0/security/alerts_v2/{id}`。DLP設定は`Get-/Set-DlpCompliancePolicy`等のPowerShell |
| Netskope | `GET /api/v2/events/dataexport/alerts/dlp`、`/events/incident`、`GET /api/v2/incidents/dlpincidents/{id}/forensics` | `PATCH /api/v2/incidents/update`で状態・重要度・担当 |
| Strac | `GET /data-security/risk`、`GET /data-security/audit-event` | `POST /data-security/risk/false-positive`。直接検査は`POST /detect`、原文を送る経路 |
| Teleskope | `/v1/classify`、`/v1/classify-file`、Metadata APIのS3資源等 | `POST /v1/scan`。接続済み資源を再検査し、応答は`202 Accepted`。結果そのものではない |
| Macie | `ListFindings`、`GetFindings`、`GetSensitiveDataOccurrences`。AWS CLIは`aws macie2 ...` | `CreateFindingsFilter(action=ARCHIVE)`、`CreateClassificationJob`等 |
| Palo Alto Networks | `GET /v2/api/incidents`、`GET /v2/api/incidents/{id}` | `PUT /v1/api/incidents/{id}/resolution-status`、担当・注記。資源ごとにv1・v2、試験版v4を区別 |
| BigID | `GET /api/v1/actionable-insights/all-cases`、`GET /api/v1/data-catalog/objects/stream`、`GET /api/v1/scans/{id}/status` | `PATCH /api/v1/actionable-insights/case-status/{caseId}`、検査設定の`POST /api/v1/scanProfiles`、検査起動の`POST /api/v1/scans`。分類器と判定はMCP説明とRESTの検証範囲を区別 |

## 人の判定をAPIで登録するときの違い

### Nightfall

Native SaaSの違反管理APIと、任意データを検査する `/v3/scan` 等は別系統。前者は後者で検査した独自アプリの違反を取得するAPIではない。違反取得は既定50件・最大100件、作成日時の既定範囲は直近90日で、`updatedAfter` と `pageToken` もある。**既定の検索範囲は保存期間の保証とは異なる。** [NF1,NF4]

Findingには検知器、信頼度、伏字付きの値・前後文脈・位置、判定識別子がある。`redactedSensitiveText` を原文値と扱わず、伏字後の値だけで別人や別の秘密を同一視しない。管理画面の原文表示機能と、APIが返す項目は別に評価する。[NF1]

判定には `DETECTOR_FALSE_POSITIVE`、`COMPANY_IGNORED_FALSE_POSITIVE`、`DETECTOR_TRUE_POSITIVE` がある。`autoApply` は既定で `true`。フォルダー条件のない自動適用を、そのまま「このフォルダーでは電話番号を許可」に使わない。場所限定なら、個別登録の `autoApply:false` と外部の許可台帳を組み合わせる案を検証する。検知の正誤と、業務上の許可は分ける。[NF1]

違反への動作は接続先・違反の `possibleActions` によって異なり、実行できない対象は無視される仕様がある。受付成功だけで全対象に反映されたと扱わず、違反の状態・履歴を読み直す。[NF1]

### Strac

公開APIには検知一覧だけでなく誤検知登録もある。登録は `documentId` に対し最大50文書／回、既定の `appType` は `slack`。応答が200でも、各対象の `marked`／`not_found`／`error` を確認する必要がある。[S1]

誤検知にしたものは通常の一覧から除外され、`showFalsePositivesOnly=true` で別途取得する。全件台帳を作るなら通常と誤検知済みを両方取り込む必要がある。資料で具体的に説明されたSlackの挙動を、Driveを含む全アプリの取消し・将来継承へ広げない。業務上許可された実際の個人情報を誤検知として扱う設計も避ける。[S1]

### MicrosoftとNetskope

Graphの現行警告APIはPurview DLPを対応元に含む。`SecurityAlert.Read.All`で取得、`SecurityAlert.ReadWrite.All`で状態・分類等の変更を行う。原文値や文脈を含むDLP記録はManagement Activity APIの権限付き経路も確認する。警告を `falsePositive`／`resolved` にする操作は、今後の同じ値の検知を許可する操作とは別である。[M1–M4,M9–M11]

Netskopeの `/incidents/update` も状態・重要度・担当の更新であり、場所と属性を条件にした将来の通知停止を証明しない。証拠取得は別のforensics経路。APIトークンにも読取りと書込みの範囲を分ける。[N1–N3]

### Macie

APIで作る検出結果フィルターの `ARCHIVE` は検出結果を保管済みにして抑制する。検査から値を除く許可リストとは異なる。台帳には保管済みも含め、検知の有無と通知状態を別に持つ。抑制したものの扱いと保存期間は[既存比較](dlp_decision_and_alert_suppression_matrix_20261111.md)を参照。[A2]

## BigIDの追加確認

BigIDはGoogle Driveの内容検査と、検知資産・危険な状態の問題管理を比較する直接候補。問題一覧だけでは、許可された場所の個人情報まで収集できるとは限らないため、資産一覧も取得する。分類結果の正誤判定と問題の`silenced`は公式MCP資料で確認したが、フォルダー×属性×期限の許可や、移動・内容変更後の自動失効は未確認。[BI1,BI7,BI9,BI10]

通常の資産一覧には1万件の検索窓による打切りがあるため、全件出力は`/data-catalog/objects/stream`を使う。検査状態の`false`は停止を意味し、正常完了とは限らない。詳細は[BigIDのAPI・形式・日本語・許可運用の精査](bigid_dlp_api_constraints_20261111.md)にまとめた。[BI3,BI4]

## 自動取得と再検査の制約

| 製品 | 認証・取得上限・結果の解釈 |
|---|---|
| Google Workspace | 管理者権限とAPI別scopeが必要。原文抜粋と監査記録には容量・期間の限界。[詳細](google_workspace_dlp_cli_api_deep_dive_20261111.md) |
| Box | 企業全体のEvents取得には管理権限。`admin_logs`は1年の履歴、`admin_logs_streaming`は低遅延だが重複・順序逆転あり。`SHIELD_ALERT`は主に脅威検知、Smart Access事象と区別。全個人情報値の一覧とは扱わない [B1,B3,B4] |
| Nightfall | Bearer認証。Native APIの公表上限はFree平均5回／秒、Enterprise平均10回／秒、瞬間上限は別。429時はRetry-Afterへ従う。契約による利用可否・割当を確認 [NF3] |
| Purview | Management Activity APIは購読開始、一覧取得、内容取得の複数段階。新しい内容の検索は1回24時間以内・開始は過去7日以内。これは監査全体の保存期間ではない。Activity Explorer出力は直近30日、続きはWatermark／PageCookie [M8,M11] |
| Microsoftの機微な内容 | 原文値・文脈には追加の読取り許可。`SensitiveInfoDetectionIsIncluded` と `ResultsTruncated` を確認。Graph警告と原文証拠は同じ応答だと期待しない。Google Drive等の外部接続で同じ項目が出るかは別途検証 [M4,M11] |
| Netskope | API v2の権限付きトークン。forensics収集・権限・契約を確認。データ出力のページ継続・更新と問題の状態APIを分ける [N1,N2] |
| Strac | `X-Api-Key`。直接Detectは本文データURL最大4 MB、文書アップロードは10 MB。保存先接続の容量保証とは別。文書保管・原本ダウンロード・削除APIもあるため、即時検査だけの無保存方式と決めつけない [S1] |
| Teleskope | API用の鍵と配置先ごとのURL。`/v1/scan`の`resource_id`はTeleskope内部識別子で、Driveのファイル識別子と別。Box月次API割当到達時には202でも検査しない条件が明記される。Driveにも同じ例外があると推定しない [T3,T4] |
| Teleskopeの直接ファイル検査 | multipart全体32 MB、文字ファイルは先頭500 KB。形式を判定できないと空の200応答。コードファイルではfiltersが適用されない。HTTP成功・空の結果を検査完了や陰性の証拠にしない [T2] |
| Macie | AWSの権限制御で検出結果と原文の標本取得を分離。原文取得は復号等の条件も必要。全機密値の一括出力ではない [A1,A3,A4] |
| Palo Alto Networks | サービスアカウント、組織のTSG識別子、アクセストークン。DLP用ロール・サービス利用権限が必要。2026年8月追加のv2と大量取得用の試験版v4を区別 [PA1,PA2] |
| BigID | 資産の継続出力はv250以降、MongoDB方式では追加設定が必要。問題管理と原本の修正は契約・権限が異なる。標本保存用のSnippet Persisterを含め、原文の送信先と保持を別に確認 [BI4,BI5,BI10,BI11] |
| Google Cloud | `includeQuote`、検出上限、検査地域等を設定。`findingsTruncated=true`では返った検出が全体の一部なので、分割検査が必要 [G1–G3] |
| Presidio／Privacy Filter | 自前の実行環境。APIサービスの認証・アクセス制御・容量制御・記録保持・モデル更新を運用する。公開モデルやRESTサービスがあることは管理済みDLPの完成を意味しない [PR2,PR3,O1] |

## 今回の用途での選び方

| 目的 | API構成の候補 | 残る確認 |
|---|---|---|
| Driveの既存DLPを利用し、許可と通知だけ自作 | Google Workspaceの監査のみ＋Reports API＋Drive API | 原文抜粋の欠落、検査済み版の証明、親階層と移動 |
| 既存の検知台帳と人の判定を外部画面から操作 | Nightfall Native API | 日本語品質、伏字と原文の差、autoApplyの場所・属性への適用境界 |
| Drive・DB・ファイルをまとめ、分類と問題管理を外部へ連携 | BigIDの資産一覧・Data Posture API・MCP | 正誤と業務許可の分離、silencedの失効・再発、全件出力、検査完了の判定、日本語の品質 |
| 企業の対応管理へ連携 | Netskope、Purview／Graph、Palo Alto Networks | 対応完了と将来の通知抑制を分離、証拠の取得範囲 |
| 検知一覧と誤検知一覧を自社台帳へ集約 | Strac | Driveでの判定操作の対応範囲、取消し、通常一覧から消える検知の取り込み |
| 登録資源をAPIで再検査 | Teleskope、S3ならMacie | 受付・実行・完了・結果取得を別々に追跡 |
| 値・位置・許可期限を自由に設計 | Google Cloud、Presidio、Privacy Filter等 | 本文抽出、網羅性の評価、全件台帳、承認、再評価、通知まで自作 |

自社台帳には少なくとも、製品側の検出識別子、保存先の識別子、検査した版、検知属性、値・位置の取得状態、人の判定、許可条件、通知状態、最終照合時刻を分けて保存する。値が伏字・抜粋・標本・欠落のどれかも保持する。識別子をJavaScript等の数値として読むと桁落ちする場合があるため、提供元の型と値を保持する。

検知器の除外やAPIの `filters` は結果自体を減らす場合がある。「検知は全件残すが通知しない」要件では、検知用の取得段階から属性を除外せず、通知判断の段階へ許可条件を置く。詳細な自作構成は[公開事例と設計案](dlp_self_built_cases_20261111.md)を参照。

## 公開一次資料

取得日時・URL・本文ハッシュ・API定義の確認項目は[出典確認記録](dlp_related_services_api_sources_20261111.json)。全文や組織の検知結果は収録しない。

| 番号 | 資料 |
|---|---|
| GW | [Google WorkspaceのCLIとAPI詳細](google_workspace_dlp_cli_api_deep_dive_20261111.md)とその一次資料 |
| B1 | [Box Shield Alert Events](https://developer.box.com/guides/events/event-triggers/shield-alert-events/) |
| B2 | [Box Classifications API](https://developer.box.com/guides/metadata/classifications/) |
| B3 | [Box Events API](https://developer.box.com/reference/get-events/) |
| B4 | [Box Shield Smart Access Events](https://developer.box.com/guides/events/event-triggers/shield-smart-access-events/) |
| NF1 | [Nightfall Native SaaS Apps API](https://help.nightfall.ai/developer-api/nightfall_apis/saas) |
| NF2 | [Nightfall Policy Update APIs](https://help.nightfall.ai/developer-api/nightfall_apis/scope_update) |
| NF3 | [Nightfall Native APIの上限](https://help.nightfall.ai/developer-api/nightfall_apis/saas/rate-limits-for-native-saas-app-apis) |
| NF4 | [Nightfall直接検査API](https://help.nightfall.ai/developer-api/nightfall_apis/dlp) |
| M1 | [Microsoft Graph alert資源](https://learn.microsoft.com/en-us/graph/api/resources/security-alert?view=graph-rest-1.0) |
| M2 | [Graph alerts_v2一覧](https://learn.microsoft.com/en-us/graph/api/security-list-alerts_v2?view=graph-rest-1.0) |
| M3 | [Graph alertの変更](https://learn.microsoft.com/en-us/graph/api/security-alert-update?view=graph-rest-1.0) |
| M4 | [Management Activity APIのDLP記録形式](https://learn.microsoft.com/en-us/office/office-365-management-api/office-365-management-activity-api-schema) |
| M5 | [Get-DlpComplianceRule](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-dlpcompliancerule?view=exchange-ps) |
| M7 | [Set-DlpCompliancePolicy](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/set-dlpcompliancepolicy?view=exchange-ps) |
| M8 | [Export-ActivityExplorerData](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/export-activityexplorerdata?view=exchange-ps) |
| M9 | [Graph Security APIの対応元](https://learn.microsoft.com/en-us/graph/api/resources/security-api-overview?view=graph-rest-1.0) |
| M10 | [Graph Securityの列挙値](https://learn.microsoft.com/en-us/graph/api/resources/enums-security?view=graph-rest-1.0) |
| M11 | [Management Activity API](https://learn.microsoft.com/en-us/office/office-365-management-api/office-365-management-activity-api-reference) |
| M12 | [Get-DlpCompliancePolicy](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-dlpcompliancepolicy?view=exchange-ps) |
| D1 | [Defender for Cloud Apps Alerts API](https://learn.microsoft.com/en-us/defender-cloud-apps/api-alerts) |
| D2 | [File policiesの廃止予定と仕様](https://learn.microsoft.com/en-us/defender-cloud-apps/data-protection-policies) |
| N1 | [Netskope Tenant Pluginの利用API](https://docs.netskope.com/en/netskope-tenant-plugin) |
| N2 | [Netskope APIトークンと操作権限](https://docs.netskope.com/en/api-tokens-2) |
| N3 | [Netskope公式公開コードのDLP操作例](https://github.com/netskopeoss/AI_Integrations_Reference_MarkDownFiles/blob/main/DLP-Incident-Management.md) |
| S1 | [Strac DLP API Reference](https://docs.strac.io/) |
| T1 | [Teleskope API Service](https://docs.teleskope.ai/the-platform/api-service) |
| T2 | [Teleskope classify-file](https://docs.teleskope.ai/the-platform/api-service/scanning-api/v1-classify-file) |
| T3 | [Teleskope scan](https://docs.teleskope.ai/the-platform/api-service/scanning-api/v1-scan) |
| T4 | [Teleskope Policy Maker APIのメール追加](https://docs.teleskope.ai/the-platform/api-service/policy-maker-api/v1-policy-maker-policies-add-email) |
| T5 | [Teleskope S3 Metadata API](https://docs.teleskope.ai/the-platform/api-service/metadata/aws/s3/aws-s3-api) |
| T6 | [Teleskope classify](https://docs.teleskope.ai/the-platform/api-service/scanning-api/v1-classify) |
| A1 | [Macie GetFindings](https://docs.aws.amazon.com/macie/latest/APIReference/findings-describe.html) |
| A2 | [Macie検出結果フィルターAPI](https://docs.aws.amazon.com/macie/latest/APIReference/findingsfilters.html) |
| A3 | [Macieの機微な内容の標本取得](https://docs.aws.amazon.com/macie/latest/user/findings-retrieve-sd-proc.html) |
| A4 | [Macie API操作一覧](https://docs.aws.amazon.com/macie/latest/APIReference/operations.html) |
| PA1 | [Palo Alto Networks DLP APIs](https://pan.dev/dlp/api/) |
| PA2 | [Palo Alto Networks API変更履歴](https://pan.dev/cdss/docs/release-notes/) |
| PA3 | [Palo Alto Networks incident詳細](https://pan.dev/dlp/api/get-v-2-api-incidents-incidentid/) |
| G1 | [Google Cloud content.inspect](https://docs.cloud.google.com/sensitive-data-protection/docs/reference/rest/v2/projects.content/inspect) |
| G2 | [Google Cloud InspectConfig](https://docs.cloud.google.com/sensitive-data-protection/docs/reference/rest/v2/InspectConfig) |
| G3 | [Google Cloud DLP API公開定義](https://dlp.googleapis.com/$discovery/rest?version=v2) |
| PR2 | [PresidioのREST利用](https://presidio.dataprivacystack.org/getting_started/getting_started_text/) |
| PR3 | [PresidioのAPI定義 固定版](https://github.com/data-privacy-stack/presidio/blob/1d7005932261a4b676e045d16fa2965dbc4b4ba2/docs/api-docs/api-docs.yml) |
| O1 | [OpenAI Privacy Filter 固定版](https://github.com/openai/privacy-filter/blob/f7f00ca7fb869683eb732c010299d901457f19c3/README.md) |
| O2 | [OpenAI Agent Builderの入力保護](https://developers.openai.com/api/docs/guides/agent-builder-safety#use-guardrails-for-user-inputs) |
| AN1 | [Claudeの独自分類の公式例](https://platform.claude.com/docs/en/about-claude/use-case-guides/content-moderation) |
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
