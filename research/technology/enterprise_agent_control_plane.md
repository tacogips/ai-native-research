---
title: "自律エージェントのエンタープライズ制御面: 主要ベンダー、OSS 部品、OSS/SaaS エージェントの包み方、本番事例"
author: claude
kind: survey
subject: エージェント制御面、エージェント ID、委任認可、ツールゲートウェイ、PDP、サンドボックス、egress 制御、credential brokering、監査、レジストリ、kill switch、HITL、Hermes、OpenClaw、OpenAI dots、本番事例
status: idea
maturity: validated
created: 2026-10-02
updated: 2026-10-02
verified: 2026-10-02
tags: [技術, 自律エージェント, コントロールプレーン, エンタープライズ, ガバナンス, AWS, Microsoft, Google, Anthropic, Salesforce, OpenAI, MCP, サンドボックス, 監査, Hermes, OpenClaw]
relates_to:
  - research/technology/hermes_openai_dots_enterprise.md
  - research/technology/agent_sandbox_isolation_confidential_computing.md
  - research/technology/autonomous_agent_risks_papers_incidents.md
  - research/technology/ontology_palantir_kinetic_layer.md
  - research/technology/ai_os_agent_os.md
summary: 2026 年秋、主要ベンダーのエージェント制御面は「専用 ID・委任認可と credential 隔離・ツールゲートウェイを強制点とするポリシー・実行サンドボックス・監査・レジストリ」に収束した。Hermes / OpenClaw は単一信頼境界であり、外部 sandbox・default-deny egress・credential 注入・ゲートウェイ + PDP・承認キュー・監査で外側から包むことを推奨する。dots 型 SaaS は vendor の admin / compliance API と CASB / SASE 等に統制が限られるため、能力トグルの最小化と compliance API による事後監査を組み合わせる。
---

# 自律エージェントのエンタープライズ制御面: 主要ベンダー、OSS 部品、OSS/SaaS エージェントの包み方、本番事例

[専門用語の日本語説明](../glossary_ja.md)。製品名・論文の原題・コードは原表記を保持する。

既存調査（`information_flow_control_and_exfiltration.md`、長期メモリ調査、`authorization_zanzibar_openfga_cedar.md`、`isolation_durable_execution_prompt_injection.md`。いずれも ai-native-company リポジトリ）で扱った IFC / CaMeL / FIDES、memory、Zanzibar / OpenFGA / Cedar の説明は繰り返さず、関係する箇所の接続だけを示す。本稿は、自律エージェントをエンタープライズで運用するための「制御面（コントロールプレーン）」について、hyperscaler / 主要ベンダーの到達点（2026-10-02 時点）、中立な OSS 部品、self-hosted OSS エージェント（Hermes / OpenClaw）と SaaS エージェント（dots 型）の統治パターン、本番運用事例を整理する。

主要な事実は vendor の一次資料（docs、公式ブログ、プレスリリース）で確認した。二次情報は「二次」、裏付けが取れなかったものは「未検証」と明記する。調査途中でセッション全体の WebSearch 上限（200 回）に達し、以降は WebFetch で一次資料を直接読み、一部は subagent 2 体に分担させた。Hermes / dots 単体の適用性は `hermes_openai_dots_enterprise.md`、隔離・機密計算は `agent_sandbox_isolation_confidential_computing.md`、リスク・インシデントは `autonomous_agent_risks_papers_incidents.md`、AI OS と標準は `ai_os_agent_os.md`、オントロジー（Palantir）は `ontology_palantir_kinetic_layer.md` を参照。

## 1. 要約(推奨)

1. **主要ベンダーの制御面は同じ構成に収束している。これを自社制御面の参照モデルにする。** 構成要素は、エージェント専用 ID（Entra Agent ID [14][16]、Google Agent Identity（SPIFFE）[29][30]、AgentCore Identity [6][7]）、委任認可と credential 隔離（OBO、token vault、credential proxy [6][15][37]）、ツールゲートウェイ（MCP / A2A）を強制点にしたポリシー（AgentCore Gateway + Cedar / Dogwood [1][3][4]、Google Agent Gateway + IAM [28]）、実行サンドボックス（microVM / gVisor [6][32][34]）、監査（OTel、Compliance API、統合監査ログ [10][18][39]）、レジストリとシャドーエージェント検出（Agent 365、Google Agent Registry、MuleSoft Agent Fabric [11][31][47]）である。
2. **Hermes / OpenClaw は「単一の信頼境界」として扱い、外側から包む。** 単体の安全機構（承認モード、hard blocklist、container backend、skill / memory 書き込みの承認ゲート、pre_tool_call hook）は充実してきた [58][60][61][62]。しかし OpenClaw は「hostile multi-tenant boundary ではない」と明言し [68]、NVIDIA NemoClaw も RBAC、SSO、テナント隔離、予算上限、SIEM の一括出力を対象外とする [75]。外部 sandbox、egress proxy、credential 注入、ツールゲートウェイ + PDP、承認キュー、監査が必須である。
3. **egress は default-deny、credential は sandbox の外の proxy が宛先ごとに注入する。** 許可宛先はモデル endpoint（自社 gateway のみ）とツールゲートウェイだけにし、宛先追加は承認キュー経由にする（OpenShell 方式）[34][75][76][91]。credential 注入は Claude Managed Agents [38]、Docker Sandboxes [79]、E2B [93]、AgentCore Gateway [8] に共通する形である。
4. **HITL と予算上限は PDP 側で宣言し、承認待ちは durable execution に置く。** Hermes の `pre_tool_call` → 外部 PDP → Temporal の signal 待ち → AgentCore Dogwood の `formerly within ... Approve` 方式で承認イベントを時相条件として検証する（設計）[4][62][98]。無人文脈（cron、webhook）は既定 deny にする [58]。
5. **テナント（信頼ドメイン）ごとにプロセス、sandbox、credential、memory store を分ける。** Hermes の profile は同一 OS ユーザー内の論理分離にすぎず [63]、OpenClaw も単一信頼境界である [68]。これが一次資料と整合する唯一の方法である。
6. **kill switch は層ごとに持つ。** ID（Entra blueprint の無効化 [16]、Okta Agent Gateway の token 失効（二次 [138]））、ネットワーク（egress proxy の遮断）、ハードウェア（NVIDIA Sentry [77]）、端末（Defender / Intune [21][23]）。JPMorganChase は「agents can be constrained or stopped」を要件化している [157]。
7. **自己改変（skill / memory）は staged write をレビューする変更管理に載せる。** `skills.write_approval` / `memory.write_approval` で staging させ [60][61]、staging 先を Git リポジトリにして CI で SkillSpector / ClawScan 系スキャン [73] と diff レビューを通してから配布する（設計）。ベンダー側の部品として、OpenClaw の Skill Workshop（提案を `PROPOSAL.md` として人間がレビュー、2026-06-03）[170] と Hermes の profile distribution（skill・config・cron を git リポジトリで配布）[169] はある。しかし Git PR レビューを企業で運用している公開事例は、再調査でも見つからなかった（未検証）。
8. **dots 型 SaaS は「能力トグル最小化 + compliance API による事後監査 + inline 差し込み口」で統治する。** dots の能力トグル [48]、Cowork の「Always allow」禁止と内蔵ブラウザの明示無効化 [41]、Anthropic Inference hooks [40] を使い、差し込み口がなければ SASE / CASB / ブラウザで横取りする。ただし dots では「Enterprise model controls は適用されない」[48]。Compliance Platform のヘルプ記事にも dots の管理・FAQ 記事にも dots のカバー範囲の記述はなく、適用は未検証のままである [53][48][164]。また dot の cloud computer はメンバーの VPN / ブラウザ / デバイスポリシーを継承しない [48]。
9. **AI-only company の統制は 3 層で設計する。** BNY は 134 の digital employees に persona、credentials、人間の supervisor を付けて本番運用している [142]。必要なのは (1) identity ライフサイクル（sponsor 割り当て、blueprint 単位 kill switch）、(2) 実行時の決定論的ポリシー（gateway に置いた PDP、時相付きポリシー）、(3) 自己改変の変更管理（skill / memory の staged write を review）である。最も直接参考になる型は Ramp の「agent ID × owner × 予算 × 承認者 × 加盟店制限」[148] と BNY の「digital employee × credential × supervisor」[142] である。

## 2. 主要ベンダーのエージェント runtime とガバナンス

### 2.1 AWS Bedrock AgentCore

| 領域 | 内容 | 出典 |
|---|---|---|
| Runtime | 各ユーザーセッションを専用 microVM で動かし CPU / メモリ / FS を隔離。終了時に microVM を破棄しメモリを消去。最長 microVM で 8 時間、Instances で 14 日 | [6][7] |
| コーディングエージェント | Claude Code、Codex CLI、Kiro CLI、Cursor CLI を各 Firecracker microVM で動かす構成を公開（2026-06-08）。credential は Secrets Manager / Token Vault に置き microVM に入れない。VPC 内、egress は allowlist + NAT。`/mnt/workspace` は 14 日保持。Hermes / OpenClaw の公式事例は見つからず | [9] |
| Identity | inbound は Cognito、Entra ID、Okta。outbound は OAuth 2LO（client credentials）/ 3LO（authorization code）。token vault で第三者 token / API key を KMS 暗号化保持。SRA は「ユーザー → エージェント」「エージェント → ツール」「ツール → 下流」の 3 認証点の分離を推奨 | [6][7] |
| Gateway | API、Lambda、OpenAPI、Smithy を MCP ツールに変換。A2A passthrough とモデルルーティング。ツールごとの credential 注入（Secure Credential Exchange）、semantic tool search | [8] |
| Observability | OTel 互換。ADOT 経由で AWS 外（オンプレ、GCP、Azure）のエージェントのテレメトリも集約（2026-08-13）。自前ホストの Hermes の OTel 出力先候補 | [10] |

**Policy（GA 2026-03-03、13 リージョン）[1]**
- Gateway が全ツール呼び出しを横取りし、エージェントコードの外で Cedar ポリシーを評価する。既定は deny [1][2][3]。
- Cedar スキーマは MCP ツール記述から自動生成。principal の属性は LLM 出力ではなく JWT クレームから取る。
- 自然言語で書いたポリシーは Cedar に変換され、automated reasoning で過剰許可・過剰制限・充足不能な条件を検出する [2][3]。

**Temporal policies（Dogwood）**
- Cedar と互換の OSS 言語 Dogwood で、セッション内の行動履歴に基づく許可・拒否を書ける [4][5]。演算子は `formerly within`、`since within`、`count`、`sum` など。例: 「1 時間以内に同じ銘柄・株数の ApproveSale が承認済みなら SellShares を許可」。
- 承認後にのみ実行、回数制限、累計予算上限をポリシーとして宣言できる。`LOG_ONLY` から `ENFORCE` へ段階移行できる [4]。
- 制約 [4]: 1 engine あたり 20 ポリシー、時間窓は最大 24 時間。セッション ID は呼び出し側が生成するため、回数制限は「セッション内」に限られ、新セッションで数え直しになると明記。アカウント / リージョンをまたぐ伝播は不可。
- HITL と予算上限を PDP 側で表現できる、珍しい一次実装である。

**SRA の推奨統制（Capability 5）[6]**: Memory の namespace 分離（session / actor / strategy）、session ID / actor ID の利用者による改ざん防止（memory poisoning 対策）、KMS CMK、VPC endpoint、WAF、VPC Flow Logs、CloudTrail、破壊的操作への HITL、Bedrock Guardrails、ログアーカイブアカウントへの集約。

**HITL**: FAQ に明示的な HITL 機能の記載はない [7]。現状は temporal policy の「承認イベント必須」で代替するのが一次資料上の手段である [4]。

### 2.2 Microsoft（Agent 365 / Entra Agent ID / Purview / Defender / Foundry）

**Agent 365（GA 2026-05-01、$15/user/月、M365 E7 に同梱）[11][12]**

| 機能 | 内容 | 出典 |
|---|---|---|
| レジストリ | 組織内の全エージェントの system of record。Entra Agent ID を持つもの、Teams / Agent Store のもの、Defender / Intune が検出したシャドーエージェントを含む。Entra 管理センターの Agent registry / Agent collections ブレードは 2026-05-01 に廃止され Agent 365 に統合（Entra の What's new、2026-03 の Plan for change で一次確認）。Entra は Agent ID として ID 基盤を担い続ける | [11][13][24][160] |
| Registry Sync（preview） | GA 告知（2026-05-01）は AWS Bedrock と Google Cloud の 2 つのみ。自動検出と棚卸しに加え、start / stop / delete などの基本的なライフサイクル操作は「soon」としている。May 2026 の更新記事は初期 preview を AWS と Google Cloud とし、注記で「Salesforce Agentforce and Databricks Genie are supported as of May 20th, 2026」と明記（一次確認済み） | [11][13] |
| ライフサイクル操作 | install / publish / block / delete、公開前の管理者承認ワークフロー、オーナー不在エージェントの自動再割り当て、MCP サーバーへのアクセス制御（Tools Management） | [13] |
| セキュリティ | Conditional Access（delegated は GA、エージェント自身のアクセスは preview）、Identity Protection、Agent Security Posture Management（preview）、SASE for Agents（prompt injection 防御、URL filtering） | [13] |
| Windows 365 for Agents | ポリシー管理された Cloud PC をエージェントの実行環境にする（preview、米国のみ） | [11] |

**Entra Agent ID（GA 2026-04。Microsoft Learn の Entra「What's new」April 2026 に「General Availability - Microsoft Entra Agent ID platform」として掲載 [160]）**
- GA の範囲は「OAuth 2.0、MCP、A2A などの標準プロトコルでエージェント ID を作成・管理する ID / 認可フレームワーク」である [160]。
- 2026-05 には sponsor のライフサイクル管理（Lifecycle Workflows）が GA になった。sponsor が退職すると、sponsorship はその manager に自動で移る。これにより、エージェント ID には常に責任を負う人間が付く [160]。
- 構造は blueprint、agent identity、agent user の 3 層 [14][17]。
  - **autonomous**: blueprint token（FIC / managed identity を推奨、client secret は本番で非推奨）→ agent identity token → app 権限、と交換 [14]。
  - **OBO**: クライアントから受け取ったユーザー token を交換。blueprint は自分で `/authorize` を開始できない [15]。
  - **agent user**: mailbox や Teams などユーザーオブジェクトが必要な資源のための credential を持たないアカウント。agent identity と 1 対 1、`user_fic` grant で取得 [14]。
- **Best practices [16]**: インスタンスごとに固有 ID、sponsor と owner を必須化。「**blueprint を無効化すると、その全 agent identity が即時ブロックされる＝迅速な kill switch**」と明記。エージェント専用 Conditional Access（MFA は満たせないため別ポリシー）、高リスク判定エージェントの自動ブロック。6〜12 か月ごとに sponsor がアクセスレビュー。access package で期限付き・承認付きの権限付与、blueprint 設定は IaC 管理。
- **Foundry**: プロジェクトごとに blueprint と共有 agent identity を自動作成し、publish 時に専用 ID を作る。ツール呼び出し時に audience を絞った token に交換し MCP / A2A へ渡す（認証方式 `AgenticIdentityToken`）[17]。共有プロジェクト ID は影響範囲が大きいと明記 [17]。

**Purview（Agent 365 対応）[18]**
- エージェントインスタンスを「ユーザーと同様に」監査、DLP、IRM、Communication Compliance、eDiscovery、保持ポリシーの対象にできる。監査は agent-to-human、human-to-agent、agent-to-tools、agent-to-agent の全方向。
- 制約（IFC の観点で重要）: DLP の対象は Teams、OneDrive / SharePoint、メールでの agent-human 間。エージェントは block されたことを認識しないためオーナーの監視が必要。**Agent 365 が新規作成したコンテンツは元データの sensitivity label を継承しない**。label の伝播（taint）は自前で補う必要がある。
- **Build 2026 の発表（2026-06-02、本文を一次確認）[19]**:
  - **Foundry**: prompt 処理に対する Purview DLP の runtime 制御が Public Preview。Sensitive Information Types をリアルタイムに検出し、顧客 PII などを含む prompt をモデル処理前に block できる。Foundry Control Plane に埋め込まれた Purview insights は GA。
  - **ローカルエージェント**: GitHub Copilot CLI、Claude Code、OpenAI Codex、**OpenClaw** に Purview を拡張（Public Preview）。内容は DSPM による可視化、prompt とツール呼び出しをリアルタイム検査する DLP、IRM による危険な振る舞いの検知、prompt・応答・データアクセス・行動の監査ログである。Hermes は名前が挙がっていない。
  - **その他**: GitHub Copilot の監査ログを Purview に流す統合（Public Preview、Entra SSO の GitHub Enterprise が対象）。Microsoft 以外の基盤で作ったエージェントの prompt / 応答を DLP で評価できる Purview SDK for .NET（Public Preview、「within the next month」に提供予定）。

**Defender**
- Copilot Studio エージェントのツール呼び出しをリアルタイムに検査し、XPIA（cross-prompt injection）などを block [20]。
- **ローカルエージェント向け AI agent runtime protection（Preview、2026-09 更新）[21][22]**: agent-native event inspection は Claude Code、Codex CLI、GitHub Copilot CLI / app の hook で prompt、pre-tool、post-tool を検査。network inspection は **OpenClaw** に対応（certificate pinning と HTTP/3 は対象外）。Audit から Block へ段階導入でき、tamper protection の対象。Hermes は対応一覧にない。
- 2026-06-02 のブログ「local agents, claws and open runtimes」[23]（subagent による要約）: Intune で OpenClaw を block するか、Microsoft Execution Containers（MXC、early preview）内での実行を強制できる。エージェントごとに専用のローカル / Entra ID を割り当て、エージェントの通信にユーザーとは別の Entra ネットワークポリシーを適用する。
- AI agent inventory（AgentsInfo テーブル）[25]。2026-09 に Purview / Entra Global Secure Access の network DLP が GA し、ユーザーの代わりに動くエージェントも対象になった [26]。

### 2.3 Google（Gemini Enterprise Agent Platform、旧 Vertex AI Agent Builder / Agentspace）

**Gemini Enterprise Agent Platform（2026-04-23 発表）[27]**: Agent Identity、Agent Registry、Agent Gateway、Model Armor、Agent Runtime（数日間のワークフローに対応）、Agent Sandbox、Memory Bank、Observability、Anomaly / Threat Detection、Security Dashboard（SCC）で構成。

| 機能 | 内容 | 出典 |
|---|---|---|
| Agent Identity | SPIFFE ID（`spiffe://TRUST_DOMAIN/resources/...`）。X.509 は自動発行で有効期間 24 時間。Google API とは mTLS、gateway とは DPoP で結んだ token。Agent Runtime 向けは GA（2026-05-07 発表）、Gemini Enterprise Agent Platform 向けは Preview | [29][30] |
| Auth Manager（Preview） | 3LO OAuth を自動化し、エンドユーザーの credential をエージェントに見せずに暗号化保持 | [29][30] |
| Principal Access Boundary（Preview） | 他の権限に関係なく、そのエージェントが「絶対に触れない」資源の上限を定める | [29] |
| 監査 | 自分として動いた場合とユーザーを代行した場合の両方を監査ログに残す | [30] |
| Agent Gateway | ingress（client → agent）と egress（agent → 任意の宛先）の両方向。MCP を解析しツール単位の条件をかける。IAM の既定は全遮断で Registry 登録資源へ明示許可。Model Armor と連携 | [28] |
| Agent Registry | エージェント、MCP サーバー、ツール、skills（preview）を登録 | [31] |
| サンドボックス | Code Execution は network アクセスなし、状態保持は最大 14 日（TTL 設定可）。GKE Agent Sandbox は gVisor、warm pool、Pod snapshot、default-deny ネットワーク | [32][34] |
| 規制業種向け（2026-05-03） | VPC-SC で境界、connector が取り込む ACL でユーザー権限どおりに検索結果を絞る、会話履歴ログは 60 日保持 | [33] |

### 2.4 Anthropic

**Claude Managed Agents（public beta、2026-04-08、ヘッダー `managed-agents-2026-04-01`）[36]**
- 構成要素は Agent、Environment、Session、Events。scheduled deployments もある [36]（詳細は 2.8 節）。
- **Self-hosted sandboxes [37]**: orchestration と推論は Anthropic 側、ツール実行・FS・network egress は顧客側。worker は outbound HTTPS で作業キューを poll。worker に置くのは API key ではなく environment key。ただし「ツールの入出力は Anthropic の control plane に流れる」。session に付けた skills と memory store の内容も Anthropic 側に保存され、session ごとに sandbox へコピーされる（memory の変更は store に同期される）[37]。
- **Credential vault**: sandbox の外の credential proxy が MCP の URL と vault を照合し、サーバー側で token を注入する。sandbox からは vault の中身を列挙もできない（二次 [38]、Anthropic と NVIDIA の発表 [77] とも整合）。
- **既定値の注意**: 既定は permissive。built-in ツールは `always_allow`、networking は `unrestricted`。`limited`（domain allowlist）への切り替えと `always_ask` の利用が推奨されている（二次 [38]）。
- **データ保持（再検証で訂正）**: Managed Agents は stateful であるため **ZDR と HIPAA BAA の対象外**と明記されている [36]。「API and data retention」の feature eligibility 表では、Managed Agents の ZDR / HIPAA はいずれも「No」とされる。注記は「Applies to all Managed Agents sub-features, including Self-hosted sandboxes」である [161]。**self-hosted sandbox にしても ZDR / HIPAA の対象にはならない。** 旧版の「self-hosted のページは ZDR / HIPAA 要件を self-hosted を選ぶ理由に挙げる」は不正確だったので訂正する。self-hosted ページ自体は eligibility を [161] に委ねている [37]。overview が self-hosted の用途として挙げるのは「compliance or data-residency requirements」である [36]。session transcript は削除するまで残り、API で削除できる [36][161]。

**Claude Enterprise / Cowork**
- **Compliance API**: Activity Feed、chats、files、projects に加え、Cowork、Claude Code、Claude in Chrome などの **session transcript**（ローカルとリモートの両方）を取得できる [39]。Cowork のヘルプ記事は「Cowork sessions via Claude, Claude Desktop, and Claude Mobile are captured in the Compliance API」と明記する [41]。保持期間は次のとおり [161]。
  - Activity Feed: 6 年。
  - ローカル session transcript（Cowork / Claude Code）: 既定 6 年。組織が有限の会話保持期間を設定していればその期間。
  - リモート session（cloud の Cowork）: 6 年。ただしユーザーが先に削除した場合を除く。
  - **ZDR が有効なローカル session は取得されない。** HIPAA readiness の組織では、Cowork / Claude Code のローカル session だけを取得し、30 日保存する。
- **Inference hooks（beta、Enterprise）[40]**: 推論の前に組織の AI security server へ transcript を送り allow / deny を受け取る。Standard Webhooks の署名付き、timeout は既定 5 秒。fail-open / fail-closed、circuit breaker、shadow mode、rollout 率を設定可能。claude.ai、Cowork、Claude Code、Claude Tag（Slack）の会話を 1 つの hook で統治でき、ツール結果が戻る時点も hook される。未対応は書き換え・マスキング（allow / deny のみ）と Bedrock / Vertex 経由の利用。**SaaS エージェントに inline DLP / PDP を差し込む一次機能として重要である。**
- **Cowork の管理設定 [41]**: 組織単位で無効化可能。cloud 実行は Enterprise では既定 off。内蔵ブラウザは Enterprise では既定 off だったが、**2026-09-10 から既定 on**。「Always allow for connector tools」は既定 off で、書き込み可能な connector はタスクごとの承認を維持。code execution の egress 設定、web search の無効化、OTel 出力がある。
- **OTel [42]**: prompt、ツール / MCP 呼び出し、承認の判断などを OTLP（HTTP/JSON または protobuf）で SIEM に送れる。prompt 本文やツール引数も既定で送られるため collector 側で redaction が必要。
- **実務ガイド（二次）[43]**: Compliance API は有効化前に遡れないため展開前に有効化する。`managed-mcp.json` を MDM で配布して MCP を allowlist 化。`coworkEgressAllowedHosts` を使う。
- **監査ログ export と Cowork（一次で再確認）[163]**: 「Access audit logs」（2026-06-15 更新、Enterprise のみ）は、Owner / Primary Owner が過去 180 日分を export する仕組みである。記録イベントの一覧は、サインイン、SSO / JIT / ドメイン、招待とメンバー削除、project とそのドキュメント、file upload、conversation の作成・改名・削除、組織データ export に限られる。entity 型も account、invite、chat_project、chat_conversation、file、sso_connection だけで、**Cowork や Claude Code の session・ツール実行に相当するイベント型は無い**。chat / project の題名と内容は export されず ID のみである。CMK を使う組織は Export ボタンを使えず、監査イベントは Compliance API で取得する。したがって「監査ログ export に Cowork の活動は含まれず、Cowork は Compliance API（session transcript）と OTel で追う」という二次情報 [43] は一次資料と整合する。ただし、Cowork を除外すると明記した一次の文言はない（イベント一覧からの推論）。export のファイル形式（CSV か）も記事には明記がない。

### 2.5 Salesforce Agentforce

- **Einstein / Salesforce Trust Layer**: 第三者 LLM の zero data retention、dynamic grounding、toxicity 検出 [44]。
- **Guardian（2026-03-20）[44]**: Shield Event Monitoring でエージェントの data access、Apex、API を監査。Transaction Security Policies で異常な一括アクセスや restricted field へのアクセスを自動 block。Security Center で prompt injection の兆候を検知。
- **権限モデル**: エージェントは呼び出したユーザーの権限で動き、Data 360 の Policy-Based Governance で field / record 単位の制御をかける（二次 [45]）。
- **MuleSoft Agent Fabric [46][47]**: Agent Registry、Agent Broker、Flex Gateway による MCP / A2A のポリシー適用。2026-01-22 に Agent Scanners を追加し、Agentforce、Bedrock、Vertex 上のエージェントを自動検出して A2A agent card 形式で登録 [47]。

### 2.6 OpenAI（dots / Frontier）

**dots**: 公式紹介ページの日付は 2026-09-28 [49]、DevDay での発表は 2026-09-29 と報道 [51][52]。GPT-6 Astra で動く。dot ごとに専用の cloud computer とブラウザを持ち、Slack / Teams からも呼び出せる [51]。

**ワークスペース管理（help 20001554、subagent が proxy 経由で一次テキストを確認）[48]**
- 「Use dots」は Enterprise で既定 off で、custom role に割り当てられる。
- 「Add dots to Slack and Teams」を有効にすると、dot が自身の ID で投稿する。
- 「Allow local computer access」と「custom rules」は既定 off。custom rules で組み込みの safeguard は上書きできない。
- cloud browser use、cloud network access、cloud computer use、password manager をそれぞれ個別に制御できる。
- dot の cloud computer は**メンバーの VPN、ブラウザのログイン状態、デバイスポリシーを継承しない**。
- いずれかの role で付与されていれば使えるため、取り消すには全ての付与を外す必要がある。
- **Enterprise model controls は dots に適用されない。**

**提供範囲**: Pro と Business Premium に順次展開。Enterprise（Edu、Healthcare を含む）は、workspace admin が有効化した場合に beta として試せる。既定は off [49][177]。

**安全機構**
- 保存した credential はモデルに見せずにログインできる [51]。行動の前に auto-review が入り、proactive research は read-only [51]。
- 一次資料 [50] でも次を確認した。
  - auto-review を強制する仕組みは dot が変更できる環境の外にある。
  - 安全監視が懸念を検知すると dot の作業を一時停止して警告を出す。
  - proactive research の read-only 制約は「in code」で強制される。
- 権限変更テスト 49 件中 45 件に合格し、「overreach の傾向」が指摘されている（二次 [52]）。
- dot の memory は個別に閲覧・削除・修正できず、削除は dot ごと削除する方法しかない。dot の context は credential、画像、スクリーンショットを保持しない。dot が作ったファイル、Codex thread、会話は保存先の保持ポリシーに従う [164]（一次確認済み）。

**Compliance Platform / API**: Compliance Logs Platform は append-only で 30 日保持、eDiscovery、DLP、SIEM と連携可能 [53]。2026-03-05 に新しい conversation logs システムが出て、旧 stateful route は非推奨になった。Codex の Policies & Configurations の変更は監査ログに記録され、Compliance API で取得できる [53]。**dots がカバーされるかは未検証のまま。** 確認した資料は 3 つある。Compliance Platform 記事（r.jina.ai 経由で全文取得）には dots / agents の記載がない [53]。dots の管理記事 [48] と privacy / security FAQ [164] にも、Compliance API、監査ログ、EKM、データレジデンシーの記載がない。EKM は ChatGPT Enterprise / Edu で利用可能 [56] だが、dots への適用は未検証。

**specialist dots と Agent 365（一次確認）**: 公式紹介ページ [49] が次を明記する。specialist dots の preview では、組織が dot ごとに「own identity, credentials, and access」を設定する。また「We're also working with Microsoft to integrate specialist dots with ... Agent 365」とある。提供時期は書かれていない。

**その他**: OpenAI Frontier（2026-02-05）は AI coworker ごとに専用 ID、明示的な権限、guardrails を付与する [54]。Codex cloud は agent フェーズで internet を既定 off にし、domain と HTTP メソッドの allowlist をかける [55]。

### 2.7 ベンダー横断比較

「記載なし」は本調査の一次資料で該当機能を確認できなかったことを示す（存在しないことの確認ではない）。

| ベンダー | ID | 委任 | gateway・policy | sandbox | 監査 | registry | kill switch | HITL |
|---|---|---|---|---|---|---|---|---|
| **AWS AgentCore** | AgentCore Identity（inbound: Cognito / Entra ID / Okta）[6][7] | OAuth 2LO / 3LO、token vault（KMS 暗号化）[6][7] | Gateway が全ツール呼び出しを横取り、Cedar Policy（GA 2026-03-03、既定 deny）、Dogwood temporal policies [1][3][4][8] | セッション専用 microVM（最長 8 時間、Instances 14 日）[6][7] | OTel / ADOT（AWS 外も集約）、CloudTrail [6][10] | 記載なし | 記載なし（ID 層は外部 IdP 依存） | 明示機能なし。temporal policy の「承認イベント必須」で代替 [4][7] |
| **Microsoft** | Entra Agent ID（blueprint / agent identity / agent user）[14][17] | OBO [15]、access package（期限付き・承認付き）[16]、Foundry `AgenticIdentityToken` [17] | Conditional Access、Tools Management（MCP アクセス制御）、SASE for Agents [13] | Windows 365 for Agents（preview）[11]、MXC（early preview）[23] | Purview の全方向監査・DLP・eDiscovery [18]、Defender の AgentsInfo [25] | Agent 365 + Registry Sync（preview）[11][13] | blueprint 無効化で全 agent identity を即時ブロック [16]、Defender / Intune の block [21][23] | 公開前の管理者承認ワークフロー [13]（実行時 HITL は記載なし） |
| **Google** | Agent Identity（SPIFFE、X.509 24 時間）[29][30] | Auth Manager（3LO、Preview）、代行時の監査 [29][30] | Agent Gateway（ingress / egress、MCP 解析、IAM 既定全遮断、Model Armor）、Principal Access Boundary [28][29] | Code Execution（network なし）、GKE Agent Sandbox（gVisor、default-deny）[32][34] | 自身 / 代行の両方を監査ログ化 [30]、会話履歴 60 日 [33] | Agent Registry（skills は preview）[31] | 記載なし | 記載なし |
| **Anthropic**（Managed Agents は self-hosted も含め ZDR / HIPAA 対象外 [161]） | 記載なし（self-hosted worker は environment key）[37] | credential vault + proxy によるサーバー側 token 注入（二次 [38]） | Inference hooks（allow / deny、fail-open / closed）[40]、`managed-mcp.json` allowlist（二次 [43]） | Managed Agents の cloud / self-hosted sandboxes、networking `limited` [36][37][38] | Compliance API（session transcript）[39]、OTel [42] | 記載なし | Cowork の組織単位無効化 [41] | `always_ask` [38]、書き込み connector のタスクごと承認 [41] |
| **Salesforce** | 呼び出しユーザーの権限で動作（二次 [45]） | 同左（二次 [45]） | MuleSoft Flex Gateway の MCP / A2A ポリシー [46][47]、Transaction Security Policies [44]、Data 360 Policy-Based Governance（二次 [45]） | 記載なし | Shield Event Monitoring [44] | MuleSoft Agent Registry + Agent Scanners [47] | Transaction Security による自動 block [44] | 記載なし |
| **OpenAI** | Frontier の AI coworker ごとの専用 ID [54]、dot が自身の ID で Slack / Teams 投稿 [48] | 保存 credential をモデルに見せずにログイン [51] | 能力トグル、custom role、custom rules（Enterprise model controls は非適用）[48] | dot ごとの専用 cloud computer とブラウザ [51]、Codex cloud の internet 既定 off [55] | Compliance Logs Platform（30 日）。dots のカバーは未検証 [53] | specialist dots の Agent 365 統合を開発中（時期未公表）[49] | 「Use dots」トグル、全 role 付与の解除 [48] | 行動前の auto-review [51] |

### 2.8 常駐・定期実行エージェントの管理統制（2026-10-02 追補）

dots 型の「常駐（always-on）」エージェントは、統制上は「人間がその場にいない実行」である。比較の軸は、誰の ID で動くか、無人実行時に承認がどう扱われるか、組織管理者が止められるかの 3 つになる。

| 製品 | 実行形態 | 誰の ID で動くか | 無人実行時の承認 | 管理者の統制・停止 | 監査・可視化 | 出典 |
|---|---|---|---|---|---|---|
| **Claude Managed Agents scheduled deployments**（beta） | API で cron（POSIX、分単位、IANA timezone）を指定。組織あたり最大 1,000 deployment。15% までの jitter | API key を持つアプリ（agent / environment / vault を参照） | agent 定義の permission policy に従う（[38] の `always_ask` 等） | pause / unpause / archive。run ごとの `budget` 上限（累計ではなく run 単位）。参照先の agent・environment・vault が archive されると自動で pause / archive | deployment run 記録（成功時 session_id、失敗時 error 型）と webhook イベント | [162] |
| **Claude Code routines**（research preview） | Anthropic の cloud（または自組織の self-hosted environment）。schedule（最短 1 時間）、API（per-routine bearer token）、GitHub イベントで起動 | **作成した個人の claude.ai アカウント**。commit / PR / Slack などはその人の連携アカウントとして出る | **permission mode の選択肢がなく、承認なしで shell・skills・connector（書き込みを含む）を実行**（artifact 公開など一部を除く）。API の `text` は untrusted として包まれる | Team / Enterprise の Owner が Routines トグルで組織全体を無効化でき、無効化すると既存 routine も止まる。cloud sessions を無効化しても使えない。既定 environment の network は Trusted（allowlist） | 各 run が通常の session として残る | [173] |
| **Claude Cowork scheduled tasks** | remote 実行（PC がスリープ中でも動く）。connector と Claude アカウント上のファイルのみで、ローカルフォルダは使えない | ユーザー | 作成時に approval mode を設定（無人時の挙動の詳細は記載なし） | Enterprise では Owner が有効化した場合に beta。scheduled task 専用の管理トグルの記載はなく、Cowork 全体のトグルで制御 | Compliance API に Cowork session が入る [41][161] | [174][41] |
| **Gemini Enterprise scheduled agent executions**（Preview、2025-12-19） | Agent Designer（2026-09-03 に Workflow Builder として GA、workflow の自動スケジュール実行を含む）。毎時〜毎年 | **設定したユーザーの credential**。14 日ごとに失効し、手動で更新が必要 | 個人向けの操作（自分の予定作成、自分宛メール）は自動。**他者が関わる操作は schedule では非対応**（release note では「review と approval のため一時停止」と記載） | 組織単位のスケジュール無効化は記載なし。管理者が共有エージェントの所有権を移すと、schedule / event trigger は無効化され、新しい owner の再有効化が必要（2026-09-21） | 承認待ちを含む全 run が chat history に残る | [175][176] |
| **OpenAI dots**（Enterprise は beta） | dot ごとの専用 cloud computer で常駐。proactive research は read-only | メンバー（specialist dots は組織が専用 ID と credential を設定する preview） | auto-review と組み込みの承認・handoff ルール。custom rules（Enterprise では既定 off）で上書きできない | 「Use dots」などの workspace トグル（Enterprise は既定 off）。dot を reset すると会話・memory・scheduled task が削除される | Activity View。Compliance API のカバーは未検証 | [48][49][50][177] |

(推論) 一次資料の範囲では、組織管理者が定期実行機能そのものを一括で止められると明記しているのは Claude Code routines（Owner トグル）と OpenAI dots（Use dots トグル）である。Gemini Enterprise と Cowork の scheduled task は、利用者個人の ID と credential で動き、専用の管理トグルは記載がない。いずれも「個人の ID で無人実行される」ため、2.2 節の Entra Agent ID 型の専用 ID・sponsor モデルとは別物として扱い、connector の scope 最小化と事後監査（session transcript）で補う必要がある。

## 3. OSS / 中立なビルディングブロック

### 3.1 MCP / エージェントゲートウェイ

| 製品 | 主な統制機能 | 出典 |
|---|---|---|
| **agentgateway**（Linux Foundation に寄贈、2026 年に AAIF プロジェクト化） | MCP / A2A / LLM を 1 バイナリで扱う。JWT / OIDC、RBAC と CEL による認可、外部 authz 委譲、ツール単位の scoping、MCP guardrails（injection 検出、PII redaction）、リクエスト単位の監査、OTel、**チーム別の予算・支出上限**、virtual keys | [84][85] |
| **Docker MCP Gateway** | MCP サーバーを個別 container で隔離。`--block-network`、`--block-secrets`（既定 true）、`--verify-signatures`、`--interceptor`（before / after の任意処理）、`--log-calls`、CPU / メモリ上限 | [86] |
| **IBM ContextForge** | MCP、A2A、REST、gRPC を束ねる registry 兼 proxy。チーム RBAC、SSO / OIDC、40 以上の plugin（PII、OPA など）、OTel。v1.0.10（2026-09-07）で A2A エージェントへの Vault token 注入に対応 | [87][88] |
| **Kong AI Gateway 2.0**（GA 2026-09-01） | MCP server bundling と MCP ACL で、**権限のない呼び出し元には discovery 時点でツールを見せない**。identity を考慮した AI ポリシー、AgentCore 向け SigV4 | [89] |
| **Envoy AI Gateway → Agent Router**（AAIF） | MCP 2025-06 仕様に準拠。OAuth、ツールのルーティングとフィルタ、セッション管理 | [90] |

既存の Cedar / Zanzibar 調査との接続: ゲートウェイ自体は PEP（強制点）である。PDP は CEL（agentgateway / Envoy 系）、外部 authz、Cedar / Dogwood（AgentCore）、OPA（ContextForge plugin）から選べる [3][84][87]。Cedar は 2025-10-08 に CNCF Sandbox に採択された [106]。

### 3.2 サンドボックス

| 基盤 | 隔離方式 | egress 制御 | 出典 |
|---|---|---|---|
| Firecracker | microVM | — | [96] |
| gVisor | ユーザー空間カーネル（syscall の横取り） | — | [95] |
| Kata Containers | VM ベースの container | — | [97] |
| **kubernetes-sigs/agent-sandbox**（v1.0.2） | gVisor / Kata を RuntimeClass で選択。Sandbox、SandboxTemplate（network policy を含む）、SandboxWarmPool、SandboxClaim の CRD | template の network policy | [91] |
| GKE Agent Sandbox（managed 版） | gVisor 必須 | default-deny | [34] |
| Modal | gVisor または VM runtime | `block_network`、`outbound_cidr_allowlist`、`outbound_domain_allowlist`（beta、SNI 照合）。実行中にポリシーを変更可（experimental） | [92] |
| E2B | — | `allowInternetAccess`、IP / CIDR / domain の allow / deny、`updateNetwork()`、**ホスト単位のリクエスト変換（ヘッダー注入＝credential 注入に使える）**。TCP を先に受理してから宛先を検証する点に注意 | [93] |
| Daytona | — | `networkBlockAll`、`networkAllowList`（CIDR 最大 10）、`domainAllowList`（最大 100）、`outboundProxyUrl` | [94] |

隔離方式の詳細比較は `agent_sandbox_isolation_confidential_computing.md` を参照。

### 3.3 Durable execution（HITL と長時間実行の基盤）

- Temporal × OpenAI Agents SDK の統合は 2025-07 に preview、**2026-03-23 に GA** [98]。
- エージェント呼び出しは Activity として扱われ、障害から自動で再開する。
- 承認待ちはワークフロー状態として数日間保持でき、プロセスの再起動にも耐える（Temporal 一般の性質で、要約は二次）[98]。

### 3.4 Egress 制御

| 部品 | 内容 | 出典 |
|---|---|---|
| Stripe Smokescreen | HTTP CONNECT proxy。mTLS の証明書 ID ごとに宛先ホストの allowlist を持ち、内部 IP を拒否して SSRF を防ぐ | [99] |
| Cilium toFQDNs | DNS 名ベースで egress を制御し、L4 / L7 ルールと組み合わせられる | [100] |
| NVIDIA OpenShell | egress を既定で拒否し、未登録の宛先へのリクエストはオペレーターの承認キューに回る。承認は sandbox を作り直すとリセット。既定 allowlist に ClawHub が含まれず plugin の install が失敗する既知 issue あり | [75][76][83] |

### 3.5 Secrets / credential brokering

- **HashiCorp Vault agentic IAM（Vault Enterprise 2.1、GA 2026-09-01）[101]**: Agent Registry を備える。RFC 9396 の `authorization_details` によるリクエスト単位の評価が既定。委任 JWT について「ユーザー権限 ∩ エージェントの上限ポリシー ∩ authorization_details」の 3 者の積集合でアクセスを判定。監査ログに identity と認可のメタデータを記録。Terraform リソースがあり、Entra、Okta、Auth0 などとの連携を検証済み。
- **1Password**
  - `op run --environment` で MCP サーバーに実行時注入し、設定ファイルに secret を残さない [102]。
  - Secure Agentic Autofill は 2025-10-08 に Browserbase 経由で early access。credential をエージェントの context に入れずにログインさせる [103]。
  - **Credential Broker（2026-07-28 に closed beta から public preview、一次確認）[165]**: 対象は EPM Business 顧客全体。Workload Identity Federation を基盤にし、最初の公式統合は GitHub Actions である。GitHub が発行する署名付き OIDC token を trust policy と照合し、そのジョブに承認された credential だけを、ジョブの間だけ渡す。vault への常時アクセスは持たせない。発行のたびに repo、branch、workflow、environment、commit を監査ログに記録する。同時に custom OIDC workflows を beta で順次展開している。対象には Kubernetes service account や「AI agent framework」も含む。今後は、エージェントと承認した人間の両方に紐づけて発行を記録する、短命で scope を絞ったアクセスを目指すとしている。
  - **1Password for NVIDIA OpenShell（beta、2026-09-28）[166]**: sandbox 内のエージェントには placeholder だけを見せる。OpenShell Gateway は、**承認済みの宛先ホストへのリクエストのときだけ**実値に置き換え、TTL を過ぎると解決を止める。開発者は宛先、read / write、期限を確認してから接続を承認する。4.4 節のパターン 2 にそのまま当てはまる実装である。
- 共通パターンは「**sandbox の外の proxy が宛先 URL ごとに credential を注入する**」である。Claude Managed Agents [38]、Docker Sandboxes [79]、E2B の request transform [93]、AgentCore Gateway [8] が同じ形をとる。

### 3.6 監査テレメトリ: OpenTelemetry GenAI semantic conventions

- 管理は専用リポジトリ `semantic-conventions-genai` に移った [104]。
- エージェント用の span は `create_agent`、`invoke_agent`、`invoke_workflow`、`plan`、`execute_tool`。主な属性は `gen_ai.agent.id`、`gen_ai.conversation.id`、`gen_ai.tool.*` など。
- いずれも **stability は Development**。`gen_ai.system_instructions` などの内容取得は Opt-In [105]。
- 監査用の証跡（改ざん検知、保持）としては OTel だけでは足りない。Anthropic も OTel は監査ログの代わりにならないとしている [39][42]。

### 3.7 A2A と標準化

| 項目 | 内容 | 出典 |
|---|---|---|
| A2A | 現行最新は v1.0.0。JWS による Agent Card 署名（正規化を含む）、OAuth2 / OIDC / mTLS、認証後に拡張 card を返す仕組み。2026-04 時点で 150 以上の組織が参加 | [108][109] |
| IETF / OIDF（subagent の調査） | `draft-ietf-oauth-identity-assertion-authz-grant`（ID-JAG、Cross App Access の基礎）、`draft-ietf-wimse-aims-00`（AI Identity Management System、2026-09-15）、OpenID Foundation AI Identity Management CG | [111][112][113] |
| OWASP Top 10 for Agentic Applications 2026 | 2025-12-09 公開 | [110] |

標準化の全体像は `ai_os_agent_os.md` を参照。

## 4. Self-hosted OSS エージェント（Hermes / OpenClaw）を包むパターン

### 4.1 Hermes Agent 自身が持つ統制（一次 docs）

| 領域 | 内容 | 出典 |
|---|---|---|
| 承認 | `approvals.mode` は smart / manual / off。timeout 300 秒、時間切れは deny。cron、single-query、unattended（webhook / API）の各文脈ごとに deny / approve の既定を設定可能。`approvals.deny` で fnmatch パターンを指定でき、難読化されたシェル表記を正規化して照合し、YOLO モードより優先 | [58][59] |
| hard blocklist | `rm -rf /`、fork bomb、disk zeroing などは YOLO でも実行不可。構文解析できないコマンドは fail-closed で拒否 | [58] |
| ファイル書き込み保護 | `~/.ssh`、`~/.aws`、`~/.kube` や Hermes 自身の secret store への書き込みを常に block。`HERMES_WRITE_SAFE_ROOT` で書き込み先を限定 | [58] |
| Container backend | docker backend は全 capability を drop、no-new-privileges、PID 256、noexec の tmpfs。container backend（docker、modal、daytona、vercel_sandbox）では container 自体を境界とみなし危険コマンド検査を省く | [58] |
| credential | `terminal` / `execute_code` から KEY、TOKEN、SECRET を含む環境変数を除去。MCP subprocess には最小限の環境変数のみ。エラー出力中の token を redact | [58] |
| injection 対策 | AGENTS.md、SOUL.md などの context ファイルを system prompt に入れる前に検査。website blocklist と SSRF guard（RFC1918、metadata endpoint）。Tirith による実行前検査（既定は fail-open） | [58] |
| Skills（自己改善） | `skill_manage` で作成、patch、削除。`skills.write_approval: true` で全書き込みが `~/.hermes/pending/skills/` に staging され、`/skills pending`、`/skills diff`、`/skills approve` でレビュー。バックグラウンドの自己改善にも適用。hub からの install はスキャンされる。`guard_agent_created` は内容スキャナーであって承認ゲートではない | [60] |
| Memory | `memory.write_approval: true` で書き込み前の承認を必須化。injection / exfiltration パターン、不可視 Unicode を block。memory の完全無効化も可能 | [61] |
| Hooks | `pre_tool_call` で block、人間ゲートへの escalate、引数の書き換え。`pre_gateway_dispatch` で受信メッセージを block。post 系 hook でテレメトリ取得。**外部の PDP（Cedar / OPA）や承認キューにつなぐ公式の差し込み口** | [62] |
| Profiles | config、.env、memory、skills、セッションを `HERMES_HOME` ごとに分ける。同じ OS ユーザー内の論理分離にすぎず、テナント隔離には別プロセスと別 sandbox が必要（設計上の指摘） | [63] |
| Managed Scope（再検証で追加） | 管理者が `/etc/hermes/config.yaml` と `.env` に置いた値を、ユーザー設定とシェル環境変数より優先させる（キー単位）。例: model provider、`security.redact_secrets: true`。**強制手段はファイル権限だけ**。v1 の制約として、エージェント自身が逃れられないハード境界、macOS / Windows、署名付きファイル、MDM 配信は対象外と明記。`HERMES_MANAGED_DIR` をユーザーが設定できると無効化されるため、service unit やイメージで固定する | [167] |
| Egress credential 注入 proxy（再検証で追加） | `hermes egress` が host 側で iron-proxy（Apache-2.0）を動かし、TLS を終端して sandbox 内の不透明な proxy token を実際の API key に差し替える。`proxy.yaml` で upstream の許可ホストを列挙する。**現状は Docker backend のみ**（Modal、Daytona、SSH、Singularity は未対応）。host プロセス自身の LLM 呼び出しは対象外 | [168] |
| Profile distribution（再検証で追加） | SOUL、config、skills、cron、MCP を git リポジトリとして配布し、`hermes profile install / update` で導入・更新する。tag / branch / commit で版管理できる。docs は用途として「a team's reviewed internal agent」を挙げる。memory、session、API key は配布対象外 | [169] |
| 商用版（二次） | Hermes Business: 共有クレジット、**メンバーごとの支出上限**、共有 skill ライブラリ（2026-09-14 発表）。Hermes Enterprise: self-hosted、telemetry なしでも動作。Nous は「大企業での導入」に言及するが、社名は公表していない。SSO、IdP 連携、監査ログ、保持、SLA の詳細は未公表（AlphaSignal も調達側が確認すべき項目として列挙）。一次の portal ページは再調査時に 429（Vercel Security Checkpoint）で取得できなかった | [64][65] |
| 固有の脅威（二次） | skill marketplace のサプライチェーン、retrieved context 経由の memory injection、マルチプロバイダーの API key 漏えい、MCP サーバーの信頼境界 | [66] |

### 4.2 OpenClaw 自身の統制

- **信頼モデル**: 「gateway 1 つ＝信頼境界 1 つ」で、hostile multi-tenant は非対応。信頼レベルが混在する場合は gateway と credential を分けるよう推奨 [68]。
- **sandbox**: mode は off（既定）/ non-main / all、scope は session / agent / shared、backend は Docker、Podman、SSH、OpenShell など。docs 自身が「完全な境界ではない」と書く [69]。
- **exec approvals の auto mode（2026-05-31）**: allowlist に一致すれば実行し、外れたものは別の reviewer model に限定した情報だけを渡して判定させ、曖昧なら人間に回す [72]。
- **ClawHub の skill 審査（2026-06-01）**: 静的解析、VirusTotal、NVIDIA SkillSpector を通した後、Codex judge（ClawScan）が判定。67,453 件のスキャンで、各スキャナーの検出の重なりは最大でも 10.4% だった [73]。
- **Skill Workshop（2026-06-03）[170]**: エージェントが作成・変更した skill を、有効な `SKILL.md` ではなく `PROPOSAL.md` として起票する。人間は Board view（pending / applied / rejected / stale）と Today view（Use it / Tweak it / Skip it）でレビューし、履歴を残したまま改訂できる。Git / PR / diff ベースの仕組みではなく、管理者ロールや企業事例の記載もない。

### 4.3 包み込みの公開事例

| 事例 | 日付 | 主な統制 | 出典 |
|---|---|---|---|
| **NVIDIA NemoClaw**（OpenClaw、Hermes、Deep Agents を OpenShell で包む） | 2026-03-16 | egress を既定で拒否し、未登録の宛先はオペレーター承認キューへ。provider key は host に残し `inference.local` 経由でルーティング。blueprint でポリシーを版管理。**RBAC、SSO、マルチテナント、予算、fleet 管理、SIEM 出力は対象外**と明記 | [74][75][76] |
| **NVIDIA Open Agent Safety Platform** | 2026-09-28 | OpenShell が全行動を trace しポリシーを強制。**Sentry（BlueField-4 DPU）が帯域外で監視し、ミリ秒単位でエージェントを隔離（ハードウェアの kill switch）**。Anthropic Claude Managed Agents と統合。JPMorganChase、Citi なども参加 | [77] |
| **OpenClaw Enterprise（OCE）** | 2026-09-29 | OSS のコントロールプレーン。マルチテナント、trusted / untrusted の硬い境界、sandbox、LLM review、細粒度の権限、ライフサイクルと監査。1.0 前は pilot のみ（1.0 は 2026 年内予定）。Red Hat、NVIDIA と共同開発。**Red Hat と OpenAI の社内で pilot 中**で、OpenAI では「full access to codebases and plugins」を持つエージェントを展開している。docker-compose / Kubernetes で self-host 可能。SSO や監査保持の詳細は未公表 | [70] |
| **Microsoft Autopilot on OpenClaw** | 2026-09-25 | ポリシー適合チェック、MXC による実行制限、承認プロンプト内の credential redaction、「結果が不明なら自動再実行しない」 | [71] |
| **Cloudflare Moltworker** | 2026-01-29 | Sandbox SDK 内で実行。Zero Trust Access（JWT）で管理画面を保護。AI Gateway で key を集中管理しコストを可視化 | [78] |
| **Docker Sandboxes** | 2026-02-23（subagent の確認） | microVM、workspace のみアクセス可、deny-by-default の proxy（`--allow-host`）、**proxy による API key 注入（sandbox 内に key が存在しない）** | [79] |
| **Tailscale Aperture** | 2026-03-24 | LLM / MCP の key をエージェントのホストに置かない。リクエスト単位でツール呼び出しとコストを記録。**日次・時間単位・累計・モデル別の予算上限で超過リクエストを拒否** | [80] |
| **Vercel Sandbox** | 日付未検証 | microVM、outbound domain allowlist。Hermes にも AI Gateway / Sandbox を提供 | [81][82] |
| **hermes-enterprise（個人のデモ、Nous 非公式）** | — | DB の role 制約で、エージェントが決定や副作用を挿入できないようにする。人間の決定は単一 API と単一トランザクションに集約。エージェント間の引き継ぎは承認済みフィールドのみを凍結して渡す。provider key は呼び出しステップ内でだけ復号 | [67] |

### 4.4 パターン別の推奨実装（一次資料からの組み立て）

「設計」と書いた部分は筆者による組み合わせの提案である。

| パターン | 推奨実装 | 出典 |
|---|---|---|
| 1. Network egress allowlist | 実行環境は sandbox（agent-sandbox + gVisor / Kata、または microVM）に入れ egress は default-deny。許可宛先はモデル endpoint（自社 gateway のみ）とツールゲートウェイだけ。宛先追加は承認キュー経由（OpenShell 方式）。Hermes 自身の website blocklist / SSRF guard は二次防御にとどめる | [34][58][75][76][91] |
| 2. ツール単位の credential brokering | エージェントには「どのツールを呼ぶか」だけを決めさせ、credential は gateway / proxy が宛先ごとに注入。候補: AgentCore Identity token vault、Vault agentic IAM の 3 者積集合、Docker / E2B の proxy 注入、Kong / agentgateway の MCP OAuth、1Password for OpenShell の「承認済みホスト宛てのときだけ placeholder を実値に置換」、1Password Credential Broker の OIDC ベースのジョブ単位発行。Hermes 単体でも `hermes egress`（iron-proxy）で Docker sandbox 向けの proxy 注入ができる。Hermes の環境変数除去と MCP 環境の分離は host に key を置かない前提の補助 | [6][58][79][84][89][93][101][165][166][168] |
| 3. 承認キュー（HITL） | 3 段で組む（設計）: (1) Hermes の `pre_tool_call` から外部 PDP に問い合わせ、(2) PDP が「承認が必要」と返したら Temporal ワークフローの signal 待ち、(3) 承認イベントを PDP の時相条件で検証（AgentCore の `formerly within ... Approve` 方式）。無人の文脈（cron、webhook）は既定 deny。人間の決定は単一 API に集約 | [4][58][62][67][98] |
| 4. skill / memory 変更の Git PR レビュー | `skills.write_approval` / `memory.write_approval` で staging。staging 先（`~/.hermes/pending/skills/`、`skills.create_dir` で外部に向けられる）を Git リポジトリにし、CI で SkillSpector / ClawScan 系スキャンと diff レビューを通してからマージして配布（設計）。配布側は Hermes の profile distribution（git リポジトリ、`hermes profile update`）[169] をそのまま使える。レビュー UI の参考として OpenClaw Skill Workshop の proposal 方式がある [170]。**企業での実装事例は再調査でも見つからなかった（未検証）** | [60][61][73][169][170] |
| 5. テナント隔離 | OpenClaw も Hermes も単一信頼境界であるため、「テナント（または信頼ドメイン）ごとにプロセス、sandbox、credential、memory store を分ける」のが一次資料と整合する唯一の方法。共有 memory は外部 provider に出し ACL を付ける。AgentCore Memory の actor / session namespace の考え方も参考 | [6][63][68] |
| 6. Kill switch | 層ごとに用意: ID（Entra blueprint の無効化、Okta Agent Gateway の token 失効（二次））、ネットワーク（egress proxy の遮断）、ハードウェア（NVIDIA Sentry）、端末（Defender / Intune による block）。JPMorganChase は「agents can be constrained or stopped」を要件として明示 | [16][21][23][77][138][157] |
| 7. 予算上限 | agentgateway のチーム別支出上限、Tailscale Aperture のコスト上限、Hermes Business のメンバー別上限、AgentCore temporal policy の `sum` 集計。NemoClaw は予算を推論 provider 側の責任とする | [4][64][75][80][84] |

### 4.5 リファレンスアーキテクチャ（Hermes を AI-only company で動かす場合。設計）

```
[Human/Agent principal] --OIDC--> [Entra/Okta/Google Agent ID: blueprint+sponsor] (kill switch)
          |
[Hermes profile per trust domain] in [gVisor/Kata/microVM sandbox, default-deny egress]
   | pre_tool_call hook ──> [PDP: Cedar/Dogwood or OPA; IFC labels from CaMeL/FIDES layer]
   | LLM traffic ─────────> [AI gateway: model allowlist, budget caps, inline DLP]
   | tool traffic ────────> [MCP gateway (agentgateway/Kong/ContextForge): ACL + credential injection from Vault]
   | escalation ──────────> [Temporal approval workflow → Slack/Teams 承認 → 署名付き承認イベント]
   | skills/memory writes → [staging → Git PR → CI scan → merge → 配布]
   | OTel GenAI spans ────> [collector → SIEM / 改ざん検知ストア]   ※OTel は監査証跡の代替ではない
[Posture/discovery: Defender/Agent 365, Noma/Zenity など]
```

既存調査との接続:
- CaMeL / FIDES 型の IFC は、PDP の入力（データラベル）として gateway で強制するのが自然である。
- 既存製品のラベル伝播は不完全である。Purview は「Agent 365 が新規作成したコンテンツに label が継承されない」と明記している [18]。そのため taint は自前で持つ必要がある。

## 5. SaaS エージェント（dots 型）の統治パターン

dots 型 SaaS エージェントの統治手段は、vendor の admin / compliance API と、外側の CASB / SASE / ブラウザ / posture 製品に限られる。独立系の評価でも dots は「セキュリティチームの監査・統制経路が不明確」と指摘されている（二次）[52]。

| # | パターン | 内容 | 出典 |
|---|---|---|---|
| 1 | vendor ネイティブ統制を最大限に使う | **dots**: 能力トグル（cloud browser / network / computer use / local / custom rules）、custom role、Slack / Teams 連携の制御。**Cowork**: 「Always allow」を禁止、egress の制御、内蔵ブラウザの明示的な無効化（2026-09-10 から既定 on） | [41][48] |
| 2 | 事後の監査は compliance API | OpenAI Compliance Logs Platform（30 日保持）、Anthropic Compliance API（Cowork / Claude Code の transcript を含む）。Zscaler AI Protect は OpenAI と Anthropic の compliance API を取り込む（二次）。Lasso も Claude Compliance API と連携 | [39][53][121][130] |
| 3 | inline の統制 | vendor 側に PDP の差し込み口がある場合（Anthropic Inference hooks）はそれを使う。ない場合は SASE、CASB、ブラウザでネットワーク / ブラウザ層を横取りする（下記） | [40] |
| 4 | ブラウザ分離の限界 | dots の cloud computer はメンバーの VPN、ブラウザ、デバイスポリシーを**継承しない**。エンタープライズブラウザや endpoint 側の統制は dot の cloud 実行には届かず、届くのは SaaS 側（connector の scope、IdP の Conditional Access、SaaS 側の SSPM）だけ、という構造的制約がある（一次資料からの推論） | [48] |
| 5 | connector の scope 管理 | OAuth consent の棚卸しで検出（Okta ISPM Agent Discovery、2026-02-12、二次）。権限を最小化し、write 系 connector はタスクごとに承認させる | [41][43][137] |
| 6 | レジストリへの集約 | Agent 365 Registry Sync、MuleSoft Agent Registry、Google Agent Registry。OpenAI は公式紹介ページで、specialist dots を Agent 365 の統制に統合する作業を Microsoft と進めていると明記している（時期は未公表）。Registry Sync は 2026-05-20 から Salesforce Agentforce と Databricks Genie にも対応 | [11][13][31][47][49] |

**inline 統制の製品（パターン 3）**
- Netskope Skylight Agent Action Control（2026-09-15）: 9 つの intent カテゴリでエージェントの行動を block / alert（二次）[128]。MCP 統制は 2025-12-01 から（二次）[129]。
- Zscaler AI Broker（2026-06-09）: MCP と A2A 通信を対象にし、registry を備える（二次）[130]。
- Prisma AIRS 3.0（2026-03-23）[131]、Prisma Browser [132]。
- Island（2026-09-24、二次）[136]。
- Entra Global Secure Access の network DLP（GA 2026-09）[26]。

### 5.1 Posture / 検出・対応ベンダー（二次を含む）

| ベンダー | 状況 | 主な機能 | 出典 |
|---|---|---|---|
| Zenity | 独立。2026-08-03 に $125M 調達 | intent に基づき実行前に block。Copilot Studio、Agentforce、ChatGPT Enterprise、Claude Enterprise などに対応 | [114][115] |
| Noma | 独立 | 2026-06-02 に Agent Access Control（承認 / review / block の registry）。2026-09-28 に EDR / MDM 経由で endpoint 上のエージェントを検出（Cowork、Claude Code、Codex を含む） | [116][117] |
| Aim Security | Cato Networks が 2025-09-03 に買収 | SASE に統合 | [118] |
| Prompt Security | SentinelOne が 2025-08-05 に発表、2025-09-05 に完了（金額は二次） | OpenClaw 展開の追跡（OneClaw）、ClawSec | [119][120] |
| Lakera | Check Point が 2025-09-16 に発表 | runtime guard | [122] |
| Pangea | CrowdStrike が買収（二次） | AIDR の基盤 | [123] |
| Lasso | 独立 | discovery、AI-SPM、red team、inline 強制 | [121] |
| WitnessAI | 独立 | — | [124] |
| Operant AI | 独立 | — | [125] |
| Straiker | 独立 | エージェントの kill switch を提供 | [126] |
| Pillar | 独立 | — | [127] |
| Obsidian | 独立 | Cowork / Claude Code にネイティブ対応（二次） | [133] |
| AppOmni | 独立 | — | [134] |
| Valence | 独立 | — | [135] |

統合の動き（二次）[139][140]: Okta が Permiso、Cisco が Astrix、Palo Alto が Koi と Portkey を買収。

## 6. 本番運用の事例（2025〜2026）

| 組織 | 内容と数値 | 公表されている統制 | 出典 |
|---|---|---|---|
| **BNY** | 2025-10 に 100 超、Annual Report 2025 で **134 の digital employees**（自律的に人間と並んで働く multi-agent）。本番 AI ソリューション 160。決済処理、照合、オンボーディング、契約レビュー | digital employee ごとに persona、**credentials（ログイン ID）、人間の supervisor**。「guardrails, telemetry and approvals」付きで deploy。法務、プライバシー、InfoSec、リスク部門による合同ガバナンス | [141][142] |
| **Ramp** | Policy Agent（GA 2026-01-13）: ポリシー適用の精度 99%、規程外支出の検出 15 倍、人間に回すのは 10〜15%、1,000 超の財務チームが利用。Accounting Agent（2026-02-12）: 「ready to sync」の精度 98% | 規程内かつ閾値未満のときだけ自動承認。人間への escalate と override。agent ごとに永続 ID、owner、予算、承認者、加盟店制限（例: 「$500 超は承認必須」）。全行動を記録 | [146][147][148][158][159] |
| **Salesforce（Customer Zero）** | help.salesforce.com で 430 万件を処理、70% を人間なしで解決（目標 80%） | 人間のベースラインに対し 70% の精度を満たしてから全体展開。ring 方式の段階展開。全コンテキストを付けて人間へ escalate | [149][150] |
| **Morningstar**（AgentCore、2026-09-28） | アドバイザー向けの夜間準備（格付けやニュースと保有銘柄の照合、ブリーフ作成）。定量値は「毎朝数時間」のみ | JWT / OIDC、Bedrock Guardrails、raw メッセージは保存せず SHA-256 化、アドバイザーごとに microVM、VPC、LangSmith による trace。最終判断は人間 | [152] |
| **Brex**（Claude on Bedrock） | 経費取引の 75% を自動化、準拠率 94%（ページ内に 60% と 73,600 時間という矛盾する数値もある） | AWS IAM、既存の AWS 境界内で処理 | [145] |
| **Goldman Sachs**（Devin） | 「当初は数百、将来は数千」（目標値）。2025-07 | 人間が監督。ID や sandbox の詳細は未検証 | [143] |
| **NBIM**（Claude） | 週 20% 超の時間削減（社内調査）、2 か月で 600 人超が利用 | モデル選定時の HITL 評価、人間中心の判断 | [144] |
| **A&O Shearman × Harvey**（2025-04-06） | 独禁法、ファンド組成、ローン審査の multi-step エージェント。定量値なし | 「transparency and oversight」（詳細は未検証） | [153] |
| **Thomson Reuters CoCounsel Legal**（2025-08-05） | 2 万超の法律事務所や法務部門が利用 | 調査計画の提示、引用の裏付け、設計段階からの人間監督 | [154] |
| **Klarna**（Q1 2025） | 2022 年以降に人員約 40% 減、取引あたり CS コスト 40% 減 | 統制の記載なし（未検証） | [151] |
| **OffDeal**（Claude Agent SDK） | 2 人で初年度 8 件、計 $91M の M&A | human-verified な評価のみ記載 | [156] |
| **Coinbase** | — | 「robust financial compliance guardrails」 | [155] |
| **JPMorganChase**（方針、2026-03-23） | 数値なし | 能力とリスクに比例した safeguard。「lethal trifecta」を持つエージェントには継続的な runtime 強制。改ざん検知可能な記録、説明責任のあるエージェント ID、データへのポリシーラベル、停止可能性 | [157] |
| **Morgan Stanley**（OpenAI、再検証で追加。自律エージェントではなく社内 chat assistant と会議要約） | Wealth Management の advisor teams の 98% 超が AI @ Morgan Stanley Assistant を利用。文書へのアクセス率が 20% から 80% に向上 | 展開前の evals（要約、翻訳、検索）、毎日の regression test。advisor が AI 出力を確認・修正してから確定（Debrief）。OpenAI の zero data retention | [171] |
| **Lumen**（Microsoft 365 Copilot、再検証で追加。自律エージェントではなく Copilot による営業準備の支援） | 営業 1 人あたり最大 4 時間かかっていた準備を 15 分に短縮（2024 年）。年 $50M 相当の時間削減を見込む | 統制の記載なし | [172] |
| **Citi**（再検証で調査、数値は見つからず） | citigroup.com のニュース一覧と 2026 年の perspectives（Jane Fraser）に、エージェント展開の数値はなかった | NVIDIA Open Agent Safety Platform の参加企業として名前が出る | [77] |

### 6.1 事例に共通する統制

- エージェントごとの ID と人間の supervisor / owner（BNY、Ramp）。
- 閾値に基づく自動承認と escalate（Ramp）。
- 精度ゲートを満たしてからの段階展開（Salesforce）。
- セッション単位の隔離と trace（Morningstar）。

**AI-only company で最も直接参考になる型**は、Ramp の「agent ID × owner × 予算 × 承認者 × 加盟店制限」[148] と、BNY の「digital employee × credential × supervisor」[142] である。

## 7. 未検証事項

再検証（2026-10-02）後も残った項目である。解消した項目は末尾の再検証ログを参照。

- **dots と Compliance API / EKM / データレジデンシー**: 適用は未検証。確認したのは Compliance Platform 記事（9261474 を r.jina.ai 経由で全文取得）、dots 管理記事 20001554、FAQ 20001529、Getting started 20001530 で、いずれにも dots のカバー範囲の記載はない [48][53][164][177]。発表日は、openai.com のページが 2026-09-28、報道が DevDay の 2026-09-29 で食い違う [49][51][52]。
- **Hermes Enterprise の SSO、監査、保持の仕様**: 未公表。portal.nousresearch.com/business は WebFetch でも r.jina.ai 経由でも 429（Vercel Security Checkpoint）で取得できなかった。Nous のブログ一覧と docs の llms.txt / sitemap にも Enterprise の仕様ページはない。OSS 側の docs で確認できたのは Managed Scope、egress proxy、profile distribution だけである [64][167][168][169]。
- **Git PR で skill / memory をレビューする企業事例**: 見つからない。`gh search repos`（"skills review agent"、"agent skills governance" など 6 クエリ）で出てくるのは個人や小規模のリポジトリだけだった。OpenClaw のブログ（Skill Workshop、OpenClaw Enterprise）にも Git ベースのレビューの記述はない [70][170]。
- **Hermes を企業に導入した事例**: 社名入りの事例は見つからない。Nous が「大企業での導入」に言及したという二次情報のみである [64]。
- **Citi のエージェント展開の数値**: citigroup.com のニュース一覧、perspectives、推測した AI ページ（404）を確認したが、見つからなかった。Morgan Stanley と Lumen は数値を確認できたが、自律エージェントではなく assistant / Copilot の事例である [171][172]。
- **Claude の監査ログ export の形式（CSV か）**: 一次資料に明記がない。Cowork のイベントが含まれないことはイベント一覧からの推論で、除外を明記した文言はない [163]。
- **Gemini Enterprise と Cowork scheduled task の組織単位の停止手段**: 一次資料に専用の管理トグルの記載がない [174][176]。

## 追補: 再検証ログ（2026-10-02）

WebSearch は使っていない。WebFetch、r.jina.ai、`gh api` / `gh search` で一次資料を直接取得した。

**検証済みにした項目**
- Agent 365 Registry Sync の Salesforce Agentforce / Databricks Genie 対応。May 2026 の更新記事の注記「supported as of May 20th, 2026」を一次で確認した。GA 告知（2026-05-01）は AWS Bedrock と Google Cloud のみ [11][13]。
- Entra Agent ID の GA（2026-04）。Microsoft Learn の Entra What's new で一次確認した。Agent registry ブレードの Agent 365 への統合（2026-05-01）も同ページで確認 [160]。
- Purview の Foundry 向け DLP runtime 制御（Public Preview）。[19] の本文（2026-06-02）を r.jina.ai 経由で全文取得して確認した。
- 1Password Credential Broker の public preview（2026-07-28、GitHub Actions が最初の統合）[165]。
- Cowork の session が Compliance API に入ること [41]。監査ログ export のイベント一覧に Cowork 関連のイベント型がないこと [163]。
- OpenAI が specialist dots の Agent 365 統合を Microsoft と進めていること（公式ページで確認。時期は未公表）[49]。

**訂正した項目**
- Claude Managed Agents の ZDR / HIPAA。self-hosted sandbox を含む全サブ機能が ZDR / HIPAA の対象外である [161]。旧版の「self-hosted は ZDR / HIPAA 要件のための選択肢と読める」記述を訂正した。self-hosted でもツールの入出力、skills、memory store は Anthropic 側を通る・保存される [37]。
- 監査ログの「CSV」。一次資料に形式の明記はないため、「監査ログ export」と表現を改めた [163]。

**新規追加**
- 2.8 節: 常駐・定期実行エージェントの管理統制の比較。対象は Managed Agents scheduled deployments、Claude Code routines、Cowork scheduled tasks、Gemini Enterprise scheduled executions / Workflow Builder GA、dots [162][173][174][175][176]。
- Purview のローカルエージェント対応（Copilot CLI、Claude Code、Codex、OpenClaw、Public Preview）、GitHub Copilot 監査の Purview 統合、Purview SDK for .NET [19]。
- Entra の sponsor ライフサイクル（Lifecycle Workflows、GA）[160]。
- Compliance API の保持期間（Activity Feed 6 年、session transcript 6 年、ZDR のローカル session は対象外、HIPAA 組織は 30 日）[161]。
- dots の安全機構（auto-review の強制機構は dot が変更できる環境の外、監視による一時停止）[50]。dot の memory と保持の扱い [164]。Enterprise は admin が有効化した場合の beta [177]。
- Hermes の Managed Scope、egress credential 注入 proxy（iron-proxy）、profile distribution [167][168][169]。
- OpenClaw Skill Workshop [170]。OpenClaw Enterprise の pilot 先（Red Hat、OpenAI の社内）[70]。
- 1Password for NVIDIA OpenShell（beta）[166]。
- 事例: Morgan Stanley [171]、Lumen [172]（いずれも assistant / Copilot の事例）。

**未検証のまま残った項目**
- dots と Compliance API / EKM / データレジデンシーの関係。
- Hermes Enterprise の仕様（portal が 429）。
- Hermes を企業に導入した事例。
- Git PR で skill / memory をレビューする企業事例。
- Citi のエージェント展開の数値。
- 監査ログ export の形式。
- Gemini / Cowork の scheduled task を組織単位で止める手段。

## 参考文献

**AWS**
- [1] AWS What's New, Policy in Amazon Bedrock AgentCore GA. https://aws.amazon.com/about-aws/whats-new/2026/03/policy-amazon-bedrock-agentcore-generally-available/
- [2] AWS Security Blog, Why Policy in Amazon Bedrock AgentCore chose Cedar. https://aws.amazon.com/blogs/security/why-policy-in-amazon-bedrock-agentcore-chose-cedar-for-securing-agentic-workflows/
- [3] AWS, AgentCore Developer Guide: Policy. https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html
- [4] AWS, AgentCore Developer Guide: Temporal policies. https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html
- [5] Dogwood policy language. https://dogwood-policy.github.io/dogwood/index.html
- [6] AWS Prescriptive Guidance, Security Reference Architecture for generative AI: autonomous agents. https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture-generative-ai/gen-auto-agents.html
- [7] AWS, Amazon Bedrock AgentCore FAQs. https://aws.amazon.com/bedrock/agentcore/faqs/
- [8] AWS, AgentCore Developer Guide: Gateway. https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
- [9] AWS ML Blog, Hosting coding agents on Amazon Bedrock AgentCore, 2026-06-08. https://aws.amazon.com/blogs/machine-learning/its-safe-to-close-your-laptop-now-hosting-coding-agents-on-amazon-bedrock-agentcore/
- [10] AWS ML Blog, Monitor on-premises and multi-cloud AI agents with AgentCore Observability, 2026-08-13. https://aws.amazon.com/blogs/machine-learning/monitor-on-premises-and-multi-cloud-ai-agents-with-agentcore-observability/

**Microsoft**
- [11] Microsoft Security Blog, Microsoft Agent 365 now generally available, 2026-05-01. https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/
- [12] Microsoft Learn, Microsoft Agent 365 overview. https://learn.microsoft.com/en-us/microsoft-agent-365/overview
- [13] Microsoft Tech Community, What's new in Agent 365 (May 2026). https://techcommunity.microsoft.com/blog/agent-365-blog/what%E2%80%99s-new-in-agent-365-may-2026/4516340
- [14] Microsoft Learn, Entra Agent ID: autonomous agent authentication and authorization flow. https://learn.microsoft.com/en-us/entra/agent-id/autonomous-agent-authentication-authorization-flow
- [15] Microsoft Learn, Entra Agent ID: agent on-behalf-of OAuth flow. https://learn.microsoft.com/en-us/entra/agent-id/agent-on-behalf-of-oauth-flow
- [16] Microsoft Learn, Entra Agent ID best practices. https://learn.microsoft.com/en-us/entra/agent-id/best-practices-agent-id
- [17] Microsoft Learn, Foundry agent identity concepts. https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity
- [18] Microsoft Learn, Purview for Agent 365. https://learn.microsoft.com/en-us/purview/ai-agent-365
- [19] Microsoft Tech Community, Microsoft Purview data security across AI apps and agents. https://techcommunity.microsoft.com/blog/microsoft-security-blog/microsoft-purview-enables-developers-with-strong-data-security-across-ai-apps-an/4524626
- [20] Microsoft Learn, Defender security for AI: get started. https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/get-started-defender-security-for-ai
- [21] Microsoft Learn, Defender for Endpoint AI agent runtime protection overview. https://learn.microsoft.com/en-us/defender-endpoint/ai-agent-runtime-protection-overview
- [22] Microsoft Learn, Configure AI agent runtime protection. https://learn.microsoft.com/en-us/defender-endpoint/configure-ai-agent-runtime-protection
- [23] Microsoft Tech Community, Securing the new risk surface: local agents, claws and open runtimes, 2026-06-02. https://techcommunity.microsoft.com/blog/microsoft-security-blog/securing-the-new-risk-surface-local-agents-claws-and-open-runtimes/4524602
- [24] topedia blog（二次）, Agent Registry is moving from Microsoft Entra to Agent 365. https://blog-en.topedia.com/2026/04/agent-registry-is-moving-from-microsoft-entra-to-agent-365/
- [25] Microsoft Learn, Defender for Cloud Apps AI agent inventory. https://learn.microsoft.com/en-us/defender-cloud-apps/ai-agent-inventory
- [26] Microsoft Security Blog, What's new in Microsoft Security (September 2026), 2026-09-24. https://www.microsoft.com/en-us/security/blog/2026/09/24/whats-new-in-microsoft-security-september-2026/

**Google**
- [27] Google Cloud Blog, Introducing Gemini Enterprise Agent Platform, 2026-04-23. https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform
- [28] Google Cloud Docs, Agent Gateway overview. https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview
- [29] Google Cloud Blog, What's new in IAM, security governance and runtime defense. https://cloud.google.com/blog/products/identity-security/whats-new-in-iam-security-governance-and-runtime-defense
- [30] Google Cloud Docs, Agent identity overview. https://docs.cloud.google.com/iam/docs/agent-identity-overview
- [31] Google Cloud Docs, Agent Registry. https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/agent-registry
- [32] Google Cloud Docs, Code Execution overview. https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/sandbox/code-execution-overview
- [33] Google Cloud Security Community, Architecting Gemini Enterprise for regulated industries, 2026-05-03. https://security.googlecloudcommunity.com/cloud-security-foundation-7/architecting-gemini-enterprise-for-regulated-industries-security-insights-from-next-26-7430
- [34] Google Cloud Docs, GKE Agent Sandbox. https://docs.cloud.google.com/kubernetes-engine/docs/concepts/machine-learning/agent-sandbox
- [35] SecurityBrief Australia, Google Cloud expands Gemini Enterprise agent controls. https://securitybrief.com.au/story/google-cloud-expands-gemini-enterprise-agent-controls

**Anthropic**
- [36] Anthropic, Claude Managed Agents overview. https://platform.claude.com/docs/en/managed-agents/overview
- [37] Anthropic, Managed Agents self-hosted sandboxes. https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes
- [38] Pluto Security（二次）, Securing Claude Managed Agents. https://pluto.security/blog/securing-claude-managed-agents/
- [39] Anthropic, Compliance API. https://platform.claude.com/docs/en/manage-claude/compliance-api
- [40] Anthropic, Inference hooks. https://platform.claude.com/docs/en/manage-claude/inference-hooks
- [41] Anthropic Support, Use Claude Cowork on Team and Enterprise plans. https://support.claude.com/en/articles/13455879-use-claude-cowork-on-team-and-enterprise-plans
- [42] Anthropic Support, Monitor Claude Cowork activity with OpenTelemetry. https://support.claude.com/en/articles/14477985-monitor-claude-cowork-activity-with-opentelemetry
- [43] Harmonic Security（二次）, Securing Claude Cowork: a security practitioner's guide. https://www.harmonic.security/resources/securing-claude-cowork-a-security-practitioners-guide

**Salesforce**
- [44] Salesforce Blog, Secure Agentforce with trusted services. https://www.salesforce.com/blog/secure-agentforce-with-trusted-services/
- [45] Atlan（二次）, Agentforce data governance. https://atlan.com/know/ai-agent/ai-agent-applications/agentforce-data-governance/
- [46] Salesforce News, MuleSoft Agent Fabric announcement. https://www.salesforce.com/news/stories/mulesoft-agent-fabric-announcement/
- [47] Salesforce News, MuleSoft Agent Fabric automated agent discovery. https://www.salesforce.com/news/stories/mulesoft-agent-fabric-automated-agent-discovery/

**OpenAI**
- [48] OpenAI Help, Manage dots in ChatGPT workspaces. https://help.openai.com/en/articles/20001554-manage-dots-in-chatgpt-workspaces
- [49] OpenAI, Introducing dots. https://openai.com/index/introducing-dots/
- [50] OpenAI, How we build safety, security and privacy into dots. https://openai.com/index/how-we-build-safety-security-and-privacy-into-dots/
- [51] VentureBeat, OpenAI launches dots. https://venturebeat.com/technology/openai-launches-dots-always-on-ai-agent-coworkers-and-chatgpt-space-where-they-can-collaborate-with-human-teams
- [52] BankInfoSecurity（二次）, OpenAI dots pushes always-on agents into enterprise. https://www.bankinfosecurity.com/openai-dots-pushes-always-on-agents-into-enterprise-a-32970
- [53] OpenAI Help, OpenAI Compliance Platform for Enterprise and Edu customers. https://help.openai.com/en/articles/9261474-openai-compliance-platform-for-enterprise-and-edu-customers
- [54] OpenAI, Introducing OpenAI Frontier, 2026-02-05. https://openai.com/index/introducing-openai-frontier/
- [55] OpenAI Developers, Codex cloud internet access. https://developers.openai.com/codex/cloud/internet-access
- [56] OpenAI Help, EKM technical FAQ. https://help.openai.com/en/articles/20000945-ekm-technical-faq
- [57] OpenAI, ChatGPT for your most ambitious work. https://openai.com/index/chatgpt-for-your-most-ambitious-work/

**Hermes / OpenClaw / NVIDIA ほか**
- [58] Nous Research, Hermes Agent docs: Security. https://hermes-agent.nousresearch.com/docs/user-guide/security
- [59] Nous Research, Hermes Agent docs: Secure Hermes on a work machine. https://hermes-agent.nousresearch.com/docs/guides/secure-hermes-on-a-work-machine
- [60] Nous Research, Hermes Agent docs: Skills. https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- [61] Nous Research, Hermes Agent docs: Memory. https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- [62] Nous Research, Hermes Agent docs: Hooks. https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- [63] Nous Research, Hermes Agent docs: Profiles. https://hermes-agent.nousresearch.com/docs/user-guide/profiles
- [64] AlphaSignal（二次）, Nous Research packages Hermes Agent for teams and private infrastructure. https://alphasignal.ai/news/nous-research-packages-hermes-agent-for-teams-and-private-infrastructure
- [65] Nous Research, Hermes Business portal. https://portal.nousresearch.com/business
- [66] Repello AI（二次）, Hermes Agent security. https://repello.ai/blog/hermes-agent-security
- [67] GitHub bflynn4141/hermes-enterprise（個人のデモ、Nous 非公式）. https://github.com/bflynn4141/hermes-enterprise
- [68] OpenClaw docs, Gateway security. https://docs.openclaw.ai/gateway/security
- [69] OpenClaw docs, Gateway sandboxing. https://docs.openclaw.ai/gateway/sandboxing
- [70] OpenClaw Blog, OpenClaw Enterprise, 2026-09-29. https://openclaw.ai/blog/openclaw-enterprise
- [71] OpenClaw Blog, Microsoft Autopilot on OpenClaw, 2026-09-25. https://openclaw.ai/blog/microsoft-autopilot-openclaw
- [72] OpenClaw Blog, Safer than YOLO: auto mode for exec approvals, 2026-05-31. https://openclaw.ai/blog/safer-than-yolo-auto-mode-for-exec-approvals
- [73] OpenClaw Blog, OpenClaw × NVIDIA skill security, 2026-06-01. https://openclaw.ai/blog/openclaw-nvidia-skill-security
- [74] NVIDIA Newsroom, NVIDIA announces NemoClaw, 2026-03-16. https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw
- [75] NVIDIA Docs, NemoClaw enterprise readiness. https://docs.nvidia.com/nemoclaw/user-guide/deepagents/reference/enterprise-readiness
- [76] NVIDIA Docs, NemoClaw approve network requests. https://docs.nvidia.com/nemoclaw/user-guide/deepagents/network-policy/approve-network-requests
- [77] NVIDIA Newsroom, Open Agent Safety Platform, 2026-09-28. https://nvidianews.nvidia.com/news/open-agent-safety-platform
- [78] Cloudflare Blog, Moltworker: self-hosted AI agent, 2026-01-29. https://blog.cloudflare.com/moltworker-self-hosted-ai-agent/
- [79] Docker Blog, Run OpenClaw securely in Docker Sandboxes. https://www.docker.com/blog/run-openclaw-securely-in-docker-sandboxes/
- [80] Tailscale Blog, OpenClaw × Tailscale Aperture, 2026-03-24. https://tailscale.com/blog/openclaw-tailscale-aperture-serve
- [81] Vercel KB, Running OpenClaw in Vercel Sandbox. https://vercel.com/kb/guide/running-openclaw-in-vercel-sandbox
- [82] Vercel Changelog, Vercel AI Gateway and Vercel Sandbox now available on Hermes Agent. https://vercel.com/changelog/vercel-ai-gateway-and-vercel-sandbox-now-available-on-hermes-agent
- [83] GitHub NVIDIA/NemoClaw issue #4104. https://github.com/NVIDIA/NemoClaw/issues/4104

**OSS ビルディングブロック / 標準**
- [84] agentgateway. https://agentgateway.dev/
- [85] GitHub agentgateway/agentgateway. https://github.com/agentgateway/agentgateway
- [86] Docker Docs, docker mcp gateway run. https://docs.docker.com/reference/cli/docker/mcp/gateway/run/
- [87] IBM, MCP ContextForge overview. https://ibm.github.io/mcp-context-forge/overview/
- [88] GitHub IBM/mcp-context-forge releases. https://github.com/IBM/mcp-context-forge/releases
- [89] Kong Blog, Kong AI Gateway 2.0 GA, 2026-09-01. https://konghq.com/blog/product-releases/kong-ai-gateway-2-0-ga
- [90] Agent Router Blog, MCP implementation. https://theagentrouter.ai/blog/mcp-implementation/
- [91] GitHub kubernetes-sigs/agent-sandbox. https://github.com/kubernetes-sigs/agent-sandbox
- [92] Modal Docs, Sandbox networking. https://modal.com/docs/guide/sandbox-networking
- [93] E2B Docs, Sandbox internet access. https://docs.e2b.dev/sandbox/internet-access
- [94] Daytona Docs, Network limits. https://www.daytona.io/docs/en/network-limits/
- [95] gVisor. https://gvisor.dev/
- [96] Firecracker. https://firecracker-microvm.github.io/
- [97] Kata Containers. https://katacontainers.io/
- [98] Temporal Blog, Announcing OpenAI Agents SDK integration. https://temporal.io/blog/announcing-openai-agents-sdk-integration
- [99] GitHub stripe/smokescreen. https://github.com/stripe/smokescreen
- [100] Cilium Docs, DNS-based policies. https://docs.cilium.io/en/stable/security/dns/
- [101] HashiCorp Blog, HashiCorp Vault agentic IAM is now generally available, 2026-09-01. https://www.hashicorp.com/en/blog/hashicorp-vault-agentic-iam-is-now-generally-available
- [102] 1Password Developer, Secure AI access. https://www.1password.dev/get-started/secure-ai-access
- [103] BusinessWire, 1Password and Browserbase partner to secure credential access for agentic AI automation, 2025-10-08. https://www.businesswire.com/news/home/20251008408822/en/1Password-and-Browserbase-Partner-to-Secure-Credential-Access-for-Agentic-AI-Automation
- [104] GitHub open-telemetry/semantic-conventions-genai. https://github.com/open-telemetry/semantic-conventions-genai
- [105] OpenTelemetry, GenAI agent spans. https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md
- [106] CNCF, Cedar project. https://www.cncf.io/projects/cedar/
- [107] Open Policy Agent. https://www.openpolicyagent.org/
- [108] A2A Protocol specification. https://a2a-protocol.org/latest/specification/
- [109] Google Open Source Blog, A year of open collaboration: A2A anniversary, 2026-04. https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html
- [110] OWASP GenAI, OWASP Top 10 for Agentic Applications for 2026. https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- [111] IETF, draft-ietf-oauth-identity-assertion-authz-grant. https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-assertion-authz-grant/
- [112] IETF, draft-ietf-wimse-aims. https://datatracker.ietf.org/doc/draft-ietf-wimse-aims/
- [113] OpenID Foundation, AI Identity Management Community Group. https://openid.net/cg/artificial-intelligence-identity-management-community-group/

**Posture / CASB / SASE ベンダー**
- [114] Zenity. https://zenity.io/
- [115] FinTech Global, Zenity lands $125M, 2026-08-04. https://fintech.global/2026/08/04/zenity-lands-125m-as-ai-agent-security-race-heats-up/
- [116] Help Net Security, Noma brings visibility and access governance to AI agents and MCP servers, 2026-06-02. https://www.helpnetsecurity.com/2026/06/02/noma-brings-visibility-and-access-governance-to-ai-agents-and-mcp-servers/
- [117] PR Newswire, Noma extends agent security and governance to the employee endpoint. https://www.prnewswire.com/news-releases/noma-extends-agent-security-and-governance-to-the-employee-endpoint-302890925.html
- [118] PR Newswire, Cato Networks acquires Aim Security. https://www.prnewswire.com/news-releases/cato-networks-acquires-aim-security-to-extend-sase-leadership-and-secure-enterprise-ai-transformation-302543642.html
- [119] SentinelOne Blog, SentinelOne acquires Prompt Security. https://www.sentinelone.com/blog/a-new-chapter-for-ai-and-cybersecurity-sentinelone-acquires-prompt-security/
- [120] Prompt Security. https://www.prompt.security/
- [121] Lasso Security. https://www.lasso.security/
- [122] Check Point, Check Point acquires Lakera. https://www.checkpoint.com/press-releases/check-point-acquires-lakera-to-deliver-end-to-end-ai-security-for-enterprises/
- [123] SiliconANGLE（二次）, AI detection and response emerges as security category, 2026-09-01. https://siliconangle.com/2026/09/01/ai-detection-response-emerges-security-category-falcon/
- [124] SecurityWeek, WitnessAI raises $58 million. https://www.securityweek.com/witnessai-raises-58-million-for-ai-security-platform/
- [125] GlobeNewswire, Operant AI launches Agent Protector, 2026-02-05. https://www.globenewswire.com/news-release/2026/02/05/3233044/0/en/operant-ai-launches-agent-protector-the-first-real-time-agentic-security-solution-enabling-safe-ai-agent-innovation-at-scale.html
- [126] SiliconANGLE, Straiker lands $64M, 2026-06-29. https://siliconangle.com/2026/06/29/straiker-lands-64m-defend-enterprise-ai-agents-attack/
- [127] Pillar Security. https://www.pillar.security/
- [128] VMblog（二次）, Netskope enables security teams to stop risky AI agent actions. https://vmblog.com/news/netskope-enables-security-teams-to-stop-risky-ai-agent-actions-before-they-execute/
- [129] SiliconANGLE（二次）, Netskope adds MCP security controls, 2025-12-01. https://siliconangle.com/2025/12/01/netskope-adds-mcp-security-controls-protect-enterprise-ai-agents/
- [130] SiliconANGLE（二次）, Zscaler launches AI Broker, 2026-06-09. https://siliconangle.com/2026/06/09/zscaler-launches-ai-broker-endpoint-ai-security-ai-agents/
- [131] PR Newswire, Palo Alto Networks secures agentic AI with Prisma AIRS 3.0. https://www.prnewswire.com/news-releases/palo-alto-networks-secures-agentic-ai-with-prisma-airs-3-0--302722579.html
- [132] Palo Alto Networks, Secure browser built for agentic AI. https://www.paloaltonetworks.com/company/press/2026/palo-alto-networks-unveils-the-industry-s-most-secure-browser-built-for-agentic-ai
- [133] SecurityWeek（二次）, Obsidian Security raises $85 million. https://www.securityweek.com/obsidian-security-raises-85-million-at-1-1-billion-valuation/
- [134] AppOmni. https://appomni.com/
- [135] Valence Security. https://www.valencesecurity.com/
- [136] SiliconANGLE（二次）, Island raises $400M, 2026-09-24. https://siliconangle.com/2026/09/24/enterprise-browser-developer-island-raises-400m-at-6-4b-valuation/
- [137] SiliconANGLE（二次）, Okta targets shadow AI with ISPM agent discovery, 2026-02-12. https://siliconangle.com/2026/02/12/okta-targets-shadow-ai-new-identity-security-posture-management-agent-discovery-features/
- [138] SiliconANGLE（二次）, Okta adds AI agent runtime gateway, 2026-09-22. https://siliconangle.com/2026/09/22/okta-adds-ai-agent-runtime-gateway-forms-blueprint-alliance-with-aws-and-crowdstrike/
- [139] Security Boulevard（二次）, Every identity giant just bought an AI agent company. https://securityboulevard.com/2026/10/every-identity-giant-just-bought-an-ai-agent-company-heres-what-they-know-that-you-dont/
- [140] guptadeepak.com（二次）, Agent security deals. https://guptadeepak.com/agent-security/deals/

**事例**
- [141] BNY, Unlocking potential: enterprise AI platform. https://www.bny.com/corporate/global/en/insights/unlocking-potential-enterprise-ai-platform-bny.html
- [142] BNY, Annual Report 2025. https://www.bny.com/corporate/global/en/investor-relations/annual-report-2025.html
- [143] CNBC, Goldman Sachs autonomous coder pilot, 2025-07-11. https://www.cnbc.com/2025/07/11/goldman-sachs-autonomous-coder-pilot-marks-major-ai-milestone.html
- [144] Anthropic Customers, NBIM. https://claude.com/customers/nbim
- [145] Anthropic Customers, Brex. https://claude.com/customers/brex
- [146] Ramp Blog, Ramp Policy Agent GA launch. https://ramp.com/blog/ramp-policy-agent-ga-launch
- [147] Ramp Blog, Accounting Agent launch. https://ramp.com/blog/accounting-agent-launch
- [148] Ramp, Ramp Agents. https://agents.ramp.com
- [149] Salesforce News, Agentforce help agent announcement. https://www.salesforce.com/news/stories/agentforce-help-agent-announcement/
- [150] Salesforce News, Customer Zero pilots. https://www.salesforce.com/news/stories/customer-zero-pilots/
- [151] Klarna Press, Klarna accelerates global momentum in Q1 2025. https://www.klarna.com/international/press/klarna-accelerates-global-momentum-in-q1-2025-and-unlocks-large-gains-from/
- [152] AWS Industries Blog, How Morningstar built a financial advisor AI assistant powered by Amazon Bedrock AgentCore. https://aws.amazon.com/blogs/industries/how-morningstar-built-a-financial-advisor-ai-assistant-powered-by-amazon-bedrock-agentcore/
- [153] A&O Shearman, A&O Shearman and Harvey to roll out agentic AI agents. https://www.aoshearman.com/en/news/ao-shearman-and-harvey-to-roll-out-agentic-ai-agents-targeting-complex-legal-workflows
- [154] Thomson Reuters, Thomson Reuters launches CoCounsel Legal, 2025-08. https://www.thomsonreuters.com/en/press-releases/2025/august/thomson-reuters-launches-cocounsel-legal-transforming-legal-work-with-agentic-ai-and-deep-research
- [155] Anthropic Customers, Coinbase. https://claude.com/customers/coinbase
- [156] Anthropic Customers, OffDeal. https://claude.com/customers/offdeal
- [157] JPMorganChase Technology Blog, Securing agentic AI. https://www.jpmorganchase.com/about/technology/blog/securing-agentic-ai
- [158] Ramp Blog, Ramp Agents announcement. https://ramp.com/blog/ramp-agents-announcement
- [159] Ramp Blog, Ramp AP agents announcement. https://ramp.com/blog/ramp-ap-agents-announcement

**再検証（2026-10-02）で追加**
- [160] Microsoft Learn, Microsoft Entra releases and announcements（What's new。April 2026「General Availability - Microsoft Entra Agent ID platform」、May 2026 の sponsor Lifecycle Workflows GA、March 2026「Plan for change – Agent Registry consolidation into Microsoft Agent 365」）. https://learn.microsoft.com/en-us/entra/fundamentals/whats-new
- [161] Anthropic, API and data retention（feature eligibility 表、Compliance API の保持）. https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
- [162] Anthropic, Managed Agents: Scheduled deployments. https://platform.claude.com/docs/en/managed-agents/scheduled-deployments
- [163] Anthropic Support, Access audit logs（2026-06-15 更新）. https://support.claude.com/en/articles/9970975-how-to-access-audit-logs
- [164] OpenAI Help, Dots privacy, security, and safety FAQs. https://help.openai.com/en/articles/20001529
- [165] 1Password Blog, 1Password Credential Broker is now in public preview, 2026-07-28. https://1password.com/blog/1password-credential-broker-public-preview
- [166] 1Password Blog, Secure agent access in development workflows with 1Password + NVIDIA OpenShell, 2026-09-28. https://1password.com/blog/1password-nvidia-openshell
- [167] Nous Research, Hermes Agent docs: Managed Scope. https://hermes-agent.nousresearch.com/docs/user-guide/managed-scope
- [168] Nous Research, Hermes Agent docs: Egress credential-injection proxy (iron-proxy). https://hermes-agent.nousresearch.com/docs/user-guide/egress/iron-proxy
- [169] Nous Research, Hermes Agent docs: Profile distributions. https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions
- [170] OpenClaw Blog, Skill Workshop: turn agent work into reusable skills, 2026-06-03. https://openclaw.ai/blog/openclaw-agent-skill-workshop
- [171] OpenAI, Morgan Stanley uses AI evals to shape the future of financial services. https://openai.com/index/morgan-stanley/
- [172] Microsoft Official Blog, AI-powered success—with more than 1,000 stories of customer transformation and innovation（Lumen の項、2025-07-24 更新）. https://blogs.microsoft.com/blog/2025/04/22/https-blogs-microsoft-com-blog-2024-11-12-how-real-world-businesses-are-transforming-with-ai/
- [173] Claude Code Docs, Automate work with routines. https://code.claude.com/docs/en/routines
- [174] Anthropic Support, Schedule recurring tasks in Claude Cowork. https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork
- [175] Google Cloud, Gemini Enterprise release notes（2025-12-19 の scheduled executions Preview、2026-09-03 の Workflow Builder GA、2026-09-21 の所有権移転）. https://docs.cloud.google.com/gemini/enterprise/docs/release-notes
- [176] Google Cloud, Gemini Enterprise: Schedule agent executions. https://docs.cloud.google.com/gemini/enterprise/docs/agent-designer/schedule-agent
- [177] OpenAI Help, Getting started with your dot. https://help.openai.com/en/articles/20001530
