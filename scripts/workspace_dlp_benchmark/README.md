# Google Workspace DLPの検知・是正比較試験

公開仕様確認日：2026年11月16日。DLPは機密情報の検知・保護、是正は検知後に共有制限や分類ラベル等を適用して状態を変えることを指す。CLIは端末のコマンド操作、APIはプログラムからの呼出し口を指す。公開仕様と独自の架空資料を使う生成・採点コードを保持する。実アカウント、契約状態、規則の識別子、Drive識別子、認証情報、監査原票、実測値はリポジトリ外に保存する。

旧版の静的レビューと対応状況は[REVIEW.md](REVIEW.md)、公式仕様の再確認・是正の状態遷移表・指標は[レビュー対応と是正試験設計](../../research/technology/workspace_dlp_benchmark_review_response_20261116.md)を参照する。コードの単体試験、生成器の実行、Google実環境での測定は別の証拠であり、互いを完了の代わりにしない。

## 何を比較するか

検知は「資料×全規則×閾値」の行列、是正は「動作×事前共有状態×操作者×契機」の状態遷移として扱う。監査のみの規則を基本の検知比較に使い、共有遮断・警告・取得制限・ラベルの是正試験は専用の資料と観測で別に行う。所有者が手動で権限を取り消した結果をDLPの遮断成功と数えない。

標準検知器の対応表は公開仕様に基づく名称の対応であり、この生成器で検知に成功した一覧ではない。[公式の標準検知器一覧](https://knowledge.workspace.google.com/admin/security/how-to-use-predefined-content-detectors)

| 分類 | 対応付ける標準検知器 | 正解で区別する点 |
|---|---|---|
| メール | Email address | 表現の存在。`example.test`という理由だけで陰性にしない |
| 電話 | Phone number | 電話番号表現と、公開窓口等を保護する方針の違い |
| 日本の旅券番号 | Japan / Passport | 番号形式の表現。発行・未割当・実在性を保証しない |
| 日本の免許証番号 | Japan / Driver's License Number | 形式の試験。公的根拠を確認できない検査数字を正しいと認定しない |
| 日本の個人番号 | Japan / Individual Number | 番号表現、検査数字の妥当性、保護判断を別の正解にする |
| 日本の口座番号 | Japan / Bank Account Number | 銀行文脈付きと、単なる7桁や連番を対にする |
| カード番号 | Credit card number | 表現、有効な検査数字、注文番号等の文脈を区別する |

分類ごとに6値、全7分類で42値を使い、各分類を開発2値・評価4値へ分ける。現行生成器は表記・文脈・形式を展開した738資料を作る。同じ値の文章違い・表記違い・形式変換は独立した人物や独立標本ではない。生成件数は出力の正解表・生成記録で確認し、旧版の固定168ファイルという件数を新しい生成物へ流用しない。小規模な合成資料の結果から実務の低い誤警告率を保証しない。

主指標は基本表記の評価用TXTである。全角、途中改行、ゼロ幅文字等の回避表現は別に集計する。値だけの例、分類名を含む例、見出しのない文章、紛らわしい数字列、検査数字だけを誤らせた例も区別して報告する。検査数字が正しくても、発行済み・実在・決済可能・未割当とは認定しない。

## 生成と、検査前の確認

```sh
python3 scripts/workspace_dlp_benchmark/benchmark.py make \
  --output /リポジトリ外の新しい保存先
```

出力先は新規ディレクトリを使う。`drive_upload`だけを専用の検査先へ配置し、正解表・規則定義・観測・報告を検査範囲へ混ぜない。各資料の先頭と末尾には資料固有の非PIIの対照文字列を置く。HTMLでは可視本文に置く。対照文字列を検知してもPII検知の成功にはしない。

Driveへ配置する前に、次を非公開台帳へ保存して確認する。

1. 実際の認証主体と代理対象、マイドライブの所有者、または共有ドライブの識別子。
2. 所有者または共有ドライブに適用する組織部門・グループと規則範囲。マイドライブと共有ドライブを別の試験群にする。
3. 契約版・管理権限・有効な規則の版・本文の検査範囲・閾値・文字認識の設定。
4. ローカル内容指紋、Driveの現在版、対象ファイルと規則の対応、観測開始・終了時刻。

`google.auth.default`を呼べたことは所有者の適用範囲一致の証明にならない。サービスアカウントの認証方式から組織内所有を推測せず、配置先と実際の主体を確認する。適用主体の根拠は[Drive DLPの公式説明](https://knowledge.workspace.google.com/admin/security/about-dlp-for-drive)、配置と別認証による読取確認は[画像等の生成器README](../pii_image_dataset/README.md)を参照する。

実配置には同生成器の`--scope-evidence`で、実主体・親フォルダー・保存方式・対象規則と、別途取得した適用範囲証拠の指紋を渡す。鮮度上限72時間はこの実装の事前条件であり、製品の検査時間の保証ではない。範囲証拠は操作者が別途確認して作る入力であり、このコードがPolicy APIやDirectory APIから組織部門・グループの適用を独立取得・評価するものではない。指紋の一致は保存後の変更を検出するが、入力の正しさを保証する署名ではない。

## 規則定義と監査原票から再現する

```sh
python3 scripts/workspace_dlp_benchmark/benchmark.py plan-rules \
  --dataset /生成先 --config /非公開保存先/rule-config.json \
  --output /非公開保存先/rule-plan.json

python3 scripts/workspace_dlp_benchmark/benchmark.py apply-rules \
  --plan /非公開保存先/rule-plan.json \
  --output /非公開保存先/rule-run.json
```

`apply-rules`は既定では通信せず計画を確認する。実際の操作は`--execute`を付けた場合だけ行う。実装は試験専用の新規作成に限り、既存規則の更新（PATCH）・削除（DELETE）は未実装として、通信前に拒否する。公式APIに更新・削除があることと、このコマンドで使えることを区別する。専用の命名空間・組織部門を指定し、作成応答だけで完了とせず、非同期操作の完了と設定の読み戻しを照合する。[Policy APIの公式例](https://docs.cloud.google.com/identity/docs/how-to/create-patch-delete-policies)、[対応する規則・検知器・動作](https://docs.cloud.google.com/identity/docs/concepts/supported-policy-api-settings)

同じ計画と実行台帳の並行適用を抑止する。POSTの結果が不明な場合は自動再送せず保留停止するため、出力名や台帳を変えて再作成しない。保存した台帳と実資源を照合してから復旧を判断する。Cloud Identityの公開discoveryにOperation取得専用の定義がないため、返された同サービス内の名前へのGETを使う対応は実API未検証であり、非対応・失敗・期限切れでは停止する。認証トークンは指定環境変数から読むだけで、認証同意・権限付与・代理認証の設定は自動化しない。

設定の形は次のとおり。値は説明用で、実際の顧客・専用組織部門等へ置き換えたJSONをリポジトリ外へ保存する。トークンの値はJSONへ書かず、実行環境の指定した変数へ渡す。`LIKELY`は公式資料で管理画面のHighと対応するが、他の値の表示名をこの例から推定しない。

```json
{
  "customer": "customers/CEXAMPLE",
  "org_unit": "orgUnits/TESTOU",
  "namespace": "DLPTEST-example",
  "thresholds": ["UNLIKELY", "POSSIBLE", "LIKELY"],
  "token_env": "GOOGLE_WORKSPACE_CLI_TOKEN"
}
```

既定は7分類×3閾値の21設定組で、独自語句一覧検知器2個、対照規則2個、各設定組の肯定／否定規則42個、計46資源を計画する。既定の`mode`は`audit`で、すべて監査のみになる。是正規則を作る場合は別計画で`mode: "native_remediation"`と、例として`positive_action: {"blockAccess": {}}`を明示する。この場合も否定・前後対照は監査のみである。他の動作の内部設定は公式形式を確認して渡し、空オブジェクトから利用可能な設定を推測しない。

試験用PII規則に加えて、先頭・末尾の対照規則と、同じPII述語の否定を観測する監査専用規則を用意する。既定の対照には、資料固有の先頭／末尾の文字列をそれぞれ収めた2つの独自語句一覧検知器を使う。公開された`wordList.words`の公式例に基づく経路で、内部構造を確認できない正規表現検知器の作成要求を推測しない。各閾値を事前固定した規則として並走させる。正解用ラベルをPII規則の条件に入れず、出力用ラベルとも別にする。

語句一覧の950語・60KB、語句の連続成分40文字等の公開上限を満たす必要がある。現行の対照文字列は39文字だが、旧版の長い対照を持つ生成物をそのまま新しい規則計画へ渡さない。規則・検知器の組織全体の既存件数も含めて容量を確認する。上限超過では自動作成を止め、操作者が別の計画を作る。分割前後を同じ設定の同時比較と偽らない。[内容と規則の容量上限](https://knowledge.workspace.google.com/admin/security/view-dlp-content-and-rule-size-limits)

```sh
python3 scripts/workspace_dlp_benchmark/benchmark.py import-audit \
  --dataset /生成先 --raw /非公開保存先/reports.json \
  --manifest /非公開保存先/observation-manifest.json \
  --output /非公開保存先/observations.json
```

原票はReports APIの規則監査を全ページ取得したJSON、または1行ごとにJSONを保存するNDJSONを使い、取得期間・完全性・対象識別子を非公開の対応表で渡す。`applicationName=rules`にはDLP以外もあるため、対象規則とファイルを照合する。名前だけで結ばず、ファイルID・規則IDと版・内容の版・適用範囲・期間を確認する。重複イベントを複数標本に数えない。[Rules監査API](https://developers.google.com/workspace/admin/reports/v1/appendix/activity/rules)

対応表は`schema_version: 2`で、少なくとも次を持つ。完全な合成例は[test_support.py](test_support.py)の`AuditFixture`と[test_observations.py](test_observations.py)を参照する。任意の自由文を埋める入力書式ではない。

| 対応表の項目 | 必要な内容 |
|---|---|
| `customer_id`、`collection` | 顧客、取得対象の開始・終了・取得時刻、全ページ取得の確認とページ数 |
| `profiles` | 分類・閾値と、肯定／否定／先頭／末尾の規則・検知器ID、読み戻した全文の指紋と更新版 |
| `files` | 資料IDとDrive ID、内容指紋・版、所有者または共有ドライブ、前後状態と観測時刻、作成／編集／規則変更の契機 |
| `scope_evidence`、`policy_before`、`policy_after` | リポジトリ外のJSONの`path`と`sha256`。対象への適用と規則全文を前後で照合する |

採点時も、保存した原票と対応表の指紋を確認して観測を再導出し、保存行との完全一致を検証する。手で`not_detected`に変更した行、古い自由文の`evidence`だけの判定済み行は拒否する。

### 未検知と未検査を混ぜない

`detected`は対象分類の検知、`not_detected`は必要な条件付き観測証拠を満たす非検知、`pending`は未判定である。`unsupported`（非対応）、`error`（取得等の失敗）、`timeout`（観測期限切れ）も陰性へ変換しない。

先頭・末尾の別対照規則だけに記録がある場合は `conditional_not_detected` として保留に残す。その対照の成功は、全PII規則が同じ内部走査で本文全体を検査した直接証明ではない。主指標の `not_detected` には、同じPII述語の否定規則の一致も必要とし、ファイル版・対象PII規則の版・適用範囲・時刻と対照を機械照合する。人が書いた自由文の`evidence`や、ログ不在だけでは採点を確定しない。この条件を揃えても内部走査版の完全性を直接取得したことにはならない。

規則変更の反映時間と、ファイルの走査完了・記録の到着は別に測る。最大24時間という規則変更の案内を全件走査の完了保証にしない。[規則の保守](https://knowledge.workspace.google.com/admin/security/maintain-data-protection-rules)、[走査時間](https://knowledge.workspace.google.com/admin/security/about-dlp-for-drive)

## 検知の採点

```sh
python3 scripts/workspace_dlp_benchmark/benchmark.py score \
  --dataset /生成先 --observations /非公開保存先/observations.json \
  --axis content --report /非公開保存先/metrics.json
```

`--axis content`は型の表現、`protection`は保護方針、`valid_number`は有効番号の正解を使う。検査数字が無効な番号表現や、同じ数字を使う商品番号を、定義なしに一つの陰性へまとめない。正解が不明な項目を0に補完しない。

| 指標 | 定義 |
|---|---|
| 適合率（precision） | TP / (TP + FP) |
| 再現率（recall） | TP / (TP + FN) |
| 正解率（accuracy） | (TP + TN) / (TP + FP + FN + TN) |
| F1値 | 2TP / (2TP + FP + FN) |
| 偽陽性率 | FP / (FP + TN) |
| 判定済み割合 | (TP + FP + FN + TN) / 対象の全試験数 |

全件の点推定は未判定や採点不能が残ると`null`にし、判定済み部分の値と、未判定を含む範囲を別に出す。

TPは正しい検知、FPは誤検知、FNは見逃し、TNは正しい非検知。分母0は`null`（算出不能）とする。未検査を除いた部分の指標を全件の精度へ拡大しない。基本／回避、分類、閾値、形式、開発／評価を別に出し、他分類への反応を行列で残す。位置を返さない製品のファイル単位の警告から、箇所別の完全回収率を推定しない。

## 画像・Office・PDF等の拡張正解

[画像等の生成器](../pii_image_dataset/README.md)の`ground_truth/files.json`を比較するときは、`--truth-profile`で製品分類との明示的な対応表を渡す。人物名を検知しただけで病歴や口座の検知成功にしない。位置・値・人物への対応のうち、製品から実際に観測できる単位だけを採点し、対応できない正解は不明のまま残す。

この正解読込の対応だけで、既存の画像・Office・PDF等へ先頭／末尾の検査対照が追加されるわけではない。検査面と版を確認できる対照を持たない拡張資料は、未検知を主指標の陰性へ確定できない。画像では可視面、複数ページでは検査したい各面に対照を配置した資料を別に準備し、本文を読めない暗号化資料のメタデータ一致を本文検査の証明にしない。`plan-rules`へ渡す資料は対照文字列等の必要な正解項目を満たす必要があり、正解の形式対応だけで全形式の自動試験を完了したとは扱わない。

```sh
python3 scripts/workspace_dlp_benchmark/benchmark.py score \
  --dataset /画像等の生成先 --truth-profile /非公開保存先/truth-profile.json \
  --observations /非公開保存先/observations.json \
  --axis content --report /非公開保存先/expanded-metrics.json
```

文字認識の設定・通常画像／画像PDF・暗号化等を区別する。読めなかった資料、コメント等の非対応面、上限超過を陰性のTNにしない。[対象面の公開説明](https://knowledge.workspace.google.com/admin/security/about-dlp-for-drive)

## 是正の計画と採点

```sh
python3 scripts/workspace_dlp_benchmark/benchmark.py plan-remediation \
  --output /非公開保存先/remediation-plan.json \
  --config /非公開保存先/remediation-expectations.json

python3 scripts/workspace_dlp_benchmark/benchmark.py score-remediation \
  --plan /非公開保存先/remediation-plan.json \
  --observations /非公開保存先/remediation-observations.json \
  --report /非公開保存先/remediation-metrics.json
```

是正計画は4動作×5共有状態×3操作者×3契機の180基本行と、解除・迂回・競合等12行、過剰適用4行、計196行である。契約上の利用可能性や実行権限まで確認した196件ではなく、未対応を含む事前の一覧である。共有遮断・警告・取得制限・ラベル、既存の外部共有、本文修復後・規則解除後の状態、競合、過剰遮断、コピーや別経路を列挙する。具体的な組合せと測る時刻は[状態遷移表R01～R14](../../research/technology/workspace_dlp_benchmark_review_response_20261116.md#是正の状態遷移表)を参照する。計画の生成と採点だけで、実際に規則や権限を変更するものではない。

`--config`の`bindings`はケースIDをキーに、`expected_action_fragment`（監査で確認する動作の構造）、`expected_label`（分類ラベルID・選択肢値）、`removed_values`（除去対象の値）等を実行前に固定する。コマンド生成だけなら省略できるが、動作の期待値を固定していない行は成功にできない。観測側の期待値で事後上書きしない。既定の期待結果を逆の値へ変更する設定は拒否し、未定義の迂回・競合は対応する許可値を事前固定する。構造の参考は[test_remediation.py](test_remediation.py)の合成例で、そこにある動作表現は試験用の対応値であり、実APIの応答を観測した例ではない。

是正観測は、計画の共有状態・操作者・契機と証拠を結ぶ`case_context`も参照する。ここでは完全な事前権限一覧とドライブ種別から共有状態を、所有者・権限と操作記録の主体から役割を照合し、ケース名や自己申告の因子だけで判定しない。現行の契機対応は`source: "synthetic_fixture"`の合成証拠だけで、実際の作成・編集・規則変更を取得して照合する接続処理は未実装である。合成の成功は計算処理の検証として分離し、製品の実測成功率へ合算しない。実証拠を結ぶ処理がない経路は`pending`になる。この自己申告形式は署名による出所保証ではない。

是正観測は計画の`plan_sha256`、`organization_domains`とケースごとの観測を持つ。各観測はファイル・規則・顧客・規則更新版、是正主体、外部認証主体、経路、契機・締切時刻を結び、`scope_evidence`、`policy_readbacks`、`baseline_control`、`probe_report`、`audit`を外部JSONのパスと指紋で参照する。警告とラベルには`state_readback`も必要で、任意の文字列タグや`appProperties`を分類ラベルの代わりにしない。無動作の陰性を確定するには、同顧客・資料版・条件・範囲の`not_detected`を原票から再導出できる`evaluation_confirmation`が必要になる。自由文だけの観測では採点できない。

対象資料が是正前には読めたことを、所有者と異なる外部認証で確認する。是正後は、その認証での実読取・権限一覧・対象版・動作の記録を組にする。403や404だけでは認証・設定・存在・保護のどれが原因か決められない。対象外の対照も同じ認証で確認し、単なる所有者の手動権限取消を標準DLPの成功にしない。

新規作成は、現行の「対象自身の契機前の状態記録」という前提と両立しないため、実証拠・合成証拠とも`pending`にする。作成専用の共有状態・操作を照合する処理は未実装である。新規共有が最初から拒否され、対象自体が読めた記録がない場合も、別資料の対照が読めるだけでは遮断遷移の成功にせず保留にする。製品の失敗という判定ではない。`action_complete`に規則更新版が返らない場合は、前後の同一Policy読み戻しによる条件付きの結合を`version_binding: "policy_readback_bracket"`と明示する。内部で評価した版を直接観測した保証ではない。版が返って異なる記録は使わない。

解除には、元の動作記録と事前拒否、解除操作の`change_evidence`、解除後の可読を使う。本文修復は事前固定値が旧版本文にあり現版から消えたこと、無効化はACTIVE→INACTIVEの更新、削除は完全な規則一覧からの消失をそれぞれ照合する。本文証拠は保存したUTF-8本文等の条件付き観測であり、任意の画像やOfficeから本文を自動抽出して全PIIの不存在を保証する実装ではない。

合成証拠の判定済み成功率は`by_evidence_domain.synthetic`に分ける。現在の`full_plan_success_rate`と`product_measured_success_rate`は実収集の接続がないため`null`であり、合成の成功を製品の成功率として出さない。出力は全計画の判定割合、残存した潜在的な外部権限数、過剰適用率、露出と解除の時間区間を分ける。未実行・非対応は分母から落として全件成功率を作らない。`exposure_interval`は最後の可読～拒否、`release_interval`は拒否～可読の区間で、再露出・再拒否と観測期限での打切りも残す。正確な発効時刻・連続監視の保証ではない。権限数はグループ等の所属を解決した実アクセス可能人数ではない。

現在の外部アクセス収集器はSheetsの本文読取だけで、ダウンロード・印刷・コピーの実行は収集しない。取得制限を採点するには、事前計画と一致する役割の本人による操作別の証拠を別途用意する。警告と分類ラベルの状態も別の読み戻しが必要である。自作権限取消の実行と証拠の接続は未実装で`unsupported`、迂回・競合の期待状態が未固定の行は`pending`に残す。作成者への通知到達の自動収集も未実装である。

## 実行・検証範囲

2026年11月16日にローカルで次を確認した。Googleへの実API通信は行っていない。

| 確認 | 結果 |
|---|---|
| `unittest`による比較試験コード | 144件成功。是正の独立試験51件を含む |
| Drive配置・外部読取の単体試験 | 28件成功。Google呼出しは模擬処理 |
| 別プロセスによるCLIの生成・計画 | 738資料・42値、規則計画46資源・21設定組、是正計画196行 |
| `apply-rules`の既定実行 | 通信0、`dry_run` |

```sh
python3 -m unittest discover -s scripts/workspace_dlp_benchmark -p 'test_*.py'
# 画像生成器READMEの実行方法でrequirements-all.txtを導入した環境を使う
.venv/bin/python -m unittest discover -s scripts/pii_image_dataset -p test_google_drive.py
```

ローカルの生成・証拠検証・採点は単体試験で確かめる。CLIの手順と試験結果は元の静的レビューと分けて[REVIEW.md](REVIEW.md)へ記録する。実環境の設定・共有操作・別アカウント読取・契機ごとの遅延測定は、必要な権限と専用範囲を用意したうえで行う別工程である。この公開コードと文書はGoogle実環境での測定済みを意味しない。

## 事例調査の改善案の検証

文脈で補う検知規則（v4-context）と、提案・確定を分けた是正フローのモデル計算は[improvement/](improvement/README.md)に置く。結果は[改善案の検証](../../research/technology/dlp_case_study_improvements_verification_20261118.md)を参照。標準の`unittest`探索は`test_improvement_suite.py`経由でこの試験も実行する。

## データセットの版と再現手順

7分類・738資料の本生成器、[31項目・385資料のv3](extended/README.md#同じデータセットを再生成する)、[画像・Office等のLIGHT](../pii_image_dataset/README.md#再現性の範囲と保存する条件)は別々の生成物で、件数や正解形式を混ぜない。v3には全ファイルの相対パス・バイト数・SHA-256を保存した固定基準と、生成後に照合する`reproduce.py`を用意した。738資料版とLIGHTへ同じバイト一致の保証を拡張するものではない。

## 業務番号の対照試験

社員番号・契約番号は組織ごとに形式が異なる。入力データはすべて合成し、同じ値を社員番号・契約番号・注文番号・請求番号として使い回す。8種類の表記を48系列に割り当て、定型見出し、別名、表、台帳名だけ、改行を挟んだ値、入力例、別種類の番号との混在、在庫番号を含めた。番号種別は、生成時の台帳上の役割で注釈する。入力例の番号はどの台帳にも割り当てられていない想定とする。

1,536資料のうち、正解が確定した1,440資料を各検知器で評価する。社員番号・契約番号の陽性は各336資料。両方を含む48資料は「社員または契約を含むファイル」の集計では1件と数える。番号だけの96資料は、同じ本文で台帳上の出自だけ異なる48組で、主指標から除外する。ファイル名も正解の手掛かりにならない識別子を使う。この設計で測るのは選んだ条件での反応であり、本番の形式の分布や陽性率は測っていない。値を共有する派生を互いに独立した標本とは扱わない。

```sh
run_dir=/任意の場所/業務番号検証
mkdir "$run_dir"
python3 scripts/workspace_dlp_benchmark/identifier_benchmark.py make --output "$run_dir/dataset"
uv run --no-project --python 3.12 --with google-re2 python \
  scripts/workspace_dlp_benchmark/identifier_benchmark.py evaluate \
  --dataset "$run_dir/dataset" --report "$run_dir/report.json"
```

検査対象は `dataset/drive_upload/*.txt`。正解表は `dataset/ground_truth.json` に生成される。評価器は固定の正解表と各本文のSHA-256を照合する。旧式を読み戻せた場合は `--rules` に `構成名 → employee / contract / order / invoice → 正規表現` のJSONを指定して比較できる。この方法が検査するのは本文に対するRE2の1回以上の一致。Workspaceの標準検知、本文の抽出、語句一覧、ラベル付与、監査ログは測っていない。

| ファイルの正解 | 比較用の固定式 | TP | TN | FP | FN | 適合率 | 再現率 | 正解率 | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 社員番号、契約番号（各分類） | 番号形式のみ | 252 | 276 | 828 | 84 | 23.33% | 75.00% | 36.67% | 35.59% |
| 社員番号、契約番号（各分類） | 定型見出し＋番号形式 | 108 | 1,068 | 36 | 228 | 75.00% | 32.14% | 81.67% | 45.00% |
| 社員番号または契約番号 | 番号形式のみ | 468 | 204 | 612 | 156 | 43.33% | 75.00% | 46.67% | 54.93% |
| 社員番号または契約番号 | 定型見出し＋番号形式 | 180 | 744 | 72 | 444 | 71.43% | 28.85% | 64.17% | 41.10% |

番号形式だけの式は他の業務番号にも反応した。定型見出しを求める式は誤検知を減らした一方、別名・表・離れた行にある社員番号を見逃し、見出し付きの入力例にも反応した。文脈のない対では、本文だけを見る決定的な分類器は、一対の両方に正解できない。この対の50%は構成上の結果で、運用時の精度推定値ではない。

Workspaceで再試験する際は、標準検知器の可能性のしきい値と、独自正規表現の最小一致回数を区別する。[設定の記録方法としきい値別の試験計画](../../research/technology/workspace_dlp_benchmark_review_response_20261116.md#業務番号の検知結果に設定条件を併記する)
