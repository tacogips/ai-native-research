---
title: "AI OS / Agent OS: 研究・産業動向・相互運用標準（2026）"
author: claude
kind: survey
subject: AI OS、Agent OS、Agentic OS、エージェント実行隔離、エージェント ID、MCP、A2A、Agent Skills、エージェントセキュリティ
status: idea
maturity: validated
created: 2026-10-02
updated: 2026-10-02
verified: 2026-10-02
tags: [技術, AI OS, Agent OS, エージェント基盤, 隔離, ID, 標準, MCP, A2A, セキュリティ]
relates_to:
  - research/technology/hermes_openai_dots_enterprise.md
  - research/technology/agent_sandbox_isolation_confidential_computing.md
  - research/technology/enterprise_agent_control_plane.md
  - research/technology/ontology_palantir_kinetic_layer.md
summary: 研究系の "Agent OS"（AIOS、MemOS 等）は本番基盤としては停滞し、2026 年の研究は「OS のセキュリティ原則でエージェントを守る」方向に移った。産業側は「専用 ID・隔離実行環境・認証情報の sandbox 外配置・承認ゲートと監査」の 4 部品に収束しつつあり、MCP 2026-07-28 版・A2A v1.0 等の標準は中立団体の管理下に入った。AI-only company は既存 OS/クラウドの隔離・ID・監査をそのまま採用し、LLM を kernel とする構想や自己改善スキルの無審査配布は採らない。
---

# AI OS / Agent OS: 研究・産業動向・相互運用標準（2026）

本ノートは、自律エージェントを動かす「OS 層」（スケジューラ、メモリ、隔離、ID、権限、監査、相互運用プロトコル）について、研究・産業・標準の 2026-10-02 時点の状況を整理する。既存調査（information_flow_control_and_exfiltration.md の FIDES/CaMeL/lethal trifecta、isolation_durable_execution_prompt_injection.md の隔離と Temporal、authorization_zanzibar_openfga_cedar.md の OpenFGA/Cedar 二層認可、エージェントメモリ調査）は再説明しない。

既存調査との差分は、(a) 「Agent OS」という枠組みで研究・製品がどこまで収束したか、(b) Windows・OpenAI・Meta・Anthropic などの製品がどの OS 機能（ID、隔離、秘密情報、承認、監査）を実装したか、(c) MCP/A2A/Skills 等の標準を OS の syscall/IPC/パッケージとして読み替えた場合の成熟度、の 3 点である。

## 1. 要約(推奨)

主要な知見（原資料 0 章）:

- **研究系の "Agent OS"**（AIOS、MemOS、MemGPT など）は、スケジューラ、コンテキスト/メモリ管理、ストレージ、アクセス制御を「カーネル」にまとめる考え方を示した。AIOS の GitHub ニュースは 2025-07 で止まっており、本番基盤として使われている形跡は見当たらない。2026 年の論文は「エージェントを OS のセキュリティ原則（isolation、privilege separation、mediation）で守る」方向に移っている（arXiv 2605.14932、2609.23700、2606.01508、2607.25076）[14][15][16][17]。
- **産業側の "Agentic OS"** は 4 つの部品に収束しつつある。(1) エージェント専用 ID（Windows agent account / Entra Agent ID、OpenAI specialist dots）、(2) 隔離実行環境（Windows Agent Workspace/MXC、OpenAI dots と Meta Muse の専用クラウド VM、Anthropic Managed Agents の sandbox）、(3) 認証情報を sandbox の外に置く（Anthropic vault/proxy、dots のパスワード非開示サインイン）、(4) 承認ゲートと監査（dots の Custom Rules、Copilot Actions の takeover）。
- **"syscall" に当たる標準**はいずれも中立団体の管理下に入った。MCP は最新仕様 2026-07-28 版（stateless 化、extensions framework）、A2A は v1.0（2026-03、Linux Foundation）、AGENTS.md と Agent Skills は事実上の標準、AP2 は FIDO Alliance へ移管、ACP は仕様継続だが ChatGPT の Instant Checkout は 2026-03 に終了。
- **結論**: 成熟しているのは「既存 OS/クラウドの隔離・ID・監査をエージェントに当てはめる」部分で、今すぐ採用できる。LLM 自身を kernel にする構想や、自己改善スキルの無審査配布はまだ hype か危険な段階にある（OpenClaw の脆弱性事例）。

推奨（原資料 5 章に基づく）:

1. **エージェント 1 体ごとに独立した非人間 ID を発行する。** Entra Agent ID 型の blueprint と A2A signed card にならい、人間の sponsor と有効期限を必須にする。
2. **brain と hands を分離し、使い捨て sandbox で実行する。** タスク単位の VM / gVisor sandbox を用意し、エージェントループは sandbox の外に置く（Managed Agents 型）。ネットワークは deny-by-default で egress proxy を通す。
3. **秘密情報は vault と proxy で注入し、モデルにも sandbox にも平文を見せない。** Anthropic vault/proxy、dots のパスワード非開示、Muse のパスワード非アクセスが同じ方向を示している。
4. **権限は「自動では狭まる方向にしか変わらない」ようにする。** Progent/CaMeL の考え方で、拡大には承認を要求し、confidential と untrusted のラベルで IFC をかける（既存調査の FIDES/CaMeL 推奨と同じ線上）。
5. **自己改善の成果物は PR と同じ扱いにする。** エージェントが作ったスキルや設定は、別のレビュー用エージェントと静的検査を通し、署名してから昇格させる。外部マーケットのスキルは原則禁止（Windows の署名要件にならう）。
6. **監視を別系統で持つ。** Muse の Sentinel のように隔離された監視エージェントと append-only ログを置き、kill switch と予算（トークン、費用、レート）上限を外部から強制する。
7. **標準は MCP 2026-07-28・A2A v1.0・AGENTS.md・Skills を採用し、決済は当面人の承認を必須にする。** AP2 と FIDO の動向を待つ。
8. **被害上限は capability の制限で決め、プロンプト検知には頼らない。** 2609.23700 が示すとおり、意味内容の検査には原理的に取りこぼしが残る。

## 2. 研究系 Agent OS

### 2.1 元祖ビジョン

| 項目 | 事実 | 出典 |
|---|---|---|
| Karpathy "LLM OS" | 2023-11-11 に X に投稿。比喩は「LLM＝CPU（GPT-4 Turbo、256 core（batch）、20Hz（tok/s））、RAM＝128K tok、Filesystem＝Ada002」。同月の講演 "Intro to LLMs" でも同じ図を示した | [1] |
| MemGPT: Towards LLMs as Operating Systems | arXiv **2310.08560**（2023-10-12 v1、2024-02-12 v2）。Packer ら（UC Berkeley、Stoica、Gonzalez）。OS のメモリ階層をまねた "virtual context management" を提案。後に Letta になった | [2] |
| Letta（MemGPT の後継） | 自らを "an AI research lab … building machines that learn" と説明し、MemGPT を "The LLM Operating System" と表記。Sleep-time Compute（アイドル時間にコンテキストを推論）や Context Repositories を研究。製品は Letta Agent / Letta Code（`npm i -g @letta-ai/letta-code`） | [3] |
| OS-Copilot / FRIDAY | arXiv **2402.07456**（2024-02）。OS 全体（web、terminal、ファイル、アプリ）を操作する自己改善エージェント。GAIA で従来手法を 35% 上回った | [4] |

### 2.2 AIOS 系（Rutgers, agiresearch）

| 論文 | arXiv ID / 会議 | 要点 |
|---|---|---|
| AIOS: LLM Agent Operating System | **2403.16971**（v1 2024-03-25、v5 2025-08-12）、**COLM 2025** | LLM 固有のリソースとサービスを "AIOS kernel" に分離し、scheduling、context、memory、storage、access control を提供。各種フレームワークのエージェント実行が**最大 2.1 倍速** [5] |
| Cerebrum (AIOS SDK) | **2503.11444**（2025-03-14）、**NAACL 2025 System Demo** | LLM/memory/storage/tool の 4 層 SDK と Agent Hub（バージョン管理、依存管理）[6] |
| LSFS: From Commands to Prompts（LLM-based Semantic File System） | **2410.11843**、**ICLR 2025** | 埋め込みでファイルを索引し、意味検索・グルーピング・rollback を syscall 化。意味検索の精度が 20–24% 向上、ファイルアクセスが最大 92% 高速 [7][8] |

- **現状**: GitHub は 6.4k stars。最新ニュースは 2025-07-08 の COLM 採択で、Local/Remote Kernel の 2 モードを持つ [9]。2026 年に入ってからの大きな更新は見当たらず、研究プロトタイプ段階にとどまると評価する。

### 2.3 メモリ OS（MemOS）

| 論文 / 実装 | 要点 |
|---|---|
| MemOS: A Memory OS for AI System | arXiv **2507.03724**（2025-07-04、改訂 2025-12-03、著者 39 名、上海交通大学・浙江大学ほか）。plaintext、activation（KV）、parametric の 3 種類のメモリを "MemCube"（provenance と versioning のメタデータ付き）で統一的に扱う [10] |
| MemOS（短報） | arXiv **2505.22101**「An Operating System for Memory-Augmented Generation (MAG)」[11] |
| 実装（MemTensor/MemOS） | Apache-2.0、11.7k stars。リポジトリ上の自己申告値は LoCoMo 88.83、LongMemEval 89.20、トークン 35.24% 削減、OpenClaw のタスク完了率を 36.63% から 50.87% に改善。最新更新は 2026-08-17。Multi-Cube で隔離メモリと共有メモリを持てる。※ベンチマーク値は第三者の再現が取れていないため**未検証** [12]。2026-10-02 に arXiv API で「MemOS かつ LoCoMo / LongMemEval」を要旨に含む論文を検索した（計 4 件: 2601.21545 ShardMemo、2604.07877 MemReader、2607.22562 SF-AMS、2609.07471 MEMO）。上記の自己申告値を再現・確認したと要旨に書いている論文はなかった。MemReader は MemOS に統合済みと書いており、MemOS 側の関係者による研究と見られる（推論）[103] |

既存のメモリ調査（メモリを正本にしない、4 種類の物理分離）との接続: MemCube の provenance/versioning メタデータは、エピソード記憶の出所追跡に相当する（推論）。

### 2.4 2026 年の "Agentic OS" 論文（すべて arXiv で ID 確認済み）

| arXiv | タイトル / 著者 / 日付 | 主張 |
|---|---|---|
| **2603.08938** | AgentOS: From Application Silos to a Natural Language-Driven Data Ecosystem（Liu, Pei ほか、2026-03-09） | GUI の OS を "Personal Agent OS" に置き換える構想。Agent Kernel がタスク分解と複数エージェントの調整を担い、アプリは Skills-as-Modules になる。**定量評価はなく構想のみ** [13] |
| **2606.01508** | Agent Operating Systems (AOS)（Sharma, Shah、2026-06-01） | AOS を scheduler、context/memory、tool/capability registry、policy enforcement、audit の 5 要素に分解。既存 OS を置き換えるのではなく、その上の control plane とする [14] |
| **2607.25076** | Towards an Agent Operating System – Lessons from Classical and Cloud OS（Steinder, Franke、2026-07-27） | POSIX や Kubernetes のように抽象と標準へ収束させるべきと主張。合意された抽象がない限り移植性も合成も実現できない [15] |
| **2605.14932** | Toward Securing AI Agents Like Operating Systems（Pirch, Holz, Rieck ほか、2026-05-14） | 広く使われている 4 つのエージェントの事例研究で「複数の保護機構が実運用では機能しない」ことを確認。OS 由来の防御で多くは緩和できるが、**設計上安全にできない能力も残る** [16] |
| **2609.23700** | When the Agent Becomes the Kernel: SoK on AI-Native OS Security（Zhang, Sun, Shi、2026-09-20） | provenance に基づく決定論的 mediation と意味内容の解析を区別。入力と行動を列挙済みの集合に制限しない限り「検出できない攻撃が原理的に残る（irreducible residual）」。既存の評価は実際の防御力を過大評価していると批判 [17] |

- 二次情報: ResearchGate に "AgenticOS: An Intent-Oriented Secure OS Architecture"（Ghost Kernel、Agent Capsule など）がある [18]。arXiv ID は確認できず**未検証**。
- **"KernelAGI"**: 該当するプロジェクトや論文は見つからなかった。前回の検索で出たのは無関係の GPU kernel 生成エージェント（arXiv 2512.23424）などだけだった。2026-10-02 に再確認した結果、arXiv API の `all:KernelAGI` と `all:"Kernel AGI"` はどちらも 0 件、`gh search repos kernelagi` も 0 件だった。`kernel-agi` で検索すると星 0〜2 の無関係な個人リポジトリが出るだけである。**Agent OS の文脈で参照すべき「KernelAGI」は存在しないと判断する**（確認できた範囲での判断）。

### 2.5 セキュリティ重視の Agent OS 研究

CaMeL と FIDES は既存調査で扱い済みのため、ここでは他方式との位置関係のみ示す。

| arXiv | 名前 | 方式と結果 |
|---|---|---|
| **2403.04960** | IsolateGPT（v1 の名称は SecGPT。Wu, Roesner, Kohno, Iqbal ら）、**NDSS 2025** | hub-and-spoke 型の実行隔離。サードパーティアプリ（spoke）をそれぞれ隔離し、hub が仲介する。**4 分の 3 のクエリで overhead 30% 未満** [19] |
| **2409.19091** | f-secure LLM system（Wu, Cecchetti, Xiao） | IFC。planner と executor を分け、security monitor が信頼できない入力を planning から締め出す [20] |
| **2503.18813** | CaMeL（Google DeepMind ほか） | 信頼できるクエリから control flow と data flow を抽出し、信頼できないデータが制御フローに影響できないようにする。capability で流出を防ぐ。AgentDojo で**証明可能な安全性付き 77%**（防御なしは 84%、v1 では 67%）[21] |
| **2505.23643** | FIDES（Microsoft、Costa, Köpf ほか、2025-05-29） | confidentiality と integrity のラベルを追跡し、決定論的にポリシーを強制する planner。OSS 実装あり（github.com/microsoft/fides）。ただし第三者が "security label forging" を報告（APIsec）[22][23][24] |
| **2504.11703** | Progent（Dawn Song ら） | ツール名と引数に対する symbolic ポリシーで least privilege を実現。SMT solver で、権限を狭める更新は自動適用、広げる更新は承認必須（monotonic confinement）[25] |
| **2601.11893** | SEAgent（2026-01-17） | 属性ベースの Mandatory Access Control と情報フロー追跡。複数エージェント間の privilege escalation を低い誤検知率と無視できる overhead で遮断 [26] |
| **2512.01295** | Systems Security Foundations for Agentic Computing（Christodorescu, Fernandes, Jha, Rehberger ほか、Google/UCSD/UW、2025-12-02） | IEEE SAGAI 2025 ワークショップの成果。実攻撃の事例 11 件と新しい研究課題を整理 [27] |

## 3. 産業の動き

### 3.1 Microsoft Windows（最も OS らしい実装）

**2025-10〜11: Copilot Actions / Experimental agentic features** [29][30][31]

| 機能 | 内容 |
|---|---|
| 既定状態 | 無効。Settings > System > AI components > Agent tools で有効化 |
| Agent accounts | ユーザーとは別の "standard account"。エージェント単位の認可とアクセス制御 |
| Agent workspace | エージェント専用デスクトップを持つ隔離環境。MSRC のサービシング基準に沿ったセキュリティ境界上に構築 |
| ファイルアクセス | 既知フォルダ（Documents、Downloads、Desktop、Pictures）に限定。それ以外は都度認可。ACL で保護 |
| 原則 "Operational trust" | エージェントに署名必須、失効・遮断可能。ユーザーは監視と takeover が可能 |

**MCP on Windows / On-device Agent Registry（ODR）** [32]

- Ignite 2025 で public preview。connector（MCP サーバ）は既定で隔離環境に入り、それぞれ独自の ID と監査記録を持つ。File Explorer と Settings の connector が同梱。
- **訂正（2026-10-02）**: Windows Insider Blog で確認したところ、Builds 26100.8313 と 26200.8313 は 2026-04-17 に Release Preview Channel に出ていた [93]。ただしこのリリースノートには MCP、ODR、agent connector への言及がない。agentic 関連で書かれているのは「taskbar からエージェントを監視する機能」だけで、first-party と third-party のアプリに対応し、最初の採用例は Microsoft 365 Copilot アプリの Researcher、API は Windows.UI.Shell.Tasks である。二次情報 [35] にあった「このビルドで ODR/MCP が Release Preview に入った」という対応付けは一次情報では確認できない。

**Build 2026（2026-06-02、一次情報）** [33]

- エージェントに local ID または Entra をバックとする ID を割り当て、行動はすべてその ID に帰属させる。
- **Microsoft Execution Containers（MXC）** を early preview で発表。"policy-driven execution layer" で、隔離は process（GitHub Copilot CLI が採用）と session（デスクトップとクリップボードを分離）の 2 段階。micro-VM と Linux container はロードマップ上。
- **Windows 365 for Agents** が GA（エージェント用 Cloud PC）。Agent 365 から Entra と Intune のポリシーで統制。
- **OpenClaw、NVIDIA OpenShell、Hermes Agent が MXC と統合**。
- 二次情報 [34] にあった 3 点を一次情報で確認した（2026-10-02）。
  - **W365 for Agents の価格**: 時間単位の従量課金。米国リージョンの on-demand は **$0.40/VM/時間**、欧州と英国は $0.52、アジアとインドは $0.56、豪州は $0.58。常時稼働の Cloud PC には別途 $5〜10/VM/月の固定費がかかる。無料試用は 50 時間。Intune で管理し、Entra ID と統合し、Agent 365 から統制する [94]。
  - **Agent Governance Toolkit**: GitHub の `microsoft/agent-governance-toolkit`（MIT、2026-03-02 作成、約 6.4k stars、最新 v4.1.0 は 2026-06-09）。説明文は "Policy enforcement, zero-trust identity, execution sandboxing, and reliability engineering for autonomous AI agents. Covers 10/10 OWASP Agentic Top 10"。OWASP 10 項目すべてへの対応は Microsoft 自身の主張である [95]。
  - **Microsoft Agent Framework**: python-1.0.0 と dotnet-1.0.0 は **2026-04-02** に GitHub でリリースされた（Build 2026 より前）[97]。Microsoft Learn は "the direct successor, created by the same teams" と説明し、Semantic Kernel と AutoGen の次世代版と位置付けている。Go 版は public preview。tool 承認、context compaction、メモリ、observability を持つ "Harness Agent" も含む [96]。

**Entra Agent ID と Agent 365** [36][37]

- Entra Agent ID は agent identity blueprint（親子関係を持つ雛形）を提供し、OAuth 2.0、MCP、A2A に対応。Conditional Access、Identity Protection、ライフサイクル管理、ネットワーク制御、サインイン/監査ログをエージェントにも適用できる。AWS Bedrock や n8n など他社エージェントも sidecar で取り込める。
- Agent 365 は GA。単体で $15/user/月、M365 E7（$99/user/月）に含まれる。registry、ownerless agent の検出、Defender と Purview の統合を提供。

### 3.2 OpenAI（"ChatGPT as Agent OS"）

**dots（DevDay 2026、2026-09-29）** [38][39][40]

| 項目 | 内容 |
|---|---|
| 形態 | "always-on agents"。1 体ごとに**専用のクラウドコンピュータとブラウザ**。モデルは GPT-6 Astra、4,000 以上のアプリと接続 |
| 権限 | built-in rules に加え **Custom Rules（allow / block / require approval）**。read-only の proactive research モードあり。アカウント操作や情報共有は auto-review、パスワード変更などは常に承認必須 |
| 秘密情報 | 保存済みパスワードは**モデルに見せずに**サインイン。監視系が危険を検出すると一時停止 |
| Specialist dots | 独自の ID、認証情報、社内システムへのアクセスを持つ enterprise preview。社内で調達、請求処理、サポート、契約業務に試験導入。Agent 365 との統合を予定 |
| 提供 | Pro と Business（Premium）。Pro は EEA、スイス、英国を除く。Enterprise は beta |

- 公式記事 [43] は WebFetch では 403 だったが、2026-10-02 に r.jina.ai 経由で取得できた。以下を公式記事で確認した。
  - 各 dot が "their own cloud computer, their own browser" を持つ。
  - モデルは GPT-6 Astra、接続できるアプリは 4,000 以上。
  - Custom Rules で "allow specific actions, require approval, or block them" を指定できる。
  - 保存済みパスワードはモデルに見せずに使う。
  - specialist dots は "its own identity, credentials, and access" を持つ。
  - 提供範囲: Pro と Business Premium の対象市場のユーザーには追加料金なしで dot が 1 体付く。Enterprise、Edu、Healthcare は管理者が有効にすれば beta を使える。
  - ChatGPT、Slack、Teams から呼び出せる。

  Pro の地域除外（EEA、スイス、英国）は公式記事では "eligible markets" とだけ書かれており、具体的な国名は報道 [38]〜[40] によるものである。

**その他の DevDay 2026 発表** [41][42]

- Agents API（public beta）: hosted execution、memory、tools、multi-agent、computer use。
- MCP Events: 接続アプリがトリガーとなって自動化を起動。
- Plugin Extensions、Sign in with ChatGPT、OpenAI Marketplace。
- Private Safety Processing（ZDR と自動安全審査）。
- Codex cloud の sandbox。
- [42] はメディアによる "full agent operating system" という表現。
- 公式の DevDay 2026 recap [102] を r.jina.ai 経由で取得した（ページの公開時刻メタデータは 2026-10-02 06:08 GMT）。次の項目が載っていることを確認した: Agents API（computer use を含む）、"MCP events for Plugin automations"、Plugin extensions（サイドバーと対話パネル）、Sign in with ChatGPT、OpenAI Marketplace（Devin、Notion、Vercel など 16 の提携ツール）、Private Safety Processing（ZDR と validated external storage）、Codex cloud 環境、ChatGPT Spaces、GPT-6.1 Sol と Astra Ultrafast。recap 本文には Agents API が "public beta" かどうかの記載がない。この区分はコミュニティ要約 [41] にだけ書かれている。

**デバイスと OpenClaw**

- io を $6.5B で買収（2025-05-21 発表、07-09 完了）。報道では "io" ブランドを捨て、ハードウェアは 2027 年に延期（二次情報）[44]。
- OpenClaw の作者 Peter Steinberger は 2026-02-14 に OpenAI に入社した（日付は Wikipedia [56]。財団の公式記事 [77] は "joined OpenAI earlier this year" とだけ書く）。OpenClaw Foundation（米国の 501(c)(3) 非営利団体）が正式に発表されたのは **2026-07-08** である。OpenAI は "a major donor" で、社内に Steinberger が率いる "Claw Labs" を置いた。議長は Dave Morin で、技術的な意思決定権は Steinberger が持つ。財団は agent identity、agent profiles、evals、enterprise deployment の各 council を招集している [77]。

**Agentic commerce**

- ACP（OpenAI と Stripe）は 2025-09 に Instant Checkout とともに開始。Instant Checkout は**2026-03 に終了**し、決済は商店側へ戻した（二次情報）[45][46]。ACP 仕様そのものは継続している。GitHub `agentic-commerce-protocol/agentic-commerce-protocol` で次の点を確認した [98]。
  - 版は 2025-09-29、2025-12-12、2026-01-16、2026-01-30、**2026-04-17** の 5 つ（2026-04-17 版が出た時点で 2026-01-30 版は deprecated）。
  - 2026-04-17 版の主な変更: 3DS 認証結果の例、エラー例と複数商品の checkout 例、**Feed API**（商店が Agent 側の feed サービスへ商品カタログを push する `POST /feeds` など）。
  - lead maintainer は OpenAI、Stripe、**Meta**。Meta は 2026-04-24 に TSC へ加わった。
  - Apache-2.0。

dots の詳細と企業導入の論点は hermes_openai_dots_enterprise.md を参照。

### 3.3 Apple

- **WWDC 2026（2026-06-08）**: "Siri AI" はまったく新しい Siri で、個人データ検索、画面認識、システム全体のアプリ操作を行う。秋に beta、EU と中国は制限付き。プレスリリースは "bold new architecture" と書くが技術詳細は非開示 [47]。
- 開発者向けには App Intents が唯一の窓口（SiriKit は deprecated。セッション 345 と 240 の App Schemas）[48][49]。
- **Apple と Google の提携（一次情報で確認）**: 2026-01-12 の両社共同声明 [90] で、"the next generation of Apple Foundation Models will be based on Google's Gemini models and cloud technology" と発表された。声明は、これが今年の "more personalized Siri" を含む Apple Intelligence を支えること、Apple Intelligence は引き続き Apple デバイスと Private Cloud Compute 上で動くことも述べている。**金額（「$1B」）は声明に書かれておらず未検証**のままである。WWDC 2026 のプレスリリース [47] は Google、Gemini、サードパーティのチャットボットのいずれにも触れていない。
- **「サードパーティのエージェントを既定の Siri 代替にできる」は一次情報で確認できない**（二次情報 beam.ai [50]、deccanherald のみ）。WWDC26 のセッション一覧で該当しそうなのはセッション 339「Bring an LLM provider to the Foundation Models framework」だが、内容は `LanguageModel` と `LanguageModelExecutor` プロトコルを実装した Swift package で任意の LLM を**アプリ内**から使えるようにするもので、システムの既定アシスタントを置き換える仕組みではない [92]。**未検証のまま**とする。
- **WWDC26 セッション 347「Secure your app: mitigate risks to agentic features」** [91]: Apple は indirect prompt injection（data poisoning と action poisoning）と "lethal trifecta" を脅威モデルとして挙げている。推奨は次のとおり。
  - 決定論的な緩和を基盤にする。Foundation Models の `.onToolCall` によるユーザー確認、App Intents の `authenticationPolicy = .requiresAuthentication` によるロック中の実行禁止など。App Schema の既定の認証ポリシーは、より厳しい方向にしか上書きできない（コンパイラが強制する）。
  - redaction と spotlighting（`<<UNTRUSTED>>` 区切り）は確率的な補助として使う。
  - Apple 自身も "Solving indirect prompt injection is an active research area" と認めている。

  OS ベンダーが「権限は厳しくする方向にしか変えられない」をコンパイラで強制している点は、Progent の単調な権限縮小と同じ考え方である（推論）。

### 3.4 Google

- Project Mariner は**2026-05-04 に終了**し、技術は Gemini Agent、Chrome auto-browse、Gemini API の computer use に吸収された [51]。
- Chrome auto browse（2026-01-28、Gemini 3）が Android の OS レベルにも展開（2026-08-18 に米国全 Android へ）。I/O 2026 で Gemini Enterprise Agent Platform（RBAC、監査ログ）を発表。いずれも二次情報で**一部未検証** [52]。
- A2A の主導、AP2 から UCP までのコマース系プロトコルは §4 を参照。

### 3.5 Meta Muse（2026-09-08）[53]

- "personal AI agent built for everyone"。モデルは Muse Spark 1.3。**Muse Secure VM**（専用 VM とブラウザ）上で動く。
- **Sentinel agent** が同じ VM 上で動作しつつ、システムレベルで隔離されている。監視役を別に置く設計である。Meta の公式発表 [88] には "Nothing Muse does reaches the internet unless the Sentinel approves it" とあり、Sentinel は**外部通信を承認するゲート**として働く（2026-10-02 に一次情報で確認）。
- パスワードと支払い手段にはアクセスできない。決済は Stripe Link。価格は Free、$20、$100。米国のみ。公式製品ページ [89] で確認できた点は次のとおり。
  - 決済時に使い捨てのカード番号が生成され、本物のカード番号は商店にもエージェントにも見えない。Link の購入保護が適用される。
  - 認証情報は "a secure credential store your agent can't read" に保管される（1Password 連携は近日予定）。
  - メール送信や購入は事前に承認でき、全行動の audit trail を確認できる。

  公式発表 [88] は「無料と有料サブスクリプションがある」とだけ書いており、$20 と $100 の金額は TechCrunch [53] による。
- **Confidential VM（一次情報で確認）**: 公式発表（2026-09-08）[88] に "Later this year, Meta will introduce Muse Confidential VM, where the whole VM, including a person's data and conversations with Muse, is encrypted with a key only they hold, so not even Meta can access it" とある。時期は "later this year"（2026 年中）以上には特定されていない。Meta Engineering Blog の 2026-08〜09 の記事に、Muse の Confidential VM を扱ったものはなかった（関連記事としては 2026-09-23 の "Bringing Private Processing to Meta AI Glasses" がある）。Confidential VM の一般論は agent_sandbox_isolation_confidential_computing.md を参照。

### 3.6 OSS の常時稼働エージェント runtime: Hermes Agent / OpenClaw

**Nous Research Hermes Agent** [54][55]

| 項目 | 内容 |
|---|---|
| ライセンス / 学習 | MIT。「経験からスキルを自作して改良する」学習ループ |
| メモリ | MEMORY.md と USER.md の有界メモリ（それぞれ約 800 / 500 tokens）と全会話の全文検索 |
| 実行基盤 | **built-in cron scheduler**、隔離 subagent、7 種の terminal backend（local、Docker、SSH、Singularity、Modal、Daytona、Vercel Sandbox）、Telegram や Slack などへの gateway |
| セキュリティ | コマンド承認、DM pairing、コンテナ隔離 |
| 規模 | GitHub 約 250k stars（取得時点） |

構造は「プロセス、スケジューラ、ファイルシステム、IPC を持つ OS 的な runtime」に近い。

**OpenClaw** [56][57]

- 経緯: 2025-11 に Warelay として公開。2026-01-27 に Moltbot、01-30 に OpenClaw へ改名。2026-08-30 に v2.0（v2026.8.1）。
- 事件: **CVE-2026-25253（RCE）**、ClawHub スキルのサプライチェーン汚染（Cisco がデータ持ち出しスキルを検出）、2026-03 に中国当局が国有企業での利用を制限。
- v2.0 についても「保存済み認証情報が保存時に暗号化されていない」という批判がある。Docker sandbox は既定で無効。
- **arXiv 2603.27517**（Suwansathit, Zhang, Gu、2026-03-29）[28]: 470 件の advisory を分析。Gateway と Node-Host の脆弱性を組み合わせると**認証なしの RCE 経路**が成立する。allowlist は「字句解析でコマンドを特定できる」という閉世界仮定に依存しているため破られる。スキル配布面にランタイムでのポリシー強制がない。根本原因は "per-layer trust enforcement rather than unified policy boundaries"。
- **OpenClaw Enterprise（OCE、2026-09-29、一次情報で確認）** [76]
  - "open source, vendor neutral platform for managing persistent agents" と位置付けている。
  - 経緯: OpenAI で生まれ、OpenClaw Foundation に寄贈された。現在は Red Hat、NVIDIA と共同で開発しており、OpenAI と Red Hat は社内で試験導入している。
  - 安全策: "hard boundaries between trusted and untrusted workloads" に、sandboxing、LLM によるレビュー、細かな権限設定を組み合わせる。これらがどう連携するかを示す reference architecture は「今後公開」とされ、まだ出ていない。
  - 「どの組織も常に無料で使える」と明言している。
- **Trail of Bits による監査（2026-09-21 公表）** [78]: OpenAI の "Patch the Planet" の一環として行われ、権限とユーザーデータの扱いを範囲とした。
  - 結果: advisory 27 件。うち深刻度付きは 24 件で、Critical 0、High 2、Medium 16、Low 6。
  - 対処: 2026.8.1 と 2026.7.33 で修正済み。
  - 繰り返し見つかった欠陥パターンは 4 つある。(1) 後続処理で権限の制限が引き継がれない、(2) 同じ資源の別名によってチェックをすり抜ける、(3) 最終的な操作が承認の対象外になる、(4) 権限を起動時にしか検査しない。いずれも 2603.27517 の「層ごとの信頼判定」批判と同じ方向の指摘である（推論）。

### 3.7 Anthropic（Agent harness と封じ込め）

**Claude Agent SDK** [59]

- Claude Code と同じ agent loop を自社インフラで動かせる。permission mode は default、acceptEdits、plan、dontAsk、bypassPermissions、auto。hook で監査とガードレールをかけられる。

**Claude Managed Agents（public beta、2026-04-08）** [60][62][63]

- 構成は **session（append-only log）、harness（brain）、sandbox（hands）** の 3 つに分かれ、"OS がハードウェアを仮想化したのと同じ" 考え方をとる。
- トークンは sandbox から**構造的に到達できない**。vault と proxy 経由で使う。
- p50 TTFT が約 60% 短縮、p95 は 90% 以上短縮。
- self-hosted sandbox は 2026-05-19、vault の env credential は 2026-06-09 に追加。

**"How we contain Claude"（2026-05-25）** [61]

| 製品 | 封じ込め方式 |
|---|---|
| claude.ai | gVisor |
| Claude Code | Seatbelt/bubblewrap |
| Cowork | VM と MITM egress proxy |

- ユーザーは承認プロンプトの約 93% をそのまま承認していた（approval fatigue）。sandbox 導入でプロンプトは **84% 減った**。
- 原則は 2 つ:「まず環境層で封じ込め、そのうえでモデル層で振る舞いを導く」「独自コンポーネントには警戒する」。

### 3.8 その他のプレイヤー（2026-10-02 に一次情報で追加確認）

| 対象 | 位置付け | セキュリティ / 企業向けの事実 |
|---|---|---|
| Sierra "Agent OS" | **"Agent OS" は Sierra の製品名として実在する**（訂正）。2025-11-05 のブログ "Sierra Agent OS 2.0: from answers to memory and action" で "build your agent once and deploy it everywhere"（chat、voice、email、SMS、ChatGPT、コンタクトセンター）と説明している。トップページ自体は "conversational AI platform" と名乗る [64][79] | トップページに SOC 2、ISO 27001、ISO 42001、HIPAA、GDPR、PCI DSS、FedRAMP、CSA STAR Level One、EU AI Act への対応が並び、"Supervisors"（監視）と guardrails への言及がある（いずれも自己表示で、認証の範囲は Trust Center で要確認）。Agent OS 2.0 の記事自体にはセキュリティの詳細が書かれていない [64][79] |
| Salesforce Agentforce 360 / "Agentic Enterprise" | **Agentforce 360 は実在する**（2025-10-13 発表）。"connects humans, agents, and data on one trusted platform" と説明し、Agentforce 360 Platform、Data 360、Customer 360 Apps、Slack の 4 要素からなる "Agentic Enterprise" を掲げる。Slack を "the system where humans, agents, apps, and data connect" とする [80]。2026-09-15 には AIforce（"our trusted enterprise harness"）を発表し、Claude 連携（Claudeforce）、Slackforce、Agentforce Coworker を出した [81]。**"OS" という語での位置付けは公式文書で確認できない**（使っているのは "platform" と "harness"） | Agentforce 360: 統制されたデータに基づく推論（grounded reasoning）、決定論的ワークフローと LLM 推論を組み合わせる hybrid reasoning、推論と精度とコンプライアンスを見る observability [80]。AIforce: モデル提供者側での Zero Data Retention、Salesforce の既存権限をそのまま強制、全操作を Salesforce 経由に戻す、新しい権限モデルは不要 [81] |
| Lindy | "The AI teammate" / "AI employee for your whole team" と名乗る。Pro 以上ではブラウザを人のように操作する [82] | SOC 2 Type II（Johanson Group が監査）。HIPAA、GDPR、PIPEDA に対応していると主張。保存時と通信時に暗号化。データをモデル学習に使わない。"Every action Lindy takes is logged"。権限を細かく設定できる [82] |
| Relevance AI | "The home of the AI Workforce" と名乗る [83] | SOC 2 Type II と GDPR。データレジデンシー、PII マスキング、学習に使わない、RBAC、SSO/SAML、human-in-the-loop の承認、バージョン管理、agent tracing、OTEL エクスポート、監査ログ。Trust Center は trust.relevanceai.com [83] |
| Writer | "The enterprise AI platform for agentic work" と名乗る [84] | SOC 2 Type II、ISO 27001、27701、42001、HIPAA、GDPR、PCI、CCPA、Data Privacy Framework（自己表示）。knowledge、tool、role ごとの権限制御、observability と guardrails、既存の ID 基盤との統合 [84] |
| Hugging Face smolagents | "a barebones library for agents that think in code"（Apache-2.0、約 29.6k stars、最新 v1.26.0 は 2026-05-29）[86] | 既定の `LocalPythonExecutor` は AST 単位の解釈器で、import を allowlist で制限し、演算回数に上限を設ける。ただし公式文書は "no local python sandbox can ever be completely secure" と明記し、堅牢な隔離には E2B、Docker、Modal、Blaxel のリモート実行を勧めている。code snippet だけを sandbox で動かす方式では API キーを sandbox に渡さずに済むが multi-agent は使えない。エージェント全体を sandbox に入れる方式では秘密情報を中へ渡す必要がある、というトレードオフが文書化されている [85] |
| Humane | AI Pin は 2025-02-28 にサーバ停止。HP が $116M で資産（CosmOS を含む）を買収 [66] | — |
| Rabbit | rabbitOS 2（2025-09-08、r1 向け）の後、**2026-09-22 に "OS3: the agentic operating system for every device"** を発表した。クラウド型で、Windows、Mac、Linux、クラウド VM、r1 で動き、DLAM（Digital LAM）で PC の直接操作と自律的なコーディングを行う [87] | 公式の主張は次のとおり: "The rabbit agent runs locally on your machine and does not copy, store, use, or sell your data"、API キーは BYOK、ユーザーが指示した操作だけを行い、機微な操作には確認を求め、権限はいつでも取り消せる。第三者による検証は見当たらない [87] |

## 4. 相互運用標準（エージェントの "syscall"）

| 標準 | 管理団体 | 2026 年の状態 | 出典 |
|---|---|---|---|
| **MCP** | Linux Foundation の **AAIF**（2025-12-09 設立。MCP、goose、AGENTS.md で発足。Platinum は AWS、Anthropic、Block、Bloomberg、Cloudflare、Google、Microsoft、OpenAI。49 組織で開始。設立時点で MCP サーバは 1 万以上） | **最新は 2026-07-28 版**（RC は 2026-05-21）。<br>・セッションと initialize ハンドシェイクを廃止した **stateless core**<br>・MRTR（Multi Round-Trip Requests）<br>・RFC 9207 の issuer 検証。DCR を deprecated にして CIMD に移行<br>・**extensions framework**（Tasks を `io.modelcontextprotocol/tasks` へ。MCP Apps、Enterprise Managed Authorization）<br>・Roots、Sampling、Logging を deprecated（12 か月の猶予）<br>Tier1 SDK（TS、Python、Go、C#）の合計 DL は月約 5 億。<br>**2026-07-28 版の changelog で追加確認した点**: `Mcp-Session-Id` を廃止し、状態は server が発行する handle を tool 引数で渡す。`server/discover` を必須化。HTTP GET と resources/subscribe を `subscriptions/listen` に置き換え。全 result に `resultType` を必須化。SSE の再開機能を削除。OpenTelemetry の trace context を `_meta` で伝播。`tools/list` などの結果に `ttlMs` と `cacheScope` を必須化。クライアントの資格情報を発行元の認可サーバに紐付け（別の AS での再利用は禁止）。12 か月以上の deprecation 期間を持つ feature lifecycle 方針。MCP Apps と Enterprise Managed Authorization は changelog 本文には名前がなく、出典は blog [68] である [69]<br>**前の版の 2025-11-25（2026-10-02 に確認）**: OpenID Connect Discovery への対応、`WWW-Authenticate` による段階的な scope 同意、URL mode の elicitation、sampling での tool calling、**CIMD（Client ID Metadata Documents）を推奨の登録方式に**、**experimental tasks**（ポーリングと結果の後取り）、tool・resource へのアイコン、JSON Schema 2020-12 を既定に、不正な Origin には 403、SDK の tier 制度、governance の正式化 [75] | [67][68][69][75] |
| **A2A** | Linux Foundation（2025-06-23 に寄贈） | **v1.0 は 2026-03**。JWS と JCS による **signed Agent Cards**。binding は JSON-RPC、gRPC、REST の 3 種。MCP とは補完関係 | [70] |
| **AGENTS.md** | AAIF | 設立時点で 6 万以上の OSS が採用 | [67] |
| **Agent Skills（SKILL.md）** | agentskills.io（Anthropic が 2025-12-18 に公開） | Codex、Gemini CLI、Copilot、Cursor、VS Code など約 40 製品（二次情報） | [71][72] |
| **ACP**（Agentic Commerce Protocol） | OpenAI、Stripe、Meta（lead maintainer。Meta は 2026-04-24 に TSC へ参加）。Apache-2.0 | 仕様は継続しており、最新版は **2026-04-17**（Feed API、3DS の例を追加）で、`unreleased` も開発中。ChatGPT の Instant Checkout は 2026-03 に終了（二次情報） | [45][46][98] |
| **AP2** | **FIDO Alliance**（2026-04-28 に寄贈。Mastercard の Verifiable Intent も同時に） | v0.2 で "Human Not Present" 決済に対応 | [73] |
| **UCP**（Universal Commerce Protocol） | 公式サイトは共同開発者として Google、Shopify、Etsy、Wayfair、Target、Walmart、Amazon、Microsoft、Meta、Salesforce、Stripe を挙げる。GitHub `Universal-Commerce-Protocol/ucp`（Apache-2.0、2025-12-31 作成） | 版は v2026-01-11、v2026-01-23、v2026-04-08、**v2026-08-25（最新）**。transport は REST と JSON-RPC で、A2A と MCP にも結び付ける。アカウント連携は OAuth 2.0。決済は **AP2 の payment mandate と verifiable credentials** を使う（一次情報で確認）。shopping は production-ready、lodging は draft | [74][99][100] |

**OS アナロジー**

| OS の概念 | エージェント標準・仕組み |
|---|---|
| デバイスドライバ兼 syscall | MCP |
| IPC / RPC | A2A |
| 実行可能パッケージと設定ファイル | Agent Skills、AGENTS.md |
| UID と証明書 | Entra Agent ID、signed Agent Card |
| 特権操作（支払い）用 capability token | AP2、ACP |

## 5. OS レベルの論点と実装

| 論点 | 研究側 | 産業側の実装 |
|---|---|---|
| **プロセス隔離** | IsolateGPT（hub-and-spoke）、AOS、2605.14932 | Windows Agent Workspace と MXC（process / session、VM は予定）、dots と Muse の専用 VM、Managed Agents の sandbox、Claude の gVisor/VM、Hermes の Docker/Modal 等の backend。OpenClaw は既定で隔離なし |
| **capability / 権限** | CaMeL（capability）、Progent（SMT による単調な権限縮小）、SEAgent（MAC）、FIDES・f-secure（IFC） | dots Custom Rules、Windows の limited privileges と ACL、Claude permission modes。**決定論的な IFC を製品に入れている例はまだない**（FIDES は OSS の研究実装にとどまる） |
| **スケジューリング / 予算** | AIOS scheduler（2.1 倍）、AOS | Hermes の cron、dots の常時稼働と並行プロジェクト、W365 for Agents の pool（米国 on-demand で $0.40/VM/時間の従量課金 [94]）。**トークンや費用の予算をカーネル機能として強制する標準はない** |
| **メモリ / FS 意味論** | MemGPT、MemOS（MemCube、provenance）、LSFS | Hermes の MEMORY.md と全文検索、Letta、Cowork の read-only / rw-no-delete マウント |
| **エージェント間 IPC** | IsolateGPT の hub 仲介 | A2A v1.0（signed card）、MCP（stateless、Tasks）、dots の teams（予定） |
| **監査** | AOS の audit 要素、2609.23700 | Managed Agents の append-only session log、Entra のサインイン/監査ログ、Windows の agent account による帰属、Purview |
| **ID** | — | Windows agent account、Entra Agent ID（blueprint）、specialist dots の独自 ID、A2A signed card、AP2 と FIDO |
| **秘密情報** | CaMeL（流出防止） | Anthropic の vault と proxy（sandbox から到達不能）、dots のパスワード非開示、Muse のパスワード非アクセス。**OpenClaw は保存時暗号化なし** |
| **サプライチェーン** | 2603.27517 | Windows のエージェント署名必須。OpenClaw の ClawHub では汚染が起きた |

複数エージェントの統制面（registry、ownerless agent 検出、ポリシー配布）は enterprise_agent_control_plane.md、業務オブジェクトに対する行為の型付けは ontology_palantir_kinetic_layer.md と接続する（推論）。

## 6. 成熟度評価

| 成熟度 | 項目 |
|---|---|
| **成熟（今すぐ採用）** | ・エージェント専用 ID と非人間アカウント（Entra Agent ID、OS アカウント分離）<br>・VM / gVisor / container による実行隔離<br>・egress proxy<br>・認証情報を sandbox の外に置く（vault）<br>・append-only の監査ログ<br>・MCP（2026-07-28 版）と A2A v1.0 の採用<br>・AGENTS.md と Skills による手順の外部化<br>Anthropic と Microsoft の一次情報は、どちらも「既存の OS 境界のほうが独自の仕組みより信頼できる」と述べている |
| **発展途上（選んで採用）** | ・決定論的 IFC / capability（CaMeL、FIDES、Progent）。安全性は証明できるが有用性が下がる（CaMeL は 77% 対 84%）。FIDES には label forging の報告がある<br>・メモリ OS（MemOS など）。自己申告のベンチマーク値が中心<br>・cron と常時稼働の runtime（Hermes、dots） |
| **hype / 研究段階** | ・LLM そのものを kernel にする "AI-native OS"（AgentOS 2603.08938 は評価なしの構想）<br>・AIOS 型の「LLM syscall カーネル」。本番採用の形跡がなく、開発も停滞気味<br>・"Agent OS" というマーケティング用語全般<br>・コマース自動決済（Instant Checkout の終了、Mariner の終了） |
| **危険（無統制では不可）** | ・自己改善スキルの自動配布と自動インストール（OpenClaw の事例）<br>・lexical な allowlist による command filter（2603.27517）<br>・人の承認だけに頼る防御（承認率 93% で形骸化） |

## 7. AI-only company 推奨アーキテクチャ

対象は機密データ・常時稼働・自己改善を前提とする AI-only company である。層ごとの推奨と既存調査との接続を示す。接続列は（提案）である。

| 層 | 推奨（原資料 5.2） | 既存調査との接続（提案） |
|---|---|---|
| 1. ID 層 | エージェント 1 体ごとに独立した非人間 ID（Entra Agent ID 型 blueprint と A2A signed card）。人間の sponsor と有効期限を必須に | ID を OpenFGA の subject として扱い、PDP 一箇所で判定する |
| 2. 実行層 | タスク単位で使い捨ての VM / gVisor sandbox。エージェントループ（brain）は sandbox の外（Managed Agents 型）。ネットワークは deny-by-default で egress proxy 経由 | brain 側の制御フローは Temporal Workflow で固定する既存方針と組み合わせる |
| 3. 秘密情報 | vault と proxy で注入し、モデルにも sandbox にも平文を見せない | Gateway のシンク検査と同じ境界に置く |
| 4. 権限 | Progent/CaMeL の考え方で「自動では狭まる方向のみ、拡大は承認」。confidential と untrusted にラベルを付けて IFC | 既存調査の FIDES/CaMeL 型ラベル伝播、Cedar の業務ルール |
| 5. 自己改善の統制 | エージェントが作ったスキルや設定（Hermes のスキル自作など）は PR と同じ扱い。別のレビュー用エージェントと静的検査を通し、署名してから昇格。外部マーケットのスキルは原則禁止（Windows の署名要件にならう） | メモリ調査の「人のフィードバック→候補ルール→PR レビュー→評価回帰→段階適用」と同一の経路に載せる |
| 6. 監視 | Muse の Sentinel のように別の隔離された監視エージェントと append-only ログ。kill switch と、予算（トークン、費用、レート）上限の外部強制 | 監視エージェントの検出結果は境界にせず、停止トリガーとしてのみ使う（既存調査の「検出器は境界にしない」） |
| 7. 標準 | MCP 2026-07-28（stateless で水平スケールしやすい）、A2A v1.0、AGENTS.md と Skills を採用。決済は AP2 と FIDO の動向待ちで、当面は人の承認必須 | MCP サーバは Gateway の背後に置き、シンク検査の対象にする |
| 8. 前提 | 2609.23700 が示すとおり、意味内容の検査には原理的に取りこぼしが残る。被害の上限は capability の制限で決め、プロンプト検知には頼らない | 既存の「外部送信シンクを構造的に持たない」方針と同じ結論 |

## 8. 未検証事項

| 項目 | 状態 |
|---|---|
| KernelAGI | arXiv API と GitHub 検索で 0 件。存在しないと判断（2026-10-02） |
| Sierra "Agent OS"、Salesforce の OS としての位置付け | Sierra は製品名として確認。Salesforce は Agentforce 360 と "Agentic Enterprise" を確認したが、"OS" という語での位置付けは確認できない |
| Lindy、Relevance、Writer、HF、Rabbit | 2026-10-02 に公式ページで調べ、§3.8 に追加。各社の認証は自己表示で、監査報告書までは見ていない |
| Apple「サードパーティのエージェントを Siri の既定にできる」 | **未検証のまま**。Apple Newsroom の WWDC26 発表と WWDC26 セッション一覧（339 など）に該当する記述はない |
| Apple「Gemini との $1B 契約」 | 提携は 2026-01-12 の共同声明で確認。**金額は未検証のまま**（声明に書かれていない） |
| Meta Confidential VM | 確認済み（公式発表 2026-09-08、"Later this year"） |
| OpenClaw Enterprise | 確認済み（openclaw.ai 2026-09-29） |
| W365 for Agents の $0.40/h、Agent Governance Toolkit、MAF v1.0 | 確認済み（W365 の公式ページ、GitHub） |
| ODR の build 番号と日付 | build と日付は確認したが、ODR/MCP との対応付けは一次情報になく訂正 |
| ACP の 2026-04-17 版、UCP の詳細 | 確認済み（GitHub、ucp.dev） |
| MemOS のベンチマーク値 | **未検証のまま**（arXiv API で検索した 4 本の要旨に再現の記述なし。本文の表までは見ていない） |
| MCP 2025-11-25 版の内容 | 確認済み（公式 changelog） |
| AgenticOS（ResearchGate） | arXiv ID 確認できず未検証（今回は再調査せず） |
| Google Chrome auto browse の Android 展開、Gemini Enterprise Agent Platform | 二次情報で一部未検証（今回は再調査せず） |
| OpenAI 公式記事（introducing-dots、devday-2026-recap） | r.jina.ai 経由で取得して確認。Agents API の "public beta" 区分だけは recap 本文で確認できない |
| Instant Checkout の 2026-03 終了 | 二次情報のまま（今回は再調査せず） |
| OpenClaw v2.0 の「保存時に暗号化されない」批判、Docker sandbox が既定で無効 | 二次情報のまま。openclaw.ai のブログ一覧に該当する記事はなかった |

## 追補: 再検証ログ（2026-10-02）

WebSearch は使わず、WebFetch（必要に応じて r.jina.ai）、arXiv API、GitHub API（gh）だけで確認した。

**検証済みにした項目**

- Meta Muse Confidential VM: "Later this year" で、鍵はユーザーだけが持つ。Sentinel は外部通信の承認ゲート [88][89]。
- OpenClaw Enterprise（2026-09-29）と OpenClaw Foundation（2026-07-08、501(c)(3)）[76][77]。
- W365 for Agents は米国で $0.40/VM/時間 [94]。
- Agent Governance Toolkit の GitHub リポジトリ [95]。
- MAF の 1.0.0（2026-04-02）[96][97]。
- MCP 2025-11-25 版の内容と、2026-07-28 版の changelog の詳細 [69][75]。
- ACP の 2026-04-17 版 [98]。
- UCP の版と AP2 との関係 [99][100]。
- OpenAI の introducing-dots と DevDay recap の主要項目 [43][101][102]。
- Apple と Google の Gemini 提携（2026-01-12 の共同声明）[90]。

**訂正した項目**

- Sierra: "Agent OS" の表記は確認できないとしていたが、Sierra Agent OS 2.0（2025-11-05）として実在した [79]。
- Salesforce: Agentforce 360 は 2025-10-13 に発表されていた。ただし "OS" という語での位置付けは確認できない [80][81]。
- Windows 26200.8313（2026-04-17 Release Preview）: ビルドと日付は正しいが、リリースノートに ODR/MCP の記述はない。記載されているのは taskbar からのエージェント監視機能である [93]。
- OpenClaw の財団移行: 「Steinberger の入社時に財団へ移った」としていたが、財団が正式に発足したのは 2026-07-08 [77]。
- MAF 1.0 は Build 2026 の発表ではなく、2026-04-02 にリリースされていた [97]。

**新規追加**

- §3.8: Lindy、Relevance AI、Writer、HF smolagents、Rabbit OS3（2026-09-22）のセキュリティと企業向けの事実 [82]〜[87]。
- WWDC26 セッション 347 の agentic 機能向け防御指針 [91] と、セッション 339 がアプリ内での LLM 差し替えであること [92]。
- OpenClaw の Trail of Bits 監査（High 2、Medium 16）[78]。
- ACP の maintainer に Meta が加わったこと [98]。

**未検証のまま残った項目**

- Apple:「サードパーティのエージェントを Siri の既定にできる」と「$1B」の金額。
- MemOS の自己申告ベンチマーク値。arXiv API で 4 本を確認したが、要旨に再現の記述はなかった。
- Agents API の "public beta" 区分。
- Instant Checkout の終了時期。
- OpenClaw v2.0 で認証情報が保存時に暗号化されない点。
- AgenticOS（ResearchGate）。
- Google の Android 展開と Gemini Enterprise Agent Platform。
- Rabbit と各 SaaS のセキュリティ主張は、どれも自己表示である。

## 参考文献

研究

- [1] Andrej Karpathy, "LLM OS"（X 投稿）, 2023-11-11. https://x.com/karpathy/status/1723140519554105733
- [2] Packer et al., MemGPT: Towards LLMs as Operating Systems, arXiv 2310.08560, 2023-10-12（v2 2024-02-12）. https://arxiv.org/abs/2310.08560
- [3] Letta, 公式サイト. https://www.letta.com/
- [4] OS-Copilot / FRIDAY, arXiv 2402.07456, 2024-02. https://arxiv.org/abs/2402.07456 / https://os-copilot.github.io/
- [5] AIOS: LLM Agent Operating System, arXiv 2403.16971, 2024-03-25（v5 2025-08-12）, COLM 2025. https://arxiv.org/abs/2403.16971
- [6] Cerebrum (AIOS SDK), arXiv 2503.11444, 2025-03-14, NAACL 2025 System Demo. https://arxiv.org/abs/2503.11444
- [7] From Commands to Prompts: LLM-based Semantic File System, arXiv 2410.11843. https://arxiv.org/html/2410.11843v1
- [8] LSFS, ICLR 2025 Proceedings. https://proceedings.iclr.cc/paper_files/paper/2025/hash/517eb19e99947f60afff0cf93e451825-Abstract-Conference.html
- [9] agiresearch/AIOS, GitHub. https://github.com/agiresearch/AIOS
- [10] MemOS: A Memory OS for AI System, arXiv 2507.03724, 2025-07-04（改訂 2025-12-03）. https://arxiv.org/abs/2507.03724
- [11] MemOS: An Operating System for Memory-Augmented Generation (MAG), arXiv 2505.22101. https://arxiv.org/abs/2505.22101
- [12] MemTensor/MemOS, GitHub（最新更新 2026-08-17）. https://github.com/MemTensor/MemOS
- [13] Liu, Pei et al., AgentOS: From Application Silos to a Natural Language-Driven Data Ecosystem, arXiv 2603.08938, 2026-03-09. https://arxiv.org/abs/2603.08938
- [14] Sharma, Shah, Agent Operating Systems (AOS), arXiv 2606.01508, 2026-06-01. https://arxiv.org/abs/2606.01508
- [15] Steinder, Franke, Towards an Agent Operating System – Lessons from Classical and Cloud OS, arXiv 2607.25076, 2026-07-27. https://arxiv.org/abs/2607.25076
- [16] Pirch, Holz, Rieck et al., Toward Securing AI Agents Like Operating Systems, arXiv 2605.14932, 2026-05-14. https://arxiv.org/abs/2605.14932
- [17] Zhang, Sun, Shi, When the Agent Becomes the Kernel: SoK on AI-Native OS Security, arXiv 2609.23700, 2026-09-20. https://arxiv.org/abs/2609.23700
- [18] AgenticOS: An Intent-Oriented Secure Operating System Architecture for Autonomous AI Agents, ResearchGate（二次情報、未検証）. https://www.researchgate.net/publication/407507476_AgenticOS_An_Intent-Oriented_Secure_Operating_System_Architecture_for_Autonomous_AI_Agents
- [19] Wu, Roesner, Kohno, Iqbal et al., IsolateGPT (SecGPT), arXiv 2403.04960, NDSS 2025. https://arxiv.org/abs/2403.04960
- [20] Wu, Cecchetti, Xiao, f-secure LLM system, arXiv 2409.19091. https://arxiv.org/abs/2409.19091
- [21] Google DeepMind et al., CaMeL, arXiv 2503.18813. https://arxiv.org/pdf/2503.18813
- [22] Costa, Köpf et al.（Microsoft）, FIDES, arXiv 2505.23643, 2025-05-29. https://arxiv.org/abs/2505.23643
- [23] microsoft/fides, GitHub. https://github.com/microsoft/fides
- [24] APIsec Labs, Trust me bro: forging security labels in FIDES. https://labs.apisec.ai/research/articles/trust-me-bro-forging-security-labels-fides/
- [25] Dawn Song et al., Progent, arXiv 2504.11703. https://arxiv.org/abs/2504.11703
- [26] SEAgent, arXiv 2601.11893, 2026-01-17. https://arxiv.org/abs/2601.11893
- [27] Christodorescu, Fernandes, Jha, Rehberger et al., Systems Security Foundations for Agentic Computing, arXiv 2512.01295, 2025-12-02. https://www.arxiv.org/pdf/2512.01295
- [28] Suwansathit, Zhang, Gu, OpenClaw 脆弱性分析, arXiv 2603.27517, 2026-03-29. https://arxiv.org/abs/2603.27517

産業

- [29] Microsoft Learn, Operating system agentic security. https://learn.microsoft.com/en-us/windows/security/book/operating-system-agentic-security
- [30] Microsoft Support, Experimental agentic features. https://support.microsoft.com/en-us/windows/experimental-agentic-features-a25ede8a-e4c2-4841-85a8-44839191dfb3
- [31] Windows Experience Blog, Securing AI agents on Windows, 2025-10-16. https://blogs.windows.com/windowsexperience/2025/10/16/securing-ai-agents-on-windows/
- [32] Windows Developer Blog, Ignite 2025: furthering Windows as the premier platform for developers, 2025-11-18. https://blogs.windows.com/windowsdeveloper/2025/11/18/ignite-2025-furthering-windows-as-the-premier-platform-for-developers-governed-by-security/
- [33] Windows Developer Blog, Build 2026: furthering Windows as the trusted platform for development, 2026-06-02. https://blogs.windows.com/windowsdeveloper/2026/06/02/build-2026-furthering-windows-as-the-trusted-platform-for-development/
- [34] zylos, Windows AI agent platform Build 2026, 2026-06-24（二次情報）. https://zylos.ai/research/2026-06-24-windows-ai-agent-platform-build-2026/
- [35] beri.net, Windows 11 taskbar agentic MCP enterprise 2026（二次情報）. https://www.beri.net/article/windows-11-taskbar-agentic-mcp-enterprise-2026
- [36] Microsoft Learn, What is Microsoft Entra Agent ID. https://learn.microsoft.com/en-us/entra/agent-id/what-is-microsoft-entra-agent-id
- [37] Microsoft, Microsoft Agent 365. https://www.microsoft.com/en-us/microsoft-agent-365
- [38] The Next Web, OpenAI dots: always-on AI agents with cloud computers（二次情報）. https://thenextweb.com/news/openai-dots-always-on-ai-agents-cloud-computers-devday
- [39] 9to5Google, OpenAI dots agent, 2026-09-29（二次情報）. https://9to5google.com/2026/09/29/openai-dots-agent/
- [40] BetaNews, OpenAI dots agents ChatGPT（二次情報）. https://betanews.com/article/openai-dots-agents-chatgpt/
- [41] OpenAI Developer Community, DevDay 2026 announcements and developer resources. https://community.openai.com/t/devday-2026-announcements-and-developer-resources/1402006
- [42] The Neuron Daily, OpenAI launched dots + 20 more tools（二次情報）. https://www.theneurondaily.com/p/openai-launched-dots-20-more-tools
- [43] OpenAI, Introducing dots（直接取得は 403。2026-10-02 に r.jina.ai 経由で取得）. https://openai.com/index/introducing-dots/
- [44] Wikipedia, Io (company)（二次情報）. https://en.wikipedia.org/wiki/Io_(company)
- [45] Stellagent, OpenAI shopping agent strategy pivot（二次情報）. https://stellagent.ai/insights/openai-shopping-agent-strategy-pivot
- [46] Exploding Topics, Agentic Commerce Protocol（二次情報）. https://explodingtopics.com/blog/agentic-commerce-protocol
- [47] Apple Newsroom, Apple unveils next generation of Apple Intelligence, Siri AI and more, 2026-06. https://www.apple.com/newsroom/2026/06/apple-unveils-next-generation-of-apple-intelligence-siri-ai-and-more/
- [48] Apple Developer, WWDC 2026 Session 345. https://developer.apple.com/videos/play/wwdc2026/345/
- [49] Apple Developer, WWDC 2026 Session 240. https://developer.apple.com/videos/play/wwdc2026/240/
- [50] beam.ai, Apple WWDC 2026 iOS 27 agent extensions enterprise（二次情報）. https://beam.ai/agentic-insights/apple-wwdc-2026-ios-27-agent-extensions-enterprise
- [51] Android Headlines, Google shuts down Project Mariner AI agent, 2026-05. https://www.androidheadlines.com/2026/05/google-shuts-down-project-mariner-ai-agent.html
- [52] technology.org, Google's new Chrome AI agent browses the web for you, 2026-01-29（二次情報）. https://www.technology.org/2026/01/29/googles-new-chrome-ai-agent-browses-the-web-for-you-while-you-sit-back/
- [53] TechCrunch, Meta debuts its Muse AI agent, 2026-09-08. https://techcrunch.com/2026/09/08/meta-debuts-its-muse-ai-agent-will-consumers-trust-it/
- [54] nousresearch/hermes-agent, GitHub. https://github.com/nousresearch/hermes-agent
- [55] Jimmy Song, Hermes Agent（二次情報）. https://jimmysong.io/ai/hermes-agent/
- [56] Wikipedia, OpenClaw（二次情報）. https://en.wikipedia.org/wiki/OpenClaw
- [57] Conscia, The OpenClaw security crisis（二次情報）. https://conscia.com/blog/the-openclaw-security-crisis/
- [58] Complete AI Training, OpenClaw Foundation launches OpenClaw Enterprise（二次情報。一次情報 [76] で内容を確認済み）. https://completeaitraining.com/news/openclaw-foundation-launches-openclaw-enterprise-for/
- [59] Anthropic, Claude Agent SDK overview. https://code.claude.com/docs/en/agent-sdk/overview
- [60] Anthropic Engineering, Managed Agents. https://www.anthropic.com/engineering/managed-agents
- [61] Anthropic Engineering, How we contain Claude, 2026-05-25. https://www.anthropic.com/engineering/how-we-contain-claude
- [62] Claude Platform Docs, Managed Agents: self-hosted sandboxes. https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes
- [63] Claude Platform Docs, Managed Agents: vaults. https://platform.claude.com/docs/en/managed-agents/vaults
- [64] Sierra, 公式サイト. https://sierra.ai/
- [65] Salesforce, Agentforce. https://www.salesforce.com/agentforce/
- [66] Wikipedia, Humane Inc.（二次情報）. https://en.wikipedia.org/wiki/Humane_Inc.

標準

- [67] Linux Foundation, Linux Foundation announces the formation of the Agentic AI Foundation, 2025-12-09. https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation
- [68] MCP Blog, 2026-07-28 specification release, 2026-07-28. https://blog.modelcontextprotocol.io/posts/2026-07-28/
- [69] Model Context Protocol, Specification 2026-07-28 changelog. https://modelcontextprotocol.io/specification/2026-07-28/changelog
- [70] Google Open Source Blog, A year of open collaboration: celebrating the anniversary of A2A, 2026-04. https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html
- [71] agentskills.io, Agent Skills. https://agentskills.io/home
- [72] The Decoder, Anthropic publishes Agent Skills as an open standard for AI platforms（二次情報）. https://the-decoder.com/anthropic-publishes-agent-skills-as-an-open-standard-for-ai-platforms/
- [73] FIDO Alliance, Google donates Agent Payments Protocol to FIDO Alliance, 2026-04-28. https://fidoalliance.org/google-donates-agent-payments-protocol-to-fido-alliance/
- [74] dev.to (ucptools), UCP vs ACP in 2026: a technical comparison of AI commerce protocols（二次情報）. https://dev.to/ucptools/ucp-vs-acp-in-2026-a-technical-comparison-of-ai-commerce-protocols-50j7
- [75] Model Context Protocol, Specification 2025-11-25 changelog. https://modelcontextprotocol.io/specification/2025-11-25/changelog

追補（2026-10-02 再検証で追加）

- [76] OpenClaw, OpenClaw Enterprise - The Open Agent Platform, 2026-09-29. https://openclaw.ai/blog/openclaw-enterprise
- [77] OpenClaw, Introducing the OpenClaw Foundation, 2026-07-08. https://openclaw.ai/blog/introducing-openclaw-foundation
- [78] OpenClaw, OpenClaw Completes Security Audit Through OpenAI's Patch the Planet Initiative, 2026-09-21. https://openclaw.ai/blog/openclaw-trail-of-bits-engagement-recap
- [79] Sierra, Sierra Agent OS 2.0: from answers to memory and action, 2025-11-05. https://sierra.ai/blog/agent-os-2-0
- [80] Salesforce, Agentforce 360 / Agentic Enterprise announcement, 2025-10-13. https://www.salesforce.com/news/press-releases/2025/10/13/agentic-enterprise-announcement/
- [81] Salesforce, AIforce announcement, 2026-09-15. https://www.salesforce.com/news/stories/aiforce-announcement/
- [82] Lindy, Security（およびトップページ https://www.lindy.ai/）. https://www.lindy.ai/security
- [83] Relevance AI, 公式サイト. https://relevanceai.com/
- [84] WRITER, 公式サイト. https://writer.com/
- [85] Hugging Face, smolagents: Secure code execution. https://huggingface.co/docs/smolagents/tutorials/secure_code_execution
- [86] huggingface/smolagents, GitHub（v1.26.0 2026-05-29、2026-10-02 時点で約 29.6k stars）. https://github.com/huggingface/smolagents
- [87] rabbit, rabbit unveils OS3: the agentic operating system for every device, 2026-09-22. https://www.rabbit.tech/newsroom/rabbitos-3-launch
- [88] Meta, Introducing Muse, 2026-09-08. https://about.fb.com/news/2026/09/introducing-muse/
- [89] Meta AI, Muse 製品ページ（r.jina.ai 経由で取得）. https://ai.meta.com/muse/
- [90] Google, Joint statement from Google and Apple, 2026-01-12. https://blog.google/company-news/inside-google/company-announcements/joint-statement-google-apple/
- [91] Apple Developer, WWDC26 Session 347: Secure your app: mitigate risks to agentic features. https://developer.apple.com/videos/play/wwdc2026/347/
- [92] Apple Developer, WWDC26 Session 339: Bring an LLM provider to the Foundation Models framework. https://developer.apple.com/videos/play/wwdc2026/339/
- [93] Windows Insider Blog, Releasing Windows 11 Builds 26100.8313 and 26200.8313 to the Release Preview Channel, 2026-04-17. https://blogs.windows.com/windows-insider/2026/04/17/releasing-windows-11-builds-26100-8313-and-26200-8313-to-the-release-preview-channel/
- [94] Microsoft, Windows 365 for Agents（価格）. https://www.microsoft.com/en-us/windows-365/agents
- [95] microsoft/agent-governance-toolkit, GitHub（2026-03-02 作成、v4.1.0 2026-06-09）. https://github.com/microsoft/agent-governance-toolkit
- [96] Microsoft Learn, Microsoft Agent Framework Overview（ms.date 2026-07-29）. https://learn.microsoft.com/en-us/agent-framework/overview/
- [97] microsoft/agent-framework, GitHub Releases（python-1.0.0 / dotnet-1.0.0, 2026-04-02）. https://github.com/microsoft/agent-framework/releases
- [98] agentic-commerce-protocol/agentic-commerce-protocol, GitHub（changelog/2026-04-17.md、MAINTAINERS.md）. https://github.com/agentic-commerce-protocol/agentic-commerce-protocol
- [99] Universal Commerce Protocol, 公式サイト. https://ucp.dev/
- [100] Universal-Commerce-Protocol/ucp, GitHub Releases（v2026-08-25 ほか）. https://github.com/Universal-Commerce-Protocol/ucp
- [101] OpenAI, Introducing dots（r.jina.ai 経由で取得、2026-10-02）. https://r.jina.ai/https://openai.com/index/introducing-dots/
- [102] OpenAI, DevDay 2026 recap（r.jina.ai 経由で取得、公開時刻メタデータ 2026-10-02）. https://openai.com/index/devday-2026-recap/
- [103] arXiv API 検索結果（2026-10-02）: 2601.21545 ShardMemo、2604.07877 MemReader、2607.22562 SF-AMS、2609.07471 MEMO. https://export.arxiv.org/api/query?search_query=abs:MemOS+AND+abs:LoCoMo
