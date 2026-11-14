# Google Drive等の機密情報検知の対象形式と精度の比較

調査日：2026年11月11日。[判定登録と再通知抑制の比較](dlp_decision_and_alert_suppression_matrix_20261111.md)を補う詳細表。公開公式資料だけを使用し、実測値は含めない。

追加調査：[Nightfallの日本語対応の精査](nightfall_japanese_support_20261111.md)、[Netskope・Strac・Teleskopeと自作部品を含む制約比較](dlp_product_limitations_and_build_options_20261111.md)、[自作の公開事例](dlp_self_built_cases_20261111.md)。

BigIDは[今回の追加精査](bigid_dlp_api_constraints_20261111.md)を反映。以下のBIは同稿と公開一次資料の番号を参照する。

**Google Drive内の保存データを扱う主候補は Google Workspace DLP、Nightfall、Microsoft Purview の外部サービス接続である。Box Shield は Box内の分類が対象であり、Google Drive全体を検査する製品としては数えない。** Purview の外部サービス接続は公開試験版で、PDF非対応等の制約がある。Nightfall の運用機能が要件に近くても、日本語の氏名・住所の検知性能まで優位とは判断できない。

「検知対応」はその種類を探す仕組みがあるという意味で、すべての表記・文脈で発見できるという保証ではない。○＝公式仕様あり、△＝限定・設定・追加処理が必要、未確認＝今回の資料では確定できない、対象外＝製品の保存先が異なる。

## 保存先と接続方式

| 製品・機能 | Google Driveの保存データ | Boxの保存データ | 導入方式・注意点 |
|---|---|---|---|
| Google Workspace DLP | ○ 標準機能。マイドライブ・共有ドライブ | 対象外 | 対応するWorkspace契約と管理権限が必要。Google Cloudの検査APIとは製品・契約を分ける [G1] |
| Box Shield 通常分類 | 対象外 | ○ | Box内の自動分類。`.gdoc`等が形式一覧にあることは、Drive全体の監視を意味しない [B1] |
| Box Shield Pro AI Classification | 対象外 | ○ | Box内の意味に基づく分類。Shield Pro追加契約 [B3] |
| Nightfall | ○ | 本稿の機能評価対象外 | Google DriveにAPIで接続し、継続検知と履歴検査 [N1] |
| Microsoft Purview 外部サービス接続 | △ Google Workspace接続。公開試験版 | △ 公開試験版 | Defender for Cloud Appsの接続設定が必要。段階提供 [M7] |
| Microsoft Defender for Cloud Apps File policies | ○ 既存方式 | ○ 既存方式 | 2027年1月6日廃止予定。新規選定は後継機能を評価する [M4] |
| Amazon Macie | 対象外 | 対象外 | Amazon S3専用。他の保存先からS3へ移す場合は別途転送処理が必要 [A4] |
| BigID | ○ マイドライブ・共有フォルダー・共有ドライブ | 今回の形式評価対象外 | 内容と共有権限をAPI接続で検査。分類の一覧と危険な状態の問題一覧を区別 [BI7] |

## 検知できる情報の種類

この表の「標準一覧に記載なし」は、製品全体で絶対に検出できないという意味ではない。独自規則や意味に基づく分類は別列・別行で扱う。Microsoftは分類機構の一覧であり、すべての分類器が外部接続先で同条件で動作するとの保証には広げない。

| 情報の種類 | Google Workspace DLP [G5] | Box 通常分類 [B2] | Box AI Classification [B3] | Nightfall [N5–N7] | Microsoft Purview [M8–M10] |
|---|---|---|---|---|---|
| 氏名 | ○ Name occurrence。日本語の個別性能は未確認 | 標準一覧に記載なし | △ 説明に基づく文書分類。氏名の箇所抽出とは別 | ○ Person name。日本語氏名は未確認 | ○ All full names。日本語を明示 |
| 電話番号 | ○ Phone number | ○ 国際形式に沿う番号 | △ 分類条件として設計 | ○ 任意の国の番号。国内表記の精度は要試験 | 日本の電話番号に特化した標準検出は今回未確認。独自規則が候補 |
| メールアドレス | ○ | ○ | △ 分類条件として設計 | ○ | 標準分類一覧で専用項目は今回未確認。独自規則が候補 |
| 日本語住所 | 日本語専用の標準検出は今回未確認 | 標準一覧に記載なし | △ 文書分類で評価。住所抽出の精度は未確認 | △ Street address は英語圏データで学習。日本語は未確認 | ○ Japan physical addresses |
| 日本のマイナンバー | ○ Individual Number | 標準一覧に記載なし | △ 条件として設計。番号検証機能とは別 | ○ JAPAN_MY_NUMBER | ○ 個人番号・法人番号 |
| 日本の運転免許証番号 | ○ | 日本専用は標準一覧に記載なし | △ 条件として設計 | 日本専用の番号検出は今回未確認。証明書画像分類とは別 | ○ |
| 日本の旅券番号 | ○ | ○ Passportに日本を含む | △ 条件として設計 | 日本専用番号検出は今回未確認。旅券画像分類あり | ○ |
| 日本の銀行口座番号 | ○ | 日本専用は標準一覧に記載なし。IBANあり | △ 条件として設計 | 日本専用は今回未確認。IBAN・複数国口座あり | ○ |
| カード番号 | ○ | ○ | △ 文書・画像の分類 | ○ 検査数字も検証 | ○ |
| API鍵・秘密鍵・パスワード | ○ 複数の標準検出 | 汎用の標準検出は一覧に記載なし | △ 説明に基づく分類。鍵の有効性検証とは別 | ○ API鍵、秘密鍵、接続文字列、パスワード | ○ 多数のサービス別資格情報 |
| 医療情報 | ○ 医療用語・文脈等 | ○ ICD9／ICD10の符号 | △ 医療文書の分類を設計 | ○ 医療情報・医療文書。米国制度中心の項目あり | ○ 医療用語・疾病等 |
| 営業秘密・設計資料・契約書 | △ 語句・形式規則。別のAI分類を組合せ可能 | △ 独自語句 | ○ 説明に沿った機密文書分類 | ○ 文書分類・自然言語で指定する独自検知 | △ 学習可能分類等は機能・接続先ごとに確認 |
| 独自の顧客番号・社内語句 | ○ 正規表現・語句一覧 [G4] | ○ 独自語句。正規表現対応とは扱わない | ○ 分類説明 | ○ 正規表現・辞書・文書指紋・自然言語で指定 [N7] | ○ 独自の機密情報の種類を定義 |

Amazon Macie は資格情報、金融情報、個人情報・医療識別番号を標準分類し、独自の形式規則を追加できる。氏名・住所・電話番号には国別の対応範囲があるため、標準検出をそのまま日本語一般へ適用できるとは扱わない。Drive対象外のため、上表の主比較から分けた。[A5]

Box AIの「条件として設計」は、例としてそのような説明を入力できるという意味である。専用の番号検出器と同じ精度・一致箇所・検査数字の検証が提供されるとの意味ではない。

## 内容を検査できるファイル形式

**ファイル形式への対応と、その中のすべての要素を読めることは別である。** ○でも容量、文字抽出、埋込み画像、保護設定の制約を受ける。Box列はBox内、Macie列はS3内の形式対応である。

| 形式・要素 | Google Workspace DLP [G1,G6] | Box 通常分類 [B1] | Box AI Classification [B3] | Nightfall [N8–N9] | Purview 外部サービス接続 [M7] | Amazon Macie [A4] |
|---|---|---|---|---|---|---|
| Google Docs／Sheets／Slides | ○ | △ `.gdoc`・`.gsheet`を列挙。Drive直接監視ではない | △ `.gdoc`・`.gslide`・`.gslides`・`.gsheet`を列挙 | ○ | △ Google Workspace対応。3形式別の抽出仕様は今回未確認 | 対象外。書出し・S3転送が必要 |
| Word `.doc`／`.docx` | ○ | ○ | ○ | ○ Office文書 | △ 形式別の接続仕様を要確認 | ○ |
| Excel `.xls`／`.xlsx` | ○ | ○ | ○ | ○ Office文書 | △ 同上 | ○ |
| PowerPoint `.ppt`／`.pptx` | ○ | ○ | ○ | ○ Office文書 | △ 同上 | 標準一覧に記載なし |
| 文字を選択できるPDF | ○ | ○ | ○ 抽出可能な文字 | ○ | **非対応** | ○ |
| 画像だけのPDF | △ OCR有効化時。見逃しあり | 非対応。画像内の文字読取りなし | △ PDFの画像読取りには制約。単独画像対応をPDF内部へ広げない | ○ OCR。言語・画質別精度は未確認 | **非対応** | 非対応。画像内の文字読取りなし |
| PNG／JPEG／TIFF等の単独画像 | △ OCRと対象形式の条件あり | 非対応 | ○ 対応画像を意味で分類。文字だけの抽出とは別 | ○ OCR | 未確認。Microsoft 365側のOCR対応を外部接続先へ広げない | 非対応 |
| Office文書の埋込み画像 | 一律の全要素検査は未確認 | 非対応 | 非対応の注意書きあり | ○ 埋込み画像の検査を説明 | 未確認 | 非対応 |
| TXT／HTML | ○ | ○ `.txt`・`.htm`・`.html`等 | ○ | ○ | 未確認 | ○ |
| CSV／JSON／XML | ○ | ○ | ○ 形式別に文字抽出上限が異なる | ○ | 未確認 | ○ |
| ソースコード・設定ファイル | ○ 列挙された拡張子 | ○ 列挙された拡張子 | ○ 列挙された拡張子 | ○ 文字ベースのコード・設定 | 未確認 | △ 非バイナリー文字形式として対応する範囲 |
| ZIP等の圧縮ファイルの内部 | ○ `.7z`・`.rar`・`.tar`・`.zip`等 | 通常分類の形式一覧に記載なし | AI分類の形式一覧に記載なし | ○ ZIP・gzip等を展開 | 未確認 | ○ ZIP・gzip・TAR等を展開 |
| Parquet／Avro | 形式別の検査は今回未確認 | 形式一覧に記載なし | 形式一覧に記載なし | ○ Parquet。Avroは今回未確認 | 未確認 | ○ 両方 |
| 音声・動画の内容 | 非対応 | 通常分類の文字検査対象外 | 形式一覧に記載なし | 非対応 | 未確認 | 非対応 |
| パスワード付き・暗号化された本文 | 非対応 | 復号して分類できる一般的保証は未確認 | 同左 | 暗号化ファイルの存在検出は可能。復号して本文検査とは別 [N5] | 非対応 | ファイル内部の保護は別途確認。S3の保存時暗号化と区別 |

PurviewのMicrosoft 365内の検査は、外部接続版とは別の対応範囲を持つ。SharePoint／OneDrive等では追加設定・従量課金によるOCRがあり、PDFやOffice内画像を扱える。**その仕様をGoogle Drive上の検査へ転記してはいけない。** [M11]

## BigIDの属性と形式の追加評価

BigIDは今回のAPI比較にも追加した。一般的な製品説明と、Google Driveでの形式別保証を分ける。

| 対象 | 公開仕様による評価 | 未確定の条件 |
|---|---|---|
| 個人・金融・人事・企業機密 | 検知カテゴリとして説明 [BI7] | 日本語の氏名・電話・住所、日本の個人番号等の個別分類器と精度 |
| API鍵・秘密・トークン | 標準分類器と独自の形式規則、文脈抜粋の保存を説明 [BI11] | 全対象の有効性検証、鍵の失効まで自動実行する保証 |
| Google Docs・Sheets・Slides | Drive接続の対象として列挙 [BI7] | コメント・埋込み画像・非表示要素まで網羅する保証 |
| PDF・文書・表・プレゼンテーション | 対象として説明 [BI7] | `.doc`／`.docx`等の拡張子別対応、保護・暗号化された本文 |
| 画像・画像PDF | 製品全体にOCR検査の説明 [BI12] | Driveでの対象形式・有効化条件・日本語の読取り精度 |
| ZIP等の内部・音声動画 | 今回の公開資料から確定できない | 展開の深さ・件数・容量、音声文字起こし等を推定しない |
| 日本語精度 | 多言語対応の製品説明あり [BI13,BI15] | 同条件の適合率・再現率、属性別・形式別の評価資料 |

## 容量と検査の速さ

| 製品・機能 | 内容検査の上限・制約 | 検知の起点と時間 |
|---|---|---|
| Google Workspace DLP | 抽出文字の先頭10 MBを解析。非Google形式は50 MBまで文字抽出。圧縮内最大1,000ファイル、検出最大10,000件 [G6] | 作成・内容変更、規則変更。大量の既存検査は数時間・1日以上の場合あり。規則反映は最大24時間 [G1,G2] |
| Box 通常分類 | 抽出文字の先頭1 MB。ファイル自体の容量とは異なる [B1] | アップロード・編集・プレビュー等。完了時間の共通保証は今回未確認 |
| Box AI Classification | 抽出文字は文書系2 MB、表・コード系100 KB。画像は最大2048×2048へ縮小 [B3] | 有効化後の分類イベント。全既存内容の一括遡及検査とは別 |
| Nightfall | 共通仕様で最大1 GB。個別の接続・展開後容量・日本語OCRの上限は確認が必要 [N8] | Driveの継続検査と履歴検査。共通の秒数保証は今回未確認 [N1] |
| Purview 外部サービス接続 | PDF・暗号化ファイル非対応。一般DLPの上限をそのまま適用できるとは扱わない [M7] | 保存データを接続経由で検査。共通の秒数保証は今回未確認 |
| Macie | 対応圧縮内は最大100万ファイル・深さ10段。別の容量上限も適用 [A4] | 標準の自動探索は代表的な保存物の抽出検査。全作成イベントの即時検査ではない [A1] |
| BigID | Drive形式別の内容検査上限は今回未確認。検査設定・方式によって本文検査か属性のみかを区別 [BI2,BI12] | 1回・予定された検査等を設定。起動・停止・正常完了を区別し、Driveの完了時間保証は別途確認 [BI2,BI3,BI9] |

## 精度を比較できる根拠

適合率は「検出したうち本当に対象だった割合」、再現率は「本当の対象のうち検出できた割合」。F1値は両者をまとめた指標である。信頼度のHigh等は検出条件の設定値であり、正答率の実測値ではない。

| 製品 | 公開資料にある精度の説明 | 日本語の氏名・電話・住所について比較できる数値 |
|---|---|---|
| Google Workspace DLP | 検査の確率的な限界と誤検知・見逃しを明記。閾値、件数、近接条件を調整可能 [G2,G5] | 同一試験条件の適合率・再現率は今回未確認 |
| Box 通常分類 | 形式・検査数字・周辺語句等を考慮。Highは誤検知低減、Lowは感度優先 [B2] | 今回未確認 |
| Box AI Classification | 同じ内容でも分類が一致しない可能性を明記。最大10ファイルで試せる [B3] | 今回未確認。日本語の入力上限の記載は精度保証ではない |
| Nightfall | 公式のDetectorsページに適合率90–95%の表明 [N6] | 当該数値の日本語・属性別内訳、試験データ、再現率は同ページから確定できない。言語FAQは英語または個別学習済みの文脈に意味理解を限定 [N10] |
| Microsoft Purview | 検出定義、補助的証拠、信頼度を公開。氏名検知は日本語対応を明示 [M8–M10] | 同一試験条件の適合率・再現率は今回未確認。信頼度85を「精度85%」と読まない |
| Amazon Macie | 検査条件・国・必須の周辺語句を検出器別に公開 [A5] | 今回未確認 |
| BigID | 多言語分類、標準・独自分類器、結果の正誤判定を説明 [BI9,BI15] | 日本語の属性別・Drive形式別の同条件評価は今回未確認。多言語の表明を正答率と扱わない |

**公開仕様から製品の精度順位は付けられない。** 特に、電話番号の国際形式対応、UTF-8文字の受付、日本語の意味理解、日本語の氏名抽出は別々に評価する必要がある。Nightfallの新しい自然言語指定の検知器と、従来の言語FAQの関係も確認が必要で、日本語非対応と一括断定しない。[N7,N10]

## 指定フォルダーと許可した属性を記録だけにする構成

「氏名・電話番号を許可する」と「そのファイル全体を検査しない」を分ける。

| 製品 | 検知を残して通知しない | 保存場所の指定 | 属性別の絞り込み・制約 |
|---|---|---|---|
| Google Workspace DLP | ○ 監査のみ、警告設定なし [G4] | フォルダー配下を直接条件にする方法は今回未確認。確認用ラベルとの組合せは構成案 | 規則単位に属性を分け、規則の記録で把握する。原文値の全件台帳とは異なる |
| Box Shield | △ 分類・一致種別と件数を保持 [B1] | ○ 指定フォルダーと子フォルダー [B2] | ファイルの一致情報を表示できる。全ファイルを属性で横断検索する操作は今回未確認 |
| Nightfall | ○ 規則ごとの通知を無効化し検出イベントを残す [N11] | 共有ドライブ・ファイル・ラベル等で範囲設定。任意の子フォルダーの厳密な指定は今回未確認 [N12] | 検出器で絞り込み可能 [N2]。接続全体の通知設定にも注意 |
| Purview 外部サービス接続 | △ 警告設定と記録を分ける構成を検証 | 親フォルダー属性を条件に使用可能。ただし全子孫までの一致は要確認 [M7] | Activity explorerで活動確認可能。Content explorerで外部データの内容を一覧する機能は非対応 [M7] |
| Amazon Macie | ○ 抑制規則で検出を自動保管し外部送信を止める [A3] | S3保存物の属性条件 | 保管済みも属性で検索可能。結果は90日保存。許可リストは該当値を報告しなくなるため本用途では抑制規則を優先 |
| BigID | △ 分類の資産一覧と問題のsilencedを分離する案 | Drive共有フォルダーは検査対象。ただし全子孫×属性の許可条件を標準機能で指定できるかは未確認 [BI7,BI10] | 資産分類も収集し、許可済みの個人情報を問題一覧の外に残す。除外一覧を通知抑制の代わりにしない [BI4,BI9] |

設計案は「許可フォルダーの氏名・電話番号＝記録だけ」「同じフォルダーの秘密鍵・カード番号＝通知」「それ以外の場所の氏名・電話番号＝通知」の3群に規則を分ける。通常の通知規則が許可フォルダーにも適用されると、記録専用規則を追加しても通知は消えない。通知規則の対象範囲も分ける。

## 評価で比較する項目

公開情報からの候補は、Drive中心ならまずGoogle Workspace DLP、判定管理を重視するならNightfall、日本語の氏名・住所の標準仕様を重視するならPurviewも加える。ただしPurviewのDrive接続は公開試験版とPDF非対応が条件になる。Box中心なら通常分類とShield Proを別々に試す。

| 評価軸 | 同じ試験で測る内容 |
|---|---|
| 情報種別 | 氏名、電話、住所、メール、個人番号、口座、カード、秘密鍵を別々に採点 |
| 日本語表記 | 姓名の空白有無、異体字、ふりがな、全角数字、区切りのない電話、市外局番、住所の省略 |
| ファイル形式 | 同じ内容をDocs、Sheets、DOCX、XLSX、文字PDF、画像PDF、PNG、CSV、ZIPに入れて比較 |
| 精度 | 適合率・再現率を属性別・形式別に測る。文書分類と箇所抽出を別に採点 |
| 検査率 | 対象ファイルのうち検査済み・一部のみ・失敗・非対応を区別。未検査を陰性に数えない |
| 時間 | 作成・更新から検知記録まで、検知から通知までの中央値と95パーセンタイル |
| 許可運用 | 許可フォルダーでも検出が残ること、秘密鍵の追記だけは通知されること、移動後に再評価されること |
| 一覧の実用性 | 場所×属性×確認結果×日時で検索できるか。検出箇所・件数・検査版まで取得できるか |

これは評価設計であり実施済み試験ではない。試験用データには実在者の情報を使わず、合成値と正解箇所を用意する。公式試験用カード番号等を自動除外する製品もあるため、既知の試験値で検出しなかったことだけを見逃し率へ算入しない。

## 公式資料

既存の[G1–G4、B1–B3、M4、N1–N2、A1–A3](dlp_decision_and_alert_suppression_matrix_20261111.md#公開公式資料)に加え、以下の公開本文を確認した。

| 番号 | 資料 | 主な確認対象 |
|---|---|---|
| G5 | [About predefined content detectors](https://knowledge.workspace.google.com/admin/security/how-to-use-predefined-content-detectors) | 個人情報・日本の識別番号・資格情報、Sheetsの近接条件は同一セル内 |
| G6 | [DLP content and rule size limits](https://knowledge.workspace.google.com/admin/security/view-dlp-content-and-rule-size-limits) | Driveの容量・文字抽出・圧縮内の上限 |
| M7 | [DLP for non-Microsoft connected apps](https://learn.microsoft.com/en-us/purview/dlp-non-microsoft-connected-applications) | 公開試験版、Drive接続、親フォルダー、PDFと内容一覧の制約 |
| M8 | [Sensitive information type entity definitions](https://learn.microsoft.com/en-us/purview/sit-sensitive-information-type-entity-definitions) | 検知項目と信頼度の定義 |
| M9 | [All full names](https://learn.microsoft.com/en-us/purview/sit-defn-all-full-names) | 日本語の氏名検知 |
| M10 | [Japan physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-japan-physical-addresses) | 日本の住所検知 |
| M11 | [OCR in Microsoft Purview](https://learn.microsoft.com/en-us/purview/ocr-learn-about) | Microsoft 365側の対象形式・従量課金 |
| N5 | [Detector Glossary](https://help.nightfall.ai/detection_platform/detection_glossary) | 氏名・電話・住所・個人番号・秘密・文書分類、暗号化の存在検出 |
| N6 | [Detectors](https://help.nightfall.ai/detection_platform/detectors) | 検知方式と適合率90–95%の自社表明 |
| N7 | [Creating Custom Detectors](https://help.nightfall.ai/detection_platform/custom_detectors) | 独自語句・形式・自然言語指定の検知 |
| N8 | [File types scanned and limitations](https://help.nightfall.ai/detection_platform/faq/file_types_scanned) | 共通の対象形式、OCR、埋込み画像、1 GB上限 |
| N9 | [Supported File Types for API](https://help.nightfall.ai/developer-api/key-concepts/file_scan/supported_file_types) | 詳細な形式一覧。API仕様をDriveの全動作保証へ広げない |
| N10 | [Supported languages](https://help.nightfall.ai/faqs/supported_languages) | 英語の意味理解と個別学習済みの文脈、UTF-8との区別 |
| N11 | [Advanced Settings for Google Drive](https://help.nightfall.ai/google-drive/policies/advanced_settings) | 規則ごと・接続全体の通知設定 |
| N12 | [Scope for Google Drive](https://help.nightfall.ai/google-drive/policies/scope) | ドライブ・ファイル・ラベル等の範囲設定 |
| A4 | [Supported storage classes and formats](https://docs.aws.amazon.com/macie/latest/user/discovery-supported-storage.html) | S3のみ、対応形式と圧縮内の検査、画像非対応 |
| A5 | [Managed data identifiers by type](https://docs.aws.amazon.com/macie/latest/user/mdis-reference-quick.html) | 標準検出の種類と対象国 |
