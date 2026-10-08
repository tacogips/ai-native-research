# OSS coding harnessの機密情報・権限・隔離機構の比較

調査日: 2026-10-08。対象はOpenCode、Gemini CLI、OpenHandsとSoftware Agent SDK、Aider、Goose、Cline、Roo Code。ハーネスとは、モデルへの入力構築、道具実行、承認、履歴保存などを制御する周辺プログラムを指す。公開一次資料と固定コミットの実装を読む静的調査であり、製品を起動して隔離突破を試す実験は実施していない。

## 結論と設計上の区別

**承認画面・ファイル除外・危険性判定・OS隔離・送信制御は別の機構である。** シェルを許可したら、専用read道具の拒否だけでは、そのプロセスによるファイル読取や通信を止められない。読取専用でマウントしても内容の読取は可能である。コンテナ内で読み取った内容をモデルへ送れば、ホスト隔離が機密の外部送信まで防いだことにはならない。

一次実装を参考にした設計上の推論として、個人情報を扱う自作ハーネスでは、①文脈の取込み、②道具実行、③OSによる資源アクセス、④ネットワーク送信、⑤モデル/検出器への要求、⑥秘密の供給、⑦履歴/観測情報保存、⑧企業設定と更新の強制を独立に設計する必要がある。以下では「実装あり」と「適切な設定なら保護」と「調査範囲で未確認」を区別する。

## 固定した調査対象

HEADは調査時に取得した開発ブランチ先端であり、公開安定版と同じとは限らない。AiderとRoo Codeはこの取得時点でHEADの日付が2026年5月だった。「古いから安全/危険」「開発HEADの機構が全導入版にある」とは推定しない。

| 対象 | 固定コミット | コミット時刻（UTC） |
|---|---|---|
| opencode | `a697115b203395c54a7496dc3d1863fe7b319c0c` | 2026-10-07T19:19:04Z |
| gemini_cli | `44d764ee579610bf73c43107f5e0422cd92588b9` | 2026-10-07T22:00:33Z |
| openhands | `3f98684763a4e17e6e2faf8dd8f1cfc3969b020c` | 2026-10-07T19:58:40Z |
| aider | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` | 2026-05-22T14:02:20Z |
| goose | `9560429ff982bbfecec5094963e5f34696b63a1c` | 2026-10-07T20:48:23Z |
| cline | `faf05ef067dd4f5908c9e909dd757581089905ca` | 2026-10-07T22:54:57Z |
| roo_code | `b867ec9145750d0ae1ff7f02d35406e9bf2a0b16` | 2026-05-15T18:04:45Z |
| openhands_sdk | `69e26889401fe69157fff536e6a69049e6644cb3` | 2026-10-07T16:46:12Z |

## 強制点の比較

| 対象 | ハーネス内の承認/拒否 | OS隔離の位置 | 機密の取込み・送信の注意 |
|---|---|---|---|
| OpenCode | action/resourceのallow/ask/deny、外部ディレクトリ、道具単位 | 標準でOS sandboxなし。利用者がDocker/VM等を外付け | read拒否とshell権限は別。MCPは外部信頼境界 |
| Gemini CLI | policy engine、信頼フォルダ、道具承認、権限拡張 | 起動時Docker/Podman/Seatbelt等に加え、HEADの道具実行時Linux bwrap/macOS Seatbelt/Windows低権限実装 | 除外対象を尊重する道具と任意シェルは別。道具通信を閉じてもモデル要求は別経路 |
| OpenHands SDK | risk analyzerとconfirmation policyを別設定 | LocalWorkspaceはローカル。DockerWorkspace/遠隔workspaceを選択 | 登録secretの遅延取得、実行時注入、出力mask。一般PII全体を自動秘匿する保証はない |
| Aider | ファイル追加/変更/コマンド等の確認、Git変更管理 | Docker利用は明示的な起動方法。通常起動のOS隔離は確認できず | 選択ファイル、リポジトリ要約、コマンド結果がモデル入力になる |
| Goose | autonomous/approve/smart_approve/chat、道具ごとの規則、任意の検出器 | Goose全体をDocker内で起動、または拡張のみ既存コンテナで起動 | 危険性分類用外部endpointも新たなデータ送信先。MCPは独立実装 |
| Cline | SDK toolPolicies、承認callback、PreToolUse等の差込み処理 | `SubprocessSandbox`は子プロセス/IPC。OS資源隔離の証拠にはならない | 旧.clineignoreと代替hookは異なる。企業制限はCLI/Desktopに一律適用されない |
| Roo Code | auto approval、command許否prefix、MCP道具承認、.rooignore | .rooignoreはOS sandboxではないと一次docsが明記 | 一部既知readコマンド検査のみ。任意scriptは別の境界 |

## OpenCode: 権限を隔離と取り違えない

[固定版のSECURITY.md](https://github.com/anomalyco/opencode/blob/a697115b203395c54a7496dc3d1863fe7b319c0c/SECURITY.md)は、標準のagentをsandbox化していない、承認は操作把握のための機能でありセキュリティ隔離ではない、真の隔離にはDockerまたはVMを使う、と明示している。MCPサーバの挙動はOpenCodeの信頼境界の外として扱う。この明示は、他製品の「sandbox」という名称も強制点で検証する必要がある根拠になる。

V2の公式docsでは`permissions`配列と`action/resource/effect`を使い、`shell`、`subagent`を指定する。旧V1の`permission`、`bash`、`task`と混ぜない。公開Web資料は更新されるため、固定sourceではV1/V2が併存することも確認した。単一の規則列では後に一致したものが優先される。ただしV2の`evaluateInput`は設定済みagent規則にdenyがあるかを先に調べ、denyなら保存済み承認allowを足す前に拒否する。その後に設定列と保存済みallowを合成し、複数resourceはdeny→ask→allowで集約する。保存済み承認で設定denyを解除できるという意味ではない。read、edit、外部directory、shell、MCP tool、Code Modeのexecuteは別の権限である。V2の基本方針は多くの操作allow、外部directory ask、`.env`系read ask、`.env.example`allow。古い記事の「.envは標準deny」を現行V2に持ち込まない。[V2 permission実装](https://github.com/anomalyco/opencode/blob/a697115b203395c54a7496dc3d1863fe7b319c0c/packages/core/src/permission.ts)、[公式V2 permissions](https://opencode.ai/v2/docs/permissions)。

**固定HEADはV1/V2移行中で、Web docsとcoreの実装に差がある。** 旧`packages/opencode/src/tool/shell.ts`はtree-sitter等で複合commandと利用directoryを推定して承認を要求し、`process.env`とplugin追加envを合成する。一方、V2 `packages/core/src/tool/bash.ts`はminimal shell boundaryと明記し、tree-sitter/PowerShell parser、command prefix承認、plugin shell.env移植等がTODO。実分岐は外部workdir承認とcommand全体へのpermissionを行うが、command引数のdirectory検出は単語照合による**警告のみ**である。従ってWeb V2 docsのscanner説明が固定coreや配布製品の全経路で実現済みとは言えない。双方ともOSがreadを遮断する機構ではなく、利用者の権限で子が動く。[シェル推定・承認・環境変数・実行](https://github.com/anomalyco/opencode/blob/a697115b203395c54a7496dc3d1863fe7b319c0c/packages/opencode/src/tool/shell.ts)。 [V2 coreのTODOと警告のみのpath検査](https://github.com/anomalyco/opencode/blob/a697115b203395c54a7496dc3d1863fe7b319c0c/packages/core/src/tool/bash.ts)。

子agentの規則継承も版差がある。旧subagent-permissionsは親のdenyとexternal_directoryをコピーする一方、公開V2 docsではcustom子が自身のpermissionを使い、親のsubsetである保証をしない。子に親以上の権限を与えない要件は、自作ハーネスで明示的な集合の共通部分として強制する必要がある。[旧子規則](https://github.com/anomalyco/opencode/blob/a697115b203395c54a7496dc3d1863fe7b319c0c/packages/opencode/src/agent/subagent-permissions.ts)、[V2子設定](https://opencode.ai/v2/docs/permissions#agents)。

資格情報はV2でSQLiteの`credential.value` JSON列に保存され、取得時にschema変換する。本調査で読んだcredential経路には、保存前暗号化・復号操作は見つからなかった。これは「OS/ディスク全体にも暗号化がない」とする断定ではない。モデル資格情報を安全に保管することと、道具の親環境から秘密を隠すことは別に検証する。[資格情報schema](https://github.com/anomalyco/opencode/blob/a697115b203395c54a7496dc3d1863fe7b319c0c/packages/core/src/credential/sql.ts)、[資格情報保存/取得](https://github.com/anomalyco/opencode/blob/a697115b203395c54a7496dc3d1863fe7b319c0c/packages/core/src/credential.ts)。

専用readは個別permissionを照会するが、全モデル送信内容を一括で個人情報分類・置換するDLP（情報の外部流出防止）処理はこの調査経路では確認できなかった。MCP/pluginは別プロセス・外部サービス・任意のコード実行があり、許可済みの道具名だけでは応答や副作用を安全と判定できない。履歴・共有・デバッグ記録も別の保存経路として導入設定を監査する。

## Gemini CLI: 起動時隔離と道具実行時隔離を区別

[固定版sandbox docs](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/docs/cli/sandbox.md)と[CLI起動処理](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/cli/src/utils/sandbox.ts)では、起動時のSeatbelt、Docker/Podman、gVisor/runsc、LXC、Windows native方式を扱う。既定Seatbelt `permissive-open`は広いreadとnetworkを許すwrite制限中心であり、機密不可視とは言えない。`strict-*`や`*-proxied`でread範囲/代理通信へ変える場合も、実際のprofileと例外を確認する。Dockerでworkspaceを同じ絶対pathにmountし、`SANDBOX_MOUNTS/ENV/PORTS`で境界が広がる。runscはLinuxで明示選択、LXCは既存環境が必要である。

HEADには別の道具実行層がある。`Config`から`createSandboxManager`を呼び、enabled時に`SandboxedFileSystemService`を配線する。OSによりLinux/macOS/Windowsのmanagerを選び、無効なら`NoopSandboxManager`、未対応OSは`LocalSandboxManager`を返す。後者の未実装道具sandbox経路は例外を投げる。実際の有効化は`params.sandbox`と`toolSandboxing`等の設定に依存する。単にsourceに存在するだけで、全安定版・全起動方法で有効とは断定しない。[Configの実配線](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/config/config.ts)、[OS分岐](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/services/sandboxManagerFactory.ts)、[manager・秘密ファイルの定義](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/services/sandboxManager.ts)。

Linuxではbwrapがmount/process/session/network等の名前空間を分離する。`--unshare-all --new-session --die-with-parent`、独立`/proc`、一時`/tmp`を使う一方、基底には**`--ro-bind / /`**があり、read-onlyなホストrootを見せる。その上でworkspace書込、禁止pathを空directoryや`/dev/null`で隠す、`.env/.env.*`mask等を重ねる。従って「bwrapだからホスト全体を読めない」は誤り。network許可時は`--share-net`になる。seccomp（Linuxのシステム呼出しフィルタ）は実装上architecture確認と`ptrace`拒否を行い、残りの呼出しを許す限定的なもの。[bwrap引数とmask](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/sandbox/linux/bwrapArgsBuilder.ts)、[Linux実行とseccomp](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/sandbox/linux/LinuxSandboxManager.ts)。

mask探索範囲・深さ・実path/別名・新規作成時期も確認が必要である。定義のコメントではgovernance fileをwrite protectするとあるが、builderの実分岐はworkspace書込可なら`.gitignore/.geminiignore`の変更を既定で許す一方`.git`は別扱い。コメントより実分岐を優先して評価する。

macOSはSeatbeltの原則拒否profileにOS動作に必要な例外を重ねる。network-enabled profileではoutboundだけでなくinbound/bindも許すため、「インターネットだけ許す」の意味ではない。Windowsはネイティブの低権限token/integrity等を使うsourceがあり、host filesystemへの低integrity付与の影響もある。これらはLinuxのnamespace隔離と同一の性質ではない。[Seatbelt基本例外とnetwork](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/sandbox/macos/baseProfile.ts)、[Windows native helper](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/sandbox/windows/GeminiSandbox.cs)。

policyのplan/default/accepting_editsではnetwork=false等があるが、明示承認・追加permission・YOLO modeなどで広がる。CLI起動設定のnetworkAccess defaultと道具mode方針も別値である。承認拡張を認める場合、恒久許可と一回限り許可、表示する対象、再実行時の範囲を監査する。設定したsandbox binaryがない場合はCLI設定でFatalSandboxErrorとなる。silentな非隔離再実行を許さない設計の参考になる。[mode規則](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/policy/policies/sandbox-default.toml)、[検出・無効化・起動失敗](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/cli/src/config/sandboxConfig.ts)。

環境変数は専用sanitize処理で削除する。allow/blockリスト、名前/値に基づく判定、GitHub実行時の厳格化があり、redaction無効・厳格モードでない場合は全envを返す。Noop sandboxもsanitizeを通すが、それをOS隔離とみなせない。フォルダ信頼・MCP・hookの信頼は別層。`.geminiignore`は尊重する道具と`@`取込みの除外であり、任意シェルへの包括read denyではない。[環境変数除去](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/packages/core/src/services/environmentSanitization.ts)、[フォルダ信頼](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/docs/cli/trusted-folders.md)、[除外対象](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/docs/cli/gemini-ignore.md)。

モデル要求と運用telemetry（使用状況の記録）はtool sandboxのnetwork制限とは別に存在する。telemetryのprompt記録設定、出力先、exporter、保存期限を別に確認する。[telemetry設定](https://github.com/google-gemini/gemini-cli/blob/44d764ee579610bf73c43107f5e0422cd92588b9/docs/cli/telemetry.md)。

## OpenHands: workspace選択、登録secret、危険性判定を組み合わせる

2026年HEADのOpenHands本体はUI/サービス連携中心であり、実行の詳細はSoftware Agent SDKを別固定コミットで調査した。旧V0のruntime設定をV1へそのまま適用しない。SDKはLocalWorkspace/RemoteWorkspaceを抽象化し、DockerWorkspaceではagent-serverをcontainer内で起動してHTTP経由で道具を実行する。**LocalWorkspaceを選べば同じSDKでもホストで動く。** DockerWorkspaceは追加volumesとnetworkを設定でき、forward_envは既定でDEBUG/セッション認証値に限定するが、追加値で境界が広がる。既定network=NoneはDocker標準通信であり、通信禁止を意味しない。[ローカルworkspace](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-sdk/openhands/sdk/workspace/local.py)、[DockerWorkspace](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-workspace/openhands/workspace/docker/workspace.py)。

特に参考になるのはSecretRegistryである。モデルにはsecret名/説明を示し、command内に登録名があれば、実行直前にStaticSecret/LookupSecret等から原値を取得して環境変数として注入する。実行結果に原値が出ても`<secret-hidden>`へ置換する。stream出力では秘密がchunk境界をまたいでも検出できるよう、最長secret長に応じた末尾を保留してから出す。取得した値を追跡することで、後続取得に失敗しても過去の値をmaskできる。[SecretRegistryとstream mask](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-sdk/openhands/sdk/conversation/secret_registry.py)、[実行時供給の例](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/examples/01_standalone_sdk/12_custom_secrets.py)。

これは「モデルが平文secretを知らずに操作する」具体例だが、処理する道具プロセスは平文を受け取る。**安全な資格情報仲介と、道具の送信先制限を併用する必要がある。** maskは登録原値の一致を中心とするため、未知の個人情報、分割/符号化/変換されたsecret、画像やopaque payloadの全内容まで自動秘匿する保証ではない。`SkipSecretMasking/PreserveDataUrls`の除外fieldも存在する。secret取得失敗はNone/skip等で扱うので、ハーネス側では取得失敗時に操作を続けてよいかを目的別に決める。

保存時はPydantic SecretStrとcontextによるredact/暗号化を使い、`expose_secrets=True`では平文を出す経路もある。LookupSecret headerの復号失敗時は、利用者意図を理由にplaintext扱いする分岐を確認した。暗号化フラグのみから全面fail-closed（判定不能時は拒否）を想定してはならない。export artifactを別処理でredactするコードもある。[secret sourceとheader例外](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-sdk/openhands/sdk/secret/secrets.py)、[export時秘匿](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-agent-server/openhands/agent_server/_secret_redaction.py)。

危険性判定はLLMSecurityAnalyzer、PatternSecurityAnalyzer、PolicyRailSecurityAnalyzer、Ensemble等がある。LLM analyzerはagent自身が付けるrisk属性を参照するため、独立した強制判定と同じではない。Pattern/PolicyRailはローカル規則・shell構造等を解析する。判定器を付けてもconfirmation policyは変わらないので、AlwaysConfirm/NeverConfirm/ConfirmRiskyを別に選ぶ。ConfirmRiskyのUNKNOWNは既定で確認する。Ensembleは例外をHIGHへ引き上げるが、NeverConfirmならHIGHも自動拒否にならない。UNKNOWNを具体値が存在すれば捨てる既定と、`propagate_unknown=True`も区別する。[モデル自己申告risk](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-sdk/openhands/sdk/security/llm_analyzer.py)、[融合と例外/UNKNOWN](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-sdk/openhands/sdk/security/ensemble.py)、[承認方針](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/openhands-sdk/openhands/sdk/security/confirmation_policy.py)、[多層設定例](https://github.com/OpenHands/software-agent-sdk/blob/69e26889401fe69157fff536e6a69049e6644cb3/examples/01_standalone_sdk/47_defense_in_depth_security.py)。

Apptainer、Kubernetes agent-sandbox、Cloud/remote APIもworkspace実装の選択肢として存在する。ただし、本稿で詳しく追ったのはDocker/Localであり、Cloudの非公開運用、全runtimeの脱出耐性、multi-tenant認証、ブラウザ/VSCode/VNC各portの外部公開安全性は未実験である。container APIに認証値を渡すこと、道具秘密を注入すること、モデルAPI資格情報を渡すことを混同しない。

## Aider: 明示ファイル選択とGitによる復元、隔離は外付け

Aiderはagent道具一般化より、選択ファイルとリポジトリ構造要約をモデルに送って編集する構造が中心。`base_coder.py`はGit-ignoreや`.aiderignore`による選択除外、内容取込み、会話構築、モデル呼出し、lint/test/run結果の反映を扱う。`.aiderignore`が一部取込みを止めても、`run_cmd.py`はsubprocess/pexpectで通常権限のコマンドを実行するのでOS read denyではない。[ファイル選択・会話・道具結果](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py)、[ignoreとGit](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repo.py)、[ローカルcommand実行](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/run_cmd.py)。

公式Docker起動例はworkspace volumeとAPI key引数を与える。`/run`はcontainer内で動くが、volumeに載せたデータは読めるし、標準networkを閉じる例ではない。model要求もcontainerから送る。API keyをcommand引数で渡すことを秘密供給の最良設計とみなさず、process一覧・shell履歴への露出も別に検討する。[Docker起動方法](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/install/docker.md)。

自動Git commit/undoは変更の復元に役立つが、外部送信済みの機密は戻せない。commit message生成にもモデル呼出しがあるため、主モデルへの本文送信だけを監査すればよいわけではない。`InputOutput`はinput history/chat history/任意LLM historyの保存を扱い、append時に内容をファイルへ書く。読んだ保存経路では一般PIIの自動匿名化は確認できない。[履歴書込み](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/io.py)、[commit message生成](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repo.py)。標準MCP server gateway、中央企業policy強制、全送信のPII検出/拒否は今回の主要経路で未確認であり、未確認を不在の網羅的証明としない。

## Goose: 道具権限、検出器、拡張コンテナを別々に選ぶ

公式permission docsでは既定Autonomousである。Approve/Smart Approveには道具ごとのAlwaysAllow/Ask/NeverAllow等があり、read/writeの分類も最善努力でモデル解釈に依存するため、「readだから無害」とは扱わない。Chat Onlyは道具を使わないが、利用者が入力した機密がmodel要求になる点は残る。[permission modes](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/documentation/docs/guides/managing-tools/goose-permissions.md)、[危険性判定](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/crates/goose/src/permission/permission_judge.rs)、[実行承認境界](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/crates/goose/src/agents/state_machine/ops_tool_approval.rs)。

任意のprompt injection（外部文書等に仕込んだ命令でagentを誘導する攻撃）検出機能は、既知patternと機械学習分類器を組み合わせる。固定scannerではshell tool以外は`scanned=false`として対象外になり、threshold既定0.8、会話の走査範囲にも制限がある。分類clientはHTTP POSTで対象textを設定endpointへ送るため、検出器自体が追加の機密送信先になる。利用者は分類器をローカルに置くか、外部送信可能な文面だけを渡すか、契約と経路を別に管理する必要がある。ML初期化に失敗した片方を`.ok()`で落とし、両方不可ならエラーという分岐があり、上位での最終動作まで未確認。[対象・走査・閾値・初期化](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/crates/goose/src/security/scanner.rs)、[分類endpointへのtext送信](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/crates/goose/src/security/classification_client.rs)。

Adversary Modeは別のモデル呼出しで実行予定commandをレビューし、許可/阻止と理由を返す。既定shell対象で同じmodel/providerを使い、`.goose/adversary.md`等の規則を設定する。これは誤判断し得るレビュー層であり、OS隔離やnetwork allowlistを置き換えない。規則に「SSH鍵を読まない」「未承認domainへ送らない」と書いてもOSレベルの強制とは異なる。[Adversary Mode](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/documentation/docs/guides/security/adversary-mode.md)。

Goose全体をDocker内で起動する方法と、host Gooseから`--container`でextensionだけを既存container内で実行する方法がある。後者ではhost本体のprovider通信・履歴・envは同じ隔離内とは限らない。MCP toolがcontainerで動いてもhostの別extension/remote MCPが同じ境界とは限らない。[二種類のDocker配置](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/documentation/docs/tutorials/goose-in-docker.md)。

secret保存は環境変数→system keyring等を使い、keyring無効/featureなしでは`secrets.yaml`file保存へ分岐する。secret fileのアクセスmodeとbackupも監査する。session managerはSQLiteへmessage等を保存するため、モデルへ送らない秘密のつもりでも、道具出力や会話に混入すればローカル履歴に残る可能性がある。[keyringとfile fallback](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/crates/goose/src/config/base.rs)、[session保存](https://github.com/block/goose/blob/9560429ff982bbfecec5094963e5f34696b63a1c/crates/goose/src/session/session_manager.rs)。

## Cline: 新SDKと旧拡張で境界が違う

HEADのSDK toolPoliciesは道具のenabled/autoApproveを制御する。**指定しない道具はenabledかつauto-approved**なので、追加道具/MCP/pluginの導入で既定許可が増えないよう、自作ハーネス側では既定拒否に変える設計が適する。`requestToolApproval`callbackとPreToolUse等の差込み処理を使えるが、それはOS隔離とは別の承認境界。[SDK既定と承認](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/docs/sdk/guides/permission-handling.mdx)、[tool approval実装](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/sdk/packages/core/src/runtime/tools/tool-approval.ts)。

同じ`requestDesktopToolApproval`は承認対象の**生のinput**を`approvalDir/<session>.request.<call>.json`へ書いてから結果を待つ。拒否・timeoutでも送信前の判断ではなく、原文が局所の承認用ファイル/IPCに一度渡る。結果が`approved===true`の場合だけ承認し、未設定・timeoutは拒否、要求fileは通常の完了/timeout後に削除するが、このcleanupを暗号学的な消去や全backupからの削除とはみなせない。承認画面/IPCもPII保存・表示経路として分類し、directoryの権限・例外時の残存・同一利用者の改ざん耐性を別に検証する。

`SubprocessSandbox`というクラスはNode/Bun子プロセスとIPC、timeout/idle終了/再起動を管理する。実際のspawnは`withResolvedClineBuildEnv(process.env)`を渡しており、読んだ実装にSeatbelt、bwrap、namespace、seccomp、低権限token等はない。したがって「プロセス障害の分離」は言えても「filesystem/network権限の隔離」とは言えない。pluginを別processへ逃がすことも同じ区別が必要。[spawnとIPC](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/sdk/packages/core/src/runtime/tools/subprocess-sandbox.ts)、[plugin子プロセス](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/sdk/packages/core/src/extensions/plugin/plugin-sandbox-bootstrap.ts)。

固定docsでは`.clineignore`は廃止方向で、旧機能は自動文脈取込みを減らすものであり、明示`@`アクセスは迂回すると説明する。代替PreToolUse hookはread_files/editor/apply_patch/run_commandsを拒否し、`.clineignore`自体の書換えを止める。Gitのpattern matcherを使い、パスは字句正規化するがsymlinkは解決せず、workspace外は対象外。shellは単語からpathを推測するため任意scriptには完全でない。hookは明示的導入と`jq/git`が必要で、旧拡張ignore controllerがrepoに残ることだけで新SDKに全効力があるとは推定しない。[移行・hook・限界](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/docs/customization/clineignore.mdx)、[代替hook](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/sdk/examples/hooks/PreToolUse_ClineignoreGuard.sh)、[旧拡張controller](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/apps/vscode/src/core/ignore/ClineIgnoreController.ts)。

企業remote configは製品ごとに適用差がある。固定docsの表では許可provider、MCP marketplace/独自MCP/組織MCP、telemetry強制はVS Code/JetBrainsで対応し、CLI/Desktopで同じ制限は保証されない。Admin/Ownerのopt-outも存在する。組織設定をworkspaceの`.cline/enterprise/`や`.cline/remote-config/`へ書き、prompt storage資格情報を含む場合があるため、企業設定自体が機密ファイルになる。[製品別企業制限と設定ファイル](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/docs/enterprise-solutions/configuration/remote-configuration/overview.mdx)。

telemetryは既定onと説明され、通常はcode/file/promptsを含まないが、Cline/ClinePass providerでは要求promptとmodel応答が記録に含まれる例外がある。OFFでもサインイン、設定確認、provider要求の通信は残る。企業管理者がtelemetryをOFFにする制御も全製品共通ではない。従って「telemetry OFF=外部送信なし」「BYOK=自動匿名化」としない。[送信内容と例外](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/docs/enterprise-solutions/monitoring/telemetry.mdx)。checkpointは復元用の別コピーであり、送信済み内容の取消しではない。[checkpoint](https://github.com/cline/cline/blob/faf05ef067dd4f5908c9e909dd757581089905ca/docs/core-workflows/checkpoints.mdx)。

## Roo Code: workspace内の専用道具制御、shellは最善努力

`.rooignore`はread/write/apply_diff等の専用道具とcontext mentionsで確認し、ファイル自身を暗黙にignoreして規則の書換えを防ぐ。変更は監視して再読込する。ただし公式docsはworkspace外には適用されず、execute_commandは既知のfile-reading commandのみ検査し、任意scriptや珍しいutilityは漏れる、OS sandboxではない、と明記する。[.rooignoreの強制範囲と限界](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/apps/docs/docs/features/rooignore.md)、[実装](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/ignore/RooIgnoreController.ts)。

command自動承認はprefix照合とallow/denyの最長一致、複合command parser、危険なparameter/command substitution検出等を使う。単純な`git *`許可を全操作安全の保証にはできない。`NeverAllow`相当のハーネス規則と「自動承認しないので画面で確認」の挙動は違い、手動承認後は通常権限のコマンドが走る。MCPの自動承認は別経路。[prefix・複合command・展開検査](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/auto-approval/commands.ts)、[MCP自動承認](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/core/auto-approval/mcp.ts)。

shadow Git等のcheckpointはworkspace変更の復元に役立つが、履歴コピーの保存境界と秘密除外も必要になる。[shadow checkpoint](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/checkpoints/ShadowCheckpointService.ts)、[checkpoint除外](https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/services/checkpoints/excludes.ts)。モデルproviderの通信とVS Codeの資格情報保存を含む全経路を、この短いignore/approval調査だけで安全と認証していない。RooのHEAD日付が古いことから製品運用終了等は推測しない。

## 個人情報ハーネスに転用する設計と検証例

以下は製品がすべて提供している機能ではなく、上記の強制点と限界から導いた設計提案である。モデルの「機密ではない」という回答だけに依存しない。

| 境界 | 実装すべき制御 | 合成データでの検証例 |
|---|---|---|
| 取込み | 読取前の資源ラベル/利用者権限、読取後でmodel前のPII検出・置換、attachment/画像/OCRも同じ経路へ | 同じ顧客番号が、対応表あり/なしで違う扱いになるか |
| 道具 | 全道具を既定拒否、server/tool/argument/recipientを構造化して許可 | 専用readを拒否したファイルをshell/script/MCPで読み込めないか |
| OS | 必要資源のみを載せたcontainer/VM、非root、書込範囲制限、読みたい秘密を見せないmount | symlink、別名、path traversal、一時file、subprocessでも拒否されるか |
| 送信 | 道具用networkとmodel用networkを分離、宛先allowlist、資格情報付きproxy、DNS/redirect対策 | toolで許可domainから未許可domainへredirectしたとき止まるか |
| secret供給 | modelにはsecret参照のみ、信頼された仲介で限定操作へ供給、短寿命化 | 原値がstdout/stderr・例外・stream境界で返ってもmaskされるか |
| 内容検査 | PIIと企業機密を別判定、外部classifierを新送信先として管理 | 非PIIのAPI key/設計図も外部送信が拒否されるか |
| 保存 | raw/redacted領域分離、ログ最小化、暗号化、期限、checkpoint/exportへの同じ方針 | telemetry、会話要約、Git commit生成、exportへsecretが漏れないか |
| 運用 | 管理者設定をagent/利用者から書換え不可、版固定、承認の対象/期限を固定 | 新MCP道具やsubagent追加で許可が増えないか |
| 失敗 | 検出器不応答・schema不正・sandbox binary欠落で拒否または管理者確認 | timeout時に自動的に非隔離再実行されないか |

**「公開LLMに平文個人情報を渡さない」が目的なら、OS sandboxだけでは達成しない。** raw dataを読む信頼されたローカル分類/検索器と、外部モデルが受け取る置換済み表現を分離し、モデルが呼べる道具にもrawを返さない契約を持たせる。一方、local modelでもhook、MCP、telemetry、package download、tool networkが外部通信すれば全面ローカルとは言えない。

## 調査限界と未検証事項

- 固定HEADの静的sourceと一次docsを調べた。全リリース版の差分史、配布binaryが同じsourceを使うこと、実行環境でのsystem call/HTTP traceは未検証。
- 複数のOSとcontainer設定を実機で起動していない。脱出耐性や安全認証、既知脆弱性の全件調査を主張しない。
- OpenHandsのApptainer/Kubernetes/Cloud/remote運用の全機構、全製品のブラウザ/GUI/plugin/MCPごとの独立コード、全ログcollector、暗号鍵保管のOS別差は詳細不足。調査していない経路に保護を推定しない。
- 企業向け非公開管理面・契約上の学習禁止・地域/保持期間は公開sourceだけでは検証できない。sandboxの技術的境界と契約上のデータ取扱いを分ける。
- 全製品に共通の未知PII自動秘匿、符号化されたsecretの包括流出防止、全MCP応答の注入無害化を確認したわけではない。「未確認」は「機能が存在しない」の断定ではない。
- レビュー後に実装リンク、版差、主張範囲を修正する。独立レビューで指摘された修正は末尾履歴へ追記する。

## 原本と再検証方法

`research/disclosures/raw/harness_20261008/oss/`にrepoごとのcommit.json、再帰tree.json、選択した公開sourceを保存した。秘密のある利用者設定や既存資格情報は読んでいない。`harness_oss_sources_20261008.json`は固定commit、出典URL、保存file、SHA-256、取得成否を記録する。sourceに対する推測pathが404だった場合も失敗として残し、未取得sourceを根拠にしない。

## 独立レビューと改善履歴

親担当が[独立レビュー](harness_review_root_to_oss_20261008.md)で一次sourceを照合した。設定denyを保存済みallowより先に拒否するOpenCode V2評価と、Clineの承認待ちJSONへ生inputを保存する経路を本文へ追記した。自読で追加確認したOpenCode V2 coreの未移植scannerと旧shellの差、子agent policyの版差も維持する。これらは説明の改善であり、OS実行/脱出耐性を実験したという意味ではない。
