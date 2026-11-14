# 個人情報検知のための日本語と海外の公開データセット

確認日：2026年11月11日。

**日本語の検知試験は、Nemotron-PII-Japanの業務文書と、Sumiの評価用文書・未知書式・陰性例を組み合わせるのが第一候補になる。** 医療文書はMeddiesの日本語49,604件、多言語比較はOpenPIIとREDACTで追加できる。日本語を扱う直接候補7系統と、補助資料4系統、海外中心の参考6系統を整理した。派生資料は独立した新規データとして合算しない。

PIIは個人を識別する情報、注釈は検知対象と正解位置・種類などを付けた情報を指す。本稿の比較対象は「氏名や番号をどこからどこまで検知できるか」であり、各資料の分類名を日本法上の個人情報該当性や送信禁止の正解と同一視しない。

## 日本語の直接候補

件数は提供元の説明に基づく。公開説明と取得条件を確認し、データ全件の品質や検出器の性能は測定していない。「日本語あり」と「日本の住所・番号・業務表現に自然に対応している」は別に評価する。

| 優先 | データセット | 日本語の量と対象 | 正解情報と用途 | 利用条件と注意 |
|---|---|---|---|---|
| A | [NVIDIA Nemotron-PII-Japan](https://huggingface.co/datasets/nvidia/Nemotron-PII-Japan) | **日本語100,000文書**。医療・金融・行政・雇用・教育・法律・通信とIT・電子商取引の8分野、43文書種類、56分類 | 本文中の文字範囲と分類810,703箇所。和暦の生年月日、建物名・部屋番号付き住所、金融口座、マイナンバー等を含む合成業務文書 | CC BY 4.0。固定の学習・最終評価分割なし。**全件に注釈があるが、本文の全検知対象を網羅する注釈ではない**。注釈なしの箇所を一律に陰性とすると、正しい検知を誤検出として数えることがある |
| A | [NagaYu Sumi](https://huggingface.co/datasets/NagaYu/sumi-ja-pii-corpus) | **日本語18,020文書**。氏名・住所・電話・メール・生年月日・金融口座・カード・マイナンバー形式・会員番号・郵便番号の10分類 | 学習12,000、調整1,500、通常評価2,000、未知書式520、陰性2,000。文字範囲付き。一般名詞にもなる姓、電話に似た型番などの誤検出試験に向く | 全体CC BY-SA 4.0。合成部分CC0、元文章ごとの条件あり。**カードとマイナンバー形式は、検査数字を意図的に不正にしている** |
| B | [ai4privacy OpenPII 1.5M](https://huggingface.co/datasets/ai4privacy/pii-masking-openpii-1.5m) | 全体1,636,375件、**日本語を含む30言語**、19分類。原版の日本語件数は本調査では確定しない | `privacy_mask`に文字範囲と分類、`masked_text`に置換後本文。学習と検証の2分割。国・言語をまたぐ氏名、住所、電話、カード等の試験 | 提供元本文はCC BY 4.0。`language`列で日本語を抽出後、実際の本文言語と日本の書式を点検する。旧400k版とは条件が違う |
| B 条件付き | [Meddies PII](https://huggingface.co/datasets/Meddies/meddies-pii) | **`japanese`構成49,604件**。17言語の合成医療・事務文書系列の一部 | 日本語構成は、注釈付き`text`、注釈なし`raw`、値を種類別にまとめた`label`。氏名・住所・日付・電話・メール・組織・識別番号の7分類 | **CC BY-NC 4.0、非商用条件**。企業での検証も非商用と自動判断しない。文字範囲形式の`pii-bioes`は9分類の別の派生構成で、日本語構成と混同しない |
| B 条件付き | [REDACT](https://github.com/guneeshvats/REDACT-PII-Benchmark) | 全体13,427件、51分類、**日本語を含む25言語**。各言語453〜621件。固定評価集合では日本語40件 | 文字範囲・分類に加え、完全な値か部分開示かなどの情報を保持。外国語混在や書き方の違いを比較する合成資料 | [独自データ規約](https://github.com/guneeshvats/REDACT-PII-Benchmark/blob/main/DATASET_TERMS.md)。防御用の検知器の開発・試験を許可し、再配布時の規約保持・出所表示等を要求。**コードのMITをデータへ適用しない**。Hugging Faceの生README取得は401で、今回の条件確認は公開GitHubによる |
| B | [sumeshi privacy-filter-jp-datasets](https://github.com/sumeshi/privacy-filter-jp-datasets) | 日本語の人工例と生成器。日付・識別番号、メール・電話等、抽出境界の例 | 読み仮名、敬称、電話書式、日本固有番号、紛らわしい陰性例等を生成するコード。確認時のファイル一覧で公開済みを確認できた合成JSONLは**3ファイル** | リポジトリ内の配布対象合成JSONLはMIT。READMEが挙げる人物・電話番号・陰性の追加ファイルは、確認時のGit一覧にはなく、**公開済みの件数として数えない**。住所・長文文書は再生成が必要 |
| C 派生資料 | [akiFQC japanese-confidential-information-extraction-sft](https://huggingface.co/datasets/akiFQC/japanese-confidential-information-extraction-sft) | **日本語40,897行**。学習38,852、検証2,045。個人情報に加えて財務情報・構成情報・取引番号等の11分類 | 入力文章と、抽出する値の一覧をJSONで答える会話形式。文章から値を抽出する生成モデルの比較に向く | 元資料別の条件を継承。OpenPII、Wikipedia NER、追加合成の混合であり、独立した40,897件の新規PII評価集ではない。文字位置の正解は直接提供する形式ではない |

ここでAは最初に採用する候補、Bは用途や条件に応じて追加する候補、Cは派生関係を管理して利用する候補という選定案。

### NemotronとSumiを組み合わせる理由

Nemotron-PII-Japanは業務分野の広さ、Sumiは誤検出と未知の文章形式を調べる構成が強みになる。Nemotronだけで誤検出率を決めず、Sumiの陰性2,000件も別に測定する。Nemotronの未注釈箇所への検知は、人手で正誤を確かめる対象にする。

Sumiでは、カード等の末尾に付ける誤り確認用の数字が不正な例を使っている。そのため「カードらしい形を検知する試験」と「検査数字まで正しい番号だけを検知する試験」の期待値を分ける。[Sumiの説明](https://huggingface.co/datasets/NagaYu/sumi-ja-pii-corpus)

Nemotronの公式発表は2026年11月9日で、既存の10月16日の調査には含まれていない。固定の最終評価分割がなく、文書同士の類似もあるため、学習にも使う場合は乱数による行分割だけでなく、文書種類・ひな形・人物の重複を確認する。[公式発表](https://huggingface.co/blog/nvidia/nemotron-pii-japan)、[配布説明](https://huggingface.co/datasets/nvidia/Nemotron-PII-Japan)

### 日本語部分の取得と正解形式

| 資料 | 取得する部分 | 正解形式で確認すること |
|---|---|---|
| Nemotron-PII-Japan | 単一の`data.parquet`に100,000件 | `spans`は注釈を埋め込む前の`text`の文字位置。`text_tagged`の位置と混ぜない |
| Sumi | `test`、`ood`、`negatives`を個別に利用 | `spans`はJSON文字列。文字の互換正規化であるNFKC処理後の位置、先頭0、終端を含まない範囲 |
| OpenPII | `language`列の日本語行を抽出 | `privacy_mask`と本文の一致。`ja`指定で英語本文だった例が既存調査にあるため、抽出後の言語確認も必要 |
| Meddies | `japanese`構成 | `raw`が入力本文。`text`は答えの種類が埋め込まれており、そのまま検知器へ渡さない。値の一覧から位置を復元する場合は、同じ値の複数出現を区別 |
| REDACT | 全体版か固定1,000件版から日本語を抽出 | 固定版は全体版に含まれる。同じ行を学習と評価に重複させない。40件だけで日本語全体の精度を判断しない |
| sumeshi | Gitで配布済みの3ファイルか、必要な生成器 | 生成例と手作成の評価例を分離。READMEの生成数は、実際に配布されている行数ではない |
| akiFQC | 入力の会話要素と抽出答えを分離 | OpenPIIやStockmarkを学習に使ったモデルの独立評価には、同じ元資料の行を含めない |

OpenPIIの日本語行数について、akiFQCは加工後の約20,754行を挙げている。この数字を原版全体の日本語件数として転記しない。[派生版の出所説明](https://huggingface.co/datasets/akiFQC/japanese-confidential-information-extraction-sft)

## 日本語を増やすための補助資料

NERは、氏名・組織名・地名などの固有表現の位置や種類を抽出する処理。以下は氏名等の抽出を調べる補助候補で、口座・カード・病歴等を網羅した個人情報検知の正解集には数えない。

| 候補 | 日本語の量と内容 | 条件と使える範囲 |
|---|---|---|
| [Stockmark ner-wikipedia-dataset](https://github.com/stockmarkteam/ner-wikipedia-dataset) | **5,343文**、8分類、約10%が固有表現なし | CC BY-SA 3.0。公開人物名・地名・組織名の範囲抽出と誤検出の補助。`llm-book`等の再配布版も同じ元資料として扱う |
| [WikiANN 日本語](https://huggingface.co/datasets/unimelb-nlp/wikiann) | **学習20,000・検証10,000・評価10,000の計40,000例**。人物・組織・地名 | 自動付与された正解。配布説明の利用条件表示は`unknown`で、商用検証の初期候補から外す。語の列に対する正解で、原文の全PII範囲ではない |
| [KWDLC](https://github.com/ku-nlp/KWDLC) | **約5,000文書、15,000文**。ウェブ文書冒頭3文、人手修正を含む固有表現・構文等の注釈 | 研究用の提供説明と権利者からの訂正・削除への対応条件を確認。包括的な商用許諾が明示された合成資料とは分ける |
| [SHINRA 森羅の属性値抽出](https://shinra-project.info/shinra/data/) | 日本語Wikipediaの記事分類・属性抽出。人物の生年月日・所属など、複数の属性を扱う補助 | CC BY-SA 3.0。分類用データ、属性抽出の教師データ、他システムの出力を区別する。文書中の全PIIや秘匿要否の正解ではない |

## 海外中心の参考データセット

| データセット | 言語と規模 | 向く試験 | 利用条件と注意 |
|---|---|---|---|
| [NVIDIA Nemotron-PII](https://huggingface.co/datasets/nvidia/Nemotron-PII) | **公開APIは学習100,000・評価100,000の計200,000行**。英語、55以上の分類 | 金融・医療・認証情報を含む合成文書。構造化書式と自由文、文字範囲の抽出 | CC BY 4.0。**READMEの計100,000件、学習50,000・評価50,000という説明と現在の配布件数が不一致**。採用版を固定し、重複を別途調べる |
| [Gretel synthetic_pii_finance_multilingual](https://huggingface.co/datasets/gretelai/synthetic_pii_finance_multilingual) | **55,940件**、英語・スペイン語・スウェーデン語・ドイツ語・イタリア語・オランダ語・フランス語、日本語なし。29分類 | カード番号・確認コード、国際銀行口座番号IBAN、国内銀行口座番号BBANなどの金融文書 | Apache 2.0。**公開APIは学習50,346・評価5,594**で、READMEの50,776・5,164とは不一致。注釈の誤りが残る可能性も説明 |
| [Gretel gretel-pii-masking-en-v1](https://huggingface.co/datasets/gretelai/gretel-pii-masking-en-v1) | **英語60,000件**。学習50,000・検証5,000・評価5,000 | 金融・医療・技術等、複数業界の合成文書。氏名、各種番号、認証用の鍵等の種類を比較 | Apache 2.0。`uid`などの出所情報を残し、派生資料と重複させない |
| [TonicAI Privacy-Bench](https://huggingface.co/datasets/TonicAI/Privacy-Bench) | **英語中心の合成18,040メッセージと357補助文書**。21人を中心とする別々の業務環境 | メール、Slack、PDF、Word、Excel、CSV。文字抽出から検知、同一人物に整合する値への置換までの試験 | CC BY 4.0。10分類、130,370の位置注釈を案内し、人手確認版もある。ファイルごとに位置の表現が異なる。全体評価に生成モデルによる採点が含まれるため、検知だけなら該当部分を切り出す |
| [Text Anonymization Benchmark TAB](https://github.com/NorskRegnesentral/text-anonymization-benchmark) | **英語の実判決1,268件** | 人手注釈。氏名等の直接識別に加え、組み合わせによる間接識別、同じ人物への言及、隠す必要の判断 | MIT表記。合成資料ではない。匿名化する対象者を指定する課題で、全人物の個人情報をすべて伏せる課題とは異なる |
| [DocPII redaction benchmark](https://huggingface.co/datasets/nutrientdocs/DocPII-redaction-benchmark) | **英語合成1,101件** | 文書と、伏せる値・種類・指示を使った検知や伏字化の試験 | MIT表記。Gretel由来の派生資料。検知する文字列の一覧であり、画像やPDFの矩形の正解集ではない。元資料を学習に使った場合は重複を確認 |

件数の照合先：[Nemotronの公開件数API](https://datasets-server.huggingface.co/size?dataset=nvidia/Nemotron-PII)、[Gretel金融の公開件数API](https://datasets-server.huggingface.co/size?dataset=gretelai/synthetic_pii_finance_multilingual)。API上の行数は独立文書数や学習・評価間の非重複を保証しない。

## 採用を保留する資料

| 候補 | 保留する理由 |
|---|---|
| [ai4privacy pii-masking-400k](https://huggingface.co/datasets/ai4privacy/pii-masking-400k) | 日本語なしの旧系列。[独自ライセンス](https://huggingface.co/datasets/ai4privacy/pii-masking-400k/blob/main/LICENSE)は学術・非商用限定で、再配布・派生成果の提供等に別途書面許諾を要求。新OpenPIIのCC BY 4.0を流用しない |
| [UniDataPro synthetic-printed-japanese-passports](https://huggingface.co/datasets/UniDataPro/synthetic-printed-japanese-passports) | 合成日本旅券画像。説明の全体5,000枚以上に対し、公開画面は96行。CC BY-NC-ND 4.0で非商用・改変物の共有制限あり。公開分の網羅的な個人情報位置正解を確認できず、5,000枚の即利用可能な検知評価集とは数えない |
| [opf-text-masking-demo](https://github.com/gghatano/opf-text-masking-demo) | 公開報告は合成日本語300文書を用いるが、READMEでは`data/`をGit管理外・再生成可能と説明。配布済みの300件と利用許諾を確認できず、生成手順の参考にとどめる |
| [Detecting Sensitive Personal Information in Japanese Pre-Training Corpora for Large Language Models](https://arxiv.org/html/2606.12114v1) | 日本語の要配慮情報の分類研究として関連するが、論文中のデータ作成説明だけで、検証用データ本体の公開取得先・利用条件が揃った候補とは扱わない |

## 要配慮個人情報の検知に使える資料

追記確認日：2026年11月13日。

**要配慮個人情報に相当する内容を含む資料はあるが、日本法に沿う分類・文字位置・対象人物の正解が揃った評価集とは区別する。** 個人情報保護法の対象は生存する個人に関する情報であり、完全に架空で実在人物に結び付かない合成情報は、通常それ自体が法的な個人情報には当たらない。以下の合成資料は、要配慮個人情報の検知試験を作るための素材として扱う。これは法の定義を資料へ当てはめた整理であり、提供元による日本法適合の認定ではない。[個人情報保護委員会・通則編の2-1、2-3](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)

要配慮個人情報には、人種、信条、社会的身分、病歴、犯罪歴、犯罪被害の事実のほか、政令で定める障害、健康診断結果、診療・調剤等に関する事実などが含まれる。病名の一般的な解説と、識別できる本人の病歴を区別する。公開された情報であることだけで、個人情報や要配慮個人情報に該当しなくなるわけではない。[個人情報保護委員会・通則編](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)

| 資料 | 要配慮個人情報との関係 | 既存の正解と追加確認 |
|---|---|---|
| [Meddies PII](https://huggingface.co/datasets/Meddies/meddies-pii) | 日本語を含む合成医療・事務文書。診療・投薬等の記述を評価する候補 | 日本語構成の既存7分類は氏名・住所・日付等で、病歴・診療内容そのものの正解を保証しない。日本語本文を確認し、病歴等の範囲と対象人物を追加注釈する案。CC BY-NC 4.0の条件確認が必要 |
| [Synthea](https://synthetichealth.github.io/synthea/) | 架空の患者について病歴・投薬・受診等を持つ構造化記録。配布済みの標本と生成器がある | 人物と医療情報を結び付ける試験の素材。日本語の文章中の検知位置の正解集ではない。日本語化や文章化を行う場合は追加作業として記録する |
| [TAB](https://github.com/NorskRegnesentral/text-anonymization-benchmark) | 英語の実際の判決文に、信条・人種や民族的出自・健康等の機微な属性を注釈する仕組みがある | `confidential_status`は日本法の分類ではない。個々の記述を日本法の対象へ対応付ける必要がある。実文書だが、全人物・全種類の要配慮個人情報を網羅する正解集とは扱わない |

TABの注釈指針には`BELIEF`、`POLITICS`、`SEX`、`ETHNIC`、`HEALTH`がある。政治・性的事項等を含む提供元の機微情報分類全体を、日本法の要配慮個人情報へ一括で読み替えない。[TAB注釈指針](https://github.com/NorskRegnesentral/text-anonymization-benchmark/blob/master/guidelines.md)

日本語の初期評価案は、利用条件を満たすMeddiesの文書を確認し、病歴・診療・調剤等について「該当する記述の範囲」「誰に関する記述か」「日本法のどの項目に対応するか」を追加する方法。氏名・患者番号の抽出率と、本人に結び付く医療情報の見逃しを別に測る。一般的な医学解説や否定された病歴等も誤警告確認用に分ける。これは追加評価の設計案であり、全件確認・追加注釈・精度測定は未実施。

## 日本の運転免許証画像の公開状況

追記確認日：2026年11月13日。**架空・実在の双方を対象とする追加調査で、[Japanese Driving License](https://universe.roboflow.com/thang-nguyen-qhngn/japanese-driving-license)の公開掲載を確認した。** 36枚・13分類、CC BY 4.0表記。加工後の[v7](https://universe.roboflow.com/thang-nguyen-qhngn/japanese-driving-license/dataset/7)は104枚で、元の掲載数と加算しない。追加候補の[jpDL](https://universe.roboflow.com/gplx/jpdl)は419枚・四隅の4分類、CC BY 4.0表記で、氏名等の項目検出とは用途が異なる。合成・実在の内訳や両資料の重複は未確認であり、架空画像と断定しない。配布入口を確認したが、画像一式の取得・品質検査は未完了。[入手候補・手順と学習方法の詳細](japan_driver_license_datasets_and_training_20261113.md)へ保存した。架空であることと公開取得先・利用条件が揃った候補は、引き続き未確認。

[OpenKYC-JPの技術説明](https://openkyc.me/engineering)には、公的な見本をもとに日本の運転免許証等の架空券面を作る生成器を作成したとの記載がある。氏名・住所は架空で「見本」の透かしを入れ、ぼけ・反射・回転・画面や印刷の再撮影等の条件を加えて評価すると説明している。ただし、[公開状況の説明](https://openkyc.me/status)ではソースコードはGitHubで公開準備中。画像本体・生成器の公開取得先、配布件数、画像の利用条件、検知位置の正解を今回確認できず、配布済みのデータセットとしては数えない。Apache License 2.0で公開するという予定を、未確認の画像一式の許諾として扱わない。

近接候補として[UniDataの合成画像一覧](https://unidata.pro/datasets/dataset-type/synthetic/)には日本の旅券と米国の運転免許証があるが、いずれも日本の運転免許証の代替としては数えない。日本旅券の公開標本と利用条件は上の採用保留表を参照。

日本向けに評価資料を作る場合は、見本と明示した架空券面に対して、氏名・住所・生年月日・番号・顔領域の正解と、傾き・反射・ぼけ等の撮影条件を管理する案がある。これは追加作成の設計案であり、既存の公開データセットの紹介や作成済みとの報告ではない。画像中の個人情報検知・文字認識と、証明書の真正性の評価を区別する。

## 最初の評価を組む案

検出器の学習済みモデル名・版と追加学習に使った資料を記録し、評価集合に同じ元文書や派生版が混ざっていないか確認する。既にSumiやOpenPIIで追加学習した検出器なら、その同系列の評価結果を未知資料での結果と同じ扱いにしない。

| 試験群 | 初期に使う量の案 | 測ること |
|---|---|---|
| 日本語の基礎検知 | Sumi `test` 2,000件 | 種類別の見逃し、正解との文字範囲一致 |
| 未知の文章形式 | Sumi `ood` 520件 | 業務ひな形を外れた文章への対応 |
| 誤検出 | Sumi `negatives` 2,000件 | 検知対象のない文書に警告した割合、1,000文書あたりの誤警告数 |
| 分野ごとの業務文書 | Nemotron-PII-Japanから8分野を各100件、計800件 | 分野別の見逃し。未注釈箇所への検知は人手で確認 |
| 医療 | 利用条件を満たす場合にMeddies日本語から500件 | 診療文書の氏名・日付・識別番号。値の抽出と位置復元を分けて測る |
| 言語・書式の比較 | REDACT固定版の日本語40件と他言語 | 言語混在、部分的な開示、種類別の傾向。小規模な確認として扱う |
| 外国の金融文書 | Gretel金融の評価集合から500件 | IBAN・カード・金融口座等。日本語の口座評価とは分ける |

この件数は評価構成の提案であり、精度を保証するために必要な標本数の算定結果ではない。調整に使った資料は最終評価から分ける。

測定では、次を別々に残す。

- **再現率**：正解のうち何割を拾えたか。種類・言語・文書種類ごとに分ける。
- **適合率**：警告のうち何割が正しかったか。注釈が網羅的でない資料は、追加の人手確認が必要。
- **文字範囲の一致**：種類と範囲の完全一致に加え、正解範囲の何割が隠れたかを測る。氏名の一部だけの伏字を成功として扱わない。
- **文書単位の取り残し**：一つでも対象情報が残った文書の割合。
- **誤警告**：対象情報がない文書への警告率。陽性例ばかりで評価しない。

日本語の試験では、全角・半角、ハイフン・空白、和暦、読み仮名、姓名の分割、敬称、同姓の地名、改行、表、文字認識の誤りを加える。元の正解位置を流用せず、加工後に位置を計算し直す。Pythonの文字位置、GoのUTF-8のバイト位置、C#のUTF-16の位置は同じ数値とは限らない。

## 関連調査と出典記録

2026年11月13日追記：[個人情報22項目のデータセットと作成方法](personal_information_dataset_creation_methods_20261113.md)では、氏名・連絡先・識別番号・証明書・支払情報・経歴・家族・各種履歴・要配慮情報を、複数の文章・画像・表で組み合わせて評価する案を整理した。既存資料が持つ内容と、追加作成・注釈が必要な範囲を分けている。

- [2026年10月16日の公開試験資料調査](pii_test_and_development_data_20261016.md)：公式テストカード・日本向け試験口座・Faker等の生成器。
- [関連データセットの拡張調査](pii_related_datasets_expansion_20261016.md)：認証情報、画像、表形式等の補助候補。
- [今回の出典確認記録](pii_detection_public_dataset_sources_20261111.json)：公開URL、取得結果、説明資料のハッシュ値。大規模データ本体を再配布するものではない。
