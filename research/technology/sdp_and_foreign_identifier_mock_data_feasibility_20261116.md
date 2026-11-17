# Google Cloud SDPの検知種類と海外の識別番号の模擬データ作成の検討

検討日：2026年11月16日。SDPはGoogle CloudのSensitive Data Protection（旧Cloud DLP）を指し、文字や画像を検査するAPI（プログラムからの呼出し口）を持つ。infoTypeはSDPの検知種類の名称である。Workspace DLPとは別製品で、Workspaceの検知結果の代わりにはならない。

根拠はSDPの公開資料で、実際の検査は行っていない。海外番号の検査数字の算式は広く公開されているものを挙げたが、本文書の時点では各国の公式資料で再確認していない。生成器へ組み込む前に確認する。

**結論：** SDPは、Workspace DLPの標準検知器にない種類（犯罪歴、雇用状況、在留資格、宗教、婚姻状況、顔・本人確認書類の画像、医療記録などの文書種別）を持つ。海外の国民識別・社会保険・税番号も国別に多数ある。海外番号の模擬データは、公開された形式と検査数字の算式で作成できる。難しいのは、未発行の番号であることの保証と、日本語の文書中でのSDPの動作の保証である。

## 1. 指定項目のSDPでの検知種類

| 項目 | SDPのinfoType | Workspace DLP標準 | 備考 |
|---|---|---|---|
| 個人番号・運転免許証・旅券・銀行口座 | `JAPAN_INDIVIDUAL_NUMBER`、`JAPAN_DRIVERS_LICENSE_NUMBER`、`JAPAN_PASSPORT`、`JAPAN_BANK_ACCOUNT` | あり | 日本固有はこれに`JAPAN_CORPORATE_NUMBER`を加えた5種だけ |
| 在留カード・保険証・基礎年金 | なし | なし | `IMMIGRATION_STATUS`は在留資格という状態の記述で、カード番号ではない |
| 氏名・住所 | `PERSON_NAME`、`STREET_ADDRESS` | 氏名のみ | 日本語での動作は未確認 |
| 病歴・健康診断 | `MEDICAL_TERM`、`MEDICAL_DATA`、`ICD10_CODE`、`BLOOD_TYPE`、文書種別`DOCUMENT_TYPE/MEDICAL/RECORD` | 医療用語のみ | 障害の専用種類はない |
| 人種・信条 | `ETHNIC_GROUP`、`RELIGIOUS_TERM`、`POLITICAL_TERM` | 民族のみ | — |
| 犯罪歴・犯罪被害 | `CRIME_STATUS`（犯罪被害の状態または犯罪歴） | なし | 社会的身分の専用種類はない |
| 職歴・学歴・勤務先 | `EMPLOYMENT_STATUS`、`ORGANIZATION_NAME`、文書種別`DOCUMENT_TYPE/HR/RESUME` | 履歴書の文書種別のみ | 学歴の専用種類はない |
| 家族構成 | `MARITAL_STATUS` | なし | 婚姻状況だけで、家族全体ではない |
| 年収・資産 | 専用種類なし。`FINANCIAL_ACCOUNT_NUMBER`、文書種別`DOCUMENT_TYPE/CONTEXT/FINANCE` | なし | 金額の意味付けはできない |
| パスワード | `PASSWORD`、`WEAK_PASSWORD_HASH`、`AUTH_TOKEN`、`ENCRYPTION_KEY`等 | あり | — |
| 顔・本人確認書類の画像 | `OBJECT_TYPE/PERSON/FACE`（試験提供）、`OBJECT_TYPE/PERSON/PHOTO_ID_CARD`、`OBJECT_TYPE/PERSON/PASSPORT` | なし | 利用できる地域が限られる |
| 音声・映像 | なし | なし | 文字と画像の検査が対象 |

出典はすべて[infoTypeの一覧](https://docs.cloud.google.com/sensitive-data-protection/docs/infotypes-reference)。

### 言語の扱い

公式資料は「国別の種類は英語とその国の言語に対応し、多くの全世界共通の種類は複数言語で動く」とし、自分のデータで確かめるよう求めている。[言語対応の説明](https://docs.cloud.google.com/sensitive-data-protection/docs/concepts-infotypes) 日本語を名指しした記述はない。したがって、日本語文書での`PERSON_NAME`・`CRIME_STATUS`等の動作は測定対象である。

また、多くの検知種類は周辺の手がかり（文脈語）がないと一致しないとされる。日本語の見出し（「社会保障番号：」等）を手がかりとして扱うかは未確認である。

### 画像

JPEG・PNG・TIFF・BMP等を、文字認識で抽出した文字と、物体の検出で検査する。1要求0.5MBまで、TIFFは50ページまで。文字認識の日本語対応は記載を確認できなかった。[画像の検査](https://docs.cloud.google.com/sensitive-data-protection/docs/inspecting-images)、[対応形式](https://docs.cloud.google.com/sensitive-data-protection/docs/supported-file-types)、[上限](https://docs.cloud.google.com/sensitive-data-protection/limits)

料金ページの本文は今回取得できなかった。費用見積りの前に確認する。

## 2. 海外の識別番号

SDPには国別の国民識別・社会保険・税・医療保険の番号が多数ある。主要なものと、模擬データの作成方法は次のとおり。

| 国 | SDPのinfoType | 形式と検査数字（公開の算式、要確認） | 模擬データ |
|---|---|---|---|
| 米国 | `US_SOCIAL_SECURITY_NUMBER`、`US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER`、`US_MEDICARE_BENEFICIARY_ID_NUMBER` | 社会保障番号（SSN）は3-2-4桁。検査数字なし。SDPは全ゼロの群、先頭群666、先頭が9の番号に一致しない（SDP資料で確認） | 作成可能。ただし一致させるには発行範囲内の形式が必要で、未発行の保証はできない |
| カナダ | `CANADA_SOCIAL_INSURANCE_NUMBER`、`CANADA_OHIP`等 | 社会保険番号（SIN）は9桁。Luhnの算式 | 作成可能 |
| 英国 | `UK_NATIONAL_INSURANCE_NUMBER`、`UK_NATIONAL_HEALTH_SERVICE_NUMBER`、`UK_TAXPAYER_REFERENCE` | 国民保険番号は英字2・数字6・英字1で使わない接頭辞がある。NHS番号は10桁で検査数字あり | 作成可能。公式の記載例は使わない接頭辞で、検知されない可能性がある |
| フランス | `FRANCE_NIR`等 | 15桁。末尾2桁は97を法とする検査値 | 作成可能 |
| ドイツ | `GERMANY_TAXPAYER_IDENTIFICATION_NUMBER`、`GERMANY_IDENTITY_CARD_NUMBER` | 税番号は11桁。検査数字と数字の重複規則あり | 作成可能 |
| 韓国 | `KOREA_RRN`、`KOREA_ARN`、`KOREA_NHI_NUMBER` | 住民登録番号は13桁。生年月日と性別の桁を含む。検査数字の扱いは新旧の発行で異なるとされる | 作成可能。検査数字の現行仕様は要確認 |
| 中国 | `CHINA_RESIDENT_ID_NUMBER` | 18桁。末尾はISO 7064の算式でXを含む | 作成可能 |
| 台湾・香港 | `TAIWAN_ID_NUMBER`、`HONG_KONG_ID_NUMBER` | 英字と数字、重み付きの検査数字 | 作成可能 |
| シンガポール | `SINGAPORE_NATIONAL_REGISTRATION_ID_NUMBER` | 英字1・数字7・英字1。末尾が検査文字 | 作成可能 |
| インド | `INDIA_AADHAAR_INDIVIDUAL`、`INDIA_PAN_INDIVIDUAL` | Aadhaarは12桁でVerhoeffの算式。PANは英字5・数字4・英字1 | 作成可能 |
| オーストラリア | `AUSTRALIA_TAX_FILE_NUMBER`、`AUSTRALIA_MEDICARE_NUMBER` | 税番号は9桁で重み付きの検査数字 | 作成可能 |
| ブラジル・メキシコ | `BRAZIL_CPF_NUMBER`、`MEXICO_CURP_NUMBER` | CPFは11桁で検査数字2桁。CURPは18文字で生年月日・検査文字を含む | 作成可能 |
| スペイン・イタリア・オランダ・スウェーデン | `SPAIN_DNI_NUMBER`、`SPAIN_SOCIAL_SECURITY_NUMBER`、`ITALY_FISCAL_CODE`、`NETHERLANDS_BSN_NUMBER`、`SWEDEN_NATIONAL_ID_NUMBER` | DNIは数字8・検査文字。BSNは11の検査。スウェーデンは生年月日とLuhn | 作成可能 |
| その他 | デンマーク、フィンランド、ノルウェー、ポーランド、アイルランド、イスラエル、トルコ、タイ、インドネシア、南アフリカ等の番号、`VAT_NUMBER` | 国ごとに異なる | 優先度を決めて追加 |

Workspace DLPの標準検知器にも国別の番号が多数あり、両製品の名称は多くが対応している。ただし、Workspaceで同じ国の同じ番号を扱えるかは国ごとに確認する。

## 3. 模擬データの設計

v3の生成器（[`extended/`](../../scripts/workspace_dlp_benchmark/extended/README.md)）に海外番号の項目群を追加する形にする。

| 設計 | 内容 |
|---|---|
| 値 | 公開の算式で検査数字が正しい値と、検査数字だけ誤った値を対にする。生年月日を含む番号は架空の生年月日から作る |
| 言語の文脈 | 同じ番号を、英語の文脈（`SSN: …`）、その国の言語の文脈、日本語の文脈（「社会保障番号：…」）の3種で置く。SDPが文脈語を必要とする種類で、日本語の見出しが効くかを測る |
| 文脈なし | 見出しのない番号だけの例を置き、文脈語への依存を測る |
| 陰性 | 同じ桁数・形式の注文番号や部品番号、公式の記載例（使わない接頭辞等） |
| 正解 | 国、番号の種類、検査数字の正誤、文脈の言語、SDPとWorkspaceの対応名 |
| 画像 | 番号を描いた画像と、SDPの`PHOTO_ID_CARD`等を測るための独自様式の見本。実物の様式は再現しない |

### 作成できるもの

- 公開された形式と検査数字の算式を持つ番号。表の大半の国が該当する。
- 文脈の言語を変えた比較。
- 形式は同じだが番号ではない陰性。

### 難しいもの

| 項目 | 理由 | 対応 |
|---|---|---|
| 未発行であることの保証 | 米国のSSNのように無作為に割り当てる方式では、正しい形式の番号が実在者の番号と一致し得る。検知させるには発行範囲内の形式が必要 | 架空の氏名とだけ組み合わせ、外部へ照会・送信しない。既存方針と同じく未発行を保証しないと明記 |
| 算式が非公開・変更済みの番号 | 一部の国は検査数字を廃止または変更している | 公式資料で確認できない番号は形式だけで作り、検査数字の正誤を正解に含めない |
| 外国語の自然な文書 | 文脈語の翻訳の質が検知に影響する | 定型の見出しと短い文に限定し、翻訳した語の出典を記録 |
| 日本語文書での動作の保証 | 公式資料に日本語の記載がない | 測定対象として扱い、結果で判断 |

## 4. SDPで検査する場合

SDPの`content.inspect`へv3の資料を送り、返った種類・確信度・位置を正解と照合する処理を追加できる。実行にはGoogle Cloudのプロジェクトと課金設定が必要で、資料を外部のAPIへ送ることになる。架空資料だけを送る前提でも、実行は利用者の判断とする。結果は他の実測と同じく公開リポジトリへ保存しない。

SDPは独自の種類として、正規表現、大規模な辞書、周辺語で確信度を上げ下げする規則、除外規則を持つ。Workspaceの独自検知器より文脈の扱いが細かいため、両者の差もこの検査で比較できる。

## 5. 公開根拠

- [infoTypeの一覧](https://docs.cloud.google.com/sensitive-data-protection/docs/infotypes-reference)
- [infoTypeの概念と言語対応](https://docs.cloud.google.com/sensitive-data-protection/docs/concepts-infotypes)
- [画像の検査](https://docs.cloud.google.com/sensitive-data-protection/docs/inspecting-images)
- [対応するファイル形式](https://docs.cloud.google.com/sensitive-data-protection/docs/supported-file-types)
- [上限](https://docs.cloud.google.com/sensitive-data-protection/limits)
- [独自のinfoTypeの作成](https://cloud.google.com/sensitive-data-protection/docs/creating-custom-infotypes)
