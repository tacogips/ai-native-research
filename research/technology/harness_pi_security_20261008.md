# Pi の機密情報管理・実行隔離・ガードレール：固定コードによる技術調査

調査日：2026-10-08。対象は `pi.dev` が提供する Pi coding agent。旧 URL `badlogic/pi-mono` は現在 `earendil-works/pi` に転送される。取得した HEAD は `1cedd32724abfcb0915f76cc61b6827e2c16dbad`、コミット時刻は 2026-10-08 00:23:06 +02:00。公開最新版としてタグ `v1.1.0`（`abe508e1b89912adde45528136c3221eb69acdd7`、2026-10-07 23:33:33 +02:00）も取得して照合した。両者の差は変更履歴と端末表示関係が中心で、本稿の主要な隔離・権限コードに差はない。開発版 HEAD と公開タグを同一だと扱わない。

一次資料の取得物は `research/disclosures/raw/harness_20261008/pi/pi-mono/`、本体 51 件と外部拡張 12 件の主要ファイルの SHA-256、固定 URL、行数は [出典台帳](harness_pi_sources_20261008.json) に保存した。依存パッケージのインストール、拡張の実行、実ユーザーの認証情報の読み取りは行っていない。以下は公開コードの静的調査であり、実環境の侵入試験結果ではない。

## 結論と境界

Pi は機能を組み替えやすいハーネスだが、そのまま個人情報漏洩防止の境界になるわけではない。モデルに何を見せるかを変える拡張点と、実行を拒否する拡張点を持つ一方、通常の `bash`・ファイル操作は起動ユーザーの権限で動く。公式のセキュリティ方針も組み込みの実行隔離がないことを明示している。[SEC][SECURITY]

ただし「どんな隔離もない」は誤りである。最新版の標準 `codemode` は、モデルが書いた JavaScript を QuickJS の仮想実行環境で動かし、Node.js・直接のファイル操作・直接の通信を公開しない。これは JavaScript の能力制限であり、そこから呼び出すホスト側ツールまで OS で隔離する機能とは異なる。[CODE][VM]

| 機構 | 標準 / 別途導入 | 保護する範囲 | 保証しない範囲 |
|---|---|---|---|
| project trust：プロジェクトを信頼するかの判断 | 標準 | プロジェクト由来の多くの設定・実行拡張の読み込み | ツールが参照するファイル範囲、AGENTS 等の指示による誘導 |
| `tool_call` 拒否イベント | 標準の拡張 API。拒否方針は利用者が実装 | Pi の経路を通るモデル発行・入れ子ツール呼び出し | 拡張自身の直接通信・直接ファイル操作 |
| `context` / `context_with_system` | 標準の拡張 API | モデルへの会話内容の書換え | 検査失敗時の送信禁止、ローカル保存の消去 |
| `codemode` | 標準 | モデル生成 JavaScript の直接 OS 能力を制限 | 許可されたツール、分類モデル呼び出し、保存値からの漏洩 |
| sandbox 公式例 | コピー・依存導入が必要 | `bash` と利用者の `!` コマンドの OS 制限 | 標準ファイルツール、拡張全体、失敗時の強制停止 |
| Gondolin 公式例 | 拡張と QEMU の導入が必要 | 標準ツールと `!` を Linux の小型仮想機械へ移す | ホストに残る拡張、渡した環境変数、書込可能な共有フォルダ |
| Pi 全体のコンテナ・仮想機械 | 外部の実行基盤 | Pi 本体・ツール・拡張を含めた OS の境界 | 境界内に持ち込んだ個人情報・認証情報のモデル送信 |
| 個人情報の認識・自動伏字 | 標準として確認できない | 独自の検査器・通信仲介で追加する必要 | 拡張 API があることを、検査の搭載と取り違えない |

## 1. プロジェクト信頼と起動時の読み込み

最新版は `.pi/settings.json`、`.pi/mcp.json`、`.pi/extensions`、skills / prompts / themes、`.pi/SYSTEM.md` 等を信頼判断の対象にする。既定の `defaultProjectTrust` は `ask`。判断順は CLI の `--approve` / `--no-approve`、ユーザー・CLI 拡張の `project_trust`、保存済みの最も近い親ディレクトリの判断、全体設定である。保存先は既定で `~/.pi/agent/trust.json`、判断対象のパスは正規化される。[SEC]

非対話の print / JSON / RPC では質問画面を表示できない。既定 `ask` と `never` は判断が得られない保護対象を読まず、`always` は読む。これはツールごとの許可モードではない。

制限の例外も公式に記載されている。セッション作成先を決める `sessionDir` は信頼確定より先にプロジェクト設定から読む。さらに `AGENTS.override.md`、`AGENTS.md`、`CLAUDE.md` は、context 読込を別途止めない限り信頼拒否時にも読む。従って、信頼拒否だけでプロンプト注入、すなわち外部の文章がモデルへ不正な指示を与える問題を遮断できるとはいえない。[SEC]

## 2. 標準ファイル操作・シェル実行

`resolveToCwd()` は `resolvePath()` を使用し、絶対パス、ホーム展開、相対パスを解決する。`resolvePath()` は `node:path.resolve` によるパスの整理であり、作業フォルダ内に閉じ込める拒否処理ではない。通常の `read` / `write` / `edit` は Node.js のファイル操作を呼ぶ既定の操作実装である。[PATH][READ][WRITE][EDIT]

そのため、作業フォルダ指定をアクセス可能範囲の指定と解釈してはいけない。通常のファイル API はシンボリックリンクを辿り得るため、字面上のパスを確認するだけでは実体の所在を保証できない。これは公開コードからの解釈であり、リンクを使った実攻撃の再現結果ではない。実体パス確認だけでも確認後の差替えの競合が残るので、機密領域の非マウント、専用ユーザー、OS 制限を併用する設計が必要になる。

`bash` の既定実装は `child_process.spawn` でローカルのシェルを起動する。`cwd`、環境変数、標準出力・標準エラーを渡す。`getShellEnv()` は `process.env` を広く引き継ぐ。従って API キーを環境変数に置く方法は、ディスク上に書かない利点があっても、実行コマンドから秘密を隔離する方法ではない。[BASH][SHELL]

各ツールは `operations` を差し替えられ、`bash` は `spawnHook` も持つ。ここで遠隔の実行器、仮想機械、制限されたファイルサービスへ渡すことができる。ただし、登録済み拡張がそれ以外の Node.js API を直接使えば、この経路は通らない。[BASH][WRITE][EDIT]

## 3. 検査・許可イベントの順序と失敗時挙動

| イベント | できること | 実装で確認した注意点 |
|---|---|---|
| `before_agent_start` | 展開後の利用者入力を参照し、システム指示の要素を調整 | これだけで入力本文を必ず差し替えたり、全送信を防げるとは扱わない |
| `tool_call` | 実行前の引数を変更、`{ block: true, reason }` で拒否 | 後続ハンドラは変更後の引数を見る。変更後の再スキーマ検証はしない |
| `tool_result` | 結果の content / details / structuredContent 等を変更 | content だけ変更すると対応しなくなる structuredContent は削除される |
| `context` | 各モデル呼び出し前の会話を書換え | システム指示・ツール宣言は Pi が復元する |
| `context_with_system` | システム指示を含む全体を書換え | 戻り値をそのまま使用するため、利用者が宣言の整合性を持つ |
| `before_provider_request` | 通信直前の要求データを差し替え | 対応する送信経路の範囲を確認する必要がある |
| `before_provider_headers` | 要求ヘッダーを直接変更、null で削除 | ヘッダーから認証情報を参照できる、信頼済みコードの権限である |
| `user_bash` | 利用者が直接書いた `!` コマンドの実行器を差し替え | モデルの `tool_call` とは別経路 |

型定義と呼出し実装を両方確認した。[TYPES][ARGS][HOOK]

**失敗時の動作はイベント間で揃っていない。** `tool_call` はハンドラの例外を実行側へ渡し、当該ツールの実行を阻止する。実行ループはエラー結果に変換するため、会話全体や Pi プロセスを必ず終了する意味ではない。[LOOP]`user_bash` も例外を再送出する。一方、`tool_result`、`context`、`context_with_system`、`before_provider_request`、`before_provider_headers` は、ハンドラ例外を捕捉してエラー通知した後、残った値で処理を継続する。入力・結果の検査拡張で例外を投げるだけでは、安全側に停止することを保証できない。[RUN]

また `ctx.executeTool()` を使った入れ子呼び出しは、引数検証・同じツール前後イベントを経由し、`parentToolCallId` を持つ。直接 `createBashTool().execute()` などを呼ぶ独自コードや、拡張自身の OS 操作はこの保証の対象ではない。[EXT][HOOK]

**設計への含意（本調査の提案）:** 個人情報の検査不能・時間切れ・未対応形式は拒否する条件として、モデルの指示と独立した送信仲介に実装する。既存イベントを使う場合も、正常終了で拒否・安全な置換ができる API と、例外が継続になる API を分けて試験する。

## 4. `codemode` によるデータ最小化と残る経路

モデルの JavaScript は QuickJS を WebAssembly 化した実行環境に入る。毎回新しい VM を Worker 内に作成する。直接の `process`、`require`、モジュール、`fetch`、タイマー、`WebAssembly` は公開しない。`eval` / `Function` は使えるが同じ VM 内に留まる。標準ハーネスは VM ヒープを 256 MiB に制限し、割込みやスタック制限を設定する。[CODE][VM][CM]

実行時間は `// @options: {"timeout_ms": ...}` で指定できる。しかし Pi の呼出し実装は未指定時に `Infinity` を渡す。ライブラリ単体の既定値と Pi からの既定を混同しない。停止信号や VM 制限があることと、標準で有限時間に必ず停止することは別である。[CMTOOLS]

ツールの生の結果は通常モデル文脈へ自動追加されず、スクリプトが `text()`、`image()`、戻り値で選んだ内容だけを返す。例えば、機密を含む検索結果をスクリプトの中で数え、「該当件数 3」とだけ返す形は、モデルに個別の氏名を渡さずに処理できる。ただし VM とツール実行器は平文を持つので、秘密計算・準同型暗号ではない。[CODE]

成功した出力の選択だけでは足りない。codemode は呼出し引数の JSON プレビュー、ツールのエラーを details と途中経過に自動記録する。最終 details はセッションにも保存され得る。またスクリプト失敗時には例外の stack / message を `Script error` として自動でモデル向けの結果へ加える。例えば個人情報を含む値を例外文に使うと、`text()` しなくても出力経路になる。成功・失敗・途中経過・details をすべて検査する必要がある。[CMERROR][CMDETAIL][LOOPSAVE][SESS]

標準ツールの呼出しは `ctx.executeTool()` を通る。別に `models.classify()` / `models.generateImages()` の能力も公開しており、登録済みの分類・画像モデルへデータを渡せる。この呼出しではモデルを provider と id から再解決し、スクリプト指定の `baseUrl` や headers を採用しない。モデル一覧から headers を除く処理もあり、認証情報を攻撃者指定 URL にそのまま送る問題を抑える。反面、許可済みの外部分類モデルへの送信自体を防ぐ PII 検査ではない。[CMODELS]

主たる会話モデルの要求イベントは Agent/SDK の接続点にある。上記の分類・画像呼出しは `ModelRuntime` へ `{ signal }` を渡す直接経路なので、通常の `tool_call` / `context` / Agent の `before_provider_request` がそのまま全て適用されるとは扱わない。公開コード上、これらの補助経路も含めた統一的な送信前検査が必要である。[SDK][RUNTIME][CMODELS]

`store()` / `load()` は JSON 値を実行間に持ち越す。Pi は `codemode-store` のセッション要素に保存し、分岐から復元する。秘密をモデルへ出力しなくても保存領域に残ることがある。原本を保持しない設計では保存値にも同じ分類・保持期間・削除方針を適用する必要がある。[CODE][CMTOOLS]

## 5. 認証情報とモデルの通信先

認証情報の既定保存先は `~/.pi/agent/auth.json`。API キーと OAuth トークンを JSON で保管する。新規作成時はファイル `0600`、親ディレクトリ `0700` を指定する。これは他ユーザーの読取を抑える UNIX 権限であり、暗号化や同じユーザーで動くツールからの隔離ではない。既存ファイルのモードをこの指定だけで強制修正するとは主張しない。[AUTH]

秘密保管サービスを使用する `!command`、環境変数参照、独自の認証保存バックエンドも利用できる。設定値を得るためのコマンドはホスト権限で実行されるため、設定ファイル自体を信頼済みの実行コードとして扱う必要がある。コマンド結果のキャッシュは利用経路により異なり、`models.json` の要求時コマンドは文書上キャッシュしない。[KEY][MODEL]

取得優先順位は実行時 `--api-key`、保存済み auth、`models.json` の API キー、環境変数・クラウド環境の認証情報。ローカル llama.cpp や OpenAI 互換のローカルサーバーを設定できるが、ローカルモデルの選択だけで補助モデル・MCP・拡張の外部通信まで停止するわけではない。[MODEL]

標準に、日本語の個人情報・要配慮個人情報を網羅的に認識する分類器、通信前の強制伏字、法律に応じた送信可否判定、全ツールの内容を追跡するデータ分類タグは確認できない。これは対象版の標準ファイル・文書で確認できた範囲の結論であり、外部拡張が存在しないとの主張ではない。

## 6. セッション・圧縮・再開・共有・診断

セッションは既定で JSONL、つまり一行一つの JSON としてローカルに保存し、再開・分岐・複製を行う。ユーザーの最初の発言で永続化が始まり、モデルが応答する前に入力がディスクへ残る。通常のセッション保存実装は暗号化処理を持たず、ファイル作成に認証情報と同じ専用の `0600` 指定を置いていないため、実際の権限は umask と上位ディレクトリ等にも依存する。`--no-session` は再開可能な永続保存を止める。[SESS][SESSDOC]

会話圧縮は、古い会話をモデルで要約して直近を残す。元セッション要素を消す機能ではない。分岐の要約もモデル送信を伴う。専用の要約呼出しは `cacheRetention: "none"` にするが、これはモデル事業者の全保持ゼロを保証する契約ではない。通常会話の検査だけを行い、要約用通信・再試行・再開後の原本を見逃す設計にしない。[SESSDOC][COMP]

`cache warming` は、モデル側にある指示の再利用領域を保つために同じ要求を再送する機能である。要求は `ModelRuntime.streamSimple()` 経由で再送される。保持時間を延ばす自動活動も個人情報の通信台帳で対象にする。[CACHE]

`/export` は HTML / JSONL、`/share` は Radius の共有物か非公開 GitHub gist へアップロードする。非公開 gist も端末内保存ではない。`/bug` は診断・任意の会話またはモデル要約を含めた報告を作る。診断の設定項目には token / password 等のキー名、URL 認証部の伏字処理があるが、会話全体の個人情報を自動で安全化する保証にはならない。[SESSDOC][BUG]

一方、長いツール出力・画像等を退避する一時ファイルには `0600` と排他的新規作成 `wx` を使い、他ユーザーが先に作ったリンクを追わない処理がある。良い部分として採用できるが、保存期間・削除の証明まではこの関数単体からいえない。[TEMP]

## 7. MCP：最新版では標準機構

MCP は外部サービスに道具として接続する共通仕様である。本版は MCP を標準で持つため、以前の Pi 説明での「MCP は非標準」を流用しない。ユーザー・プロジェクト設定、stdio、Streamable HTTP、OAuth、ツールの公開方式、資源取得を持つ。[MCP]

stdio はサーバー実行ファイルと引数を別々に指定し、shell の文字列として直接実行しない。ただし `npx` / `uvx` 等を指定すれば別の配布物を取得・実行し得る。Pi の生成経路は `inheritEnv: false` を指定しておらず、基盤 `StdioTransport` は既定で親の `process.env` と追加 env を結合する。設定に env を明記したことは、他の環境変数が除外されたことを意味しない。[MCPEXEC][STDIO]

HTTP には OAuth とヘッダー認証を用意する。OAuth は認証要求と応答を対応させる state、公開クライアントの認証コード横取りを抑える PKCE、ループバックのコールバック、発行者確認等を実装する。これは認証境界の保護であり、返る文章やツール説明を安全と認定する仕組みではない。明示の `authServerMetadataUrl` は信頼済み設定として扱う。[MCP][OAUTH][PKCE]

MCP の roots は作業フォルダを通知する情報であり、サーバーが読める OS パスを強制制限するものではない。既定の `codemode` 公開、`direct` 公開、非表示にした宣言を区別し、宣言非表示と能力の禁止を混同しない。危険なサーバー自身のファイル・ネットワーク権限は別途隔離する必要がある。[MCP][MCPEXEC]

## 8. 公式の防護例の実力と限界

### `permission-gate.ts`

`rm` の一部、`sudo`、`chmod/chown ...777` を正規表現で見つけ、対話で確認する。非対話では対象を拒否する。これは事故を抑える学習用の例であり、別のコマンド表現、スクリプト、他のツールを含めた一般的な権限体系ではない。[GATE]

### `protected-paths.ts`

`write` / `edit` の引数に `.env`、`.git/`、`node_modules/` の部分文字列があると拒否する。`read`、`bash`、別名の拡張ツールは対象にしない。したがって `.env` の読取漏洩防止やリンク実体の所在判定をこの例が持つと説明しない。[PROTECT]

### `sandbox/index.ts`

`@anthropic-ai/sandbox-runtime` で macOS の `sandbox-exec`、Linux の `bubblewrap` を使い `bash` と `!` を包む。既定の読取禁止は `~/.ssh`、`~/.aws`、`~/.gnupg`。書込は作業フォルダ・`/tmp` が中心で、`.env` 等の書込を抑える。`.env` の denyWrite は denyRead ではない。また `~/.pi/agent/auth.json` をこの例の既定 denyRead が全面的に保護するとはいえない。[SBDEFAULT]

**初期化失敗、macOS/Linux 以外、`--no-sandbox`、無効設定では、例の登録ツールはローカルの `bash` 実行へ戻る。** 検査失敗時に拒否する本番用設計としてそのまま採用しない。また `.pi/sandbox.json` は全体設定より優先して上書きする。モデルが書き換えられるプロジェクト設定を信頼済みポリシーと同じにしない。これらはコード上の挙動であり、未知の脆弱性を推定したものではない。[SANDBOX][SBDEFAULT]

### Gondolin・全体隔離

Gondolin 例は read / write / edit / bash / grep / find / ls と `!` を小型仮想機械へ渡す。作業フォルダは `/workspace` に共有され、書込がホストへ反映される。ホスト環境変数をゲスト実行へ継承する点を公式文書が明記している。環境変数の秘密を除く修正が必要であり、ホストの別拡張は隔離されない。[GONDOLIN][ISO]

公式文書は Pi 全体の Docker、Docker Sandboxes、OpenShell も説明する。Docker Sandboxes のホスト仲介によるモデル認証情報の差替えと、単純に環境変数で本物のキーをコンテナへ渡す Docker は異なる。ここに挙げた外部基盤の強度は Pi 本体の機能として計上せず、基盤自身の別途検証に委ねる。[ISO]

## 9. 拡張の供給網・管理統制・自動通信

拡張は Pi と同じプロセス権限を持ち、モデル要求・応答・認証情報を参照できる。npm / git / ローカル配布物を取り込む package manager は、npm の既定インストール引数に `--ignore-scripts` を強制しない。固定バージョンを扱う機構はあるが、取得時の署名検証・会社の配布許可台帳を標準の強制管理機構として確認していない。『Pi 内の tool_call で許可しているから拡張自体も安全』は成立しない。[PKG][SEC]

匿名の導入・更新報告は `https://pi.dev/api/report-install?version=...` へアクセスする。対象コードの URL 引数は version で、User-Agent も送る。これは会話送信とは異なるが、受信サーバーには通常の通信メタデータも届く。`PI_TELEMETRY=0` または設定で止められ、`PI_OFFLINE` は自動ネットワーク活動を止めるための設定である。後者は OS のネットワーク拒否と同一ではない。[REPORT]

企業単位で強制する変更不能な中央ポリシー、全操作の改ざん検知監査、管理者と利用者の役割分離、データ分類タグの全経路追跡、法域別の保持・送信制御は、対象版の標準機構として確認できない。必要な場合は外部の実行管理・通信仲介・認証情報仲介に置く。

## 10. 個人情報を扱うハーネスへの採用案と検証項目

以下は Pi の実装済み機能ではなく、本調査からの設計提案である。

1. **生データは制限された処理器へ置く。** codemode のようにモデルへ渡す結果を選べる機構を使い、一般モデルには件数・匿名の分類・参照番号を返す。参照番号の対応表はモデルから見えないサービス側へ置く。
2. **モデル送信を統一的に検査する。** 会話、要約、分類、画像、再試行、事前読込、共有・診断、MCP、拡張の直接通信を通信先の許可条件と照合する。検査不能なら拒否する。会話イベントだけを唯一の境界にしない。
3. **本物の秘密は実行環境へ渡さない。** 専用の通信仲介が宛先を限定して認証情報を付け、ツール環境変数から秘密を除く。
4. **実行ポリシーは作業データの外へ置く。** プロジェクト設定で中央の拒否方針を緩められないようにする。拡張・MCP サーバーも同じ境界内へ置くか、別の最小権限で動かす。
5. **保存の漏れを検証する。** 原本をモデルへ出さない場合でも JSONL、codemode-store、長い出力の一時ファイル、エラー、HTML、診断 ZIP に入っていないか調べる。

| 必須の試験 | 合格条件 |
|---|---|
| PII 検査器の停止・時間切れ・不正応答 | モデル宛て送信と危険なツールを止める |
| sandbox 初期化失敗・未対応 OS | 制限なし実行へ戻らない |
| ファイル工具・bash・独自工具・MCP の同じ機密ファイル参照 | 全経路で同じアクセス方針を適用 |
| 相対パス、絶対パス、シンボリックリンク、確認後の差替え | 禁止領域へのアクセスを OS 側でも止める |
| 拡張・MCP 子プロセスからの環境変数参照 | モデル認証情報を取得できない |
| 会話ではなく圧縮・分類・画像・共有を使う送信 | 同じ送信検査と監査が適用される |
| 再開・分岐・圧縮後の再送信 | 以前の秘密や削除対象が復活しない |
| 型検証後に拡張が引数を変更 | 変更後も方針に違反する実行を止める |
| 作業フォルダの設定・拡張を書換え | 中央の隔離と拒否方針を解除できない |

本稿ではこれらの実行試験を行っていない。次段階の実装・受入検証仕様として整理した。

## 11. 外部の Pi 拡張：権限判断と OS 隔離を分けて評価する

標準・公式の例に加えて、代表的な二つの外部拡張の原本も保存した。全公開拡張を網羅した一覧ではなく、権限判断のみを追加する設計と OS 隔離も追加する設計を比較する対象である。Pi 1.1.0 との実行互換性は試験していない。

### `pi-permission-modes` 2.4.1

固定コミット `07dae7ec54b56bf795f67c52308e20ef2f0acc62`。命令を tree-sitter により構文木、すなわち命令の構造として解析する判断層と、`sandbox-runtime` による OS の強制層を持つ。プロジェクトの追加設定は制限を厳しくする方向だけで併合する。公式の簡単な正規表現例より広いが、変数で組み立てた命令・ファイル内スクリプト等の解析限界は著者が明記している。

コードでは sandbox が利用できない場合を確認要求へ移し、承認後は隔離なしで実行する。標準ファイルツールは OS 隔離の対象ではない。読取は主に拒否先一覧で制限し、作業フォルダ外の一般読取まで一律禁止するわけではない。個人情報用の採用では確認画面への切替を「隔離が維持された」と扱わない。[外部拡張の方針](https://github.com/wynainfo/pi-permission-modes/blob/07dae7ec54b56bf795f67c52308e20ef2f0acc62/SECURITY.md)、[実行分岐](https://github.com/wynainfo/pi-permission-modes/blob/07dae7ec54b56bf795f67c52308e20ef2f0acc62/src/bash-enforce.ts#L38-L84)、[制限を厳しくする併合](https://github.com/wynainfo/pi-permission-modes/blob/07dae7ec54b56bf795f67c52308e20ef2f0acc62/src/resolve.ts#L72-L114)。

### `pi-permission-system` 0.8.0

固定コミット `9affcc9d1b52cd79b8bb7da2bebb761ac7e5b1d8`。ツール・命令・MCP・技能・作業フォルダ外のアクセスへ許可/質問/拒否の判断を追加し、`tool_call` で実行を拒否する。これは OS の実行隔離ではないと著者が明示する。許可された道具が行える行為を別途制限する必要がある。

任意の診断記録を有効にすると、入力文章・生のツール引数・命令・対象・判断を記録し得る。拒否の監査を追加した結果、別のログに個人情報が複製される点も評価対象となる。MCP 代理ツールの規則と直接登録ツールの規則は別なので、最新版 Pi の標準 MCP で実際に付く `mcp__...` 名に方針が適用されるか確認する。[著者の境界説明](https://github.com/MasuRii/pi-permission-system/blob/9affcc9d1b52cd79b8bb7da2bebb761ac7e5b1d8/README.md#L635-L647)、[拒否の実装](https://github.com/MasuRii/pi-permission-system/blob/9affcc9d1b52cd79b8bb7da2bebb761ac7e5b1d8/src/index.ts#L1949-L1969)、[診断記録の内容](https://github.com/MasuRii/pi-permission-system/blob/9affcc9d1b52cd79b8bb7da2bebb761ac7e5b1d8/README.md#L576-L580)。

## 独立レビューによる改善

[Claude Code 担当の独立レビュー](harness_review_claude_to_pi_20261008.md) の指摘を固定コードで再確認し、ツールの停止と会話全体の終了を区別した。codemode の引数・エラー・details の自動記録、および失敗時に例外本文をモデルへ返す経路を追記し、MCP 環境継承の引用行を修正した。レビュー・改善とも静的照合の範囲であり、実機検証の合格を意味しない。

## 一次資料と固定行参照

各リンクは取得した固定コミットを指定しており、現在の main の変更に追従しない。全体の出典台帳には元ファイルと SHA-256 を収録した。

[SECURITY]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/SECURITY.md#L45-L60
[SEC]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/docs/security.md#L1-L94
[ISO]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/docs/containerization.md#L1-L175
[EXT]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/docs/extensions.md#L138-L150
[TYPES]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/extensions/types.ts#L860-L930
[ARGS]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/extensions/types.ts#L1220-L1230
[RUN]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/extensions/runner.ts#L1183-L1420
[HOOK]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/agent-session.ts#L645-L744
[SDK]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/sdk.ts#L328-L441
[RUNTIME]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/model-runtime.ts#L649-L815
[PATH]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/utils/paths.ts#L103-L107
[BASH]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/tools/bash.ts#L97-L121
[SHELL]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/utils/shell.ts#L138-L149
[READ]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/tools/read.ts#L92-L210
[WRITE]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/tools/write.ts#L24-L91
[EDIT]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/tools/edit.ts#L80-L167
[AUTH]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/auth-storage.ts#L25-L107
[KEY]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/resolve-config-value.ts#L1-L12
[MODEL]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/docs/models.md#L19-L64
[SESS]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/session-manager.ts#L1124-L1188
[SESSDOC]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/docs/sessions.md#L3-L66
[COMP]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/compaction/compaction.ts#L612-L637
[CACHE]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/cache-warmer.ts#L325-L343
[BUG]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/bug-report.ts#L19-L63
[TEMP]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/utils/output-files.ts#L12-L34
[MCP]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/docs/mcp.md#L130-L195
[MCPEXEC]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/mcp/runtime.ts#L100-L122
[STDIO]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/mcp/src/transports/stdio.ts#L90-L103
[OAUTH]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/mcp/src/oauth/callback.ts#L90-L161
[PKCE]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/mcp/src/oauth/flow.ts#L1-L110
[GATE]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/examples/extensions/permission-gate.ts#L1-L34
[PROTECT]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/examples/extensions/protected-paths.ts#L1-L28
[SANDBOX]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/examples/extensions/sandbox/index.ts#L217-L288
[SBDEFAULT]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/examples/extensions/sandbox/index.ts#L57-L110
[GONDOLIN]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/examples/extensions/gondolin/index.ts#L1-L50
[PKG]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/package-manager.ts#L1845-L1865
[CODE]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/codemode/README.md#L1-L94
[VM]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/codemode/src/runtime/worker.ts#L52-L68
[CM]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L46-L54
[CMTOOLS]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L429-L507
[CMODELS]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L626-L728
[REPORT]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/modes/interactive/interactive-mode.ts#L1359-L1376

[LOOP]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/agent/src/agent-loop.ts#L724-L782
[CMERROR]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L303-L313
[CMDETAIL]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L450-L539
[LOOPSAVE]: https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/agent/src/agent-loop.ts#L932-L940
