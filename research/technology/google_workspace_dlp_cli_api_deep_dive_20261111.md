# Google Workspace DLPのCLI取得とAPI仕様

調査日：2026年11月11日。Google Workspace CLIは `googleworkspace/cli` の `gws` を指す。DLPは機密情報の検知・制御、APIはプログラムからの呼出し口、CLIは端末からコマンドで操作する仕組み、OAuth scopeは認証時に許可する操作範囲である。

Box・Nightfall・Microsoft・Netskope・Strac・Teleskope等との比較は[機密情報検知サービスのAPI対応表](dlp_related_services_api_matrix_20261111.md)を参照。

**DLPの検知ログは `gws admin-reports activities list` で取得する構成にできる。ルールと独自検知器の設定はCloud Identity Policy API、警告一覧はAlert Center APIで取得する。確認した版のgwsには後二者のサービス登録がなく、API直接呼出しが必要になる。** Google Cloud Sensitive Data Protectionの検査APIは別製品であり、Workspaceの検知ログを取り出すAPIではない。[C1–C3,P1–P4,R1,A1]

以下は公開仕様と固定版コードによる確認で、組織への認証・ログ取得・ルール変更は行っていない。コマンド例も認証済み環境での実行検証はしていない。組織から取得する設定・検知結果・原文抜粋は非公開情報として、この公開調査リポジトリへ保存しない。

## 取得対象による違い

| 欲しいもの | APIと取得内容 | gwsの対応 | 今回の用途での限界 |
|---|---|---|---|
| DLPルールの設定 | Policy APIの `policies.list/get`。条件、適用範囲、動作、有効状態等 | 確認版では未登録。直接呼出し | 検知結果ではなく設定。実効設定と、明示設定された元の規則も区別する [P1–P4] |
| 独自検知器 | 同API。正規表現・語句一覧・URL一覧の設定 | 同上 | 標準検知器の学習済みモデルや内部判定器を取得するものではない [P3] |
| 検知・動作の監査記録 | Reports APIの `activities.list`、`applicationName=rules` | 対応するコマンドあり | DLP以外の規則も含む。イベント種別ごとに項目が異なる [C1,R1–R3] |
| 一致した原文の抜粋 | 同APIの `includeSensitiveData=true` と `snippets` | API定義に項目あり。利用版のschemaを確認 | 保存設定・権限に依存。切詰め・件数削減があり、全検知箇所の完全一覧ではない [R1,R2,S1] |
| 発生した警告 | Alert Center APIの `alerts.list/get`、`DlpRuleViolation` | 確認版では未登録 | 通知しない規則の検知台帳には不十分。警告は1規則1日50件まで [A1,A2,D3] |
| 指定ファイルの最新の全検知箇所 | 上記APIに汎用の全箇所取得手段は確認できない | 完成コマンドとして扱わない | 過去イベント・抜粋と、現時点の全件検査結果は別 |
| 任意の内容を即時検査 | Workspaceの上記APIは設定・記録の取得用 | `activities.list`では検査を起動しない | 自前の本文抽出と別の検知器、または別製品の検査APIを組み合わせる |
| 人の許可判定と将来通知の抑制 | 独自台帳・通知処理として追加 | 完成機能ではない | 警告の状態変更を、同じ値に対する恒久許可へ読み替えない |

## gwsの公開コードで確認できる範囲

対象版は `cd3697e07eb520056dcf142d0c7439bbb9ba32e9`。サービス登録には `admin-reports`／`reports` → `admin` の `reports_v1` があり、`cloudidentity` と `alertcenter` はない。[C1]

`service:version` の解析後も `resolve_service(service)` を呼ぶ実装のため、未登録サービスを `gws cloudidentity:v1 ...` や `gws alertcenter:v1beta1 ...` と書くだけでは通らない。未登録APIも使えるように見えるエラーメッセージはあるが、コードの実際の分岐を優先した。これは当該版の静的解析であり、今後の版まで非対応と断定しない。[C1,C2]

gwsは対応サービスのAPI公開定義を読んでコマンドを組み立てる。API公開定義とは、呼出し名・引数・応答形式を機械可読に記述したDiscovery Documentである。今回取得した定義では、Reports APIは20261109版に `includeSensitiveData`、Cloud Identity APIは20261108版に `policies` のget/list/create/patch/deleteが存在した。[J1,J2]

## 検知ログの取得例

まず利用中のgwsの版と引数を調べる。以下は読み取りコマンドの例である。

```bash
gws --version
gws admin-reports --help
gws schema admin-reports.activities.list
```

```bash
gws admin-reports activities list \
  --params '{"userKey":"all","applicationName":"rules","startTime":"2026-11-01T00:00:00Z","endTime":"2026-11-02T00:00:00Z","maxResults":1000,"includeSensitiveData":false}' \
  --page-all --page-limit 1000
```

ここでは最初から `eventName=rule_match` に限定しない。規則関連には `rule_match`、`rule_trigger`、`action_complete`、ラベル付与・変更・除去等があり、1種類だけでは関連する経緯を取り落とす。`rule_match` は `matched_templates` や `rule_id` を持つ一方、`action_complete` 等は `matched_detectors` や `rule_resource_name` 等を持ち、同一形式ではない。[R2]

出力は1ページにつき1個のJSONを1行で表すNDJSONになる。`--page-all` の既定ページ上限は10であり、「全ページ指定だから必ず最後まで取れる」と扱わない。上例も1,000ページに達して最後の応答に `nextPageToken` が残れば未完了であり、期間の分割や続きの取得が必要。APIの1ページは最大1,000件。[C3,R1]

最初は原文抜粋を含めずに取得し、返ったイベントの `parameters` を確認する。DLPかどうかを表す `rule_type`、Driveを表す `data_source` があるイベントではそれらで絞り込む。項目のない旧形式等を無条件に廃棄せず、規則識別子・イベント仕様との対応を確認する。[R2]

原文の確認が必要なら、同じリクエストの `includeSensitiveData` を `true` にする。これは「権限も保存設定も不要になる」指定ではなく、応答に機微な利用者生成内容を含めるためのAPI引数である。Rules、Chat、Workspace Studio以外への同指定は権限エラーになる仕様がある。[R1,J1]

### 記録として保存する項目

| 区分 | 主な項目 | 解釈 |
|---|---|---|
| 元イベント | `id.time`、`id.uniqueQualifier`、`events[].name`、元の `parameters` | 元データを保持し、正規化後の表だけにしない。重複排除鍵は顧客・アプリ・活動識別子と配下イベントも考慮 |
| 対象 | `resource_id`、`resource_title`、`resource_owner_email` | ファイルとの照合。項目の有無はイベント別 |
| 規則 | `rule_resource_name`／`rule_id`、`rule_name`、`rule_type` | 名前変更に備え識別子を使う。旧形式と新形式の対応を保存 |
| 検知内容 | `matched_detectors`／`matched_templates`、`matched_threshold`、`snippets` | 必ずすべての値・位置・件数がそろうものではない |
| 実行経緯 | `scan_type`、`has_alert`、`triggered_actions`、`suppressed_actions` | `suppressed_actions` は優先度の高い動作があるため実行されなかった動作を表す。業務上の許可一覧ではない |
| 共有先 | `resource_recipients`、`resource_recipients_omitted_count` | 検知時の共有先。一部省略や、その後の変更を考慮 |

項目は公式イベント定義による。入れ子の `messageValue` 等を文字列と同一視しない。警告APIの `suppressedActionTypes` も独自の許可台帳へ直接変換しない。[R1,R2,A2]

## ルール設定の取得と変更

### 直接取得する例

Policy APIの読み取り用OAuth scopeは `https://www.googleapis.com/auth/cloud-identity.policies.readonly`、変更用は末尾が `.policies` のscope。利用者は特権管理者である必要がある。無人処理の公式例では、サービスアカウントへ組織全体の権限を委任し、管理者として実行する。[P1,P4–P6]

次は、上記の読み取りscopeを持つ有効なアクセストークンが別途用意されている場合の取得例。環境変数名は説明用であり、この調査ではトークンの取得・設定は行わない。

```bash
curl --fail-with-body --get \
  'https://cloudidentity.googleapis.com/v1/policies' \
  --header "Authorization: Bearer ${WORKSPACE_POLICY_ACCESS_TOKEN}" \
  --data-urlencode 'filter=customer == "customers/my_customer"' \
  --data-urlencode 'pageSize=100'
```

`nextPageToken` がある限り `pageToken` に渡して続きを取る。既定は50件、最大100件。まず取得した `setting.type` の実値を確認し、DLPルールと検知器へ絞る。文書中には `settings/` 付きの表現と省略された設定型名が併存するため、接頭辞を推測した正規表現だけに依存しない。[P2,P4]

| 設定型 | 何を表すか | 取得後に確認するもの |
|---|---|---|
| `rule.dlp` | DLPルール | 条件、適用範囲、有効状態、動作等 |
| `detector.regular_expression` | 独自の形式規則 | 正規表現と参照される規則 |
| `detector.word_list` | 独自の語句一覧 | 語句一覧と参照される規則 |
| `detector.url_list` | 独自のURL一覧 | 対象アプリと用途。Driveのフォルダー許可一覧を意味しない |

これらの設定型には変更対応が明記されている。APIの変更応答は `Operation`、すなわち処理の進行・結果を表す資源であり、HTTP成功だけで適用・再検査の完了と扱わない。[P3,J2]

### APIの有無に関する公式資料の食い違い

Drive DLP FAQには依然としてAPI利用不可の回答がある。一方、2026年6月8日の公式発表はDLPルール・検知器の作成・更新・削除を追加し、現在のCloud Identity API仕様とDiscovery Documentにも実在する。**APIの有無は、古いFAQの一文ではなく、対象の現行API・設定型・操作に分けて判断する。** [D1,P3,P7,J2]

## 実行権限を混同しない

| 用途 | 認証時の主な許可範囲 | 管理権限等 |
|---|---|---|
| 規則監査記録の読取り | `admin.reports.audit.readonly` | 対応する管理者権限。一般利用者のDrive閲覧権限だけでは足りない [R1,R3] |
| 抜粋の保存・閲覧 | 上記API引数に加え設定・権限を確認 | 原文保存を有効にする。管理画面での閲覧には機微な内容を見る権限と設定が必要。APIでも期待する内容が返るかを検証 [S1] |
| Policy APIの読取り | `cloud-identity.policies.readonly` | 特権管理者。サービスアカウントだけに権限を与えて終わりにはしない [P1,P5,P6] |
| Alert Center API | `apps.alerts` | 警告API用の認証・管理権限を別途設定。読取り専用scopeという名称ではない [A1] |
| ファイルの親・版・共有状態 | Drive APIの用途に合ったscope | 対象ファイルへのアクセスが別途必要。特権管理者だから任意の利用者の全ファイルが自動的に読めるとは扱わない [F1,F2] |

表のscopeはすべて `https://www.googleapis.com/auth/` 以下。権限委任の設定とアプリが要求するscopeは完全に対応させる。広い別scopeを許可しても必要なscopeの代替にならない。[P4]

## 検知結果を全件台帳にする場合の制約

| 制約 | 仕様と含意 |
|---|---|
| 抜粋は全箇所ではない | 前後各100 Unicode文字までの文脈を含み、抜粋は500文字で切詰め。イベントの `snippets` 合計50 KBに収めるため抜粋自体が除去される。元データ変更・削除後も180日閲覧可能なため、現在の原本とも一致しない [S1] |
| 警告一覧は検知全集ではない | 通知を有効にした規則だけが警告を発生させる。1規則1日50件の上限があり、再共有後の受信者情報も自動更新されない。まず規則監査記録を収集する [D3] |
| 何も返らない意味 | 陰性、未検査、非対応、取得期間外、権限不足、遅延、規則不一致を区別できない場合がある。ログ不在を「検査済みで問題なし」に変換しない |
| 原本の網羅的検査ではない | 抽出文字の先頭10 MB、非Google形式の文字抽出は50 MBまで、圧縮内部1,000ファイル、検出10,000件／ファイル等の制約がある [D2] |
| 過去記録と現在の場所 | 監査記録だけで現時点の親階層・共有状態を確定しない。Drive APIで親をたどり、移動・削除も照合する [F1,F2] |
| 取得可能期間と処理量 | Reports APIは原則直近180日の範囲で取得する。1ページ最大1,000件、既定のAPI割当は利用者・プロジェクト当たり毎分2,400照会、条件付き照会は追加上限がある [R1,R4] |
| 即時性と完了証明 | 規則反映には最大24時間。検査起動、検知記録、警告作成、取得可能化は別段階。API取得成功は全ファイル検査完了の証拠ではない [D1,D3] |

監査記録の取込みは一定時間を重複させて再取得し、活動と配下イベントの識別子で重複排除する設計が適する。遅延許容幅は測定して決める。原文抜粋を外部へ保存した場合は、Google側で非表示・削除しても外部の複製へ自動反映されるとは扱わない。

## 指定フォルダーの氏名と電話だけを許可する構成

今回の要件は「検知は残すが、許可場所の特定属性だけ通知しない」。Google側の検知そのものを除外すると台帳に残せないため、**検知用規則と通知の判断を分ける**構成を検討する。

| 段階 | 構成案 | 確認すべきこと |
|---|---|---|
| 検知 | 氏名、電話、秘密鍵等の属性別に監査のみの規則を有効化し、通知を無効化 | 監査のみでも一致時の記録が残る。全ファイル・全箇所の完全台帳になるとは限らない [D4] |
| 収集 | Reports APIをgws等で定期取得 | イベントの形式、遅延、ページの欠落、原文抜粋の有無 |
| 場所の照合 | Driveの `resource_id` をもとに親フォルダーを再帰的にたどる | 指定フォルダー直下と全子孫を区別。移動・ショートカットの扱いを定義 |
| 許可 | フォルダー識別子×属性×共有条件×期限×判定者を独自台帳に保持 | 「正しい検知だが業務上許可」と「誤検知」を分ける |
| 通知 | 許可条件に合う氏名・電話は通知せず、同じファイルの秘密鍵等は通知 | 許可で検知記録を削除しない。複数検知器の結果を属性へ対応させる |
| 再評価 | 内容・場所・共有条件・規則の変更で許可を再判定 | Driveの現在の版と、検知イベントが検査した時点の版を同一視しない |

Google標準側で条件を表現する候補にはDrive分類ラベルがあるが、**フォルダー識別子とその子孫を任意条件として直接指定できるとは今回も確認できない**。Policy APIのDrive条件表では本文・題名・形式・分類ラベル等が列挙される。URLの前方一致はフォルダー所属の判定にならず、`policyQuery.orgUnit` は利用者等の組織部門であってファイルの親フォルダーではない。[P2,P3]

Driveの現在の属性を確認するコマンド例は次のとおり。`version` は本文以外も含むサーバー上の変更で増える値で、内容だけの指紋ではない。[F1,F2]

```bash
gws drive files get \
  --params '{"fileId":"FILE_ID","supportsAllDrives":true,"fields":"id,name,mimeType,parents,driveId,version,modifiedTime,trashed"}'
```

この構成は検知基盤をGoogleに任せ、場所ごとの許可・一覧・通知を自作する案である。全件の正確な値・位置まで必要なら、抜粋の上限を補う独自抽出・検査が必要になる。日本語の検知種類、形式ごとの検査対象、実測精度の扱いは[形式と精度の比較](dlp_detection_formats_accuracy_matrix_20261111.md)、自作の責任範囲は[公開事例](dlp_self_built_cases_20261111.md)を参照。

## 導入前に行う検証

実在者の情報を使わず、合成文書で次を検証する。以下は試験計画であり、実施済み結果ではない。

| 試験 | 合格条件 |
|---|---|
| 監査のみ | 通知なしでも氏名・電話等の記録がAPIに返る |
| 属性の分離 | 氏名・電話を許可しても、新たに追記した秘密鍵は通知候補になる |
| フォルダー移動 | 許可配下へ移動・配下から移出したとき、許可状態を再計算する |
| 共有変更 | 検知時の受信者一覧に頼らず、現在の共有条件を評価する |
| 抜粋の欠落 | 大量検出でも上限到達を考慮し、完全一覧と誤表示しない |
| 抽出の失敗 | 画像PDF・暗号化・容量超過等を「問題なし」にしない |
| 再取得 | 同じ期間を重複取得しても通知が重複せず、遅れて現れた記録を取り込める |
| 再検査 | 規則変更や原本修正後に、旧記録が残っていても現在状態と分離できる |

## 公開一次資料

取得URL・日時・本文のSHA-256・API定義から抽出した対応項目は[出典確認記録](google_workspace_dlp_cli_api_sources_20261111.json)に保存。組織の設定・ログ・認証情報は含めない。

| 番号 | 資料 |
|---|---|
| C1 | [gwsのサービス登録 固定版](https://github.com/googleworkspace/cli/blob/cd3697e07eb520056dcf142d0c7439bbb9ba32e9/crates/google-workspace/src/services.rs) |
| C2 | [gwsのサービス名と版の解析 固定版](https://github.com/googleworkspace/cli/blob/cd3697e07eb520056dcf142d0c7439bbb9ba32e9/crates/google-workspace-cli/src/main.rs#L321) |
| C3 | [gwsの仕様とページ取得](https://github.com/googleworkspace/cli/blob/cd3697e07eb520056dcf142d0c7439bbb9ba32e9/README.md) |
| P1 | [Policy API overview](https://docs.cloud.google.com/identity/docs/concepts/overview-policies) |
| P2 | [Policy資源の定義](https://docs.cloud.google.com/identity/docs/reference/rest/v1/policies) |
| P3 | [Policy APIの対応設定](https://docs.cloud.google.com/identity/docs/concepts/supported-policy-api-settings) |
| P4 | [policies.list](https://docs.cloud.google.com/identity/docs/reference/rest/v1/policies/list) |
| P5 | [Setting up the Policy API](https://docs.cloud.google.com/identity/docs/how-to/setup-policies) |
| P6 | [Listing and getting policies](https://docs.cloud.google.com/identity/docs/how-to/list-get-policies) |
| P7 | [DLPの変更API追加 2026年6月8日](https://workspaceupdates.googleblog.com/2026/06/introducing-workspace-policy-api-mutate-endpoints-for-DLP.html) |
| P8 | [Creating patching and deleting policies](https://docs.cloud.google.com/identity/docs/how-to/create-patch-delete-policies) |
| R1 | [Reports API activities.list](https://developers.google.com/workspace/admin/reports/reference/rest/v1/activities/list) |
| R2 | [Rules Audit Activity Events](https://developers.google.com/workspace/admin/reports/v1/appendix/activity/rules) |
| R3 | [Reports API overview](https://developers.google.com/workspace/admin/reports/v1/overview) |
| R4 | [Reports APIの上限](https://developers.google.com/workspace/admin/reports/v1/limits) |
| S1 | [検知した原文抜粋の保存と制約](https://knowledge.workspace.google.com/admin/security/view-content-that-triggers-dlp-rules) |
| A1 | [Alert Center alerts.list](https://developers.google.com/workspace/admin/alertcenter/reference/rest/v1beta1/alerts/list) |
| A2 | [DlpRuleViolation](https://developers.google.com/workspace/admin/alertcenter/reference/rest/v1beta1/DlpRuleViolation) |
| D1 | [Drive DLP FAQ APIの記述は現行仕様と不整合](https://knowledge.workspace.google.com/admin/security/dlp-for-drive-faq) |
| D2 | [DLPの容量と規則の上限](https://knowledge.workspace.google.com/admin/security/view-dlp-content-and-rule-size-limits) |
| D3 | [DLPの警告と監査記録](https://knowledge.workspace.google.com/admin/security/view-dlp-for-drive-dashboard-incidents-alerts-and-audit-events) |
| D4 | [Drive DLP規則と監査のみの設定](https://knowledge.workspace.google.com/admin/security/create-dlp-for-drive-rules-and-custom-content-detectors) |
| F1 | [Drive files資源](https://developers.google.com/workspace/drive/api/reference/rest/v3/files) |
| F2 | [Drive files.get](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/get) |
| J1 | [Reports APIの公開定義](https://admin.googleapis.com/$discovery/rest?version=reports_v1) |
| J2 | [Cloud Identity APIの公開定義](https://cloudidentity.googleapis.com/$discovery/rest?version=v1) |
