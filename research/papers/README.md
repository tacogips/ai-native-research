# 引用論文の取得台帳と日本語解説

2026年10月5〜7日に、引用されたarXiv論文を重複を除いて185本取得した。合計4,407頁、約303.4 MiB。全件でPDFの形式、本文抽出、容量、SHA-256を確認した。

各解説は取得したPDFの要旨と本文の手法・結果・議論の関連箇所に基づく。全付録の精読と実験の再現は行っていない。著者の主張、評価条件・限界、企業設計への解釈を分けた。

PDF原本と抽出本文、全頁にOCR（画像の文字認識）を実行した検索可能なPDFと認識本文は、この作業環境の `arxiv/論文ID/` に保存する。PDF・本文・処理ログはGit管理から除外し、解説・取得台帳・OCR台帳・再実行用スクリプトをGitへ保存する。別の環境では以下の手順で取得する。

```sh
python3 scripts/download_arxiv_papers.py
```

リポジトリのルートで実行する。Python 3.9以上、Popplerの `pdftotext`・`pdfinfo`、OCRmyPDFとTesseractが必要。macOSでは `brew install poppler ocrmypdf` で導入できる。引用先を走査し、PDFを順番に取得して本文を抽出した後、全件のOCRを自動実行する。既に保存した同じ指定版は再利用する。版を指定していない論文は取得時の最新版であり、後日の取得で内容が変わり得る。同じPDFかはハッシュ値で照合する。複数の明示版を引用した場合は最大の版を1本取得するため、古い引用の数値はその版に戻って確認する必要がある。

[機械可読の取得台帳](arxiv_manifest.json)には、引用元、指定版、PDFから読めた版、取得日、保存先、容量、頁数、SHA-256を収録した。PDF内で版を検出できない場合は `not-detected` と記録する。

## OCRの保存方法と検証

2026年10月7日、全185本・4,407頁のOCRを完了した。既存の文字層がある頁も `--force-ocr` で画像化し、英語の文字認識を実行する。原本の文字抽出だけでOCR済みとは扱わない。原本は変更しない。OCRmyPDF 17以上を使用する。付属の拡張で描画解像度を300 dpiへ制限し、小さな高解像度画像が頁全体を数億画素へ膨らませることを防ぐ。初期に完了した一部は標準の解像度で処理した。頁を飛ばす設定は使わない。

付属拡張による解像度制限時にGhostscriptで頁の描画が失敗した場合は、同じ解像度と頁の範囲でPopplerへ切り替える。切替条件は処理ログへ残し、対応できない変換条件では停止する。

| ファイル | 用途 |
|---|---|
| `paper.pdf` | 配布元から取得した原本 |
| `paper.txt` | 原本の文字層から抽出した本文 |
| `paper_ocr.pdf` | 全頁を文字認識した検索可能なPDF |
| `paper_ocr.txt` | 画像から認識した本文 |
| `ocr.log` | 論文ごとの処理ログ |

[OCR台帳](ocr_manifest.json)に全件の処理状態、原本と成果物のSHA-256、認識言語、処理の版、頁数、認識本文の文字数、開始・完了日時を記録する。原本・OCR版PDF・認識本文の頁数が一致し、認識本文が空でなく、頁を省略した記録がなく、原本のハッシュ値が変更されていないことを検証する。途中で失敗した場合は停止し、再実行時には検証済みの成果物を再利用する。

最終照合では、185本・4,407頁の頁数一致、原本と成果物のハッシュ値、全PDFの検索用文字層を確認した。省略頁の記録と空の認識頁は0件だった。過去の代表9頁に加えて新規2頁の原本・OCR版の見た目も確認し、検証範囲と日時をOCR台帳へ記録した。OCR版PDFの合計容量は約1,473.9 MiB。認識器の品質警告98件は処理ログと台帳に保持し、誤認識がないことの保証とは扱わない。

OCRだけを再実行する場合：

```sh
python3 scripts/ocr_arxiv_papers.py --jobs 8 --language eng
```

数式、図中の小さな文字、表の列順、英語以外の文字には誤認識があり得る。これは全文翻訳や数式の構造認識ではない。引用・数値の確定には原本を照合する。全頁の自動処理・構造検証と、代表的な頁の見た目の確認を行い、全頁の文字を人手で校正したとは扱わない。

## 今回の重点テーマから読む

- 意味検索・関係検索・代替方式：追加18論文・307頁（[解説13](paper_notes_13.md)）、[最新研究と企業での比較案](../technology/rag_semantic_graph_alternatives_20261007.md)。

- AIの実行基盤・隔離・復元・自己変更：追加12論文・206頁（[解説12](paper_notes_12.md)）、[17技術の比較](../technology/agent_os_sandbox_deep_dive_20261007.md)。

- 機密区分と権限の申請・付与、人の承認、取消し、規則の改善：追加7論文（[解説11](paper_notes_11.md)）、[事例と設計案](../technology/data_clearance_access_grant_workflows_20261006.md)。

- 検索認可と索引：HONEYBEE、Retrieval Pivot Attacks、RAGent、MetaPermit（[解説10](paper_notes_10.md)）。
- 企業の知識構造：HippoRAG・OG-RAG・Zep（[解説3](paper_notes_03.md)）、SCAIR（[解説8](paper_notes_08.md)）、GROUND・PolicyKG（[解説9](paper_notes_09.md)）。
- 機密情報の流れ：CaMeL・FIDES（[解説4](paper_notes_04.md)）、APPA（[解説8](paper_notes_08.md)）。
- 作業・監査記録：aiAuthZ（[解説8](paper_notes_08.md)）、AgentTrace（[解説10](paper_notes_10.md)）。
- 自己改善の監査：Self-Authored Verification（[解説8](paper_notes_08.md)）、Harness Tampering・SEABench・Safety Must Survive Self-Improvement（[解説9](paper_notes_09.md)）。
- 説明の忠実性：2023年と2025年の説明・推論モデル研究（[解説10](paper_notes_10.md)）。

## 全論文の索引

| 論文ID | 内容・原題 | 日本語解説 | 保存したPDF | 取得版 |
|---|---|---|---|---|
| [1503.02531](https://arxiv.org/abs/1503.02531) | 大きなモデルの知識を小さなモデルへ移す | [解説](paper_notes_01.md) | [原本](arxiv/1503.02531/paper.pdf)・[OCR版](arxiv/1503.02531/paper_ocr.pdf)・[認識本文](arxiv/1503.02531/paper_ocr.txt) | v1 |
| [2004.10964](https://arxiv.org/abs/2004.10964) | 汎用言語モデルを分野・業務に合わせて追加学習する | [解説](paper_notes_01.md) | [原本](arxiv/2004.10964/paper.pdf)・[OCR版](arxiv/2004.10964/paper_ocr.pdf)・[認識本文](arxiv/2004.10964/paper_ocr.txt) | v3 |
| [2102.12892](https://arxiv.org/abs/2102.12892v1) | 保存状態を複製しても秘密と識別子の一意性を守る | [解説](paper_notes_12.md) | [原本](arxiv/2102.12892/paper.pdf)・[OCR版](arxiv/2102.12892/paper_ocr.pdf)・[認識本文](arxiv/2102.12892/paper_ocr.txt) | v1 |
| [2106.09685](https://arxiv.org/abs/2106.09685) | 更新する重みを絞る追加学習 | [解説](paper_notes_01.md) | [原本](arxiv/2106.09685/paper.pdf)・[OCR版](arxiv/2106.09685/paper_ocr.pdf)・[認識本文](arxiv/2106.09685/paper_ocr.txt) | v2 |
| [2212.04356](https://arxiv.org/abs/2212.04356) | 大量の音声と文字による音声認識 | [解説](paper_notes_01.md) | [原本](arxiv/2212.04356/paper.pdf)・[OCR版](arxiv/2212.04356/paper_ocr.pdf)・[認識本文](arxiv/2212.04356/paper_ocr.txt) | v1 |
| [2304.02711](https://arxiv.org/abs/2304.02711) | 定義済みの知識構造に合わせた情報抽出 | [解説](paper_notes_01.md) | [原本](arxiv/2304.02711/paper.pdf)・[OCR版](arxiv/2304.02711/paper_ocr.pdf)・[認識本文](arxiv/2304.02711/paper_ocr.txt) | v2 |
| [2304.11771](https://arxiv.org/abs/2304.11771) | 職場での生成 AI の効果と経験差 | [解説](paper_notes_01.md) | [原本](arxiv/2304.11771/paper.pdf)・[OCR版](arxiv/2304.11771/paper_ocr.pdf)・[認識本文](arxiv/2304.11771/paper_ocr.txt) | v2 |
| [2305.04388](https://arxiv.org/abs/2305.04388) | Language Models Don’t Always Say What They Think | [解説](paper_notes_10.md) | [原本](arxiv/2305.04388/paper.pdf)・[OCR版](arxiv/2305.04388/paper_ocr.pdf)・[認識本文](arxiv/2305.04388/paper_ocr.txt) | v2 |
| [2306.05685](https://arxiv.org/abs/2306.05685) | AI による回答採点と、その偏り | [解説](paper_notes_01.md) | [原本](arxiv/2306.05685/paper.pdf)・[OCR版](arxiv/2306.05685/paper_ocr.pdf)・[認識本文](arxiv/2306.05685/paper_ocr.txt) | v4 |
| [2307.07697](https://arxiv.org/abs/2307.07697) | 知識の関係をたどりながら答える | [解説](paper_notes_01.md) | [原本](arxiv/2307.07697/paper.pdf)・[OCR版](arxiv/2307.07697/paper_ocr.pdf)・[認識本文](arxiv/2307.07697/paper_ocr.txt) | v6 |
| [2307.16648](https://arxiv.org/abs/2307.16648) | 言語モデルによる概念体系の学習 | [解説](paper_notes_01.md) | [原本](arxiv/2307.16648/paper.pdf)・[OCR版](arxiv/2307.16648/paper_ocr.pdf)・[認識本文](arxiv/2307.16648/paper_ocr.txt) | v2 |
| [2307.16699](https://arxiv.org/abs/2307.16699) | 文章から論理形式への変換による概念体系の拡張 | [解説](paper_notes_01.md) | [原本](arxiv/2307.16699/paper.pdf)・[OCR版](arxiv/2307.16699/paper_ocr.pdf)・[認識本文](arxiv/2307.16699/paper_ocr.txt) | v1 |
| [2309.15817](https://arxiv.org/abs/2309.15817) | 模擬ツール環境で AI の危険な操作を見つける | [解説](paper_notes_01.md) | [原本](arxiv/2309.15817/paper.pdf)・[OCR版](arxiv/2309.15817/paper_ocr.pdf)・[認識本文](arxiv/2309.15817/paper_ocr.txt) | v2 |
| [2310.01798](https://arxiv.org/abs/2310.01798) | 外部の根拠なしの自己修正には限界がある | [解説](paper_notes_01.md) | [原本](arxiv/2310.01798/paper.pdf)・[OCR版](arxiv/2310.01798/paper_ocr.pdf)・[認識本文](arxiv/2310.01798/paper_ocr.txt) | v2 |
| [2310.06816](https://arxiv.org/abs/2310.06816) | 検索用ベクトルから元の文章を復元する | [解説](paper_notes_02.md) | [原本](arxiv/2310.06816/paper.pdf)・[OCR版](arxiv/2310.06816/paper_ocr.pdf)・[認識本文](arxiv/2310.06816/paper_ocr.txt) | v1 |
| [2310.08560](https://arxiv.org/abs/2310.08560) | 長い対話のための階層的な記憶 | [解説](paper_notes_02.md) | [原本](arxiv/2310.08560/paper.pdf)・[OCR版](arxiv/2310.08560/paper_ocr.pdf)・[認識本文](arxiv/2310.08560/paper_ocr.txt) | v2 |
| [2311.07509](https://arxiv.org/abs/2311.07509) | 企業の質問に対する関係データと SQL の比較 | [解説](paper_notes_02.md) | [原本](arxiv/2311.07509/paper.pdf)・[OCR版](arxiv/2311.07509/paper_ocr.pdf)・[認識本文](arxiv/2311.07509/paper_ocr.txt) | v1 |
| [2311.15999](https://arxiv.org/abs/2311.15999v1) | Firecrackerと共有CPUの漏えい経路 | [解説](paper_notes_12.md) | [原本](arxiv/2311.15999/paper.pdf)・[OCR版](arxiv/2311.15999/paper_ocr.pdf)・[認識本文](arxiv/2311.15999/paper_ocr.txt) | v1 |
| [2401.18059](https://arxiv.org/abs/2401.18059v1) | 断片と階層要約をまとめて検索 | [解説](paper_notes_13.md) | [原本](arxiv/2401.18059/paper.pdf)・[OCR版](arxiv/2401.18059/paper_ocr.pdf)・[認識本文](arxiv/2401.18059/paper_ocr.txt) | v1 |
| [2402.07456](https://arxiv.org/abs/2402.07456) | 操作手順を蓄積する汎用計算機操作支援 | [解説](paper_notes_02.md) | [原本](arxiv/2402.07456/paper.pdf)・[OCR版](arxiv/2402.07456/paper_ocr.pdf)・[認識本文](arxiv/2402.07456/paper_ocr.txt) | v2 |
| [2402.11163](https://arxiv.org/abs/2402.11163) | 知識グラフ上の複雑な質問を道具で解く | [解説](paper_notes_02.md) | [原本](arxiv/2402.11163/paper.pdf)・[OCR版](arxiv/2402.11163/paper_ocr.pdf)・[認識本文](arxiv/2402.11163/paper_ocr.txt) | v1 |
| [2403.02691](https://arxiv.org/abs/2403.02691) | 外部文書に埋め込まれた不正指示の評価 | [解説](paper_notes_02.md) | [原本](arxiv/2403.02691/paper.pdf)・[OCR版](arxiv/2403.02691/paper_ocr.pdf)・[認識本文](arxiv/2403.02691/paper_ocr.txt) | v3 |
| [2403.04960](https://arxiv.org/abs/2403.04960) | AI アプリ同士の実行を隔離する | [解説](paper_notes_02.md) | [原本](arxiv/2403.04960/paper.pdf)・[OCR版](arxiv/2403.04960/paper_ocr.pdf)・[認識本文](arxiv/2403.04960/paper_ocr.txt) | v2 |
| [2403.16971](https://arxiv.org/abs/2403.16971) | AI 実行の資源管理を共通層へ集める | [解説](paper_notes_02.md) | [原本](arxiv/2403.16971/paper.pdf)・[OCR版](arxiv/2403.16971/paper_ocr.pdf)・[認識本文](arxiv/2403.16971/paper_ocr.txt) | v5 |
| [2404.16130](https://arxiv.org/abs/2404.16130) | 文書群全体の傾向を関係グラフと要約から答える | [解説](paper_notes_02.md) | [原本](arxiv/2404.16130/paper.pdf)・[OCR版](arxiv/2404.16130/paper_ocr.pdf)・[認識本文](arxiv/2404.16130/paper_ocr.txt) | v2 |
| [2405.11706](https://arxiv.org/abs/2405.11706) | 知識構造を使って質問の誤りを検知・修正する | [解説](paper_notes_02.md) | [原本](arxiv/2405.11706/paper.pdf)・[OCR版](arxiv/2405.11706/paper_ocr.pdf)・[認識本文](arxiv/2405.11706/paper_ocr.txt) | v1 |
| [2405.14831](https://arxiv.org/abs/2405.14831) | HippoRAG | [解説](paper_notes_03.md) | [原本](arxiv/2405.14831/paper.pdf)・[OCR版](arxiv/2405.14831/paper_ocr.pdf)・[認識本文](arxiv/2405.14831/paper_ocr.txt) | v3 |
| [2405.20362](https://arxiv.org/abs/2405.20362) | Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools | [解説](paper_notes_03.md) | [原本](arxiv/2405.20362/paper.pdf)・[OCR版](arxiv/2405.20362/paper_ocr.pdf)・[認識本文](arxiv/2405.20362/paper_ocr.txt) | v1 |
| [2406.12045](https://arxiv.org/abs/2406.12045) | τ-bench | [解説](paper_notes_03.md) | [原本](arxiv/2406.12045/paper.pdf)・[OCR版](arxiv/2406.12045/paper_ocr.pdf)・[認識本文](arxiv/2406.12045/paper_ocr.txt) | v1 |
| [2406.13352](https://arxiv.org/abs/2406.13352) | AgentDojo | [解説](paper_notes_03.md) | [原本](arxiv/2406.13352/paper.pdf)・[OCR版](arxiv/2406.13352/paper_ocr.pdf)・[認識本文](arxiv/2406.13352/paper_ocr.txt) | v3 |
| [2406.13356](https://arxiv.org/abs/2406.13356) | Unlearning or Obfuscating? | [解説](paper_notes_03.md) | [原本](arxiv/2406.13356/paper.pdf)・[OCR版](arxiv/2406.13356/paper_ocr.pdf)・[認識本文](arxiv/2406.13356/paper_ocr.txt) | v4 |
| [2407.01449](https://arxiv.org/abs/2407.01449v6) | PDF頁画像を直接検索する | [解説](paper_notes_13.md) | [原本](arxiv/2407.01449/paper.pdf)・[OCR版](arxiv/2407.01449/paper_ocr.pdf)・[認識本文](arxiv/2407.01449/paper_ocr.txt) | v6 |
| [2407.10805](https://arxiv.org/abs/2407.10805) | Think-on-Graph 2.0 | [解説](paper_notes_03.md) | [原本](arxiv/2407.10805/paper.pdf)・[OCR版](arxiv/2407.10805/paper_ocr.pdf)・[認識本文](arxiv/2407.10805/paper_ocr.txt) | v7 |
| [2407.12784](https://arxiv.org/abs/2407.12784) | AgentPoison | [解説](paper_notes_03.md) | [原本](arxiv/2407.12784/paper.pdf)・[OCR版](arxiv/2407.12784/paper_ocr.pdf)・[認識本文](arxiv/2407.12784/paper_ocr.txt) | v1 |
| [2408.14717](https://arxiv.org/abs/2408.14717v1) | DB集計と文章の意味判断を組み合わせる | [解説](paper_notes_13.md) | [原本](arxiv/2408.14717/paper.pdf)・[OCR版](arxiv/2408.14717/paper_ocr.pdf)・[認識本文](arxiv/2408.14717/paper_ocr.txt) | v1 |
| [2408.15256](https://arxiv.org/abs/2408.15256) | OntoChat and Participatory Prompting | [解説](paper_notes_03.md) | [原本](arxiv/2408.15256/paper.pdf)・[OCR版](arxiv/2408.15256/paper_ocr.pdf)・[認識本文](arxiv/2408.15256/paper_ocr.txt) | v3 |
| [2409.04701](https://arxiv.org/abs/2409.04701v3) | 文書全体の文脈から断片の表現を作る | [解説](paper_notes_13.md) | [原本](arxiv/2409.04701/paper.pdf)・[OCR版](arxiv/2409.04701/paper_ocr.pdf)・[認識本文](arxiv/2409.04701/paper_ocr.txt) | v3 |
| [2409.07489](https://arxiv.org/abs/2409.07489) | RAGent | [解説](paper_notes_10.md) | [原本](arxiv/2409.07489/paper.pdf)・[OCR版](arxiv/2409.07489/paper_ocr.pdf)・[認識本文](arxiv/2409.07489/paper_ocr.txt) | v2 |
| [2409.12917](https://arxiv.org/abs/2409.12917) | Training Language Models to Self-Correct via Reinforcement Learning | [解説](paper_notes_03.md) | [原本](arxiv/2409.12917/paper.pdf)・[OCR版](arxiv/2409.12917/paper_ocr.pdf)・[認識本文](arxiv/2409.12917/paper_ocr.txt) | v2 |
| [2409.19091](https://arxiv.org/abs/2409.19091) | System-Level Defense against Indirect Prompt Injection Attacks | [解説](paper_notes_03.md) | [原本](arxiv/2409.19091/paper.pdf)・[OCR版](arxiv/2409.19091/paper_ocr.pdf)・[認識本文](arxiv/2409.19091/paper_ocr.txt) | v2 |
| [2410.05779](https://arxiv.org/abs/2410.05779) | LightRAG | [解説](paper_notes_03.md) | [原本](arxiv/2410.05779/paper.pdf)・[OCR版](arxiv/2410.05779/paper_ocr.pdf)・[認識本文](arxiv/2410.05779/paper_ocr.txt) | v3 |
| [2410.11843](https://arxiv.org/abs/2410.11843) | LLM-based Semantic File System for AIOS | [解説](paper_notes_03.md) | [原本](arxiv/2410.11843/paper.pdf)・[OCR版](arxiv/2410.11843/paper_ocr.pdf)・[認識本文](arxiv/2410.11843/paper_ocr.txt) | v1 |
| [2411.07763](https://arxiv.org/abs/2411.07763) | Spider 2.0 | [解説](paper_notes_03.md) | [原本](arxiv/2411.07763/paper.pdf)・[OCR版](arxiv/2411.07763/paper_ocr.pdf)・[認識本文](arxiv/2411.07763/paper_ocr.txt) | v2 |
| [2411.07781](https://arxiv.org/abs/2411.07781) | RedCode | [解説](paper_notes_03.md) | [原本](arxiv/2411.07781/paper.pdf)・[OCR版](arxiv/2411.07781/paper_ocr.pdf)・[認識本文](arxiv/2411.07781/paper_ocr.txt) | v1 |
| [2411.09601](https://arxiv.org/abs/2411.09601) | Accelerating Knowledge Graph and Ontology Engineering with Large Language Models | [解説](paper_notes_03.md) | [原本](arxiv/2411.09601/paper.pdf)・[OCR版](arxiv/2411.09601/paper_ocr.pdf)・[認識本文](arxiv/2411.09601/paper_ocr.txt) | v1 |
| [2412.14161](https://arxiv.org/abs/2412.14161) | TheAgentCompany | [解説](paper_notes_03.md) | [原本](arxiv/2412.14161/paper.pdf)・[OCR版](arxiv/2412.14161/paper_ocr.pdf)・[認識本文](arxiv/2412.14161/paper_ocr.txt) | v3 |
| [2412.15235](https://arxiv.org/abs/2412.15235) | OG-RAG | [解説](paper_notes_03.md) | [原本](arxiv/2412.15235/paper.pdf)・[OCR版](arxiv/2412.15235/paper_ocr.pdf)・[認識本文](arxiv/2412.15235/paper_ocr.txt) | v1 |
| [2501.13956](https://arxiv.org/abs/2501.13956) | Zep: A Temporal Knowledge Graph Architecture for Agent Memory | [解説](paper_notes_03.md) | [原本](arxiv/2501.13956/paper.pdf)・[OCR版](arxiv/2501.13956/paper_ocr.pdf)・[認識本文](arxiv/2501.13956/paper_ocr.txt) | v1 |
| [2502.11371](https://arxiv.org/abs/2502.11371) | RAG vs. GraphRAG | [解説](paper_notes_04.md) | [原本](arxiv/2502.11371/paper.pdf)・[OCR版](arxiv/2502.11371/paper_ocr.pdf)・[認識本文](arxiv/2502.11371/paper_ocr.txt) | v3 |
| [2502.14802](https://arxiv.org/abs/2502.14802v2) | 事実・連想・文脈をつなぐHippoRAG 2 | [解説](paper_notes_13.md) | [原本](arxiv/2502.14802/paper.pdf)・[OCR版](arxiv/2502.14802/paper_ocr.pdf)・[認識本文](arxiv/2502.14802/paper_ocr.txt) | v2 |
| [2503.03704](https://arxiv.org/abs/2503.03704) | Memory Injection Attacks via Query-Only Interaction | [解説](paper_notes_04.md) | [原本](arxiv/2503.03704/paper.pdf)・[OCR版](arxiv/2503.03704/paper_ocr.pdf)・[認識本文](arxiv/2503.03704/paper_ocr.txt) | v5 |
| [2503.11444](https://arxiv.org/abs/2503.11444) | Cerebrum (AIOS SDK) | [解説](paper_notes_04.md) | [原本](arxiv/2503.11444/paper.pdf)・[OCR版](arxiv/2503.11444/paper_ocr.pdf)・[認識本文](arxiv/2503.11444/paper_ocr.txt) | v1 |
| [2503.13657](https://arxiv.org/abs/2503.13657) | Why Do Multi-Agent LLM Systems Fail? | [解説](paper_notes_04.md) | [原本](arxiv/2503.13657/paper.pdf)・[OCR版](arxiv/2503.13657/paper_ocr.pdf)・[認識本文](arxiv/2503.13657/paper_ocr.txt) | v3 |
| [2503.18666](https://arxiv.org/abs/2503.18666) | AgentSpec | [解説](paper_notes_04.md) | [原本](arxiv/2503.18666/paper.pdf)・[OCR版](arxiv/2503.18666/paper_ocr.pdf)・[認識本文](arxiv/2503.18666/paper_ocr.txt) | v3 |
| [2503.18813](https://arxiv.org/abs/2503.18813) | Defeating Prompt Injections by Design | [解説](paper_notes_04.md) | [原本](arxiv/2503.18813/paper.pdf)・[OCR版](arxiv/2503.18813/paper_ocr.pdf)・[認識本文](arxiv/2503.18813/paper_ocr.txt) | v2 |
| [2504.00018](https://arxiv.org/abs/2504.00018) | SandboxEval | [解説](paper_notes_04.md) | [原本](arxiv/2504.00018/paper.pdf)・[OCR版](arxiv/2504.00018/paper_ocr.pdf)・[認識本文](arxiv/2504.00018/paper_ocr.txt) | v1 |
| [2504.11703](https://arxiv.org/abs/2504.11703) | Progent | [解説](paper_notes_04.md) | [原本](arxiv/2504.11703/paper.pdf)・[OCR版](arxiv/2504.11703/paper_ocr.pdf)・[認識本文](arxiv/2504.11703/paper_ocr.txt) | v3 |
| [2504.18575](https://arxiv.org/abs/2504.18575) | WASP | [解説](paper_notes_04.md) | [原本](arxiv/2504.18575/paper.pdf)・[OCR版](arxiv/2504.18575/paper_ocr.pdf)・[認識本文](arxiv/2504.18575/paper_ocr.txt) | v3 |
| [2505.01538](https://arxiv.org/abs/2505.01538) | HONEYBEE | [解説](paper_notes_10.md) | [原本](arxiv/2505.01538/paper.pdf)・[OCR版](arxiv/2505.01538/paper_ocr.pdf)・[認識本文](arxiv/2505.01538/paper_ocr.txt) | v3 |
| [2505.05410](https://arxiv.org/abs/2505.05410) | Reasoning Models Don’t Always Say What They Think | [解説](paper_notes_10.md) | [原本](arxiv/2505.05410/paper.pdf)・[OCR版](arxiv/2505.05410/paper_ocr.pdf)・[認識本文](arxiv/2505.05410/paper_ocr.txt) | v1 |
| [2505.21936](https://arxiv.org/abs/2505.21936) | RedTeamCUA | [解説](paper_notes_04.md) | [原本](arxiv/2505.21936/paper.pdf)・[OCR版](arxiv/2505.21936/paper_ocr.pdf)・[認識本文](arxiv/2505.21936/paper_ocr.txt) | v5 |
| [2505.22101](https://arxiv.org/abs/2505.22101) | MemOS (Short Version) | [解説](paper_notes_04.md) | [原本](arxiv/2505.22101/paper.pdf)・[OCR版](arxiv/2505.22101/paper_ocr.pdf)・[認識本文](arxiv/2505.22101/paper_ocr.txt) | v1 |
| [2505.22954](https://arxiv.org/abs/2505.22954) | Darwin Gödel Machine | [解説](paper_notes_04.md) | [原本](arxiv/2505.22954/paper.pdf)・[OCR版](arxiv/2505.22954/paper_ocr.pdf)・[認識本文](arxiv/2505.22954/paper_ocr.txt) | v3 |
| [2505.23643](https://arxiv.org/abs/2505.23643) | Securing AI Agents with Information-Flow Control | [解説](paper_notes_04.md) | [原本](arxiv/2505.23643/paper.pdf)・[OCR版](arxiv/2505.23643/paper_ocr.pdf)・[認識本文](arxiv/2505.23643/paper_ocr.txt) | v2 |
| [2506.03989](https://arxiv.org/abs/2506.03989v2) | 原文の順序・構造を保つDOSRAG | [解説](paper_notes_13.md) | [原本](arxiv/2506.03989/paper.pdf)・[OCR版](arxiv/2506.03989/paper_ocr.pdf)・[認識本文](arxiv/2506.03989/paper_ocr.txt) | v2 |
| [2506.08837](https://arxiv.org/abs/2506.08837) | Design Patterns for Securing LLM Agents | [解説](paper_notes_04.md) | [原本](arxiv/2506.08837/paper.pdf)・[OCR版](arxiv/2506.08837/paper_ocr.pdf)・[認識本文](arxiv/2506.08837/paper_ocr.txt) | v3 |
| [2506.12618](https://arxiv.org/abs/2506.12618) | OpenUnlearning | [解説](paper_notes_04.md) | [原本](arxiv/2506.12618/paper.pdf)・[OCR版](arxiv/2506.12618/paper_ocr.pdf)・[認識本文](arxiv/2506.12618/paper_ocr.txt) | v2 |
| [2506.14866](https://arxiv.org/abs/2506.14866) | OS-Harm | [解説](paper_notes_05.md) | [原本](arxiv/2506.14866/paper.pdf)・[OCR版](arxiv/2506.14866/paper_ocr.pdf)・[認識本文](arxiv/2506.14866/paper_ocr.txt) | v2 |
| [2507.02735](https://arxiv.org/abs/2507.02735) | Meta-SecAlign | [解説](paper_notes_05.md) | [原本](arxiv/2507.02735/paper.pdf)・[OCR版](arxiv/2507.02735/paper_ocr.pdf)・[認識本文](arxiv/2507.02735/paper_ocr.txt) | v4 |
| [2507.03724](https://arxiv.org/abs/2507.03724) | MemOS: A Memory OS for AI System | [解説](paper_notes_05.md) | [原本](arxiv/2507.03724/paper.pdf)・[OCR版](arxiv/2507.03724/paper_ocr.pdf)・[認識本文](arxiv/2507.03724/paper_ocr.txt) | v4 |
| [2507.08432](https://arxiv.org/abs/2507.08432) | xpSHACL | [解説](paper_notes_05.md) | [原本](arxiv/2507.08432/paper.pdf)・[OCR版](arxiv/2507.08432/paper_ocr.pdf)・[認識本文](arxiv/2507.08432/paper_ocr.txt) | v1 |
| [2507.09089](https://arxiv.org/abs/2507.09089) | Early-2025 AI and Developer Productivity | [解説](paper_notes_05.md) | [原本](arxiv/2507.09089/paper.pdf)・[OCR版](arxiv/2507.09089/paper_ocr.pdf)・[認識本文](arxiv/2507.09089/paper_ocr.txt) | v2 |
| [2509.10540](https://arxiv.org/abs/2509.10540) | EchoLeak | [解説](paper_notes_05.md) | [原本](arxiv/2509.10540/paper.pdf)・[OCR版](arxiv/2509.10540/paper_ocr.pdf)・[認識本文](arxiv/2509.10540/paper_ocr.txt) | v1 |
| [2509.25926](https://arxiv.org/abs/2509.25926) | Type-Directed Privilege Separation | [解説](paper_notes_05.md) | [原本](arxiv/2509.25926/paper.pdf)・[OCR版](arxiv/2509.25926/paper_ocr.pdf)・[認識本文](arxiv/2509.25926/paper_ocr.txt) | v2 |
| [2509.26354](https://arxiv.org/abs/2509.26354) | Your Agent May Misevolve | [解説](paper_notes_05.md) | [原本](arxiv/2509.26354/paper.pdf)・[OCR版](arxiv/2509.26354/paper_ocr.pdf)・[認識本文](arxiv/2509.26354/paper_ocr.txt) | v2 |
| [2510.09023](https://arxiv.org/abs/2510.09023) | The Attacker Moves Second | [解説](paper_notes_05.md) | [原本](arxiv/2510.09023/paper.pdf)・[OCR版](arxiv/2510.09023/paper_ocr.pdf)・[認識本文](arxiv/2510.09023/paper_ocr.txt) | v1 |
| [2510.10114](https://arxiv.org/abs/2510.10114v4) | 実体・文・文章の図で生成AIの関係抽出を省く | [解説](paper_notes_13.md) | [原本](arxiv/2510.10114/paper.pdf)・[OCR版](arxiv/2510.10114/paper_ocr.pdf)・[認識本文](arxiv/2510.10114/paper_ocr.txt) | v4 |
| [2510.12469](https://arxiv.org/abs/2510.12469) | Proof of Cloud | [解説](paper_notes_05.md) | [原本](arxiv/2510.12469/paper.pdf)・[OCR版](arxiv/2510.12469/paper_ocr.pdf)・[認識本文](arxiv/2510.12469/paper_ocr.txt) | v2 |
| [2510.15001](https://arxiv.org/abs/2510.15001) | VaultGemma | [解説](paper_notes_05.md) | [原本](arxiv/2510.15001/paper.pdf)・[OCR版](arxiv/2510.15001/paper_ocr.pdf)・[認識本文](arxiv/2510.15001/paper_ocr.txt) | v2 |
| [2510.23474](https://arxiv.org/abs/2510.23474) | Policy-Aware Generative AI for Safe, Auditable Data Access Governance | [解説](paper_notes_11.md) | [原本](arxiv/2510.23474/paper.pdf)・[OCR版](arxiv/2510.23474/paper_ocr.pdf)・[認識本文](arxiv/2510.23474/paper_ocr.txt) | v1 |
| [2511.15203](https://arxiv.org/abs/2511.15203) | IPI-Centric LLM Agent Defense Frameworks | [解説](paper_notes_05.md) | [原本](arxiv/2511.15203/paper.pdf)・[OCR版](arxiv/2511.15203/paper_ocr.pdf)・[認識本文](arxiv/2511.15203/paper_ocr.txt) | v1 |
| [2511.17959](https://arxiv.org/abs/2511.17959) | Towards Automating Data Access Permissions | [解説](paper_notes_10.md) | [原本](arxiv/2511.17959/paper.pdf)・[OCR版](arxiv/2511.17959/paper_ocr.pdf)・[認識本文](arxiv/2511.17959/paper_ocr.txt) | v1 |
| [2511.20284](https://arxiv.org/abs/2511.20284) | Can LLMs Make (Personalized) Access Control Decisions? | [解説](paper_notes_11.md) | [原本](arxiv/2511.20284/paper.pdf)・[OCR版](arxiv/2511.20284/paper_ocr.pdf)・[認識本文](arxiv/2511.20284/paper_ocr.txt) | v2 |
| [2512.01295](https://arxiv.org/abs/2512.01295) | Systems Security Foundations for Agentic Computing | [解説](paper_notes_05.md) | [原本](arxiv/2512.01295/paper.pdf)・[OCR版](arxiv/2512.01295/paper_ocr.pdf)・[認識本文](arxiv/2512.01295/paper_ocr.txt) | v2 |
| [2512.11147](https://arxiv.org/abs/2512.11147) | MiniScope | [解説](paper_notes_05.md) | [原本](arxiv/2512.11147/paper.pdf)・[OCR版](arxiv/2512.11147/paper_ocr.pdf)・[認識本文](arxiv/2512.11147/paper_ocr.txt) | v1 |
| [2512.12594](https://arxiv.org/abs/2512.12594) | CeLLMate | [解説](paper_notes_05.md) | [原本](arxiv/2512.12594/paper.pdf)・[OCR版](arxiv/2512.12594/paper_ocr.pdf)・[認識本文](arxiv/2512.12594/paper_ocr.txt) | v2 |
| [2512.12806](https://arxiv.org/abs/2512.12806) | Fault-Tolerant Sandboxing for AI Coding Agents | [解説](paper_notes_05.md) | [原本](arxiv/2512.12806/paper.pdf)・[OCR版](arxiv/2512.12806/paper_ocr.pdf)・[認識本文](arxiv/2512.12806/paper_ocr.txt) | v1 |
| [2512.20275](https://arxiv.org/abs/2512.20275) | G-SPEC | [解説](paper_notes_05.md) | [原本](arxiv/2512.20275/paper.pdf)・[OCR版](arxiv/2512.20275/paper_ocr.pdf)・[認識本文](arxiv/2512.20275/paper_ocr.txt) | v1 |
| [2601.05504](https://arxiv.org/abs/2601.05504) | Memory Poisoning Attack and Defense | [解説](paper_notes_06.md) | [原本](arxiv/2601.05504/paper.pdf)・[OCR版](arxiv/2601.05504/paper_ocr.pdf)・[認識本文](arxiv/2601.05504/paper_ocr.txt) | v2 |
| [2601.11893](https://arxiv.org/abs/2601.11893) | Mandatory Access Control for LLM-Based Agents | [解説](paper_notes_06.md) | [原本](arxiv/2601.11893/paper.pdf)・[OCR版](arxiv/2601.11893/paper_ocr.pdf)・[認識本文](arxiv/2601.11893/paper_ocr.txt) | v1 |
| [2601.14242](https://arxiv.org/abs/2601.14242) | APEX–Agents | [解説](paper_notes_06.md) | [原本](arxiv/2601.14242/paper.pdf)・[OCR版](arxiv/2601.14242/paper_ocr.pdf)・[認識本文](arxiv/2601.14242/paper_ocr.txt) | v3 |
| [2601.18511](https://arxiv.org/abs/2601.18511) | Scaling up FHE-based Privacy-Preserving ML | [解説](paper_notes_06.md) | [原本](arxiv/2601.18511/paper.pdf)・[OCR版](arxiv/2601.18511/paper_ocr.pdf)・[認識本文](arxiv/2601.18511/paper_ocr.txt) | v2 |
| [2602.03117](https://arxiv.org/abs/2602.03117) | AgentDyn | [解説](paper_notes_06.md) | [原本](arxiv/2602.03117/paper.pdf)・[OCR版](arxiv/2602.03117/paper_ocr.pdf)・[認識本文](arxiv/2602.03117/paper_ocr.txt) | v3 |
| [2602.03442](https://arxiv.org/abs/2602.03442v1) | 単語・意味検索・全文読出しをAIが反復選択 | [解説](paper_notes_13.md) | [原本](arxiv/2602.03442/paper.pdf)・[OCR版](arxiv/2602.03442/paper_ocr.pdf)・[認識本文](arxiv/2602.03442/paper_ocr.txt) | v1 |
| [2602.08235](https://arxiv.org/abs/2602.08235) | When Benign Inputs Lead to Severe Harms | [解説](paper_notes_06.md) | [原本](arxiv/2602.08235/paper.pdf)・[OCR版](arxiv/2602.08235/paper_ocr.pdf)・[認識本文](arxiv/2602.08235/paper_ocr.txt) | v2 |
| [2602.08668](https://arxiv.org/abs/2602.08668) | Retrieval Pivot Attacks in Hybrid RAG | [解説](paper_notes_10.md) | [原本](arxiv/2602.08668/paper.pdf)・[OCR版](arxiv/2602.08668/paper_ocr.pdf)・[認識本文](arxiv/2602.08668/paper_ocr.txt) | v3 |
| [2602.10133](https://arxiv.org/abs/2602.10133) | AgentTrace | [解説](paper_notes_10.md) | [原本](arxiv/2602.10133/paper.pdf)・[OCR版](arxiv/2602.10133/paper_ocr.pdf)・[認識本文](arxiv/2602.10133/paper_ocr.txt) | v1 |
| [2602.14211](https://arxiv.org/abs/2602.14211) | SkillJect | [解説](paper_notes_06.md) | [原本](arxiv/2602.14211/paper.pdf)・[OCR版](arxiv/2602.14211/paper_ocr.pdf)・[認識本文](arxiv/2602.14211/paper_ocr.txt) | v3 |
| [2602.20021](https://arxiv.org/abs/2602.20021) | Agents of Chaos | [解説](paper_notes_06.md) | [原本](arxiv/2602.20021/paper.pdf)・[OCR版](arxiv/2602.20021/paper_ocr.pdf)・[認識本文](arxiv/2602.20021/paper_ocr.txt) | v1 |
| [2603.02277](https://arxiv.org/abs/2603.02277) | Container Sandbox Escape | [解説](paper_notes_06.md) | [原本](arxiv/2603.02277/paper.pdf)・[OCR版](arxiv/2603.02277/paper_ocr.pdf)・[認識本文](arxiv/2603.02277/paper_ocr.txt) | v3 |
| [2603.08938](https://arxiv.org/abs/2603.08938) | AgentOS | [解説](paper_notes_06.md) | [原本](arxiv/2603.08938/paper.pdf)・[OCR版](arxiv/2603.08938/paper_ocr.pdf)・[認識本文](arxiv/2603.08938/paper_ocr.txt) | v2 |
| [2603.13424](https://arxiv.org/abs/2603.13424) | Agent Privilege Separation in OpenClaw | [解説](paper_notes_06.md) | [原本](arxiv/2603.13424/paper.pdf)・[OCR版](arxiv/2603.13424/paper_ocr.pdf)・[認識本文](arxiv/2603.13424/paper_ocr.txt) | v1 |
| [2603.14341](https://arxiv.org/abs/2603.14341) | Generation of Human Comprehensible Access Control Policies from Audit Logs | [解説](paper_notes_11.md) | [原本](arxiv/2603.14341/paper.pdf)・[OCR版](arxiv/2603.14341/paper_ocr.pdf)・[認識本文](arxiv/2603.14341/paper_ocr.txt) | v1 |
| [2603.15714](https://arxiv.org/abs/2603.15714) | Large-Scale Public Prompt Injection Competition | [解説](paper_notes_06.md) | [原本](arxiv/2603.15714/paper.pdf)・[OCR版](arxiv/2603.15714/paper_ocr.pdf)・[認識本文](arxiv/2603.15714/paper_ocr.txt) | v1 |
| [2603.24775](https://arxiv.org/abs/2603.24775) | Agent Identity Protocol | [解説](paper_notes_06.md) | [原本](arxiv/2603.24775/paper.pdf)・[OCR版](arxiv/2603.24775/paper_ocr.pdf)・[認識本文](arxiv/2603.24775/paper_ocr.txt) | v1 |
| [2603.27517](https://arxiv.org/abs/2603.27517) | Security Analysis of OpenClaw | [解説](paper_notes_06.md) | [原本](arxiv/2603.27517/paper.pdf)・[OCR版](arxiv/2603.27517/paper_ocr.pdf)・[認識本文](arxiv/2603.27517/paper_ocr.txt) | v3 |
| [2604.00169](https://arxiv.org/abs/2604.00169) | System-Level Characterization of MPC and FHE | [解説](paper_notes_06.md) | [原本](arxiv/2604.00169/paper.pdf)・[OCR版](arxiv/2604.00169/paper_ocr.pdf)・[認識本文](arxiv/2604.00169/paper_ocr.txt) | v2 |
| [2604.01344](https://arxiv.org/abs/2604.01344) | IDEA2 | [解説](paper_notes_06.md) | [原本](arxiv/2604.01344/paper.pdf)・[OCR版](arxiv/2604.01344/paper_ocr.pdf)・[認識本文](arxiv/2604.01344/paper_ocr.txt) | v1 |
| [2604.03081](https://arxiv.org/abs/2604.03081) | Supply-Chain Poisoning of Agent Skills | [解説](paper_notes_07.md) | [原本](arxiv/2604.03081/paper.pdf)・[OCR版](arxiv/2604.03081/paper_ocr.pdf)・[認識本文](arxiv/2604.03081/paper_ocr.txt) | v1 |
| [2604.08304](https://arxiv.org/abs/2604.08304) | Securing Retrieval-Augmented Generation | [解説](paper_notes_10.md) | [原本](arxiv/2604.08304/paper.pdf)・[OCR版](arxiv/2604.08304/paper_ocr.pdf)・[認識本文](arxiv/2604.08304/paper_ocr.txt) | v3 |
| [2604.08552](https://arxiv.org/abs/2604.08552) | Ontology-Constrained Biomedical Metadata | [解説](paper_notes_07.md) | [原本](arxiv/2604.08552/paper.pdf)・[OCR版](arxiv/2604.08552/paper_ocr.pdf)・[認識本文](arxiv/2604.08552/paper_ocr.txt) | not-detected |
| [2604.18231](https://arxiv.org/abs/2604.18231) | AgenTEE | [解説](paper_notes_07.md) | [原本](arxiv/2604.18231/paper.pdf)・[OCR版](arxiv/2604.18231/paper_ocr.pdf)・[認識本文](arxiv/2604.18231/paper_ocr.txt) | v2 |
| [2604.23178](https://arxiv.org/abs/2604.23178) | Judging the Judges | [解説](paper_notes_07.md) | [原本](arxiv/2604.23178/paper.pdf)・[OCR版](arxiv/2604.23178/paper_ocr.pdf)・[認識本文](arxiv/2604.23178/paper_ocr.txt) | v2 |
| [2604.23280](https://arxiv.org/abs/2604.23280) | AI Identity | [解説](paper_notes_07.md) | [原本](arxiv/2604.23280/paper.pdf)・[OCR版](arxiv/2604.23280/paper_ocr.pdf)・[認識本文](arxiv/2604.23280/paper_ocr.txt) | v1 |
| [2604.25149](https://arxiv.org/abs/2604.25149) | Semantic Layers for Reliable Data Analytics | [解説](paper_notes_07.md) | [原本](arxiv/2604.25149/paper.pdf)・[OCR版](arxiv/2604.25149/paper_ocr.pdf)・[認識本文](arxiv/2604.25149/paper_ocr.txt) | not-detected |
| [2604.26851](https://arxiv.org/abs/2604.26851) | Resume-ing Control | [解説](paper_notes_07.md) | [原本](arxiv/2604.26851/paper.pdf)・[OCR版](arxiv/2604.26851/paper_ocr.pdf)・[認識本文](arxiv/2604.26851/paper_ocr.txt) | v1 |
| [2605.03213](https://arxiv.org/abs/2605.03213) | When Agents Handle Secrets | [解説](paper_notes_07.md) | [原本](arxiv/2605.03213/paper.pdf)・[OCR版](arxiv/2605.03213/paper_ocr.pdf)・[認識本文](arxiv/2605.03213/paper_ocr.txt) | v2 |
| [2605.08442](https://arxiv.org/abs/2605.08442) | Injection–Execution Dissociation | [解説](paper_notes_07.md) | [原本](arxiv/2605.08442/paper.pdf)・[OCR版](arxiv/2605.08442/paper_ocr.pdf)・[認識本文](arxiv/2605.08442/paper_ocr.txt) | v5 |
| [2605.09045](https://arxiv.org/abs/2605.09045) | Containment Verification | [解説](paper_notes_07.md) | [原本](arxiv/2605.09045/paper.pdf)・[OCR版](arxiv/2605.09045/paper_ocr.pdf)・[認識本文](arxiv/2605.09045/paper_ocr.txt) | v2 |
| [2605.11418](https://arxiv.org/abs/2605.11418) | Under the Hood of SKILL.md | [解説](paper_notes_07.md) | [原本](arxiv/2605.11418/paper.pdf)・[OCR版](arxiv/2605.11418/paper_ocr.pdf)・[認識本文](arxiv/2605.11418/paper_ocr.txt) | v1 |
| [2605.13471](https://arxiv.org/abs/2605.13471) | Sleeper Channels and Provenance Gates | [解説](paper_notes_07.md) | [原本](arxiv/2605.13471/paper.pdf)・[OCR版](arxiv/2605.13471/paper_ocr.pdf)・[認識本文](arxiv/2605.13471/paper_ocr.txt) | v1 |
| [2605.14932](https://arxiv.org/abs/2605.14932) | Securing AI Agents Like Operating Systems | [解説](paper_notes_07.md) | [原本](arxiv/2605.14932/paper.pdf)・[OCR版](arxiv/2605.14932/paper_ocr.pdf)・[認識本文](arxiv/2605.14932/paper_ocr.txt) | v1 |
| [2605.15338](https://arxiv.org/abs/2605.15338) | Hidden in Memory | [解説](paper_notes_07.md) | [原本](arxiv/2605.15338/paper.pdf)・[OCR版](arxiv/2605.15338/paper_ocr.pdf)・[認識本文](arxiv/2605.15338/paper_ocr.txt) | v2 |
| [2605.17634](https://arxiv.org/abs/2605.17634) | AI Agents May Always Fall for Prompt Injections | [解説](paper_notes_07.md) | [原本](arxiv/2605.17634/paper.pdf)・[OCR版](arxiv/2605.17634/paper_ocr.pdf)・[認識本文](arxiv/2605.17634/paper_ocr.txt) | v1 |
| [2605.18930](https://arxiv.org/abs/2605.18930) | OEP | [解説](paper_notes_07.md) | [原本](arxiv/2605.18930/paper.pdf)・[OCR版](arxiv/2605.18930/paper_ocr.pdf)・[認識本文](arxiv/2605.18930/paper_ocr.txt) | v1 |
| [2605.22781](https://arxiv.org/abs/2605.22781) | DeltaBox | [解説](paper_notes_07.md) | [原本](arxiv/2605.22781/paper.pdf)・[OCR版](arxiv/2605.22781/paper_ocr.pdf)・[認識本文](arxiv/2605.22781/paper_ocr.txt) | v2 |
| [2606.01508](https://arxiv.org/abs/2606.01508) | Agent Operating Systems | [解説](paper_notes_08.md) | [原本](arxiv/2606.01508/paper.pdf)・[OCR版](arxiv/2606.01508/paper_ocr.pdf)・[認識本文](arxiv/2606.01508/paper_ocr.txt) | not-detected |
| [2606.02668](https://arxiv.org/abs/2606.02668) | What You Approve Is What Executes: Consent Integrity for Black-Box LLM Agents | [解説](paper_notes_11.md) | [原本](arxiv/2606.02668/paper.pdf)・[OCR版](arxiv/2606.02668/paper_ocr.pdf)・[認識本文](arxiv/2606.02668/paper_ocr.txt) | v1 |
| [2606.04141](https://arxiv.org/abs/2606.04141) | Caught in the Act(ivation) | [解説](paper_notes_08.md) | [原本](arxiv/2606.04141/paper.pdf)・[OCR版](arxiv/2606.04141/paper_ocr.pdf)・[認識本文](arxiv/2606.04141/paper_ocr.txt) | v1 |
| [2606.04329](https://arxiv.org/abs/2606.04329) | From Untrusted Input to Trusted Memory | [解説](paper_notes_08.md) | [原本](arxiv/2606.04329/paper.pdf)・[OCR版](arxiv/2606.04329/paper_ocr.pdf)・[認識本文](arxiv/2606.04329/paper_ocr.txt) | v2 |
| [2606.04425](https://arxiv.org/abs/2606.04425) | Cross-Session Stored Prompt Injection | [解説](paper_notes_08.md) | [原本](arxiv/2606.04425/paper.pdf)・[OCR版](arxiv/2606.04425/paper_ocr.pdf)・[認識本文](arxiv/2606.04425/paper_ocr.txt) | v2 |
| [2606.05233](https://arxiv.org/abs/2606.05233) | Domain-Conditioned Safety | [解説](paper_notes_08.md) | [原本](arxiv/2606.05233/paper.pdf)・[OCR版](arxiv/2606.05233/paper_ocr.pdf)・[認識本文](arxiv/2606.05233/paper_ocr.txt) | v1 |
| [2606.05634](https://arxiv.org/abs/2606.05634) | Bootstrapping Semantic Layer from Execution | [解説](paper_notes_08.md) | [原本](arxiv/2606.05634/paper.pdf)・[OCR版](arxiv/2606.05634/paper_ocr.pdf)・[認識本文](arxiv/2606.05634/paper_ocr.txt) | v1 |
| [2606.08433](https://arxiv.org/abs/2606.08433) | AI Code Sandboxes: Part 1 | [解説](paper_notes_08.md) | [原本](arxiv/2606.08433/paper.pdf)・[OCR版](arxiv/2606.08433/paper_ocr.pdf)・[認識本文](arxiv/2606.08433/paper_ocr.txt) | v1 |
| [2606.23075](https://arxiv.org/abs/2606.23075) | Safety in Self-Evolving LLM Agent Systems | [解説](paper_notes_08.md) | [原本](arxiv/2606.23075/paper.pdf)・[OCR版](arxiv/2606.23075/paper_ocr.pdf)・[認識本文](arxiv/2606.23075/paper_ocr.txt) | v1 |
| [2606.27379](https://arxiv.org/abs/2606.27379) | The Term Machine Unlearning Is Overused | [解説](paper_notes_08.md) | [原本](arxiv/2606.27379/paper.pdf)・[OCR版](arxiv/2606.27379/paper_ocr.pdf)・[認識本文](arxiv/2606.27379/paper_ocr.txt) | v1 |
| [2607.05518](https://arxiv.org/abs/2607.05518) | aiAuthZ | [解説](paper_notes_08.md) | [原本](arxiv/2607.05518/paper.pdf)・[OCR版](arxiv/2607.05518/paper_ocr.pdf)・[認識本文](arxiv/2607.05518/paper_ocr.txt) | v1 |
| [2607.05803](https://arxiv.org/abs/2607.05803v1) | 語ごとの照合に負の寄与を導入するSigned MaxSim | [解説](paper_notes_13.md) | [原本](arxiv/2607.05803/paper.pdf)・[OCR版](arxiv/2607.05803/paper_ocr.pdf)・[認識本文](arxiv/2607.05803/paper_ocr.txt) | v1 |
| [2607.13718](https://arxiv.org/abs/2607.13718) | How Agents Ask for Permission: User Permissions for AI Agents, from Interfaces to Enforcement | [解説](paper_notes_11.md) | [原本](arxiv/2607.13718/paper.pdf)・[OCR版](arxiv/2607.13718/paper_ocr.pdf)・[認識本文](arxiv/2607.13718/paper_ocr.txt) | v2 |
| [2607.22571](https://arxiv.org/abs/2607.22571) | SCAIR | [解説](paper_notes_08.md) | [原本](arxiv/2607.22571/paper.pdf)・[OCR版](arxiv/2607.22571/paper_ocr.pdf)・[認識本文](arxiv/2607.22571/paper_ocr.txt) | v1 |
| [2607.23933](https://arxiv.org/abs/2607.23933v2) | SpecBox：予測による環境準備と結果再利用 | [解説](paper_notes_12.md) | [原本](arxiv/2607.23933/paper.pdf)・[OCR版](arxiv/2607.23933/paper_ocr.pdf)・[認識本文](arxiv/2607.23933/paper_ocr.txt) | v2 |
| [2607.24300](https://arxiv.org/abs/2607.24300) | Self-Authored Verification Is Unreliable | [解説](paper_notes_08.md) | [原本](arxiv/2607.24300/paper.pdf)・[OCR版](arxiv/2607.24300/paper_ocr.pdf)・[認識本文](arxiv/2607.24300/paper_ocr.txt) | v1 |
| [2607.24625](https://arxiv.org/abs/2607.24625) | APPA | [解説](paper_notes_08.md) | [原本](arxiv/2607.24625/paper.pdf)・[OCR版](arxiv/2607.24625/paper_ocr.pdf)・[認識本文](arxiv/2607.24625/paper_ocr.txt) | v2 |
| [2607.25076](https://arxiv.org/abs/2607.25076) | Towards an Agent Operating System | [解説](paper_notes_08.md) | [原本](arxiv/2607.25076/paper.pdf)・[OCR版](arxiv/2607.25076/paper_ocr.pdf)・[認識本文](arxiv/2607.25076/paper_ocr.txt) | v1 |
| [2608.00824](https://arxiv.org/abs/2608.00824v1) | 見出しを保持する意味分割と採点の不安定性 | [解説](paper_notes_13.md) | [原本](arxiv/2608.00824/paper.pdf)・[OCR版](arxiv/2608.00824/paper_ocr.pdf)・[認識本文](arxiv/2608.00824/paper_ocr.txt) | v1 |
| [2608.01759](https://arxiv.org/abs/2608.01759) | Benign Alone, Harmful Together | [解説](paper_notes_08.md) | [原本](arxiv/2608.01759/paper.pdf)・[OCR版](arxiv/2608.01759/paper_ocr.pdf)・[認識本文](arxiv/2608.01759/paper_ocr.txt) | v1 |
| [2608.06477](https://arxiv.org/abs/2608.06477) | StepJack | [解説](paper_notes_08.md) | [原本](arxiv/2608.06477/paper.pdf)・[OCR版](arxiv/2608.06477/paper_ocr.pdf)・[認識本文](arxiv/2608.06477/paper_ocr.txt) | v1 |
| [2608.06984](https://arxiv.org/abs/2608.06984) | HarnessSafe | [解説](paper_notes_08.md) | [原本](arxiv/2608.06984/paper.pdf)・[OCR版](arxiv/2608.06984/paper_ocr.pdf)・[認識本文](arxiv/2608.06984/paper_ocr.txt) | v1 |
| [2608.07530](https://arxiv.org/abs/2608.07530) | NL2SHACL-Bench | [解説](paper_notes_09.md) | [原本](arxiv/2608.07530/paper.pdf)・[OCR版](arxiv/2608.07530/paper_ocr.pdf)・[認識本文](arxiv/2608.07530/paper_ocr.txt) | v2 |
| [2608.09028](https://arxiv.org/abs/2608.09028) | PolicyKG | [解説](paper_notes_09.md) | [原本](arxiv/2608.09028/paper.pdf)・[OCR版](arxiv/2608.09028/paper_ocr.pdf)・[認識本文](arxiv/2608.09028/paper_ocr.txt) | v1 |
| [2608.09732](https://arxiv.org/abs/2608.09732) | ColluSkill | [解説](paper_notes_09.md) | [原本](arxiv/2608.09732/paper.pdf)・[OCR版](arxiv/2608.09732/paper_ocr.pdf)・[認識本文](arxiv/2608.09732/paper_ocr.txt) | v1 |
| [2608.11274](https://arxiv.org/abs/2608.11274v1) | 実行時の制約と成功の証拠を要求する | [解説](paper_notes_12.md) | [原本](arxiv/2608.11274/paper.pdf)・[OCR版](arxiv/2608.11274/paper_ocr.pdf)・[認識本文](arxiv/2608.11274/paper_ocr.txt) | v1 |
| [2608.11323](https://arxiv.org/abs/2608.11323) | Deployment Decision Reliability | [解説](paper_notes_09.md) | [原本](arxiv/2608.11323/paper.pdf)・[OCR版](arxiv/2608.11323/paper_ocr.pdf)・[認識本文](arxiv/2608.11323/paper_ocr.txt) | v1 |
| [2608.12851](https://arxiv.org/abs/2608.12851) | Practice Makes Unsafe | [解説](paper_notes_09.md) | [原本](arxiv/2608.12851/paper.pdf)・[OCR版](arxiv/2608.12851/paper_ocr.pdf)・[認識本文](arxiv/2608.12851/paper_ocr.txt) | v1 |
| [2608.16628](https://arxiv.org/abs/2608.16628v1) | 図表・文章をまとめて結び、局所的に抽出を補う | [解説](paper_notes_13.md) | [原本](arxiv/2608.16628/paper.pdf)・[OCR版](arxiv/2608.16628/paper_ocr.pdf)・[認識本文](arxiv/2608.16628/paper_ocr.txt) | v1 |
| [2608.26108](https://arxiv.org/abs/2608.26108) | Agentic AI Containment Architecture | [解説](paper_notes_09.md) | [原本](arxiv/2608.26108/paper.pdf)・[OCR版](arxiv/2608.26108/paper_ocr.pdf)・[認識本文](arxiv/2608.26108/paper_ocr.txt) | not-detected |
| [2608.26157](https://arxiv.org/abs/2608.26157) | GROUND | [解説](paper_notes_09.md) | [原本](arxiv/2608.26157/paper.pdf)・[OCR版](arxiv/2608.26157/paper_ocr.pdf)・[認識本文](arxiv/2608.26157/paper_ocr.txt) | v1 |
| [2608.26575](https://arxiv.org/abs/2608.26575) | Confidential Computing on Blackwell GPUs | [解説](paper_notes_09.md) | [原本](arxiv/2608.26575/paper.pdf)・[OCR版](arxiv/2608.26575/paper_ocr.pdf)・[認識本文](arxiv/2608.26575/paper_ocr.txt) | v2 |
| [2608.27443](https://arxiv.org/abs/2608.27443) | Do User-Authored Permission Policies Improve Protection Against AI Agent Overreach? | [解説](paper_notes_11.md) | [原本](arxiv/2608.27443/paper.pdf)・[OCR版](arxiv/2608.27443/paper_ocr.pdf)・[認識本文](arxiv/2608.27443/paper_ocr.txt) | v1 |
| [2608.27800](https://arxiv.org/abs/2608.27800) | ContextLeak | [解説](paper_notes_09.md) | [原本](arxiv/2608.27800/paper.pdf)・[OCR版](arxiv/2608.27800/paper_ocr.pdf)・[認識本文](arxiv/2608.27800/paper_ocr.txt) | v1 |
| [2609.00069](https://arxiv.org/abs/2609.00069) | Auditing Harness Tampering | [解説](paper_notes_09.md) | [原本](arxiv/2609.00069/paper.pdf)・[OCR版](arxiv/2609.00069/paper_ocr.pdf)・[認識本文](arxiv/2609.00069/paper_ocr.txt) | v1 |
| [2609.00267](https://arxiv.org/abs/2609.00267v1) | 複数AIへの本人性・認可・権限委任 | [解説](paper_notes_12.md) | [原本](arxiv/2609.00267/paper.pdf)・[OCR版](arxiv/2609.00267/paper_ocr.pdf)・[認識本文](arxiv/2609.00267/paper_ocr.txt) | v1 |
| [2609.11294](https://arxiv.org/abs/2609.11294v1) | AgentZip：多数の実行環境の記憶圧縮 | [解説](paper_notes_12.md) | [原本](arxiv/2609.11294/paper.pdf)・[OCR版](arxiv/2609.11294/paper_ocr.pdf)・[認識本文](arxiv/2609.11294/paper_ocr.txt) | v1 |
| [2609.17817](https://arxiv.org/abs/2609.17817) | Reflections on Trusting Trust, Revisited | [解説](paper_notes_09.md) | [原本](arxiv/2609.17817/paper.pdf)・[OCR版](arxiv/2609.17817/paper_ocr.pdf)・[認識本文](arxiv/2609.17817/paper_ocr.txt) | v1 |
| [2609.19622](https://arxiv.org/abs/2609.19622v1) | 角度と密度から補完的な資料を探すG³RAG | [解説](paper_notes_13.md) | [原本](arxiv/2609.19622/paper.pdf)・[OCR版](arxiv/2609.19622/paper_ocr.pdf)・[認識本文](arxiv/2609.19622/paper_ocr.txt) | v1 |
| [2609.23700](https://arxiv.org/abs/2609.23700) | When the Agent Becomes the Kernel | [解説](paper_notes_09.md) | [原本](arxiv/2609.23700/paper.pdf)・[OCR版](arxiv/2609.23700/paper_ocr.pdf)・[認識本文](arxiv/2609.23700/paper_ocr.txt) | v1 |
| [2609.26457](https://arxiv.org/abs/2609.26457) | Recursive Self-Improvement of AI Research Agents | [解説](paper_notes_09.md) | [原本](arxiv/2609.26457/paper.pdf)・[OCR版](arxiv/2609.26457/paper_ocr.pdf)・[認識本文](arxiv/2609.26457/paper_ocr.txt) | v1 |
| [2609.29647](https://arxiv.org/abs/2609.29647v1) | AgentKernel：本人性・入力・記憶・実行の保護 | [解説](paper_notes_12.md) | [原本](arxiv/2609.29647/paper.pdf)・[OCR版](arxiv/2609.29647/paper_ocr.pdf)・[認識本文](arxiv/2609.29647/paper_ocr.txt) | v1 |
| [2609.31039](https://arxiv.org/abs/2609.31039) | MetaPermit | [解説](paper_notes_10.md) | [原本](arxiv/2609.31039/paper.pdf)・[OCR版](arxiv/2609.31039/paper_ocr.pdf)・[認識本文](arxiv/2609.31039/paper_ocr.txt) | v1 |
| [2609.31318](https://arxiv.org/abs/2609.31318v1) | AgentXploit：コード分析と実行環境での安全性検査 | [解説](paper_notes_12.md) | [原本](arxiv/2609.31318/paper.pdf)・[OCR版](arxiv/2609.31318/paper_ocr.pdf)・[認識本文](arxiv/2609.31318/paper_ocr.txt) | v1 |
| [2609.32327](https://arxiv.org/abs/2609.32327v1) | 学習した複数実体の図で根拠を連結 | [解説](paper_notes_13.md) | [原本](arxiv/2609.32327/paper.pdf)・[OCR版](arxiv/2609.32327/paper_ocr.pdf)・[認識本文](arxiv/2609.32327/paper_ocr.txt) | v1 |
| [2609.32390](https://arxiv.org/abs/2609.32390) | Reward Hacking and Agent Containment Failure | [解説](paper_notes_09.md) | [原本](arxiv/2609.32390/paper.pdf)・[OCR版](arxiv/2609.32390/paper_ocr.pdf)・[認識本文](arxiv/2609.32390/paper_ocr.txt) | not-detected |
| [2609.34776](https://arxiv.org/abs/2609.34776v1) | PDF頁単位の検索を五つの構成で比較 | [解説](paper_notes_13.md) | [原本](arxiv/2609.34776/paper.pdf)・[OCR版](arxiv/2609.34776/paper_ocr.pdf)・[認識本文](arxiv/2609.34776/paper_ocr.txt) | v1 |
| [2609.35193](https://arxiv.org/abs/2609.35193v1) | 二つの既知実体を結ぶ関係を軽く推定 | [解説](paper_notes_13.md) | [原本](arxiv/2609.35193/paper.pdf)・[OCR版](arxiv/2609.35193/paper_ocr.pdf)・[認識本文](arxiv/2609.35193/paper_ocr.txt) | v1 |
| [2609.35596](https://arxiv.org/abs/2609.35596) | SEABench | [解説](paper_notes_09.md) | [原本](arxiv/2609.35596/paper.pdf)・[OCR版](arxiv/2609.35596/paper_ocr.pdf)・[認識本文](arxiv/2609.35596/paper_ocr.txt) | v2 |
| [2609.37661](https://arxiv.org/abs/2609.37661v1) | 実体の近隣構造で橋渡し資料を探すNexusRAG | [解説](paper_notes_13.md) | [原本](arxiv/2609.37661/paper.pdf)・[OCR版](arxiv/2609.37661/paper_ocr.pdf)・[認識本文](arxiv/2609.37661/paper_ocr.txt) | v1 |
| [2609.38353](https://arxiv.org/abs/2609.38353v2) | AIの履歴を標識付きの図で検索 | [解説](paper_notes_13.md) | [原本](arxiv/2609.38353/paper.pdf)・[OCR版](arxiv/2609.38353/paper_ocr.pdf)・[認識本文](arxiv/2609.38353/paper_ocr.txt) | v2 |
| [2609.38983](https://arxiv.org/abs/2609.38983) | Approval Laundering | [解説](paper_notes_09.md) | [原本](arxiv/2609.38983/paper.pdf)・[OCR版](arxiv/2609.38983/paper_ocr.pdf)・[認識本文](arxiv/2609.38983/paper_ocr.txt) | v1 |
| [2610.00037](https://arxiv.org/abs/2610.00037) | Guarded Commits: Transactional Human Approvals for LLM Workflows | [解説](paper_notes_11.md) | [原本](arxiv/2610.00037/paper.pdf)・[OCR版](arxiv/2610.00037/paper_ocr.pdf)・[認識本文](arxiv/2610.00037/paper_ocr.txt) | v1 |
| [2610.01073](https://arxiv.org/abs/2610.01073) | Safety Must Survive Self-Improvement | [解説](paper_notes_09.md) | [原本](arxiv/2610.01073/paper.pdf)・[OCR版](arxiv/2610.01073/paper_ocr.pdf)・[認識本文](arxiv/2610.01073/paper_ocr.txt) | v1 |
| [2610.02456](https://arxiv.org/abs/2610.02456v1) | SideKernel：macOSの隔離の使いやすさ | [解説](paper_notes_12.md) | [原本](arxiv/2610.02456/paper.pdf)・[OCR版](arxiv/2610.02456/paper_ocr.pdf)・[認識本文](arxiv/2610.02456/paper_ocr.txt) | v1 |
| [2610.04083](https://arxiv.org/abs/2610.04083v1) | 不正な目標が永続情報から後のAIへ伝わる | [解説](paper_notes_12.md) | [原本](arxiv/2610.04083/paper.pdf)・[OCR版](arxiv/2610.04083/paper_ocr.pdf)・[認識本文](arxiv/2610.04083/paper_ocr.txt) | v1 |
| [2610.06001](https://arxiv.org/abs/2610.06001v1) | AgentSpy：AIと子プロセスの外部観測 | [解説](paper_notes_12.md) | [原本](arxiv/2610.06001/paper.pdf)・[OCR版](arxiv/2610.06001/paper_ocr.pdf)・[認識本文](arxiv/2610.06001/paper_ocr.txt) | v1 |
| [2610.06274](https://arxiv.org/abs/2610.06274v1) | 自己設定で安全上の制約を変更させない | [解説](paper_notes_12.md) | [原本](arxiv/2610.06274/paper.pdf)・[OCR版](arxiv/2610.06274/paper_ocr.pdf)・[認識本文](arxiv/2610.06274/paper_ocr.txt) | v1 |
| [2610.08452](https://arxiv.org/abs/2610.08452v1) | 検索と生成の失敗を分けて構成を探索 | [解説](paper_notes_13.md) | [原本](arxiv/2610.08452/paper.pdf)・[OCR版](arxiv/2610.08452/paper_ocr.pdf)・[認識本文](arxiv/2610.08452/paper_ocr.txt) | v1 |
