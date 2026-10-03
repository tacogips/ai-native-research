---
title: "オントロジーを AI エージェントに適用する: Palantir Ontology/AIP、セマンティックレイヤー、論文と標準"
author: claude
kind: survey
subject: オントロジー、Palantir Ontology、AIP、Action type、セマンティックレイヤー、ナレッジグラフ、SHACL、kinetic layer
status: idea
maturity: validated
created: 2026-10-02
updated: 2026-10-02
verified: 2026-10-02
tags: [技術, オントロジー, Palantir, AIP, セマンティックレイヤー, ナレッジグラフ, SHACL, 認可, 情報フロー制御, エージェント]
relates_to:
  - research/technology/hermes_openai_dots_enterprise.md
  - research/technology/enterprise_agent_control_plane.md
  - research/technology/ai_os_agent_os.md
  - research/technology/autonomous_agent_risks_papers_incidents.md
summary: Palantir Ontology は名詞（object/link）に加えて動詞（Action type）まで型付けし、LLM には Action・Object Query・Function などのツールしか渡さない点で、読み取り専用が中心の他社セマンティックレイヤーと異なる。AI-only company では、オントロジーを「エージェントが世界を変更できる唯一の窓口（kinetic layer）」とし、Action を Cedar/OpenFGA の認可・IFC ラベル・監査へ 1 対 1 で写像し、commit 前に SHACL/Cedar で検証する構成を推奨する。スキーマ進化は「エージェント提案→ブランチ評価→人レビュー→merge」に限定する。
---

# オントロジーを AI エージェントに適用する: Palantir Ontology/AIP、セマンティックレイヤー、論文と標準

本稿は、Palantir Ontology/AIP を中心に、エージェント向けのオントロジー／セマンティックレイヤー製品、関連論文（2023〜2026）、標準（RDF 1.2、SHACL 1.2 ほか）を 2026-10-02 時点で調査したものである。主題は「オントロジーを、LLM エージェントが業務データを読み書きするための型付きインタフェースとして使えるか」である。

既存調査（ai-native-company リポジトリ research/technology/ 配下）との関係は次のとおりである。認可調査（authorization_zanzibar_openfga_cedar.md）は「誰が何をしてよいか」を OpenFGA（ReBAC）と Cedar の二層で判定し、判定をランタイムの PDP 一箇所に集約するとした。情報フロー制御調査（information_flow_control_and_exfiltration.md）は、ラベル伝播とシンク検査を Gateway で行うとした。メモリ調査（Zep/Graphiti を扱ったもの）は「メモリを正本にしない」とした。本稿で加わるのは、これらが判定・検査する対象である「業務世界のモデル（名詞と動詞）」そのものをどう型付けするか、という層である。認可・IFC・メモリの各推奨は再説明せず、オントロジー層との写像と差分だけを書く。

## 1. 要約(推奨)

1. **エージェントの書き込み経路を型付き Action に限定する（kinetic layer）。** Palantir Ontology が他社と違うのは、Action type（入力パラメータ、submission criteria、side effect、action log、revert）という書き込み経路まで型付けしている点である。LLM エージェントには「オブジェクト検索」「Action 適用」「Function 呼び出し」などのツールだけを渡し、生データには触れさせない [1][8]。Palantir 自身も「Actions-only」モデルを推奨し、writeback dataset への直接 Edit 権限を非推奨としている [7]。AI-only company でも、生 SQL の書き込みや任意の REST 呼び出しはエージェントに渡さない（提案）。
2. **Action を型付きツールスキーマ兼 MCP ツールとし、自動実行か確認必須かを Action ごとに決める。** Ontology MCP は Action 定義を MCP ツールとして公開し、application restrictions で実行範囲を絞る [27]。Chatbot Studio の Action ツールは「自動実行」と「ユーザー確認後に実行」を選べる [1]。これと同様に、Action registry からツールを自動生成し、リスク層（金額、外部影響、不可逆性）に応じて自動適用かステージングかを決める（提案）。
3. **Ontology の要素を既存の認可・IFC・監査へ 1 対 1 で写像する。** Action type は Cedar の action、Link type は OpenFGA の relation tuple、markings は IFC のラベル、action log と Checkpoints（理由記録）は監査に対応させる（6.1 節）。既存の認可調査が定めた「PDP 一箇所への集約」とは、Action 実行時の判定点をその PDP に置くことで整合する（推論）。
4. **commit 前に検証し、違反はエージェントに返して修復させる。** Validate API（dry-run 相当）[9] や submission criteria [6] と同じく、「変更後のグラフ」を SHACL や Cedar で事前検証する。OBQC＋Repair で精度 72% [94]、G-SPEC で安全違反 0 [115]、GROUND で RLS とフィルタの違反 0 [96] という実証がある。ただし、NL から SHACL を自動生成すると意味的な誤りが残るため [117]、制約の作成と変更は人のレビュー対象とする。
5. **セマンティクスを明示して LLM の精度を上げる。** enterprise text-to-SQL の精度は、SQL 直接で 16%、KG 経由で 54% [93]、ontology によるクエリ検査と修復で 72% [94] となった。セマンティック文書の追加で +17〜23pt の改善があり、モデル間の差は有意でない [95]。メトリクス定義だけではデータが漏れるため、RLS 等の強制保証を同じ層に置く [96]。
6. **オントロジーの進化は「提案→ブランチ評価→人レビュー→merge」に限定し、自己権限に関わるメタデータは変更禁止とする。** Palantir AI FDE（Global Branch の proposal）[16]、Automate × Global Branching [18]、Fabric IQ の proposal-first な ontology agent [59] はいずれもこの形である。エージェントが Cedar ポリシー、marking 付与、Checkpoint 設定を変更できないようにする（提案）。
7. **Palantir を採るか OSS で自作するかは、ロックインとコストで判断する。** 競合の多く（Snowflake、Databricks、dbt/MetricFlow、Cube、AtScale、Apache Ossie）は読み取り専用のセマンティックレイヤーで、統制された書き込み層を持たない。Fabric IQ は rules と proposal-first の agent を持つが preview であり、Palantir 級の Action はない [59]。自作する場合の最小構成は Postgres＋Action registry＋Cedar/SHACL＋OpenFGA＋Ossie/MetricFlow＋Graphiti＋MCP である（6.6 節、提案）。

## 2. Palantir 詳細

### 2.1 Ontology の構成要素

| 要素 | 定義・事実 | 出典 |
|---|---|---|
| Ontology | 「組織の digital twin」。dataset と model を一つの整合した全体に統合する | [2] |
| Object type / Property | 実世界の実体・イベントのスキーマと、その特性のスキーマ | [2] |
| Link type | 2 つの object type 間の関係のスキーマ | [2] |
| Action type | 「ユーザーが一度に行う、オブジェクト・プロパティ値・リンクへの変更の集合」の定義 | [2] |
| Functions | Ontology とネイティブに統合されたコードロジック | [2] |
| Interfaces | 共通の形を持つ object type のポリモーフィズム。interface に対する Action も定義できる | [2][3] |
| 設計思想 | Ontology はデータではなく「意思決定」を表す。Data / Logic / Action / Security の 4 要素で構成し、Action を「the verbs」と呼ぶ。エージェントは「徐々に信頼されるチームメンバー」として、事前に決めた境界の内側で動く | [4] |
| Object Storage v2 | object type 1 つあたり数百億オブジェクト、最大 2,000 プロパティ。1 Action で最大 10,000 オブジェクトを編集できる。streaming、incremental indexing、スキーマ変更時の編集マイグレーションに対応。OSv1 は 2026-06-30 以降使用不可 | [5] |

### 2.2 Action type（エージェントが書き込める唯一の経路）

| 機能 | 内容 | 出典 |
|---|---|---|
| Submission criteria（旧称 validations） | 条件（「現在のユーザーに基づく」または「パラメータに基づく」）を演算子で組み合わせる。全条件を満たした場合のみ提出できる。失敗メッセージは利用者に表示される | [6] |
| 権限 | 提出者は、編集対象の object/link type とそのデータソースを閲覧でき、かつ submission criteria を満たす必要がある。推奨は「Actions-only」モデルで、Read だけで編集できる。writeback dataset に Edit 権限を与えると「必要以上のデータが露出する」と明記されている | [7] |
| Rules / side effects | オブジェクトとリンクの作成・変更・削除、function-backed action、webhook、通知 | [8] |
| 監査・取り消し | action log、revert、batch 実行。結果は writeback dataset に反映される | [8] |
| Validate API | 実行前に検証だけを行う API（dry-run 相当） | [9] |
| Branching | Action type もブランチ上で変更できる | [10] |

### 2.3 AIP 製品群（2026 年の状態）

2026 年に入って、AIP 周りの名称と製品構成は大きく変わった。主な変化は、Agent Studio の Chatbot Studio への改名、AI FDE の GA、pro-code Agents の登場、Ontology MCP の GA である。

| 製品 | 内容／状態 | 出典 |
|---|---|---|
| AIP Logic | ノーコードで LLM 関数を作る環境。Automate と組み合わせると、Ontology の編集を「自動適用」するか「人のレビュー待ちにステージ」するかを選べる | [11][12] |
| AIP Chatbot Studio（旧 Agent Studio） | 2025-05-05 週に GA（当時の名称は AIP Agents）。発表時に、ad-hoc から完全自動までの 4-tier フレームワークを提示した。2026-04-22 の告知により、4/27 週から Chatbot Studio に改名された。API は後方互換を維持している | [13][14] |
| AIP Assist / Threads / Document Intelligence / Model Catalog | 各種補助機能 | [11] |
| AIP Evals | テストケースと評価器で本番前に検証する。「Generate evals」で自動生成もできる。2026-04 に AI FDE からも使えるようになった。組み込み評価器は 19 種 | [15][14] |
| AI FDE | Foundry を対話で操作するエージェント。モードは Data Integration、Ontology Editing、Functions、Governance など。「すべての操作はユーザー既存の権限を尊重」し、変更は Global Branch の proposal か pull request として提案される。2026-03-12 GA | [16][17] |
| Pro-code Agents | 2026-07-09 に登場。Claude Agent SDK、OpenAI Agents SDK、Google ADK のテンプレートがある。OSDK、OMCP、Palantir MCP に scoped permissions で認証するため、client secret は不要。Ontology binding と application restrictions でアクセス範囲を絞る。主に Automate から非同期に起動され、Global Branching で開発する | [18][19][20] |
| Autopilot（beta 2026-03-19） | automation と logic のフロー可視化、オブジェクト単位のトレース | [17] |
| AIP Evolve（beta 2026-08-18） | 複数のエージェントを協調させてシステムを改善する。モデル移行、コスト削減、レイテンシ削減、評価スコア改善、独自目標のガイド付き設定 | [21] |
| Object Timeline（2026-08-11） | 編集ごとに token 使用量、実行時間、「agentic coverage」を追跡する | [21] |
| Automate × Global Branching（2026-07-09） | automation をブランチ上で変更して E2E テストし、レビュアーの承認を経て merge する | [18] |

### 2.4 LLM を Ontology のツールに閉じ込める仕組み

| 仕組み | 内容 | 出典 |
|---|---|---|
| ツールの種類 | Action（Ontology 編集。「自動実行」か「ユーザー確認後に実行」を選べる）、Object Query（指定した object type と property に対するフィルタ・集計・リンク走査のみ）、Function（バージョン固定が可能）、Update application variable、Command、Request clarification。旧来の Ontology semantic search は legacy 扱い | [1] |
| Retrieval context | 固定 N 件のオブジェクト、または vector property による上位 K 件の意味検索 | [22] |
| 最小権限 | Chatbot Studio は「プラットフォームのセキュリティ統制により、LLM にはタスクに必要なものだけへのアクセスを与える」と説明している | [23] |
| アーキテクチャ上の主張 | 「送信データは第三者プロバイダに保持されず、再学習にも使われない」。人とエージェントの両方の活動に role、marking、purpose ベースの統制をかけ、end-to-end で可観測にする | [24] |

### 2.5 外部エージェント向けの経路（OSDK / MCP）

| 経路 | 内容 | 状態 | 出典 |
|---|---|---|---|
| OSDK | Ontology から型付き SDK を生成する（TS / Python / Java、加えて OpenAPI）。object、action（batch も可、`$returnEdits`）、function、AIP Logic を扱える。OAuth は public または confidential client | Python OSDK 2.x GA（2025-07-14 週） | [25][26] |
| Ontology MCP（OMCP） | Developer Console のアプリが持つ object type、action type、query function を MCP ツールとして公開する。application restrictions で実行できる Action を制限する。外部 LLM にデータを渡すことになる、という注意書きが明記されている。2026-03-26 に Copilot Studio と連携 | 2026-01 末 beta → GA（2026-06-25 告知、6/16 週から全 Foundry enrollment） | [27][28][17] |
| Palantir MCP | ビルダー向け。ontology の構造や transform を変更できるが、Ontology のデータは書けない（overview に「cannot write ontology data」と明記） | 2025-07-17 告知で「7/14 週から全 enrollment で利用可能（now available）」。ただしこの告知に「generally available」の語はない。正式な GA は 2026-06-25 告知「Palantir MCP is now generally available」（6/22 週から全 Foundry enrollment）。2026-06-30 に tool search（opt-in）を追加。**訂正**: 旧版の「2025-07-14 週に GA」は「広く提供開始」と読むのが正確で、GA 表記は 2026-06 | [29][26][28] |

「70 以上のツール」という数は第三者レビューの記述であり、未検証である [30]。Palantir MCP の overview ページにはツール総数の記載がない [29]。

### 2.6 セキュリティモデル

| 統制 | 分類 | 内容 | 出典 |
|---|---|---|---|
| Markings / Organizations / CBAC | Mandatory（強制） | 派生データに lineage 経由で伝播し、明示的に外さない限り継承される | [31][32] |
| Roles（Owner / Editor / Viewer / Discoverer） | Discretionary（任意） | リソース単位で付与する | [31] |
| Granular policies / Restricted views | Discretionary | ユーザー属性と列値を比較する規則による行レベル統制。下流へは伝播しない | [33] |
| Object / Property security policies | Discretionary（mandatory の追加も可） | object 単位で行、property 単位で列、組み合わせてセル単位を統制する。API、OSDK、アプリのすべてに適用される。2026-04-23 GA | [34][14] |
| Mandatory control properties | Mandatory | オブジェクト単位の marking や分類。許可する marking のリストで制約できる | [35] |
| Checkpoints | 目的の正当化と監査 | 機微な操作（Submit action、export など）の前に理由の入力を求め、利用者・時刻・理由・対象を記録する | [36] |
| Purpose-based access control | 方針 | 利用者は個々のデータセットではなく「Purpose」（特定の目的のためにキュレーションしたデータの集合）へのアクセスを申請する。各 Purpose には owner を置き、ガバナンス担当とデータ owner の双方がアクセス付与の理由を記録するため、監査人は「誰が何に」だけでなく「なぜ」アクセスできるかを追える（2020-12-04 のブログ） | [37] |
| Sensitive Data Scanner / Cipher / Retention / Audit logs | ガバナンス | FIPPs（公正情報取扱原則）を実装したもの | [38] |

この表で重要なのは、lineage に沿って伝播するのが mandatory な markings だけであり、行レベルの granular policies は下流に伝播しない点である。IFC ラベルをどちら側に置くかを決めるうえで、この区別が前提になる（6.2 節）。

### 2.7 デプロイと認証

| 項目 | 内容 | 出典 |
|---|---|---|
| Apollo | 制約ベースの継続デリバリ。エアギャップ環境に対応し、FedRAMP / IL5 / IL6 向けの統制を持つ | [39][40] |
| FedRAMP High | 2024-12 に、AIP、Apollo、Foundry、Gotham、FedStart を含む全製品で取得 | [41] |
| FedStart | 他社 SaaS を、Palantir の認定済み環境上で FedRAMP や IL5 として提供するプログラム | [42] |
| IL6 | 2022-10-10、Palantir Federal Cloud Service（PFCS）が DISA から DoD IL6 の Provisional Authorization を取得し、Secret Region を追加したと発表。発表時点で IL6 PA を持つのは Microsoft、AWS と並ぶ 3 社とされる | [120] |

### 2.8 業績・顧客事例

| 項目 | 数値 | 出典 |
|---|---|---|
| Q2 2026（2026-08-03 発表）売上 | 19.35 億ドル（前年比 +93%） | [43] |
| US commercial | 7.64 億ドル（+149%）、TCV 21.32 億ドル（+153%） | [43] |
| US government | 8.09 億ドル（+90%） | [43] |
| 100 万ドル超の案件数 | 220 件（500 万ドル超 98 件、1,000 万ドル超 73 件）。Rule of 40 スコアは 155 | [43] |
| 顧客数と顧客あたり売上（FY2025） | 顧客数 954（2024 年は 711）。上位 20 顧客の平均売上（TTM）9,390 万ドル（2024 年 6,460 万ドル、+45%）。FY2025 売上 44.75 億ドル。単純平均では 1 顧客あたり約 469 万ドル/年（44.75 億 ÷ 954、推論による試算） | [124] |
| FY2026 ガイダンス | 売上 81.5〜81.58 億ドル、US commercial 34.24 億ドル超 | [43] |
| US commercial の顧客数 | 653 社（+35%）、NDR 157% | [44] |
| 事例（Q2 call） | Kirkland & Ellis（数日かかった分析・起草が数分に）。非営利ヘルスシステム（3 年で 3,700 万ドル）。資産運用会社（3,500 万ドル）。顧客の顧客ごとの「agent swarms」が 1,000 万ドルの ACV に。Maven の「25,000 人超の builders」 | [44] |
| Tampa General Hospital | Foundry Ontology に看護師シフト、患者センサス、手術予定を統合。PACU（術後回復室）の患者待機時間 −28%、看護師配置比率 +30%、PACU 予測モデルの精度 95%、患者配置の管理時間 −83%（Palantir 自身の公表値） | [121] |
| Land O'Frost | 「週 70〜80 時間の削減見込み」は二次要約経由で、palantir.com/impact と AIPCon ページには記載が見つからず未検証 | [45] |
| Maven Smart System | 2024-05 に 4.8 億ドル、2025-05 に上限 13 億ドル。2026-03 に program of record 化が報道された | [46][47] |
| Army Enterprise Agreement | 2025-08-01。10 年で上限 100 億ドル、75 契約を統合 | [48][49] |
| AIP Bootcamp | 2024-06 時点で 1,300 件超（公表時期によって分母が異なる） | [50][51] |

一次情報は SEC 8-K [43]、10-K [124]、Palantir の事例ページ [121]、プレスリリース [120] であり、[44] は決算説明会の書き起こし（二次）、[45] は二次要約経由、[46]〜[48] は報道である。

### 2.9 批判と限界

| 論点 | 内容 | 出典 |
|---|---|---|
| NHS Federated Data Platform | 契約は 1.82 億ポンド（7 年で最大 3.3 億ポンド）、期間は 2023-11〜2027-02。BMA が反対動議を可決し、約 50,000 人の患者が反対の書簡を送った。契約書は 200 ページが黒塗りだった | [52][53]（Hansard 本文は取得不可） |
| US CLOUD Act | 米政府による開示リスクが指摘されている | [54]（本文は未取得のため未検証） |
| ICE（ImmigrationOS と報道された案件） | USAspending の ICE 向け Palantir 契約 70CTD022FR0000170（Investigative Case Management）で、2025-04-11 の修正 P00009 が 29,898,236 ドルを追加し、「new targeting and enforcement prioritization, self-deportation tracking, and immigration lifecycle process」の機能を配備するとしている。2025-09-25 に同額の P00012（ELITE を含む）、2026-09-16 に 20,061,497.76 ドルの option 行使（P00016）。契約全体の金額は 1.708 億ドル（2022-09〜2027-09）。「約 3,000 万ドル」は P00009 と整合する。USAspending の記載に「ImmigrationOS」という名称はなく、名称との対応は報道による | [123][55] |
| EFF の報告（2026-01-15）と Palantir の反論（2026-01-27） | EFF は、ICE が Palantir 製ツール ELITE（Enhanced Leads Identification & Targeting for Enforcement）を使い、Medicaid を含む HHS の住所データから強制送還対象を地図に表示し、住所の「confidence score」を出していると報じた。Palantir は「連邦機関横断の master database は作っていない」、ELITE は退去命令確定者など特定個人の住所推定に使う優先執行ツールで、HHS と ICE の情報共有は Privacy Act 等の要件下にあり、全操作が「indelible audit log」に残ると反論した | [122][56] |
| ロックイン | 単一の民間業者への依存、ベンダーロックイン、相互運用性が懸念されている | [46] |
| 技術的な制約 | OSv1 廃止（2026-06-30）による移行負担。名称と製品の頻繁な変更（Agent→Chatbot）。Ontology MCP で外部 LLM にデータが渡るリスクは、ドキュメント自身が警告している [27]。席単価・ライセンス単価は公開されていない。10-K は subscription と usage-based の価格体系を併用・試行中としている。公開されている規模感は、上位 20 顧客の平均 9,390 万ドル/年、全顧客の単純平均約 469 万ドル/年（推論）、ICE ICM 契約の 1 修正 約 2,990 万ドル、NHS FDP の 7 年最大 3.3 億ポンド [52] である | [5][14][27][124][123] |

## 3. 比較製品と分類

### 3.1 エージェント向けオントロジー／セマンティックレイヤー製品

| 製品 | モデルの形 | エージェント連携 | 書き込み（kinetic） | 状態・日付 | 出典 |
|---|---|---|---|---|---|
| **Microsoft Fabric IQ Ontology** | entity type、property、relationship、metric（DAX 由来）、rule（自然言語）、namespace、継承、data binding（仮想層）。Graph へのマテリアライズは任意。RDF/Turtle/OWL の import と export に対応 | ontology agent が proposal-first で変更を提案する。OneLake の RLS / OLS / CLS を尊重する | rules と Activator によるアラートまで。Palantir 型の Action はない | Preview。旧体験は 2027-01-31 に廃止。2025-11-18 の Ignite 2025 Book of News で「now in preview」として発表（Work IQ、Foundry IQ と並ぶ context layer） | [59][132] |
| Salesforce Data 360（旧 Data Cloud） | 統合プロファイル、zero copy、Agent Context Engine | Agentforce が利用 | Agentforce actions（CRM 上） | 改名済み | [60] |
| ServiceNow Workflow Data Fabric / Knowledge Graph | Knowledge Graph（データにビジネス文脈を付与）、Zero Copy connectors、RaptorDB、Integration Hub | 「data AI-ready…so AI agents can understand, trust, and act」と説明。AI Agents が案件履歴をもとに処理を実行 | ワークフロー（ServiceNow 上の処理。統制モデルの詳細は未確認） | 製品ページで構成要素を確認。Knowledge Graph 単体ページは取得できず、発表日も未確認 | [61] |
| SAP Business Data Cloud + SAP Knowledge Graph | data products ＋ Databricks ＋ KG | Joule agents に end-to-end のプロセス理解を与える | SAP のトランザクション（詳細未検証） | BDC は 2025-02-13 発表。SAP Knowledge Graph は 2024-10-08（TechEd）に発表され、購買発注・請求書・顧客などのビジネスエンティティ間の関係を既定で持ち、「Q1 2025 に Datasphere と Joule 経由で提供」予定とされた。2025-05-20 には Joule が Perplexity と SAP Knowledge Graph で回答を生成すると発表。GA の正式日付は未確認 | [62][134][135] |
| Databricks UC Metric views | YAML で定義する measure / dimension | Genie Agents。synonym で精度を改善 | なし | 2025-05-29 に Public Preview。ベース機能の GA 告知はプロダクト／SQL リリースノート（2025〜2026）で見つからず未確認。現行 docs ページには preview 表記がない（推論: GA 済みの可能性）。2026-06-26 に parameters が Public Preview、2026-09-24 に OpenSharing による共有が GA | [63][131] |
| Snowflake Semantic views | logical tables、relationships、facts、dimensions、metrics | Cortex Analyst / Cortex Agents のツール | なし | 2025-04-17 に preview。release 9.25（2025-08-25〜28）で「querying semantic views」が GA。Snowsight での作成・管理 UI は 2025-10-02 に GA | [64][129][130] |
| OSI → **Apache Ossie（incubating）** | YAML / JSON の semantic model（datasets、relationships、fields、metrics、`ai_context`）＋ ontology spec（EntityType / ValueType） | ツール間でセマンティクスを交換する | なし | 2025-09-23 発表 → 2025-12-12 に初版 spec → 2026-06-16 に Apache-2.0 へ再ライセンス → apache/ossie。現在 v0.2.0.dev0 | [65][66] |
| dbt Semantic Layer / MetricFlow | metrics-as-code | API、多数の連携 | なし | MetricFlow は 2025-10-14 に BSL から Apache-2.0 へ | [67][68] |
| Cube | cubes と views、Semantic SQL | MCP server。「エージェントは warehouse に直接クエリしない」。ポリシーは一度定義すればどこでも適用される | なし | v1.7.48 | [70] |
| AtScale | SML（OSS）、Git CI/CD | MCP | なし | — | [71] |
| Stardog | RDF KG、virtual graphs、推論、data quality constraints | Voicebox（LLM） | なし | — | [72] |
| Graphwise（Ontotext GraphDB ＋ PoolParty） | RDF / OWL、タクソノミー | GraphRAG | なし | 合併済み | [73] |
| TopBraid EDG | RDF / OWL / SHACL / SPARQL に基づくオントロジーガバナンス。専門家のレビュー・承認を経て公開し、全変更の版履歴と監査証跡を持つ | MCP、Python SDK、REST API でエージェントに context を供給。AI がデータから初期構造を提案し、ドリフトを検知して更新を提案する | なし（context 供給と統治が中心） | 製品ページで確認（日付なし） | [128] |
| Neo4j GraphRAG | property graph、KG builder | 各種 retriever | Cypher で書き込み可（統制は自前） | neo4j-graphrag 1.22.0（2026-10-01）。2025-10-02 に Aura Agent（early access、GA は 2025 Q4 予定と告知）と MCP server の正式サポート（Q4）を発表 | [74][136] |
| Glean Knowledge Graph | enterprise graph ＋ personal graph | エージェントの multi-hop 推論。ソースシステムの権限を継承 | なし | 2025-06-27 更新 | [75] |
| RelationalAI | PyRel の semantic model（Snowflake Native App） | graph / prescriptive / predictive reasoner、coding agent skills | なし | — | [76] |
| Kumo（Relational FM） | 複数テーブルにまたがる予測。PQL で記述 | — | なし | kumo.ai と www.kumo.ai は docs.nvidia.com/sdgm/rfm/overview へ 301 リダイレクトされる（2026-10-02 確認）。製品名は「Kumo Relational」で、NVIDIA docs に掲載。kumo-ai の GitHub org は「Client for NVIDIA Kumo relational foundation models」（NIM endpoint 向け、2026-08-12 作成）を公開している。NVIDIA 傘下に入ったことを強く示唆するが（推論）、買収の公式発表は確認できず未検証 | [77][133] |
| Google Enterprise KG | Entity Reconciliation（BigQuery）、schema.org / JSON-LD | — | なし | Preview | [78] |
| Amazon Neptune ＋ Bedrock KB GraphRAG | Neptune Analytics（vector ＋ graph） | マネージド GraphRAG（S3 のみ、データソースあたり 1,000 ファイル） | なし | — | [79][80] |
| Timbr | SQL ネイティブのオントロジーで既存 DB の上に仮想 KG を作る。concept（OWL Class に対応、多重継承）、property、relationship（推移的関係も可）、mapping、view | MCP server（`query_data`、`generate_sql`、`execute_sql`、`describe_knowledge_graph` など）。API key と ontology／agent 指定のヘッダで範囲を絞る | なし（MCP docs に書き込みツールの記載なし） | docs で確認 | [126][127] |

### 3.2 分類

| 分類 | 該当製品 | 書き込み層 |
|---|---|---|
| 読み取り専用のセマンティック層 | Snowflake、Databricks、dbt、Cube、AtScale、Ossie、Timbr | なし |
| 文書 KG / GraphRAG | Neo4j、Glean、Neptune、Graphwise | なし（Neo4j は Cypher で可だが統制は自前） |
| オントロジーと書き込みを統合 | Palantir。Salesforce、ServiceNow、SAP はアプリ固有の範囲で近いものを持つ | あり |
| 中間 | Fabric IQ（rules と proposal-first agent はあるが、統制された書き込み Action はない）、TopBraid EDG（SHACL と承認ワークフローでスキーマを統治するが、業務データへの Action はない） | 限定的 |

AI-only company の観点では、読み取り専用のセマンティック層は「LLM の読み取り精度を上げる部品」にはなるが、「エージェントの書き込みを統制する層」の代わりにはならない（推論）。

### 3.3 2025〜2026 年の追加事例（エンタープライズエージェントへの KG／オントロジー適用）

| 事例 | 内容 | 出典 |
|---|---|---|
| Microsoft Fabric IQ（2025-11-18） | Ignite 2025 で、Work IQ（Microsoft 365）、Fabric IQ、Foundry IQ を束ねた「universal context layer」を発表。Fabric IQ はビジネスエンティティとその関係の semantic model で、Power BI の semantic layer（2,000 万モデル）を業務オペレーションへ拡張し、「define once, reuse everywhere across analytics, apps and agents」を掲げる。Foundry IQ は Fabric IQ を知識源の一つとして agentic retrieval を行い、ユーザー権限を尊重する | [132] |
| SAP Knowledge Graph（2024-10-08 発表 → 2025） | 購買発注・請求書・顧客などの関係を既定で持つ KG を Datasphere と Joule に提供し、AI を SAP 固有のビジネスセマンティクスに接地させる。2025-05-20 には Joule が Perplexity と SAP Knowledge Graph を使い、業務データに基づく構造化回答を返すと発表 | [134][135] |
| Neo4j Aura Agent（2025-10-02） | エンタープライズデータに接地したエージェントを構築・デプロイする Aura Agent（early access）と、MCP server の正式サポートを発表。Uber、Walmart、Klarna などのエージェント展開を支えるとしているが、定量値は示されていない | [136] |
| Tampa General Hospital（Palantir） | Ontology に看護師シフト・センサス・手術予定を統合し、患者配置の管理時間 −83% など（2.8 節） | [121] |

いずれも「エージェントに業務エンティティと関係の型を与える」点は共通だが、Palantir の Action に相当する統制された書き込み経路を公開情報で確認できたのは Palantir だけである（推論）。

## 4. 研究論文（2023〜2026）

arXiv ID はすべて arXiv API か abs ページで確認済みである。

### 4.1 オントロジー／セマンティック層と text-to-SQL・分析

| arXiv | タイトル（年） | 要点・数値 | 出典 |
|---|---|---|---|
| 2311.07509 | KG Benchmark for Enterprise SQL QA（2023, data.world） | GPT-4 の zero-shot で、SQL 直接は 16%、KG 表現経由は 54%。dbt は自社 Semantic Layer で「addressable な質問で 83%」と報告している [69] | [93] |
| 2405.11706 | Ontologies to the Rescue!（2024） | Ontology-based Query Check＋LLM Repair で精度 72%（うち 8% は「わからない」）、誤り率 20% | [94] |
| 2604.25149 | Semantic Layers for Reliable LLM Analytics（2026） | 4KB のセマンティック文書の追加で +17〜23pt。モデル間の差は有意でなく、セマンティクスの有無が分散のほぼすべてを説明する | [95] |
| 2608.26157 | GROUND（2026） | 統制されたセマンティック層で SQL を検証する（metric / join / grain / RLS / cost）。強制された保証（RLS とフィルタ）は全モデルで違反 0。metric 定義だけではデータが漏れる | [96] |
| 2606.05634 | GATE（2026） | 実行フィードバックからセマンティック層を自動的に補う | [97] |
| 2411.07763 | Spider 2.0 | 実際の enterprise text-to-SQL の難しさ | [119] |

### 4.2 GraphRAG・KG 推論・KG 型記憶

| arXiv | タイトル（年） | 要点・数値 | 出典 |
|---|---|---|---|
| 2404.16130 | GraphRAG（Microsoft, 2024） | entity KG とコミュニティ要約。graphrag v3.2.0（2026-09-24） | [98][81] |
| 2410.05779 | LightRAG（2024） | 軽量な graph RAG | [99][82] |
| 2502.11371 | RAG vs. GraphRAG（2025, 改訂 2026-03） | タスクによって優劣が分かれ、併用すると一貫して改善する | [100] |
| 2412.15235 | OG-RAG（2024） | ontology で根拠付けた hypergraph。事実の recall +55%、正答 +40% | [101] |
| 2405.14831 / 2501.13956 | HippoRAG / Zep（Graphiti） | KG 型の長期記憶。既存のメモリ調査と接続する部分 | [102][103][83] |
| 2307.07697 / 2407.10805 / 2402.11163 | Think-on-Graph / ToG-2 / KG-Agent | KG を辿るエージェント型推論 | [104][105][106] |
| 2607.22571 | SCAIR（ACL 2026 Industry） | 公開ベンチで強い手法は実際の enterprise KG では汎化しない。スキーマと業務制約を明示すると、再学習なしで大きく改善する | [107] |

### 4.3 オントロジー工学・制約付きエージェント・SHACL

| arXiv | タイトル（年） | 要点・数値 | 出典 |
|---|---|---|---|
| 2304.02711 | SPIRES / OntoGPT | zero-shot での KB 充填。ontogpt v1.2.0（2026-09） | [108][84] |
| 2307.16648 | LLMs4OL | LLM による ontology learning | [109] |
| 2307.16699、2411.09601、2408.15256、2604.01344 | LLM とオントロジー工学（OntoChat、IDEA2 の expert-in-the-loop CQ） | competency question（オントロジーが答えるべき問い）の抽出は、人間との協調が前提 | [110][111][112][113] |
| 2604.08552 | ARMS: ontology 制約エージェント（2026） | 実行時にテンプレートと語彙サービスをツールとして参照する。precision 0.56→0.93、ontology 制約付きフィールドは 0.36→0.92 | [114] |
| 2512.20275 | G-SPEC（neuro-symbolic, 2025） | KG と SHACL でエージェントの行動を検証する。安全違反 0（ベースラインの準拠率 82.4%）、レイテンシ 142ms。改善の 68% は KG、24% は SHACL による | [115] |
| 2608.09028 | PolicyKG（2026） | 規程を SHACL に変換する。shape の F1 0.866 | [116] |
| 2608.07530 | NL2SHACL-Bench（2026） | 構文的に正しい SHACL は出せるが、複雑な制約で意味的に等価なものは作れない。人のレビューが必須 | [117] |
| 2507.08432 | xpSHACL（2025） | SHACL 違反を LLM で説明する | [118] |

論文群から読み取れる傾向は 2 点ある（推論）。第一に、精度の主因はモデルの差よりもセマンティクス（スキーマ、業務制約）を明示するかどうかである（2604.25149、2607.22571）。第二に、安全性の保証は LLM の自己規律からではなく、決定的な検証層（SHACL、統制セマンティック層）から得られている（2512.20275、2608.26157）。

## 5. 標準と SHACL ガードレール

### 5.1 標準の状態（2026-10 時点）

| 標準 | 状態 | 出典 |
|---|---|---|
| RDF 1.2 Concepts | Candidate Recommendation（2026-04-07）。triple terms（文に関する文）、方向付き言語文字列、バージョン宣言 | [85] |
| SHACL 1.2 Core | Working Draft（2026-09-18）。node expressions、`sh:targetWhere`。Rules / UI / Profiling / SPARQL は別モジュール | [86] |
| OWL 2 | W3C Recommendation（2012。既知の事実で、今回は再取得していない） | — |
| schema.org | v30.1（2026-09-15） | [87] |
| FIBO（EDM Council, OWL） | master_2026Q2（2026-07-14）、MIT | [88][89] |
| gist（Semantic Arts、上位の企業オントロジー） | v14.1.0（2026-04-17）、CC-BY-4.0 | [90] |
| BFO / ISO/IEC 21838-2 | BFO-2020。**訂正**: リポジトリの記載は「ISO 21838-2:2020」だが、ISO の公開メタデータでは ISO/IEC 21838-2:2021（Part 2: Basic Formal Ontology、2021-11-30 発行、第 1 版）。同シリーズは Part 1（要件、2021-08-06）、Part 3 DOLCE と Part 4 TUpper（いずれも 2023-09-19）、Part 5 UFO（DIS 段階） | [91][125] |
| Common Core Ontologies | v2.2（2026-08-14）、BSD-3 | [92] |
| Apache Ossie（旧 OSI） | v0.2.0.dev0（semantic model と ontology spec） | [66] |

### 5.2 SHACL をガードレールとして使う方法

| 手順 | 内容 | 対応する既存の仕組み・実証 |
|---|---|---|
| 事前検証 | Action を提出する前に、「変更後のグラフ」を SHACL で検証する | Palantir の submission criteria [6]、Validate API [9] |
| 修復ループ | 違反を severity とメッセージ付きでエージェントに返し、修復させる | 2405.11706 の OBQC＋Repair [94]、違反説明は xpSHACL [118] |
| 実証 | 行動検証で安全違反 0、統制セマンティック層で RLS 違反 0 | G-SPEC [115]、GROUND [96] |
| 制約の作成・変更 | NL→SHACL の自動生成は意味的な誤りが残るため、人のレビュー対象とする | NL2SHACL-Bench [117]、PolicyKG の F1 0.866 [116] |

## 6. AI-only company への設計含意（推論・提案）

本節はすべて推論・提案である。

### 6.1 写像表: Ontology ↔ Cedar/OpenFGA ↔ IFC ↔ 監査

エージェントは kinetic ontology を経由してしか世界を変えない、という前提で写像する。

| Ontology の概念 | 認可（Cedar / OpenFGA） | IFC（FIDES / CaMeL） | 監査 |
|---|---|---|---|
| Object type / instance | Cedar の resource 型と entity。属性は ABAC の入力 | オブジェクトとプロパティに機密性・完全性ラベル（markings に相当） | — |
| Link type | OpenFGA の relation tuple（`doc#owner@user`）として ReBAC の源泉にする | ラベルの伝播経路（lineage） | — |
| Action type | Cedar の action。principal は agent ID と委任元、context にはパラメータを入れる | sink のチェック。side effect（webhook や外部送信）を「egress」として扱い、低ラベル化の可否を判定する | action log（誰が、どの Action を、どのパラメータで、どう編集したか） |
| Submission criteria | Cedar の `when` 条件、または SHACL shape（変更後の状態の不変条件） | 入力ラベル ≤ 出力の許容ラベル | 拒否理由も記録 |
| Checkpoints（理由の入力） | 高リスク Action で必須にする | 低ラベル化（declassify）時の正当化 | エージェントの「理由」と、その根拠になったオブジェクト ID |
| Object / Property security policy | Cedar の entity filter、OpenFGA の `ListObjects` | 読み出し時の汚染（taint）付与 | read audit |

### 6.2 既存調査との接続

| 既存調査 | 既存の推奨 | オントロジー層での接続（推論・提案） |
|---|---|---|
| authorization_zanzibar_openfga_cedar.md | 閲覧・操作可否は OpenFGA（ReBAC）、業務ルールは Cedar、判定は PDP 一箇所に集約 | Link type を OpenFGA の tuple の源泉とし、Action type を Cedar の action とする。Action 実行の判定点を既存 PDP に置けば、「Action registry が PEP、PDP が判定」の分担になり、集約方針と矛盾しない。submission criteria のうち状態の不変条件は SHACL、主体・文脈の条件は Cedar に分けて置く |
| information_flow_control_and_exfiltration.md | 外部送信シンクを構造的に持たない。データフローは Gateway でラベル伝播とシンク検査。権限引数は出所検査。検出器は境界にしない | Action の side effect 宣言（webhook、通知、外部送信）を egress sink の唯一の列挙とし、宣言のない外部送信経路を持たない。markings 相当の mandatory ラベルを lineage で伝播させる（Palantir でも lineage で伝播するのは markings だけ [31][32]）。Action パラメータのうち権限に関わる引数（宛先、対象 ID）は出所検査の対象にする。Ontology MCP の「外部 LLM にデータが渡る」という警告 [27] は、lethal trifecta の外部送信脚がツール公開経路にも生じることを示す |
| isolation_durable_execution_prompt_injection.md | 制御フローは Temporal Workflow で固定 | Action を Temporal の activity として呼び出し、Workflow 側が呼べる Action の集合を固定する。revert と action log は Workflow の補償処理と監査に使える |
| メモリ調査（Zep/Graphiti） | メモリを正本にしない。台帳／エピソード／手続き／人のフィードバックの 4 種類を物理分離。自己改善は人のフィードバック→候補ルール→PR レビュー→評価回帰→段階適用 | オントロジー（業務 DB＋Action registry）を台帳＝正本とし、Graphiti（2501.13956）の temporal KG はエピソード記憶に限定する。KG 型の記憶とオントロジーを混同しない。自己改善フローは 6.4 節のオントロジー進化フローと同じ形にそろえる |

### 6.3 設計方針

| # | 方針 | 根拠 |
|---|---|---|
| 1 | **書き込み経路は Action だけにする。** 生 SQL の書き込みや任意の REST 呼び出しはエージェントに渡さない | Palantir は「Actions-only」モデルを推奨し、データセットへの直接 Edit 権限を非推奨にしている [7] |
| 2 | **Action ＝ 型付きツールスキーマ ＝ MCP ツールにする。** Action の定義からツールを自動生成し、ツールごとに「自動実行／確認必須」を決める | Ontology MCP [27]、Chatbot Studio の Action tool [1] |
| 3 | **Mandatory（ラベル）と discretionary（ロールや行ポリシー）を分ける。** IFC ラベルは mandatory 側に置き、派生物へ自動で伝播させる | Palantir では markings だけが lineage で伝播する [31][32][33] |
| 4 | **書き込み前に検証する。** SHACL／Cedar の dry-run を経てから commit する | Validate API [9]、5.2 節 |
| 5 | **自動適用かステージングかを分ける。** リスク層（金額、外部への影響、不可逆性）で使い分ける | Automate × Logic の「自動適用 or 人のレビュー待ちにステージ」[12] |

### 6.4 オントロジー進化をエージェントに任せるときの統治

先行事例は次のとおりである。

| 事例 | 統治の形 | 出典 |
|---|---|---|
| Palantir AI FDE | Ontology Editing モードで、変更は Global Branch の proposal として出る | [16] |
| Global Branching | リソースごとの承認ポリシーとレビュアー | [58][18] |
| AIP Evolve | 改善目標をエージェントに与える | [21] |
| Fabric IQ ontology agent | proposal-first、名前付きバージョン、復元 | [59] |

提案フローは次のとおりである（提案）。

1. エージェントがスキーマ差分（object / link / action / constraint）を提案する。
2. ブランチ上で以下を実行する。
   - competency question のテスト（2408.15256 / 2604.01344）[112][113]
   - AIP Evals 相当の回帰評価 [15]
   - 既存オブジェクトのマイグレーション検証（OSv2 の「スキーマ変更時の編集マイグレーション」に相当）[5]
   - SHACL の自己整合チェック
3. 人がレビューして merge する。認可ポリシー、IFC ラベル、制約、外部 side effect を伴う Action に触れる差分は、必ず人のレビューに回す。

**自己改変の禁止領域**: エージェントは、自分の権限を決めるメタデータ（Cedar ポリシー、marking 付与、Checkpoint の設定）を変更できないようにする。Palantir でも、marking 付与者の変更は Checkpoint の対象になっている [36]。

### 6.5 オントロジー層 vs 素の DB＋ツール API

| 観点 | オントロジー（kinetic）層 | 素の DB＋ツール API |
|---|---|---|
| LLM の精度 | セマンティクスを明示すると +17〜38pt（2311.07509、2604.25149） | スキーマから推測させるため誤りやすい |
| 安全性 | Action 単位の最小権限、事前検証、監査、revert | API ごとにばらばら。生 SQL は危険 |
| 漏洩防止 | 行・列・セルのポリシーとラベル伝播を一元化 | 各 API で重複実装し、抜けが出やすい（GROUND では metric だけでは漏洩した） |
| 監査・説明責任 | action log と Checkpoints で what と why が残る | ログの形式がまちまち |
| 変更容易性 | スキーマ進化のガバナンスが必要。モデリングに初期コストがかかる | 速いが統制が効かない |
| ロックイン | Palantir は強い。Fabric は preview。OSS なら Ossie / RDF / SHACL で相互運用 | 低い |
| コスト | Palantir の単価は非公開。FY2025 の 1 顧客あたり単純平均は約 469 万ドル/年、上位 20 顧客平均は 9,390 万ドル/年 [124]（推論による試算を含む） | 安い |
| 性能 | 書き込み経路が Action 経由に限られる（OSv2 で 1 Action 10k 件） | 自由 |

### 6.6 OSS で自作する場合の最小構成（提案）

| 層 | 構成要素 |
|---|---|
| 業務 DB（正本） | Postgres |
| Action registry | Postgres の上に置く。型付きパラメータ＋前提条件＋side effect 宣言 |
| 事前検証 | Cedar（認可）と SHACL（pySHACL など）または JSON Schema |
| ReBAC | OpenFGA |
| 指標の定義 | Ossie / MetricFlow の YAML |
| エピソード記憶 | Graphiti（Zep）の temporal KG |
| エージェントへの公開 | MCP サーバ（Action を 1 対 1 でツール化） |
| ラベル伝播 | lineage 表で実装 |
| 物理的強制 | 「エージェントは書き込み経路を Action しか持たない」ことを、ネットワークと DB の権限で物理的に強制する |

## 7. 未検証事項

| 項目 | 状況 |
|---|---|
| Databricks metric views のベース機能の GA 日 | 2025-05-29 の Public Preview は確認。GA 告知はプロダクト／SQL リリースノート（2025-01〜2026-09）で見つからない |
| Kumo と NVIDIA の買収関係 | リダイレクトと「NVIDIA Kumo Relational」の名称は確認。NVIDIA newsroom の RSS に該当なし、SEC 全文検索 API はエラーで、公式の買収発表は未確認 |
| SAP Knowledge Graph の GA 日 | 発表（2024-10-08）と「Q1 2025 提供予定」は確認。GA の告知は news.sap.com のタグページで見つからない |
| ServiceNow Knowledge Graph の発表日・統制モデル | 製品ページで構成要素のみ確認。Knowledge Graph 単体ページは本文を取得できず |
| Palantir の TCO（総保有コスト） | 席単価・ライセンス単価は非公開。10-K の顧客数・上位 20 顧客平均売上と個別契約額のみ。NHS FDP の契約文書は england.nhs.uk と Contracts Finder API から取得できず、金額は [52] のまま |
| その他 | Land O'Frost の数値（palantir.com/impact と AIPCon ページに記載なし）、US CLOUD Act の記事本文（未取得）、Palantir MCP の「70 以上のツール」（第三者レビュー。公式 overview に総数の記載なし） |

調査途中でセッションの WebSearch 上限（200 回）に達した。以降は Palantir ドキュメント、W3C、GitHub API、arXiv API への直接アクセスで裏付けを取り、裏付けが取れなかった項目に「未検証」を付けている。2026-10-02 の再検証では、WebSearch を使わずに一次 URL、r.jina.ai 経由の取得、USAspending API、SEC EDGAR、ISO 公開メタデータ、GitHub API で裏付けを取った（下の追補を参照）。

## 追補: 再検証ログ（2026-10-02）

**検証済みにした項目**
- Ontology MCP の GA: 2026-06-25 告知（6/16 週から全 Foundry enrollment）[28]。
- IL6: 2022-10-10、PFCS が DISA から IL6 PA を取得 [120]。
- Purpose-based access control: 2020-12-04 のブログ本文を r.jina.ai 経由で取得し、内容を 2.6 節に記載 [37]。
- EFF 報告（2026-01-15、ELITE と HHS/Medicaid データ）と Palantir の反論（2026-01-27）の内容 [122][56]。
- ICE 契約額: USAspending で 2025-04-11 の修正 P00009 が 29,898,236 ドル（「約 3,000 万ドル」と整合）[123]。
- Tampa General の数値: Palantir の事例ページで確認（PACU 待機 −28% など）[121]。
- Fabric IQ の発表日: 2025-11-18（Ignite 2025 Book of News）[132]。
- Snowflake semantic views: 2025-04-17 に preview、release 9.25（2025-08-25〜28）で querying が GA [129][130]。

**訂正した項目**
- Palantir MCP の GA: 「2025-07-14 週に GA」→ 2025-07 は「全 enrollment で now available」（GA の語なし）、正式な GA 告知は 2026-06-25（6/22 週）[26][28]。
- BFO: ISO/IEC 21838-2 の発行年を「2020（リポジトリ記載）」から 2021（2021-11-30 発行）に訂正 [125]。
- 「Tampa General / Land O'Frost」の行を分割し、Tampa General の数値を一次情報に差し替え。旧記載の「ベッド割当・人員配置の自動化」は Tampa General の事例と整合する。

**新規追加**
- Palantir FY2025 10-K の顧客数 954、上位 20 顧客平均売上 9,390 万ドル、価格体系（subscription／usage-based）の記述 [124]。
- ServiceNow Workflow Data Fabric、Timbr（MCP server を含む）、TopBraid EDG の行を一次情報で埋めた [61][126][127][128]。
- Databricks metric views の Public Preview 日（2025-05-29）と、その後の機能の告知 [131]。
- Kumo: 製品名「NVIDIA Kumo Relational」、kumo-ai GitHub org の NVIDIA 名義クライアント [133]。
- 3.3 節（追加事例）: Fabric IQ／Foundry IQ、SAP Knowledge Graph、Neo4j Aura Agent [132][134][135][136]。
- ISO/IEC 21838 シリーズ（Part 1、3、4、5）の状態 [125]。

**未検証のまま残った項目**
- Databricks metric views のベース機能の GA 日、Kumo の買収の公式発表、SAP Knowledge Graph の GA 日、ServiceNow Knowledge Graph の発表日、Land O'Frost の数値、NHS FDP の契約文書、US CLOUD Act 記事本文、Palantir MCP の「70 以上のツール」、Palantir の単価・TCO（7 節を参照）。

## 参考文献

**Palantir（ドキュメント・アナウンス・ブログ）**

- [1] Palantir, AIP Agent Studio: Tools, 2026-10-02 参照. https://www.palantir.com/docs/foundry/agent-studio/tools
- [2] Palantir, Ontology: Core concepts, 2026-10-02 参照. https://www.palantir.com/docs/foundry/ontology/core-concepts
- [3] Palantir, Actions on interfaces, 2026-10-02 参照. https://www.palantir.com/docs/foundry/action-types/actions-on-interfaces
- [4] Palantir, Why Ontology, 2026-10-02 参照. https://www.palantir.com/docs/foundry/ontology/why-ontology
- [5] Palantir, Object backend overview（Object Storage v2）, 2026-10-02 参照. https://www.palantir.com/docs/foundry/object-backend/overview
- [6] Palantir, Action types: Submission criteria, 2026-10-02 参照. https://www.palantir.com/docs/foundry/action-types/submission-criteria
- [7] Palantir, Action types: Permissions, 2026-10-02 参照. https://www.palantir.com/docs/foundry/action-types/permissions
- [8] Palantir, Action types: Overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/action-types/overview
- [9] Palantir, API: Validate action, 2026-10-02 参照. https://www.palantir.com/docs/foundry/api/ontology-resources/actions/validate-action
- [10] Palantir, Branching action types, 2026-10-02 参照. https://www.palantir.com/docs/foundry/action-types/branching-action-types
- [11] Palantir, AIP features, 2026-10-02 参照. https://www.palantir.com/docs/foundry/aip/aip-features
- [12] Palantir, AIP Logic integration with Automate, 2026-10-02 参照. https://www.palantir.com/docs/foundry/logic/aip-logic-integration-automate
- [13] Palantir, Announcements 2025-04. https://www.palantir.com/docs/foundry/announcements/2025-04
- [14] Palantir, Announcements 2026-04. https://www.palantir.com/docs/foundry/announcements/2026-04
- [15] Palantir, AIP Evals: Getting started, 2026-10-02 参照. https://www.palantir.com/docs/foundry/aip-evals/getting-started
- [16] Palantir, AI FDE overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/ai-fde/overview
- [17] Palantir, Announcements 2026-03. https://www.palantir.com/docs/foundry/announcements/2026-03
- [18] Palantir, Announcements 2026-07. https://www.palantir.com/docs/foundry/announcements/2026-07
- [19] Palantir, Agents overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/agents/overview/
- [20] Palantir, Agents: Scoped permissions, 2026-10-02 参照. https://www.palantir.com/docs/foundry/agents/scoped-permissions/
- [21] Palantir, Announcements 2026-08. https://www.palantir.com/docs/foundry/announcements/2026-08
- [22] Palantir, AIP Agent Studio: Retrieval context, 2026-10-02 参照. https://www.palantir.com/docs/foundry/agent-studio/retrieval-context
- [23] Palantir, Chatbot Studio overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/chatbot-studio/overview
- [24] Palantir, Architecture center: AIP architecture, 2026-10-02 参照. https://www.palantir.com/docs/foundry/architecture-center/aip-architecture
- [25] Palantir, TypeScript OSDK, 2026-10-02 参照. https://www.palantir.com/docs/foundry/ontology-sdk/typescript-osdk
- [26] Palantir, Announcements 2025-07. https://www.palantir.com/docs/foundry/announcements/2025-07
- [27] Palantir, Ontology MCP overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/ontology-mcp/overview
- [28] Palantir, Announcements 2026-06. https://www.palantir.com/docs/foundry/announcements/2026-06
- [29] Palantir, Palantir MCP overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/palantir-mcp/overview
- [30] ChatForest, Palantir MCP server review（第三者レビュー、未検証）. https://chatforest.com/reviews/palantir-mcp-server/
- [31] Palantir, Security overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/security/overview
- [32] Palantir, Markings, 2026-10-02 参照. https://www.palantir.com/docs/foundry/security/markings
- [33] Palantir, Manage granular policies, 2026-10-02 参照. https://www.palantir.com/docs/foundry/platform-security-management/manage-granular-policies
- [34] Palantir, Object security policies, 2026-10-02 参照. https://www.palantir.com/docs/foundry/object-permissioning/object-security-policies
- [35] Palantir, Mandatory control properties, 2026-10-02 参照. https://www.palantir.com/docs/foundry/object-link-types/mandatory-control-properties
- [36] Palantir, Checkpoints: Core concepts, 2026-10-02 参照. https://www.palantir.com/docs/foundry/checkpoints/core-concepts
- [37] Palantir Blog, Purpose-based access controls at Palantir, 2020-12-04（r.jina.ai 経由で取得、2026-10-02）. https://blog.palantir.com/purpose-based-access-controls-at-palantir-f419faa400b3
- [38] Palantir, Data protection and governance, 2026-10-02 参照. https://www.palantir.com/docs/foundry/security/data-protection-and-governance
- [39] Palantir, Apollo: Introduction, 2026-10-02 参照. https://www.palantir.com/docs/apollo/core/introduction
- [40] Palantir Blog, Palantir Apollo Orchestration: Constraint-based continuous deployment for modern architectures. https://blog.palantir.com/palantir-apollo-orchestration-constraint-based-continuous-deployment-for-modern-architectures-cdf42da19ba4
- [41] BusinessWire, Palantir Granted FedRAMP High Baseline Authorization, 2024-12-03. https://www.businesswire.com/news/home/20241203054493/en/Palantir-Granted-FedRAMP-High-Baseline-Authorization
- [42] Palantir Blog, Introducing Palantir FedStart. https://blog.palantir.com/introducing-palantir-fedstart-cd5995d0dfaa
- [43] Palantir, SEC 8-K Exhibit 99.1 Q2 2026 press release, 2026-08-03. https://www.sec.gov/Archives/edgar/data/0001321655/000132165526000039/a2026q2ex991pressrelease.htm
- [44] The Motley Fool, Palantir (PLTR) Q2 2026 earnings call transcript, 2026-08-10. https://www.fool.com/earnings/call-transcripts/2026/08/10/palantir-pltr-q2-2026-earnings-call-transcript/
- [45] Palantir, Impact（二次要約経由、数値未検証）. https://www.palantir.com/impact/
- [46] Military.com, Pentagon expands Palantir's role in AI contract, 2026-03-22. https://www.military.com/feature/2026/03/22/pentagon-expands-palantirs-role-ai-contract.html
- [47] Tom's Hardware, Pentagon formalizes Palantir's Maven AI as a core military system, 2026. https://www.tomshardware.com/tech-industry/artificial-intelligence/pentagon-formalizes-palantirs-maven-ai-as-a-core-military-system-with-multi-year-funding-platforms-investment-grows-to-usd13-billion-from-usd480-million-in-2024
- [48] Washington Technology, Palantir signs $10B enterprise agreement with Army, 2025-08. https://www.washingtontechnology.com/contracts/2025/08/palantir-signs-10b-enterprise-agreement-army/407153/
- [49] U.S. Army, U.S. Army awards enterprise service agreement to enhance military readiness and drive operational efficiency, 2025. https://www.army.mil/article/287506/u_s_army_awards_enterprise_service_agreement_to_enhance_military_readiness_and_drive_operational_efficiency
- [50] Palantir, AIP Bootcamp. https://www.palantir.com/platforms/aip/bootcamp/
- [51] Palantir Blog, Deploying full-spectrum AI in days: How AIP Bootcamps work. https://blog.palantir.com/deploying-full-spectrum-ai-in-days-how-aip-bootcamps-work-21829ec8d560
- [52] The Lowdown, Palantir: the controversy, the contracts and the campaign. https://lowdownnhs.info/topics/accountablility/palantir-the-controversy-the-contracts-and-the-campaign/
- [53] UK Parliament Hansard, NHS Federated Data Platform, 2026-04-16（本文取得不可）. https://hansard.parliament.uk/Commons/2026-04-16/debates/2FDCA71C-D0C1-4738-BEE8-A4BDA311DB99/NHSFederatedDataPlatform
- [54] TechRadar, NHS users report that it is "awful" to use Palantir（本文未取得、未検証）. https://www.techradar.com/pro/security/nhs-users-report-that-it-is-awful-to-use-palantir-could-be-forced-to-exit-nhs-after-pushback-from-staff-mps-unions-and-pressure-groups-over-federated-data-platform
- [55] Wikipedia, Palantir（二次情報）. https://en.wikipedia.org/wiki/Palantir
- [56] Palantir Blog, Correcting the record: Response to the EFF January 15, 2026 report on Palantir, 2026-01-27（r.jina.ai 経由で取得、2026-10-02）. https://blog.palantir.com/correcting-the-record-response-to-the-eff-january-15-2026-report-on-palantir-4b3a12536cd2
- [57] Palantir, AIP overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/aip/overview
- [58] Palantir, Foundry Branching overview, 2026-10-02 参照. https://www.palantir.com/docs/foundry/foundry-branching/overview

**比較製品**

- [59] Microsoft Learn, Fabric IQ Ontology overview, 2026-10-02 参照. https://learn.microsoft.com/en-us/fabric/iq/ontology/overview
- [60] Salesforce, Data 360. https://www.salesforce.com/data/
- [61] ServiceNow, Workflow Data Fabric（r.jina.ai 経由で取得、2026-10-02）. https://www.servicenow.com/platform/workflow-data-fabric.html（旧 URL https://www.servicenow.com/products/workflow-data-fabric.html は本文なし）
- [62] SAP News, SAP Business Data Cloud and Databricks turbocharge business AI, 2025-02-13. https://news.sap.com/2025/02/sap-business-data-cloud-databricks-turbocharge-business-ai/
- [63] Databricks, Metric views. https://docs.databricks.com/aws/en/metric-views/
- [64] Snowflake, Semantic views overview. https://docs.snowflake.com/en/user-guide/views-semantic/overview
- [65] Snowflake Blog, Open Semantic Interchange, 2025-09-23. https://www.snowflake.com/en/blog/open-semantic-interchange-ai-standard/
- [66] Apache Software Foundation, apache/ossie. https://github.com/apache/ossie
- [67] dbt Labs, dbt Semantic Layer. https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl
- [68] dbt Labs, MetricFlow. https://github.com/dbt-labs/metricflow
- [69] dbt Labs Blog, Semantic layer as the data interface for LLMs. https://www.getdbt.com/blog/semantic-layer-as-the-data-interface-for-llms
- [70] Cube, Introduction. https://docs.cube.dev/docs/introduction
- [71] AtScale, Semantic layer. https://www.atscale.com/product/semantic-layer/
- [72] Stardog, Documentation. https://docs.stardog.com/
- [73] Graphwise. https://graphwise.ai/
- [74] Neo4j, neo4j-graphrag-python documentation. https://neo4j.com/docs/neo4j-graphrag-python/current/
- [75] Glean Blog, Knowledge graph: the agentic engine, 2025-06-27 更新. https://www.glean.com/blog/knowledge-graph-agentic-engine
- [76] RelationalAI, Documentation. https://docs.relational.ai/
- [77] NVIDIA, Relational Foundation Model overview. https://docs.nvidia.com/sdgm/rfm/overview
- [78] Google Cloud, Enterprise Knowledge Graph overview. https://docs.cloud.google.com/enterprise-knowledge-graph/docs/overview
- [79] AWS, What is Neptune Analytics. https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html
- [80] AWS, Bedrock Knowledge Bases: Build graphs. https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-build-graphs.html
- [81] Microsoft, graphrag（v3.2.0, 2026-09-24）. https://github.com/microsoft/graphrag
- [82] HKUDS, LightRAG. https://github.com/HKUDS/LightRAG
- [83] Zep, graphiti. https://github.com/getzep/graphiti
- [84] Monarch Initiative, ontogpt（v1.2.0, 2026-09）. https://github.com/monarch-initiative/ontogpt

**標準**

- [85] W3C, RDF 1.2 Concepts and Abstract Data Model, Candidate Recommendation 2026-04-07. https://www.w3.org/TR/rdf12-concepts/
- [86] W3C, SHACL 1.2 Core, Working Draft 2026-09-18. https://www.w3.org/TR/shacl12-core/
- [87] schema.org, schemaorg（v30.1, 2026-09-15）. https://github.com/schemaorg/schemaorg
- [88] EDM Council, FIBO specification. https://spec.edmcouncil.org/fibo/
- [89] EDM Council, fibo（master_2026Q2, 2026-07-14）. https://github.com/edmcouncil/fibo
- [90] Semantic Arts, gist（v14.1.0, 2026-04-17）. https://github.com/semanticarts/gist
- [91] BFO-ontology, BFO-2020. https://github.com/BFO-ontology/BFO-2020
- [92] CommonCoreOntology, CommonCoreOntologies（v2.2, 2026-08-14）. https://github.com/CommonCoreOntology/CommonCoreOntologies

**arXiv**

- [93] KG Benchmark for Enterprise SQL QA（data.world）, 2023. https://arxiv.org/abs/2311.07509
- [94] Ontologies to the Rescue!, 2024. https://arxiv.org/abs/2405.11706
- [95] Semantic Layers for Reliable LLM Analytics, 2026. https://arxiv.org/abs/2604.25149
- [96] GROUND, 2026. https://arxiv.org/abs/2608.26157
- [97] GATE, 2026. https://arxiv.org/abs/2606.05634
- [98] GraphRAG（Microsoft）, 2024. https://arxiv.org/abs/2404.16130
- [99] LightRAG, 2024. https://arxiv.org/abs/2410.05779
- [100] RAG vs. GraphRAG, 2025（改訂 2026-03）. https://arxiv.org/abs/2502.11371
- [101] OG-RAG, 2024. https://arxiv.org/abs/2412.15235
- [102] HippoRAG, 2024. https://arxiv.org/abs/2405.14831
- [103] Zep（Graphiti）, 2025. https://arxiv.org/abs/2501.13956
- [104] Think-on-Graph, 2023. https://arxiv.org/abs/2307.07697
- [105] Think-on-Graph 2.0, 2024. https://arxiv.org/abs/2407.10805
- [106] KG-Agent, 2024. https://arxiv.org/abs/2402.11163
- [107] SCAIR（ACL 2026 Industry）, 2026. https://arxiv.org/abs/2607.22571
- [108] SPIRES / OntoGPT, 2023. https://arxiv.org/abs/2304.02711
- [109] LLMs4OL, 2023. https://arxiv.org/abs/2307.16648
- [110] LLM とオントロジー工学（OntoChat、IDEA2 を含む 4 本の一群）, 2023. https://arxiv.org/abs/2307.16699
- [111] LLM とオントロジー工学（同上の一群）, 2024. https://arxiv.org/abs/2411.09601
- [112] LLM とオントロジー工学（同上の一群）, 2024. https://arxiv.org/abs/2408.15256
- [113] LLM とオントロジー工学（同上の一群）, 2026. https://arxiv.org/abs/2604.01344
- [114] ARMS: ontology 制約エージェント, 2026. https://arxiv.org/abs/2604.08552
- [115] G-SPEC, 2025. https://arxiv.org/abs/2512.20275
- [116] PolicyKG, 2026. https://arxiv.org/abs/2608.09028
- [117] NL2SHACL-Bench, 2026. https://arxiv.org/abs/2608.07530
- [118] xpSHACL, 2025. https://arxiv.org/abs/2507.08432
- [119] Spider 2.0, 2024. https://arxiv.org/abs/2411.07763

**再検証（2026-10-02）で追加**

- [120] Palantir Newsroom, Palantir Announces Expansion of Federal Cloud Service with DoD IL6, 2022-10-10. https://www.palantir.com/newsroom/press-releases/palantir-announces-expansion-of-federal-cloud-service-with-dod-il6/
- [121] Palantir, Impact: Tampa General Hospital, 2026-10-02 参照. https://www.palantir.com/impact/tampa-general-hospital/
- [122] EFF (Josh Richman), Report: ICE Using Palantir Tool That Feeds On Medicaid Data, 2026-01-15. https://www.eff.org/deeplinks/2026/01/report-ice-using-palantir-tool-feeds-medicaid-data
- [123] USAspending.gov, Award 70CTD022FR0000170（ICE, Palantir Technologies Inc., Investigative Case Management）, transactions API で 2026-10-02 取得. https://www.usaspending.gov/award/CONT_AWD_70CTD022FR0000170_7012_GS35F0086U_4730
- [124] Palantir Technologies Inc., Form 10-K for FY2025, 2026-02-17. https://www.sec.gov/Archives/edgar/data/1321655/000132165526000011/pltr-20251231.htm
- [125] ISO, ISO/IEC 21838-2:2021（ISO Open Data deliverables metadata, 2026-09-30 版で確認）. https://www.iso.org/standard/74572.html ／ https://isopublicstorageprod.blob.core.windows.net/opendata/_latest/iso_deliverables_metadata/json/iso_deliverables_metadata.jsonl
- [126] Timbr, Intro to Timbr, 2026-10-02 参照. https://docs.timbr.ai/doc/docs/getting-started/intro-timbr
- [127] Timbr, MCP overview, 2026-10-02 参照. https://docs.timbr.ai/doc/docs/integration/mcp/overview
- [128] TopQuadrant, TopBraid EDG, 2026-10-02 参照. https://www.topquadrant.com/topbraid-edg/
- [129] Snowflake, Release note: Semantic views (Preview), 2025-04-17. https://docs.snowflake.com/en/release-notes/2025/other/2025-04-17-semantic-views
- [130] Snowflake, 9.25 Release notes（Aug 25–28, 2025: Querying semantic views GA）. https://docs.snowflake.com/en/release-notes/2025/9_25 ／ Snowsight での作成・管理 GA（2025-10-02）: https://docs.snowflake.com/en/release-notes/2025/other/2025-10-02-semantic-views-in-snowsight
- [131] Databricks, Release notes May 2025（Metric views are in Public Preview, 2025-05-29）／ June 2026 ／ September 2026. https://docs.databricks.com/aws/en/release-notes/product/2025/may ／ https://docs.databricks.com/aws/en/release-notes/product/2026/june ／ https://docs.databricks.com/aws/en/release-notes/product/2026/september
- [132] Microsoft, Ignite 2025 Book of News, 2025-11-18. https://news.microsoft.com/ignite-2025-book-of-news/
- [133] kumo-ai, kumo-relational-client（NVIDIA Kumo Relational Client）, GitHub, 2026-08-12 作成. https://github.com/kumo-ai/kumo-relational-client
- [134] SAP News, SAP Supercharges Copilot Joule with Collaborative Capabilities to Ignite Enterprise AI Revolution, 2024-10-08. https://news.sap.com/2024/10/sap-teched-copilot-joule-collaborative-capabilities-enterprise-ai/
- [135] SAP News, SAP Reimagines How Enterprises Run With Business AI, 2025-05-20. https://news.sap.com/2025/05/sap-business-ai-reimagine-how-enterprises-run/
- [136] Neo4j, Neo4j Invests $100M in GenAI, Launches New Agentic AI Offerings, 2025-10-02. https://neo4j.com/press-releases/neo4j-100m-genai-investment/
