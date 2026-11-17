# LIGHTのPII/DLP検知用データセット作成

架空の個人情報を含む資料と、含まない資料を作り、Google Driveへ置けるディレクトリにまとめるスクリプトです。文字・表・画像・Office・PDF・圧縮資料を扱います。600MBを目安とし、許容上限は660MBです。必要な条件を満たせば容量が小さくてもよく、画像劣化や容量を埋めるための反復は作りません。

ローカル資料の生成・検証とAstraによる指摘の修正・再確認を通過しました。Google Sheetsの実環境での作成・権限確認は未完了のため、LIGHT全体は完成扱いにしていません。検証件数と限界は[検証記録](REVIEW.md)を参照してください。作成済みと検証済みを区別した`ground_truth/coverage.json`を確認してください。

## 元データは何か

**外部の人物データセットや実在の証明書は読み込んでいません。** `generate.py`の`FIELDS`・`NEGATIVE`と追加条件のスクリプトに書いた、独自の架空例を使います。生成AIへの問い合わせもありません。

人物設定は12の姓と10の名を組み合わせた120人分です。氏名だけ、メールだけ、番号だけの資料も含めるため、全資料に氏名を表示するわけではありません。住所・学校・会社・銀行等は見本の設定、メールは`example.test`です。電話や番号について実在性・未割当・未発行は保証しません。カード番号は独自の試験値を中心にし、比較用の資料には一般的な試験値も含めます。実際のサービスへの照会・決済・本人確認には使いません。

調査で候補に挙げたSumi、Nemotron-PII-Japan、Nemotron-Personas-Japan、Finance-Japan、Synthea、免許証の公開画像は、今回の生成処理では使っていません。それらの利用条件を今回の独自生成物の条件と混同しないでください。

フォントは利用者が指定します。再配布せず、使用したファイルのハッシュ値を生成記録へ残します。PDFには日本語フォントを埋め込みます。主な公開仕様の参照先は末尾に記載しています。

## 何を、どの順序で作るか

1. **元文書を240例作ります。** PIIあり120例、なし120例です。陽性は基本情報20、識別番号16、経歴16、所得・家族12、支払・口座16、免許証・旅券の見本12、医療・健康14、その他の要配慮情報14例です。陰性は一般資料36、空欄帳票20、紛らわしい表現28、一般解説16、非個人の表12、空の資料8例です。
2. **文章と位置の正解を作ります。** 情報の種類・値・人物への対応を持たせ、画像は描画位置を記録します。要配慮情報は11分類に分け、全体で計画の22項目を扱います。
3. **鮮明な画像にします。** 同じ元文書をPNG・JPEG・TIFFへ変換します。人物名を分散し、配置も6種類に変えます。免許証・旅券は見本表示と図形の顔領域を持つ独自様式で、実物の厳密な再現ではありません。
4. **適した資料だけを各形式へ展開します。** TXTは240例、その他の通常形式は資料群ごとの代表例を選びます。全32分類を全形式に機械的に複製することは既定では行いません。形式変換した資料を独立した文書数へ加算しません。
5. **隠れた情報・読取条件を追加します。** 非表示セル、コメント、脚注、数式、文書属性、添付、暗号化、入れ子等を作ります。通常の陰性資料にも同じ構造を使います。空欄化・伏字・本人の事実と一般説明等の比較も作ります。
6. **ディレクトリを構成します。** 陰性だけ、陽性だけ、混在、空、深い階層、陰性999件と陽性1件、隠しファイル、同内容の複製等を作ります。999件の複製は独立した精度標本ではありません。
7. **正解を分離して保存します。** 入力と正解を照合し、実形式、内容、画像、暗号化の鍵条件、容量、再生成の結果を検証します。

240例は生成した元文書数であり、240件の統計的に独立した実務標本ではありません。同じひな形・一部の属性文・番号の反復が残ります。LIGHTは対応確認と変更時の検出検証に向き、低い誤警告率を数値保証するには追加の独立文書が必要です。

## 作成できる形式・条件

| 区分 | 作成するもの |
|---|---|
| 文字・構造化資料 | TXT、Markdown、UTF-16、CP932、CSV、TSV、JSON、JSONL、XML、HTML |
| メール | EMLの本文、宛先、署名、引用、添付、メールやZIPの入れ子 |
| Office | DOCX、XLSX、XLS、XLSM、XLSB、PPTX。XLSBは実際のバイナリ形式。マクロは動かさず、現在のXLSMはマクロコードなし |
| PDF | 文字PDF、画像PDF、複数ページ、文字・画像の混在、段組、縦方向の配置、フォーム、注釈、添付 |
| 画像 | PNG、JPEG、TIFF、複数ページTIFF。意図的な劣化なし |
| 圧縮 | ZIPの無圧縮・Deflate・ZipCrypto・AES、ZIP64、入れ子、7z、TAR、GZIP、BZIP2、XZ |
| 保護 | Excel・PDFの開封暗号化、編集・構造保護、変更用パスワード、内外で異なる鍵、正しい鍵・鍵なし・誤った鍵 |
| 本文以外 | 非表示シート・行列、フィルタ、白文字、表示書式、コメント、数式と計算結果、名前定義、画像、埋込み文書、ヘッダー・フッター、脚注、変更履歴、ノート、非表示スライド、属性、ファイル名・ディレクトリ名 |
| Google Sheets | 通常のネイティブ変換、編集保護、非表示シート、メモ、コメント、数式、画像、出力物、権限試験の作成処理。実環境の確認は別工程 |

破損・切断、拡張子の不一致、固定した容量境界の資料も含みます。固定境界は試験用の設定で、実製品の上限を証明する値ではありません。CSEはLIGHTでは任意です。シート保護・共有権限・CSE・開封用暗号化を同じ方式として採点しません。

## 実行方法

PythonとNode.js、Info-ZIPの`zip`、日本語フォントが必要です。依存を固定したファイルを用意しています。検証・描画には追加でLibreOffice、文字認識にはTesseractと日本語認識データを使います。

```sh
python3 -m venv .venv
.venv/bin/pip install -r scripts/pii_image_dataset/requirements-all.txt
npm ci --prefix scripts/pii_image_dataset
.venv/bin/python scripts/pii_image_dataset/build.py \
  --output /任意の新しい保存先/pii-light \
  --font /日本語フォントの保存先/font.ttf \
  --xlsx-engine xlsxwriter \
  --sheetjs-module scripts/pii_image_dataset/node_modules/xlsx
```

出力先は新しいディレクトリを指定します。存在する保存先の上書きはしません。乱数の初期値は`--seed`で変更でき、既定値は`20261113`です。日本語を表示できるフォントを使用してください。

通常のXLSXを作る処理は`--xlsx-engine`で指定します。公開された依存だけで作る場合は、上の例のように`xlsxwriter`を指定してください。`build.py`と、生成済み画像から続ける`generate_all.py`の両方で指定できます。

| 指定値 | 動作 |
|---|---|
| `auto`（既定） | 利用可能ならArtifact Toolを使い、利用できなければXlsxWriterを使う従来の選択。環境によって作成器が変わる |
| `xlsxwriter` | 常にXlsxWriterを使う。Artifact Toolがあっても呼び出さない |
| `artifact` | Artifact Toolを使う。利用できなければ明示的に失敗し、XlsxWriterへ切り替えない |

`generation.json`の`xlsx_engine.requested`と`xlsx_engine.actual`に要求値と実際の選択を保存します。作成器の版は`baseline_xlsx_author`へ記録します。この指定は通常XLSXに対するもので、特殊な保存条件の資料は従来どおり専用の生成処理を使います。

```text
pii-light/
  drive_upload/                ← Driveへ置く検査対象だけ
    files/                    ← PNG・JPEG・TIFF
    text/ structured/ mail/ office/ pdf/
    features/ protected/ archives/ comparisons/
    names/ names-control/ boundaries/ scenarios/ trees/
  ground_truth/               ← 正解・鍵・条件・対応表。検知器へ渡さない
  automation/                 ← Sheetsの作成設定とスクリプト。検知器へ渡さない
  generation.json             ← 生成器・依存・フォント等の版
```

`drive_upload`だけをアップロード・検査します。親ディレクトリ全体には架空のPIIを含む正解や生成設定があり、それを入力へ混ぜると陰性評価が成立しません。空フォルダを省略する転送方式では、空ディレクトリ試験を別に作成・確認してください。

## 正しく作れたかの確認

```sh
PII_XLSX_MODULE=scripts/pii_image_dataset/node_modules/xlsx \
  .venv/bin/python scripts/pii_image_dataset/verify_all.py --dataset /作成先/pii-light
.venv/bin/python scripts/pii_image_dataset/verify_media.py --dataset /作成先/pii-light
.venv/bin/python scripts/pii_image_dataset/verify_protection.py --dataset /作成先/pii-light
.venv/bin/python scripts/pii_image_dataset/coverage.py --dataset /作成先/pii-light
```

- `verify_all`は全配置・ハッシュ・形式の内部構造と、別の読取処理で復元した値を確認します。信頼する正解側に保存した復元内容の指紋も比較するため、陰性資料への追記も検知します。この指紋は正解自体の改ざんを防ぐ署名ではありません。文字・構造化資料、PDF、陰性のXMLベースOfficeでは原稿と格納面の期待値も別途比較します。陰性の書庫・メールの内部も再帰的に照合します。対応外の格納面まで独立した期待値照合を済ませたことにはしません。画像の文字はこの処理で成功扱いにしません。
- `verify_media`はPDFやOfficeに内包した画像が元PNGと同じ画素であることを確認します。
- `verify_protection`は実際に鍵を変えて読み、完了・部分読取・復号不能を比較します。
- `coverage`はLIGHTの形式・条件との対応を確認します。「作成済み」は本文の検証合格やGoogle上の実測成功を意味しません。
- `check_ocr`はTesseractによる文字認識の補助確認です。これはDLPの意味分類の検出率ではありません。
- `render_office`はLibreOffice本体を使った代表例の描画です。付属Pythonは使いません。変換成功、表示対象の文字一致、ページ範囲、目視確認の状態を分けて記録します。文字一致だけでは字形・重なりの正しさは保証しません。日本語フォントの場所を明示します。非表示スライドは検査用に表示して出力し、非表示の構造は別に確認します。

```sh
.venv/bin/python scripts/pii_image_dataset/render_office.py \
  --dataset /作成先/pii-light --output /新しい描画先 \
  --font-dir /日本語フォントのディレクトリ
```

同じ設定で再生成し、通常の文字・画像・Office等はバイト単位で比較します。暗号化の乱数や書庫の内部時刻による差は、復号後の値・項目・保護条件を比較します。ファイルのバイト差と内容差を混同しません。

## 再現性の範囲と保存する条件

このLIGHT生成器は、[385資料のv3 TXT生成器](../workspace_dlp_benchmark/extended/README.md#同じデータセットを再生成する)とは別のデータセット。同じ生成器・乱数の初期値だけで、過去の全ファイルのバイト一致までは保証しない。日本語フォントの実ファイル、PythonとNode.jsの版、`requirements-all.txt`、`package-lock.json`、外部の`zip`、利用するOffice生成処理が影響する。フォント自体はリポジトリへ同梱しないため、同じフォントを別途確保する必要がある。

通常XLSXの作成器も同じに固定します。`auto`は環境依存であり、`xlsxwriter`指定の生成物が過去のArtifact Toolによる生成物とバイト一致する保証はありません。作成器の明示と依存の固定は再生成条件を明らかにするもので、LIGHT全体の過去のバイト再現を完了したという意味ではありません。

再生成では`--seed 20261113`、同一のフォント（SHA-256で確認）、依存の固定ファイル、`generation.json`の生成元・作成器の記録をそろえる。外部ツールの版と生成時のコマンドも、比較対象の保存物と一緒に残す。保存先の構造は上記の`drive_upload`・`ground_truth`・`automation`を維持し、空ディレクトリも保持する。

二組の生成物を比較する手順は次のとおり。暗号化の乱数等によるバイト差は、復号後の内容と構造の比較へ分けて報告する。

```sh
.venv/bin/python scripts/pii_image_dataset/verify_repro.py \
  --first /一組目/pii-light --second /二組目/pii-light
```

この比較は`ground_truth/files.json`が列挙したファイルと、指定した正解・条件のJSONが対象で、余分な未列挙ファイルを含む全保存物の完全一致を証明するものではない。Google上の資料ID・共有状態・Google Sheetsへの変換結果はローカル生成とは別に確認する。今回の再現性整備ではLIGHT全体の再生成・描画・復号比較は実行していない。

## Google Drive・Google Sheets

`google_drive.py`は既定では作成計画だけを表示します。APIで実作成する場合は、利用可能なGoogle認証と試験先が必要です。

```sh
.venv/bin/python scripts/pii_image_dataset/google_drive.py --dataset /作成先/pii-light
.venv/bin/python scripts/pii_image_dataset/google_drive.py \
  --dataset /作成先/pii-light --execute --parent root \
  --scope-evidence /リポジトリ外の保存先/scope-evidence.json \
  --report /リポジトリ外の保存先/drive-run.json
```

`--execute`では、実際の認証主体と規則の適用範囲を確認した、リポジトリ外の`--scope-evidence`が必要です。認証が成功したことだけで検査対象と認定しません。マイドライブはファイル所有者、共有ドライブはそのドライブに適用するDLP規則を確認し、別の試験群として記録します。[適用主体の公式説明](https://knowledge.workspace.google.com/admin/security/about-dlp-for-drive)

事前確認の証拠は`schema_version: 1`、`creator_email`、`parent_id`、`drive_kind`（`my_drive`または`shared_drive`）、`rule_ids`、`scope_readback`を持つJSONです。共有ドライブでは`shared_drive_id`も指定します。`scope_readback`は別保存した正規化証拠の`path`と`sha256`で、参照先には時差付きの`verified_at`と、規則ごとの有効状態・Drive対象・適用する主体・組織部門やグループを確認した`rule_scope_checks`を置きます。現在のDrive利用者と配置先、保存済み証拠の指紋を照合し、不一致・不足なら配置前に停止します。証拠の鮮度上限72時間はこの実装の事前条件であり、製品の検査・反映時間の保証ではありません。範囲証拠は操作者が別途確認して作る入力です。Drive APIだけで組織部門やグループを独立評価したことや、DLPの走査完了を証明したことにはなりません。保存物の指紋一致も、入力の真実性を保証する署名ではありません。

`--upload-all`は通常ファイルも配置します。`--reader`は指定した試験用アカウントへ読取権限を付与し、別アカウントで確認するまで維持します。その後、同じ報告に対して`--permission-stage verify-granted`、`revoke`、`verify-revoked`を順に実行します。読取確認には`--reader-credentials`で所有者とは別の認証情報を指定します。既存資料や公開共有の権限は変更しません。権限の付与・取消と、別アカウントが実際に読めたかの確認は区別します。

権限を変えずに現在の読取を観測する段階は`observe-access`です。CLIは段階実行に`--execute`を要求しますが、この段階は権限の付与・取消を呼びません。既存の専用実行報告と、その対象に対応する別認証を使います。

```sh
.venv/bin/python scripts/pii_image_dataset/google_drive.py \
  --permission-stage observe-access --execute \
  --reader-credentials /リポジトリ外の認証情報.json \
  --report /リポジトリ外の保存先/drive-run.json
```

現在の収集経路は外部認証によるSheets本文の`spreadsheets.get`のみです。所有者側のファイル版と全ページの権限一覧を前後で保存し、時刻、読取結果、版の安定性を記録します。ダウンロード・印刷・コピーを実行した証拠や、拒否がDLPに起因する証明は収集しません。作成時には要求開始・応答完了とサーバー側の作成・更新時刻を別記し、時計の一致を未確認のまま単一の契機時刻と扱いません。

この手動取消の確認は、標準DLPが既存共有を遮断した実証ではありません。DLP是正を評価するときは、対象規則の実行記録・所有者側の前後状態・別認証の実アクセスを組にし、[検知・是正比較試験](../workspace_dlp_benchmark/README.md)の別の観測・指標で採点します。認証失敗・取得不能・規則の未反映を遮断成功にしません。

格納箇所別のネイティブSheetsには、出力の`automation/google_sheets.gs`と`google_sheets_config.json`も用意します。Apps ScriptでAdvanced Drive service v3を有効にし、試験用の親フォルダと、正解を保存する別フォルダを設定して`buildPiiSheets(config)`を呼び出します。検証済みXLSXを変換してから、非表示・メモ・コメント・数式・画像・編集保護を別資料へ配置します。設定と正解は検査対象の外に置きます。


### Sheetsを少数ずつ作り、再開する

Apps Scriptには[1回あたりの実行時間上限](https://developers.google.com/apps-script/guides/services/quotas)があるため、既定では1資料ずつ、4分を目安に区切ります。1件の外部API呼出しが長引く場合まで上限内終了を保証するものではありません。

1. 出力の`automation/google_sheets.gs`と`appsscript.json`を試験用Apps Scriptプロジェクトへ配置します。実環境の認証・サービス有効化は別途必要です。
2. `google_sheets_config.json`の2つの保存先を、試験入力の親フォルダーと検査範囲外の報告フォルダーへ設定します。この設定ファイル自身も検査範囲外のDriveへ置きます。実際のIDを設定したものは公開リポジトリへ戻しません。
3. `runPiiSheets`の`configFileId`をその設定ファイルのIDへ変更して実行します。進捗報告と再開参照を保存します。
4. `runPiiSheets`を繰り返し実行します。作成済みの資料と出力を再利用します。元資料が変わると再開を拒否します。処理中の入力フォルダーを完成資料として配布しません。

直接呼ぶ場合は`buildPiiSheets(config)`の戻り値の`reportFileId`を、次回の`config.resumeReportId`へ渡します。初回の参照保存に失敗した場合も、報告フォルダー内の有効な初期JSONのIDから再開できます。`maxCasesPerRun`で1〜28件へ変更可能ですが、通常は既定値を使います。失敗出力は次回に再試行し、`retryFailedExports=false`を指定した場合だけ再試行を抑止します。同名候補が複数ある場合は未確認として停止します。

同じApps Scriptプロジェクト内の同時実行を抑止します。別プロジェクトから同じ試験先を同時操作することは想定しません。保存済み資料の回収を試みますが、外部サービスとの全操作を一つの不可分な処理にはできないため、実行報告・入力・保留出力の最終照合は省略しません。

出力形式は[Google公式の対応表](https://developers.google.com/workspace/drive/api/guides/ref-export-formats)に基づきます。出力成功・失敗と、出力物の正解確認済みかは別です。

実環境のID、認証情報、権限・取得結果は非公開の実行報告へ保存し、この公開リポジトリへ追加しません。CSV・TSVは全シートを保持する出力ではありません。出力時に消えるメモや画像等もあるため、元資料の正解を無条件に出力物へ転用しません。出力物は正解保存側の保留フォルダーに置き、内容を確認するまで検査対象へ含めません。

## 検出検証に使うとき

「読めなかった」は検出漏れや陰性と分け、読めた資料でPII検出を採点します。一部しか読めなかった資料も別に記録します。氏名だけを検出した結果を病歴・口座等の成功にはしません。暗号化の警告だけでもPII検出成功にはしません。

正解の対象範囲は、値全体、種類、人物への関係、画像領域、格納場所です。複数ページPDFとTIFFでは、同じ値でもページ・フレームごとの出現を別に記録します。`value_id`は値の対応、`occurrence_id`はそのファイル内での各出現を表します。

会員IDで別文書の予約情報と結び付ける条件は、`conditional_expectations.json`に観測できる事実と、文書間の結合を許す場合・許さない場合の正解を分けています。製品に許す参照範囲を先に固定して採点します。銀行名・支店・番号や住所内部の細分化、法的な分類の確定判断、証明書の真贋・実物への厳密な類似は保証しません。製品の出力分類へ対応付けてから評価してください。

ファイルだけの警告しか返さない製品に対し、位置別・値別の完全回収率を推定しません。人物名やメールが共通して含まれる陽性も多いため、ファイル警告率だけで他の項目の能力を判断しないでください。

## 公開仕様・関連調査

- [全体の作成計画](../../research/technology/pii_dlp_test_dataset_creation_plan_20261113.md)
- [22項目のデータセット調査](../../research/technology/personal_information_dataset_creation_methods_20261113.md)
- [Google Driveのアップロードと変換](https://developers.google.com/workspace/drive/api/guides/manage-uploads)
- [Google Sheetsの保護方式](https://support.google.com/docs/answer/1218656?hl=en)
- [GoogleのCSEとDLPの制約](https://knowledge.workspace.google.com/admin/security/client-side-encryption-faq)
- [Officeの埋込みパッケージ](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/32be961f-d71a-4812-913f-b675c79aa88a)
- [WinZipのAES拡張](https://www.winzip.com/en/support/aes-encryption/)、[7z形式](https://www.7-zip.org/7z.html)
- [Tesseractの日本語認識データ](https://github.com/tesseract-ocr/tessdata_fast)

Google APIの403はファイル権限以外の原因でも発生するため、権限試験では原因を分類し、設定障害や原因不明を取消後拒否の成功にしません。[Googleの共通エラー一覧](https://docs.cloud.google.com/resource-manager/docs/core_errors?hl=en)を参照してください。
