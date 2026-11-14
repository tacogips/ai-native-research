# Claude Code と sandbox-runtime の機密情報・実行隔離機構

調査日: 2026-10-08。対象は個人情報を扱う独自ハーネス（モデルの周囲で入力、道具、権限、実行、記録を管理するソフトウェア）の開発。公開一次資料の仕様調査と、公開ソースの静的読解を行った。実資格情報、利用者の Claude 設定、実個人情報は使用していない。

## 結論

Claude Code は「モデルの指示」「道具の許可」「シェルのOS隔離」「拡張・管理者設定」「モデル・記録へのデータ送信」を別の層として実装している。Bash の隔離だけで個人情報の外部モデル送信を防ぐ設計にはならない。Read、WebFetch、MCP、hooks などに別の境界が必要である。

移植価値が特に高いのは、構造化された道具呼出しへの介入、拒否・確認規則を許可より優先する設計、OS によるプロセス木の隔離、外側の代理通信による認証委任である。独自の個人情報分類・置換を組み込む際は、CLI hook の障害時継続、添付ファイルの別経路、置換前の観測記録、記憶への持越しを追加で閉じる必要がある。

## 証拠の範囲と固定版

- **公開ソース確認**: `anthropics/sandbox-runtime` の調査時 main を `fedc0bbe206c2705b3de990fdbed51b3255214c9` に固定。コミット日時は 2026-10-07T23:02:18+01:00。以下のソースリンクはこの固定値を使用する。
- **公開タグ確認**: `v0.0.79` は `d9aac2098351ca17f3743fbaf6ecbd0051b7e00e`。main の `package.json` は `0.0.78` と記載しているが、README とコードに v0.0.79 後の変更がある。main と配布版は同一と扱わない。Claude Code がこの main をそのまま同梱することも確認できない。
- **公式仕様確認**: Claude Code の公式 Markdown 30ページを原本として保存。1ページは取得失敗。資料は取得日時と SHA-256（ファイル同一性を確認する要約値）で固定し、対応する Claude Code 最低版が記載されている機能ではそれを尊重する。
- **非公開部分**: Claude Code 本体の完全な現行実装、内部の分類器、管理サーバー、クラウド代理通信の実装は公開資料から検証できない。公式説明と公開 SRT のコードを混同しない。
- **実行検証の限界**: ソースと同梱テストの所在を確認したが、依存パッケージの導入・全OSの実行・隔離脱出実験・テスト一式の実行は行っていない。

原本とクローンは `research/disclosures/raw/harness_20261008/claude/` に保存。取得台帳は [harness_claude_sources_20261008.json](harness_claude_sources_20261008.json)。

## 調査対象を網羅する表

| 分野 | 確認した機構 | 強制される場所・確認限界 |
|---|---|---|
| 構造化された道具の制御 | 許可・確認・拒否、道具定義の除去、入力書換え、SDK callback | Claude Code の実行側。自然言語指示とは別 |
| プロンプト注入対策 | 作業場所への信頼、コマンド解析、別モデルの分類、ページの要約 | モデル・解析器は完全な安全境界ではない |
| 入力・出力の個人情報検査 | 入力拒否・道具結果置換の拡張点、エラー報告の既知パターン除去 | 全入力経路の汎用PII検査を標準提供する証拠は未確認 |
| モデルへの送信 | TLS、API提供者選択、代理接続、保持契約 | Bashの通信禁止では停止できない |
| ログ・記憶 | 会話JSONL、履歴、作業記憶、観測出力、保持掃除 | 個人情報検査の前後関係に注意 |
| 承認 | 複数許可モード、明示ask、管理者によるbypass禁止 | 非対話実行とSDKで動作が異なる |
| OS隔離 | macOS Seatbelt、Linux bubblewrap＋seccomp、独立SRTのWindows alpha | Claude Code組込のnative Windowsは未対応 |
| 通信 | HTTP/SOCKS代理、名前とポート、実IP検査、要求単位の検査 | 代理経路・TLS除外・許可先内部の操作が残る |
| 認証委任 | 環境変数/ファイルの拒否・ダミー置換、TLS再注入、AWS再署名 | 外側の代理が実秘密を保持。一般PII検査とは別 |
| サブエージェント | 道具集合の縮小、規則継承、専用MCP、hooks | 会話窓・作業木の分離はOS分離ではない |
| 拡張・MCP供給網 | 出所属性、信頼確認、サーバー許可台帳、配布元制限 | 名前の一致だけでは実行物の信頼を証明しない |
| 管理ポリシー | 管理者優先、allowManaged系、policyHelper、失敗時処理 | 配列統合・例外・読取失敗・最低版を確認 |

## 1. 許可規則と道具の呼出し境界

`permissions.deny` → `ask` → `allow` の優先順で、狭い許可が広い拒否の例外になることはない。裸の道具名を拒否すると、その道具をモデルに見せる定義から除く。引数に条件を付けた拒否は呼出し時に評価する。規則はモデルではなく Claude Code が適用し、`CLAUDE.md` や会話の指示は権限を変更しない。[公式 permissions](https://code.claude.com/docs/en/permissions#manage-permissions)

Read と Edit は道具群をまたぐ正規のファイル規則である。`Read` 拒否は Read に加え、対象に対する Edit/Write を止めるが NotebookEdit は別途 Edit 拒否が必要。`Write(path)` や `Glob(path)` を設定しても多くのファイル検査はその規則を参照しない。`.claudeignore` は無効。絶対パスには `//path` を用い、`/path` は設定元基準なので、sandbox側の普通の `/path` と同じ意味ではない。[ファイル規則](https://code.claude.com/docs/en/permissions#read-and-edit)

SDK の評価は hooks、deny、ask、許可モード、allow、`canUseTool` の順。`canUseTool` はすべての道具の必須検査ではなく、allowやbypassで前段承認されると到達しない。SDK は一部の場合に `CLAUDE_SDK_CAN_USE_TOOL_SHADOWED` 警告を出す。全呼出しへの検査には `PreToolUse` が必要。[SDK permissions](https://code.claude.com/docs/en/agent-sdk/permissions#how-permissions-are-evaluated)

### Bash の解析

複合コマンドを分割し、各部分を評価する。部分的な許可は残りのコマンドを承認しない。拒否・確認は入れ子の置換や制御構文にも適用する。固定された実行前置語や一定の環境変数代入を解析し、読取専用コマンドには標準の自動承認がある。解析不能な入力は Manual mode で確認する。[Bash規則](https://code.claude.com/docs/en/permissions#bash)

ただしこれは文字列と構文に対する許可処理であり、実行プログラムの安全性をOSで証明するものではない。別の実行表現や、許可されたスクリプトの内部のファイル操作までは一般に同じ規則で捕捉できない。標準で認識するファイルコマンド、リダイレクト、`tee` の検査があっても、任意の Python/Node 内部読取への全面適用とは異なる。個人情報の隔離は呼出し規則に加えてOS境界で担保する。

### 許可モード

Manual/default、acceptEdits、plan、auto、dontAsk、bypassPermissions の違いは自動承認の範囲である。bypassでも明示deny/askや重要経路の削除保護は残る。autoは別の分類モデルまたはサーバーの判定を使う。判定欠落は拒否し、分類器の連続拒否は手動承認へ戻る。非対話実行では手動応答がないため拒否が継続する。隔離したBashの自動許可は許可モードとは別の設定である。[permission modes](https://code.claude.com/docs/en/permission-modes)、[SDKの順序](https://code.claude.com/docs/en/agent-sdk/permissions)

**推論**: 分類器はデータ持出し判定の補助にはなるが、PIIの定義や組織の送信先契約を満たす決定的な検査に置き換えられない。分類器自体へのメッセージ送信もデータ経路として管理する。

## 2. hooks を使った検査・置換とその穴

`PreToolUse` は道具の生成済み構造化引数を受け、`allow/deny/ask/defer` と `updatedInput` を返す。書換えは入力オブジェクト全体を置換し、書換え後の値で許可規則を検査する。複数hooksの判断は `deny > defer > ask > allow`。モデルからの入力、MCPへの送信、ファイルへの書込みなどを実行前に検査する拡張点になる。[PreToolUse](https://code.claude.com/docs/en/hooks#pretooluse-decision-control)

`PostToolUse.updatedToolOutput` は全道具の結果をモデルへ渡す前に置換できる。従来の `updatedMCPToolOutput` はMCPに限定される。`decision:block` だけでは原結果がモデルに見える。結果置換でも既に行ったネットワーク送信やファイル書込みは取り消せず、OpenTelemetryの道具観測や分析イベントはhook前に原結果を記録する。検査器をこの段階だけに置くと、モデルは守れても観測基盤へ原PIIが残り得る。[PostToolUse](https://code.claude.com/docs/en/hooks#posttooluse-decision-control)

| 経路・失敗 | 公式の動作 | 開発上の含意（推論） |
|---|---|---|
| CLI command hook の exit 1、起動失敗、不正JSON | 多くのイベントで非阻止エラー。通常の許可処理へ進む | 検査器障害を拒否へ変換する外側の必須境界が必要 |
| exit 2 | 阻止可能イベントでは阻止。JSON allowでも上書き不可 | 検査失敗をexit 2とし、最低版を固定 |
| CLIのcommand/http/MCP hook timeout | PreToolUseでは呼出しを阻止せず通常許可処理へ | タイムアウトを安全拒否と誤解しない |
| SDK callback hook timeout | PreToolUseの道具呼出しを阻止 | CLIとの違いを受入試験にする |
| PostToolUseの置換結果が組込道具のschemaに不適合 | 置換を無視して原結果を使用。MCP結果はschema検査なし | 各道具の正しい出力構造を保持し、置換失敗を外側で送信拒否へ変換 |
| `async:true` | 既に進行済みなので判断を強制できない | 監査補助には使えても持出し防止には使えない |
| `@file` 添付 | prompt構築で直接追加。PreToolUseなし | Read hookだけでは全入力を検査できない |
| UserPromptSubmit | 拒否はできるがprompt本文の置換は不可 | 入力を匿名化して再投入する経路を外側に設ける |
| MessageDisplay | 画面表示だけを置換。モデル・会話記録は原文 | 画面の伏字を送信済みデータの伏字と誤認しない |

根拠: [終了値・timeout](https://code.claude.com/docs/en/hooks#exit-code-output)、[添付の例外](https://code.claude.com/docs/en/hooks#pretooluse)、[MessageDisplay](https://code.claude.com/docs/en/hooks#messagedisplay)、[SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)。

HTTP hooks はJSON入力を外部URLへPOSTする。prompt/agent hooks は入力を別モデルやエージェントに渡す。検査のために元のPIIを外部へ送る実装にならないよう、command型の局所検査、許可URL、環境変数の見える範囲、返答・stderr・debug出力を同時に管理する。MCP hookの結果も道具同様に出所と信頼を確認する。[hook handler](https://code.claude.com/docs/en/hooks#hook-handler-fields)

## 3. Claude Code 内蔵sandboxの対象・既定・例外

内蔵sandboxは既定で無効。有効時はBash/PowerShell/Monitorと子プロセスに作用する。Read/Edit/Write/WebFetch/WebSearch、ローカルMCP、command hooks、LSP、status lineやapiKeyHelper等はその外側で動く。`sandbox.filesystem.denyRead` はRead道具を直接制限せず、通信許可先もWebFetchを直接制限しない。[対象範囲](https://code.claude.com/docs/en/sandboxing#what-runs-outside-the-sandbox)

既定の読取は資格情報を含む機械の大部分、書込みは作業場所と一時場所・追加場所、通信は空の許可先から始めて代理を通す。環境変数は継承される。既定の資格情報拒否一覧はない。したがって「sandboxをONにしたから秘密を読まない」にはならない。

隔離に失敗した場合、既定では隔離なしで実行する場合がある。管理用途では `enabled:true` に加え `failIfUnavailable:true`、`allowUnsandboxedCommands:false` が必要。`excludedCommands` は引き続き別の脱出経路なので、管理者必須sandboxでの設定源制限と組み合わせる。`filesystem.disabled:true` は通信だけを残してファイル保護を外し、後続実行物を書き換える危険も残す。[失敗時処理](https://code.claude.com/docs/en/sandboxing#get-started)、[strict mode](https://code.claude.com/docs/en/sandboxing#turn-off-the-retry-with-strict-sandbox-mode)

手入力した `!` シェルコマンドは通常は隔離外で、background sessionやLinuxの環境scrub等では例外がある。モデルの再試行 `dangerouslyDisableSandbox` の承認はモードとallow/ask次第で、単に「必ず人間に確認」とは言えない。全機能を同じOS境界へ入れるには、Claude Code自体をコンテナ、VM、SRT等の外側の隔離に入れる必要がある。

## 4. sandbox-runtime のOS実装

以下は **固定mainの公開コード** の確認であり、Claude Codeの実際の同梱版確認ではない。

### macOS

Seatbelt の `sandbox-exec` にポリシー文字列を渡す。基本は `deny default` からプロセス実行・必要なOS機能を許可し、読取・書込・通信の規則を生成する。直接のインターネット通信を許さず、指定した局所代理と必要なOS通信に限定する。子プロセスも境界内となる。[macos-sandbox-utils.ts L981](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/macos-sandbox-utils.ts#L981)

読み込みは広い拒否に狭い許可を開ける設計で、さらにその内部の狭い拒否は残る。書込みは許可の内部でも拒否が優先する。許可規則一般の `deny > ask > allow` と同じアルゴリズムではない。[読取規則 L350](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/macos-sandbox-utils.ts#L350)、[書込規則 L913](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/macos-sandbox-utils.ts#L913)

`allowAppleEvents` は別アプリ起動を開け、起動アプリは隔離外となる。`enableWeakerNetworkIsolation` はGoの証明書検証等のため `trustd` への通信を開けるため弱化する。信頼されないrepo設定からこれらを許す設計は避ける。[例外生成 L1050](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/macos-sandbox-utils.ts#L1050)

### Linux / WSL2

`bubblewrap` の読取専用の元ファイルシステムへ許可書込経路をbindし、読取拒否のファイルには空ファイル、ディレクトリには一時ファイルシステムを重ねる。`--unshare-net` の独立通信空間を作り、Unix socketを介した `socat` 中継だけで外側の代理へ届く。代理用環境変数を無視するソフトウェアは原則つながらないのであり、環境変数の設定だけで通信を制限しているわけではない。[Linux mount計画 L2400](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/linux-sandbox-utils.ts#L2400)、[通信 L3376](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/linux-sandbox-utils.ts#L3376)

独立PID空間、独立ユーザー空間、専用 `/proc`、新しいセッション、親死亡時終了を使う。seccomp（OS呼出しのフィルタ）はAF_UNIX socket生成とio_uringの経路を制限する。適用補助プログラム内でさらにPID/ユーザー/mount空間を分け、非フィルタ適用の中継プロセスを対象コードから不可視にする。継承済みsocket記述子は生成禁止だけでは無効にならない。[Linux起動 L3293](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/linux-sandbox-utils.ts#L3293)、[PID保護 L3480](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/linux-sandbox-utils.ts#L3480)、[seccomp説明](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/README.md#unix-socket-restrictions-linux)

Linuxの読み込みglobは実行準備時に既存経路へ展開されるため、その後に新設されるファイルの保護はmacOSの規則と一致しない。書込globにも制約があり、非存在経路、symlink、mountの重なりを含めた受入試験が必要。`enableWeakerNestedSandbox`、任意Unix socket許可、seccomp未導入は別々の弱化要因。Docker socketはホストの大きな権限へつながる。[経路制約](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/README.md#filesystem-configuration)

### Windows

公開SRTはalphaとして別の局所ユーザー `srt-sandbox`、制限付きトークン、job object、SID（アカウント識別子）に結び付いたWFP通信フィルタ、ファイルのACEアクセス規則を使う。二段階起動で対象を当該アカウントとして起動し、専用profileと新しい環境を使う。同じアカウントとして外側で起動したプロセスにもSIDの通信制限が残る。代理認証トークンのコマンド引数表示、OSのDNSサービスを通る名前解決等の既知制約が明記されている。[Windowsコード](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/windows-sandbox-utils.ts)、[README Windows](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/README.md#windows-alpha)

一方、Claude Code組込sandboxは公式ではmacOS/Linux/WSL2のみで、native Windowsでは隔離なし。この二つを同じ対応表へまとめない。

### 設定を書き換えて自ら権限を増やすことへの保護

SRTはshell起動ファイル、Gitの危険な設定・hooks、IDE設定、`.claude/commands`/`.claude/agents` 等を自動書込拒否の候補にする。Linuxの再帰探索には深さ上限がある。許可作業場所内でも、実行後に宿主が読み込む設定を自由に書けると隔離をまたぐための保護である。[保護候補](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/sandbox-utils.ts#L10)、[探索制約](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/README.md#mandatory-deny-paths-auto-protected-files)

**推論**: 対象一覧と浅い探索だけでは、組織が新たに追加する検査器や秘密台帳の改変保護を自動的に満たせない。実行物・ポリシー・代理設定を対象外の読取専用領域に置く。

## 5. 通信代理と要求単位の検査

SRTはHTTP/HTTPS代理とSOCKS代理を外側に作る。通信はhost/portの正規化、設定deny、設定allow、strictAllowlist、命令別allow、確認callbackの順で判定する。固定mainではcallbackの `true` だけが許可で、例外や不明値は拒否する。ただしREADMEはこの挙動をv0.0.79後の変更と記載しているので、旧配布版へ同じcallback返答を無検証で移植しない。[判定 L480](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/sandbox-manager.ts#L480)

許可した名前を一度解決し、loopback、link-local、cloud metadata、宿主自身のIP、明示拒否IP/CIDR等を除いた後、その検査済みIPへ接続する。解決と接続の間に再解決しない。私設アドレス帯全体は既定拒否ではなく、`deniedResolvedAddresses` に組織の禁止帯を足す。親代理や外部MITM経路では相当の検査をその経路側に依存する。[resolved-address-guard.ts L199](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/resolved-address-guard.ts#L199)

これは**名前の解決結果**を検査する機構であり、allowlistで明示したIP literalへの直接接続はこのguardで再拒否しない。また解決先IP:portをallowedDomainsで明示許可すれば禁止帯の例外になり、明示許可されたlocalhost名にはloopbackだけへの到達を認める。従ってmetadataやlocalhostへの絶対到達禁止を独自ハーネスの要件にする場合は、明示IP・名前の許可の両方を管理し、guardだけに依存しない。[例外と順序 L141-L146](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/resolved-address-guard.ts#L141)、[IP/localhost例外 L226-L253](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/resolved-address-guard.ts#L226)

`network.filterRequest` はライブラリ側のcallbackとしてmethod、URL、headers、body streamを受け、要求単位のallow/denyを行う。例外は拒否。HTTPには直接、HTTPSには `tlsTerminate` によるTLS終端（代理が復号し、再接続すること）を有効にした場合に作用する。通常のCONNECTトンネルやTLS終端除外先では内容を検査できない。SOCKSは一般のアプリケーション要求をHTTP形式に変換しない。[request-filter.ts L1](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/request-filter.ts#L1)、[例外拒否 L173](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/request-filter.ts#L173)、[HTTPS実装](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/tls-terminate-proxy.ts)

**推論**: このcallbackに局所PII検査を置くことは可能だが、全bodyを必要とする分類器なら、判定完了前に上流へ送らないようbodyを全量検査する実装・上限・時間制限が必要。仕様はPII分類器そのものを提供していない。ドメイン許可だけでは、そのサービス内の別tenant、別repository、アップロード、コメント、URL引数を区別できない。

READMEには古い「内容を検査しない」「custom proxyは将来」の記述と、新しいTLS終端/filterRequest/httpProxyPortの記述が混在する。個別実装と固定版を優先し、全版共通の不在という断定には使わない。

## 6. 秘密を渡さず認証する仕組み

認証鍵を「暗号化して子へ渡す」のではなく、子にはダミー値だけを渡し、外側の代理が許可先への要求で実値に戻す。モデル・子プロセス・そのstdoutに実鍵を載せずサービスを利用する認証委任である。実鍵は宿主の管理側に存在する。[credential-sentinel.ts L1](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/credential-sentinel.ts#L1)

| 機構 | 実装・仕様 | 残る制約 |
|---|---|---|
| env `mode:deny` | 指定した環境変数を子へ渡さない | 指定外の秘密や別ファイルは残る |
| env `mode:mask` | セッション固有sentinelへ置換 | 値形式が必要ならextract/JWTの指定が必要 |
| file `mode:mask` | Linuxは読取専用の置換コピーをbind | macOSはコピー置換でなくファイル拒否 |
| `injectHosts` | 実鍵を復元するhostを別途制限 | 未指定では到達可能な設定allowedDomainsに広がる |
| TLS終端 | 復号したheaders/bodyでsentinelを実値に戻す | 除外先・証明書固定・相互TLSなどと両立しない場合 |
| AWS SigV4 | 複数の鍵を対として検出し再署名 | 一部streaming/事前署名/SigV4Aは再署名不能 |
| `onExtractNoMatch` | warn / deny / error を選べる | 既定warnではパターン不一致で未加工値が残る |

**別の失敗経路**: `decode:jwt` の環境変数でJWT形式検証に失敗した場合、または指定した `maskClaims` に該当する文字列の項目がない場合、固定mainは警告して置換を省き、実値を子に残す。この経路はextractの `onExtractNoMatch:deny/error` だけでは閉じない。値全体のmaskに戻す、起動前に値形式と対象項目を局所検証して失敗を拒否する、または当該環境変数をdenyする設計が必要である。ファイル内の複数JWT候補でも不適合候補は無加工で残ることがあり、他の候補が置換できたという成功数だけで全秘密を保護したと扱わない。[環境変数の失敗 L103-L144](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/credential-mask-env.ts#L103)、[ファイル候補 L240-L270](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/credential-mask-files.ts#L240)

根拠: [credential-mask-env.ts L81](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/credential-mask-env.ts#L81)、[file L317](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/credential-mask-files.ts#L317)、[body置換](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/body-substitution.ts)、[AWS署名](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/aws-sigv4.ts)、[Claude仕様](https://code.claude.com/docs/en/sandboxing#mask-credentials)。

Claude Codeはmask・TLS終端・平文再注入・AWS対の指定を信頼されたuser/managed/CLI設定からのみ採用し、repoの設定からの権限増加を防ぐ。denyは複数設定源から足せる。環境scrubはBashだけでなくhooks/stdio MCPの環境も削り、Claude本体のAPI認証は保持する。ただしGitHub tokenやproxy設定は残すと公式が説明するので「全秘密を消す」と表現しない。[env scrub](https://code.claude.com/docs/en/env-vars#what-the-subprocess-environment-scrub-removes)

**推論**: この設計は「AIに秘密そのものを読ませず必要な操作をする」用途に直接関連する。しかし秘密鍵を隠すことと、サービスが返す顧客データ・PIIを隠すことは別。許可操作・対象レコード・返却列・集計最少人数を制限する業務APIを外側に設ける必要がある。sentinelを含む要求でも、広い許可先の破壊的操作をすべて安全にするわけではない。

## 7. モデル送信、観測出力、記録、記憶

Claude Codeは局所実行でも外部モデルへデータを送る。TLSは経路暗号化であり、モデル提供者が平文を扱わない意味ではない。局所Bashのドメイン規則はClaude本体のAPI送信を制限しない。企業API・Team/Enterpriseの通常契約は生成モデル学習に使わないという方針だが、保持・フィードバック・例外は別に確認する。消費者アカウントでは学習許可設定により変わる。[data usage](https://code.claude.com/docs/en/data-usage)、[ZDR](https://code.claude.com/docs/en/zero-data-retention)

標準商用保持は30日、ZDR（適用対象の推論データを原則サービス側に保持しない方針）は適格アカウントで別途有効化する。法令対応や利用方針違反への対応は例外で、違反検知した入力・出力を最大2年保持する場合がある。組織への認証、モデル、利用機能、提供者の適用範囲を確認し、保持ゼロを暗号学的な非閲覧や送信禁止と混同しない。利用者の機械に保存する会話・記憶、MCP、運用メタデータも別範囲である。[ZDR範囲・例外](https://code.claude.com/docs/en/zero-data-retention#data-retention-for-policy-violations)。LLM gatewayはAPIへの接続先・認証を統一するが、それ自体に局所PII除去が実装される証拠とはならない。[gateway](https://code.claude.com/docs/en/llm-gateway)

局所ではsession JSONLにメッセージ・道具呼出し・結果が保存され、history、貼付cache、ファイルsnapshot、debug等も別にある。既定のcleanupPeriodDaysは30日だが、すべての保存物が同じ条件で削除されるわけではない。Desktop/Cowork会話の例外、保持設定を安全に判断できない際の掃除停止、historyの特別条件などがある。[保存物・掃除](https://code.claude.com/docs/en/claude-directory#cleaned-up-automatically)

自動記憶は `~/.claude/projects/<project>/memory/` のMarkdownで、同一repoのworktreeも共有する。局所の別会話窓だから情報が混ざらない、とは言えない。`autoMemoryEnabled` と保存場所を管理し、機密度・利用目的・保持期限を記憶に伝播させる。[memory](https://code.claude.com/docs/en/memory)

観測出力はuser prompt・道具引数・内容の出力が通常は無効で、`OTEL_LOG_USER_PROMPTS`、`OTEL_LOG_TOOL_DETAILS`、`OTEL_LOG_TOOL_CONTENT` 等で変わる。`OTEL_LOG_RAW_API_BODIES` は会話全体を含む要求/応答を出力できる。通常のエラー報告には既知の秘密・パス・mail等の除去があるが、これを一般のモデル入力や任意の観測出力のPII除去保証へ拡張しない。[monitoring](https://code.claude.com/docs/en/monitoring-usage)、[エラー報告](https://code.claude.com/docs/en/data-usage#telemetry-services)

## 8. サブエージェント、MCP、拡張と供給元

サブエージェントは主会話の権限規則を継承し、`tools` と `disallowedTools` で道具集合を減らせる。`tools` 未指定なら多くの道具を継承する。`disallowedTools` の引数条件は道具全体を除くため、コマンド単位の制限とは違う。Bashが残るならRead/Editのみの道具表示制限で完全な読取専用にはならない。[subagents](https://code.claude.com/docs/en/sub-agents#available-tools)

MCPは単独の子へ接続したり親の接続を共有でき、独自の道具・外部通信・返却データが増える。子の起動イベントSubagentStartは生成を止められないので、生成承認はAgent道具の前段で行う。子も同じhooksを呼び、agent_id/agent_typeで出所を識別できる。別会話窓やGit worktreeは処理整理であり、独立OSアカウント・VMを意味しない。[hooks継承](https://code.claude.com/docs/en/hooks#hook-locations)、[SubagentStart](https://code.claude.com/docs/en/hooks#subagentstart)

ローカルMCPはBash sandboxの外で起動する。SRTでMCPサーバーを包む利用例が公式公開repoにあるが、自動で全MCPへ適用される意味ではない。外部MCPは認証を持って独立したサービスへデータを送る。project `.mcp.json` の承認とfolder trustがあり、非対話 `-p` では対話の信頼確認が出ない点を確認する。[MCP](https://code.claude.com/docs/en/mcp)、[SRT利用例](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/README.md#example-use-case-sandboxing-mcp-servers)

現行hooksの `mcp_server.source` はplugin/sdk/user/project等の出所を伝える。サーバー名や道具名prefixだけで信頼を判断しない。`allowedMcpServers`/`deniedMcpServers` にはname/command/URLの管理がある。`allowManagedMcpServersOnly` がないallowlistは下位設定で広げられる。管理者自身が配るサーバーにはallowlist検査を省く例外もある。[出所属性](https://code.claude.com/docs/en/hooks#pretooluse-input)、[managed MCP](https://code.claude.com/docs/en/managed-mcp)

plugin由来の子定義はpermissionMode/hooks/mcpServersを無視するが、plugin全体としてはhooksやMCPを別に登録できる。従って子定義の制限だけでpluginの全実行を制限したと考えない。管理配布元の限定、版とcommitの固定、コード署名/ハッシュの外部確認、実行権限の局所最小化を組み合わせる。[plugin subagents](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope)、[組織plugin設定](https://code.claude.com/docs/en/plugins/org)

## 9. 管理者ポリシーと障害時動作

managed設定は通常は下位のuser/project/local/CLIより強い。複数管理源は既定で最高優先のものを使い、`managedSourcesBehavior:merge` では種類別の統合を行う。単純な「全部後勝ち」ではない。配列の合算はallowも増やし得るので、管理源の所有者と統合規則を確認する。[managed sources](https://code.claude.com/docs/en/managed-settings#how-claude-code-combines-managed-sources)

主な鍵は `allowManagedPermissionRulesOnly`、`allowManagedHooksOnly`、`disableBypassPermissionsMode`、`sandbox.network.allowManagedDomainsOnly`、`sandbox.filesystem.allowManagedReadPathsOnly`、`sandbox.network.strictAllowlist`、`allowManagedMcpServersOnly`、`allowedProviders`、`forceLoginOrgUUID`、`strictPluginOnlyCustomization`、`strictKnownMarketplaces`。名前が似た制御でも、制限する対象と下位設定を無視する範囲は異なる。[settings reference](https://code.claude.com/docs/en/settings-reference)

壊れたJSON管理文書は起動拒否、invalidな単一制限鍵は安全側へ、invalid allowlistは空とするなどの処理がある一方、規則の個別invalid entryは除去される場合がある。管理文書が存在するのにOSで読取拒否された場合は、その政策なしで起動するケースも公式が明記する。`policyHelper` の非ゼロ終了・残るschema不整合は起動拒否にする。最低版の誤った指定等はfail-openとなる例外がある。[管理設定の失敗](https://code.claude.com/docs/en/managed-settings#keys-that-fail-closed)

単一の制限値を持つ鍵の安全側補修と、permissions/autoMode等の項目別補修は **Claude Code v2.1.282以降** の仕様である。その他のallowlistには個別の最低版がある。旧版にも同じ失敗時処理があるとは推定せず、組織の最低版と必須機能を具体的に対応付ける。

**推論**: 管理設定ファイルの存在だけを準拠証明にせず、起動前に読取可能性・構文・所有権・採用設定・digestを確認し、組織が承認した境界にならなければ独自起動器が停止するべきである。

## 10. クラウド実行は別の境界

Anthropic-hosted cloud sessionは独立VM、外側の通信代理、Git資格情報の代理注入を使う。Git資格情報・署名鍵はVMへ入らず、代理がscope付きで認証する。ネットワークをNoneにしてもモデルAPI通信は続き、そこでデータは外に出得る。自己運用の実行環境ではOS隔離・通信・資格情報の責任範囲が変わる。[cloud security](https://code.claude.com/docs/en/claude-code-on-the-web#security-and-isolation)

クラウドのnetwork secretsも特定プラン・要求形式に限定され、一般のenv値まで全て外側に隠す機構ではない。組込GitHub道具、MCP connector、モデルAPIの通信をシェルのネットワークallowlistと同一視しない。[cloud environments](https://code.claude.com/docs/en/cloud-environments#network-access)

## 11. 独自のPIIハーネスへの採用案と検証項目

以下は調査からの**設計提案**であり、Claude Codeの既存機能という主張ではない。

1. **外側の入力組立境界**: 利用者本文、添付、IDE文脈、MCP結果、子の報告、記憶を一箇所で分類。対象実レコードの局所IDとモデル用仮名を分け、対応表をモデル・shell・子から隠す。
2. **道具の意味に基づく制御**: 任意shellを最小化し、宛先、tenant、対象ID、返却列、目的、最大件数を構造化引数にする。承認は道具名ではなく書換え後の実操作とbindingして保存する。
3. **実行側の最小権限**: 必要資料だけを読めるOS領域、検査器と対応表は外側の読取専用領域、ネットワークは固定した代理だけ。失敗時に隔離なし・検査なしへ切り替えない。
4. **秘密の代理保持**: SRTのsentinel方式を認証鍵へ利用し、injectHostsを明示、extract不一致は拒否。JWT decode/項目maskの失敗は別に拒否し、全値maskまたはdenyへ戻す。PIIの返却結果には別の局所検査を置く。
5. **モデル・記録直前の境界**: 入力と結果を無加工でログに書く前に検査し、画面だけを伏字にしない。会話・記憶・観測・添付cacheの保持と暗号化は独立に設定する。
6. **出所と子の制約継承**: 拡張・MCPの版、権限、証拠、モデル送信先を固定。子へ親以上の権限・データ範囲を渡さず、報告も再検査する。

最低限の受入試験には、hookの非起動/exit 1/exit 2/不正JSON/timeout、@添付、IDE自動文脈、全道具結果置換前の記録、結果置換のschema不整合、非対話再開、設定源除外、管理JSON不整合/読取拒否、sandbox未利用、除外コマンド、未知宛先、TLS除外、credential extract不一致、JWT decode失敗/項目不一致/候補混在、PII入り子報告、共有記憶、同名MCP、別tenantへの送信を含める。架空データと専用試験環境を使い、実個人情報や実秘密を出力しない。

## 未確認・追加検証が必要な点

- Claude Code本体の同梱SRTの正確な版・差分と、公式資料の全機能の現行実装との一致。
- 認証mask、TLS終端、body検査、経路制約の全OS実行挙動。特にWindows alphaとLinuxの動的ファイル生成。
- `updatedToolOutput` の各道具schema・並行hooksの書換え競合・会話保存への原文残存範囲。公式はtelemetry先行を説明するが、全保存経路を一括保証していない。
- モデル提供者ごとの分類器送信内容、保持設定、地域、proxy互換性。別の安全判定を局所実装と誤認しない。
- enterprise管理源の適用例外、第三者MCP・plugin・IDEの局所/外部保存、クラウド内部の非公開強制機構。

公開資料で確認できなかった項目は「機能なし」ではなく「未確認」として比較表へ持ち込む。

## 独立レビュー後の改善

他の調査担当による独立レビューで、結果置換のschema不適合時に原結果へ戻る経路と、JWT decode/項目mask不一致で実env値が残る経路を追加確認した。両方を失敗時表・設計案・受入試験へ反映した。PII検査に直結するため、単に未確認リストへ残す扱いから本文の既知制約へ変更した。さらにhostname guardの明示IP/localhost例外、ZDRの保持例外、管理設定補修の最低版を補った。[独立レビュー記録](harness_review_oss_to_claude_20261008.md)
