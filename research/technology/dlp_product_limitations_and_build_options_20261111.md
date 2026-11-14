# 機密情報検知製品と自作部品の制約比較

調査日：2026年11月11日。[属性・形式・容量の詳細表](dlp_detection_formats_accuracy_matrix_20261111.md)、[判定登録・再通知抑制](dlp_decision_and_alert_suppression_matrix_20261111.md)、[Nightfallの日本語精査](nightfall_japanese_support_20261111.md)を補う。

[API対応の追加比較](dlp_related_services_api_matrix_20261111.md)では、BigIDを加え、検知結果・設定・人の判定・再検査を分けて16系統を評価。Stracの誤検知登録、Nightfallの判定自動適用、Teleskopeの再検査等の具体的な操作と制約を整理した。

**Nightfall以外にもGoogle Workspace、Microsoft Purview、Netskope、Strac、Teleskope、BigIDがGoogle Driveを検査する候補になる。OpenAIはPrivacy Filterという手元で動かせる専用検知モデルとAgent Builderの保護機能を提供する。AnthropicにもClaudeでプライバシーに関する分類を組む公式例がある。** 完成品の運用機能と、検知モデル・開発用部品を分けて選ぶ。

以下の「未確認」は、非対応や劣るという断定ではなく、今回の公開資料から採用条件を証明できないもの。デメリットは今回の「場所×属性で許可し、検知を残して通知だけ止める」用途に対する評価である。

## 検知と検査範囲の制約

| 製品・機能 | Google Drive | 日本語で考慮する制約 | 形式・容量・検査漏れの制約 | この用途での主なデメリット |
|---|---|---|---|---|
| Google Workspace DLP | 標準対応 | 日本の識別番号は標準搭載。氏名・住所の日本語実測値は未確認 | 抽出先頭10 MB、非Google形式の文字抽出50 MBまで。Docs等のコメント・保護ファイル・動画音声は検査対象外 [G1,G6] | 検知ログと、値・位置を備えた全件台帳は別。任意フォルダーと子階層の条件指定は要確認 |
| Box Shield 通常分類 | Box内のみ | 氏名・日本語住所・個人番号の専用検知は標準一覧に記載なし | 先頭1 MBの抽出文字。画像内の文字、圧縮内部は対応根拠不足 [B1–B2] | Driveが主保存先なら単独では対象外。1ファイル1分類で、属性の台帳と機密区分が同じではない |
| Box Shield Pro AI分類 | Box内のみ | 日本語の説明入力と、日本語分類の精度保証は別 | 文書2 MB、表・コード100 KB。単独画像は最大2048×2048。PDF・Office内画像には制約 [B3] | 判定の揺れ、有効化前の全件遡及検査の条件、独自分類の評価負担 |
| Nightfall | API接続 | 氏名・住所・日本語OCRの精度は未確認。自然言語指定の箇所検知は6〜128文字 [NF] | 共通仕様1 GB。接続別・展開後・日本語OCRの上限は要確認 | 標準の日本語氏名・住所検知を前提に採用できない。通知管理の充実と日本語品質を分ける |
| Purview 外部サービス接続 | 公開試験版 | 日本語氏名・住所の分類器は存在。Driveでの分類器別の適用範囲は検証が必要 | PDF・暗号化ファイル非対応。Microsoft 365のOCR仕様を流用しない [M7] | Content explorer非対応。活動ログは見られるが、外部の原文・検出値を同じ画面で全件把握できるとは限らない |
| Defender for Cloud Apps File policies | API接続 | 分類器と接続先を分けて検証 | 2027年1月6日廃止予定 [M4–M5] | Authorizeによる将来一致抑制はあるが、新規投資の主候補にしにくい |
| Amazon Macie | 対象外、S3のみ | 国別検知を日本語全般へ拡張しない | 自動探索は抽出検査。画像・動画音声非対応。PowerPointは標準形式一覧に記載なし [A1,A4] | Driveからの転送・文字抽出・巡回を別に作る必要がある |
| Netskope API Data Protection | API接続 | 日本語日付・旅券周辺語句の改善履歴あり。日本語氏名・住所の同条件評価は今回未確認 [X2] | 旧方式とNext Gen、通信中検査は上限が異なる。過去の128 MB対応や32 MB既定値を現契約の上限と断定しない [X3] | 外部所有ファイルの更新通知が得られない等、Google側イベントの制約 [X1] |
| Strac | API接続 | 日本の旅券番号を一覧に記載。日本語氏名・住所・個人番号の検知精度は未確認 [X5] | Docs・Sheets・PDF・画像、共通一覧でDOCX・XLSX・MSG等。Drive接続の全形式・容量・圧縮上限は要確認 [X4–X5] | 製品説明は豊富だが、判定継承・再通知抑制の照合条件を確定できる公開操作仕様は今回不足 |
| Teleskope | API接続 | 今回取得した接続・問題管理の資料だけでは日本語の分類器別精度を証明できない | 接続先ごとの検査可能形式・OCR・サイズ上限は個別確認 [X6–X7] | 所有者・共有・機密属性を組み合わせられるが、形式別・日本語別の保証の確認が残る |
| BigID | API接続。共有ドライブ等を明示 | 多言語の製品説明はあるが、日本語の氏名・住所・番号の属性別精度は未確認 | Docs・Sheets・Slides・PDF・文書等。拡張子別、画像PDF、埋込み画像、圧縮内部、容量は未確認 | 問題一覧と資産一覧が別。silencedを場所×属性の恒久許可と扱わない。全件出力には通常の一覧と別のAPIが必要 [BI] |
| OpenAI Privacy Filter | 接続は自作 | 日本語の合成評価を公開。日本の番号体系の専用検証・実業務精度とは別 [O2] | 文字列を受けるモデル。PDF・Office抽出、OCR、圧縮展開は別途必要。最大128,000トークン [O1] | 台帳・巡回・承認・通知・例外失効は自作。言語・用途により見逃しと過剰検知 |
| OpenAI Agent Builderの保護機能 | 継続巡回は自作 | 個人情報の伏字化を提供。日本語属性別の数値は今回未確認 [O3] | 入力・処理手順中の検査。保存先の全件検査機能としては扱わない | Drive接続を付けただけで検査台帳と通知管理が完成するわけではない |
| Anthropic Claudeによる独自分類 | 継続巡回は自作 | 多言語分類とPrivacy分類を公式例で説明。日本語の全箇所抽出精度の保証ではない [C1] | モデルが読める入力と、ファイル全体・埋込み画像の網羅性は別 | 原文の取得・分類規則・評価・台帳・通知制御・費用管理を開発する必要がある |

## 例外設定と運用上の副作用

| 製品群 | 許可・通知抑制で注意する点 | 導入権限・処理・契約の条件 |
|---|---|---|
| Google Workspace | ファイルの許可ラベルが残ると、新たに追加した機密情報まで警告対象外にし得る。内容変更時に許可状態を失効させる仕組みが必要 | 対応Workspace契約、DLP管理権限。利用者側で暗号化した本文は検査不可。未暗号化の属性は別 [X8] |
| Box通常・AI | 手動分類を保護する設定は、値単位の誤検知承認ではない。機密内容を削除しても、無効化・削除した規則のラベルが自動で消えるとは限らない [B1–B3] | Shield／Shield Pro契約。分類変更権限を誰へ与えるか決める。AI分類は1企業1規則で、通常分類と合計50規則の制限 [B3] |
| Nightfall | Ignore allは将来の別の違反も無視。検知器のExcludeは検知記録自体を消すため、記録のみの許可運用と異なる | Workspace管理者による接続承認。30日以内の検出値は伏字なしで閲覧・出力する機能があり、指紋だけを持つ方式ではない [NF,X9] |
| Purview外部接続 | 利用者の解除、利用者向け警告、シミュレーションは非対応。Microsoft 365版の操作をそのまま期待しない [M7] | Defender for Cloud Apps接続とPurview権限が必要。組織への段階提供、契約・追加費用の適用範囲を確認 |
| Defender旧方式 | Authorizeが内容更新・新版・規則変更で失効する条件は要確認 | 廃止前の移行が必要。後継で同じ例外動作が続くとは保証しない |
| Macie | 許可リストは該当値を報告しない。検知を残すなら抑制規則を使い分ける。自動保管は修正済みの証拠ではない [A2–A3] | S3と必要な復号権限、検査量の費用。検出結果は90日保存で、長期台帳は別途設計 |
| Netskope | 「通知しない」「問題を無視する」「検査対象外」を区別。API方式とブラウザー等の通信中検査を混同しない | 組織全体へのアクセス委任と広いDrive権限。Basic等の古い契約名称に基づく資料は現契約との対応を要確認 [X1] |
| Strac | 伏字化・公開権限解除は原本や利用者の業務へ影響する。記録のみの運用に修正動作を付けない | 日本語・検出値の保持・処理地域・権限の内訳・費用は契約条件と設定を確認。宣伝上の低誤検知率を比較精度として採用しない |
| Teleskope | Ignored／Resolvedは手動の状態変更も可能。修正後の原本再検査や将来の再発識別と同一視しない [X6] | Drive接続は組織全体の権限委任、専用サービスアカウント、管理用ユーザーを要求 [X7] |
| BigID | 誤検知の判定、問題のsilenced、原本修正、除外一覧を分離。公開例のresolved変更は、原本の修正・再検査を要求する処理ではない | DSPM／問題管理と原本修正は契約・権限を分けて確認。検査器の配置だけで原文無送信・無保存と断定しない。抜粋の外部保存機能もある [BI] |
| OpenAI Privacy Filter | 8分類と自社の許可属性が一致しない場合は後処理・追加規則・学習が必要。マスキングを不可逆な匿名化と扱わない | Apache-2.0の公開重み。総パラメーター15億、処理時に使う部分5,000万。実行環境とモデル管理は自社負担 [O1] |
| OpenAI API／Anthropic API | 指示しただけで全件・全箇所を検出する保証はない。モデル変更時の再評価が必要 | 入力した原文を提供者へ送る経路になる。必要な保持・処理条件は利用API・契約ごとに確認。手元で動かすモデルと区別 |

保存データの検査は、作成直後の持ち出しを必ず先に止める方式とは異なる。原本変更・共有先変更・コピー・移動を新たな評価条件にしないと、過去の許可を別の用途へ誤って適用し得る。これらは製品横断の設計上の注意で、各製品に実際に同じ不具合があるという指摘ではない。

## OpenAIとAnthropicの提供範囲

| 項目 | OpenAI Privacy Filter | OpenAI Agent Builder | Anthropic Claude |
|---|---|---|---|
| 提供形態 | 専用の公開重みモデル | 処理手順に組み込む保護機能 | APIで独自分類を組む公式例 |
| 個人情報の検知・伏字化 | 8分類の箇所検知 | 組込みの個人情報伏字化 | Privacy等の独自基準で分類する例 |
| 手元での実行 | 可能 | 手元だけでの実行とは扱わない | 公開重みを手元で動かす方式とは扱わない |
| Drive巡回・検知台帳・許可場所・再通知抑制 | 別途実装 | 別途実装 | 別途実装 |
| 今回の根拠で言える範囲 | 自作の検知エンジン候補 | AI処理の途中を保護する開発部品 | 自作の分類処理候補 |

Anthropicは内部で機微情報を除去・曖昧化する仕組みも説明しているが、その説明だけで、顧客が入手できる専用DLP製品や公開重みモデルがあるとは判断しない。[C2]

OpenAI Privacy Filterは2026年4月22日公開。日本語の合成評価は、モデル説明資料の表7が968例、適合率89.7%、再現率86.6%、F1値88.1%。別の「カテゴリの手掛かりを前に置く」条件の表8は1,189例、適合率90.0%、再現率75.8%である。同じ日本語でも条件で結果が変わり、実業務文書の精度・氏名等の個別精度・Nightfallとの直接比較には使えない。[O1–O2]

## 追加で確認した公式資料

G・B・M・N・Aの既存番号は[形式と精度の比較](dlp_detection_formats_accuracy_matrix_20261111.md#公式資料)と[判定登録の比較](dlp_decision_and_alert_suppression_matrix_20261111.md#公開公式資料)を参照。NFは[Nightfall精査](nightfall_japanese_support_20261111.md)。

BIは[BigIDのAPI・日本語・形式・許可運用の精査](bigid_dlp_api_constraints_20261111.md)と、同稿BI1〜BI15の公開一次資料を参照。

| 番号 | 公開資料 |
|---|---|
| X1 | [Netskope Google Drive API接続](https://docs.netskope.com/en/configure-google-drive-for-api-data-protection) |
| X2 | [Netskope 109.0.0変更履歴](https://docs.netskope.com/en/netskope-release-notes-version-109-0-0) |
| X3 | [Netskope 103.0.0変更履歴](https://docs.netskope.com/en/netskope-release-notes-version-103-0-0) |
| X4 | [Strac Google Drive DLP](https://www.strac.io/integration/google-drive-dlp) |
| X5 | [Strac検知対象・形式一覧](https://www.strac.io/blog/strac-catalog-of-sensitive-data-elements) |
| X6 | [Teleskope Policy Maker](https://docs.teleskope.ai/the-platform/policy-maker) |
| X7 | [Teleskope Google Drive接続](https://docs.teleskope.ai/connectors/saas/filesharing/google-drive) |
| X8 | [Google利用者側暗号化FAQ](https://knowledge.workspace.google.com/admin/security/client-side-encryption-faq) |
| X9 | [Nightfall検出結果の出力](https://help.nightfall.ai/dashboard/sdp_events) |
| O1 | [OpenAI Privacy Filter発表](https://openai.com/index/introducing-openai-privacy-filter/) |
| O2 | [OpenAI Privacy Filter Model Card](https://cdn.openai.com/pdf/c66281ed-b638-456a-8ce1-97e9f5264a90/OpenAI-Privacy-Filter-Model-Card.pdf)（表7・8、PDF 18・19ページ） |
| O3 | [OpenAI Agent Builderの入力保護](https://developers.openai.com/api/docs/guides/agent-builder-safety#use-guardrails-for-user-inputs)・[Guardrailsノード](https://developers.openai.com/api/docs/guides/node-reference#guardrails) |
| C1 | [Claude Content moderation公式構築例](https://platform.claude.com/docs/en/about-claude/use-case-guides/content-moderation) |
| C2 | [Anthropicの機微情報の処理説明](https://support.anthropic.com/en/articles/8325621-i-would-like-to-input-sensitive-data-into-my-free-pro-or-max-plan-claude-account-who-can-view-my-conversations) |
