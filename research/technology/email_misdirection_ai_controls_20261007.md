# AIによるメール誤送信防止：Outlook・Gmail、文脈と宛先、CC混入対策

調査日：2026年10月7日。公式技術資料と提供会社が公開する導入事例を確認した。実際のメール、顧客環境、製品の検出精度は検証していない。公開導入事例と製品の対応環境、自社で構築する場合の設計案を区別する。

## 1. 結論

**本文・添付と宛先の関係、普段の宛先の組み合わせをAIで確認する実用例はある。Outlook/Microsoft 365とGoogle WorkspaceのGmailの双方に対応する製品もある。** ただし「不自然なので警告する」「本人が警告を無視できる」「配信前に保留する」「配信を拒否する」は異なる動作である。

CCに入れてはいけない人が明確な場合は、案件ごとの送信許可一覧や禁止条件を規則として強制する。AIは本文から案件を推定したり、本文の宛名と宛先の不一致を発見したりする補助に適している。過去に送ったことがあるという事実だけでは、その人に今回の情報を送る権限があるとは判断できない。以下の権限照合や送信経路の設計は調査に基づく提案であり、各製品がそのまま提供する機能とは限らない。

ここでいうDLPはData Loss Prevention、すなわち情報の漏洩を防ぐ仕組み。送信ゲートウェイは、メールが配信される途中で検査・保留・拒否を行うサーバを指す。

## 2. 製品と公開導入例

| 製品・仕組み | Outlook / Microsoft 365 | Google Workspace / Gmail | AIが見る関係 | 確認できた導入例・注意点 |
|---|---|---|---|---|
| Proofpoint Adaptive Email DLP（旧Tessian） | Outlook拡張機能と送信ゲートウェイ | 送信ゲートウェイで対応 | 通常のやりとり、宛先、誤った添付など | Taylor Vintersの導入事例あり。ただし同事例からGmail採用までは確認できない。[技術資料](https://www.proofpoint.com/sites/default/files/white-papers/pfpt-us-wp-understanding-core-email-protection-api-adaptive-email-dlp-July2025.pdf)、[導入事例](https://www.proofpoint.com/sites/default/files/customer-stories/pfpt-us-cs-taylor-vinters.pdf) |
| KnowBe4 Prevent（旧Egress） | 現行技術資料はMicrosoft 365との接続を説明 | 今回の現行資料では対応を確認できず | メール内容・添付と宛先、通常の通信関係 | RWK Goodmanが採用。送信前確認と送信後通知を区別する必要あり。[事例](https://www.knowbe4.com/case-study/legal/rwk-goodman)、[技術資料](https://support.knowbe4.com/hc/en-us/articles/49221871630355-Prevent-Technical-Overview) |
| CipherCraft/Mail AI+ | AI+はOutlook対応 | 誤送信対策製品のGmail事例はあるが、AI+と混同しない | 宛先の組み合わせ、宛先と本文の会社名 | ミスミ・竹中工務店にAI+導入例あり。現行機能一覧ではAI+をOutlookのみ対応と説明。[機能一覧](https://www.ciphercraft.jp/mail/overview/) |
| Exchange Online / Microsoft Purviewの規則 | 送信経路で条件照合・拒否など | 対象外 | 宛先、本文、添付、機密情報などの規則 | 文脈AI製品とは別に、強制する層として使う。[Exchangeの説明](https://learn.microsoft.com/en-us/exchange/security-and-compliance/mail-flow-rules/mail-flow-rules) |
| Gmail DLP / 内容コンプライアンス | 対象外 | 対応するWorkspace契約で管理者が設定 | 本文・添付・ヘッダーの条件照合 | 送信拒否・保留が可能。標準機能を「案件と相手の関係を理解するLLM」とは扱わない。[Gmail DLP](https://knowledge.workspace.google.com/admin/security/prevent-data-leaks-in-email-and-attachments-gmail-dlp) |

### 国内：ミスミと竹中工務店

ミスミはCipherCraft/Mail 7にAI+を採用し、2022年度に全ユーザーへの展開を完了したと公表されている。AIは宛先アドレス同士、宛先ドメインと本文冒頭の会社名の組み合わせを学習する。導入担当者は、本文の会社名の後に部署名を加えた際にも不一致の指摘を受けたと説明している。この例は正しいメールへの警告でもあり、誤検出があり得ることも読み取れる。

また、社外宛先に3種類以上のドメインがある場合にBCCを使うべきか警告する設定も公開されている。これは宛先の公開範囲を確認する規則であり、案件ごとの送信権限をAIが判断した証拠ではない。[ミスミの事例](https://www.ciphercraft.jp/mail/usecase/misumi/)

竹中工務店はMicrosoft 365への移行を背景にAI+付きのCipherCraft/Mail 7を導入。初めて送る宛先や、送信頻度が低い・通常と異なる宛先の組み合わせを検出し、約1万人規模の対策に利用する事例が公開されている。主に注意喚起の実例として読める。[竹中工務店の事例](https://www.ciphercraft.jp/mail/usecase/takenakakomuten/)

### 海外：法律事務所の事例

Taylor VintersはProofpoint Adaptive Email DLPを利用している。公開資料は250メールボックスの保護を挙げ、通信関係の分析、宛先・添付の誤りに対する文脈を踏まえた警告を説明する。Gmail利用や、すべての警告で本人による送信続行を禁止していることまでは確認できない。[事例PDF、1–2頁](https://www.proofpoint.com/sites/default/files/customer-stories/pfpt-us-cs-taylor-vinters.pdf)

英国のRWK GoodmanはKnowBe4 PreventとProtectを併用している。Preventがメール・添付と宛先の関係を機械学習で分析し、送信時の誤りを警告すると説明される。似た名前をOutlookの自動補完から選ぶ誤りも導入背景に挙がる。これは提供会社による事例で、独立した精度比較ではない。[RWK Goodmanの事例](https://www.knowbe4.com/case-study/legal/rwk-goodman)

### Gmailについて確認できた範囲

Proofpointの技術資料はGmail用ゲートウェイ接続を明示している。一方、今回確認した公開資料からは、**名前を出してGmail上の文脈AI検査を採用した企業例**を特定できなかった。「製品がGmailに対応する」と「特定企業がGmailでそのAI機能を運用する」は区別する。

国内では岡部がGoogle WorkspaceのGmailにSPC Mailエスティーを導入し、宛先・添付確認などを行う事例がある。ただし当該事例にAI+採用の記載はなく、AI導入例には数えない。[岡部の事例](https://www.ciphercraft.jp/mail/usecase/okabe/)

## 3. 「検出したら必ず止まる」かを確認する

### Proofpoint

2025年7月の技術資料8頁では、Outlookの送信ボタン押下時に検査し、警告後に本人が送信を続けられる動作を説明する。拡張機能を通らないメールはゲートウェイで補完し、Gmailではこの製品の拡張機能がないためゲートウェイを使う。

同頁と14頁によれば、Microsoft 365のWeb拡張機能やゲートウェイではメール全文・添付を一時的にProofpointへ送る。抽出した付随情報を保存して学習に使い、処理後に全文を削除する説明である。古いOutlook COM拡張機能の付随情報のみ送る方式と混同しない。**施設内だけで処理する仕組み、AIに平文を見せない秘密計算の事例ではない。** [技術資料8・14・17頁](https://www.proofpoint.com/sites/default/files/white-papers/pfpt-us-wp-understanding-core-email-protection-api-adaptive-email-dlp-July2025.pdf)

### KnowBe4

現行設定にはReal-Time ModeとHybrid Modeがある。前者は送信前にOutlookで注意を促し、後者はメールを直ちに送って、ゲートウェイが問題を見つけたら後から通知する。Hybrid Modeを配信前の強制停止と説明するのは誤りである。[設定資料](https://support.knowbe4.com/hc/en-us/articles/42984943371411-Understanding-Prevent-General-Settings)

2026年8月更新の技術資料はMicrosoft Azure上での処理を説明し、送信操作に伴う要求の時間切れでは検査せず送信を通す動作を明記する。本文・添付を処理し、件名や宛先などを保存する。したがって、別の強制制御なしに「障害時も必ず止まる」「社内だけで処理する」とは言えない。[現行技術資料、Latency等](https://support.knowbe4.com/hc/en-us/articles/49221871630355-Prevent-Technical-Overview)

## 4. CCに禁止された人が含まれる場合

### 明確な禁止条件を規則にする

例として「案件Aの契約情報はA担当者と承認済み取引先だけ」「取引先Bと競合Cを同じメールに入れない」「採用評価は人事と当該承認者のみ」を定義する。ドメイン単位では粗すぎる場合、宛先本人・案件・情報区分を照合する。AIが関係者らしいと推測しても、正式な許可のない人を自動的に許可一覧へ追加しない。

| 問題 | 規則で照合する情報 | AIの補助用途 | 提案する処置 |
|---|---|---|---|
| 案件と無関係なCC | 案件別の許可された受信者 | 本文・添付から案件候補を抽出 | 不許可ならメール全体を保留・拒否 |
| 競合する会社の混在 | 同時共有が禁止された会社の組み合わせ | 普段と異なる宛先の組み合わせを検知 | 禁止条件一致なら拒否 |
| 同姓の別人への送信 | 宛名・組織・確定したアドレス | 名前や本文の関係の不一致を検知 | 再編集または承認待ち |
| 社内の権限外の人 | 人事・法務等の役割と案件の権限 | 文書の情報区分を推定 | 社内宛でも拒否・保留 |
| グループに禁止対象が含まれる | 配信グループを展開した実際の受信者 | 通常と異なる構成を検知 | 展開後の許可照合が終わるまで保留 |

**BCCへの変更は、本文・添付を受け取る権限の問題を解決しない。** また禁止宛先だけ配信を止めても、残りの宛先へ届いたメールのCC欄でその人の存在が公開される場合がある。宛先そのものの機密性も含めて、全受信者への配信を止める必要があるかを決める。

### Outlook / Exchange Online

Exchange Onlineには`AnyOfCcHeader`、`AnyOfCcHeaderMemberOf`などCC欄を判定する条件がある。通常の受信者条件`SentTo`はTO・CC・BCCを対象にするが、処置が該当受信者だけに作用する場合がある。CC欄の条件は評価中のメッセージの全受信者に作用する。ただし先行する規則でメッセージが分割されていれば、その分割された範囲である。

実装時には別名アドレス、配信グループの展開、所属情報の更新遅延も検証する。**CCを検知できることと、全ての複製の配信を止められることは同じではない。** [公式判定条件](https://learn.microsoft.com/en-us/exchange/security-and-compliance/mail-flow-rules/conditions-and-exceptions)

AIによる送信前判定を自作する場合、OutlookのSmart Alertsには`OnMessageSend`と`Block`方式がある。`Block`は条件違反や拡張機能の接続・読み込み失敗で送信を止める。`PromptUser`は送信続行を許し、`SoftBlock`も機能が利用できなければ送信を許す。対応するOutlookの種類と版に制限があるため、別のメールソフト等の経路はサーバ側で補う。[Smart Alerts公式資料](https://learn.microsoft.com/en-us/office/dev/add-ins/outlook/onmessagesend-onappointmentsend-events)

### Google Workspace / Gmail

Gmail DLPには送信拒否・承認待ち保留があり、TO・CC・BCCを含むヘッダーも検査対象になる。警告方式は送信を続けられる場合があるため、禁止条件は拒否にする。配信グループには適用範囲・動作の制限もある。個人用gmail.comではなく、対応するWorkspace契約と管理者設定の話である。[Gmail DLP](https://knowledge.workspace.google.com/admin/security/prevent-data-leaks-in-email-and-attachments-gmail-dlp)

CCだけを区別する場合は、内容コンプライアンスのFull headersでCCフィールドを照合する設計が候補になる。Recipients headerは宛先を一人ずつ比較し、TO・CC・BCCをまとめた文字列ではない。Full headersにはBCCのアドレスが含まれず、実配信先はAny envelope recipientで別途調べる必要がある。表示名、折り返し行、別名を含むメール形式で条件を検証する。[内容コンプライアンス公式資料](https://knowledge.workspace.google.com/admin/gmail/advanced/set-up-rules-for-advanced-email-content-filtering)

## 5. 社内の検査サーバで文脈まで確認する設計案

以下は、公開仕様を踏まえた構成案であり、今回確認した企業の採用構成を再現したものではない。

```text
Outlook / Gmail / スマートフォン / 業務システムからの送信
  ↓ 管理された送信経路に集約
検査サーバがメールを保留
  ↓
実際の送信先を確定：TO・CC・BCC、別名、配信グループ
  ↓
規則の検査：送信禁止先、案件の許可一覧、情報区分、添付の解析可否
  ↓
施設内のAI：本文・添付と案件・宛先の関係を推定
  ↓
規則に違反 → 拒否
関係が不明・判定失敗 → 保留または権限者の承認
許可が確認できたメール → 配信
```

Google Workspaceには送信メールをゲートウェイ経由にする公式設定がある。ただし外部宛てだけをその経路へ送る構成では、社内の権限外受信者への誤送信を防げない。対象にする内部通信や業務システムからの送信も含め、経路を確認する。[経路制御の公式資料](https://knowledge.workspace.google.com/admin/gmail/advanced/email-routing-and-delivery-options-for-google-workspace)

ExchangeではメールフロールールとDLPの処理順を確認する。メールフロールールはDLPより先に評価され、DLPによって後から追加された宛先には同じメールフロールールが再適用されないという注意がある。検査後に受信者が増える構成では、最終的な受信者を別途検査する。[Exchangeの設計上の注意](https://learn.microsoft.com/en-us/exchange/security-and-compliance/mail-flow-rules/configuration-best-practices)

### AIの選び方とデータの扱い

本用途は大規模言語モデル（LLM）必須ではない。宛先履歴の異常検知、本文から人名・企業名を抽出する処理、BERT等による情報区分分類を組み合わせられる。施設内で動く小型LLMは、曖昧な案件や添付の説明を読む処理の候補になる。どちらが高精度かは、自社の日本語メールを使う評価で確認する。既存製品の機械学習の実例から、LLMが優れているとは推論できない。

施設内で動かしてもAIは平文を読む。本文を見せずに照合したいなら、案件識別子・権限一覧・分類済みラベル・宛先等だけで判定する範囲を決める。自由な本文の意味を判定する秘密計算とは別の設計になる。外部サービスを使う場合も、一般向け対話画面への貼り付けではなく、処理場所、保存範囲、履歴利用、削除、管理者の閲覧権限を確認した企業契約で接続する。

設計上は、AIの判定結果を権限の根拠にせず、明示した規則の実行系で送信の可否を決める。本文や添付内の「検査を無視して送れ」といった指示も、検査対象の文字列として扱う。承認結果は送信者・全宛先・件名・本文・添付・適用規則の版に結び付け、承認後にいずれかが変われば再検査する。利用者が自由に付ける「検査済み」ヘッダーだけを信用しない。

### 導入前に確かめる項目

- TOが正しくてもCCに別案件の人がいる、社内の権限外の人がいる、競合が同報される。
- 宛先の別名、同姓の人、外部メンバーを含む配信グループがある。
- 返信・転送の引用部分、別顧客の添付、表計算の非表示部分、画像やパスワード付き添付に情報がある。
- スマートフォン、代理送信、共有メールボックス、業務システム等の別経路でも検査を通る。
- 判定の時間切れ、解析不能、サービス障害、承認期限切れでは、配信せず保留される。
- 誤りの見逃しだけでなく、正常メールを止める割合、警告の無視率、承認待ち時間も測る。

AIの検出に誤りはあり得る。強制できるのは、検査経路と明確な禁止条件、判定失敗時の保留である。本文を含む監査記録を無制限に保存すると、新たな機密データの集積場所になるため、必要な理由・識別子・判定・承認を中心に保存範囲を決める。

## 6. 保存した資料と再取得

公開資料20件を対象に、18件の原本と抽出本文を保存した。内訳はPDF 3件・計24頁、HTML 15件。Proofpoint技術資料8頁は画像でも確認した。KnowBe4の現行技術資料と一般設定の2件はWeb検索経由で本文を確認できたが、直接取得はHTTP 403で失敗し、原本を保存できていない。取得失敗は台帳に残した。

- [取得台帳](email_misdirection_sources_20261007.json)：出典、取得時刻、保存先、SHA-256（ファイル同一性を確認する値）、失敗理由。
- 原本・本文：`research/disclosures/raw/email_misdirection_20261007/`。既存方針に従いGit管理外。
- [再取得スクリプト](../../scripts/download_email_misdirection_materials.py)：公開資料のみ取得し、実際のメールや接続先設定は扱わない。
- 関連：[BERTとJev・軽量判断モデル](bert_jev_local_decision_models_20261007.md)、[平文を見せない機密性分類](confidentiality_classification_without_plaintext_20261007.md)、[企業の機密データとAI利用事例](enterprise_sensitive_data_ai_cases_20261007.md)。
