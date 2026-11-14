# OSSハーネス調査の独立レビュー

確認日：2026年10月8日。親エージェントがOSS担当の稿と保存原本を照合した。レビュー対象は固定した開発版の記述であり、配布済み実行ファイルの挙動を認証するものではない。

## 照合した主要な主張

| 主張 | 確認した保存原本 | 結果 |
|---|---|---|
| OpenCodeの権限規則は後の一致を使う | `packages/core/src/permission.ts` の `evaluate`・`evaluateInput` | 後の一致を使うが、管理されたdenyを保存済みallowで覆さない事前検査も存在。単純な規則列の説明と全有効規則の評価を分ける必要がある |
| Geminiのbwrapは全ホスト情報を不可視にしない | `packages/core/src/sandbox/linux/bwrapArgsBuilder.ts` | rootの読取り専用bindを確認。maskと書込み指定を重ねる説明に整合 |
| ClineのSubprocessSandboxはOS隔離と同義でない | `sdk/packages/core/src/runtime/tools/subprocess-sandbox.ts` | Nodeのspawn、親の環境変数、IPCを確認。読んだ実装でOS資源の制限を立てる処理は確認できない |
| Cline SDKの未指定道具は自動承認される | `docs/sdk/guides/permission-handling.mdx` | docsの既定説明に整合。別のDesktop承認IPCの失敗時拒否と混同しない |
| OpenHandsは秘密のstream境界を保留してmaskする | `secret_registry.py` のstream用buffer | 最長秘密長を考慮した保留を確認。未知PIIの一般検出とは異なる説明に整合 |

## 改善要求

1. OpenCodeについて、後の規則優先だけで管理済みのdenyを保存済みallowで上書きできるように読ませない。固定V2の `evaluateInput` はconfigured rulesのdenyを先に評価している。具体的なsource参照を追加する。
2. Clineの承認をPII保存経路にも含める。`requestDesktopToolApproval` は道具の生の引数を承認要求JSONへ書き出す。承認で拒否しても、その前に承認ディレクトリへ元の引数を渡す点を補足する。同じ利用者・プロセス権限の敵対者に対する改ざん耐性は、本調査の読取りだけで断定しない。
3. 製品ごとに、古いV1とV2、通常の拡張と新SDK、公開開発版と安定配布版を本文で区別する。担当が追加したOpenCode shellの未移植部分の説明を維持する。

読んだ原本の範囲で、Gemini・Cline・OpenHandsの強制場所に関する重大な誤りは確認しなかった。上記の補足を反映し、最終稿で再確認する。

## 改善後の再確認

3件の要求を最終稿で再確認した。OpenCodeのconfigured deny先行と保存済みallowの合成、Clineの生の引数を含む承認要求JSON、V1/V2・SDKの版差を補足済み。公開コードの範囲に関する説明上の指摘は全件解消した。
