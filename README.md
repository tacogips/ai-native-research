# ai-native-research

機密データを扱い、自律的に改善・運用する「ほぼ無人で AI のみが企業活動を行うシステム（AI-only company）」の設計に向けた調査ノート集。

## 前段の調査（ai-native-company リポジトリ, 2026-10-02）

本リポジトリの調査は、以下の既存調査を引き継ぐ。各ノートではこれらを再説明せず、差分と接続を書いている。

| 既存調査 | 要旨（推奨） |
|---|---|
| `research/technology/information_flow_control_and_exfiltration.md`（FIDES、lethal trifecta、contextual integrity） | 外部送信シンクを構造的に持たない。制御フローは Temporal Workflow で固定（CaMeL 的）、データフローは Gateway でラベル伝播とシンク検査（FIDES 的）、権限を持つ引数は出所を検査。Model Armor 等の検出器は適応的攻撃で 90% 超破られるため境界にしない。外部送信・降格・untrusted 由来の権限引数は人の承認に残す |
| 業務を長期間継続するための AI エージェントのメモリ（MemGPT 以降、Letta / Mem0 / Zep） | メモリを正本にしない（業務 DB が正）。業務記録・エピソード・手続き・人のフィードバックの 4 種を物理分離。エンティティ単位は bi-temporal。判断時の参照メモリは ID と版で固定。自己改善は人のフィードバック → 候補ルール → PR レビュー → 評価回帰 → 段階適用で、メモリへの自動書き込みは禁止 |
| `research/technology/authorization_zanzibar_openfga_cedar.md` | 二層構成: 「誰が何を見られるか」は OpenFGA（ReBAC）、「この操作をしてよいか（業務ルール）」は Cedar。判定はランタイムの認可サービス（PDP）一箇所に集約 |
| `research/technology/isolation_durable_execution_prompt_injection.md` | CaMeL の基本、Dual LLM、Rule of Two、隔離、durable execution |

## 本リポジトリの調査（2026-10-02）

| ファイル | 内容 |
|---|---|
| [research/technology/hermes_openai_dots_enterprise.md](research/technology/hermes_openai_dots_enterprise.md) | **メイン**: Hermes Agent と OpenAI dots のエンタープライズ適用性、技術的アプローチ、課題、論文・事例 |
| [research/technology/enterprise_agent_control_plane.md](research/technology/enterprise_agent_control_plane.md) | 主要ベンダーの制御面（AgentCore / Entra Agent ID・Agent 365 / Google / Anthropic / Salesforce / OpenAI）、OSS 部品、OSS・SaaS エージェントの包み方、本番事例 |
| [research/technology/autonomous_agent_risks_papers_incidents.md](research/technology/autonomous_agent_risks_papers_incidents.md) | 常駐・自己改善エージェントのリスク: 2025〜2026 の論文、実インシデント、エージェント ID 標準、規制 |
| [research/technology/agent_sandbox_isolation_confidential_computing.md](research/technology/agent_sandbox_isolation_confidential_computing.md) | サンドボックス・コンテナ・microVM、egress / 秘密情報の隔離、Confidential Computing（GPU TEE と物理攻撃）、データ保護技術 |
| [research/technology/ai_os_agent_os.md](research/technology/ai_os_agent_os.md) | AI OS / Agent OS の研究・産業動向（Windows agentic OS、dots、Muse、Managed Agents）、MCP / A2A / Skills 等の標準 |
| [research/technology/ontology_palantir_kinetic_layer.md](research/technology/ontology_palantir_kinetic_layer.md) | オントロジーの AI 適用: Palantir Ontology / AIP、セマンティックレイヤー製品、論文、標準、AI-only company への写像 |

## 横断的な結論

1. **エージェントは「信頼できない実行器」、統制は外側の制御面に置く。** Hermes は境界を OS に委ね、dots の Auto-review も決定的保証ではない。ID・PDP・IFC・監査・egress・予算・kill switch は制御面で強制する。
2. **書き込み経路を型付き Action に一本化する。** Palantir の Ontology Action（提出条件・action log・revert）の形で、Action ↔ Cedar/OpenFGA ↔ IFC ラベル ↔ 監査を 1 対 1 に写像し、エージェントには Action 由来の MCP ツールしか渡さない。
3. **永続状態への書き込み（メモリ・スキル・cron・設定）は権限昇格として扱う。** 2026 年の研究は攻撃の主戦場が入力から状態に移ったことを示し、自己進化だけで安全性が劣化する（misevolution）。staged → エージェントから見えない固定評価 → 署名昇格に限定する。
4. **隔離は microVM / gVisor が最低ライン、egress proxy やパッケージミラーも攻撃面。** 秘密情報は credential injection proxy でエージェントに見せない。TEE はクラウド運営者対策には有効だが物理攻撃は防げない。
5. **非人間 ID とスポンサー、層ごとの kill switch。** Entra Agent ID / Google Agent Identity / IETF WIMSE AIMS が整いつつある。人の承認は不可逆・外部送信・降格・権限拡大の例外処理に絞る（承認の大半はノイズ化する）。
6. **SaaS エージェント（dots 型）は機密系に直結しない。** 自社 MCP Gateway を唯一の経路にし、ベンダーの compliance API の対象範囲が確認できるまで周辺業務に限定する。

## 注記

- 調査は 2026-10-02 時点。各ノートの「未検証」は一次情報で裏付けが取れなかった項目。
- 調査途中で Web 検索のセッション上限に達したため、後半は一次資料の直接取得（WebFetch / arXiv API / GitHub API）で確認している。
- 同日に中断分の再検証を実施し、各ファイル末尾の「追補: 再検証ログ」に検証・訂正・追加・残課題を記録した。主な訂正:
  - Hermes v0.21.0 の「protected instruction files は常に承認」は、実装上はプロジェクト側の AGENTS.md 等だけが対象で、`~/.hermes` 配下の skill・memory は対象外（既定 false の `write_approval` のみ）
  - Unit 42 の Hermes + DeepSeek 悪用事例では、自律攻撃は失敗し、成功した侵入は手動
  - Claude Managed Agents は self-hosted sandbox を含め ZDR / HIPAA 対象外
  - dots はデータレジデンシー対象外（ベータ機能除外）、Business Premium は HIPAA BAA 対象外
  - Palantir MCP / Ontology MCP の GA は 2026-06-25
  - Entra Agent ID の GA は 2026-04
