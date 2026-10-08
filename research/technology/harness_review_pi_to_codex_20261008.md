# Pi 担当から Codex 技術稿への独立レビュー

レビュー日：2026-10-08。対象：[Codex 技術稿](harness_codex_security_20261008.md)。固定取得コード `979011409de0a60b52f179721948e65531d26144` の該当関数・既存試験を読み、説明の強さと出典を照合した。実際の各 OS による隔離、通信、失敗処理の再現試験は行っていない。

## 判定

主要な境界説明はソースと整合する。特に、現在の環境変数の既定、前処理の失敗時の継続、実行後の MCP 結果置換が未対応である点、命令通信の代理部とモデル送信を区別する説明は、PII 用ハーネスを設計する際に有用である。ただし以下の 1 件の機構上の限定と 3 件の引用精度を改善する必要がある。

## 必須修正：拒否制御は同期 hooks に限る

第 6 節の `PreToolUse` について、明示された拒否と終了コード 2 がいつでも実行を止めるように読める。`ConfiguredHandler.can_apply_control_effects()` は `execution_mode() == Sync` の場合だけ true。`async=true` の command と `ExecutorScoped` の処理は Async になる。前処理の解析は `can_apply_control_effects()` を確認してから拒否・引数変更を適用する。

**修正案:** 「固定版の同期 `PreToolUse` は、明示された拒否や終了コード 2 と非空の標準エラーで阻止できる。非同期処理は制御効果を適用せず、診断や追加文脈等に用いる。前処理を検査境界とする場合は同期であることを確認する。」

この限定を加えても、起動失敗・時間切れ・不正 JSON・理由のない終了コード 2 は安全側に停止しない、という現稿の重要な結論は変わらない。

根拠：[同期・非同期の判定](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/hooks/src/engine/mod.rs#L142-L159)、[拒否効果を適用する条件](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/hooks/src/events/pre_tool_use.rs#L233-L277)。

## 出典行の改善

| 現稿の出典 | 指摘 | 推奨する参照 |
|---|---|---|
| `exec_policy.rs#L405` | `bypass_sandbox` の代入より前の prompt 側を指す | L440–455：全解析命令が明示 allow かを評価 |
| `file-system/src/lib.rs#L347` | `FileSystemSandboxContext` の宣言を指し、読取条件自体は後方 | L408–414：`should_read_from_sandbox()` |
| `login/src/auth/storage.rs#L182` | 保存バックエンドの trait 付近で、0600 の実体ではない | L215–230：JSON 化・OpenOptions・Unix mode |

修正用リンク：[bypass 判定](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/core/src/exec_policy.rs#L440-L455)、[読取の分岐](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/file-system/src/lib.rs#L408-L414)、[認証 JSON 保存](https://github.com/openai/codex/blob/979011409de0a60b52f179721948e65531d26144/codex-rs/login/src/auth/storage.rs#L215-L230)。

## 再確認して整合していた事項

- `ShellEnvironmentPolicy::default()` は `inherit=All`、`ignore_default_excludes=true`。KEY / SECRET / TOKEN を通常自動除外するという旧説明を採用していない。
- `PreToolUse.parse_completed()` は `should_block=false` から始まり、実行エラーや不正 JSON では Failed の記録だけを作る。終了コード 2 と空の stderr も block にしない。
- `PostToolUse` の既存試験は `updatedMCPToolOutput` を unsupported として Failed にする。実行済み操作の取消しとは異なる、との限定も正しい。
- `network-proxy` の既定で `enabled=false`、`credential_broker=false`。コードの存在を全利用者で常に有効な機構と扱っていない。
- 子エージェントの役割設定後に runtime overrides を再適用し、親の承認・cwd・権限構成に揃える説明は `child_config.rs` と整合する。
- 認証ファイルの 0600 は作成モードであり、暗号化や同一ユーザーからの隔離ではない。現稿は「作成する」と適切に限定している。

## 追加の確認事項・調査の限界

管理設定・クラウド・Computer Use・MCP 通信の対象外一覧は現行の公開サービス文書に依存する。これらを固定 CLI の同じコードから証明したとは主張しない。サービス文書の取得日時・原本保存を出典台帳で照合する。

権限の説明は、実行対象 OS、配布形態、管理設定に応じた差をすでに記載している。今後の受入試験では、Linux の名前空間作成失敗、シンボリックリンク・拒否パターン更新、Windows の未対応規則、代理部を通らないモデル通信、前処理の同期/非同期/失敗の分岐を分けて実行する。これらは次段階の試験要件であり、このレビューで再現して合格したものではない。

## 改善確認

上記の修正を Codex 担当が反映した後、改訂稿を再読して確認した。同期処理のみが拒否制御を適用する限定と、exec_policy L440、file-system L408、auth storage L215 の引用がすべて修正されている。本レビューの 4 指摘は解消済み。これは文書・原本コードの整合性の確認であり、実機試験の合格を意味しない。
