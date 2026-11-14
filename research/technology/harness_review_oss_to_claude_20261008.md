# 独立レビュー: OSS調査担当からClaude Code調査稿へ

対象: `harness_claude_security_20261008.md` 初稿。レビュー日: 2026-10-08。方法: 保存した公式Markdownと固定SRT source `fedc0bbe206c2705b3de990fdbed51b3255214c9` の静的照合。`git rev-parse HEAD`で実checkoutも一致を確認した。実機sandbox試験・binary同梱版の証明は行っていない。

## 判定

初稿の主要区別（承認とOS隔離、Claude内蔵と独立SRT、MCP/hooks境界外、モデル通信と道具通信、CLI/SDK timeout差）は一次資料で裏付けられる。ただし個人情報流出防止の必須境界として読む場合、以下の **P1 2件の追記が必要**。修正前は「失敗時の挙動まで説明済み」とするには不十分。

P1は外部モデルへ原文が戻り得る、または実secretが子プロセスへ残り得る重要な省略。P2は脅威境界/版/保証範囲の精度を上げる補足。

## 指摘一覧

| ID | 優先度 | 根拠と問題 | 必要な修正 |
|---|---|---|---|
| C-R1 | P1 | hooks.md L2087–2091付近: built-in道具の`updatedToolOutput`がschema不適合なら置換を無視して**原結果を採用**。MCPはschema検証なし。初稿は置換の存在を強調し、schemaを未確認欄に残すのみ | 失敗表へ「置換schema不正→原文使用」を明記。全結果の形を固定し、検査器失敗/不正出力時に本体へ渡さない外側の必須境界を提案 |
| C-R2 | P1 | credential-mask-env.ts L103–144: JWT decode検証失敗、またはmaskClaims指定対象に文字列claimがないとwarn+continueで実env原値が残る。`onExtractNoMatch`は後段のextract不一致用であり、この分岐を覆わない | extract no-matchとJWT/claim失敗を別行へ。JWT設定を事前検証するかwhole-value mask/denyへ戻す外側方針を提案。「onExtractNoMatch:denyなら全mask失敗安全」と読ませない |
| C-R3 | P2 | resolved-address-guard.ts L1–24/L160–170: guardはhostname対象。allowlistの明示IP literalを再判定しない。名前から禁止IPへ解決しても、そのIP:portが明示allowなら例外あり。親proxy/MITM経路は自前の検証へ委任 | 「loopback等を除く」に明示許可例外・IP literal対象外を補足。localhost/metadataを絶対拒否する設計として誤読させない |
| C-R4 | P2 | zero-data-retention.md L76–78: 法律上必要な場合/利用規約違反の対応ではZDRでも保持あり、違反検知時のinput/outputは最大2年。第三者platform、feedback、運用記録も別範囲 | 「サービス側非保持」は適用対象と例外付き契約上の保持方針として表現。個人情報の非閲覧/外部送信禁止とは別とする |
| C-R5 | P2 | managed-settings.md L365: restrictive key修復とfield単位補修はv2.1.282以降。初稿は一般に最低版尊重と書くが、重要なfail-closed説明に版がない | 重要な失敗表/管理節へ最低版を直接付記。旧版にも同じ安全側挙動があると推定しない |

固定sourceへのリンク:

- [JWT/env mask分岐](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/credential-mask-env.ts#L103)
- [hostname guardの範囲](https://github.com/anthropics/sandbox-runtime/blob/fedc0bbe206c2705b3de990fdbed51b3255214c9/src/sandbox/resolved-address-guard.ts#L1)
- [公式PostToolUse](https://code.claude.com/docs/en/hooks#posttooluse-decision-control)
- [公式ZDR例外](https://code.claude.com/docs/en/zero-data-retention#data-retention-for-policy-violations)
- [管理設定の安全側処理](https://code.claude.com/docs/en/managed-settings#keys-that-fail-closed)

## 根拠を確認できた主張

- `updatedToolOutput`は全道具、旧`updatedMCPToolOutput`はMCPのみ。blockだけでは原出力を隠さない。道具副作用とhook前telemetryは取消されない（hooks.md L2062–2091）。
- `canUseTool`は全道具必須gateではない。allow/bypass等で前段承認される呼出しはcallbackを通らず、PreToolUse denyは残る。`allowed_tools`を道具集合のallowlistと取り違えない（agent-sdk_permissions.md冒頭の6段階）。
- CLI command/http/MCP hook timeoutは通常permission flowへ進み、SDK PreToolUse timeoutは道具を止める（hooks.md L843–850、agent-sdk_hooks.md L787以降）。
- `@file`は通常PreToolUseの外だが、Readのpath拒否規則の適用対象に含まれる最善努力の実装と説明される。したがって「hook対象外」と「全権限対象外」は同じではない（permissions.md L339–346）。
- `.claudeignore`不採用、Read denyとEdit/Writeの関係、NotebookEdit別途Edit規則、path付きWrite等が参照されない点は一次docsと一致。
- sandbox内読取は広い既定であり、資格情報deny自動一覧ではない。`failIfUnavailable`と`allowUnsandboxedCommands`を別に閉じる必要、excludedCommands/手入力`!`/MCP/hooks/LSP等が別境界という説明は一次docsと一致。
- standalone SRT Windows alphaのWFP/SID等と、Claude内蔵native Windows非隔離は別であり、初稿は区別できている。
- request-filterの例外拒否、TLS終端なしのCONNECTでbody検査できない点はsourceと一致。secret bodyのsentinel置換はchunk境界を保留する方式で、圧縮/符号化で置換し損なってもダミーのまま上流へ行く方向。これは未知PIIの流出防止保証ではない。

## 追加検証の境界

このレビューは保存一次資料に対する整合性を検査した。Claude本体の現行binaryが同じ分岐を実装すること、全OSでのescape耐性、全道具の出力schema、全ログ保存順序、契約の個別適用を証明していない。独立SRTの機構をClaudeに標準搭載済みと扱わない初稿の留保は保持する。

## 改善の確認

上記指摘は担当へ通知済み。本文修正後の該当箇所を再確認して結果を追記する。

2026-10-08 再確認: 担当がC-R1〜C-R5を本文へ反映した後、該当行と設計案/受入試験を再読した。schema不適合→原結果使用、JWT/claim失敗の独立した実値残存、明示IP/localhost例外、ZDR保持例外、v2.1.282最低版の説明が原本と一致する。指摘5件を説明上解消とする。実機試験等の未検証境界は引き続き維持し、製品の安全認証を行ったという意味ではない。
