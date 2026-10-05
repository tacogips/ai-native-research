# 引用論文の取得台帳と日本語解説

2026年10月5〜6日に、引用されたarXiv論文を重複を除いて148本取得した。合計3,806頁、約259.9 MiB。全件でPDFの形式、本文抽出、容量、SHA-256を確認した。

各解説は取得したPDFの要旨と本文の手法・結果・議論の関連箇所に基づく。全付録の精読と実験の再現は行っていない。著者の主張、評価条件・限界、企業設計への解釈を分けた。

PDFと抽出本文はこの作業環境の `arxiv/論文ID/` に保存している。PDF・抽出本文はGit管理から除外し、解説・取得台帳・取得スクリプトをGitへ保存する。別の環境では以下の手順で取得する。

```sh
python3 scripts/download_arxiv_papers.py
```

リポジトリのルートで実行する。Python 3.9以上と、Popplerの `pdftotext`・`pdfinfo` が必要。引用先を走査し、PDFを順番に取得して本文を抽出する。既に保存した同じ指定版は再利用する。版を指定していない論文は取得時の最新版であり、後日の取得で内容が変わり得る。同じPDFかはハッシュ値で照合する。複数の明示版を引用した場合は最大の版を1本取得するため、古い引用の数値はその版に戻って確認する必要がある。

[機械可読の取得台帳](arxiv_manifest.json)には、引用元、指定版、PDFから読めた版、取得日、保存先、容量、頁数、SHA-256を収録した。PDF内で版を検出できない場合は `not-detected` と記録する。

## 今回の重点テーマから読む

- 検索認可と索引：HONEYBEE、Retrieval Pivot Attacks、RAGent、MetaPermit（[解説10](paper_notes_10.md)）。
- 企業の知識構造：HippoRAG・OG-RAG・Zep（[解説3](paper_notes_03.md)）、SCAIR（[解説8](paper_notes_08.md)）、GROUND・PolicyKG（[解説9](paper_notes_09.md)）。
- 機密情報の流れ：CaMeL・FIDES（[解説4](paper_notes_04.md)）、APPA（[解説8](paper_notes_08.md)）。
- 作業・監査記録：aiAuthZ（[解説8](paper_notes_08.md)）、AgentTrace（[解説10](paper_notes_10.md)）。
- 自己改善の監査：Self-Authored Verification（[解説8](paper_notes_08.md)）、Harness Tampering・SEABench・Safety Must Survive Self-Improvement（[解説9](paper_notes_09.md)）。
- 説明の忠実性：2023年と2025年の説明・推論モデル研究（[解説10](paper_notes_10.md)）。

## 全論文の索引

| 論文ID | 内容・原題 | 日本語解説 | 保存したPDF | 取得版 |
|---|---|---|---|---|
| [1503.02531](https://arxiv.org/abs/1503.02531) | 大きなモデルの知識を小さなモデルへ移す | [解説](paper_notes_01.md) | [PDF](arxiv/1503.02531/paper.pdf) | v1 |
| [2004.10964](https://arxiv.org/abs/2004.10964) | 汎用言語モデルを分野・業務に合わせて追加学習する | [解説](paper_notes_01.md) | [PDF](arxiv/2004.10964/paper.pdf) | v3 |
| [2106.09685](https://arxiv.org/abs/2106.09685) | 更新する重みを絞る追加学習 | [解説](paper_notes_01.md) | [PDF](arxiv/2106.09685/paper.pdf) | v2 |
| [2212.04356](https://arxiv.org/abs/2212.04356) | 大量の音声と文字による音声認識 | [解説](paper_notes_01.md) | [PDF](arxiv/2212.04356/paper.pdf) | v1 |
| [2304.02711](https://arxiv.org/abs/2304.02711) | 定義済みの知識構造に合わせた情報抽出 | [解説](paper_notes_01.md) | [PDF](arxiv/2304.02711/paper.pdf) | v2 |
| [2304.11771](https://arxiv.org/abs/2304.11771) | 職場での生成 AI の効果と経験差 | [解説](paper_notes_01.md) | [PDF](arxiv/2304.11771/paper.pdf) | v2 |
| [2305.04388](https://arxiv.org/abs/2305.04388) | Language Models Don’t Always Say What They Think | [解説](paper_notes_10.md) | [PDF](arxiv/2305.04388/paper.pdf) | v2 |
| [2306.05685](https://arxiv.org/abs/2306.05685) | AI による回答採点と、その偏り | [解説](paper_notes_01.md) | [PDF](arxiv/2306.05685/paper.pdf) | v4 |
| [2307.07697](https://arxiv.org/abs/2307.07697) | 知識の関係をたどりながら答える | [解説](paper_notes_01.md) | [PDF](arxiv/2307.07697/paper.pdf) | v6 |
| [2307.16648](https://arxiv.org/abs/2307.16648) | 言語モデルによる概念体系の学習 | [解説](paper_notes_01.md) | [PDF](arxiv/2307.16648/paper.pdf) | v2 |
| [2307.16699](https://arxiv.org/abs/2307.16699) | 文章から論理形式への変換による概念体系の拡張 | [解説](paper_notes_01.md) | [PDF](arxiv/2307.16699/paper.pdf) | v1 |
| [2309.15817](https://arxiv.org/abs/2309.15817) | 模擬ツール環境で AI の危険な操作を見つける | [解説](paper_notes_01.md) | [PDF](arxiv/2309.15817/paper.pdf) | v2 |
| [2310.01798](https://arxiv.org/abs/2310.01798) | 外部の根拠なしの自己修正には限界がある | [解説](paper_notes_01.md) | [PDF](arxiv/2310.01798/paper.pdf) | v2 |
| [2310.06816](https://arxiv.org/abs/2310.06816) | 検索用ベクトルから元の文章を復元する | [解説](paper_notes_02.md) | [PDF](arxiv/2310.06816/paper.pdf) | v1 |
| [2310.08560](https://arxiv.org/abs/2310.08560) | 長い対話のための階層的な記憶 | [解説](paper_notes_02.md) | [PDF](arxiv/2310.08560/paper.pdf) | v2 |
| [2311.07509](https://arxiv.org/abs/2311.07509) | 企業の質問に対する関係データと SQL の比較 | [解説](paper_notes_02.md) | [PDF](arxiv/2311.07509/paper.pdf) | v1 |
| [2402.07456](https://arxiv.org/abs/2402.07456) | 操作手順を蓄積する汎用計算機操作支援 | [解説](paper_notes_02.md) | [PDF](arxiv/2402.07456/paper.pdf) | v2 |
| [2402.11163](https://arxiv.org/abs/2402.11163) | 知識グラフ上の複雑な質問を道具で解く | [解説](paper_notes_02.md) | [PDF](arxiv/2402.11163/paper.pdf) | v1 |
| [2403.02691](https://arxiv.org/abs/2403.02691) | 外部文書に埋め込まれた不正指示の評価 | [解説](paper_notes_02.md) | [PDF](arxiv/2403.02691/paper.pdf) | v3 |
| [2403.04960](https://arxiv.org/abs/2403.04960) | AI アプリ同士の実行を隔離する | [解説](paper_notes_02.md) | [PDF](arxiv/2403.04960/paper.pdf) | v2 |
| [2403.16971](https://arxiv.org/abs/2403.16971) | AI 実行の資源管理を共通層へ集める | [解説](paper_notes_02.md) | [PDF](arxiv/2403.16971/paper.pdf) | v5 |
| [2404.16130](https://arxiv.org/abs/2404.16130) | 文書群全体の傾向を関係グラフと要約から答える | [解説](paper_notes_02.md) | [PDF](arxiv/2404.16130/paper.pdf) | v2 |
| [2405.11706](https://arxiv.org/abs/2405.11706) | 知識構造を使って質問の誤りを検知・修正する | [解説](paper_notes_02.md) | [PDF](arxiv/2405.11706/paper.pdf) | v1 |
| [2405.14831](https://arxiv.org/abs/2405.14831) | HippoRAG | [解説](paper_notes_03.md) | [PDF](arxiv/2405.14831/paper.pdf) | v3 |
| [2405.20362](https://arxiv.org/abs/2405.20362) | Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools | [解説](paper_notes_03.md) | [PDF](arxiv/2405.20362/paper.pdf) | v1 |
| [2406.12045](https://arxiv.org/abs/2406.12045) | τ-bench | [解説](paper_notes_03.md) | [PDF](arxiv/2406.12045/paper.pdf) | v1 |
| [2406.13352](https://arxiv.org/abs/2406.13352) | AgentDojo | [解説](paper_notes_03.md) | [PDF](arxiv/2406.13352/paper.pdf) | v3 |
| [2406.13356](https://arxiv.org/abs/2406.13356) | Unlearning or Obfuscating? | [解説](paper_notes_03.md) | [PDF](arxiv/2406.13356/paper.pdf) | v4 |
| [2407.10805](https://arxiv.org/abs/2407.10805) | Think-on-Graph 2.0 | [解説](paper_notes_03.md) | [PDF](arxiv/2407.10805/paper.pdf) | v7 |
| [2407.12784](https://arxiv.org/abs/2407.12784) | AgentPoison | [解説](paper_notes_03.md) | [PDF](arxiv/2407.12784/paper.pdf) | v1 |
| [2408.15256](https://arxiv.org/abs/2408.15256) | OntoChat and Participatory Prompting | [解説](paper_notes_03.md) | [PDF](arxiv/2408.15256/paper.pdf) | v3 |
| [2409.07489](https://arxiv.org/abs/2409.07489) | RAGent | [解説](paper_notes_10.md) | [PDF](arxiv/2409.07489/paper.pdf) | v2 |
| [2409.12917](https://arxiv.org/abs/2409.12917) | Training Language Models to Self-Correct via Reinforcement Learning | [解説](paper_notes_03.md) | [PDF](arxiv/2409.12917/paper.pdf) | v2 |
| [2409.19091](https://arxiv.org/abs/2409.19091) | System-Level Defense against Indirect Prompt Injection Attacks | [解説](paper_notes_03.md) | [PDF](arxiv/2409.19091/paper.pdf) | v2 |
| [2410.05779](https://arxiv.org/abs/2410.05779) | LightRAG | [解説](paper_notes_03.md) | [PDF](arxiv/2410.05779/paper.pdf) | v3 |
| [2410.11843](https://arxiv.org/abs/2410.11843) | LLM-based Semantic File System for AIOS | [解説](paper_notes_03.md) | [PDF](arxiv/2410.11843/paper.pdf) | v1 |
| [2411.07763](https://arxiv.org/abs/2411.07763) | Spider 2.0 | [解説](paper_notes_03.md) | [PDF](arxiv/2411.07763/paper.pdf) | v2 |
| [2411.07781](https://arxiv.org/abs/2411.07781) | RedCode | [解説](paper_notes_03.md) | [PDF](arxiv/2411.07781/paper.pdf) | v1 |
| [2411.09601](https://arxiv.org/abs/2411.09601) | Accelerating Knowledge Graph and Ontology Engineering with Large Language Models | [解説](paper_notes_03.md) | [PDF](arxiv/2411.09601/paper.pdf) | v1 |
| [2412.14161](https://arxiv.org/abs/2412.14161) | TheAgentCompany | [解説](paper_notes_03.md) | [PDF](arxiv/2412.14161/paper.pdf) | v3 |
| [2412.15235](https://arxiv.org/abs/2412.15235) | OG-RAG | [解説](paper_notes_03.md) | [PDF](arxiv/2412.15235/paper.pdf) | v1 |
| [2501.13956](https://arxiv.org/abs/2501.13956) | Zep: A Temporal Knowledge Graph Architecture for Agent Memory | [解説](paper_notes_03.md) | [PDF](arxiv/2501.13956/paper.pdf) | v1 |
| [2502.11371](https://arxiv.org/abs/2502.11371) | RAG vs. GraphRAG | [解説](paper_notes_04.md) | [PDF](arxiv/2502.11371/paper.pdf) | v3 |
| [2503.03704](https://arxiv.org/abs/2503.03704) | Memory Injection Attacks via Query-Only Interaction | [解説](paper_notes_04.md) | [PDF](arxiv/2503.03704/paper.pdf) | v5 |
| [2503.11444](https://arxiv.org/abs/2503.11444) | Cerebrum (AIOS SDK) | [解説](paper_notes_04.md) | [PDF](arxiv/2503.11444/paper.pdf) | v1 |
| [2503.13657](https://arxiv.org/abs/2503.13657) | Why Do Multi-Agent LLM Systems Fail? | [解説](paper_notes_04.md) | [PDF](arxiv/2503.13657/paper.pdf) | v3 |
| [2503.18666](https://arxiv.org/abs/2503.18666) | AgentSpec | [解説](paper_notes_04.md) | [PDF](arxiv/2503.18666/paper.pdf) | v3 |
| [2503.18813](https://arxiv.org/abs/2503.18813) | Defeating Prompt Injections by Design | [解説](paper_notes_04.md) | [PDF](arxiv/2503.18813/paper.pdf) | v2 |
| [2504.00018](https://arxiv.org/abs/2504.00018) | SandboxEval | [解説](paper_notes_04.md) | [PDF](arxiv/2504.00018/paper.pdf) | v1 |
| [2504.11703](https://arxiv.org/abs/2504.11703) | Progent | [解説](paper_notes_04.md) | [PDF](arxiv/2504.11703/paper.pdf) | v3 |
| [2504.18575](https://arxiv.org/abs/2504.18575) | WASP | [解説](paper_notes_04.md) | [PDF](arxiv/2504.18575/paper.pdf) | v3 |
| [2505.01538](https://arxiv.org/abs/2505.01538) | HONEYBEE | [解説](paper_notes_10.md) | [PDF](arxiv/2505.01538/paper.pdf) | v3 |
| [2505.05410](https://arxiv.org/abs/2505.05410) | Reasoning Models Don’t Always Say What They Think | [解説](paper_notes_10.md) | [PDF](arxiv/2505.05410/paper.pdf) | v1 |
| [2505.21936](https://arxiv.org/abs/2505.21936) | RedTeamCUA | [解説](paper_notes_04.md) | [PDF](arxiv/2505.21936/paper.pdf) | v5 |
| [2505.22101](https://arxiv.org/abs/2505.22101) | MemOS (Short Version) | [解説](paper_notes_04.md) | [PDF](arxiv/2505.22101/paper.pdf) | v1 |
| [2505.22954](https://arxiv.org/abs/2505.22954) | Darwin Gödel Machine | [解説](paper_notes_04.md) | [PDF](arxiv/2505.22954/paper.pdf) | v3 |
| [2505.23643](https://arxiv.org/abs/2505.23643) | Securing AI Agents with Information-Flow Control | [解説](paper_notes_04.md) | [PDF](arxiv/2505.23643/paper.pdf) | v2 |
| [2506.08837](https://arxiv.org/abs/2506.08837) | Design Patterns for Securing LLM Agents | [解説](paper_notes_04.md) | [PDF](arxiv/2506.08837/paper.pdf) | v3 |
| [2506.12618](https://arxiv.org/abs/2506.12618) | OpenUnlearning | [解説](paper_notes_04.md) | [PDF](arxiv/2506.12618/paper.pdf) | v2 |
| [2506.14866](https://arxiv.org/abs/2506.14866) | OS-Harm | [解説](paper_notes_05.md) | [PDF](arxiv/2506.14866/paper.pdf) | v2 |
| [2507.02735](https://arxiv.org/abs/2507.02735) | Meta-SecAlign | [解説](paper_notes_05.md) | [PDF](arxiv/2507.02735/paper.pdf) | v4 |
| [2507.03724](https://arxiv.org/abs/2507.03724) | MemOS: A Memory OS for AI System | [解説](paper_notes_05.md) | [PDF](arxiv/2507.03724/paper.pdf) | v4 |
| [2507.08432](https://arxiv.org/abs/2507.08432) | xpSHACL | [解説](paper_notes_05.md) | [PDF](arxiv/2507.08432/paper.pdf) | v1 |
| [2507.09089](https://arxiv.org/abs/2507.09089) | Early-2025 AI and Developer Productivity | [解説](paper_notes_05.md) | [PDF](arxiv/2507.09089/paper.pdf) | v2 |
| [2509.10540](https://arxiv.org/abs/2509.10540) | EchoLeak | [解説](paper_notes_05.md) | [PDF](arxiv/2509.10540/paper.pdf) | v1 |
| [2509.25926](https://arxiv.org/abs/2509.25926) | Type-Directed Privilege Separation | [解説](paper_notes_05.md) | [PDF](arxiv/2509.25926/paper.pdf) | v2 |
| [2509.26354](https://arxiv.org/abs/2509.26354) | Your Agent May Misevolve | [解説](paper_notes_05.md) | [PDF](arxiv/2509.26354/paper.pdf) | v2 |
| [2510.09023](https://arxiv.org/abs/2510.09023) | The Attacker Moves Second | [解説](paper_notes_05.md) | [PDF](arxiv/2510.09023/paper.pdf) | v1 |
| [2510.12469](https://arxiv.org/abs/2510.12469) | Proof of Cloud | [解説](paper_notes_05.md) | [PDF](arxiv/2510.12469/paper.pdf) | v2 |
| [2510.15001](https://arxiv.org/abs/2510.15001) | VaultGemma | [解説](paper_notes_05.md) | [PDF](arxiv/2510.15001/paper.pdf) | v2 |
| [2511.15203](https://arxiv.org/abs/2511.15203) | IPI-Centric LLM Agent Defense Frameworks | [解説](paper_notes_05.md) | [PDF](arxiv/2511.15203/paper.pdf) | v1 |
| [2511.17959](https://arxiv.org/abs/2511.17959) | Towards Automating Data Access Permissions | [解説](paper_notes_10.md) | [PDF](arxiv/2511.17959/paper.pdf) | v1 |
| [2512.01295](https://arxiv.org/abs/2512.01295) | Systems Security Foundations for Agentic Computing | [解説](paper_notes_05.md) | [PDF](arxiv/2512.01295/paper.pdf) | v2 |
| [2512.11147](https://arxiv.org/abs/2512.11147) | MiniScope | [解説](paper_notes_05.md) | [PDF](arxiv/2512.11147/paper.pdf) | v1 |
| [2512.12594](https://arxiv.org/abs/2512.12594) | CeLLMate | [解説](paper_notes_05.md) | [PDF](arxiv/2512.12594/paper.pdf) | v2 |
| [2512.12806](https://arxiv.org/abs/2512.12806) | Fault-Tolerant Sandboxing for AI Coding Agents | [解説](paper_notes_05.md) | [PDF](arxiv/2512.12806/paper.pdf) | v1 |
| [2512.20275](https://arxiv.org/abs/2512.20275) | G-SPEC | [解説](paper_notes_05.md) | [PDF](arxiv/2512.20275/paper.pdf) | v1 |
| [2601.05504](https://arxiv.org/abs/2601.05504) | Memory Poisoning Attack and Defense | [解説](paper_notes_06.md) | [PDF](arxiv/2601.05504/paper.pdf) | v2 |
| [2601.11893](https://arxiv.org/abs/2601.11893) | Mandatory Access Control for LLM-Based Agents | [解説](paper_notes_06.md) | [PDF](arxiv/2601.11893/paper.pdf) | v1 |
| [2601.14242](https://arxiv.org/abs/2601.14242) | APEX–Agents | [解説](paper_notes_06.md) | [PDF](arxiv/2601.14242/paper.pdf) | v3 |
| [2601.18511](https://arxiv.org/abs/2601.18511) | Scaling up FHE-based Privacy-Preserving ML | [解説](paper_notes_06.md) | [PDF](arxiv/2601.18511/paper.pdf) | v2 |
| [2602.03117](https://arxiv.org/abs/2602.03117) | AgentDyn | [解説](paper_notes_06.md) | [PDF](arxiv/2602.03117/paper.pdf) | v3 |
| [2602.08235](https://arxiv.org/abs/2602.08235) | When Benign Inputs Lead to Severe Harms | [解説](paper_notes_06.md) | [PDF](arxiv/2602.08235/paper.pdf) | v2 |
| [2602.08668](https://arxiv.org/abs/2602.08668) | Retrieval Pivot Attacks in Hybrid RAG | [解説](paper_notes_10.md) | [PDF](arxiv/2602.08668/paper.pdf) | v3 |
| [2602.10133](https://arxiv.org/abs/2602.10133) | AgentTrace | [解説](paper_notes_10.md) | [PDF](arxiv/2602.10133/paper.pdf) | v1 |
| [2602.14211](https://arxiv.org/abs/2602.14211) | SkillJect | [解説](paper_notes_06.md) | [PDF](arxiv/2602.14211/paper.pdf) | v3 |
| [2602.20021](https://arxiv.org/abs/2602.20021) | Agents of Chaos | [解説](paper_notes_06.md) | [PDF](arxiv/2602.20021/paper.pdf) | v1 |
| [2603.02277](https://arxiv.org/abs/2603.02277) | Container Sandbox Escape | [解説](paper_notes_06.md) | [PDF](arxiv/2603.02277/paper.pdf) | v3 |
| [2603.08938](https://arxiv.org/abs/2603.08938) | AgentOS | [解説](paper_notes_06.md) | [PDF](arxiv/2603.08938/paper.pdf) | v2 |
| [2603.13424](https://arxiv.org/abs/2603.13424) | Agent Privilege Separation in OpenClaw | [解説](paper_notes_06.md) | [PDF](arxiv/2603.13424/paper.pdf) | v1 |
| [2603.15714](https://arxiv.org/abs/2603.15714) | Large-Scale Public Prompt Injection Competition | [解説](paper_notes_06.md) | [PDF](arxiv/2603.15714/paper.pdf) | v1 |
| [2603.24775](https://arxiv.org/abs/2603.24775) | Agent Identity Protocol | [解説](paper_notes_06.md) | [PDF](arxiv/2603.24775/paper.pdf) | v1 |
| [2603.27517](https://arxiv.org/abs/2603.27517) | Security Analysis of OpenClaw | [解説](paper_notes_06.md) | [PDF](arxiv/2603.27517/paper.pdf) | v3 |
| [2604.00169](https://arxiv.org/abs/2604.00169) | System-Level Characterization of MPC and FHE | [解説](paper_notes_06.md) | [PDF](arxiv/2604.00169/paper.pdf) | v2 |
| [2604.01344](https://arxiv.org/abs/2604.01344) | IDEA2 | [解説](paper_notes_06.md) | [PDF](arxiv/2604.01344/paper.pdf) | v1 |
| [2604.03081](https://arxiv.org/abs/2604.03081) | Supply-Chain Poisoning of Agent Skills | [解説](paper_notes_07.md) | [PDF](arxiv/2604.03081/paper.pdf) | v1 |
| [2604.08304](https://arxiv.org/abs/2604.08304) | Securing Retrieval-Augmented Generation | [解説](paper_notes_10.md) | [PDF](arxiv/2604.08304/paper.pdf) | v3 |
| [2604.08552](https://arxiv.org/abs/2604.08552) | Ontology-Constrained Biomedical Metadata | [解説](paper_notes_07.md) | [PDF](arxiv/2604.08552/paper.pdf) | not-detected |
| [2604.18231](https://arxiv.org/abs/2604.18231) | AgenTEE | [解説](paper_notes_07.md) | [PDF](arxiv/2604.18231/paper.pdf) | v2 |
| [2604.23178](https://arxiv.org/abs/2604.23178) | Judging the Judges | [解説](paper_notes_07.md) | [PDF](arxiv/2604.23178/paper.pdf) | v2 |
| [2604.23280](https://arxiv.org/abs/2604.23280) | AI Identity | [解説](paper_notes_07.md) | [PDF](arxiv/2604.23280/paper.pdf) | v1 |
| [2604.25149](https://arxiv.org/abs/2604.25149) | Semantic Layers for Reliable Data Analytics | [解説](paper_notes_07.md) | [PDF](arxiv/2604.25149/paper.pdf) | not-detected |
| [2604.26851](https://arxiv.org/abs/2604.26851) | Resume-ing Control | [解説](paper_notes_07.md) | [PDF](arxiv/2604.26851/paper.pdf) | v1 |
| [2605.03213](https://arxiv.org/abs/2605.03213) | When Agents Handle Secrets | [解説](paper_notes_07.md) | [PDF](arxiv/2605.03213/paper.pdf) | v2 |
| [2605.08442](https://arxiv.org/abs/2605.08442) | Injection–Execution Dissociation | [解説](paper_notes_07.md) | [PDF](arxiv/2605.08442/paper.pdf) | v5 |
| [2605.09045](https://arxiv.org/abs/2605.09045) | Containment Verification | [解説](paper_notes_07.md) | [PDF](arxiv/2605.09045/paper.pdf) | v2 |
| [2605.11418](https://arxiv.org/abs/2605.11418) | Under the Hood of SKILL.md | [解説](paper_notes_07.md) | [PDF](arxiv/2605.11418/paper.pdf) | v1 |
| [2605.13471](https://arxiv.org/abs/2605.13471) | Sleeper Channels and Provenance Gates | [解説](paper_notes_07.md) | [PDF](arxiv/2605.13471/paper.pdf) | v1 |
| [2605.14932](https://arxiv.org/abs/2605.14932) | Securing AI Agents Like Operating Systems | [解説](paper_notes_07.md) | [PDF](arxiv/2605.14932/paper.pdf) | v1 |
| [2605.15338](https://arxiv.org/abs/2605.15338) | Hidden in Memory | [解説](paper_notes_07.md) | [PDF](arxiv/2605.15338/paper.pdf) | v2 |
| [2605.17634](https://arxiv.org/abs/2605.17634) | AI Agents May Always Fall for Prompt Injections | [解説](paper_notes_07.md) | [PDF](arxiv/2605.17634/paper.pdf) | v1 |
| [2605.18930](https://arxiv.org/abs/2605.18930) | OEP | [解説](paper_notes_07.md) | [PDF](arxiv/2605.18930/paper.pdf) | v1 |
| [2605.22781](https://arxiv.org/abs/2605.22781) | DeltaBox | [解説](paper_notes_07.md) | [PDF](arxiv/2605.22781/paper.pdf) | v2 |
| [2606.01508](https://arxiv.org/abs/2606.01508) | Agent Operating Systems | [解説](paper_notes_08.md) | [PDF](arxiv/2606.01508/paper.pdf) | not-detected |
| [2606.04141](https://arxiv.org/abs/2606.04141) | Caught in the Act(ivation) | [解説](paper_notes_08.md) | [PDF](arxiv/2606.04141/paper.pdf) | v1 |
| [2606.04329](https://arxiv.org/abs/2606.04329) | From Untrusted Input to Trusted Memory | [解説](paper_notes_08.md) | [PDF](arxiv/2606.04329/paper.pdf) | v2 |
| [2606.04425](https://arxiv.org/abs/2606.04425) | Cross-Session Stored Prompt Injection | [解説](paper_notes_08.md) | [PDF](arxiv/2606.04425/paper.pdf) | v2 |
| [2606.05233](https://arxiv.org/abs/2606.05233) | Domain-Conditioned Safety | [解説](paper_notes_08.md) | [PDF](arxiv/2606.05233/paper.pdf) | v1 |
| [2606.05634](https://arxiv.org/abs/2606.05634) | Bootstrapping Semantic Layer from Execution | [解説](paper_notes_08.md) | [PDF](arxiv/2606.05634/paper.pdf) | v1 |
| [2606.08433](https://arxiv.org/abs/2606.08433) | AI Code Sandboxes: Part 1 | [解説](paper_notes_08.md) | [PDF](arxiv/2606.08433/paper.pdf) | v1 |
| [2606.23075](https://arxiv.org/abs/2606.23075) | Safety in Self-Evolving LLM Agent Systems | [解説](paper_notes_08.md) | [PDF](arxiv/2606.23075/paper.pdf) | v1 |
| [2606.27379](https://arxiv.org/abs/2606.27379) | The Term Machine Unlearning Is Overused | [解説](paper_notes_08.md) | [PDF](arxiv/2606.27379/paper.pdf) | v1 |
| [2607.05518](https://arxiv.org/abs/2607.05518) | aiAuthZ | [解説](paper_notes_08.md) | [PDF](arxiv/2607.05518/paper.pdf) | v1 |
| [2607.22571](https://arxiv.org/abs/2607.22571) | SCAIR | [解説](paper_notes_08.md) | [PDF](arxiv/2607.22571/paper.pdf) | v1 |
| [2607.24300](https://arxiv.org/abs/2607.24300) | Self-Authored Verification Is Unreliable | [解説](paper_notes_08.md) | [PDF](arxiv/2607.24300/paper.pdf) | v1 |
| [2607.24625](https://arxiv.org/abs/2607.24625) | APPA | [解説](paper_notes_08.md) | [PDF](arxiv/2607.24625/paper.pdf) | v2 |
| [2607.25076](https://arxiv.org/abs/2607.25076) | Towards an Agent Operating System | [解説](paper_notes_08.md) | [PDF](arxiv/2607.25076/paper.pdf) | v1 |
| [2608.01759](https://arxiv.org/abs/2608.01759) | Benign Alone, Harmful Together | [解説](paper_notes_08.md) | [PDF](arxiv/2608.01759/paper.pdf) | v1 |
| [2608.06477](https://arxiv.org/abs/2608.06477) | StepJack | [解説](paper_notes_08.md) | [PDF](arxiv/2608.06477/paper.pdf) | v1 |
| [2608.06984](https://arxiv.org/abs/2608.06984) | HarnessSafe | [解説](paper_notes_08.md) | [PDF](arxiv/2608.06984/paper.pdf) | v1 |
| [2608.07530](https://arxiv.org/abs/2608.07530) | NL2SHACL-Bench | [解説](paper_notes_09.md) | [PDF](arxiv/2608.07530/paper.pdf) | v2 |
| [2608.09028](https://arxiv.org/abs/2608.09028) | PolicyKG | [解説](paper_notes_09.md) | [PDF](arxiv/2608.09028/paper.pdf) | v1 |
| [2608.09732](https://arxiv.org/abs/2608.09732) | ColluSkill | [解説](paper_notes_09.md) | [PDF](arxiv/2608.09732/paper.pdf) | v1 |
| [2608.11323](https://arxiv.org/abs/2608.11323) | Deployment Decision Reliability | [解説](paper_notes_09.md) | [PDF](arxiv/2608.11323/paper.pdf) | v1 |
| [2608.12851](https://arxiv.org/abs/2608.12851) | Practice Makes Unsafe | [解説](paper_notes_09.md) | [PDF](arxiv/2608.12851/paper.pdf) | v1 |
| [2608.26108](https://arxiv.org/abs/2608.26108) | Agentic AI Containment Architecture | [解説](paper_notes_09.md) | [PDF](arxiv/2608.26108/paper.pdf) | not-detected |
| [2608.26157](https://arxiv.org/abs/2608.26157) | GROUND | [解説](paper_notes_09.md) | [PDF](arxiv/2608.26157/paper.pdf) | v1 |
| [2608.26575](https://arxiv.org/abs/2608.26575) | Confidential Computing on Blackwell GPUs | [解説](paper_notes_09.md) | [PDF](arxiv/2608.26575/paper.pdf) | v2 |
| [2608.27800](https://arxiv.org/abs/2608.27800) | ContextLeak | [解説](paper_notes_09.md) | [PDF](arxiv/2608.27800/paper.pdf) | v1 |
| [2609.00069](https://arxiv.org/abs/2609.00069) | Auditing Harness Tampering | [解説](paper_notes_09.md) | [PDF](arxiv/2609.00069/paper.pdf) | v1 |
| [2609.17817](https://arxiv.org/abs/2609.17817) | Reflections on Trusting Trust, Revisited | [解説](paper_notes_09.md) | [PDF](arxiv/2609.17817/paper.pdf) | v1 |
| [2609.23700](https://arxiv.org/abs/2609.23700) | When the Agent Becomes the Kernel | [解説](paper_notes_09.md) | [PDF](arxiv/2609.23700/paper.pdf) | v1 |
| [2609.26457](https://arxiv.org/abs/2609.26457) | Recursive Self-Improvement of AI Research Agents | [解説](paper_notes_09.md) | [PDF](arxiv/2609.26457/paper.pdf) | v1 |
| [2609.31039](https://arxiv.org/abs/2609.31039) | MetaPermit | [解説](paper_notes_10.md) | [PDF](arxiv/2609.31039/paper.pdf) | v1 |
| [2609.32390](https://arxiv.org/abs/2609.32390) | Reward Hacking and Agent Containment Failure | [解説](paper_notes_09.md) | [PDF](arxiv/2609.32390/paper.pdf) | not-detected |
| [2609.35596](https://arxiv.org/abs/2609.35596) | SEABench | [解説](paper_notes_09.md) | [PDF](arxiv/2609.35596/paper.pdf) | v2 |
| [2609.38983](https://arxiv.org/abs/2609.38983) | Approval Laundering | [解説](paper_notes_09.md) | [PDF](arxiv/2609.38983/paper.pdf) | v1 |
| [2610.01073](https://arxiv.org/abs/2610.01073) | Safety Must Survive Self-Improvement | [解説](paper_notes_09.md) | [PDF](arxiv/2610.01073/paper.pdf) | v1 |
