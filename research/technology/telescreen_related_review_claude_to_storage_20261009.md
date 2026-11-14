# 保存先監視稿と総合稿の独立レビュー

確認日：2026-10-09。担当：SaaS製品調査担当からストレージ稿・総合稿への独立レビュー。公開取得資料と公式公開文書のみを確認し、非公開実装、顧客接続、製品操作、通信監査は対象としない。

対象：

- [ストレージ稿](telescreen_related_storage_monitoring_20261009.md)
- [総合稿](telescreen_related_systems_20261009.md)
- [ストレージ取得台帳](telescreen_related_storage_sources_20261009.json)

## 結果

**確認した重要境界について、必須の内容訂正は見つからなかった。** 網羅的な製品操作試験や全引用の再取得を行ったという意味ではない。補強事項を1件記載する。

| ID | 優先度 | 確認・補強事項 | 判断 |
|---|---|---|---|
| S-R1 | 低 | 本文が引用するRubrik `actions_available_data_security_policies.html` がストレージ台帳にない。検索経由で公開公式本文を確認したがHTML原本未保存である旨を台帳にも追加する | 記述自体は支持される。取得経路の追跡性を補強する提案 |

## 原本と照合した主要事項

### Datadog：S3内容検査とログと設定不備を分離している

保存原本 `storage/datadog_s3.txt` L2845–2855 は、顧客環境で管理するEC2検査器がS3テキストを読み、検出規則種と一致位置をDatadogへ送ると説明する。原文非送信はこの機構の説明である。L2907–2911には `s3:GetObject`、`kms:Decrypt` 等があり、検査器まで本文を読まない方式とはいえない。

`storage/datadog_investigate.txt` L2887–2895の代表ログ最大5件・既定7日保持はログ側の節。L2968–2977はクラウド保存先とファイル、所有者への確認を扱い、L2980–3007の担当・状態・Jira・手順・履歴は関連するCloud Securityの設定不備へ移動した後の操作。両稿はこの範囲を明示し、S3一致ごとに同じ問題状態や原文保持規則が適用されるとは記載していない。[S3検査](https://docs.datadoghq.com/security/sensitive_data_scanner/setup/cloud_storage/)、[調査操作](https://docs.datadoghq.com/security/sensitive_data_scanner/guide/investigate_sensitive_data_findings/?lang_pref=en)

### IBM：完了操作と予定評価は同義ではない

公式公開文書の検索経由本文を独立取得し、保存先に対応するWorkloadでは方針更新後、即時ではなくPending scanに進み、予定された方針実行で違反があればOpenへ戻ると確認した。Workforceは異なる。Allow dataは方針を変更する操作であり、原文削除の証明ではない。両稿の記述は支持される。直接HTTP403であることも台帳・本文で区別している。別の `ibm_rescan.txt` はDSPM分類停止のトラブルシューティングであり、Exposure Managerの状態遷移の原本と混同しない。[Managing issues](https://www.ibm.com/docs/en/exposure-manager?topic=managing-issues)

### Rubrik：閉じる理由はデータ修正だけではない

公開公式文書を検索経由で再確認した。Data Security Posture policiesの継続評価は新規違反と既存違反の解消を扱う。一方、Actions available for data security policiesはDisable/Delete操作でその方針の違反を閉じると説明する。両稿が両条件を記載するのは適切。台帳の5原本は `content_availability: login_page_only` で、公開文書全文を直接取得したとは数えない。検索索引の取得時点は文書更新日・現行契約条件を証明しないため、その限界は残る。[方針](https://docs.rubrik.com/en-us/saas/dspm/dsp_policies.html)、[操作](https://docs.rubrik.com/en-us/saas/dspm/actions_available_data_security_policies.html)

### Cortex：一般提供と予告を分離している

`storage/cortex_ga.txt` L10、L17–21、L27–44から、Cortex Data Securityの一般提供発表は2026-09-15、DLP HarmonizationとUnified DDRは10月リリース予告と確認した。関連リンクにPublic Previewの見出しもあるが、本文は一般提供。`cortex_expansion.txt` L26、L34、L44、L48はCortex Cloudの業務クラウド/Claude対象拡大と、接続先による修正差を説明する。両稿は旧Prisma系機構と現行ブランド、予告機能を区別する。[一般提供発表](https://www.paloaltonetworks.com/blog/security-operations/cortex-data-security-ga-dlp-ddr/)、[対象拡大](https://www.paloaltonetworks.com/blog/cloud-security/expanding-cloud-data-footprint/)

### Concentric：原文破棄と個人情報不保持を混同していない

保存PDFの2025年FAQ pp.1–3を抽出して確認した。自社SaaS内の自社モデルで本文を処理し、抽出原文は処理後破棄する説明。ただし検出した氏名・メールは伏字保存の例外であり、完全な個人情報不保持とはいえない。両稿は例外と第三者AI不使用/顧客内処理の違いを明記する。[FAQ](https://concentric.ai/wp-content/uploads/2025/06/AI_FAQs_June2025-Mary-B.pdf)

## 総合稿の横断確認

Teleskope標準Outpostの遠隔平文処理と顧客内GPU分類の条件差、Nightfallのイベント重複と全コピーの同一問題化の違い、Metomicの現行通信制御への重点移動、Gamma.AIのPalo Alto Networks統合は、SaaS担当の取得資料と整合していた。優先10対象を企業数・実測精度順位とは数えていない。原文非送信・非保持・学習不使用・暗号文分類を分離する説明、確認不能を安全扱いしない設計案も妥当。

企業基盤稿・OSS稿の全コード/全取得原本の再監査は本レビューの範囲外。総合稿のBigID/Cyera/Varonis/GitGuardian/DefectDojo等は、担当詳細稿と各担当の独立レビューによる検証を併用する。保存予定リンクの存在確認とCSV/JSON集計はrootの保存検証が別途担当する。

## 補強の反映確認

S-R1を取得台帳に `rubrik_policy_actions` として追加した。公開検索本文で確認、直接HTML原本未保存の状態を明記し、保存成功件数へ含めない。独立レビューの指摘を統合担当が反映した。
