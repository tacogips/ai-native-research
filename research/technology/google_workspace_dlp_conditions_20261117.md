# Google Workspace DLPで設定できる条件と再利用の方法

Google Driveのデータ保護規則について、何を検査するか、どう一致させるか、どの定義を別の規則から使えるかを整理する。DLPは機微情報の検知と持ち出し制御を行う機能である。語句一覧や正規表現は独立した検知器として共用できるが、検査対象、件数、条件の組み合わせは規則側で設定する。以下は2026年11月17日に確認した公開仕様に基づく。実環境の設定や実測結果は含まない。

## 条件の種類と設定画面

| 種類 | 意味と設定する場所 | 別の規則での利用 |
|---|---|---|
| Content conditions 文書内容の条件 | 規則の作成・編集で、検査対象と一致方法を指定する | 検知器を共用できる。AND／ORなどで組み立てた条件全体を独立した名前付き定義として共用する機能は、確認した公開仕様にはない |
| Custom content detector 独自検知器 | 管理コンソール → セキュリティ → アクセスとデータ管理 → データ保護 → 検知器を管理 | 正規表現・語句一覧を保存し、各規則から参照する |
| Context conditions 利用状況の条件 | 規則の該当欄で既存の条件を選択、または新規作成する | IPアドレス、地域、端末状態などの名前付き定義を共用する。Driveではダウンロード・印刷・コピー禁止の動作に限定 |
| Sharing conditions 共有先の条件 | Driveの共有遮断を選択した規則で共有先を指定する | 共有を許可・拒否する組織部門、グループ、ドメインを選ぶ |

規則作成の入口は「管理コンソール → ルール → ルールを作成 → データ保護」。対象アプリと動作を選択した後に、適用範囲と内容の条件を設定する。[規則作成](https://knowledge.workspace.google.com/admin/security/create-data-protection-rules)、[独自検知器](https://knowledge.workspace.google.com/admin/security/custom-content-detectors)、[利用状況の条件](https://knowledge.workspace.google.com/admin/security/combine-dlp-rules-with-context-aware-access-conditions)

「ルールログイベント」のCondition builderは、記録を検索する条件であり、DLPの検知条件は変更しない。[記録の検索条件](https://knowledge.workspace.google.com/admin/reports/rule-log-events)

## 検査対象として選べるもの

Driveの公開仕様には、次の組み合わせが示されている。対象アプリを変えると、同じ項目が使えるとは限らない。

| Content type to scan 検査対象 | What to scan for 一致方法 |
|---|---|
| All content 全内容 | 標準検知器、文字列、正規表現、語句一覧。タイトル・本文・変更提案を含む |
| Body 本文 | 標準検知器、文字列、正規表現、語句一覧 |
| Suggested edits 変更提案 | 標準検知器、文字列、単語、正規表現、語句一覧 |
| Title タイトル | 上記に加えて、指定文字列で始まる・終わる |
| File name ファイル名 | 文字列または単語を含む |
| File extension 拡張子 | 指定した拡張子に一致。`pdf`のように先頭のピリオドを付けない |
| File type ファイル形式 | 一般的なMIME型、独自のMIME型、システムのファイル分類。MIME型はデータ形式を示す識別子 |
| Classification label 分類ラベル | ラベルの存在や、対応する選択肢型フィールドの値 |
| File encryption status 暗号化状態 | クライアント側で暗号化されている／いない。クライアント側暗号化は端末側で内容を暗号化する方式 |

拡張子とファイル形式は別の判定である。名前が`.pdf`で終わることだけでは内容の形式を保証しない。暗号化状態の一致も、暗号化された本文を読んで検知できたことを意味しない。[Driveの条件一覧](https://knowledge.workspace.google.com/admin/security/about-dlp-for-drive)

## 標準検知器と一致の閾値

`Matches predefined data type`ではGoogleが用意した情報の種類を選ぶ。例はクレジットカード番号、メールアドレス、電話番号、国別の識別番号である。国別・全世界向けの区分を確認する。Google CloudのSensitive Data Protectionという別製品の全検知器が、そのままWorkspaceで使えるとは限らない。[標準検知器一覧](https://knowledge.workspace.google.com/admin/security/how-to-use-predefined-content-detectors)

| 項目 | 意味と設計上の注意 |
|---|---|
| Likelihood threshold 検知の確からしさの下限 | 判定を採用する最低水準。百分率の精度や同じ文書を抽選する確率ではない。高い設定では拾う範囲が狭くなり得る |
| Minimum unique matches 異なる一致値の最低数 | 同じ値の繰り返しと、複数の異なる値を区別するための数 |
| Minimum match count 一致回数の最低数 | 一致した出現回数の下限。異なる値の数とは別に設定する |
| Use proximity matching 近接一致 | 標準検知器の一致が、指定した正規表現の前後何文字以内にあるかを追加条件にする |

例えば同じ番号を3回記載した資料は、出現回数3でも異なる値は1、という違いを試験する。近接一致に使う正規表現は検知器として事前に定義する。Sheetsの近接一致は同じセル内に限られ、隣のセルや行まで探さない。[近接一致](https://knowledge.workspace.google.com/admin/security/how-to-use-predefined-content-detectors)、[閾値と件数のAPI仕様](https://docs.cloud.google.com/identity/docs/concepts/supported-policy-api-settings)

## 語句一覧と文字列の条件

`Matches words from word list`は、保存した語句一覧の検知器を規則から選択する方式である。独自検知器の作成画面では、名前・説明とカンマ区切りの語句を入力する。規則側では一覧名、一致方式、最低検出回数などを指定する。

| 項目 | 説明 |
|---|---|
| 語句の扱い | 大文字小文字と記号を無視し、単語全体が一致する。各語は英数字2文字以上という制約が公式説明にある |
| 日本語の注意 | 日本語の語の境界や部分一致の扱いは、この説明だけでは確定できない。単独語・文中・前後に文字がある対照資料を用意する |
| 文字列との違い | `Contains text string`は規則に直接文字列を指定する。語句一覧という独立した定義の参照ではない |
| 使い分けの例 | 製品名・病名・内部名称など複数の語は語句一覧、固定の一文は文字列、番号の形式は正規表現を候補にする |

語句一覧は「意味が同じ言い換え」や誤字まで理解する仕組みではない。例えば「糖尿病」「糖尿病患者」「糖 尿 病」を別々の対照とし、未検知と未検査を分けて記録する。これは試験設計案であり、製品の日本語一致結果を述べたものではない。[語句一覧の仕様と設定例](https://knowledge.workspace.google.com/admin/security/custom-content-detectors)

## 正規表現の条件

`Matches regular expression`では、RE2構文で作成した独自検知器を選択する。RE2は、文字の並びの規則を記述する正規表現の実装である。作成画面のTest Expressionで式を確認できる。[設定手順](https://knowledge.workspace.google.com/admin/security/custom-content-detectors)

設計例として、郵便番号の形は`[0-9]{3}-[0-9]{4}`、架空の受付番号の形は`CASE-[0-9]{6}`と表せる。ただし、この式だけでは前後の文字との境界、実在性、番号の正しさを確認しない。住所の番地・建物名の有無や、番号の検査数字まで保証する式でもない。形式に合う注文番号などが誤検知になる対照も必要である。

RE2は後読み・先読みや後方参照をサポートしない。別の正規表現処理系で通った式をそのまま採用せず、RE2の対応構文を確認する。[RE2構文](https://github.com/google/re2/wiki/Syntax)

## 分類ラベルの条件

ラベルの存在、単一選択の選択肢型フィールドの値、およびそれらの否定を条件にできる。複数選択フィールドの値や、数値・日付・テキスト・人物型の値を調べる条件には対応しない。

同じ規則で分類ラベルを条件と付与動作の両方に使うことはできない。二段構成にするなら、「内容の検知 → 機微ラベル付与」の規則と、「機微ラベルがある → 共有制限」の規則を分ける。二段構成にはラベル反映待ちが入るため、最初の検知から遮断までを別に測る必要がある。後半は運用設計上の評価観点である。[ラベル条件と動作の制約](https://knowledge.workspace.google.com/admin/security/apply-classification-labels-to-drive-files-automatically-with-dlp-rules)

## AND OR NOTと条件グループ

| 演算子 | 意味 | 設計例 |
|---|---|---|
| AND | すべての条件に一致 | 「病名の語句一覧に一致」かつ「氏名の検知器に一致」 |
| OR | いずれかの条件に一致 | 「標準のカード番号検知」または「独自の番号形式」 |
| NOT | 条件の否定 | 「タイトルに公開済みを含む」の否定 |

条件グループを使い、`タイトル条件 AND (標準検知 OR 独自検知)`のように括弧に相当する階層を作れる。標準と独自の検知範囲を広げる目的ならOR、両方の裏付けを要求する目的ならANDであり、同じ結果にはならない。病名と氏名が同じ文書にあることも、その人物の病名であることの証明にはならない。[条件の組み合わせ](https://knowledge.workspace.google.com/admin/security/examples-of-dlp-rules-with-nested-condition-operators)

## 利用状況と共有先の条件

Context conditionsでは、地域、公開IPアドレスの範囲、端末の管理・承認状態などを定義して選択する。1規則に割り当てる利用状況の条件は1つで、その定義内で複数属性を組み合わせる。内容の条件もある場合は、両方を満たしたときに動作する。Driveではダウンロード・印刷・コピー禁止の動作に限られる。[利用状況の条件の適用範囲](https://knowledge.workspace.google.com/admin/security/combine-dlp-rules-with-context-aware-access-conditions)

Sharing conditionsはDriveの共有遮断用である。指定した組織部門・グループ・ドメインだけへの共有を許す方式と、指定した対象への共有を拒否する方式がある。「外部への共有を一律に遮断」と「特定の共有先だけを許可」のどちらを求めるかで設計を分ける。[共有先の条件](https://knowledge.workspace.google.com/admin/security/set-up-sharing-boundaries-in-data-protection-rules)

適用範囲のScopeは、共有先や本文中の人物ではなく、どの所有者の資料に規則を適用するかを決める。マイドライブは所有者、共有ドライブはその共有ドライブに適用される規則を見る。[適用範囲](https://knowledge.workspace.google.com/admin/security/plan-data-protection-rules)

## 再利用と変更時の確認

語句一覧・正規表現の検知器は共用する。本文とタイトルのどちらを調べるか、一致回数、AND／OR、動作は各規則に置く。検知器の編集は、それを参照する規則の対象文書の再検査を起こす。変更の影響を一部だけに限定したい場合は、新しい検知器を作って試験規則へ割り当てる設計が考えられる。[検知器の編集](https://knowledge.workspace.google.com/admin/security/custom-content-detectors)

| 上限の対象 | 公開値 |
|---|---|
| 正規表現 | 1,000文字 |
| 1語句一覧 | 950語、合計60KB |
| 規則で使用する正規表現・語句一覧の検知器 | 合わせて100 |
| 1規則の基本条件 | 100 |

これらは公式の推奨上限表に示されており、一部は強制されない場合もある。上限を超えて動作したように見えても、正常動作の保証にはしない。[条件と検知器の上限](https://knowledge.workspace.google.com/admin/security/view-dlp-content-and-rule-size-limits)

検証では、一致する値だけでなく、似た別用途の値、語の前後、繰り返しと異なる値、見出しの有無、暗号化や未対応形式を分ける。検索結果に出ない資料を陰性と決めず、検査の証拠と対象範囲を確認する。規則の有効化、ラベル付与、共有遮断、通知・集計はそれぞれ別の結果として確認する。
