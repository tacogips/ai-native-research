# 独立レビュー: OSS調査担当から横断ガードレール調査稿へ

対象: `harness_guardrail_mechanisms_20261008.md` 初稿。レビュー日: 2026-10-08。5つの原本repoで`git rev-parse HEAD`を実行し、本文の固定commitと一致を確認した。外部モデルへの呼出しや実秘密の利用は行わず、本文の主要主張を静的sourceへ照合した。

## 判定と補足依頼

初稿のLlamaFirewall PIICheck外部送信とERROR→score0→ALLOW/SUCCESS、NeMoの旧逐次出力のparallel/sequentialエラー差、LLM GuardのVaultと判定返却、Guardrails AIの原文履歴、Presidioの日本語設定と検出限界は、固定sourceに一致する。安全対策の設計資料としては以下を追加すると、入力送信前と記録前の境界が明確になる。

| ID | 優先度 | 根拠・補足すべき内容 | 提案 |
|---|---|---|---|
| G-R1 | P1 | NeMoの`_mask_sensitive_data_outcome`は変更後本文だけでなく`metadata.text=original_text`を返す。伏字にしたことで原文がすべて消えるわけではない | action outcome/診断/ログのmetadataも保持・出力方針に含める。これは外部へ自動送信する証明ではなく、返却物に原文を残す実装の確認 |
| G-R2 | P1 | NeMo `speculative_generation`は入力検査と主model要求を同時にtask化。拒否型検査では停止判定前に秘密が送られ得る。ただしIORailsは既知の入力rewrite railがあれば指定を無効化する | 「入力拒否は送信前」の保証に使うなら順序を固定。既知rewriteの無効化分岐と、custom処理の宣言/実配線の必要性も併記 |
| G-R3 | P2 | 旧LLMRailsのstreaming sequential経路は`require_rail_outcome`→`is_blocked`を確認し、その後`user_output_chunks`をyieldする。読んだ同ブロックにtransformの反映は見当たらず、新IORailsと同一挙動と推定できない | 構成検証を通ったことと全stream経路でmaskが適用されることを分ける。旧/新engine別の合成PII chunk試験を未検証として明記。静的観察のみで確定障害とは断定しない |
| G-R4 | P2 | LLM Guardは空scanner列で結果dictionaryが空のまま原文を返す。Guardrails AIのhistoryは既定10件のmemory stackで、`history_max_length=0`を渡しても`or 10`により10になる | 「検査器を接続したつもり」や「0で履歴なし」の設定を検証する。履歴の存在を外部転送や永続保存へ拡張して断定しない |

根拠:

- [NeMo outcome原文metadata](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/library/sensitive_data_detection/actions.py#L129)
- [IORails speculative有効化判定](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/guardrails/iorails.py#L840)
- [検査とmodel要求のtask化](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/guardrails/iorails.py#L1266)
- [旧engineの逐次出力経路](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/rails/llm/llmrails.py#L2051)
- [LLM Guard空scanner処理](https://github.com/protectai/llm-guard/blob/168c1034ffdb33837e7ae6fd6a16b80567c1be03/llm_guard/evaluate.py#L50)
- [Guardrails AI memory history](https://github.com/guardrails-ai/guardrails/blob/06d0ff2c5f9bcb493d976b76f885e37e41ce845d/guardrails/guard.py#L137)

## 詳細確認

### NeMo

`OutputRailsStreamingConfig`はenabled=False、stream_first=True、context_size=50、chunk_size=200。設定検証はcatalogでtransform_targetが判明する既知のflowを対象に、stream_firstと文脈重複を拒否する。未知/custom flowのrewriteを一般に自動検知する保証ではない。旧LLMRailsのparallel execution status不成功と例外はpassしてchunk処理を続行し、sequentialはエラーJSONをyieldしてreturnする。検査前にyieldした部分を回収しない。本文のこの区別は正確である。

個人情報検出/置換はいずれもPresidioへlanguage="en"を渡す。entities空は検査しない、設定なしは例外であり、これらを同じ「PIIなし」と扱わない。検出漏れ、日本語適合性、局所推論の精度は実測していない。

### LlamaFirewall

PIICheckの既定Together接続とmodel名、LLMClientのuser contentへの検査対象prompt送信を確認した。CustomCheckScannerは評価例外を既定応答へ変換し、PIICheckのERRORはscore0、閾値0.7未満でALLOW、status SUCCESSとなる。API keyがないとclient構築時に例外になる経路は別であり、「全失敗が必ずALLOW」と一般化しない。

LlamaFirewallの既定SYSTEM/MEMORY scanner空、PII scanner非自動有効化、scanner空の統合結果ALLOW/SUCCESSを確認した。アプリが判定を無視すれば送信阻止しない点は正しい。検出精度と真の攻撃成功率は未実験。

### LLM Guard

scan_prompt/scan_outputは変更後文字列、妥当性辞書、score辞書を返す。fail_fastは検査loopのbreakであり、modelやnetworkの強制停止は呼出し側の責任。Vaultはlistを保持しget()でそのlistを返す。名称から暗号化保管や案件別の認可を推定しない。

DeanonymizeのEXACT/CASE_INSENSITIVE/FUZZY/COMBINED_EXACT_FUZZYを確認した。復元先の宛先認可を別に設ける提案は、この置換が自動的に許可対象を選別するわけではないという実装範囲に一致する。

### Guardrails AI

NOOPはvalueを返し、REASKはincorrectValueを持つFieldReAskへ進む。validator logはvalueBeforeValidationを保持し、iteration.outputs.validator_logsへ追記する。guard.historyはmemory stackであるため、少なくともプロセス内に検査前内容が残り得るという主張は妥当。すべてのHub validatorが局所処理か、外部通信するかは個別調査が必要であり、本文も区別している。

### Presidio

READMEは全機密の検出を保証しないと明記。言語対応にはNlpEngineとrecognizerの双方の設定が必要というtutorialに一致する。日本語modelの導入のみで日本法上の「容易な照合」や社内名簿との対応を判断できると扱わない点は妥当。

## レビュー範囲外

OpenAI Agents SDK、LangGraph/Deep Agents等の新しい補足、CaMeLと多agent論文の精読は親担当が追加中のため、このレビューでは5主要ガードレールの主張に限定する。SDKのmainバージョン・暗号化session・全道具guardrail範囲、論文の評価条件/数値をこの確認で証明したとは扱わない。

改善後の再確認は追記する。

2026-10-08 改善後再確認: G-R1〜G-R4の該当本文とリンクを再読した。原文metadataの残存、speculative生成と既知rewrite抑止、旧/新streamingの未検証区別、空scanner、memory historyの0→10が固定sourceと一致する。4件の説明上の補足を解消とする。親が追加したASTによる2件の局所確認プログラムと結果も読み、通信/識別器等を模擬した上流関数の意味確認であって全library/実機試験ではないという留保を確認した。
