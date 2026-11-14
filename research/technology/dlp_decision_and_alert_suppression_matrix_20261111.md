# 機密情報検知と判定登録による再通知抑制の製品比較

調査日：2026年11月11日。対象は Google Workspace DLP、Box Shield、Microsoft Purview DLP、Microsoft Defender for Cloud Apps、Nightfall、Amazon Macie、BigID の7製品系統。DLP は機密情報の持ち出しを検知・制御する仕組みを指す。公開公式資料による仕様比較であり、実機で通知経路を検証した結果ではない。

[検知属性・日本語・Google Drive接続・対応ファイル形式・精度・容量の詳細比較](dlp_detection_formats_accuracy_matrix_20261111.md)を追加。Purviewの外部サービス接続の公開試験版は、下表のSharePoint／OneDrive版と別に評価する。

追加調査：[Nightfallの日本語対応](nightfall_japanese_support_20261111.md)、[他製品・OpenAI・Anthropicを含む制約比較](dlp_product_limitations_and_build_options_20261111.md)、[自作の公開事例と設計案](dlp_self_built_cases_20261111.md)、[BigIDの精査](bigid_dlp_api_constraints_20261111.md)。以下の7製品比較での運用機能の評価を、日本語精度の順位とは扱わない。表中のBIはBigID精査稿と同稿の公開一次資料を参照。

Googleの設定・検知記録を取り出す方法は[CLIとAPIの詳細](google_workspace_dlp_cli_api_deep_dive_20261111.md)を参照。現行Policy APIはDLPルールの変更にも対応するが、検知記録・原文抜粋・人の許可台帳とは別に扱う。

**「検知したものを人が OK／NG と判定し、以後の同じ情報の警告を抑える」という要件には、Nightfall の判定一括適用と自動無視が最も直接的に対応する。** Google Workspace は確認済みラベルと検知規則の組合せ、Box は手動分類と上書き制御で近い運用を設計できる。Amazon Macie は文字列の許可リストと検出結果の抑制規則を持つが、S3 専用で、標準の自動探索は抽出検査である。以下で根拠と適用範囲を区別する。

## 判定と抑制の意味

OK は「誤検知」と「機密だがこの用途では許可」を分ける。NG は「実際の機密情報・違反として対応を続ける」とする。NG と登録した後も繰返し通知だけを止め、未解決の問題として残す動作は、OK として無視する動作とは別要件である。

| 機能 | 意味 | 例 |
|---|---|---|
| 判定登録 | 検出の正誤や業務上の許可を人が記録する | 誤検知、真の違反、業務上許可 |
| 重複集約 | 同じ未解決問題を新しい問題として増やさない | 既存の問題に検出箇所を追加 |
| ファイル例外 | 指定したファイルの将来の検出を抑える | 承認済みファイルを無視 |
| 値の例外 | 同じ文字列が別ファイルに現れても判定を適用する | 公開済みの代表電話番号を許可 |
| 通知抑制 | 検出を残しつつ外部通知等を止める | 自動保管して通知先へ送らない |
| 学習 | 判定から未知の類似情報の分類を改善する | 完全一致しない別の文章にも適用 |

完全一致への判定適用と、未知の類似文書への学習は別機能である。通知を終了状態にするだけでは、将来の再通知抑制を証明しない。

## 機能差の比較表

**○：公式資料に直接の仕様説明あり。△：設定による構成、用途限定、または部分対応。未確認：今回確認した公開資料では要件を証明できない。未確認は非対応の断定ではない。** 表中の番号は後述の公式資料に対応する。

| 製品・対象 | 作成・更新の検知 | OK／NG の記録 | 同一ファイルの将来の警告抑制 | 同じ値を別ファイルでも許可 | NG を残した重複抑制 | 変更後に例外を再評価 |
|---|---|---|---|---|---|---|
| **Google Workspace DLP／Drive** | ○ 作成・内容変更で検査。即時完了保証ではない [G1–G2] | △ 人が設定する確認用ラベルで構成 [G3] | △ 「検知条件 AND 確認済みラベルでない」を規則化 [G3–G4] | 未確認。許可値だけを検出箇所単位で除外する機能は未確認 | 未確認。警告の終了と将来抑制の連動は未確認 | △ 内容変更で再検査。ただし確認済みラベルを自動失効させる仕様は未確認 |
| **Box Shield／通常の自動分類** | ○ アップロード・編集等で分類 [B1] | △ 手動で Public／Confidential 等の分類ラベルを設定 [B2] | △ 手動分類の保護・分類済みファイルを飛ばす設定。通知停止専用機能とは異なる [B2] | 未確認。手動分類を別ファイルの同じ値へ自動適用する仕様は未確認 | 未確認。分類と警告の重複管理は別 | △ 最新版への手動上書きは保護。新版まで同じ保護が続く保証へ広げない [B2] |
| **Box Shield Pro／AI Classification** | ○ 有効化後の分類イベントで検査 [B3] | △ 自動分類を手動変更できる競合処理 [B3] | △ 通常分類と同様、手動分類等を保護する設定 [B3] | 未確認 | 未確認 | △ 最新版の手動上書き保護。既存全件の即時再分類ではない [B3] |
| **Microsoft Purview DLP／SharePoint・OneDrive** | ○ 新規・既存ファイルを検査 [M1] | ○ 利用者が誤検知を報告、理由を記録して制限解除可能。許可設定が必要 [M2] | △ ファイル×規則ごとに警告1件。OK登録に起因する恒久例外とは区別 [M3] | 未確認。利用者の誤検知報告が同じ値の全体許可になる仕様は未確認 | ○ ファイル×規則で1件の警告 [M3] | △ 内容・規則の再評価あり。承認解除の範囲・期間は別途確認 [M1–M3] |
| **Microsoft Defender for Cloud Apps／File policies** | ○ 保存済み・新規内容を継続検査 [M4] | ○ 安全と判定したファイルを Authorize で承認 [M4] | ○ 承認したファイルの将来の一致を抑制 [M4] | 未確認。ファイル承認を同じ値の全体許可へ拡張しない | 未確認 | 未確認。内容変更・新版で承認が失効する条件の確認が必要 |
| **Nightfall／Google Drive を中心に比較** | ○ Drive の継続検知・履歴検査 [N1] | ○ 誤検知、違反でない、真の違反を検出箇所ごとに登録 [N2] | ○ Drive の Ignore all は当該ファイルの現在・将来の違反を自動無視 [N3] | ○ 完全一致の検出へ既存・新規の両方で判定適用。全検出が誤検知の問題は自動無視 [N2] | ○ Drive で同じ値・同じファイルは既存の問題へ追加。別ファイル・新しい値は新規 [N4] | △ 値単位なら新しい値は対象外。ファイル丸ごと無視は将来の新しい違反も無視 [N2–N4] |
| **Amazon Macie／Amazon S3** | △ 自動探索は代表的な保存物を抽出検査。全新規作成を即時検査する保証ではない [A1] | △ 許可リスト・抑制規則へ人が反映。二択の判定画面とは異なる [A2–A3] | ○ 検出結果の属性条件による抑制規則で構成 [A3] | ○ 完全一致文字列／正規表現の許可リスト [A2] | △ 検出は続け自動保管。未解決NGを活動中のまま集約する機能とは異なる [A3] | △ 更新後も条件に一致すれば抑制。版変更による承認自動失効は未確認 |
| **BigID／Drive等** | △ 定期検査・検査起動等を確認。Drive更新の最大遅延は未確認 [BI2,BI7,BI9] | ○ 公式MCP説明に結果の正誤判定。業務許可は分離する [BI9] | △ 問題にsilenced状態。ファイルの今後の全検知停止を意味するとは未確認 [BI10] | 未確認。除外一覧は検知報告自体を減らすため、記録を残す許可とは別 [BI9] | △ 方針・保存先等の問題管理。将来の同一問題の集約鍵・再通知条件は未確認 [BI1,BI10] | 未確認。内容・場所・共有変更後の抑制失効・再発条件を要試験 |

**Microsoft Defender for Cloud Apps の File policies は2027年1月6日に廃止予定。** 後継として Purview DLP または自動ラベル付けへの移行が案内されている。Authorize の仕様がそのまま後継に引き継がれるとは確認できないため、新規採用の主候補にはしない。[M4–M5]

## 製品別の適用条件

### Google Workspace

Drive の作成・内容変更による検知と、確認済みラベルを否定条件にする機能は確認できる。ただし「問題一覧で OK を押すと同じ値が全社で許可される」という一連の機能は今回未確認である。[G1–G4]

構成案は、人が変更できる別のラベルに「未確認／誤検知／業務上許可／NG」を用意し、通知規則を `機密情報に一致 AND 確認結果が誤検知でも業務上許可でもない` とする。これは公開仕様からの設計案であり、完成済みの承認機能の紹介ではない。同じ規則でラベルを条件と動作の両方に使えないため、確認用ラベルと自動分類の役割を分ける。[G3]

確認済みラベルが残ったまま内容を変更すると新しい機密情報も通知対象外になり得る。この構成で「確認時点の内容だけを承認」するには、版や内容の変更時に確認状態を戻す追加処理が必要である。Drive の DLP と Gmail の送信時検査は検知の時点が異なるため、この表の作成・更新検知を Gmail 下書きの常時監視へ広げない。[G2]

許可文字列の存在を NOT 条件にすると、許可値以外の秘密を含む文書全体まで対象外にし得る。検出箇所だけを除外する許可リストの代替としては扱わない。[G4]

### Box

通常の自動分類は特定の情報種別・独自語句等への一致でラベルを付ける。文字抽出は先頭1 MB、通常分類は画像内の文字読取りに非対応である。[B1]

分類競合では、手動で最新版の自動分類を変更した場合の保護と、利用者・フォルダー・業務処理等が付けたラベルを飛ばす設定がある。一方、「分類済みを飛ばす」設定でも別の分類規則が付けたラベルは上書き対象になる。確認済み Public ラベルを人が設定し、その分類に応じて制限を変える運用は可能だが、個々の検出値に対する誤検知記録とは異なる。[B2]

AI Classification は Shield Pro の追加機能で、ラベル説明に基づく分類を補う。有効化後の対象イベントが起点で、既存全件の一括検査は標準動作として説明されていない。人の修正が未知の文書への自動学習になるとは確認できない。[B3]

Box の Smart Access の業務理由による例外と、マルウェア検知の「安全とする」は、個人情報検知の恒久的な許可リストと混同しない。[B4]

### Microsoft

Purview は誤検知報告と業務理由付きの制限解除を提供する。これは実際の業務を継続するための操作であり、未知の文書に対する自動学習や同じ値の全体許可を意味しない。SharePoint／OneDrive の「1ファイル×1規則で警告1件」は、OK 判定による許可と独立した重複抑制である。[M1–M3]

Defender for Cloud Apps の Authorize は将来の一致を抑えることが明記されている。ただし前述の廃止予定がある。[M4]

また、2026年10月初旬から Defender XDR 側の組込み調整規則により、DLP の信号を警告ではなく行動記録として扱う変更がある。Purview の検知、Defender の問題一覧、メール通知のどこで抑制を確認するかを決める必要がある。[M6]

### Nightfall

検出箇所単位で「対象情報ではない」「違反ではない」「真の違反」を登録し、完全一致へ今後も判定を適用できる。すべての検出箇所が誤検知になった問題は自動無視され、履歴が残る。1件でも未承認の検出箇所があれば、全件誤検知を条件とする自動無視の条件を満たさない。[N2]

ファイル単位の Ignore all は別機能で、Drive ファイルの現在・将来の違反をまとめて無視し、取消しもできる。同じ承認値だけを抑えて新しい機密値を検知したい用途では、ファイル全体の無視より完全一致への判定適用を優先して検証する。[N3]

これらは判定適用と問題の自動無視の仕様である。外部通知が自動無視より先に送信されないか、メール等を完全に無通知にできるかは接続先・設定ごとの実機確認が必要である。完全一致の照合規則、全接続先間の適用境界、文字正規化も公開記載だけでは確定できない。

### Amazon Macie

許可リストは指定した文字列や正規表現に一致する箇所を検出結果から除外する。検査処理や自動探索に、そのリストを適用する設定が必要である。[A2]

抑制規則は検出自体を止めず、条件に合う結果を自動保管し、Amazon EventBridge と AWS Security Hub CSPM へ送らない。したがって「後で調査できるように残し、再通知を止める」に直接対応する。ただし自動保管と修正済みは別であり、結果の保存は90日である。[A3]

## 選定の目安と確認試験

| 優先する要件 | 候補 | 選定条件 |
|---|---|---|
| 人の判定を登録し同じ値へ今後も適用 | Nightfall | 完全一致の適用境界と、自動無視前の通知順序を試す |
| Google Drive 内で確認済みファイルの通知を抑える | Google Workspace DLP | ラベルで構成。内容変更時の確認取消しを設計する |
| Box 内で人の分類を優先して共有制限を変える | Box Shield | 分類の競合処理と、新版で再判定される条件を試す |
| Microsoft 365 内で理由付き解除と警告集約 | Microsoft Purview DLP | 制限解除と再通知停止を別に検証する |
| S3 の既知の許可値・通知対象を管理 | Amazon Macie | 許可リストと抑制規則を使い分け、検査対象と頻度を設定する |

導入時は、同じ試験用文書で次の動作を確認する。実在者の情報は不要である。

1. 保存しただけで検知・通知されるか。共有操作なしで確認する。
2. 誤検知、機密だが業務上許可、NG を別々に登録できるか。
3. 内容を変えず再保存したとき、検出記録・問題件数・外部通知がどう変わるか。
4. 同じ許可値を別ファイルに記載したとき判定が適用されるか。
5. 許可済みファイルに別の機密値を追記したとき、新規の問題として通知されるか。
6. 外部共有への変更、新版、複製、移動、規則変更で承認が失効するか。
7. 判定取消し、理由・担当者・日時の履歴、例外の期限を管理できるか。

## 公開公式資料

各資料は2026年11月11日に公開本文を確認。番号ごとに、本文で使用した主な根拠を記す。

| 番号 | 資料 | 確認した根拠 |
|---|---|---|
| G1 | [About DLP for Drive](https://knowledge.workspace.google.com/admin/security/about-dlp-for-drive) | 検査対象、既存ファイル再検査、所要時間 |
| G2 | [DLP for Drive FAQ](https://knowledge.workspace.google.com/admin/security/dlp-for-drive-faq) | 内容変更が検査起点、ファイル・規則作成時の警告 |
| G3 | [Apply classification labels to Drive files automatically with DLP rules](https://knowledge.workspace.google.com/admin/security/apply-classification-labels-to-drive-files-automatically-with-dlp-rules) | ラベルの有無・選択値と否定条件、条件とラベル付与の制約 |
| G4 | [Create DLP for Drive rules and custom content detectors](https://knowledge.workspace.google.com/admin/security/create-dlp-for-drive-rules-and-custom-content-detectors) | AND／OR／NOT、独自語句と正規表現、監査のみの規則 |
| B1 | [Classification Policies](https://support.box.com/hc/en-us/articles/1500003376782-Classification-Policies-Automated-Classification) | 分類イベント、既存内容、1 MBと画像の制約 |
| B2 | [Classification Settings](https://support.box.com/hc/en-us/articles/360063660273-Classification-Settings) | 競合処理、最新版の手動変更保護、変更権限 |
| B3 | [AI Classification](https://support.box.com/hc/en-us/articles/44263764561171-AI-Classification) | Shield Pro、有効化後の分類、競合処理 |
| B4 | [Shield Frequently Asked Questions](https://support.box.com/hc/en-us/articles/360043696834-Shield-Frequently-Asked-Questions) | Smart Access とマルウェアの例外、分類との区別 |
| M1 | [Learn about DLP](https://learn.microsoft.com/en-us/purview/dlp-learn-about-dlp) | SharePoint／OneDrive の既存・新規検査、再評価 |
| M2 | [Send email notifications and show policy tips](https://learn.microsoft.com/en-us/purview/dlp-use-notifications-and-policy-tips) | 誤検知報告、理由付き解除、報告記録 |
| M3 | [DLP policy reference](https://learn.microsoft.com/en-us/purview/dlp-policy-reference) | 利用者の解除、SharePoint／OneDrive のファイル×規則で1警告 |
| M4 | [File policies in Microsoft Defender for Cloud Apps](https://learn.microsoft.com/en-us/defender-cloud-apps/data-protection-policies) | 継続検査、Authorize と将来一致抑制、廃止日 |
| M5 | [Migrate file policies to Microsoft Purview](https://learn.microsoft.com/en-us/defender-cloud-apps/migrate-file-policies-to-purview) | 移行先と機能の対応 |
| M6 | [Investigate DLP alerts with Microsoft Defender XDR](https://learn.microsoft.com/en-us/defender-xdr/dlp-investigate-alerts-defender) | 2026年10月の組込み警告調整規則 |
| N1 | [Getting Started for Google Drive](https://help.nightfall.ai/google-drive/getting_started) | Drive の継続監視と履歴検査 |
| N2 | [Data Detection and Response Events](https://help.nightfall.ai/dashboard/sdp_events) | 判定登録、Bulk Annotate、Smart Auto-Ignore、取消し |
| N3 | [Manage Google Drive Events](https://help.nightfall.ai/google-drive/policies/events) | Ignore all、将来の違反、履歴、取消し |
| N4 | [Deduplication and Automatic Resolution of Events](https://help.nightfall.ai/dashboard/sdp_events/deduplication) | 同じ値・同じファイルの集約、新しい値・別ファイルの新規発生 |
| A1 | [Performing automated sensitive data discovery](https://docs.aws.amazon.com/macie/latest/user/discovery-asdd.html) | S3 の代表的な保存物の抽出検査 |
| A2 | [Defining sensitive data exceptions with allow lists](https://docs.aws.amazon.com/macie/latest/user/allow-lists.html) | 完全一致文字列、正規表現、検査への適用 |
| A3 | [Creating a suppression rule for Macie findings](https://docs.aws.amazon.com/macie/latest/user/findings-suppression-rule-create.html) | 自動保管、検出継続、通知先への非送信、90日保存 |
