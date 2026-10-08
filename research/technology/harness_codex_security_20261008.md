# Codexの機密情報管理と実行隔離の技術機構

確認日：2026年10月8日。公開CLI安定版 `rust-v0.161.0`、変更識別子 `979011409de0a60b52f179721948e65531d26144` を固定した。クラウド、デスクトップ、CLI、IDE、API実行環境の説明を混ぜず、コードで確認した機構と公開サービスの仕様を区別する。

Codexの強みは、操作の認可とOSが強制する実行制限を重ね、ファイル・通信・資格情報を制御できる点にある。ただし、シェルの通信を禁止しても、モデルへの文章送信、接続サービス、ブラウザーまで一括して止まるわけではない。個人情報の分類や伏字化は、モデルへの入力構築と保存処理を含めた別の制御が必要になる。

## 1. 実行前の認可と実行時の強制

| 機構 | 強制箇所 | 主な動作 | 保護の範囲と限界 |
|---|---|---|---|
| 操作承認 | `core/src/exec_policy.rs`、`tools/sandboxing.rs` | 命令を解析し、allow・prompt・forbiddenを評価。承認を操作やセッションの単位で保持 | 許可した道具の中で扱うデータの用途を自動的に正当化しない |
| 権限構成 | `PermissionProfile` と `sandboxing/src/manager.rs` | 有効な権限をコマンド変換・OSの実行部へ渡す | 設定をプロンプトで知らせるだけではなく実行経路で制限する |
| 自動承認レビュー | `core/src/guardian/` と `ext/guardian-reviewer/` | 承認対象の操作を別のモデルで審査し、ユーザーの許可と危険度を評価 | 通常の承認不要操作をすべて検査する機構ではない。審査自体もモデルを使う |
| 実行直前・直後の処理 | `hooks/src/events/` | 入力の変更、阻止、追加の文脈などを処理 | エラー時の停止はイベント・出力条件ごとに異なる |

コマンドを許可する規則は、隔離内の許可と同じではない。固定コードでは、解析したすべての命令区間が明示的に許可されると `bypass_sandbox` を立てる経路がある。広すぎる命令先頭の許可を、単なる承認画面の省略と解釈してはいけない。[固定コード exec_policy.rs](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/core/src/exec_policy.rs#L440)。

自動レビューでは、拒否を普通の隔離エラーとして扱い、別の道具で同じ操作を再試行することは認めない。公開仕様は、審査プロンプトの生成・セッション・応答解析の失敗では操作を実行せず、時間切れも実行しないと説明する。ユーザーによる明示的な一回の再許可経路は別に存在する。[Auto-review](https://learn.chatgpt.com/docs/sandboxing/auto-review#denials-and-failure-behavior)。

## 2. OSごとの隔離

### LinuxとWSL2

現行実装は `bubblewrap` を既定のファイル隔離に使用する。これはプロセスから見えるファイルシステムやプロセス・通信の名前空間を作る道具である。続いて `no_new_privs`（実行時の権限昇格を禁止する設定）と `seccomp`（システム呼出しの制限）を適用し、最後に利用者のコマンドへ切り替える。Landlockは旧方式として明示選択する経路であり、「現行LinuxはLandlockだけ」と説明するのは誤り。[起動順序の固定コード](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/linux-sandbox/src/linux_run_main.rs#L103)。

`bwrap` がPATH上になければ同梱した補助実行部を使うが、権限なしの利用者名前空間を作れるか等の条件がある。旧Landlock方式で表現できない読取り・書込みの分離規則は拒否する経路を持つ。ホストのOS中核は共有するため、小型仮想機械と同じ隔離ではない。[公式Sandbox](https://learn.chatgpt.com/docs/sandboxing)、[権限の環境差](https://learn.chatgpt.com/docs/permissions#environment-differences)。

### macOS

SeatbeltというOSの制限機構を使い、`/usr/bin/sandbox-exec` から生成した規則付きでプロセスを起動する。任意のPATH上の同名実行ファイルを選ばない。ファイル規則、通信規則、必要なシステムサービスへのアクセスを組み合わせる。子プロセスにもOSの制約が継承される。[固定コード seatbelt.rs](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/sandboxing/src/seatbelt.rs#L55)。

### Windows

`elevated` は専用の低権限利用者、ファイルのアクセス権、ファイアウォールを使う方式。`unelevated` は制限したアクセストークンによる代替方式で、通信隔離や複雑な読取り・書込みの区分に差がある。表現できない規則は拒否する。さらに固定コードにはWindows MXC用の別実装が存在するため、単に「Windows＝Restricted Token」と一括しない。[公式権限説明](https://learn.chatgpt.com/docs/permissions#environment-differences)、[Windows選択コード](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/sandboxing/src/windows.rs)、[MXC実装](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/sandboxing/src/windows_mxc.rs)。利用可能性と既定選択は配布形態・管理設定で確認する。

## 3. ファイルの読取りと書込み

`read-only` は書込みを抑える区分であり、個人情報を読めないという意味ではない。旧来の `workspace-write` も書込み先の制限が中心である。機密性のためには、現行の名前付き権限構成で読み取れる領域を狭め、秘密ファイルを明示的に拒否する。

現在の構成は、パスに対して `read`・`write`・`deny` を指定できる。同じ対象ならdenyが優先するが、より具体的な規則で狭い下位領域を再び許可することもできる。「denyは階層を問わず常に優先」と読み替えない。Linux・Windowsの再帰的な拒否パターンは、起動前に対象パスを走査する場合がある。走査深度と実行中に作られるファイルの扱いを、利用するOSの実装で確認する。[Permissions](https://learn.chatgpt.com/docs/permissions#filesystem-permissions)。

書込み可能領域の `.git`、`.agents`、`.codex` は保護対象となる。これは設定や履歴を容易に改変させないための措置であり、PIIの内容分類ではない。[保護パスの説明](https://learn.chatgpt.com/docs/agent-approvals-security#protected-paths-in-writable-roots)。

プロセス内のファイル操作も、読取り制約が必要なら実行環境の補助部へ渡す仕組みを持つ。`FileSystemSandboxContext.should_read_from_sandbox()` は全ディスクの読取りが許されているかで分岐する。CLIのシェルだけを検査して、ファイル道具の制御がないと決めつけるのも不正確。[固定コード file-system](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/file-system/src/lib.rs#L408)。

## 4. 通信制御と対象外の経路

コマンドに通信を許す設定と、代理部で通信先を制限する設定は別である。`network_access=true` で `network_proxy` を有効にしなければ、利用者のドメイン規則だけでは制限されない。代理部を有効にした場合は許可先一覧を基本とし、同じ通信先のdenyがallowに優先する。[公式通信設定](https://learn.chatgpt.com/docs/agent-approvals-security#network-isolation)。

代理部はHTTP・SOCKS等を扱い、ローカル・私有ネットワーク、Unixソケット、DNSによる名前解決の危険を別に管理する。名前解決に失敗したり私有IPへ解決されたりする場合は拒否するが、公式はDNSの付替えを完全には防げないと明記する。TCPだけを見て、UDP、DNS、ソケット、ローカル代理を無制限にしない。[通信仕様](https://learn.chatgpt.com/docs/agent-approvals-security#dns-rebinding-protections)。

**コマンドの代理部の対象外**には、モデル・認証API、ウェブ検索、アプリの接続機能、MCPサーバーへの接続、ブラウザー、Computer Use、別のクラウド実行がある。これらは別の管理設定や接続側の認可を使う。「シェルの外向き通信禁止＝個人情報が外部へ出ない」は成立しない。[対象外の公式一覧](https://learn.chatgpt.com/docs/agent-approvals-security#traffic-outside-the-command-network-proxy)。

## 5. 資格情報と環境変数

### 子プロセスへの環境変数の継承

固定版の `ShellEnvironmentPolicy` は `ignore_default_excludes=true` が既定である。したがって、名前にKEY・SECRET・TOKENを含む変数が自動的に除かれると想定してはいけない。`inherit=none` 又は `core` と明示的な許可・除外を検討する。除外の後に `set` を適用するため、設定によって除外済みの変数を戻せる。実行部の内部認証や連携認証に使う一部の変数は、別の非継承一覧で除去する。[既定値の固定コード](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/protocol/src/config_types.rs#L261)、[継承処理](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/protocol/src/shell_environment.rs#L18)、[公式環境変数設定](https://learn.chatgpt.com/docs/config-file/config-advanced#shell-environment-policy)。

### 資格情報を代理部で渡す機構

固定コードの `network-proxy/credential_broker` は、環境変数から得た秘密をダミー値へ置き換え、承認した通信先へ送るときに本物へ戻す処理を持つ。設定可能な方式にはBearer・Token・Basic・Headerがあり、URLの先頭部分で注入先を指定できる。TLSを代理部で終端する制御と連動する。設定の既定は有効ではないため、コードがあることと全利用者で動くことを区別する。[設定と既定値](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/network-proxy/src/config.rs#L159)、[注入先の構成](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/network-proxy/src/credential_broker/provider_config.rs)、[処理本体](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/network-proxy/src/credential_broker.rs)。

これは認証用の秘密値を隠す機構であり、任意の文章にある氏名・診断名を自動匿名化するものではない。また、本物の鍵を見せなくても代理部で許されたAPI操作はできる。宛先だけでなく、操作・対象資源・期間を制限する必要がある。

### ローカル保存

認証情報の保存には、ファイルとOSの資格情報保管機構などの方式がある。ファイル方式の `auth.json` は秘密をJSONで保持し、Unixでは0600で作成する。これは同じ利用者が動かす任意のコードから読めなくする暗号化保証ではない。自動選択方式の代替保存も確認する。[認証仕様](https://learn.chatgpt.com/docs/auth#credential-storage)、[保存コード](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/login/src/auth/storage.rs#L215)。

## 6. 実行前後の拡張を検査境界として使う際の条件

固定版の `PreToolUse` は、同期処理で明示された拒否や適切な終了コード2を返した場合に阻止できる。`async=true` 又は `ExecutorScoped` の処理は非同期に分類され、制御効果を適用しない。[同期条件の固定コード](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/hooks/src/engine/mod.rs#L142)。また、起動失敗、時間切れ、不正なJSON、入力の直列化失敗は、失敗記録だけを残し `should_block=false` となる経路がある。さらに終了コード2でも標準エラーに阻止理由がないと失敗扱いで進む。PII検出器が故障した場合に必ず止める保証にはならない。[固定コード pre_tool_use.rs](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/hooks/src/events/pre_tool_use.rs#L187)。

`PostToolUse` は既に実行された操作を取り消さない。固定版には `updatedMCPToolOutput` が未対応として失敗する試験があり、Claude Codeの現行の結果置換機能をそのまま移植できない。[固定コードと試験](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/hooks/src/events/post_tool_use.rs#L410)。

実行前処理だけでは、ユーザーが直接入力する文章、画像、初期指示、会話の再開や要約などを一括して匿名化できない。全体のPII送信制御は、最終的にモデルへ渡す入力の検査点と、ログを保存する前の検査点を持つ必要がある。これは既存機能の保証ではなく、本調査から導く開発要件である。

## 7. MCPとサブエージェント

MCPは道具と外部サービスをつなぐ規約である。サーバーが示す読取り・破壊的操作等の情報を承認判定に使うが、その情報の正しさと、サーバー側の本人確認・データ認可は別に検証する。コマンドの代理部による制限はMCPの通信へ自動適用されない。[MCP道具処理](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/core/src/tools/handlers/mcp.rs)、[承認の公式説明](https://learn.chatgpt.com/docs/agent-approvals-security#sandbox-and-approvals)。

子エージェントの設定は親の有効設定から作り、承認方針、権限構成、作業環境を更新する。役割の設定だけで親の境界を変更しない処理を確認した。ただし、会話の複製と共有ファイルから得るデータを案件単位で隔離する機構と同義ではない。[子設定の固定コード](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/core/src/agent/child_config.rs#L104)。

## 8. 履歴と観測情報

履歴の保存方針には、文章、道具の引数・結果、要約、エージェント間の通信等が含まれる。モデル向けの記憶に使う項目の選別も、個人情報の匿名化とは異なる。[履歴方針の固定コード](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/rollout/src/policy.rs#L10)。

`otel.log_user_prompt=false` は観測イベントのユーザープロンプト記録の設定であり、会話原本、道具出力、診断ログ、他の接続先を一括削除する設定ではない。利用者の保存期間・削除要求・復元時の認可を別に設計する。[観測の設定](https://learn.chatgpt.com/docs/config-file/config-advanced#observability-and-telemetry)。

## 9. 組織による管理とクラウド

管理者は許す承認方式、権限構成、通信、MCPや機能を上位の要求として制約できる。ローカル設定だけでは固定できない境界を管理者の要求へ移す。現行の公開説明には、OS・全OS・共通設定の優先順位と、ローカル／クラウドの適用範囲の差がある。機能ごとの上書き・併合規則を確認する。[Managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration)。

旧Codex Cloudの準備段階だけで秘密を渡す方式と、現行のクラウド環境やAgents APIの資格情報代理は別の仕組みである。自己管理の実行環境へ渡す接続専用鍵はエージェントから読めるが、アプリのAPI鍵とは分ける仕様である。これを「クラウドでは秘密が全部読めない」と一般化しない。[世代別の公式説明](https://learn.chatgpt.com/docs/agent-approvals-security#sandbox-and-approvals)、[Agents APIの隔離と資格情報](https://developers.openai.com/api/docs/guides/agents-api/environments/security)。

## 10. 個人情報用ハーネスへ取り込む条件

再利用できるのは、型付きの権限表現、実行境界での制約、OSごとの規則変換、管理者の上限規則、操作ごとの承認、資格情報代理と履歴の分離である。追加すべきなのは、モデル送信直前の検査、元データを持つ保管部と伏字の対応表の分離、案件・利用者ごとの認可、MCP・検索・画像・要約を含む情報の経路管理、検査失敗時の実行・送信停止である。

この固定版の公開コードと文書の確認は、全プラットフォームの実機試験や非公開サービスの内部監査を代替しない。Windows MXCの配布条件、クラウドの内部強制方式、全拡張の安全性、PII検出精度は公開仕様・個別環境の追加確認が必要となる。[一次資料の保存記録](harness_codex_sources_20261008.json)。
