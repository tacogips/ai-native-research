# 拡張版（v3）の検知試験資料

要配慮個人情報、在留カード・保険証・基礎年金等の番号、資産・年収・勤務先・家族構成、パスワードと一方向変換値を加えた文字資料を作り、独自の正規表現をRE2でローカル検査する。結果と設計は[v3の報告](../../../research/technology/workspace_dlp_v3_extended_detection_report_20261116.md)を参照。

値はすべて独自の架空例。番号の未発行・未割当は保証しない。顔・音声・映像は本文検査の対象外のため生成しない。

| ファイル | 内容 |
|---|---|
| `catalog.py` | 31項目、8グループ、標準検知器の対応、独自正規表現・語句一覧、公開上限 |
| `samples.py` | 陽性の値と文、項目固有の陰性・判断保留の例 |
| `build.py` | 生成（`make`）、ローカル検査（`evaluate`）、分類ラベル計画（`label-plan`） |
| `labels.py` | ラベルの読取専用取得と現在状態の照合 |
| `evaluation.py` | 証拠照合済み観測の31項目×3構成の内部集計 |
| `audit.py` | 原票と規則・検知器の照合、再導出による採点、複数構成の結合 |
| `upload.py` | TXTの新規作成計画と明示実行。途中結果を非公開に保存 |
| `SETUP.md` | 管理画面の入力・読み戻し、日本語語句一覧の対照試験手順 |
| `test_extended.py` | 上限、RE2でのコンパイル、生成の再現性、ラベル計画の形式 |

RE2と同じ動作を得るため、検査には`google-re2`が必要。入っていなければ`evaluate`は実行を拒否する。

```sh
uv venv --python 3.12 /任意の場所/re2venv
uv pip install --python /任意の場所/re2venv/bin/python google-re2
PY=/任意の場所/re2venv/bin/python
$PY scripts/workspace_dlp_benchmark/extended/build.py make --output artifacts/workspace-dlp-v3/truth-r2/dataset
$PY scripts/workspace_dlp_benchmark/extended/build.py evaluate --dataset artifacts/workspace-dlp-v3/truth-r2/dataset --report artifacts/workspace-dlp-v3/truth-r2/report.json
$PY scripts/workspace_dlp_benchmark/extended/build.py label-plan --output artifacts/workspace-dlp-v3/truth-r2/label_plan.json
$PY -m unittest discover -s scripts/workspace_dlp_benchmark/extended -p 'test_*.py'
```

`evaluate`が測るのは独自正規表現だけで、Workspaceの標準検知器・語句一覧・ラベル付与の実際の動作ではない。実環境の結果は公開リポジトリへ保存しない。

## 同じデータセットを再生成する

**現行v3は、生成物を配布しなくても、このリポジトリのコードからファイル名・配置・本文・正解表をバイト単位で再生成できる。** 比較対象は`v3-extended`・正解版`r2`のローカル生成物。Google上のファイルID・所有者・ラベル・監査記録・検知結果は含まず、再生成できることから検知結果の再現を保証しない。過去の私有保存物との同一性も、この公開基準だけでは証明しない。

生成だけならPython標準機能で動き、RE2・Google認証・フォント・通信は不要。Python 3.12を推奨する。リポジトリのルートから次を実行する。

```sh
python3 scripts/workspace_dlp_benchmark/extended/reproduce.py make \
  --output /任意の新しい保存先/workspace-dlp-v3-r2
# 後から同じ生成物を再確認する場合
python3 scripts/workspace_dlp_benchmark/extended/reproduce.py verify \
  --dataset /任意の保存先/workspace-dlp-v3-r2
```

`make`は新規生成後に固定基準と照合する。既存ディレクトリへの上書きは拒否する。基準不一致時は終了コードが非ゼロになるが、調査用の生成物は残す。`verify`は読取りだけで、ファイルの追加・欠落・バイト差・空ディレクトリの差・生成元の変更を拒否する。シンボリックリンクも拒否する。

```text
workspace-dlp-v3-r2/                    # 保存先の名前は任意
├── drive_upload/                       # Driveへ置くのはこの中のTXTだけ
│   ├── <項目ID>-heading-<1〜3>.txt      # 見出し付き陽性
│   ├── <項目ID>-sentence-<1〜3>.txt     # 文中の陽性
│   ├── <項目ID>-table-<1〜3>.txt        # タブ区切り表の陽性
│   ├── <項目ID>-shared_empty.txt       # 共通の空欄
│   ├── <項目ID>-shared_masked.txt      # 共通の伏字
│   └── <項目ID>-<個別の対照名>.txt      # 項目固有の陰性・判断保留
├── ground_truth.json                   # 385資料×31項目の正解と資料のSHA-256
└── generation.json                     # データセット版・正解版・件数・分類
```

合計387ファイル（TXT385＋JSON2）、サブディレクトリ1。開発93資料・評価292資料で、G1〜G7に資料がありG8は対象外。実際の全387相対パス・サイズ・SHA-256（内容の一致を調べる検査値）は[`dataset-reference.json`](dataset-reference.json)に収録する。ファイル時刻・所有者・権限・ZIPの圧縮結果は比較しない。文字はUTF-8、改行はOSによらずLFに固定する。生成元と基準も`.gitattributes`でLFの取得を指定する。乱数や現在時刻を使わず、対照文字列も資料IDから導出する。`PYTHONHASHSEED`の違いでも出力を変えない。

生成元は`build.py`・`catalog.py`・`samples.py`・`../dataset.py`。`reproduce.py`自身を含む5ファイルの検査値も固定基準に保存する。生成物や実アカウント情報の代わりに、これらのコードと基準を版管理する。**未追跡のままでは別環境へ複製されないため、再現用の変更一式がコミットに含まれる必要がある。**

正解表には資料ID、ファイル名、主項目、分類グループ、変種、値ID、開発／評価の区分、主項目の正解、全項目の正解行列、先頭・末尾の対照文字列、TXTの検査値を記録する。判断保留は`null`のまま保存する。ラベル計画とRE2評価報告は別コマンドの追加出力なので、この387ファイルへ混ぜない。

生成仕様を意図して更新したときだけ、新しい基準を別パスへ出力し、本文・正解の差分を確認して採用する。旧版を再現する場合は、コードと基準を同じコミットへ戻す。

```sh
python3 scripts/workspace_dlp_benchmark/extended/reproduce.py record \
  --dataset /新仕様で生成した保存先 \
  --output /新しい保存先/dataset-reference.next.json
```

基準の自動更新はしない。新しい基準を生成できたこと自体は正解の妥当性を証明しない。生成器と基準の変更は同時にレビューする。検査用の模擬資料だけから基準を作り、実環境で取得した情報を基準に混ぜない。

## ラベルの読取りと正解との照合

`labels.py`はDrive APIの読取専用処理。既定では認証も通信も行わず計画だけを表示する。`--execute`を付けるときだけ、利用者が明示した認証で`files.get`と`files.listLabels`を呼ぶ。ラベル・本文・共有権限は変更しない。必要なOAuthの許可範囲は`drive.metadata.readonly`。Drive Labels APIで定義自体を読む許可とは別である。

対応表はリポジトリ外のJSONに保存する。形式は次のとおり。`files`は生成した正解表の資料IDと実際のファイルIDの対応。`groups`はG1〜G7すべてについて設定する。IDは表示名ではなくAPIから確認した識別子を使う。

```json
{
  "schema_version": 1,
  "configuration": "combined",
  "files": [{"case_id": "生成資料のID", "file_id": "DriveのファイルID"}],
  "groups": {
    "G1": {"label_id": "ラベルID", "field_id": "フィールドID", "selection_ids": ["確度高の選択肢ID", "確度中の選択肢ID"]}
  }
}
```

上記は構造を示す抜粋で、実行用にはG2〜G7も必要。構成は`standard`（標準のみ）、`custom`（独自のみ）、`combined`（併用）のいずれか。各構成の試験で実際に使用したラベルを対応付け、別々に観測する。構成名の指定だけで既存規則が切り替わるわけではない。

```sh
# 計画だけ。認証・通信なし。
$PY scripts/workspace_dlp_benchmark/extended/labels.py --mapping /非公開の場所/labels-mapping.json
# 明示的な実環境実行の承認後だけ使用。今回のローカル検証では実行しない。
$PY scripts/workspace_dlp_benchmark/extended/labels.py --mapping /非公開の場所/labels-mapping.json --dataset artifacts/workspace-dlp-v3/truth-r2/dataset --execute --output /非公開の場所/labels-snapshot.json
# 保存した観測をオフラインで照合。
$PY scripts/workspace_dlp_benchmark/extended/labels.py --mapping /非公開の場所/labels-mapping.json --dataset artifacts/workspace-dlp-v3/truth-r2/dataset --snapshot /非公開の場所/labels-snapshot.json --output /非公開の場所/labels-report.json
```

実行時・オフライン照合時ともに、正解表のSHA-256と実際のTXTを照合してからMD5を導出し、読取りの対応表へ結び付ける。取得前後のDriveの`md5Checksum`・`mimeType`も確認し、観測前に編集済みの資料や別形式を旧正解へ照合しない。MD5が欠ける場合は判定不能とする。全ページを読み、前後のファイル版が違えば`stale`（版が変わったため判定保留）にする。取得失敗、ページ継続の異常、未知の選択肢、重複ラベル、ゴミ箱の資料は不在へ変換しない。正解が`None`の項目は主指標から除外し、未観測は`pending`（判定待ち）として保持する。正解表のSHA-256（内容の検査値）を保存し、照合時の差替えを拒否する。

出力の`evaluation_label_snapshot_metrics`は、評価資料のグループ別の**参照可能なラベルの現在状態との一致**である。適合率・再現率・正解率・F1値を含み、`primary_metrics`は判断保留の正解を除外した主指標。未観測が残る場合は主指標を出さない。ラベル不在でも検知状態は`pending`のまま。DLPが検査済みであること、自動付与したこと、すべてのラベルを見る権限があることの証明にはならない。全ページの取得も原子的な一括読取りではないため、ファイル版が同じでも途中でラベルが変わった可能性は残る。

公式仕様：[files.listLabels](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/listLabels)、[Labelのフィールドと選択肢](https://developers.google.com/workspace/drive/api/reference/rest/v3/Label)。

## ローカル再検証と残る作業

生成・RE2評価を独立に再実行し、385資料・評価対象292件と、従来の項目別・グループ別・語句一覧の仮定別の結果の一致を確認した。ローカル評価にも正解率を追加した。分類器は同じ雛形を見て設計したものであり、この一致は未知の資料への性能を保証しない。

ラベル読取りは通信を模擬した単体試験だけを実施した。実アカウントによる読取り・実際のラベル付与・検知・再検査の安定性試験は未実施。31項目×3構成の監査取込みと検知の採点は、保存原票を用いた通信なしの経路を実装・試験した。検知器・規則のAPI作成要求の詳細確認と作成計画は残る。v3用アップロード処理は模擬通信で検証したが、実環境の作成は未実施。日本語語句一覧の対照手順はSETUP.mdに記載したが、実試験は未実施。既存CLIもv3の正解行列を見分けて専用処理へ接続する。実監査の取込み成功は未検証。


## 31項目・3構成の集計処理

`evaluation.py`に、証拠照合済みの観測を受け取る内部関数`reduce_matrix`を追加した。資料×31項目×3構成の全組合せを作り、欠損は`pending`として残す。標準のみ・独自のみ・併用は別々に集計し、併用の実測を他の2構成の結果から推測しない。

`evaluation_by_item`と`evaluation_by_group`は評価用資料だけ、`all_by_item`と`all_by_group`は開発資料も含む診断用。主指標は各集計の`primary_metrics`で、正解が`None`のセルを除外する一方、未観測・非対応・失敗を除外して良い数値を出すことはしない。未決定セルがあれば主指標は`null`。判定済み部分の指標、母数、判定率、上下限は別に残す。

グループは項目の論理和。正解は陽性が1つでもあれば陽性、陽性がなく判断保留があれば保留。観測は検知が1つでもあれば検知、すべての項目で非検知を確認して初めて非検知とする。非対応が残るグループを陰性へ変換しない。G8は資料を生成していない対象外として別記する。

集計関数自体は証拠を検証しない。実行入口は下記の監査取込み・採点を使い、`observations.py`による原票・設定・版・範囲の照合と、採点時の再導出を通す。任意の判定JSONだけを実測として受け入れる入口は設けていない。

[環境準備・管理画面での入力・日本語語句一覧の対照手順](SETUP.md)を追加した。正規表現検知器のAPI内部構造を推測せず、公開仕様で確認できた範囲と保留部分を分けている。


## v3のTXTを新規フォルダーへアップロードする準備

`upload.py`はv3の`ground_truth.json`を読み、内容の検査値を確認したTXTだけを計画する。正解表・生成設定・規則計画と、正解表にない余分なファイルは送らない。既定ではGoogleの認証処理も通信も呼ばない。

```sh
$PY scripts/workspace_dlp_benchmark/extended/upload.py --dataset artifacts/workspace-dlp-v3/truth-r2/dataset
```

実行用の依存は`google-auth`と`google-api-python-client`。実行時は`google.auth.default`でGoogleの既定認証を読み、Drive APIの`drive`スコープを要求する。既定認証がサービスアカウントの場合もあるため、認証成功だけで所有者を推定しない。利用可能なアカウント・認証設定は実行前に確認する。アカウントの切替えや認証情報の新規作成をこの処理からは行わない。

以下は実環境への明示指示を受けてから使用する。今回のローカル検証では実行していない。

```sh
$PY scripts/workspace_dlp_benchmark/extended/upload.py \
  --dataset artifacts/workspace-dlp-v3/truth-r2/dataset \
  --execute --parent 試験用親フォルダーID \
  --scope-evidence /非公開の場所/scope-evidence.json \
  --output /非公開の場所/v3-upload-result.json
```

`scope-evidence`の形式は[既存Drive処理の事前確認仕様](../../pii_image_dataset/README.md#google-drivegoogle-sheets)と共通。72時間以内に確認した規則ごとの適用範囲証跡、作成主体、親フォルダー、マイドライブ／共有ドライブの区別を持つ。共有ドライブにはドライブ自体のIDが必要。証跡は操作者による別途確認を入力とするもので、DLP検査の完了証明ではない。

規則を無効のまま資料を配置し、本文版を確認してから有効化する場合は、v3の`upload.py`に限り`--pre-activation-placement`（有効化前配置）を明示する。既定では証跡の全対象規則が`active: true`であることを要求する。この指定時だけ、`active: false`の対象規則も許可する。規則状態が欠ける場合や文字列・数値の場合は許可しない。証跡を実際に確認した状態のまま保存し、無効な規則を有効と書き換えてはならない。

```sh
$PY scripts/workspace_dlp_benchmark/extended/upload.py \
  --dataset artifacts/workspace-dlp-v3/truth-r2/dataset \
  --parent "$TEST_PARENT_ID" \
  --scope-evidence /非公開の場所/scope-evidence.json \
  --output /非公開の場所/pre-activation-upload.json \
  --pre-activation-placement --execute
```

この指定でも所有者・親・適用範囲・証跡の指紋と鮮度の検査は維持する。報告の`pre_activation_placement`と`rule_activation.rule_states`に用途と証跡上の状態を記録し、全対象規則が有効かを`all_rules_active`に保存する。これは資料配置の完了だけを表す。規則の有効化は行わず、現在のPolicy状態の独立確認、検査完了、検知の陰性判定の根拠にはならない。その後の有効化と有効状態の読戻し、検知・是正の事前確認と採点は別途必要であり、それらの有効状態の要件は緩和しない。

実行処理は現在のDrive利用者と親フォルダーの所有範囲・追加権限を確認してから、新しい試験フォルダーを毎回作る。非委任のサービスアカウントが所有するマイドライブは拒否する。作成したフォルダーとTXTについて、所有範囲・親・試験ID・資料IDを応答で照合し、TXTのMD5（転送された内容の検査値）も照合する。共有権限の追加・取消や、既存資料の更新・削除は呼ばない。ただし親や共有ドライブから権限を継承する可能性があるため、配置先の共有状態は別途確認する。

要求前に処理中の資料名を保存し、応答後には検証前でも返されたIDを記録する。途中で失敗したら停止し、成功済みIDと結果不明の要求を残す。自動再試行・自動削除・自動再開はしない。応答が失われた場合、サーバー上で作成されている可能性があるので、別の出力パスで安易に再実行せず、専用フォルダーと試験IDで実状態を確認する。

実行報告はリポジトリ外かつデータセット外の新規パスに限り、所有者だけが読める権限で保存する。`uploads[].case_id`と`uploads[].metadata.id`は、ラベル読取りの対応表の`case_id`と`file_id`へ対応する。報告はDLP検査結果ではなく、作成・内容・所有範囲の確認記録である。

公式仕様：[files.create](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create)、[Filesの属性](https://developers.google.com/workspace/drive/api/reference/rest/v3/files)。

v3試験63件、既存ベンチマーク144件、共通のDrive処理28件が成功した。通信は模擬した。標準の`python3 -m unittest`でもv3試験を探索するようにし、計207件が成功した（標準PythonではRE2がないため1件省略、RE2入りPython 3.12では省略なしで成功）。Drive処理28件には`xlsxwriter`も必要。一時的なPython 3.12環境で依存を満たして実行した。これらは実環境での作成・検知・ラベル付与の成功を意味しない。


## 監査原票の取込みと、31項目・3構成の採点

すべて保存ファイルを読む処理で、API通信はしない。原票・実行対応表・規則と検知器の読み戻し・適用範囲・観測・報告はリポジトリ外へ置く。実行対応表の基本構造は既存の`observations.py`と共通で、v3では次を追加する。

| 場所 | 必須の追加値と意味 |
|---|---|
| 対応表の最上位 | `benchmark: "v3-extended"` |
| 各`profiles[]` | `benchmark: "v3-extended"`、`kind`は31項目のID、`configuration`は`standard`・`custom`・`combined`、`threshold`は`UNLIKELY`・`POSSIBLE`・`LIKELY`のいずれか |
| `roles` | `positive`・`negative`・`head`・`tail`の4規則。各規則のAPI資源名、全文のSHA-256、更新時刻。対照には語句一覧検知器の資源名と全文のSHA-256も必要 |
| `custom_detectors` | 独自または併用構成では項目の正規表現検知器を1つ。病歴では語句一覧も1つ。各値は`id`・`kind`（`regular_expression`または`word_list`）・`sha256`を持つ。標準のみでは空一覧 |
| 規則の読み戻し | 肯定・否定・対照の条件は`audit.expected_conditions`が導出する式と完全一致。動作は監査のみ。有効状態・顧客・適用範囲・更新版も照合する |
| `files` | 正解表の全資料について、実ファイルID、生成時のSHA-256、先頭・末尾の対照語、契機、前後の本文版・所有範囲・観測時刻を記録する |

`collection`には取得窓・取得時刻・全ページ数・取得完了を記録する。`scope_evidence`には資料×適用範囲の照合証拠、`policy_before`と`policy_after`には窓の前後に保存したポリシー全文を、私有パスとSHA-256で参照する。自由記述の説明だけを根拠に非検知へ確定しない。完全な合成入力の組立例は`test_audit.py`、共通形式は`../test_support.py`にある。いずれも製品の実出力を収録したものではない。

独自検知器は規則と同じ顧客・適用範囲で、保存全文と指紋が一致し、正規表現または語句一覧がv3の定義と一致する必要がある。正規表現の`regularExpression`内部は公開表に具体的な型がないため、読戻しに単一の文字列だけが入る構造に限って照合する。フィールド名は仮定せず、複数値・未知のフラグ等は拒否する。これはAPI作成要求の形式を確定したことや、実出力の内部構造を検証したことを意味しない。合成応答での単体試験だけを実施している。

標準検知器のIDは`audit.STANDARD`に対応候補を固定し、[Policy APIの式の仕様](https://docs.cloud.google.com/identity/docs/concepts/supported-policy-api-settings)と[公開infoType一覧](https://docs.cloud.google.com/sensitive-data-protection/docs/infotypes-reference)を参照する。WorkspaceでそのIDを使った作成成功、日本語対応、製品間の同一性能は仮定しない。履歴書の分類を使う職歴・学歴、医療文脈を使う健診等は直接の項目検知とは異なるため、項目ごとの失敗として分析する。

```sh
# 既存CLIもv3対応表・正解表を見分ける。
$PY scripts/workspace_dlp_benchmark/benchmark.py import-audit \
  --dataset artifacts/workspace-dlp-v3/truth-r2/dataset \
  --raw /非公開の場所/raw-pages.json \
  --manifest /非公開の場所/manifest.json \
  --output /非公開の場所/observations.json
$PY scripts/workspace_dlp_benchmark/benchmark.py score \
  --dataset artifacts/workspace-dlp-v3/truth-r2/dataset \
  --observations /非公開の場所/observations.json \
  --report /非公開の場所/report.json
# 別々に実施した構成の観測は専用入口で結合できる。
$PY scripts/workspace_dlp_benchmark/extended/audit.py score \
  --dataset artifacts/workspace-dlp-v3/truth-r2/dataset \
  --observations /非公開の場所/standard.json /非公開の場所/custom.json /非公開の場所/combined.json \
  --output /非公開の場所/comparison.json
```

`audit.py import-audit`も同じ引数で使える。採点時は保存した原票と対応表から観測を再導出し、手書き変更、正解・資料の差替え、構成の付け替えを拒否する。複数入力の同じ項目・構成・閾値の重複は、都合のよい窓を自動選択せずエラーとする。閾値ごとに別集計し、標準検知器が計画上ない項目は`unsupported`、未取得の規則列は`pending`とする。

この版の原票照合は[公開Rules監査仕様](https://developers.google.com/workspace/admin/reports/v1/appendix/activity/rules)の`rule_match`を対象とし、他のイベント名を自動で同一視しない。実環境が別の監査形式を返す場合は、原票を保全し、公開仕様に基づく別の変換処理と試験を追加するまで未確認にする。


`label-plan`の`drive_labels_api_create_plan`には7ラベルの`labels.create`要求案も含む。管理者用ラベル・単一選択フィールド1つ・選択肢2つの構成とし、複数選択を意味する`selectionOptions.listOptions`は省略する。作成後のラベルID・フィールドID・選択肢IDの読み戻し、ラベルの公開、利用権限の設定は別工程。作成要求の送信処理はなく、この版では実行しない。 `ADMIN`型をAPIで作成・公開する場合は`useAdminAccess=true`、Manage Labels権限、`drive.admin.labels`が必要である。管理者としての読取り専用は`drive.admin.labels.readonly`で、`drive.labels`の利用者アクセスによる`SHARED`型書込みとは異なる。[公式認可仕様](https://developers.google.com/workspace/drive/labels/guides/authorize)。[公式の型定義](https://developers.google.com/workspace/drive/labels/reference/rest/v2/labels#SelectionOptions)を根拠とし、合成した計画をローカル試験で検証した。


## 独立レビュー後の正解表r2

サブエージェントの独立レビューで、本文とラベル観測の内容照合、ラベル主指標での判断保留の除外、跨分類の正解の3点を修正した。[対応記録](REVIEW.md)を参照。

生成する正解表は`truth_revision: "r2"`。初版r1の本文・値・正規表現は変えず、「父が高血圧で通院」の資料で家族関係を陽性にし、障害の陽性9資料で病歴を判断保留にした。全体の正解セル10個を修正し、本文のSHA-256は全385資料で初版と一致する。初版と修正版を別の出力先で保存し、既存結果へ黙って上書きしない。

評価対象は引き続き292資料。家族構成の再現率は1.0000から0.8571、G3の再現率は0.9167から0.8800へ変わった。検知器の改善・悪化ではなく、正解の誤りを訂正した影響である。病歴は評価資料の保留が1から7へ増えた。他のグループの集計は変わらない。旧r1の報告数値とr2の数値を混ぜず、保存する報告の`truth_revision`を確認する。

## 標準検知器の対応表を明示して固定する

既定は`audit.STANDARD`の候補を維持する。実際に確認した別のIDを使う場合は、リポジトリ外のJSONへ対応表を保存し、実行対応表の最上位で次のように参照する。

```json
{"standard_detector_map": {"path": "/非公開の場所/standard-detectors.json", "sha256": "保存ファイルのSHA-256"}}
```

参照先は`schema_version: 1`と`detectors_by_item`を持ち、**全31項目**の一覧を指定する。各項目の値は検知器IDの文字列一覧、計画上非対応なら空一覧とする。以下は構造だけを示す抜粋であり、実行用には残りの項目も必要である。

```json
{"schema_version": 1, "detectors_by_item": {"email": ["SYNTHETIC_EMAIL_DETECTOR"], "assets": []}}
```

入力表の項目欠損・未知項目・重複ID・同名JSONキーの重複・文字列一覧以外の値を拒否する。条件式へ安全に埋め込むため、IDは英数字と`_`、`.`、`/`、`:`、`-`からなる識別子または資源名に限定する。対応表だけでは、入力IDが製品で使えることやその意味が正しいことを証明しない。実際の規則読み戻しとの完全一致も必要である。

原票取込み時に、参照先ファイルのSHA-256と正規化した対応表のSHA-256を観測へ保存する。採点時はファイルを読み直し、観測を再導出して指紋と結び付けを照合する。明示表を使わない場合も、既定候補の正規化した指紋を記録する。この結び付けを持たない旧v3観測は原票から再取込みする。

空一覧の項目は標準構成で`unsupported`、一覧があるのに観測規則がない項目は`pending`とする。異なる対応表を使った観測を同じ比較へ混ぜない。独自のみの観測でも、結合先と同じ対応表を明示しておく。参照先が異なるファイルでも、正規化した表が同一なら結合できる。監査原票のイベント種別の対応範囲は変更していない。

## 先頭・末尾の対照語句を分割する

語句の内容は変えず、同じedge（先頭または末尾）の語句一覧を複数の検知器へ分けられる。各edgeの条件は分割検知器の論理和（いずれか一致）とし、肯定・否定の項目規則では先頭の論理和と末尾の論理和の両方を要求する。PIIを検知する正規表現を変更する機能ではない。

実行対応表の`profiles[].roles.head`と`tail`で、次の`control_detectors`形式を使う。例は参照部分だけの抜粋であり、規則自体の`id`・指紋・更新時刻等の既存項目も必要である。

```json
{
  "head": {
    "control_kind": "word_list",
    "control_detectors": [
      {"id": "policies/SYNTHETIC-HEAD-A", "sha256": "検知器全文のSHA-256"},
      {"id": "policies/SYNTHETIC-HEAD-B", "sha256": "検知器全文のSHA-256"}
    ]
  },
  "tail": {
    "control_kind": "word_list",
    "control_detectors": [
      {"id": "policies/SYNTHETIC-TAIL-A", "sha256": "検知器全文のSHA-256"},
      {"id": "policies/SYNTHETIC-TAIL-B", "sha256": "検知器全文のSHA-256"}
    ]
  }
}
```

旧形式の`detector_id`・`detector_sha256`による単一検知器も引き続き使える。同じedgeで旧形式と新形式を同時指定することは拒否する。先頭だけ分割し、末尾を旧単一形式にすることは可能。単一の条件式は既存形式を維持し、新形式でも検知器が1つなら同じ式になる。

各分割検知器の全文の指紋・型・顧客・適用範囲を照合する。検知器IDの重複、先頭と末尾でのID集合の交差、edge内で分割をまたぐ語句の重複を拒否する。語句一覧が大文字小文字と記号を無視することを踏まえ、その違いだけの語句重複も拒否する。各検知器は1〜950語、UTF-8でカンマ区切りにした内容が60KB以内である必要がある。この実装では既存の対照語条件として1語40文字以内も課す。40文字は対照語に対する実装の条件であり、製品一般の文字数上限の主張ではない。

ファイルごとに、そのファイルの先頭対照語が先頭の分割語句の和集合に、末尾対照語が末尾の和集合に含まれることを照合する。定義の欠落・改変・未知の構造はエラーとして停止する。検知器を分割しただけで検査完了が証明されるわけではなく、非検知への条件付き判定には従来どおり肯定・否定・先頭・末尾の監査記録と、本文版・範囲・設定の照合が必要である。

分割の処理は`../controls.py`で共通化し、監査取込みとv3条件式の導出から利用する。実ID・実測の制限値・監査記録はこの説明や試験コードへ含めない。追加の試験は合成定義と模擬原票だけで実施している。
