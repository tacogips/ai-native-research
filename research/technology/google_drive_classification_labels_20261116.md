# Google Driveの分類ラベルとフィールドの仕様と運用上の論点

調査日：2026年11月16日。分類ラベル（classification labels）は、管理者が定義し、Driveのファイルへ付ける分類用の属性情報を指す。フィールドはラベルの中の個々の入力項目、DLPは機密情報の検知・保護を指す。

公開の公式資料だけを根拠とする。組織の設定、ラベルの識別子、監査記録、実測値は掲載しない。以下は仕様の確認であり、実環境での動作は検証していない。管理ヘルプの各ページは2026年11月10日更新の版を参照した。

**運用判断に効く要点：** 1ファイルに付けるラベル数に上限はないが、組織で作れるラベルは150個まで。DLP規則で条件・動作に使えるのは単一選択の選択肢型フィールドだけで、同じ規則でラベルを条件と動作の両方には使えない。ファイル上の値はフィールド単位でAPIから変更でき、付与にはファイルの編集権限とラベルの適用権限の両方が要る。[K1–K3,D2,D3]

## ラベルとフィールドとは

ラベルは「機密区分」「契約書」のような分類の単位で、ファイル本文とは別にDriveが保持する。ダウンロードした複製には付いていかない（Drive上の属性であるため。複製への非継承を明記した資料は今回確認していない）。用途は検索の絞り込み、DLP規則の条件と動作、既定の分類などである。[K1,K2]

フィールドはラベル内の入力項目で、ラベルを帳票とすると記入欄に当たる。フィールドなしのラベルも作れ、その場合は付いているかどうかだけの目印になる。[D3]

| 種類 | 定義 | 制約 |
|---|---|---|
| バッジ付きラベル | 色分けできる選択肢を持つ選択型フィールドを含むラベル | 1ラベルにバッジ付きフィールドは1つまで。バッジ付きラベル自体は組織で複数作れる [D3,K2] |
| 標準ラベル | 0個以上のフィールドを持つラベル | 下表の上限に従う [D3] |

| フィールドの型 | 管理画面での名称 | 上限 |
|---|---|---|
| 選択肢（単一選択） | Options list | 選択肢200個 [K2] |
| 選択肢（複数選択） | Options list（複数選択を許可） | 選択肢200個、選べる値は10個まで [K2] |
| バッジ | Badge list | 1ラベルに1つ、選択肢200個 [K2] |
| 文字 | Text | 100文字まで [K2] |
| 数値 | Number | 記載を確認していない |
| 日付 | Date | 記載を確認していない |
| 利用者 | Person | 複数選択を許可した場合10人まで [K2] |

## 数の上限

| 項目 | 上限 | 出典 |
|---|---|---|
| 組織で作れるラベル数 | 150（バッジ付きラベルを含む） | [K1,K2] |
| 1ラベル当たりのフィールド数 | 10 | [K2] |
| 1ファイルに付けられるラベル数（Drive） | 上限なし | [K1] |
| 1通のメールに付けられるラベル数（Gmail） | 20 | [K1] |
| 1ファイルに付けられるバッジ付きラベル数 | 記載なし | — |

1つのラベルに複数のフィールドをまとめる理由は、主に二つある。第一に、組織全体のラベル数が150個に限られるため、属性ごとにラベルを作ると枯渇しやすい。第二に、公開・無効化・閲覧や付与の権限はラベル単位で設定するため、関連する属性をまとめれば管理が一度で済む（後者は仕様からの推論）。

## DLP規則でのラベルの使い方

| 使い方 | できること | できないこと | 出典 |
|---|---|---|---|
| 条件 | ラベルが付いているか、単一選択の選択肢型フィールドの値（1つ以上）、およびその否定 | 複数選択を許可した選択肢型の値、数値・日付・文字・利用者の値 | [K3] |
| 動作（付与） | ラベルと単一選択の選択肢型フィールドの値の付与。バッジ付きラベルを含む | 値なしでラベルだけを付ける。複数選択型の値、他の型の値を付ける | [K3] |
| 条件と動作の併用 | — | 同じ規則でラベルを条件と動作の両方に使う | [K3,K4] |

値なしでラベルだけを付けたい場合、公式資料は既定の分類を案内している。[K3]

**ページ間の表記差：** DLP for Driveの規則作成ページの条件表は演算子「Is」と「ラベルが付いているか」だけを示し、フィールド値の条件に触れていない。ラベルの自動付与ページはフィールド値の条件を明記している。運用設計では、管理画面で実際に設定できる範囲を確認する。[K3,K4]

### DLPが付与した値の扱い

| 論点 | 仕様 | 出典 |
|---|---|---|
| 新規・既存ファイル | DLP規則によるラベル付与は新規と既存のファイルの両方に適用される | [K3] |
| 利用者による変更 | 規則ごとに、利用者が値を変更できるかを選べる。禁止した場合、利用者が変更するとDLPが直ちに再検査して規則の値へ戻すと説明するページがある。DLPのページ本体にはこの再上書きの記述がない | [K2,K3,K5] |
| 複数規則の競合 | 同じ種類の規則が同じファイルへ異なる値を付けようとすると、選択肢の並びで上位の値が適用される | [K3] |
| 付与元の優先順位 | DLP規則の値はAI分類より優先し、両者は既定の分類より優先する | [K3] |
| 規則の無効化 | 規則を無効化すると、その規則が付けたラベルと値が自動で外れる。ただし利用者の変更を許可していて利用者が変更した値は残る。反映には数分〜数時間以上かかる | [K3] |
| ラベル定義のロック | DLP規則が使うラベル・フィールド・選択肢は、無効化と削除ができない。名前変更とフィールド・選択肢の追加はできる。全規則から外すとロックが解ける | [K3] |

ロックの範囲にもページ間で差がある。ラベルの編集・監視ページは「DLP規則が使うラベルは編集できない」と書く一方、破壊的な編集（無効化・削除）のロックとも書いている。既定の分類に使ったラベルは、編集・無効化・削除のいずれもできないとされる。[K5,K6]

## 既定の分類と必須ラベル

| 機能 | 仕様 | 出典 |
|---|---|---|
| 既定の分類 | 新規作成時と所有者の変更時に、組織部門またはグループ単位で設定したラベルを付ける。選択肢型フィールドを持つラベルだけが対象。所有者が変わらない既存ファイルには遡って付けない。グループの設定が組織部門より優先する。利用者のラベル権限にかかわらず付く | [K6] |
| 必須フィールド | 強制されない。未入力でも利用・共有・編集は妨げられず、Driveに案内表示が出るだけ | [K1,K2] |

## 権限

| 操作 | ファイル側 | ラベル側 | 出典 |
|---|---|---|---|
| ラベルの付与・値の変更 | 編集者 | 適用権限（管理画面では「Can apply labels and set values」） | [D3,K1,K2] |
| ラベルの閲覧・検索 | 閲覧者 | 閲覧権限 | [D3] |

ファイルの閲覧権限しかない利用者は、ラベルの適用権限を持っていても値を見るだけで付与できない。またDriveのラベルは、ラベル対応の契約を持つ利用者が所有するファイルか、共有ドライブ内のファイルにしか付けられない。[K1,K2,D3]

## API

ファイル上の値の操作はDrive API、ラベルの定義の操作はDrive Labels APIと、別のAPIに分かれる。

### ファイル上の値：`files.modifyLabels`

既存ラベルの特定フィールドの値だけを変更できる。1回の要求に複数の変更を含められ、すべて成功するかすべて失敗するかのどちらかになる。[D1,D2]

```http
POST https://www.googleapis.com/drive/v3/files/FILE_ID/modifyLabels

{
  "labelModifications": [
    {
      "labelId": "LABEL_ID",
      "fieldModifications": [
        { "fieldId": "FIELD_ID", "setSelectionValues": ["CHOICE_ID"] }
      ]
    }
  ]
}
```

| 項目 | 内容 |
|---|---|
| 値の設定 | 型に応じて`setSelectionValues`、`setTextValues`、`setIntegerValues`、`setDateValues`（`YYYY-MM-DD`）、`setUserValues`（メールアドレス）を使う |
| 値の消去 | フィールド単位で`unsetValues: true` |
| ラベルを外す | `removeLabel: true` |
| フィールドなしで付ける | `fieldModifications`を省いた`labelModifications` |
| 選択肢の指定 | 表示名ではなく選択肢の識別子 |
| 型・個数の誤り | 複数値を受けないフィールドへの複数値や型の不一致は400エラー |
| 応答 | 追加・更新されたラベルだけを返す |
| 認可範囲 | `drive`、`drive.file`、`drive.metadata`のいずれか |

指定しなかった同じラベルの他フィールドが保持されるかは、公式資料に明記がない。仕様の説明は指定したフィールド単位の置き換えなので保持されると考えられるが、運用前に実環境で確認する。[D1,D2]

### 現在の値の取得

| 方法 | 内容 | 出典 |
|---|---|---|
| `files.listLabels` | ファイルに付いたラベルの一覧。1ページ既定100件 | [D4] |
| `files.get`の`includeLabels` | 指定したラベル識別子の値を`labelInfo`に含める。`fields`にも`labelInfo`の指定が必要 | [D5,D6] |

### 検索

Drive APIの`files.list`でラベルの有無と値を検索できる。例の名前は説明用で、実際はラベルとフィールドの識別子を使う。[D6]

| 目的 | 構文の例 |
|---|---|
| ラベルの有無 | `'labels/contract' in labels`、`not 'labels/contract' in labels` |
| フィールドの有無 | `labels/contract.comment IS NOT NULL` |
| 単一値の比較 | `labels/contract.status = 'executed'`、`labels/contract.value_usd < 2000` |
| 複数値 | `'EMAIL_ADDRESS' IN labels/project.project_leads` |

使える演算子は型で異なる。文字は`=`・`contains`・`starts with`等、数値と日付は比較演算子、選択肢と利用者は`=`と`!=`、複数値は`in`と`not in`。[D6]

### ラベルの定義：`labels.delta`

フィールドの追加・更新・型変更・有効化・無効化・削除、選択肢の追加・更新・有効化・無効化・削除をまとめて行う。変更は下書きになり、Driveのファイルで使うには公開が必要。認可範囲はアクセス方式で異なる。管理者アクセス（`useAdminAccess=true`）で`ADMIN`型を編集する場合は`drive.admin.labels`とManage Labels権限が必要で、管理者としての読取り専用には`drive.admin.labels.readonly`を使う。`drive.labels`での書込みは、管理者アクセスを指定しない利用者の`SHARED`型に対応する。各メソッドのscope一覧だけから両者を交換可能と解釈しない。[D7,D8,D9]

| 状態 | 内容 | 出典 |
|---|---|---|
| 無効化 | 付与済みの値と検索結果は残る。利用者は新たに付与できない | [K5] |
| 削除 | 付与済みのラベルと利用者が入力した値がすべて完全に消える。公開済みのラベル・フィールド・選択肢は、先に無効化して公開してから削除する | [K5,D8] |
| 公開後の型変更 | 管理画面ではフィールドの型と利用者型の複数選択の可否を変更できない | [K2,K5] |

**ページ間の食い違い：** APIのライフサイクル説明は、無効化したラベルもAPIからは付与できるとする。管理ヘルプは無効化を「利用者に付けさせたくないとき」の操作と説明する。また`labels.delta`には型変更の操作があるが、公開済みラベルでの制限はAPI側に書かれていない。どちらも運用前に確認する。[D8,K2,K5]

## 監査記録

利用者または規則がラベルを付与・更新すると管理者向けの監査記録に残り、変更前後の値を含む。DLPページはDriveの監査記録で規則による付与を確認できるとしている。イベント名は今回確認していない。[K3,K5]

ラベルの値そのものがDLPの本文検査の対象になるかは、公式資料に記載がない。

## 運用設計で決めること

| 論点 | 仕様から言えること | 決めること |
|---|---|---|
| ラベルの分け方 | ラベルは組織で150個まで、フィールドは1ラベル10個まで。権限はラベル単位 | 用途（DLP用、業務分類、試験の正解用等）ごとにラベルを分けるか、フィールドで分けるか |
| DLPで使う型 | 条件・動作とも単一選択の選択肢型だけ | DLPに使う分類は単一選択の選択肢型で設計する |
| 付与と制限の分離 | 同じ規則でラベルを条件と動作の両方に使えない | 付与する規則と、ラベルを条件に共有を制限する規則を別にする |
| 利用者の上書き | 規則ごとに変更可否を選べる | 誤検知の申立てを利用者の値変更で受けるか、別の手続きにするか |
| 規則の停止 | 無効化で規則が付けた値は外れる。利用者が変えた値は残る | 規則の入替え時に、外れた値と残った値の確認手順を用意する |
| 定義の変更 | DLPが使う定義は無効化・削除できない。削除は全付与を消す | 選択肢の廃止手順（規則から外す→無効化→公開→削除）と影響確認 |
| 外部連携 | 値はAPIでフィールド単位に変更・検索できる。付与には編集権限が要る | 自動処理の実行主体と、その主体が編集権限を持つ範囲 |
| 試験での利用 | 試験の正解用ラベルを規則の条件にしない（[試験の説明書](../../scripts/workspace_dlp_benchmark/README.md)） | 正解用ラベルとDLP出力用ラベルを別ラベルにし、正解用は規則が参照しない |

## 未確認の事項

- 1ファイルに付けられるバッジ付きラベルの数。
- `files.modifyLabels`で指定しなかったフィールドが保持されること（明記なし）。
- 数値型・日付型フィールドの上限値。
- ラベルの付与・変更を記録する監査イベントの名称と項目。[Driveの監査イベント一覧](https://knowledge.workspace.google.com/admin/reports/drive-log-events)で確認する。
- 利用者が変更した値をDLPが戻すか（ページ間で記述が異なる）。
- 無効化したラベルをAPIから付与できるか（ページ間で記述が異なる）。

## 公開一次資料

| 番号 | 資料 |
|---|---|
| K1 | [Get started as a classification labels admin](https://knowledge.workspace.google.com/admin/security/get-started-as-a-classification-labels-admin?hl=en) |
| K2 | [Create classification labels for your organization](https://knowledge.workspace.google.com/admin/security/create-classification-labels-for-your-organization) |
| K3 | [Apply classification labels to Drive files automatically with DLP rules](https://knowledge.workspace.google.com/admin/security/apply-classification-labels-to-drive-files-automatically-with-dlp-rules) |
| K4 | [Create DLP for Drive rules and custom content detectors](https://knowledge.workspace.google.com/admin/security/create-dlp-for-drive-rules-and-custom-content-detectors) |
| K5 | [Edit and monitor classification labels for your organization](https://knowledge.workspace.google.com/admin/security/edit-and-monitor-classification-labels-for-your-organization) |
| K6 | [Apply default classification labels to new files automatically](https://knowledge.workspace.google.com/admin/security/apply-default-classification-labels-to-new-files-automatically) |
| D1 | [files.modifyLabels](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/modifyLabels) |
| D2 | [Set a label field on a file](https://developers.google.com/workspace/drive/api/guides/set-label) |
| D3 | [Drive Labels API overview](https://developers.google.com/workspace/drive/labels/guides/overview) |
| D4 | [files.listLabels](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/listLabels) |
| D5 | [files.get](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/get) |
| D6 | [Search for files with a specific label or field value](https://developers.google.com/workspace/drive/api/guides/search-labels) |
| D7 | [labels.delta](https://developers.google.com/workspace/drive/labels/reference/rest/v2/labels/delta) |
| D8 | [Label lifecycle](https://developers.google.com/workspace/drive/labels/guides/label-lifecycle) |
| D9 | [Choose Google Drive Labels API scopes（認可範囲・Administrator access）](https://developers.google.com/workspace/drive/labels/guides/authorize) |
