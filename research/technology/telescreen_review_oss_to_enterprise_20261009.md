# 独立レビュー：保存状態の監視製品・国内製品

実施日：2026-10-09。対象は `telescreen_related_enterprise_20261009.md` と同名資料台帳に保存された原本。公開資料の支持、転送先、処理場所・保存の例外、問題状態と修正の区別を確認した。実有償環境の通信・削除・精度・契約SKUの試験ではない。

## 確認した重要点

| 主張 | 原本による確認 | 判定 |
|---|---|---|
| Macieの内容findingは新規・policy再発とは異なる | AW07：sensitive data findingsはunique/new、policyのsubsequent occurrenceと区別 | 支持あり。外側の重複/再発管理が必要という説明が妥当 |
| SDP quoteは既定非返却、設定次第でBigQuery保存 | GO01の include_quote と findings storage の説明 | 支持あり。content APIだけの非保存をstorageへ広げていない |
| Workspace snippetsは元の削除後も残る | GO09：180日、前後100文字、500文字上限、source deleted/changedでも残る | 支持あり。設定の既定値を未確認とした点も妥当 |
| BigIDの例はexport後にresolvedにする | BI02のMark Issues as Resolved | 支持あり。外部ticket作成を元データの修正証明と区別している |
| Cyera Outpostとfull SaaS、Data Insightsへmetadata | CY01は問い合わせページだがFAQ本文を実際に含む | 支持あり。問い合わせタイトルだけで本文不在と誤判定しない |
| Varonis CollectorとDatAdvantage Cloudの処理境界 | VA01の製品別処理説明 | 基本記述は支持あり。ただし下記AI Monitoring例外の補強が必要 |
| P-Pointer差分・更新監視・承諾処理・CSV | JP01の本文 | 支持あり。国内の直接候補との説明が妥当 |
| HTTP200、保存hash、抽出本文 | saved状態の原本/抽出の全hashを確認。gzip magicなし、短すぎる抽出なし | 保存整合は合格。HTTP200だけで内容保証しない説明と一致 |

## 補強要求

1. **VaronisのAI Monitoring opt-in例外を同じ保存比較欄へ追記する。** VA01の公開Security本文は、Copilot/AgentForce/ChatGPT Enterprise等のAI audit logsからpromptsとresponsesをData Security Platform SaaSへ収集・分析・保存し、licensed retentionを180日、AI Prompt auditor権限で閲覧と説明する。全文書の取得とは異なるが、質問文・回答文を保存する例外なので、「原文を持続保存しない/metadataのみ」の読者による機能横断の一般化を防ぐ。既存の製品別記述を撤回する必要はない。
2. **GO06の転送先を維持して読む。** 元support URLはCreate and manage activity rulesへ転送する。Closed等の状態はGO10本文にあるため現稿の併記に根拠があるが、GO06だけをAlert center状態仕様の根拠に使わない。固定原本を保持し、転送先は台帳と本文説明で分かるようにする改善は任意。

初稿には404のCH05引用があったが、レビュー途中の現稿では削除されていた。取得失敗ページを現稿の根拠に採用していないことを確認した。商用完成品の内部実装を独立検証したという説明はなく、提供者の公開仕様と未確認領域を分けている。

原本台帳：[enterprise資料](telescreen_related_enterprise_sources_20261009.json)。Varonis原本：[公式Security](https://www.varonis.com/trust/security)。修正の解消確認は下に追記する。

## 改善後の再確認

Varonisの比較欄へAI Monitoringを明示的に有効化した場合の質問文・回答文のSaaS保存、質問文180日、AI Prompt auditor閲覧権限が追記された。VA01の原本と再照合し、上記補強要求1は解消を確認した。GO06の転送先保持とGO10の状態仕様併記も維持され、残る必須訂正はない。確認日は2026-10-09。
