# 個人情報をモデルへ渡す前の検査とガードレールの実装

確認日：2026年10月8日。ガードレールは、入力・生成結果・道具の呼出し等を検査し、拒否・変更・再確認へ振り分ける処理である。OSの隔離や暗号化とは別の機構であり、検査結果を受け取るだけのプログラムと、送信・実行を実際に阻止するプログラムを区別する。

**秘密を公開モデルへ渡さないことが目的なら、検査器も同じ秘密を外部モデルへ送らない構成が必要である。** 出力検査は、既にモデルへ送った入力の漏洩を取り消せない。非同期の事後判定や画面だけの伏字も、情報の送信防止とは異なる。

## 1. 分野ごとの機構

| 分野 | 実装の例 | 制御する対象 | 別途必要な境界 |
|---|---|---|---|
| 入力・検索結果の個人情報検出 | Presidio、NeMoのsensitive data rails、LLM Guard Anonymize | 文字列中の氏名、番号、連絡先等 | データの出所・照合可能性、画像・添付・履歴等の取込み、検出漏れ |
| 注入された命令の検出 | PromptGuard、LLM Guard PromptInjection | 外部文書や利用者入力に含まれる誘導 | 判定不能時の停止、道具の強制認可、許可済み宛先への流出 |
| 意図と操作の整合性 | LlamaFirewall AlignmentCheck、Codex自動レビュー等 | 目的・操作・推論に現れる逸脱 | 判定器への秘密送信、独立性、説明されない行動、権限そのもの |
| 形式と内容の検証 | Guardrails AI、型付きの道具定義 | JSON等の型、値、規則 | 型が正しくても誤宛先や権限外の操作は起こり得る |
| 処理の流れの制御 | NeMoの対話・入出力・検索・実行のrails、SDKの道具検査 | 手順、検査順序、阻止条件 | 未接続の道具、初期指示、別のモデル呼出し、保存経路 |
| 情報の流れの制御 | CaMeL等の研究 | どの情報に由来する値を、どの操作へ使えるか | 多エージェントへの引継ぎ、権限ラベルの保存、外部実行の接続 |

## 2. NeMo Guardrails

公開コードは `NVIDIA-NeMo/Guardrails` の変更 `9f793de53e432c4c9c765975f5dd54df175fcb6e` を固定した。READMEは開発ブランチと安定版0.24.1を分けている。以下の機構は固定した開発コードを対象とする。

NeMoは入力、出力、検索結果、対話、実行という異なる箇所に処理を挿入する。個人情報の検出・置換にはPresidioを呼び出す実装がある。固定コードの `detect_sensitive_data` は入力・出力・検索結果を区別するが、実際の呼出しでは `language="en"` を指定する。日本語の氏名・住所・マイナンバーを対象にするなら、識別器・言語設定・接続を追加検証する必要がある。検査対象のentitiesが空なら検出なしとして進むため、「ライブラリを追加した」という事実だけでは検査は有効にならない。[検出実装](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/library/sensitive_data_detection/actions.py#L155)。

出力を逐次送信する設定は特に重要である。`stream_first` は検査前に出力する設定で、ストリーム検査を有効にする場合の構成内既定はtrueである。一方、ストリーム検査自体は既定falseである。固定コードは既知の出力置換処理について、先に出力する設定や重複文脈がある設定を拒否し、`stream_first=false`・`context_size=0`等を要求する。独自に作った処理がすべて同じ構成検証で捕捉されるわけではない。[既定値と置換処理の構成検証](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/rails/llm/config.py#L374)。

固定した逐次送信の実装では、検査を並列化した経路は処理失敗や例外で出力を続ける場合がある。順番に検査する経路では失敗をエラーとして返して終了する。したがって、単に「NeMoは失敗時に拒否する／しない」と製品単位でまとめない。検査前出力を選べば、後から拒否しても先に送った部分は戻らない。[送信と検査の順序・失敗分岐](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/rails/llm/llmrails.py#L1968)。

伏字化の返却物にも原文は残り得る。`_mask_sensitive_data_outcome` は変更後の本文とともに `metadata.text=original_text` を返す。これは自動的な外部送信の証明ではないが、結果の付随情報を診断・記録へ保存する側でも原文を除く必要がある。[原文を含む返却物](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/library/sensitive_data_detection/actions.py#L129)。

`speculative_generation` は入力検査と主モデルへの要求を同時に開始するため、拒否が確定する前に入力が送られ得る。ただし新しいIORails実行部は、既知の入力置換処理が登録されていればこの並行実行を無効にする。拒否だけを行う検査や独自処理にも、同じ送信前保証が自動的に付くとは限らない。[置換処理による無効化](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/guardrails/iorails.py#L840)、[検査と生成の同時開始](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/guardrails/iorails.py#L1266)。

旧LLMRailsの逐次出力経路では、拒否判定を確認した後に元の `user_output_chunks` を送信する。確認した処理区間には置換結果の反映が見当たらず、新IORailsと同一の挙動とは推定できない。これは静的観察であり、確定した実行障害という判定ではない。旧・新の実行部ごとに、合成の個人情報を複数の出力断片へ分け、実際の受信内容に置換が適用されるかを試験する必要がある。[旧実行部の送信経路](https://github.com/NVIDIA-NeMo/Guardrails/blob/9f793de53e432c4c9c765975f5dd54df175fcb6e/nemoguardrails/rails/llm/llmrails.py#L2051)。

NeMoの検出・自己検査にはローカル識別器だけでなく、外部モデルや外部サービスを使う方式もある。入力を外部へ出せるかという条件を満たしてから選ぶ。OSのファイル隔離、通信先制限、利用者・案件別の認可は、この内容検査とは別に置く。

## 3. LlamaFirewall

`meta-llama/PurpleLlama` の変更 `172c1074069eb88ec834124272c1b1c4f8893445` を固定した。PromptGuardは命令注入を分類し、CodeShieldは生成コードの静的検査を行い、AlignmentCheckは目的との整合性を検査する。固定コードには実験的なPIICheckも存在するが、標準のscanner割当てで自動的に有効にはならない。SYSTEM・MEMORYには既定でscannerがなく、対応した役割へ明示的に設定する。[scanner選択・既定値・判定の統合](https://github.com/meta-llama/PurpleLlama/blob/172c1074069eb88ec834124272c1b1c4f8893445/LlamaFirewall/src/llamafirewall/llamafirewall.py#L48)。

**実験的なPIICheckは、既定で検査対象の文章をTogether APIへ送る。** モデル名は `meta-llama/Llama-3.3-70B-Instruct-Turbo`、接続先は `https://api.together.xyz/v1` であり、ローカルで個人情報の有無を判定する方式と同一ではない。接続先の変更は可能だが、ローカルにしたときの互換性と精度は別に検証する。[PIICheck構成](https://github.com/meta-llama/PurpleLlama/blob/172c1074069eb88ec834124272c1b1c4f8893445/LlamaFirewall/src/llamafirewall/scanners/experimental/piicheck_scanner.py#L31)、[モデルへの本文送信](https://github.com/meta-llama/PurpleLlama/blob/172c1074069eb88ec834124272c1b1c4f8893445/LlamaFirewall/src/llamafirewall/utils/base_llm.py#L72)。

さらに、モデル評価の例外を既定の応答へ変える処理があり、PIICheckの既定応答は `detected_pii_types=["ERROR"]` である。この値のscoreは0となり、標準の阻止閾値0.7ではALLOW、最終statusはSUCCESSとなる。検査失敗を「PIIなし」に近い判定へ変えてしまう経路として、個人情報用の送信阻止にはそのまま採用しない。[例外の変換](https://github.com/meta-llama/PurpleLlama/blob/172c1074069eb88ec834124272c1b1c4f8893445/LlamaFirewall/src/llamafirewall/scanners/custom_check_scanner.py#L66)、[ERRORのscoreと判定](https://github.com/meta-llama/PurpleLlama/blob/172c1074069eb88ec834124272c1b1c4f8893445/LlamaFirewall/src/llamafirewall/scanners/experimental/piicheck_scanner.py#L73)。これは当該scannerの固定版の挙動であり、全LlamaFirewallの機構についての一括評価ではない。

`scan()`の結果を受け取ることと、アプリのモデル要求や道具実行を止めることは別である。アプリ側で判定に従って停止し、対象外の役割や直通の道具経路を作らない。

## 4. LLM Guard

`protectai/llm-guard` の変更 `168c1034ffdb33837e7ae6fd6a16b80567c1be03` を固定した。入力と出力へ複数のscannerを順に適用し、変更後の文章、各scannerの妥当性、危険度を返す。`fail_fast=true` は最初の不合格で**検査の列を止める**設定であり、アプリの送信まで自動停止する設定ではない。アプリは不合格、例外、scannerなし等をどう扱うか決める必要がある。[検査の実装](https://github.com/protectai/llm-guard/blob/168c1034ffdb33837e7ae6fd6a16b80567c1be03/llm_guard/evaluate.py#L25)。

検査器の列が空の場合、原文と空の判定辞書が返る。空辞書を「すべて合格」と解釈する呼出し側の実装では、検査の接続漏れを見逃す。初期化時に必要な検査器の存在も確認する。

AnonymizeとDeanonymizeは、検出した値を置換し、生成結果を元に戻す構成を作れる。ただし、`Vault` の実装は置換前後の組をプロセス内のリストへ保存するものであり、暗号化された秘密保管サービスではない。保存期間、案件ごとの分離、誰が復元できるかをアプリが管理する。[Vault実装](https://github.com/protectai/llm-guard/blob/168c1034ffdb33837e7ae6fd6a16b80567c1be03/llm_guard/vault.py)。

Deanonymizeは完全一致以外に大文字小文字を無視する方式や近似一致を選べる。復元を外部送信する道具の前で無条件に行うと、モデルには伏せた秘密を別の宛先へ渡してしまう。復元先の権限と宛先を確認し、モデルが出力した任意の置換記号を復元許可として扱わない。[復元方式](https://github.com/protectai/llm-guard/blob/168c1034ffdb33837e7ae6fd6a16b80567c1be03/llm_guard/output_scanners/deanonymize.py#L17)。

## 5. Guardrails AI

`guardrails-ai/guardrails` の変更 `06d0ff2c5f9bcb493d976b76f885e37e41ce845d` を固定した。検査器と失敗時の動作を組み合わせ、FIX、FILTER、REFRAIN、EXCEPTION、REASK、NOOP等を選べる。NOOPは失敗しても元の値を返す。REASKは再びモデルに生成させる経路なので、秘密の送信可否を再評価する必要がある。[失敗時の動作](https://github.com/guardrails-ai/guardrails/blob/06d0ff2c5f9bcb493d976b76f885e37e41ce845d/guardrails/validator_service/validator_service_base.py#L81)。

検査器の実行記録には、検査前の値 `valueBeforeValidation` を保持する処理がある。出力を修正しても、診断記録や実行履歴の原文が同じように除かれるとは限らない。Hubから追加する検査器や観測先は、新たなコードと送信先として個別に調べる。[検査前の記録](https://github.com/guardrails-ai/guardrails/blob/06d0ff2c5f9bcb493d976b76f885e37e41ce845d/guardrails/validator_service/validator_service_base.py#L132)。

実行履歴は既定で10件をプロセス内に保持する。固定コードでは `history_max_length=0` も `or 10` によって10へ変換されるため、0を指定して履歴を無効にしたつもりでも原文が残り得る。これはメモリ内の保持の確認であり、永続保存・外部転送までを示すものではない。[履歴の初期化](https://github.com/guardrails-ai/guardrails/blob/06d0ff2c5f9bcb493d976b76f885e37e41ce845d/guardrails/guard.py#L137)。

形式検査や個人情報検出は、OSの隔離、通信の強制制限、道具の操作対象の認可を代替しない。検査器のAPIを通らずにモデルや道具を呼べる構成では、その経路へ検査を接続する必要がある。

## 6. Presidioと日本語への適用

`microsoft/presidio` から取得した変更 `d8847904621733f4eaad4f9bd977b96a11325c90` を固定した。Presidioは文章中の情報を、形式、検査用の計算、周辺文脈、固有表現の抽出等で識別する。個人情報を扱うローカルな検査器を組み立てる基礎として使えるが、公式は全機密情報を検出する保証がないと明記する。[READMEの検出限界](https://github.com/microsoft/presidio/blob/d8847904621733f4eaad4f9bd977b96a11325c90/README.md#L55)。

言語ごとに文字列の解析用モデルと識別器の双方を構成する。日本語対応のモデルを加えるだけで、国内の住所・番号・氏名や企業内のID対応まで完全に分かるわけではない。マイナンバーの形式・検査、顧客番号の列情報、名簿との対応、自由記述の病歴などを組み合わせて評価する。[言語設定](https://github.com/microsoft/presidio/blob/d8847904621733f4eaad4f9bd977b96a11325c90/docs/tutorial/05_languages.md)、[対象情報の一覧](https://github.com/microsoft/presidio/blob/d8847904621733f4eaad4f9bd977b96a11325c90/docs/supported_entities.md)。

## 7. 開発用SDKの検査境界

OpenAI Agents SDKの公開仕様では、入力の検査は既定でエージェントと並行して動く。そのため、判定が終わる前にモデル要求や道具実行が進む可能性がある。最初のモデル要求も阻止したい場合は、`run_in_parallel=false` と、モデルを使わずに済む前処理を組み合わせる。

入力検査は処理列の最初のエージェント、出力検査は最終出力を作るエージェントに適用される。道具単位の検査は、検査を構成した関数道具・ローカルMCP等へ別に接続する。すべての子エージェント・道具へ自動的に同じ検査が付くと想定しない。[公式Guardrails](https://openai.github.io/openai-agents-python/guardrails/)。

現行仕様は、拒否判定と検査器が投げる例外でも保存方針を区別する。拒否した最終道具出力を置換しても、再実行に必要な道具引数等には同じ個人情報が残り得る。原出力、引数、会話、観測の各経路へ保存方針を適用する。SDKの隔離機能や暗号化セッションは、内容検査と別の境界である。[SDK固定実装の追加調査](harness_sdk_security_20261008.md)に、追跡配信、保存、Unix-local・Docker、LangChain等の逐次出力と認可も整理した。

## 8. 情報の流れの制御

CaMeLは、モデルによる計画と、信頼しない文書から値を取り出す処理を分け、値の出所と使用できる操作を実行部で制御する研究である。外部文書の命令を検出するだけでなく、情報がどの操作へ流れるかを追う構成として参考になる。[Defeating Prompt Injections by Design](https://arxiv.org/abs/2503.18813)。

2026年10月の研究は、個々のエージェントがCaMeLを使っていても、情報をエージェント間で渡す際に信頼属性を失うと注入が成立し得ることを論じる。単体の防御を複数配置するだけでなく、引継ぎでも出所・権限・機密区分を保存する必要がある。[Can CaMeLs Talk](https://arxiv.org/abs/2610.05640)。これは研究上の結果であり、本調査の各製品がこの方式を実装しているという意味ではない。

CaMeLの抽出モデルは原文を読む。副作用なしとして登録した道具を先に許可する実装もあるため、情報フロー追跡だけで抽出・修復モデルへの送信を防いだと考えない。Multi-CaMeLの評価では機密性の規則が空であり、0%の攻撃成功率は全個人情報保護の証明ではない。保証は階層的な親子呼出しに限定され、暗黙依存の追跡や分岐・再試行にも限界がある。

公開Multi-CaMeL実装はSequrity Control APIへ依存し、商用の遠隔実行器内部は本調査で監査していない。より強い情報の非干渉性を論じるLLMbdaも、Leanの証明・実行器原本を取得して再検証できたわけではない。[論文全文・固定コード・評価条件の追加調査](harness_information_flow_and_evaluation_20261008.md)を参照する。

## 9. 個人情報用に満たすべき条件

内容検査を強制境界にするなら、対象外の取込み経路をなくし、判定前のモデル送信を防ぎ、例外や不明を許可へ変えず、原文を観測記録へ流さない。復元は信頼したアプリで、本人・案件・宛先への認可を確認して行う。未知の機密を完全に検出できるという仮定を置かず、資源ラベルとアクセス制御を併用する。

静的コード確認の結果は、検出精度や攻撃への成功率の実測ではない。機密分類の試験には、[43例の文脈付きPII一覧](pii_classification_examples_20261008.json)を使い、形式検出と法的該当性、企業秘密、検査失敗を別に採点する。[固定資料の台帳](harness_guardrail_sources_20261008.json)。

独立したOSS担当の[レビュー](harness_review_oss_to_guardrails_20261008.md)を受け、原文の付随情報、入力の並行生成、旧・新の逐次送信、空の検査器・履歴設定を補足した。固定した実装から実際の関数を取り出す[確認用プログラム](../../scripts/probe_harness_guardrail_semantics.py)で、LlamaFirewallの評価例外後の許可とLLM Guardの判定返却を再現した。[結果](harness_guardrail_probe_results_20261008.json)は通信部分を模擬した2件の意味確認であり、検出精度・本番環境全体の試験ではない。
