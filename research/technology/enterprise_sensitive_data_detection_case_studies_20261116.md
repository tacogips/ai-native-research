# 企業の機密データ検知・管理の取り組み事例

報告日：2026年11月16日。Google Workspace の DLP（データ損失防止。機密情報を検知して共有や送信を止める機能）の調査を補うため、Google Workspace に限らず、企業が社内文書・SaaS・データ基盤に散在する個人情報や機密情報をどう検知し、どう管理したかの公開事例を集めた。

- **対象：** 利用企業や組織が実際に取り組んだ事例。製品の機能比較は[保存データを継続検査する SaaS DLP 製品の比較](telescreen_related_saas_dlp_20261009.md)と[企業基盤・国内製品の比較](telescreen_related_enterprise_20261009.md)で扱ったので、ここでは扱わない。
- **根拠：** 公開資料だけを使った。各事例は本文を開いて確認したものに限る。資料に書かれていない項目は「記載なし」とした。
- **ベンダー事例の扱い：** 製品の販売会社が出した顧客事例は宣伝資料である。数値は自己申告で、測り方もほとんど書かれていない。表では【販】と付けた。
- **用語：**
  - ラベル：ファイルや列に付ける分類の印（例：「社外秘」）。共有制限などの条件に使う。
  - 過剰共有（オーバーシェア）：業務上必要な範囲より広く共有された状態。
  - 適合率：検知したもののうち、本当に機密だった割合。再現率：本当の機密のうち、検知できた割合。
  - ポリシータグ：BigQuery で列ごとに付け、閲覧権限やマスキング（値を伏せる処理）を決める印。
  - infoType：Google の Sensitive Data Protection（旧 Cloud DLP）が用意する検出器の種類。

## 1. 結論

1. **重大事故の多くは「内容」ではなく「共有範囲」から起きている。** エイチーム（93万人分、最長約6年半公開）、米国 GSA（全職員に銀行口座情報などが閲覧可能）、Salesforce のゲスト権限の問題（楽天ほか）はいずれも、共有設定の誤りが長期間放置された事例である。発見のきっかけは、別ツールの検証、外部の通報、監査で、常時監視ではなかった。**既存の共有状態を棚卸しして直すことが、内容の検知より先に効く。**
2. **内容の検知は、正規表現や標準検知器だけでは誤検知が多すぎて運用が止まる。** Purview の初回走査で1,200万件の大半が誤検知（Aprio）、Microsoft DLP の調整に1,000時間超（米国の医療機関）、マイナンバー検知器が AWS アカウント ID や配送番号に反応（Looop、メルカリ）。成功した事例は、周辺語・除外リスト・文書の種類の判定・LLM（大規模言語モデル）などで文脈を補っている。
3. **大規模に自動化した企業は「検知」と「確定・強制」を分けている。** Airbnb、Uber、Meta、Grab、Databricks、Square は、検知結果を「提案」として所有者に確認させ、確定したラベルだけをアクセス制御・マスキング・削除に使う。人の確認は、確信度が低いもの、希少で機微な分類、保護を弱める変更に絞る。
4. **ラベルは少数の段階にし、既定値を安全側に置く。** Microsoft は4段階、Box と NRI は4〜5段階、Airbnb は3段階。TKC は全ファイルの既定を「社外秘」、北海道電力は暗号化付きの「社内」にした。細かい種別は検知規則側で持ち、ラベルは増やさない。
5. **生成 AI（Microsoft 365 Copilot、Gemini）の導入が、データ整理の最大の動機になっている。** AI は利用者の権限の範囲でデータを拾うため、過剰共有がそのまま AI の回答に現れる。各社は「ラベル付け」より先に「共有リンクの削除と権限の縮小」を導入の前提にした。Google Workspace／Gemini 側で同じ動機を明示した公開事例は見つからなかった。
6. **導入は「把握 → 担当者だけに通知 → 本人に警告 → 自動是正・遮断」の順に進めるのが共通である。** 最初から遮断した事例はなかった。
7. **効果の数値は弱い。** 検知精度を公開した日本企業はなかった。海外の自社構築事例でも適合率・再現率を出したのは Databricks と Meta（2020年論文）くらいである。評価は自前の試験データで行う必要がある。

## 2. 事例一覧

### 2.1 国内

| 組織 | 年 | 保存先 | 課題 | 手法 | 成果・限界 | 出典 |
|---|---|---|---|---|---|---|
| クラスメソッド | 2024 | Google ドライブ | 共有ドライブ単位の設定では一律にしか効かない | ドライブのラベルを条件に DLP ルールでダウンロード・印刷・外部共有を制限。汎用ラベル → 機密度・年度ラベル → 業務別ラベル（付けられる人を限定）の3段階 | 誰でも付けられるラベルは誰でも外せる。ラベルと規則の対応が管理画面で追いにくく、別表で管理 | [J1] |
| エイチーム | 2023 | Google ドライブ | 「リンクを知っている全員」設定で 1,369 ファイル、935,779 人分が公開状態 | 導入検討中のセキュリティ製品の検証で発覚。公開設定の無効化、外部共有の制御、監視強化 | 最古は2017年から公開状態 | [J2] |
| 奈良市、近畿大学 | 2025, 2026 | Google ドライブ | 共有範囲の誤り（県内の教育関係者全体、ゼミ学生） | 利用者・外部からの通報で発覚 | 技術的な検知ではなかった | [J3] |
| 舞鶴市 | 2025 | Google Workspace | 三層分離（用途別にネットワークを分ける方式）で庁外業務ができない | 一般事務を Workspace へ、基幹系は残す。Chrome Enterprise Premium の DLP で監視 | 規則の詳細と効果は記載なし | [J4] |
| メルカリ（CS 端末） | 2026 | Chromebook のブラウザ | 仮想デスクトップと端末の DLP を二重管理 | 承認ツール以外へのアップロード・貼り付けを制限。Gemini in Chrome は読み取り専用で段階導入 | 3年で50%超のコスト削減を「見込む」（予測値）【販】 | [J5] |
| メルカリ（CS チャット） | 2025 | Spanner、添付画像 | チャットの機微情報を手作業で削除していた | Sensitive Data Protection の infoType、独自の正規表現、周辺語（「マイナンバー」が前後10文字以内） | 配送番号がカード番号・マイナンバーと誤検知。抜き取り確認で監視。「機微情報の定義と運用が技術より難しい」 | [J6] |
| READYFOR | 2025 | BigQuery | 全社員が全データを閲覧できた。手作業のタグ付けは漏れる | 100種超の infoType で定期走査し、機密度「中」以上の列に Pub/Sub と Cloud Functions でポリシータグを自動付与 | プロジェクト名が人名、都道府県名が住所と誤検知 → 除外リスト。API の利用上限に再試行で対応 | [J7] |
| ファインディ | 2024 | BigQuery | 全員公開は危険、絞りすぎは業務に支障 | 定期走査で中〜高リスクの列を一覧化し、Dataform でポリシータグ、列単位の動的マスキング。長文は DLP API で部分マスク | 全文マスクは分析に必要な情報を失う | [J8] |
| TKC | 2025 | SharePoint、OneDrive（1.3億ファイル、201TB） | 人手では管理不能 | 全ファイルの既定ラベルを「社外秘」（印刷・転送不可）。カード番号・マイナンバー等で自動ラベル。7段階で展開 | 有効化率 5.7% → 23% → 52% → 全員。検討に約1年。警告を受けても対処が分からない利用者がいる【販】 | [J9] |
| 北海道電力 | 2026 | Microsoft 365 | 端末単位の対策の限界、持ち出し特例の増加 | 既定を暗号化付き「社内」ラベル。1部門で試験 → PC 入替に合わせ全社展開。内部リスク管理は流出経路ごとの規則に変更 | 試験で警告が大量に出て全件確認は不可能。「利用」と「流出」の境界が曖昧【販】 | [J10] |
| 野村総合研究所 | 2026 | Box（約350TB） | 手作業のラベルにばらつき・付け漏れ。営業秘密の要件 | 管理者がプロンプトで基準を定義し AI がラベルを提案、社員が確定。疑わしいときは安全側の仮ラベル。4区分 | 最終判断は人が持つ方針【販】 | [J11] |
| Looop | 2026 | Web 通信（SaaS、生成 AI） | アプリ単位の一律禁止は業務を止める | Zscaler の Web DLP で「確認」動作（理由を入力すれば送信可） | マイナンバー辞書が12桁の AWS アカウント ID に反応。API 通信の誤検知でフォームデータと JSON を除外。既定の「ソースコード」辞書は実コードを検知しなかった | [J12] |
| ADK アーツ | 2018 | 無償クラウドストレージ | 取引先とのやり取りで無償ストレージを使用 | 管理者通知 → 利用者に理由入力 → 禁止の3段階 | 90日で205件ブロック【販】 | [J13] |

### 2.2 海外（自社で構築した仕組み）

| 企業 | 年 | 対象と規模 | 検知方式 | 管理・是正 | 特記 | 出典 |
|---|---|---|---|---|---|---|
| Airbnb | 2021 | MySQL、Hive、S3、ログ、GitHub（数PB） | 判定器をデータ項目ごとに定義（正規表現、既知値の照合、CNN・BERT などの機械学習）。標本抽出で走査 | 所有者の申告と検知結果が一致すれば確定、食い違えばチケット。放置された Hive エクスポートは自動削除。秘密情報は `git blame` で投入者（退職者なら上司）に割当 | 一致した値は定期削除、チケットには値を載せない。誤検知は信用を失うと明記 | [G1] |
| Uber DataK9 | 2024 | 40万超のデータセット、40種超のタグ | ルール（辞書、正規表現、型）と機械学習のスコアを重み付きで合算 | 所有者の承認で確定。分類をアクセス制御・暗号化・保持に使う | 本番条件は正解率90%超かつ F2（再現率を重く見る指標）85%超。機密列は希少なので正解率だけでは誤る | [G2] |
| Uber File Semantic Analyzer | 2026 | Google Drive などから社外へ出るファイル（年約15万件） | 調整済み LLM が要約・機微語句・重要度を出し、ルールで判断 | 確度の高いものを分析者が確認 | 誤検知97%減、約4人年分の工数削減 | [G3] |
| Meta | 2020, 2026 | 数百万のデータ資産 | 2020年：標本抽出＋ルール＋機械学習（平均 F2 0.9以上）。2026年：決定的ルールで約85%を処理し、残り約15%を LLM（コスト約400倍） | 分類結果を保持期限とアクセス制御に使う。安定した LLM の判断はルールへ移す | 既存ラベルを LLM に見せない（自己参照の防止）。人の正解ラベルは追記のみで、モデル出力を正解に昇格させない | [G4] |
| Grab Metasense | 2023–24 | データレイク、Kafka（ペタバイト級） | GPT-3.5 に表名・列名だけを渡してタグ付け（値は渡さない） | タグから機微度を決め、属性ベースのアクセス制御と動的マスキング | 修正タグは平均1個未満、年約360人日削減。シンガポール当局が LLM 誤りによる格下げの危険を指摘し、ルールによる無作為照合と人の確認で対応 | [G5] |
| Databricks LogSentinel | 2026 | 社内のログとテーブル | 複数の LLM で列を2段階分類（大分類 → 細分類） | 注釈なし・注釈と中身の不一致・地域外持ち出しで Jira 起票 | 2,258件で適合率最大92%、再現率最大95%。監査が数週間 → 数時間 | [G6] |
| Square | 2020, 2022 | 数百のサービス | 列名・型で絞ってから標本値を Google DLP API で判定 | 所有者は承認か却下だけ。ログで値を隠す注釈がない項目にボットが PR を自動作成 | 自動化の前に誤検知を極小にしないと通知疲れ | [G7] |
| Shopify | 2021 | 1日約200億イベント | 自動検知ではなく、スキーマに PII（個人を特定できる情報）の扱いを宣言 | 取り込み時にトークン化（値を意味のない符号に置き換える）。削除請求は対応表の削除で完了 | 正しいやり方を既定にした。普及と過去データ移行（94人で約3年）が最難関 | [G8] |
| GitHub | 2026 | 自社の1.5万超のリポジトリ | 秘密情報の検知と push 時の遮断を全組織で強制 | 失効・再発行を最優先。種類ごとの手順書 | アラートの90%は有効な秘密でなかった。9か月で未対応ゼロ | [G9] |
| GitLab | 2026頃 | 全社員の Google Drive | 内容は見ず、共有の権限とメタデータだけ（Nira） | 外部共有・公開リンクがあり1年更新のないファイルを毎晩自動是正。所有者への一括是正依頼 | 内容の検知なしでも過剰共有を減らせる例 | [G10] |
| incident.io | 2024 | BigQuery | 判定しない。新しい文字列列はすべて機密扱い | 権限のない人にはハッシュ値。機密解除は許可リストへの PR で | 「既定で機密」は誤検知が多いが、許可リストで吸収 | [G11] |

### 2.3 海外（ベンダー公開の顧客事例）【すべて販】

| 組織 | 業種 | 保存先 | 内容 | 自己申告の数値 | 出典 |
|---|---|---|---|---|---|
| Microsoft 社内 | IT（30万人超） | SharePoint、OneDrive、Teams | Copilot 展開前に過剰共有を是正。4段階ラベル、入れ物（サイト）単位の既定ラベル、ラベルを下げるときは理由入力。6か月ごとにサイト所有者が継続を承認、なければ削除対象 | 記載なし | [V1] |
| 匿名の金融機関 × Varonis | 金融 | M365（約100万ファイル） | 機密12万件のうち5.7万件が露出。管理者に事前通知してから自動是正、共有リンク約2,000件削除 | 10日で Copilot への露出 99.8%減 | [V2] |
| 匿名の食品製造業 × Varonis | 製造 | M365 | 8人の Copilot 試行で露出が判明。50種のデータ型で独自分類、70万件にラベル | 露出97.5%減 | [V3] |
| Tampa General Hospital × Varonis | 医療 | SharePoint | Copilot 導入可否の判断のため権限を分析 | 約4.3万ファイルを7日で評価 | [V4] |
| Aprio × Teleskope | 会計 | M365 | Purview の初回走査で1,200万件超の大半が誤検知。文書の種類を文脈で判定し、結果を Purview のラベルとして付与 | ラベル付与を100%自動化 | [V5] |
| 匿名の学術医療センター × Cyera | 医療 | M365、AWS、電子カルテ | Microsoft DLP の調整に1,000時間超費やして行き詰まり。別製品で分類して Purview に渡す | 危険度上位30%に絞って対応 | [V6] |
| 匿名のグローバル銀行 × Bonfy | 金融 | SharePoint | 標準ツールは業務文脈がなく誤検知多発。ラベル付けを Copilot 展開の前提に | 誤検知70%減 | [V7] |
| Box 社内 | IT | Box | 10個超の案を5段階に絞ったラベル体系 | 記載なし | [V8] |
| 米国の K-12 学校 × DoControl | 教育 | Google Drive | 公開共有67.5万件、信頼外ドメイン共有約170万件、全組織共有460万件が判明。違反時に本人へ教育的な通知 | 是正約100万件、露出約90%減 | [V9] |
| 米国の FinTech 企業 × DoControl | 金融 | Google Drive | 既存の Drive ラベルを条件に方針を適用。個人メール宛て共有は承認制で1.5年で失効、6か月未閲覧は共有を自動解除 | 外部共有17万件超、直近90日の自動処理30万件 | [V10] |
| Zego × Metomic | 保険 | Google Workspace、Slack | 公開共有が数百〜数千件と判明。Slack では違反内容を自動で伏せ字 | 記載なし | [V11] |
| 匿名の FinServ 企業 × Metomic | 金融 | Google Drive、Slack | 第1段階は担当者だけに警告、第2段階で本人にも通知 | 記載なし | [V12] |
| Nova Credit × Nightfall | 金融 | Gmail、Drive、Slack | 前のメール DLP は誤検知が多く警告が無視されていた | 80%を自動是正 | [V13] |
| Wake Forest University | 教育 | Google Workspace | DLP ルールで機密情報の共有を検知し、誤共有を取り消し | DLP 単独の数値なし | [V14] |

### 2.4 事故・行政処分

| 事例 | 年 | 何が起きたか | 原因 | 当局・会社が求めた対策 | 出典 |
|---|---|---|---|---|---|
| 米国 GSA（連邦調達庁） | 2025 | Google 共有ドライブで、建物の詳細図面、取引先の銀行口座・納税者番号などが全職員から閲覧可能 | 機密度と共有範囲の不一致。「全社共有を避ける」指針と年次研修があっても発生 | 是正と影響者の特定・通知 | [I1] |
| Salesforce のゲスト権限（楽天ほか） | 2020–21 | 外部から保存情報にアクセス可能。楽天市場関連だけで最大約138万件 | ゲストユーザーの権限設定。新しい保護設定が既存レコードには自動適用されなかった | 個人情報保護委員会が既存レコードの所有者確認とアクセスレポートでの確認を要請 | [I2] |
| Box の公開カスタムリンク | 2019 | 推測可能な共有 URL から多数の企業文書（旅券写真、口座番号など）を発見 | 公開リンクと推測しやすい URL の組合せ | 共有の既定を社内に限定、共有リンクの定期確認 | [I3] |
| Mermaids（英国の慈善団体） | 2021 | 使わなくなったメールグループが公開状態で残り、約550人の健康情報などが検索可能 | 利用終了後も公開設定を解除しなかった | 英国 ICO（情報コミッショナー事務局）が £25,000 の制裁金 | [I4] |
| Drizly | 2022–23 | GitHub 上の認証情報経由で約250万人の情報流出 | 認証情報の不適切な保管 | 米国 FTC（連邦取引委員会）が不要データの破棄、保存期間の設定を命令 | [I5] |
| Blackbaud | 2023–24 | SaaS 保存データの侵害。口座番号などの流出が開示担当に伝わらなかった | 暗号化されていない機微情報、過剰保存 | FTC が資産の体系的な棚卸しと不要バックアップの削除を命令。SEC（証券取引委員会）は不正確な開示で300万ドル | [I6] |
| 1Health（旧 Vitagene） | 2023 | 公開 S3 バケットに遺伝・健康情報 | 暗号化・アクセス制限・データ棚卸しの欠如。約2年で少なくとも3回警告を受けていた | FTC が安全管理強化と検体破棄を命令 | [I7] |
| Samsung | 2023 | 社内ソースコード等を ChatGPT に入力（報道） | 外部生成 AI への業務情報の入力 | 入力文字数の制限、社内 PC での利用禁止（報道） | [I8] |

## 3. 横断的な傾向

### 3.1 何を先にやるか：共有の棚卸しが先、内容の検知が後

事故の原因の大半は共有設定である。内容を検知しなくても、共有範囲と最終更新日だけで是正を始められる（GitLab は「外部共有があり1年更新なし」を毎晩自動是正、DoControl の FinTech 事例は「6か月未閲覧」で共有解除）。

設定を後から締めても、既存の共有状態は自動では直らない。Salesforce では新しい保護設定が既存レコードに適用されず、エイチームでは公開状態が最長約6年半残った。Google Workspace でも、外部共有の制限を変えた後に既存ファイルの共有がどうなるかは、公式資料と実環境で確認する必要がある。

### 3.2 検知の精度は文脈で補う

| 誤検知の例 | 事例 | 対処 |
|---|---|---|
| 12桁の数字がマイナンバーと衝突（AWS アカウント ID、配送番号） | Looop、メルカリ | 周辺語、対象経路の絞り込み |
| 人名・住所の検出器がプロジェクト名・都道府県名に反応 | READYFOR | 除外リスト（初期以降はほぼ追加不要） |
| 税務書類と販促資料を正規表現で区別できない | Aprio | 文書の種類を項目の組合せで判定 |
| テスト用・プレースホルダーの秘密情報 | Airbnb、GitHub | パス単位の除外、有効性の確認（GitHub では90%が無効） |
| 同じ列名で意味が違う（年齢と有効期限） | Meta、Uber | 所有者・コード・系統情報などの文脈を LLM に与える |

安く確実な判定を先に、高い判定を後に置く構成が共通する。Meta は決定的ルールで約85%を処理し、LLM は残りに限る。Square は列名と型で絞ってから値を判定する。

### 3.3 検知と確定を分け、人の確認を絞る

- 検知結果は「提案」として持ち、所有者の承認で確定する（Airbnb、Uber、Grab、Square、Databricks、NRI）。
- 強制（アクセス制御、マスキング、削除）は確定ラベルだけを見る。
- 所有者には「承認か却下か」だけを求め、直し方（PR、一括是正リンク）を添える。
- 退職や組織変更で所有者が空白になる問題は各社共通で、Airbnb は上司を順にたどって在籍者を探す。
- LLM の誤りで機密度が下がる方向の変更は特に危険で、人の確認やルールによる無作為照合を入れる（Grab、Meta）。

### 3.4 ラベル体系は少なく、既定は安全側

| 組織 | 段階数 | 既定値 |
|---|---|---|
| Airbnb | 3（critical / personal / public） | 記載なし |
| Microsoft | 4（Public は入れ物に使わない） | OneDrive は「Confidential\Internal-only」 |
| NRI | 4（極秘・機密・社内限・一般） | 疑わしいときは安全側の仮ラベル |
| Box | 5 | 記載なし |
| TKC | 実質1種類を全ファイルに | 「社外秘」（印刷・転送不可） |
| 北海道電力 | 記載なし | 暗号化付き「社内」 |

既定を安全側に置くと、付け忘れは保護側に倒れる。代わりに、利便性低下への反発と問い合わせの急増が起きる（TKC は6か月前から周知、北海道電力は問い合わせが1か月で収束）。

### 3.5 段階的に導入する

共通の順序は「棚卸しで数値化 → 担当者だけに通知 → 本人に警告（理由入力） → 自動是正・遮断」である。

- Microsoft は Copilot を4段階で展開した（開発チーム → 営業 → 人事・法務など → 全社）。
- ADK アーツと Looop は「通知 → 理由入力 → 禁止」の3段階。
- Metomic の FinServ 事例は「這う、歩く、走る」と表現した。

### 3.6 抽出した値を広げない

- Airbnb は一致した値を定期削除し、チケットには資産名と項目種別だけを書く。
- GitHub は外部へ回す前に秘密の値を伏せる。
- Grab は LLM に表名と列名だけを渡し、値を渡さない。
- Shopify は取り込み時にトークン化する。

検知の仕組み自体が機密データの新しい保管場所になるのを避ける設計である。

### 3.7 効果の測り方

実証研究や調査では、検知件数より運用指標が重要だと示されている。

- ESG と MIND の調査（DLP ベンダーの委託、回答者100人の自己申告）では、確認したアラートの47%が誤検知、全アラートのうち是正に至ったのは8%だった。[R1]
- Varonis の自社データ分析では、90%の組織で機密ファイルが全従業員に開放されていた。ラベル付きファイルがある企業は10社に1社だった（企業の割合で、ファイルの分類率ではない）。[R2]
- Metomic が約650万の Google Drive ファイルを走査した報告では、40.2%に機密情報、34.2%が社外アドレスに共有されていた。ただし公開リンクの件数と割合が本文内で整合しない。[R3]
- Glasgow 大学の実験（8人、政府文書）では、精度が中程度（平衡正解率0.7）の自動予測を見せるだけで、人のレビューの精度が38%、速度が72%上がった。全自動の遮断ではなく、人の判断の補助としても使える。[R4]

Databricks は、適合率と再現率を最低限の歯止めとし、レビュー時間、意味のずれの検知遅延、週に処理できるチケット数を最適化の指標にしている。[G6]

## 4. Google Workspace での設計への示唆

以下は、上記の事例から導いた設計案である。Workspace の各機能が日本語文書でどう動くかは公式資料に書かれていないものが多く、[拡張版データセットの報告](workspace_dlp_v3_extended_detection_report_20261116.md)のとおり実環境で確かめる必要がある。

1. **最初に既存の共有状態を棚卸しする。** 「インターネット公開」「リンクを知っている全員」「外部の指定相手」「全社」を分けて数える。内容の検知を待たずに、「外部共有があり長期間更新なし」などメタデータだけの規則で是正を始められる（GitLab、DoControl の事例）。
2. **内容の検知は「共有範囲との重なり」で優先度を付ける。** 認証情報・口座・健康・人事の情報と広い共有が重なるものを先に直す（GSA の事例）。
3. **標準検知器は最初は監査だけにして誤検知を観察する。** 日本の12桁の番号は他の番号と衝突しやすいので、周辺語や除外を組み合わせる。誤検知の例と対処を表として蓄積する（メルカリ、READYFOR、Looop）。
4. **ラベルは少なくし、確実に守る文書はラベルを条件に制御する。** 付け外しできる人を限定したラベルで重要文書を扱う（クラスメソッド）。DLP ルールによるラベルの自動付与は「提案」と位置づけ、確定と分ける（Airbnb、NRI）。
5. **既定値を安全側にするなら、周知と問い合わせ対応を先に準備する**（TKC、北海道電力）。
6. **Gemini などの AI 機能を広げる前に過剰共有を直す。** AI は利用者の権限の範囲で文書を拾う。Copilot 事例と同じく、ラベル付けより共有の是正が先である。
7. **評価は自前の試験データと運用指標で行う。** 検知件数ではなく、真の問題の割合、確認時間、是正率、再発率を追う。検知されなかったファイルも抜き取って見逃しを推定する。
8. **通知には直し方を添え、所有者が空白の場合の割当先を決めておく。** 違反時の本人への教育的な通知は、多くの事例で使われている（DoControl、Metomic、Microsoft）。

これらの示唆を既存の検知精度の検証と是正フローに取り込んだ結果は、[改善案の検証](dlp_case_study_improvements_verification_20261118.md)にまとめた。

## 5. 確認できなかったこと

- Google 公式の日本語の Workspace DLP・ドライブラベル導入事例は見つからなかった。Google Sensitive Data Protection も、詳細な顧客事例は見つからなかった。
- Gemini for Workspace の導入を動機にデータ整理をした公開事例は見つからなかった。
- 自治体・教育委員会・大学で DLP を本格運用した国内事例は見つからなかった。見つかったのは誤共有の事故と再発防止の発表である。
- 国内企業で検知精度（適合率・再現率）を公開した事例はなかった。
- Lyft、Netflix、Dropbox、Pinterest、Slack、LINEヤフー、SmartHR、freee などの自社事例は、今回の検索では一次資料を見つけられなかった。存在しないという意味ではない。
- Opsin と Culligan の事例（Copilot での露出が80%から15%未満）は、出典を開けなかったため載せていない。

## 出典

URL は2026年11月16日に確認した。【販】はベンダーまたは販売会社の資料。

### 国内

- [J1] クラスメソッド「Google ドライブのラベルと DLP」2024-10-25 https://dev.classmethod.jp/articles/google-drive-label-with-dlp/
- [J2] エイチーム 2023-12-07, 12-21 https://www.a-tm.co.jp/news/43858/ 、 https://www.a-tm.co.jp/news/44238 、 https://scan.netsecurity.ne.jp/article/2023/12/27/50409.html
- [J3] ScanNetSecurity（奈良市）https://scan.netsecurity.ne.jp/article/2025/09/02/53545.html 、（近畿大学）https://scan.netsecurity.ne.jp/article/2026/07/16/55715.html
- [J4] レバテックLAB（舞鶴市）https://levtech.jp/media/article/focus/detail_713/
- [J5] Google Cloud ブログ（メルカリ）2026-11-05【販】https://cloud.google.com/blog/products/chrome-enterprise/chrome-enterprise-premium-drives-50-projected-cost-reduction-for-mercari
- [J6] メルカリ技術ブログ 2025-12 https://engineering.mercari.com/blog/entry/20251208-b7adaa9b98/
- [J7] READYFOR（Zenn）2025-12 https://zenn.dev/readyfor_blog/articles/f5c21782bd838e
- [J8] ファインディ技術ブログ 2024-09-02 https://tech.findy.co.jp/entry/2024/09/02/093000
- [J9] 日本マイクロソフト（TKC）2025-03-06【販】https://www.microsoft.com/ja-jp/customers/story/22478-tkc-corporation-microsoft-365-e5
- [J10] 日本マイクロソフト（北海道電力）2026-06【販】https://www.microsoft.com/ja-jp/customers/story/26712-hokkaido-electric-power-microsoft-purview
- [J11] Box Japan（野村総合研究所）【販】https://japan.box.com/case/nomura-research-institute-box-shield-pro
- [J12] Looop 技術ブログ 2026-09-29 https://techblog.looop.co.jp/entry/2026/09/29/113401
- [J13] サイバネット（ADK アーツ）【販】https://www.cybernet.co.jp/netskope/casestudy/01/
- 参考：NRI セキュア（NRI の Netskope 導入）【販】https://www.nri-secure.co.jp/service/case/netskope-nri 、Zscaler（BASE）【販】https://www.zscaler.com/jp/customers/base 、Google for Education の手引き https://services.google.com/fh/files/misc/gfe-preventing-information-leakage.pdf 、DLP ルールによるラベル自動付与（Google 公式ヘルプ）https://knowledge.workspace.google.com/admin/security/apply-classification-labels-to-drive-files-automatically-with-dlp-rules?hl=ja

### 海外（自社構築）

- [G1] Airbnb「Automating Data Protection at Scale」Part 1–3, 2021 https://medium.com/airbnb-engineering/automating-data-protection-at-scale-part-1-c74909328e08 、 https://medium.com/airbnb-engineering/automating-data-protection-at-scale-part-2-c2b8d2068216 、 https://medium.com/airbnb-engineering/automating-data-protection-at-scale-part-3-34e592c45d46 （直接取得は拒否されたため Wayback Machine の保存版で確認）
- [G2] Uber DataK9 2024-05-09 https://www.uber.com/en-US/blog/auto-categorizing-data-through-ai-ml/
- [G3] Uber File Semantic Analyzer 2026-06-04 https://www.uber.com/blog/ubers-file-analyzer/
- [G4] Meta 2020 https://engineering.fb.com/security/data-classification-system/ 、 https://arxiv.org/abs/2006.14109 、2026-06-25 https://engineering.fb.com/2026/06/25/security/privacy-aware-infrastructure-in-the-ai-native-era-an-asset-classification-case-study/
- [G5] Grab Metasense https://engineering.grab.com/llm-powered-data-classification 、 https://engineering.grab.com/metasense-v2 、シンガポール PDPC の文書 https://pdpc.gov.sg/-/media/files/pdpc/pdf-files/practical-guidance-provided-by-pdpc/practical-guidance-to-data-protection-provisions-in-relation-to-grabs-proof-of-concept-to-automate-data-classification-and-enable-data-use.pdf
- [G6] Databricks LogSentinel 2026-03-06 https://www.databricks.com/blog/logsentinel-how-databricks-uses-databricks-llm-powered-pii-detection-and-governance
- [G7] Square 2020 https://developer.squareup.com/blog/using-amundsen-to-support-user-privacy-via-metadata-collection-at-square/ 、講演 2022 https://www.infoq.com/presentations/square-data-security
- [G8] Shopify 2021-06-10 https://shopify.engineering/managing-pii-shopify-scale
- [G9] GitHub 2026-07-02 https://github.blog/security/application-security/how-github-used-secret-scanning-to-reach-inbox-zero/
- [G10] GitLab handbook（Nira）保存版 https://web.archive.org/web/20260113204951/https://handbook.gitlab.com/handbook/security/corporate/systems/nira/
- [G11] incident.io 2024-11-14 https://incident.io/blog/how-we-handle-sensitive-data-in-big-query
- 参考：LinkedIn（スキーマ注釈で注釈なしならビルド失敗）https://www.linkedin.com/blog/engineering/data-management/shifting-left-on-governance-datahub-and-schema-annotations

### 海外（ベンダー公開の顧客事例）【すべて販】

- [V1] Microsoft Inside Track https://www.microsoft.com/insidetrack/blog/how-were-tackling-microsoft-365-copilot-governance-internally-at-microsoft/ 、 https://www.microsoft.com/insidetrack/blog/empowering-employee-self-service-with-guardrails-how-were-using-sensitivity-labels-to-make-microsoft-more-secure/
- [V2] Varonis Copilot Security Scan サンプル https://info.varonis.com/hubfs/Security%20Scan/Varonis%20M365%20Copilot%20Security%20Scan%20Sample.pdf
- [V3] Varonis Concierge https://www.varonis.com/blog/concierge
- [V4] Varonis（Tampa General Hospital）https://www.varonis.com/customer-stories/how-tampa-general-hospital-safely-deployed-m365-copilot
- [V5] Teleskope（Aprio）https://www.teleskope.ai/case-studies/how-aprio-operationalized-data-security-with-teleskope
- [V6] Cyera https://www.cyera.com/customer-story/how-a-leading-academic-medical-center-solved-a-1-000-hour-dlp-stalemate-and-achieved-real-time-data-visibility
- [V7] Bonfy https://em360tech.com/sites/default/files/2025-09/bonfy-case-study-globalbank-microsoft365.pdf
- [V8] Box https://blog.box.com/box-using-box-how-we-deployed-box-shield-internally
- [V9] DoControl（K-12）https://www.docontrol.io/case-studies/docontrol-k-12-schools-data-security-programs
- [V10] DoControl（FinTech）https://www.docontrol.io/case-studies/data-security-fintech-case-study
- [V11] Metomic（Zego）https://metomic.io/blog/how-zego-protects-their-google-docs-around-the-clock
- [V12] Metomic（FinServ）https://metomic.io/resource-centre/from-immaturity-to-proactivity-a-finserv-companys-journey-to-data-security-awareness
- [V13] Nightfall（Nova Credit）https://nightfall.ai/case-studies/nova-credit
- [V14] Google Workspace（Wake Forest University）https://workspace.google.com/blog/customer-stories/wake-forest-university-redefines-cybersecurity-google-workspace-education-plus

### 事故・行政処分

- [I1] GSA OIG 2025-04-18 https://www.gsaig.gov/sites/default/files/audit-reports/A250043-2%20Final%20Alert%20Memorandum%20Redacted.pdf
- [I2] 楽天 https://corp.rakuten.co.jp/news/update/2020/1225_01.html 、個人情報保護委員会の注意喚起 https://www.ppc.go.jp/news/careful_information/salesforce_guestuser/
- [I3] Adversis https://www.adversis.io/blogs/pandoras-box-another-new-way-to-leak-all-your-sensitive-data
- [I4] 英国政府（Mermaids）https://www.gov.uk/government/publications/charity-inquiry-mermaids/charity-inquiry-mermaids （現在は Withdrawn 表示）
- [I5] FTC（Drizly）https://www.ftc.gov/news-events/news/press-releases/2022/10/ftc-takes-action-against-drizly-its-ceo-james-cory-rellas-security-failures-exposed-data-25-million
- [I6] FTC（Blackbaud）https://www.ftc.gov/news-events/news/press-releases/2024/05/ftc-finalizes-order-blackbaud-related-allegations-firms-security-failures-led-data-breach 、SEC https://www.sec.gov/newsroom/press-releases/2023-48
- [I7] FTC（1Health）https://www.ftc.gov/news-events/news/press-releases/2023/06/ftc-says-genetic-testing-company-1health-failed-protect-privacy-security-dna-data-unfairly-changed
- [I8] The Korea Times（Samsung）https://www.koreatimes.co.kr/business/companies/20230611/samsung-electronics-to-adopt-own-ai-amid-chatgpt-security-concerns

### 調査・研究

- [R1] ESG / MIND「The State of Data Loss Prevention」（ベンダー委託）https://22293892.fs1.hubspotusercontent-na1.net/hubfs/22293892/Web%20Content/eBooks/eBook%20ESG%20State%20of%20DLP.pdf
- [R2] Varonis「2025 State of Data Security Report」（ベンダー自社分析）https://info.varonis.com/hubfs/Files/reports/2025-varonis-state-of-data-security-report.pdf
- [R3] Metomic「Google Scanner Report」（ベンダー自社分析）https://www.metomic.io/resource-centre/metomic-finds-40-of-google-drive-files-contain-sensitive-information-putting-organizations-at-risk-of-a-data-breach/
- [R4] McDonald ほか, ACM CHIIR 2019 https://eprints.gla.ac.uk/174446/
