# 開発用 SDK における個人情報の検査・保存・実行隔離

調査日：2026-10-08。対象は OpenAI Agents Python SDK、LangChain、LangGraph、Deep Agents の公開コードと公式文書。OpenAI の情報は OpenAI Docs の手順を用い、公式の説明を取得したうえで固定コードと照合した。TypeScript 版を同じコードから検証したとは扱わない。

| 対象 | 取得 HEAD | コード内のパッケージ版 |
|---|---|---|
| OpenAI Agents Python SDK | `f007b3fb05e82ef2d2bea5646a0822769a52f7c9` | 0.23.1 |
| LangChain | `1f587e3f4e0b34d67ea83896f74f855ee6ec103f` | `langchain` 1.4.3 |
| LangGraph | `40a2e6d845054cc0cc17a6a169ca6e7394e5231c` | `langgraph` 1.2.14 |
| Deep Agents | `caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b` | `deepagents` 0.7.23 |

全て 2026-10-07 のコミットを取得した。表の版は取得ソース内の値であり、公開済みの最新安定版を独立に証明する表ではない。主要 51 ファイルと公式 HTML 7 件を保存し、[出典台帳](harness_sdk_sources_20261008.json) に SHA-256・固定 URL・取得日を収録した。API 呼出し、依存の導入、実ユーザーの秘密の読取、実機の隔離試験は行っていない。

## 1. 採用判断の要点

検査する SDK、実行する環境、保存する仕組みは別の境界である。SDK に「guardrail」や「sandbox」という名前があっても、個人情報をモデルへ送信しないこと、コマンドから秘密を読めないこと、ログに平文が残らないことを一括して保証しない。

| 領域 | Agents SDK | LangChain / LangGraph / Deep Agents |
|---|---|---|
| モデル前の検査 | 入力 guardrail。既定はモデルと並行、逐次へ変更可能 | `PIIMiddleware.before_model`。既定は入力のみ |
| ツールの実行前後 | FunctionTool 用 guardrail と承認中断。全種類が対象ではない | middleware と ToolNode。人の承認にはチェックポイントを使う |
| 実行中の出力 | 最終出力検査は既に流れた文字を戻さない | 最新 PII middleware は v3 の出力変換・分割検査を持つ |
| 保存暗号化 | `EncryptedSession` を明示使用 | `EncryptedSerializer` を明示使用 |
| 実行隔離 | SandboxAgent で実行先を選ぶ。Unix-local と Docker は異なる | Backend を選ぶ。LocalShellBackend は隔離なし |
| 利用者・案件の分離 | Session ID と context によるアプリ側の設計 | thread ID・store namespace・backend によるアプリ側の設計 |
| 法律に基づく個人情報の判定 | 既定ではない。独自検査器を実装 | 標準の形式検出は法律上の個人情報を網羅しない |

## 2. Agents SDK：入力・最終出力・ツールの検査

### 入力検査は並行が既定

`InputGuardrail.run_in_parallel=True` は、主たるモデル処理と検査を並行に始める。後から tripwire、すなわち拒否判定が成立すると停止させるが、その時点までのモデル送信・費用・実行済みツールの副作用を巻き戻さない。個人情報を外部モデルに渡す前の検査には `run_in_parallel=False` が必要である。検査器そのものが外部モデルであれば、その検査先に原本を送る点も別に評価する。[GUARD]

拒否判定は `InputGuardrailTripwireTriggered` / `OutputGuardrailTripwireTriggered` 等の例外として伝わる。検査関数の例外も伝播し、同じ検査群の残りを取り消して待つ処理がある。Pi の一部の拡張イベントのように例外を記録してそのまま元の値を使う設計とは異なる。ただし、検査より先に始めた処理や副作用は別問題である。[GRUN]

入力 guardrail は引継ぎの最初のエージェントのみ、出力 guardrail は最終出力を作るエージェントのみ。全ての中間モデル呼出し・引継ぎ・ツールをこの二つで検査したとはいえない。これらは検査 API であり、日本の個人情報や機密文脈を判定する規則が初期状態で装備されているわけではない。[GUARD]

### FunctionTool と検査対象外を区別する

ツール入力検査は実行前、出力検査は実行後。`ToolGuardrailFunctionOutput` は、通常許可、内容を拒否して安全なメッセージで続ける `reject_content`、例外で実行を止める `raise_exception` を区別する。出力検査は、既に実行したメール送信やデータ変更を取り消せない。[TOOL]

対象は `FunctionTool` の処理経路である。本版のローカル MCP はサーバー設定の `tool_input_guardrails` / `tool_output_guardrails` を公開ツールへ付けられる。従って「MCP は guardrail に一切非対応」という以前の一般化も正しくない。一方、HostedMCP、WebSearch、FileSearch、CodeInterpreter、画像生成、Computer、Shell、ApplyPatch、LocalShell、handoff 自体はこの FunctionTool 検査経路を使わない。種類ごとの認可点が必要である。[GUARD]

ツール承認を要求した場合、入力検査は既定で承認後・実行直前に行う。`ToolExecutionConfig(pre_approval_tool_input_guardrails=True)` を使うと承認待ちを発行する前にも検査し、承認後に再び検査する。個人情報を承認画面へ表示する前の安全化と、実行直前の最新認可を分けられる。[GUARD]

### 承認は中断・復元する状態

`needs_approval` 等を設定すると、道具を実行せず `interruptions` と `RunState` を返し、アプリが承認・拒否して同じ実行を再開する。一回の call ID の承認と、同じ道具に対して実行中ずっと使う sticky 承認は異なる。後者は直列化した RunState でも引き継がれるため、復元時に利用者・案件・期限を検証する必要がある。HostedMCP の継続承認は server_label と道具名の組で管理する。[APPROVE]

ローカル Shell / ApplyPatch の承認は初期状態で有効ではない。`on_approval` コールバックを置くだけでは要求を有効化しない。`needs_approval` を設定する。SDK は Codex の自動承認レビューを自動継承しない。[APPROVE] [公式 Guardrails and human review](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)。

## 3. Agents SDK：ストリーム出力と拒否後の保存

最終出力 guardrail は完成後に検査する。トークンをそのまま利用者へ流せば、後から拒否しても見せた文字は回収できない。公式のストリーム例も、文字が出た後に検査が発火することを示す。検査済み出力だけを見せたいアプリは、検査完了まで表示を保留するか、各出力経路に検査済みの変換を置く必要がある。[STEX]

最新 SDK は拒否された最終出力の保存に細かな処理を持つ。tripwire が拒否した場合、既に完了したツール呼出し・結果と再現に必要な理由付けを保存対象にし、候補の最終出力を除く。ツール結果がそのまま最終出力になり拒否されたときは、再現に必要な呼出し対を安全に再構成できる場合、結果を `Output withheld by an output guardrail.` という固定の内容に替える。現在応答の guardrail 結果も内容を削る。安全に整形できない形なら現在応答部分を捨てる。[GUARD][BLOCK]

しかし、**検査関数が例外を投げて判定不能になった場合は、tripwire の拒否とは異なり、完成した最終ターンを保存してから例外を表出する**。拒否された結果を安全化する処理があっても、例外・保存障害・取り消しの扱いを個別に設計しなければならない。また結果の置換時にも、再現に必要な関数引数は残る場合がある。元データが引数に入っていれば、それが保存経路である。[GUARD]

`output_guardrail_blocked_message` の独自文字列・同期 formatter は、拒否本文を受け取らないように設計されている。利用者が context 内の秘密をこの formatter でコピーすれば、置換文に漏れる。アプリ側の拒否理由にも生データを含めない。

## 4. Agents SDK：追跡記録と保存暗号化

### 追跡には機密を含む設定が既定

`trace_include_sensitive_data` の既定は true。モデルの入力・出力、関数ツールの入力・出力を追跡に含め得る。`OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=false` 又は RunConfig で切り替える。音声の追跡には別の設定がある。観測記録を止めることとセッション記録を止めることは異なる。[TRDEF][TRACE]

既定の追跡処理器・配信部を登録するため、独自の伏字処理器を `add_trace_processor()` で追加しただけでは既定の外部送信を置き換えない。処理器の例外は独立に捕捉され、後続の配信部が引き続き動ける。強制するなら `set_trace_processors()` で既定を置換し、伏字と送信を同じアプリ所有の配信部にまとめ、伏字失敗時にはそのまとまりを捨てる。[TRSET][TREX][TRACE]

途中で tracing を無効化しても、既に処理器に入った配信待ちの記録は消去されず、flush により送られ得る。ID、名前、任意 metadata、エラー本文にも個人情報を入れない。診断と監査の目的で原本を複製しないことを、単一の入力フラグに依存させない。[TRACE]

### `EncryptedSession`

これは保存先 Session を包む暗号化機構である。高い乱数性を持つ秘密鍵と Session ID から HKDF-SHA256 でセッション別の鍵を導き、Fernet による認証付き暗号化でメッセージを保管する。読み出すと復号し、通常の処理へ平文を返す。従って保存時の保護であり、モデルへの送信を暗号文だけで行う機構ではない。[CRYPT]

再起動後は同じ鍵と Session ID が必要。低い乱数性のパスワードを使っても HKDF が強固な鍵へ変えるわけではない。現在版は平文・不完全な暗号包みを読み出し時に飛ばし、自動移行しない。期限 TTL を過ぎると復元対象から外すが、期限切れの原本は保存先に残る。特定の自動圧縮経路で期限切れ先頭を回収する処理はあるものの、TTL を全保存先の物理削除保証と説明しない。[CRYPT]

鍵保管サービス、鍵の更新、バックアップ削除、利用者認可はアプリの責任である。暗号化されるメッセージと、Session ID 等の周辺 metadata の保護を区別する。

## 5. Agents SDK：SandboxAgent の実行先による差

SandboxAgent は通常の Agent のモデル・引継ぎ・MCP・検査を持ちながら、道具を実行する作業環境を別に選ぶ。管理側にはモデル認証、承認、実行状態を残し、計算側にファイル・シェルを渡す構成が可能である。名前だけで全コードが隔離環境に移るわけではなく、独自道具や MCP がどこで実行されるかはアプリが確認する。[SB] [公式 Sandbox Agents](https://developers.openai.com/api/docs/guides/agents/sandboxes)。

| 実行先 | 固定実装で確認した境界 | 注意点 |
|---|---|---|
| Unix-local / Linux | コマンドの OS 隔離を追加しない | 作業フォルダ・HOME 指定はアクセス可能範囲の拒否ではない |
| Unix-local / macOS | `sandbox-exec` によりファイル制限を付ける | 通信は隔離しない。実行部がない場合にはエラーにする |
| Docker | コンテナで実行。`network_mode="none"` を設定可能 | 未指定のネットワークまで禁止したと想定しない。共有領域・能力追加を確認 |
| 外部の実行サービス | 各サービスの実行基盤に依存 | SDK のクライアント抽象だけから強度を証明しない |

Unix-local は `inherit_host_environment=True` が既定。false にすると許可した環境変数だけに絞れる。manifest の環境変数はその後から追加・上書きされる。Linux では絞ってもファイルや通信の OS 制限にはならない。[UNIX][UNENV]

Docker の manifest に FUSE を必要とする記憶領域のマウント等があると `/dev/fuse`、`SYS_ADMIN`、`apparmor:unconfined` を追加する経路がある。FUSE なしの SYS_ADMIN 要求も別に扱う。通常のコンテナとこうした権限追加構成は同じ強さではない。個人情報用途は必要性・共有元・読取専用条件を検証する。[DOCK]

`SandboxPathGrant` は追加領域への read_only、Docker 専用の host_path 等を持つ。manifest の `ephemeral` は保存時に残さないための印であり、生きている実行環境から値を見せない機能ではない。snapshot、Session 状態、memory の保存はそれぞれ確認する。[GRANT][MAN]

sandbox memory は会話 Session と別の仕組みで、会話の原記録、要約、生の記憶、整理した指示等を作業フォルダへ作る。個人情報が会話から記憶ファイルへ移る経路を持つため、圧縮されたことを匿名化されたことと扱わない。[MEM]

## 6. 引継ぎ・MCP・アプリの認可

handoff は既定で、それまでの会話履歴を次のエージェントへ渡す。`input_filter`、引継ぎ履歴の整理、又は明示入力の agent-as-tool を使えば範囲を縮められる。`is_enabled` はツールの候補をモデルへ提示する前の判定であり、モデルがその後作る引数内の対象資源を認可するものではない。引数依存の認可は `on_handoff` の最初に置き、許されなければ例外で止める。[HAND]

アプリの context は通常のモデル入力として自動送信されず、ツール・hooks が扱う局所状態である。この方法で鍵・利用者情報をプロンプトから分離できる。しかしツールが context から秘密を読んで返せば漏洩するため、「非公開引数」だけで能力を安全にしたとはいえない。[CTX]

MCP・外部モデル・組込み検索・独自 HTTP 通信には各サービスで使う認証とデータ認可が必要である。検査済み関数ツールだけを作っても、別の道具が同じデータへ直接アクセスできれば統一的な送信方針にはならない。

## 7. LangChain：標準の形式検出と streaming の新しい処理

`PIIMiddleware` は、メール、クレジットカード番号、IP、MAC アドレス、URL の検出を持つ。カードには Luhn、IP には標準の形式検証を使う。独自関数・正規表現を足せる。拒否、全置換、部分伏字、ハッシュを選ぶ。初期値は入力 true、出力 false、ツール結果 false。氏名・日本の個人識別符号・診断文脈を網羅するモデルではない。[PII]

`hash` は対象文字列の SHA-256 の先頭 8 桁に置換する、秘密鍵なしの決定的な処理である。候補辞書から照合しやすく、短い値の衝突もあり得る。法的な匿名化、あるいは秘密鍵で保護したトークン化と同一にしない。[HASH]

### 検査対象と時点

`before_model` の入力検査は最後の HumanMessage の content、結果検査は最後の AIMessage より後の ToolMessage の content が対象である。システム指示、古い履歴、任意 context、画像内文字、独自 metadata まで一律に走査するものではない。`after_model` の永続状態側の出力処理も AIMessage の content を変えるコードであり、別属性の tool_calls の引数をこれだけで安全化したと扱わない。[PIIBEF][PIIAFT]

最新の取得版は v3 のストリーム変換器も持つ。最後の 128 文字を一時保持して複数の断片にまたがる検出を行い、AI の文字・理由付け、ツール引数の公開イベント、ツールの出力・失敗、values の状態表示を変換する。これにより「最終検査まで利用者へそのまま送る」という以前の弱点に対する実装がある。v3 の出力面と通常の古い stream/callback を混同しない。[PIIWIRE]

**表示の伏字と実行の認可は別である。** ストリーム変換は公開イベントのコピーを変更し、元の graph 状態をそのまま残す部分がある。承認画面が伏字でも、実際のツール引数・送信先が安全になったとはいえない。長い独自形式が 128 文字の窓を超える場合、標準で検出できない形式、検出器自身の例外も別途評価する。確認したコードの存在を全日本語 PII の検出精度の保証に変換しない。[PIIWIRE][PIIAFT]

## 8. LangChain の人による審査と LangGraph の保存

HumanInTheLoopMiddleware はモデルが作った道具呼出しを実行前に中断し、人が approve / edit / reject / respond を返せる。対象の `interrupt_on` 規則を指定する。継続には LangGraph のチェックポイント、つまり中断時の状態の保存と安定した thread ID が必要である。承認者の本人確認と対象状態の所有権を SDK が代わりに確立するわけではない。[HITL]

最新実装は、人が編集した呼出しと実際に実行した道具・引数を対応させ、結果へその変更の案内を付ける。これは承認された内容と実行内容の取り違えを抑える処理であるが、編集後の対象・引数も業務の認可条件と照合する必要がある。[HEDIT]

ToolRuntime は state、context、config、store、stream_writer、tool_call_id をモデルが決める通常引数と分離して注入する。注入引数をモデル提示の型から除き、モデルが同名値を渡しても注入値へ置き換える仕組みがある。これを利用者の認可情報の受渡しに使えるが、道具コード自体が安全に使う必要がある。[RUNT][INJECT]

### チェックポイント暗号化の境界

LangGraph の `EncryptedSerializer` は型付きの保存内容を暗号化し、AES-EAX による暗号化と改ざん検証を利用できる。鍵は `LANGGRAPH_AES_KEY` 又は明示値で渡す。復元時に平文へ戻すため、実行中やモデル宛て通信の保護ではない。[LCRYPT]

本版の `loads_typed()` は型名に `+` がなければ平文として基礎 serializer へ渡す。Agents SDK の EncryptedSession が認証済み暗号包みだけを読む設計と異なり、暗号化ラッパーを付けたことだけで平文の既存記録を拒否するとはいえない。[LCRYPT]

また SQLite の保存実装では checkpoint 本文は指定 serializer、metadata は別の `json.dumps` を使う。暗号化 serializer を指定しても、thread ID、checkpoint ID、metadata まで暗号化するとは扱わない。利用者名や個人情報を識別子・metadata に使わない。[CHECK]

データベースを読む権限と、復元される Python オブジェクトの安全性も別の問題である。JsonPlusSerializer はチェックポイント保存器内の信頼済みデータ用で、データベースへ直接書ける攻撃者がいると復元時のコード実行につながり得るとの注意を持つ。現在のコードは msgpack の型許可範囲が既定で広く、`LANGGRAPH_STRICT_MSGPACK=true` 又は明示許可一覧で絞れる。`pickle_fallback` の既定は false。特定 CVE の再現としてではなく、現在コードの信頼境界として採用する。[SERDE]

thread ID と store namespace はデータの区分名であって、利用者の本人確認・アクセス制御そのものではない。Web アプリは外部から渡された ID の所有権を確認してから graph の復元や store 読取へ使う。

## 9. Deep Agents：backend と権限設定

Deep Agents は LangChain の agent と LangGraph の状態実行の上に、ファイル・計画・補助エージェント・圧縮等を組み合わせる。標準の backend は StateBackend、つまり状態内の仮想ファイルである。共有の長期保存、ローカルファイル、コンテナ等は差替えで選ぶ。[DGRAPH]

| backend | 何を保存・実行するか | 境界 |
|---|---|---|
| StateBackend | graph の状態の仮想ファイル | ホスト OS のファイルを直接開かない。チェックポイントに内容は残り得る |
| StoreBackend | LangGraph の永続 store | namespace の設計・store 認可が必要 |
| FilesystemBackend | ホストのファイル | 既定 virtual_mode は実体パスの根を確認するが、プロセス隔離ではない |
| LocalShellBackend | ホストのファイルとシェル | 隔離なし。ファイル方針をシェルで回避できる |
| BaseSandbox の具体実装 | サービス・コンテナ等の計算環境 | 実際の execute / upload / download と環境側の制限で決まる |
| CompositeBackend | パスごとに複数 backend へ振分け | 振分けは保管場所の選択であり、全体の最小権限を自動保証しない |

FilesystemBackend の現在の `virtual_mode=True` は、`..` 等を拒否し、パスを resolve した後に root 配下かを確認する。古い版や false 設定の無制限パスと同一にしない。false では絶対パスを許し、相対パスの基準だけを root に置く。いずれも OS が同じプロセスへ強制する境界ではない。[DFILE]

LocalShellBackend の名前に内部 ID として sandbox が使われても、コードは無制限のホストシェル実行と明記する。環境継承の既定は `inherit_env=False` で、明示の env がなければ空の環境を作る。この点は Pi や Agents Unix-local の既定全継承と異なる。ただしホスト権限・アクセス可能なディスク・ネットワークは別に残る。[DSHELL][DSENV]

### 新しいファイル権限設定

対象版は FilesystemPermission を持ち、操作・パスに allow / deny / interrupt を指定できる。**最初に合致した規則が勝ち、未一致は allow**。ルールを置いたことだけで全件拒否にはならない。interrupt は HITL による確認に接続する。これらの規則はファイルツールの機構であり、LocalShellBackend の任意コマンドを OS で制限する機構ではない。[DPERM]

補助エージェントは、設定がなければ親のファイル権限を継承するが、個別の権限があればそちらを優先する。親の厳しい制限を子が緩められない中央の上限規則と同一には扱わない。また標準の補助エージェントは依頼本文だけの会話で、fork を選べば親の履歴を継承する。この「会話文脈の分離」と、共有した backend のデータ認可を分ける。[DGRAPH][DSUB]

BaseSandbox は抽象的な実行経路で、読取・検索等も execute によるコマンド、書込は upload_files、編集は実行側の処理で行う。従って各具体環境の通信、マウント、秘密、寿命、資源制限をレビューする必要がある。backend を任意の利用者間で使い回す場合、thread ID が異なるだけでその環境のファイルを分離したとはいえない。[DSBOX]

## 10. 個人情報を扱うハーネスへの設計条件

以下は SDK 既定の保証ではなく、本調査からの設計提案である。

1. 原本の形式検出と本人への対応判断を、外部モデル送信前の局所サービスへ置く。氏名だけでなく照合表・業務文脈を持つ分類にする。
2. 検査の並行実行、最終出力だけの検査、公開画面だけの伏字を別々の目的として扱う。厳密な送信禁止では原本を送る処理より先に判定する。
3. ツールの宛先・引数・本人・案件を実行前に認可する。結果・失敗文・structured output・途中経過・追跡・保存前の検査点も用意する。
4. 暗号化 Session / checkpoint を採用し、鍵と認可をアプリ側へ置く。復元時の平文、metadata、圧縮・memory・snapshot・バックアップへ同じ保持方針を適用する。
5. 実行基盤へ本物のモデルキーを渡さず、宛先と操作を限定した認証仲介を使う。モデル・補助分類・MCP・観測記録の全通信先を分けて台帳にする。
6. 道具の OS 制限を実装する環境を選び、隔離失敗時は制限なし実行へ戻さない。SDK の設定と管理者の変更不能な上限方針を分ける。

| 受入試験 | 確認する対象 |
|---|---|
| 拒否・例外・時間切れ・非対話・検査の取り消し | 実行停止、モデル送信、保存、既に流れた文字 |
| 分割メール、長い独自識別子、画像、tool_calls、例外文 | 入力・公開イベント・実際の実行引数の差 |
| 承認前後のデータ変更、復元、継続承認 | 承認対象の最新性と利用者・案件の一致 |
| チェックポイント本文・metadata・ID・trace | 暗号化と伏字の範囲、既定配信部の残存 |
| Linux Unix-local、macOS、Docker network none、マウント | 説明どおりの OS 制約と権限追加時の差 |
| 複数案件・子エージェント・共有 backend | 情報と権限が案件間・親子間で流れないこと |

これらは実装後の試験要件であり、今回実行済み・合格済みの一覧ではない。

## 一次資料の固定参照

[GUARD]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/docs/guardrails.md#L3-L78
[GRUN]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/run_internal/guardrails.py#L120-L223
[TOOL]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/tool_guardrails.py#L39-L99
[APPROVE]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/docs/human_in_the_loop.md#L8-L39
[TRACE]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/docs/tracing.md#L143-L173
[TRDEF]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/run_config.py#L53-L58
[TREX]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/tracing/provider.py#L117-L175
[TRSET]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/tracing/setup.py#L37-L62
[CRYPT]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/extensions/memory/encrypt_session.py#L69-L175
[BLOCK]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/run_internal/blocked_output.py#L164-L191
[STEX]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/examples/agent_patterns/streaming_guardrails.py#L9-L17
[HAND]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/docs/handoffs.md#L88-L116
[CTX]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/docs/context.md#L1-L48
[SB]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/docs/sandbox/clients.md#L1-L80
[UNIX]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/sandbox/sandboxes/unix_local.py#L737-L779
[UNENV]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/sandbox/sandboxes/unix_local.py#L1520-L1559
[DOCK]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/sandbox/sandboxes/docker.py#L1861-L1907
[GRANT]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/sandbox/workspace_paths.py#L204-L213
[MAN]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/src/agents/sandbox/manifest.py#L163-L168
[MEM]: https://github.com/openai/openai-agents-python/blob/f007b3fb05e82ef2d2bea5646a0822769a52f7c9/docs/sandbox/memory.md#L1-L100
[PII]: https://github.com/langchain-ai/langchain/blob/1f587e3f4e0b34d67ea83896f74f855ee6ec103f/libs/langchain_v1/langchain/agents/middleware/pii.py#L492-L566
[PIIWIRE]: https://github.com/langchain-ai/langchain/blob/1f587e3f4e0b34d67ea83896f74f855ee6ec103f/libs/langchain_v1/langchain/agents/middleware/pii.py#L38-L112
[PIIBEF]: https://github.com/langchain-ai/langchain/blob/1f587e3f4e0b34d67ea83896f74f855ee6ec103f/libs/langchain_v1/langchain/agents/middleware/pii.py#L699-L778
[PIIAFT]: https://github.com/langchain-ai/langchain/blob/1f587e3f4e0b34d67ea83896f74f855ee6ec103f/libs/langchain_v1/langchain/agents/middleware/pii.py#L800-L846
[HASH]: https://github.com/langchain-ai/langchain/blob/1f587e3f4e0b34d67ea83896f74f855ee6ec103f/libs/langchain_v1/langchain/agents/middleware/_redaction.py#L297-L334
[HITL]: https://github.com/langchain-ai/langchain/blob/1f587e3f4e0b34d67ea83896f74f855ee6ec103f/libs/langchain_v1/langchain/agents/middleware/human_in_the_loop.py#L247-L271
[HEDIT]: https://github.com/langchain-ai/langchain/blob/1f587e3f4e0b34d67ea83896f74f855ee6ec103f/libs/langchain_v1/langchain/agents/middleware/human_in_the_loop.py#L541-L680
[LCRYPT]: https://github.com/langchain-ai/langgraph/blob/40a2e6d845054cc0cc17a6a169ca6e7394e5231c/libs/checkpoint/langgraph/checkpoint/serde/encrypted.py#L1-L80
[CHECK]: https://github.com/langchain-ai/langgraph/blob/40a2e6d845054cc0cc17a6a169ca6e7394e5231c/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py#L425-L449
[SERDE]: https://github.com/langchain-ai/langgraph/blob/40a2e6d845054cc0cc17a6a169ca6e7394e5231c/libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py#L85-L125
[RUNT]: https://github.com/langchain-ai/langgraph/blob/40a2e6d845054cc0cc17a6a169ca6e7394e5231c/libs/prebuilt/langgraph/prebuilt/tool_node.py#L1662-L1690
[INJECT]: https://github.com/langchain-ai/langgraph/blob/40a2e6d845054cc0cc17a6a169ca6e7394e5231c/libs/prebuilt/langgraph/prebuilt/tool_node.py#L1380-L1429
[DFILE]: https://github.com/langchain-ai/deepagents/blob/caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b/libs/deepagents/deepagents/backends/filesystem.py#L132-L223
[DSHELL]: https://github.com/langchain-ai/deepagents/blob/caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b/libs/deepagents/deepagents/backends/local_shell.py#L1-L90
[DSENV]: https://github.com/langchain-ai/deepagents/blob/caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b/libs/deepagents/deepagents/backends/local_shell.py#L110-L203
[DSBOX]: https://github.com/langchain-ai/deepagents/blob/caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b/libs/deepagents/deepagents/backends/sandbox.py#L1-L15
[DPERM]: https://github.com/langchain-ai/deepagents/blob/caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b/libs/deepagents/deepagents/middleware/filesystem.py#L365-L413
[DGRAPH]: https://github.com/langchain-ai/deepagents/blob/caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b/libs/deepagents/deepagents/graph.py#L646-L714
[DSUB]: https://github.com/langchain-ai/deepagents/blob/caaa7e7c12d214afa5cf0a1afed8eb6232aa6f7b/libs/deepagents/deepagents/middleware/subagents.py#L76-L119

## 独立レビュー

[親担当による原本照合](harness_review_root_to_sdk_20261008.md)で、入力並行実行、拒否・例外後の保存、追跡配信、Unix-localの隔離範囲、逐次出力のコピー、保存暗号化、ファイル権限の優先順位を確認した。重要な修正要求はなかった。
