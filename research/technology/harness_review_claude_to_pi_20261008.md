# Pi 調査稿の独立レビュー

レビュー日: 2026-10-08。レビュー担当はClaude Code調査担当。対象: `harness_pi_security_20261008.md`。照合した公開コードは `1cedd32724abfcb0915f76cc61b6827e2c16dbad` 固定。原稿の結論に引きずられず、主な安全境界を実行側とイベント側の両方で確認した。実行試験は行っていない。

## 結論

主要結論は固定コードと一致する。特に、標準MCPとproject trustを最近の版の機能として認識している点、codemodeのJavaScript能力制限とホスト道具のOS権限を分ける点、検査イベントごとに失敗時の挙動が異なる点は妥当。重大な事実訂正は発見していない。ただしPII設計に直接関わる説明を3点補強し、1点の出典行を直すとよい。

## 変更を推奨する項目

| 優先度 | 項目 | 確認した証拠 | 推奨する改善 |
|---|---|---|---|
| 高 | `tool_call` の例外時の「停止」の対象 | agent-loop.ts L724-L782は例外を当該道具のerror resultへ変換する。runner.ts L1244付近はcatchせず上位へ渡す | 「当該ツールの実行を阻止する。会話・全プロセスを必ず終了する意味ではない」と明記 |
| 高 | codemodeの自動記録にもPIIが入る | execute.ts L63は引数をJSON化してpreview、L454/L467はargsとerrorを記録、L525-L539はdetailsにcallsを返す。agent-loop.ts L932-L940とagent-session.ts L1144-L1163はdetails付きtoolResultを保存 | 「選択した結果だけモデルへ返す」利点に加え、引数プレビューと失敗内容は局所detailsや観測に残り得る点を具体的に追記。保存値だけの検査にしない |
| 中 | codemodeのScript errorは自動でモデルへ返る | execute.ts L303-L313はerror.stack/messageを文字列化、L512は失敗時に出力へ加える | 原結果をtextにしなくても、スクリプトがPIIを含む例外を投げるとモデルに出る。出力検査は成功・失敗両方に適用する、と追記 |
| 低 | MCP環境継承の出典アンカー | stdio.ts L94-L98が`process.env`統合。原稿の[STDIO]はL99-L109で、その行が外れている | アンカーをL90-L103等へ変更し、主張そのものは維持 |

固定出典: [agent-loop.ts L724](https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/agent/src/agent-loop.ts#L724)、[codemode引数 L63](https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L63)、[codemode error L303](https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L303)、[details返却 L525](https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/extensions/codemode/execute.ts#L525)、[結果保存 L1144](https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/coding-agent/src/core/agent-session.ts#L1144)、[MCP環境継承 L94](https://github.com/earendil-works/pi/blob/1cedd32724abfcb0915f76cc61b6827e2c16dbad/packages/mcp/src/transports/stdio.ts#L94)。

## 再確認して一致した項目

- **拒否・書換えイベント**: runnerのtool_callは例外を握り潰さず、context、context_with_system、tool_result、before_provider_request、before_provider_headersは捕捉後に継続する。agent-loopは引数schema検査後にtool_callを呼び、変更された引数を再度schema検査していない。原稿の区別は正しい。
- **標準MCPと信頼**: security.mdはprojectのMCP/拡張等を承認対象とし、AGENTS/CLAUDE文脈は例外、非対話askではprotected resourceを読まないと明記する。標準に全面的なOS隔離がない説明と矛盾しない。
- **codemodeの実行時間**: execute.ts L487-L491が未指定時Infinityを渡す。worker.ts L52-L64はQuickJSのheap/stack/interruptを構成する。VMの存在を有限時間停止やホスト道具の隔離に言い換えない説明は妥当。
- **補助モデル経路**: execute.ts L626-L728のmodels.classify/generateImagesは登録済みprovider/idで再解決し、runtimeへsignalだけを渡す。sdk.tsの通常会話hookを当然に通るという断定を避けるのは妥当。
- **sandbox例の失敗**: sandbox/index.ts L217-L288では未初期化・無効時にlocalBashへ戻り、session_startの初期化例外でsandboxEnabled=falseにする。原稿の失敗時継続はコードで確認した仕様であり、未知脆弱性を仮定していない。
- **局所セッション**: session-manager.ts L1124-L1188はJSONL平文書込み、最初のuser/assistantでpersist、mode指定なし。`0600`の認証保存や一時出力と混同していない。
- **能力の出所**: ctx.executeTool()の入れ子経路はagent-session.ts L729以降の共通道具pipelineへ入るが、拡張自身の直接OS操作は同じ監視境界ではない。原稿はこの範囲を正しく限定する。

## 残る検証の範囲

本レビューは安全上重要な主張の静的照合であり、Pi全コード・全provider・外部MCP実装・Gondolin/OpenShellの安全性を保証しない。受入段階では、検査器例外時の実送信、無加工detailsの保存・共有、実行中拡張のreload、直接分類モデル、結果途中経過、sandbox依存の欠落、端末/RPC/print間の差を架空データで実行検証する必要がある。

## 改善後の再確認（2026-10-08）

Pi 担当の改稿を再読し、上記 4 件すべての反映を確認した。`tool_call` の停止範囲、自動引数・エラー・details 保存、`Script error` のモデル出力、STDIO の L90–L103 引用が本文へ追加・訂正された。これらの指摘は解消済み。追加された外部 `pi-permission-system` の取得版は **0.8.0** であり、担当者の途中メッセージにあった 0.13.0 は保存稿には採用されていない。外部拡張の実行互換性の検証は本レビューの対象外である。
