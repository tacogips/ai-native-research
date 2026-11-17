# v3検証環境の準備と最初の対照試験

この文書は公開仕様と架空資料に基づく手順案。実環境での実施記録ではない。実施は別途明示された指示を受けて行い、識別子・画面・監査・測定値をリポジトリ外へ保存する。

## 管理画面とAPIの使い分け

| 対象 | 確認できた公開仕様 | この版での経路 |
|---|---|---|
| 正規表現検知器 | Policy APIの`detector.regular_expression`は変更対応。ただし参照した表は値を`Struct`（入れ子の構造）とだけ記載している | 管理画面で作成・読み戻し。内部フィールドを推測したAPI作成要求は送らない |
| 語句一覧 | Policy APIの`detector.word_list`は変更対応 | このv3用の自動作成処理は未接続。管理画面で作成・読み戻し |
| DLP規則 | Policy APIは`matches_regex_detector`等の条件を記述できる | この版の`label-plan`は設計JSON。APIへそのまま送る形式ではない |
| ラベル定義 | Drive Labels APIにラベル作成の方法がある | `label-plan`に作成要求の計画を含む。API実行処理は未実装で、管理画面で作成できる |
| ファイル上のラベル | Drive APIの`files.listLabels`で取得できる | `labels.py`で読取専用に実装。既定は計画表示 |

変更対応と、正しい作成要求の形式を確認できたことは別である。今回参照した公開表だけでは`regular_expression`内部のフィールド名・必須値を確定できないため、APIで作成できないと断定せず、作成要求の実装を保留する。今後、公式の具体例・型定義が見つかれば、それに基づく計画生成と模擬通信試験を追加する。

出典：[Policy APIの設定表](https://docs.cloud.google.com/identity/docs/concepts/supported-policy-api-settings)、[Drive Labels APIのラベル作成](https://developers.google.com/workspace/drive/labels/guides/create-label)、[files.listLabels](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/listLabels)。2026年11月16日確認。

## 管理者用ラベルの認可範囲

`label-plan`の`ADMIN`型ラベルをAPIで管理する場合、`useAdminAccess=true`、利用者のManage Labels権限、書込み用の`https://www.googleapis.com/auth/drive.admin.labels`が必要である。管理者として定義を読むだけなら`drive.admin.labels.readonly`を利用できる。`drive.labels`による書込みは、`useAdminAccess`を設定しない利用者アクセスでの`SHARED`型に対応するため、`ADMIN`型の作成・公開の代用にはしない。各メソッドが複数のscopeを列挙していても、ラベル型とアクセス方式に合うものを選ぶ。[公式の認可範囲とAdministrator access](https://developers.google.com/workspace/drive/labels/guides/authorize)

Drive Labels APIの有効化、OAuthの許可範囲、管理者権限はそれぞれ別の条件である。ファイル上に付与された値の`files.listLabels`等はDrive APIの操作であり、ラベル定義を管理するDrive Labels APIのscopeと混同しない。

## 準備と入力値

1. `build.py make`で合成資料を生成し、`label-plan`で設計JSONを生成する。正解表や設計JSONは検査対象へアップロードしない。
2. 試験用の組織部門またはグループと、資料所有者・共有ドライブの規則適用範囲の一致を確認する。サービスアカウント所有のマイドライブを組織利用者の試験と混同しない。
3. 管理コンソールのデータ保護で独自検知器を作成する。経路・画面の名称は公式の[独自検知器の説明](https://knowledge.workspace.google.com/admin/security/custom-content-detectors)を参照する。
4. 下表のとおり設計JSONから入力する。各画面の入力前・保存後・再表示時を保存し、設定値と照合する。APIで読み戻せた場合も全文を私有領域へ保存する。

| 設計JSONの項目 | 入力先と意味 | 確認すること |
|---|---|---|
| `custom_detectors`のキー | 検知器名。`v3-項目ID`を試験用の接頭辞と組み合わせる | 既存検知器と区別できる名前 |
| `custom_detectors`の値 | 正規表現。指定した文字の並びを検出する条件 | JSONのエスケープを展開した文字列を入力。1,000文字以内。RE2の構文確認はローカルで行う |
| `word_lists`の値 | 語句一覧。病名の対照試験に使う語 | 大文字小文字・記号の扱いと単語全体一致の仕様に注意。部分一致を仮定しない |
| `labels[].label` | グループごとの分類ラベル | 正解を表すラベルと、DLPが出力するラベルを分ける |
| `labels[].field` | 単一選択の選択肢型フィールド「検知」 | 複数選択のフィールドにしない |
| `labels[].options` | 「確度高」「確度中」の順 | 同一フィールドで競合した場合に上位の値が選ばれる。名前自体は校正された確率を意味しない |
| `rules[].conditions_or` | いずれかの検知器が一致する条件 | 「標準検知器なし」は説明用の仮置きで、実際の条件として入力しない |
| `rules[].action` | 対応ラベル・フィールド・選択肢の指定 | 既存資料の共有制限は追加せず、計画された出力ラベルだけを使用する |

ラベルのAPI作成要求は`label-plan`の`drive_labels_api_create_plan`で確認できる。単一選択にするため、`selectionOptions.listOptions`は付けない。公式の[SelectionOptionsの型定義](https://developers.google.com/workspace/drive/labels/reference/rest/v2/labels#SelectionOptions)では、この値があると複数値のフィールドを表す。作成処理は実行していない。

ラベルの公開と利用権限も確認する。ラベルの作成だけではDLPが値を付けるとは限らない。[DLPによるラベル付与の公式説明](https://knowledge.workspace.google.com/admin/security/apply-classification-labels-to-drive-files-automatically-with-dlp-rules)に従い、同じ規則でラベルを条件と動作の両方に使わない。

## 3構成を混ぜない手順

標準のみ・独自のみ・併用の3構成は別々の試験として扱う。同じフォルダーへ置くだけでは規則の適用範囲は分かれない。構成ごとの適用範囲と有効な規則を確認し、別の試験資料・期間・出力ラベルまたは適用主体で結果の混在を避ける。過去に付いたラベルが次の構成の結果に混ざる再利用は避ける。

`label-plan`の14本はラベル出力用の設計枠であり、31項目の検知精度を測る全規則を意味しない。項目別の肯定・否定・先頭・末尾の対照規則、閾値、設定読み戻しと観測窓を別途定義する必要がある。ラベルの付与だけではどの項目を検出したかは分からない。

## 最初に行う日本語語句一覧の対照試験

本試験の前に、小さい独立した試験規則で一致方法を確認する。以下は本番の評価値へ合わせ込むための資料ではなく、語境界の扱いを識別する専用資料である。

- 語句一覧は、病名1語「糖尿病」だけにする。
- 比較用の独自正規表現は`糖尿病`とする。
- 2本の規則の適用範囲・対象本文・動作を揃え、監査のみとする。
- 各資料に固有の先頭・末尾対照語を付け、他の病名・分類語を入れない。

| 専用資料の本文 | 調べたい違い | 判定の扱い |
|---|---|---|
| `糖尿病` | 単独の語 | 語句一覧と正規表現の基本対照 |
| ` 糖尿病 ` | 前後が空白 | 空白が語境界として働くか |
| `診断は糖尿病です` | 日本語の文中 | 空白なしの部分一致の有無 |
| `前糖尿病後` | 前後に日本語の文字が連続 | 語全体一致と単なる部分一致の区別 |
| `糖尿` | 語の一部だけ | 一致しない対照 |
| `糖 尿 病` | 語の内部に空白 | 正規化の違い。陽性と決め付けず独立の観測項目にする |
| `病名なし` | 対象語を含まない | 誤反応の対照 |

ログ未出現は未検査・処理待ちと区別する。正規表現側が検知しただけでは語句一覧側の検査完了を証明できない。各規則の肯定・否定と先頭・末尾の対照記録、ファイルの版、前後の規則設定を確認して結果を記録する。日本語の文中で検知した事実があっても、すべての日本語の語境界で同じ動作をすると一般化しない。

この専用対照試験は未実施。語句一覧と正規表現のどちらかへ本試験の条件を変更する場合は、新しい設定版・新しい観測窓として扱う。同じ評価資料を見ながらの調整結果を独立した精度として報告しない。

## 再検査の観測

DLP内部で文書を2回検査する場合があることと、検証側で複数回観測することは別である。内部の1回目・2回目の詳細な判定処理や両者の同一性は、確認した[公式説明](https://knowledge.workspace.google.com/admin/security/about-dlp-for-drive)に記載されていない。異なる可能性は仮説にとどめる。監査上の2イベントを内部の2回の検査と断定しない。

公開仕様の確認（2026年11月17日）：規則監査の `scan_type` は検査モードを表す。`DRIVE_ONLINE_SCAN` は変更された単一のDrive項目に対する評価、`DRIVE_OFFLINE_SCAN` は更新された規則をDrive項目全体へ評価するモードである。この区分から内部の検査回数、1回目・2回目の判定処理、全対象の完了は分からない。値がない記録は不明として残す。[規則監査イベントの公式仕様](https://developers.google.com/workspace/admin/reports/v1/appendix/activity/rules)

少数資料の観測では、`eventName=content_matched` と `filters=resource_id==<FILE_ID>` でファイル単位の取得を設計できる。ページを最後まで取得し、返却された全イベントの種類・ファイル識別子・顧客・時刻を照合する。不正な絞り込み条件は無視される場合があるため、記録がある既知の対照で絞り込みを確認する。空の結果だけでは条件の有効性や陰性を証明できない。これは公開仕様に基づく観測設計であり、既存の採点処理を変更するものではない。[activities.listの公式仕様](https://developers.google.com/workspace/admin/reports/reference/rest/v1/activities/list)
