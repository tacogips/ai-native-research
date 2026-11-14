# 日本の運転免許証画像の入手候補と学習方法

確認日：2026年11月13日。未認証で読める公開資料だけに基づく。架空・実在の双方を対象とし、画像中の氏名・住所・番号等の値は本稿へ転記しない。

## 入手候補

**日本の免許証画像を対象とする公開掲載候補として、Roboflow UniverseのJapanese Driving Licenseが見つかった。** 架空画像であることを条件とした前の調査結果と区別する。合成・実在の内訳や取得元の説明はなく、「架空データセット」とは呼ばない。

| 項目 | 公開ページで確認した内容 |
|---|---|
| 名称・提供者 | Japanese Driving License、Thang Nguyen |
| 一覧 | https://universe.roboflow.com/thang-nguyen-qhngn/japanese-driving-license |
| 公開表示の画像数 | 36枚。独立した36人物や36券面を意味するとは未確認 |
| 課題 | 物体検出。画像内の対象領域を四角い範囲として見つける課題 |
| 分類 | 13分類。氏名、住所、生年月日、免許番号、有効期限等 |
| 利用条件表示 | CC BY 4.0。提供者の表示であり、各画像の収集経緯・本人同意を確認したという意味ではない |
| 版 | 6個の版を掲載。番号はv2からv7 |
| v7 | 104画像。学習102・調整1・評価1。640×640への変換と、学習例ごとに3出力、明るさ・露出を各±20%変更すると説明 |
| v7配布画面 | https://universe.roboflow.com/thang-nguyen-qhngn/japanese-driving-license/dataset/7 |
| COCO形式の取得入口 | https://universe.roboflow.com/thang-nguyen-qhngn/japanese-driving-license/dataset/7/download/coco |

分類の原表記は`name`、`address`、`conditions`、`date-of-birth`、`delivery-date`、`first-issue-dates`、`issuing-authority`、`license-number`、`name-and-dob`、`residence`、`superior`、`valid-until`、`vehicle-category`。`superior`等の厳密な意味・分類の重なりは、画像と注釈を取得して確認する必要がある。

**36枚という元の掲載数と、画像加工後のv7の104枚を足し合わせない。** 104枚の独立資料を収集したという意味でもない。評価用が1枚のため、提供元の分割だけでは検知精度を十分に判断できない。文字列の正解や顔領域の正解まで含むかは未確認で、氏名等の位置検出と文字認識を混同しない。[一覧](https://universe.roboflow.com/thang-nguyen-qhngn/japanese-driving-license)、[v7の件数・加工条件](https://universe.roboflow.com/thang-nguyen-qhngn/japanese-driving-license/dataset/7)

### 入手方法と現在の到達点

Braveで未ログインの公開配布画面を開き、COCO JSONを選ぶと、ログインまたは無料アカウント作成の画面へ進むことを確認した。**画像一式のダウンロードと内容検査は未完了**。ログイン後の画面やアカウント固有の取得用情報は本稿の根拠に含めない。

入手する際は、v7の配布画面からCOCO JSONまたはYOLO形式を選択する。COCO JSONは画像・分類・対象領域をJSONに記録する形式で、YOLOは検出モデル向けの文字形式の注釈。Roboflowの一般的な書き出し手順は、形式を選んでZIPまたは取得用コードを使うもの。取得用コードにはアカウント固有の鍵が入る場合があるため、公開調査資料へは転載しない。[公式の書き出し説明](https://docs.roboflow.com/datasets/versions/dataset-versions/exporting-data.md)

取得後に確認する項目は、元券面・人物・画像の重複、各画像の出所、分類と範囲の正しさ、文字列の正解の有無、表裏・旧様式・撮影条件の内訳。学習と評価は元券面単位で分け、明るさだけを変えた同一画像を両方へ入れない。この段落は評価の設計案で、確認済みの品質を示すものではない。

### 追加候補：jpDL（419枚、カードの四隅の検出）

Braveの未認証の公開画面で、[jpDL / GPLX](https://universe.roboflow.com/gplx/jpdl)を確認した。419画像・5版、CC BY 4.0表示。4分類は`0top_left`、`1top_right`、`2bottom_left`、`3bottom_right`で、左上・右上・左下・右下の四隅を示す。氏名・住所の分類ではない。日本の免許証候補として関連表示され、公開標本のファイル名には`JapanGoldLicense`が含まれるが、全419枚の国・書類種類・人物・券面の独立性は未確認。提供元の説明文は未掲載。

取得入口は[版5](https://universe.roboflow.com/gplx/jpdl/dataset/5)。公開標本ページの「Download image」を押すとログインまたは無料アカウント作成の画面へ進んだ。画像本体は未取得で、419枚という一覧表示を加工後の版5の件数と同一視しない。実在・合成の内訳、注釈品質、元のJapanese Driving Licenseとの重複も未確認。

用途上は、Japanese Driving Licenseを氏名等の領域検出、jpDLをカード位置・四隅の検出の候補として区別する。両者の画像数を独立標本数として足さない。

## 他の候補の位置付け

| 候補 | 確認できること | 未確認のこと |
|---|---|---|
| [OpenKYC-JP](https://openkyc.me/engineering) | 日本の免許証等について、見本の透かし付きの架空券面を生成し、ぼけ・反射・回転・再撮影等で評価すると説明 | [コードは公開準備中](https://openkyc.me/status)。画像一式・生成器の公開取得先、画像の利用条件は未確認 |
| [UniDataの合成画像一覧](https://unidata.pro/datasets/dataset-type/synthetic/) | 日本の旅券と米国の運転免許証を掲載 | 日本の運転免許証の既製資料の販売は、この一覧からは確認できない |
| [Shaipの資料収集サービス](https://ja.shaip.com/offerings/data-collection/) | 運転免許証等の文書画像を提供すると案内 | 日本の免許証の在庫、件数、合成か実在か、価格、利用条件は未確認。既製の日本向け資料としては数えない |

## 公開事例に見る学習と認識の方法

以下は公開された研究・実装の例であり、日本の商用各社における採用率や学習画像の収集方法を示す統計ではない。今回確認した国内製品資料からは、学習画像の取得元・件数・合成画像の割合を特定できない。

| 方法 | 公開事例と確認できる範囲 |
|---|---|
| 学習済みモデルで追加学習せずに抽出 | [ABEJAの技術記事](https://tech-blog.abeja.asia/entry/local-secure-ocr-edge-grammar-structured-output-202603)は、画像と文章を扱う既存モデルで日本語・英語の免許証標本から氏名等を抽出する実験。主題は出力形式の制御で、大規模な文字認識精度の保証ではない |
| ひな形と架空属性から画像・正解を同時生成 | [DocXPand-25kの論文](https://arxiv.org/abs/2407.20662)と[生成コード](https://github.com/QuickSign/docxpand)は、架空の身分証24,994画像を扱う。氏名・日付・番号・顔等を生成し、背景画像へ配置。欧州系の架空様式で、日本の免許証の配布資料ではない。コードMIT、データCC BY-NC-SA 4.0を区別する |
| 合成画像で学習した後、実画像で追加学習 | [An End-to-End OCR-Free Solution For Identity Document Information Extraction](https://iris.unica.it/retrieve/8ead1786-cbb1-438c-9ae7-b2caa44d6f1c/1-s2.0-S1877050924024657-main.pdf)は、文書画像から直接項目を抽出するDonutモデルを二段階で追加学習する研究。[実装](https://github.com/SandroGT/SynthIDGenerator)はイタリアの身分証4種類を対象とし、日本向けの性能を示すものではない |
| 撮影条件の変化を合成して評価 | [OpenKYC-JP](https://openkyc.me/engineering)は日本の免許証等でぼけ・反射・回転・再撮影を利用した評価を説明。追加学習に使用したとは確認していない |
| 読み取り後の辞書・書式補正 | [PFU DynaEye](https://www.pfu.ricoh.com/dynaeye/product/dlocr/)は日本の免許証の印字幅・間隔への対応、氏名・住所辞書による補正を説明。これは学習データの公開ではなく、認識処理の構成例 |

合成資料が実画像を含まないとは一律に判断しない。DocXPandは顔を人工生成すると説明する一方、SynthIDGeneratorは公開された顔写真資料を使う。文字・顔・背景・券面それぞれの出所と条件を個別に確認する。

## 個人情報検知向けの利用案

免許証全体の送信を制御したい場合は「免許証の存在と位置」、項目別に伏せたい場合は「氏名・住所・番号等の位置」、値を照合したい場合は「文字列の読み取り」を別々に評価する。前者の成功だけで後二者の成功を主張しない。

初期候補は上記Roboflow資料の実体確認。その後、見本と明示した合成券面で書式・撮影条件を補い、実際の撮影画像で別途評価する設計が考えられる。合成画像での成績を実物での成績と読み替えず、文字認識・個人情報の位置検出・証明書の真正性を別の課題として扱う。

関連：[個人情報検知用データセット](pii_detection_public_datasets_20261111.md)、[画像・構造化資料等の追加候補](pii_related_datasets_expansion_20261016.md)。
