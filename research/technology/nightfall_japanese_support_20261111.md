# Nightfallの日本語検知対応と採用上の制約

調査日：2026年11月11日。[製品横断の詳細比較](dlp_detection_formats_accuracy_matrix_20261111.md)から日本語の適用条件を掘り下げた。[公式資料18件の取得記録](nightfall_japanese_sources_20261111.json)には公開URL、取得日時、原文のハッシュ、短い根拠抜粋を保存した。製品の実機試験は含めない。

**Nightfallを「日本語の個人情報全般に標準対応」と評価する根拠は不足している。日本向けに明示されたマイナンバー検知、日本語文字列を扱う独自規則、国を限定しない電話番号検知は確認できる。一方、日本語氏名・住所・機密文書分類・画像の文字読取りの精度は未確認である。** 特に、AIによる独自の箇所抽出には検出文字列の長さの下限があり、従来の氏名検知の不足を当然に補えるとは言えない。

## 日本語対応の判定表

「仕様あり」は検知器の存在・入力受付の説明を指し、精度の実測保証ではない。「未確認」は非対応の断定ではなく、導入条件として保証できない状態を指す。識別子は公式表記。

| 対象 | 標準機能の公開仕様 | 日本語での評価 | 採用時に残る制約 |
|---|---|---|---|
| UTF-8の日本語文字 | 独自検知器はUTF-8文字を扱う [S1] | 文字列の受付・形式規則の対象として利用可能 | 日本語の意味理解とは別。異体字・全半角の同一視は未確認 |
| 氏名 | `PERSON_NAME`は姓名等を検出 [S2] | 日本語の漢字・かな氏名を標準対応とする記載は未確認 | 言語FAQは英語または個別学習済みの文脈に意味理解を限定。英語氏名の検出成功を日本語へ拡張しない [S1] |
| 住所 | `STREET_ADDRESS`は英語圏データで学習。英語・スペイン語・フランス語の地名接尾辞を説明 [S2] | 日本語住所への対応は未確認 | 丁目・番地・建物名・住所省略・縦書きは別途評価 |
| 電話番号 | `PHONE_NUMBER`は任意の国の番号、市外局番・国番号を扱う [S2] | 日本の電話番号も対象と読むことはできるが、表記別の精度は未確認 | 国内表記、区切りなし、全角、括弧、内線、国番号形式を分けて試す |
| メール | `EMAIL_ADDRESS`を提供 [S2] | 一般的なメール形式の検知候補 | 日本語を含む国際化メールアドレスの扱いは未確認 |
| マイナンバー | `JAPAN_MY_NUMBER`を明示 [S2] | 日本固有の標準検知器として確認済み | 全角、区切り、検査数字、法人番号との区別、日本語の周辺語句は説明不足 |
| 日本の免許・旅券・口座番号 | 今回取得した標準一覧では日本専用の番号検知を確認できず [S2] | 標準対応としては採点しない | 「各国の証明書画像を分類」と、番号の箇所検知・正当性検証を混同しない |
| API鍵・秘密鍵 | `API_KEY`、`CRYPTOGRAPHIC_KEY`等 [S2] | 日本語文書内の既知形式の鍵を検出する候補 | 文書全体の言語理解を必要としない種類と、日本語の周辺文脈依存の種類を区別 |
| パスワード | `PASSWORD_IN_CODE`はコードと自然文中のパスワードを対象 [S2] | 日本語の「パスワードは…」の理解は未確認 | 既知形式の鍵の対応から自然文パスワードの対応を推定しない |
| 日本語の契約書・機密文書 | 標準文書分類と自然言語で定義する独自文書分類 [S3,S5] | 日本語の対応言語・評価値は未確認 | 分類ができても氏名・電話の全箇所を列挙できることにはならない |
| 日本語の画像・画像PDF | OCR（画像からの文字読取り）を提供 [S10] | 日本語OCR、縦書き・手書きの対応仕様と精度は未確認 | 読取りが失敗すると、その後の文字列検知も失敗し得る |
| 管理画面・日本語窓口 | 今回の公開操作資料では日本語版の提供を確認できず | 未確認 | 日本語を入力できることと、画面・問い合わせ対応の日本語化を分ける |

同じ文字列でも人名・地名・製品名などで意味が変わる。UTF-8対応や漢字に一致する正規表現だけでは、未知の日本語氏名を一般的に識別できるとは評価しない。

## 従来の言語FAQと新しいAI検知の関係

### 言語FAQが明示する範囲

公式FAQは、数値・英数字の検知では地域に対応する言語の文脈を学習させる場合があるとし、ブラジルCPFのポルトガル語・英語を例示する。一方、英語または個別に学習済みの場合を除き、文字の意味を理解しないと説明する。日本語氏名を対応対象として挙げてはいない。[S1]

これは従来型の標準検知器に関する有力な制約だが、新しい大規模言語モデルを使う全機能まで「英語以外は一切動かない」と断定する根拠にはしない。

### 新しいAI機能にも日本語の保証はない

自然言語で指定する箇所検知と文書分類は、説明・例・紛らわしい陰性例などを用いて判定する。前者は文字列の箇所を探し、後者は文書全体の種類を判定する。どちらの操作仕様も、今回確認した本文に日本語の対応言語一覧や日本語評価結果を示していない。[S4,S5]

箇所検知の仕様は、説明文600文字まで、検出文字列6〜128文字、関連語句を少なくとも1つ指定することを要求する。**仕様を文字数どおりに読むと、4文字の合成氏名「山田太郎」は下限を満たさない。** Unicode文字・バイト等の数え方や、周辺の「氏名：」も含めて検出させた場合の抽出境界は未確認である。したがって、短い日本語氏名の解決策として無条件に採用しない。[S4]

両機能の説明は、対象をファイル・添付・メール本文に限定し、メッセージと項目単位の検査は2026年に追加予定とする。調査日が2026年であっても、その一文だけで提供済みとは判断しない。[S4,S5]

### 更新履歴で補強できる点とできない点

| 時期 | 公式の変更説明 | 日本語対応について判断できること |
|---|---|---|
| 2024年1月 | ブラジル・ポルトガル・メキシコ等の合成人名、スペイン語・ポルトガル語住所の改善 [S14] | 英語以外の一部改善は確認。日本語への改善とは書かれていない |
| 2025年4月 | 氏名・住所・生年月日の検知へ、人の判定を使って再学習する仕組みを追加 [S13] | 判定がモデル改善に使われる説明はあるが、日本語の新規対応・精度保証ではない |
| 2025年11月 | 意味に基づく文書分類と自然言語指定の箇所検知を説明 [S13] | 新機能の存在は確認。日本語氏名・住所対応の根拠には不足 |
| 取得した2026年変更履歴 | 10月までの更新を含む [S13] | 今回確認した履歴では日本語全般への対応宣言は見つからない |

現在の住所一覧は英語・スペイン語・フランス語を挙げる一方、2024年履歴はポルトガル語も挙げる。記載の範囲が一致しないため、一覧からの欠落を機能廃止と解釈しない。日本語についても検索結果の不在だけで非対応とは断定しない。

## 独自規則で補える範囲

| 方法 | 日本語への使い方の案 | 限界 |
|---|---|---|
| 辞書 | 許可を得た試験用の氏名・社内固有語句を登録して一致を探す [S7] | 未登録の人名の発見にはならない。表記揺れの自動吸収は未確認 |
| 正規表現 | 電話番号・顧客番号・個人番号候補など、既知の形を探す [S1,S6] | 数字の形だけでは識別できない誤検知と、日本語の意味判断が残る |
| 周辺語句による調整 | 「電話」「連絡先」「住所」等を条件に信頼度を調整する構成案 [S6,S9] | 元の検知で候補が出ないものを、日本語の語句追加だけで発見できるとは限らない |
| 既存検知器の拡張 | 標準検知器へ周辺語句・除外条件を付ける [S8] | 日本語の氏名モデルを追加学習する操作と同義ではない |
| AIによる独自分類 | 日本語の例と陰性例で試し、適合率と再現率を測る [S4,S5] | 日本語の明示対応・短い箇所の抽出・継続性能を保証しない |

**「検知記録は残して警告だけ止める」用途では、検知器の除外条件を使わない。** 除外条件は検出箇所自体を結果から外す。場所と属性で通知方針を分け、許可された情報も検知台帳に残す構成を試験する。[S6] [通知・判定の比較](dlp_decision_and_alert_suppression_matrix_20261111.md)

## Google Driveとファイル形式

Driveの継続検知・履歴検査、規則の選択は確認できるが、接続対応は日本語分類の品質証明ではない。[S15,S16]

| 入力 | 共通仕様での対応 | 日本語について別に検証する点 |
|---|---|---|
| Docs・Sheets・Slides、Word・Excel・PowerPoint | 検査対象 [S10] | 文字抽出と検出器の精度。表の列見出し・別セルの氏名との関係 |
| 文字付きPDF・TXT・CSV・JSON等 | 検査対象 [S10] | 文字コード、改行、抽出順序、全角、正規化 |
| PNG・JPEG・TIFF、埋込み画像、画像PDF | OCRを使った検査を説明 [S10,S11] | 漢字・かな、縦書き・手書き、画質別の読取りとその後の検知 |
| ZIP・gzip等 | 展開して内部を検査 [S10] | 内部形式、展開上限、個々の失敗の可視化 |

共通の最大容量は1 GBと説明されるが、Drive接続の展開後容量・OCR対象量・文字抽出上限・処理時間の個別保証は未確認である。APIにはバイト位置と文字位置、表の行列情報を返す例があるが、Drive画面で日本語の全検出箇所が同様に取得できるとの保証には広げない。[S10,S17,S18]

OCRの技術文書は文字の取り違え、余分な改行・記号を明記し、参考として85〜98%の文字単位の精度に言及する。しかし日本語の評価条件・試験データは示されない。この数値を日本語OCRの精度や個人情報検知の再現率として引用しない。[S11]

## 精度と評価条件

公式の検知器紹介は適合率90〜95%を表明するが、日本語・属性・形式別の内訳は確認できない。箇所検知の設定確認には75%以上の適合率という説明もあるが、これも自社の日本語文書に対する独立した精度保証ではない。文書分類側の75%は信頼度の説明を含み、同じ指標として比較しない。[S3–S5]

標準一覧は氏名・電話・メール等について、他の検知器との組合せまたは検出数10件以上を勧める。ただしこれは最低10件でないと使えないという仕様ではない。少数件を見つけたい目的で安易に閾値を上げると、見つけるべき1件を通知対象から外してしまう。[S2]

| 評価群 | 試験する条件 | 記録する結果 |
|---|---|---|
| 氏名 | 合成した2〜5文字・6文字以上、姓名間の空白有無、漢字・ひらがな・カタカナ・ローマ字 | 標準検知と独自検知を別々に採点。未検出・余分な抽出範囲 |
| 住所 | 合成の都道府県〜建物名、丁目・番地、省略、改行 | 住所全体・部分だけの検出を分ける |
| 数値属性 | 国内・国際電話形式、全角数字、区切り、試験用個人番号と紛らわしい顧客番号 | 適合率、再現率、検査数字と周辺語句の影響 |
| 文書・画像 | 同じ内容をDocs、Sheets、DOCX、XLSX、文字PDF、画像PDF、PNGに配置 | 文字抽出、OCR、検知のどこで失敗したか |
| 許可運用 | 指定場所の氏名・電話は記録のみ、別の秘密鍵を追記、別場所へ移動 | 検知台帳が残ること、新たな違反だけ通知されること |

提供者への確認事項は、日本語対応の検知器・版・言語別評価、短い氏名の処理、OCRの日本語・縦書き・手書き対応、文字数と正規化の定義、Driveでの個別機能の提供範囲である。現状の公開仕様に基づく採用評価は、**既知形式の数字・鍵と独自規則は試験候補、日本語の氏名・住所を網羅的に自動発見する用途は採用根拠が未充足**とする。

## 公式資料

| 番号 | 資料 |
|---|---|
| S1 | [Which languages does Nightfall support?](https://help.nightfall.ai/faqs/supported_languages) |
| S2 | [Nightfall Detector Glossary](https://help.nightfall.ai/detection_platform/detection_glossary) |
| S3 | [Detectors](https://help.nightfall.ai/detection_platform/detectors) |
| S4 | [Create an Entity Detector using a Prompt](https://help.nightfall.ai/detection_platform/custom_detectors/create-an-entity-detector-using-a-prompt) |
| S5 | [Create a Prompt-based File Classifier](https://help.nightfall.ai/detection_platform/custom_detectors/create-a-prompt-based-file-classifier) |
| S6 | [Create Regular Expression Detector](https://help.nightfall.ai/detection_platform/custom_detectors/regexp_detector) |
| S7 | [Creating Dictionary Detector](https://help.nightfall.ai/detection_platform/custom_detectors/dictionary_detector) |
| S8 | [Extend a Nightfall Detector](https://help.nightfall.ai/detection_platform/custom_detectors/extend_nightfall_detector) |
| S9 | [How do I use Context Rules?](https://help.nightfall.ai/detection_platform/faq/context_rules) |
| S10 | [File types scanned and limitations](https://help.nightfall.ai/detection_platform/faq/file_types_scanned) |
| S11 | [Scanning Images using Custom Regex Detectors](https://help.nightfall.ai/developer-api/key-concepts/scanning_features/pre_configured_detection_rules/scanning-images-for-patterns-using-custom-regex-detectors) |
| S12 | [Using Context Rules in API](https://help.nightfall.ai/developer-api/key-concepts/scanning_features/context_rules) |
| S13 | [Release Notes 2025–2026](https://help.nightfall.ai/release_notes/nightfall_new_features) |
| S14 | [Release Notes 2021–2024](https://help.nightfall.ai/release_notes/release_notes_old) |
| S15 | [Getting Started for Google Drive](https://help.nightfall.ai/google-drive/getting_started) |
| S16 | [Detection Rules for Google Drive](https://help.nightfall.ai/google-drive/policies/detection_rules) |
| S17 | [Special File Types](https://help.nightfall.ai/developer-api/key-concepts/file_scan/special_file_types) |
| S18 | [Supported File Types for API](https://help.nightfall.ai/developer-api/key-concepts/file_scan/supported_file_types) |
