# 機微情報と個人情報と企業秘密の検知項目比較

調査日：2026年11月12日。DLPは機密情報の漏えいを防ぐ仕組み、APIはソフトウェア同士の呼出し口である。個人識別、金融、健康、思想信条、認証情報、企業秘密、画像等を**117項目**に整理し、Google Workspace DLP、Google Cloud Sensitive Data Protection、Microsoft Purview、Nightfall、Amazon Macieと、自作に使えるPresidio・Gitleaksを比較する。

**既知の番号・鍵・用語は標準検知しやすい。文書の種類や明示された機微な記述は意味に基づく分類も使える。一方、本人との関係、未公表かどうか、業務上の許可、法的な秘密性は、内容検査だけでは確定できない。** 本表の標準対応は検知器の存在であり、検出漏れがない保証でも、製品間の精度順位でもない。

「世の中のすべての機密項目」に閉じた一覧はない。国・制度・業種・組織固有の秘密を追加できる調査用の分類表とする。国別の番号は日本を詳しく分け、海外は代表的な番号群としてまとめる。法令上の要配慮個人情報と、一般に配慮を要する情報は同一集合ではなく、本表全体を法的な該当一覧として使わない。[L1]

## 判定の読み方

| 表記 | 意味 | 判断の限界 |
|---|---|---|
| 標 | 対象項目の標準検知器・認識器を公開仕様で確認 | 有効化・契約・対象形式・周辺語句等の条件あり |
| 標限定 | 対応国・文字・近接種別などに限定した標準検知 | 行の対象全体への対応とは数えない |
| 分 | 標準の文書分類で種類を判定 | 全機密箇所の抽出や秘密性の確定ではない |
| 分限定 | 近い文書分類を候補抽出に使える | その項目専用の標準分類ではない |
| 分試 | 試験提供の標準分類 | 提供条件・版を導入時に確認 |
| 画 | 標準の画像分類・物体検出 | 読取文字・本人確認・真正性検証とは別 |
| 規 | 公開された独自の形式規則・語句辞書で候補検知を作る案 | **実装・試験が必要。汎用の意味判断ができるという評価ではない** |
| 文 | 公開された独自の意味分類・学習機能で候補検知を作る案 | 日本語、接続先、例示、精度の検証が必要 |
| 拡 | 自作の追加モデル・抽出処理・接続部が必要 | 完成した標準機能として数えない |
| 追 | Presidioで公開された任意追加の医療モデル等が必要 | 標準の最小構成や日本語対応とは分ける |
| 未 | この対象の標準対応を公開資料から確定できない | 非対応の断定ではない |
| 外 | 本文・画像だけでは確定せず外部の事実が必要 | 製品の属性連携や独自台帳を組み合わせれば判断を構築できる場合がある |
| 非 | 当該方式の公開仕様で入力・処理の対象外 | 別の抽出処理や別製品を追加する場合は別評価 |
| 不可 | 表の条件では本文へアクセスできず検査できない | 暗号化の存在そのものの検出とは異なる |
| — | Gitleaksの既定の秘密検知規則では本調査の比較対象外 | 独自規則で拡張できることを製品の標準対応とは数えない |

「限定」「試」「条件」は個別の補完・限界欄と併せて読む。複数の方式を使える場合、代表的な入口を示す。`規`・`文`・`拡`は公開された拡張手段を項目へ対応付けた**設計上の推論**であり、当該項目の検出実証ではない。

## 比較する製品と根拠

AWSの追加比較は[5サービスと同じ117項目の比較表](aws_sensitive_data_services_matrix_20261112.md)を参照。Macieに加えてBedrock Guardrails、AWS Glue、Comprehend PII、Comprehend Medicalを確認し、独立API、日本語、日本の番号、記録のみの運用、画像・音声の補助処理を整理した。機械可読な表では`aws_assessment`を追加した。

| 列名 | 製品・比較対象 | 標準判定と拡張手段の根拠 |
|---|---|---|
| GW | Google Workspace DLP。Workspace内の検知・制御 | 標準検知一覧[G1]、語句・形式規則[G2]。Cloud側の分類を転記しない |
| GC | Google Cloud Sensitive Data Protection。検査API・分類機能 | 標準一覧[C1]、独自検知[C2]、検査API[C3]。入力と実行地域に制約あり |
| MS | Microsoft Purviewの分類機構全体 | 機密情報の種類[M1]、文書分類[M2]、独自規則[M3]、独自学習[M4]。すべての接続先で同機能が使えるという表ではない |
| NF | Nightfallの検知・文書分類 | 標準一覧[N1]、独自規則[N2]、自然言語指定[N3,N4]。画像・文書分類と言語対応は機能ごとに確認 |
| AM | Amazon Macie。S3内の内容検査 | 国別標準一覧[A1]、独自規則[A2]。Driveの直接検査は対象外 |
| PR | Presidio。自分で運用する公開ソースの部品 | 標準認識器、地域指定、任意追加の医療モデル[P1]。日本語の人名・住所にはモデル等の設定が別途必要 |
| GL | Gitleaks。コード・文字列等の秘密検知 | 公開された既定規則[K1]と拡張機能[K2]。個人情報一般を扱うDLP製品ではない |

日本語について「標」とした番号や電話も、全角・異体字・改行・縦書き・省略への性能を保証しない。特にMSの文書分類の多くは対応言語が英語とされる。GCの文書・画像分類には実行地域の限定がある。NFの新しい意味分類について日本語の保証を確認できていない。これらを日本語対応の確約として扱わない。[C1,M2,N3,N4] 日本語の個別条件は[既存調査](nightfall_japanese_support_20261111.md)も参照。

## 項目別の比較表

### 個人の識別情報と連絡先

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D001 | 氏名一般 | 標 | 標 | 標 | 標 | 標限定 | 標 | — | 人名という文字列の検出。本人確認ではない。Macieはラテン文字に限定 |
| D002 | 日本語の漢字・かな氏名 | 未 | 未 | 標 | 未 | 規 | 拡 | — | Purviewは日本を明示。他製品の汎用人名検知を日本語保証へ広げない |
| D003 | 住所一般 | 規 | 標 | 標 | 標限定 | 標限定 | 拡 | — | PresidioのLOCATIONは地名であり、郵便住所全体とは異なる |
| D004 | 日本語住所 | 規 | 未 | 標 | 未 | 規 | 拡 | — | PurviewのJapan physical addresses。郵便番号だけの検出は別 |
| D005 | 電話番号一般 | 標 | 標 | 規 | 標 | 標限定 | 標 | — | Macieは対象国を列挙。Purviewは今回専用の標準項目を未確認 |
| D006 | 日本の電話番号 | 標 | 標 | 規 | 標 | 規 | 標限定 | — | 国番号・国内形式・全角・区切りなしは別試験。Presidioは地域設定を確認 |
| D007 | メールアドレス | 標 | 標 | 規 | 標 | 規 | 標 | — | 国際化されたアドレスや伏字は別試験 |
| D008 | 生年月日 | 標 | 標 | 規 | 標 | 標 | 規 | — | 単なる日付と本人の誕生日の区別が必要。PresidioのDATE_TIMEは汎用日付 |
| D009 | 年齢 | 標 | 標 | 規 | 規 | 規 | 規 | — | 年齢の検出と未成年の本人確認を区別 |
| D010 | 日本のマイナンバー | 標 | 標 | 標 | 標 | 規 | 規 | — | 日本専用の標準番号検知を4製品で確認 |
| D011 | 日本の運転免許証番号 | 標 | 標 | 標 | 規 | 規 | 規 | — | 証明書画像の分類と番号の箇所検知を分ける |
| D012 | 日本の旅券番号 | 標 | 標 | 標 | 規 | 規 | 規 | — | Macieの標準旅券一覧に日本は含まれない |
| D013 | 日本の在留カード番号 | 規 | 規 | 標 | 規 | 規 | 規 | — | PurviewはJapanese Residence Card Numberを列挙 |
| D014 | 日本の住民票コード等 | 規 | 規 | 標限定 | 規 | 規 | 規 | — | PurviewのJapan resident registration numberは11桁と周辺語句。日本語の制度上の対応を導入時に確認 |
| D015 | 日本の健康保険の記号番号 | 規 | 規 | 未 | 規 | 規 | 規 | — | 米国やカナダの医療番号の標準対応を日本へ流用しない |
| D016 | 日本の基礎年金番号等 | 規 | 規 | 未 | 規 | 規 | 規 | — | PurviewのJapan social insurance numberとの制度上の対応は個別定義で確認 |
| D017 | 海外の国民識別・納税番号 | 標限定 | 標限定 | 標限定 | 標限定 | 標限定 | 標限定 | — | SSN、Aadhaar等。全世界すべての番号に対応するという意味ではない |
| D018 | 法人番号 | 規 | 標 | 標 | 規 | 規 | 規 | — | 個人番号と区別。番号の存在だけでは企業秘密にならない |
| D019 | 社員・顧客・会員・学生番号 | 規 | 規 | 規 | 規 | 規 | 規 | — | 書式・辞書・登録済み台帳との照合を設計。数字だけで種類を確定しない |
| D020 | 利用者名・画面名・アカウントID | 規 | 標限定 | 規 | 規 | 規 | 規 | — | GCのGENERIC_IDは広い候補であり、誰のアカウントかの確定ではない |

### 端末識別と位置や行動

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D021 | IPアドレス | 標 | 標 | 標 | 標 | 規 | 標 | — | 個人との結び付きは別の台帳が必要 |
| D022 | MACアドレス | 標 | 標 | 規 | 標 | 規 | 標 | — | 端末の通信識別子。所有者の特定とは異なる |
| D023 | 端末IMEI・広告識別子 | 標 | 標 | 規 | 標限定 | 規 | 規 | — | NightfallはIMEIを確認。広告識別子まで同一視しない |
| D024 | Cookie・セッション情報 | 標 | 標 | 規 | 標 | 標 | 規 | 標限定 | Gitleaksは一部サービス固有のcookie。すべてのcookieが認証情報とは限らない |
| D025 | 緯度経度 | 規 | 標 | 規 | 標 | 標限定 | 規 | — | Macieは英語の周辺語句が条件。実際の居場所であることは別確認 |
| D026 | 訪問先・移動履歴 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 座標や住所の検出だけで時系列の本人行動は復元できない |
| D027 | 閲覧・検索・購入履歴 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 履歴の書式や見出しは候補。誰の履歴か、私生活かは文脈が必要 |
| D028 | 車台番号VIN | 標 | 標 | 規 | 標限定 | 標 | 規 | — | 車両識別番号であり、所有者の本人特定は別 |

### 金融と支払い

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D029 | クレジットカード番号 | 標 | 標 | 標 | 標 | 標 | 標 | — | 検査数字の適合はカードの実在・有効性を保証しない |
| D030 | カード有効期限・確認コード | 規 | 標 | 規 | 規 | 標 | 規 | — | 短い数値だけでは誤検知しやすく、周辺語句と番号との関係が必要 |
| D031 | カード磁気帯情報 | 標 | 標 | 規 | 規 | 標 | 規 | — | 通常のカード番号だけの検出とは別 |
| D032 | 日本の銀行口座番号 | 標 | 標 | 標 | 規 | 規 | 規 | — | 支店・口座種別・名義人の対応や実在性は別の確認 |
| D033 | 海外口座IBAN・SWIFT等 | 標 | 標 | 標 | 標 | 標限定 | 標限定 | — | PresidioはIBAN、Macieは国別口座。SWIFTは金融機関の識別であり個人口座ではない |
| D034 | 暗号資産の公開アドレス | 規 | 規 | 規 | 規 | 規 | 標限定 | — | PresidioはBitcoin。公開アドレスと秘密鍵を区別 |
| D035 | 給与・賞与・報酬明細 | 規 | 規 | 分 | 分 | 規 | 拡 | — | 文書の種類を分類。金額・本人との対応の全箇所抽出は別 |
| D036 | 資産・残高・所得・債務 | 規 | 規 | 分 | 分 | 規 | 拡 | — | 個人金融文書としての分類と各金額の意味付けを区別 |
| D037 | 税務申告・納税書類 | 規 | 規 | 分 | 分試 | 規 | 拡 | — | Nightfallの個人向け税務文書はEarly Preview。日本の様式は別評価 |
| D038 | 与信評価・信用履歴 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 点数だけでは与信情報と判定できず、書式や本文の意味が必要 |
| D039 | 取引履歴・送金先 | 規 | 規 | 分限定 | 分限定 | 規 | 拡 | — | 金融文書の候補分類。全取引の属性抽出とは別 |

### 医療と健康

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D040 | 病名・医療用語 | 標 | 標 | 標 | 標限定 | 規 | 追 | — | 用語の存在と、特定人の病歴という事実を分ける |
| D041 | 疾病・処置の符号ICD等 | 標 | 標 | 標 | 規 | 標限定 | 規 | — | MacieはHCPCS等を列挙。ICDまで標準対応と拡張しない |
| D042 | 処方薬・薬剤名 | 標限定 | 標限定 | 標 | 標限定 | 標限定 | 追 | — | 米国FDAの名称・符号と日本の薬剤一般を区別 |
| D043 | 医療記録・診療録という文書 | 規 | 分 | 分 | 分 | 規 | 拡 | — | GCはDOCUMENT_TYPE/MEDICAL/RECORD。診断が正しいという保証ではない |
| D044 | 患者の診察券・診療録番号 | 規 | 標限定 | 規 | 規 | 規 | 規 | — | GCのMEDICAL_RECORD_NUMBER。医療機関独自の書式は追加設定 |
| D045 | 海外の医療保険・医療識別番号 | 標限定 | 標限定 | 標限定 | 標限定 | 標限定 | 標限定 | — | NHS、Medicare等。対応国・制度ごとに異なる |
| D046 | 血液型 | 規 | 標 | 規 | 規 | 規 | 追限定 | — | GCはBLOOD_TYPE。Presidioは生体測定の広い種類で候補、専用保証ではない |
| D047 | 健診結果・検査値 | 規 | 規 | 標限定 | 分限定 | 規 | 追 | — | Purviewの検査用語は検査結果全体の意味判断と異なる |
| D048 | 障害・精神疾患・依存症の記述 | 規 | 標限定 | 標限定 | 分限定 | 規 | 追限定 | — | 病名・障害用語の候補。本人の事実、否定、既往、家族歴を区別 |
| D049 | 妊娠・出産・不妊治療の記述 | 規 | 規 | 文 | 文 | 規 | 追限定 | — | 医療文書や用語を使った候補。文脈別に試験が必要 |
| D050 | 遺伝子検査結果の説明文 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 疾患説明と生の配列・変異の意味解釈は別 |
| D051 | DNA配列・生体試料の個人対応 | 規 | 規 | 規 | 規 | 規 | 拡 | — | 配列らしい形式は候補。専門解析と対応台帳なしに本人・疾患を確定できない |

### 思想信条など配慮を要する内容

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D052 | 民族・人種を表す語 | 標 | 標 | 規 | 文 | 規 | 拡 | — | 文中の語の検出。外見や姓から本人の属性を推定する用途に読み替えない |
| D053 | 宗教・信条を表す語 | 規 | 標 | 文 | 文 | 規 | 標限定 | — | GCのRELIGIOUS_TERM、PresidioのNRP。本人の信仰の確定ではない |
| D054 | 政治的所属・政治思想を表す語 | 規 | 標 | 文 | 文 | 規 | 標限定 | — | GCのPOLITICAL_TERM。政党への言及と本人の支持は別 |
| D055 | 労働組合の所属を表す語 | 規 | 標 | 文 | 文 | 規 | 規 | — | GCのTRADE_UNION。所属事実や労働法上の判断は別 |
| D056 | 性別・性自認の記述 | 標 | 標 | 文 | 文 | 規 | 拡 | — | 氏名や顔からの推測ではなく、明示された内容の検知 |
| D057 | 性的指向の記述 | 規 | 標 | 文 | 文 | 規 | 拡 | — | GCのSEXUAL_ORIENTATION。性的な内容一般の分類とは異なる |
| D058 | 性的生活・私的関係の記述 | 規 | 分限定 | 文 | 文 | 規 | 拡 | — | GCの性的話題の分類は、特定人の性的生活の事実認定ではない |
| D059 | 婚姻・離婚・家族関係 | 規 | 標限定 | 文 | 文 | 規 | 拡 | — | GCのMARITAL_STATUSは婚姻状態。家族全体の関係抽出を保証しない |
| D060 | 社会的身分・出自 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 地名・姓などから推測せず、明示記述の候補として扱う |
| D061 | 犯罪歴・身元調査の文書 | 規 | 分限定 | 文 | 分 | 規 | 拡 | — | GCの法的文書分類は近接種別。NightfallはFILE_BACKGROUND_OR_CRIMINAL |
| D062 | 犯罪被害・刑事手続・少年事件 | 規 | 分限定 | 文 | 文 | 規 | 拡 | — | 書類分類だけでは、被害者・被疑者・証人や確定判決を区別できない |
| D063 | 内部通報・相談・懲戒記録 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 人事・法務文書を候補にできるが、通報者の特定と保護判断は別 |

### 認証情報と技術上の秘密

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D064 | 平文パスワード | 標 | 標 | 標 | 標 | 規 | 規 | 標限定 | Gitleaksは資格情報の代入等に一致する範囲。任意の短い語をパスワードとは識別できない |
| D065 | 秘密鍵・暗号鍵 | 標 | 標 | 標限定 | 標 | 標 | 規 | 標 | 公開鍵や公開証明書まで一律に秘密と判定しない |
| D066 | AWS・Google Cloud・Azure等の鍵 | 標 | 標 | 標 | 標限定 | 標限定 | 規 | 標 | 提供者ごとの種類・形式に差。MacieはAWS・GCP等の列挙範囲 |
| D067 | 生成AIサービスのAPI鍵 | 規 | 標 | 規 | 標限定 | 規 | 規 | 標 | GCはOPENAI_API_KEY、ANTHROPIC_API_KEY等。Nightfallは汎用API_KEY |
| D068 | OAuth・Bearer・JWT | 標 | 標 | 標限定 | 標限定 | 標限定 | 規 | 標限定 | サービス固有形式の対応と、任意の認証文字列への対応を分ける |
| D069 | データベース接続文字列 | 規 | 規 | 標限定 | 標 | 規 | 規 | 標限定 | NightfallはDATABASE_CONNECTION_STRING。秘密を含まない接続文字列もあり得る |
| D070 | 署名付きURL・共有用秘密URL | 標限定 | 標限定 | 標限定 | 規 | 規 | 規 | 標限定 | Google Storageの署名URLやAzure SAS等、既知形式の範囲 |
| D071 | 弱いパスワードハッシュ | 標 | 標 | 規 | 規 | 規 | 規 | 規 | 対象形式の検出。実際に解読できるかの検証ではない |
| D072 | 復旧コード・ワンタイム番号 | 規 | 規 | 規 | 規 | 規 | 規 | 規 | 短い数字は汎用。見出し・期限・発行元などの情報が必要 |
| D073 | 鍵の有効性・失効状態 | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 形が正しいことでは確定できず、発行元の状態や認可された検証が必要 |

### 企業秘密と業務文書

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D074 | 機密や社外秘の明示表示 | 規 | 規 | 規 | 分 | 規 | 規 | 規 | NightfallのFILE_CONFIDENTIALは明確に機密表示された内容。表示のない秘密は別 |
| D075 | 顧客名簿・顧客管理の出力 | 規 | 規 | 文 | 分 | 規 | 拡 | — | NightfallはFILE_CUSTOMER_LIST。個人情報の箇所検知とも組み合わせる |
| D076 | 履歴書・職務経歴書 | 規 | 分 | 分 | 分限定 | 規 | 拡 | — | GCはDOCUMENT_TYPE/HR/RESUME。Nightfallは人事分類の範囲 |
| D077 | 人事評価・採用・解雇資料 | 規 | 規 | 分 | 分 | 規 | 拡 | — | 人事という文書分類と、各評価の内容・対象者の抽出を区別 |
| D078 | 契約書・秘密保持契約 | 規 | 分限定 | 分 | 分 | 規 | 拡 | — | GCは法務の話題や書類分類で候補。秘密保持契約専用とは扱わない |
| D079 | 訴訟・弁護士との相談文書 | 規 | 分限定 | 分限定 | 分限定 | 規 | 拡 | — | 法務分類は可能でも、法的秘匿特権や秘密保持義務の成立は確定しない |
| D080 | 請求書・見積・価格資料 | 規 | 分限定 | 分 | 分限定 | 規 | 拡 | — | GCとNightfallは請求書を確認。見積・価格全般へ無条件に広げない |
| D081 | 決算・予算・財務予測 | 規 | 分限定 | 分 | 分 | 規 | 拡 | — | GCは金融文書の種類。未公表かどうかは外部の公表状況が必要 |
| D082 | 買収・合併の交渉資料 | 規 | 規 | 分 | 分 | 規 | 拡 | — | NightfallはFILE_M_AND_A、PurviewはMerger and acquisition files |
| D083 | 経営戦略・取締役会資料 | 規 | 規 | 文 | 分 | 規 | 拡 | — | NightfallはFILE_EXECUTIVE_COMMS。Purviewは独自の事業計画分類を作る案[M4] |
| D084 | 製品計画・研究開発資料 | 規 | 規 | 分限定 | 分 | 規 | 拡 | — | 文書種別は候補。未発表製品かどうかは公表状態と照合 |
| D085 | 特許・発明資料 | 規 | 分 | 分限定 | 分 | 規 | 拡 | — | GCは特許・出願文書。Nightfallは内部向けと公開向けの分類を用意するが公表状態の真実性は別確認 |
| D086 | ソースコード | 規 | 分 | 分 | 分 | 規 | 拡 | — | ソースコードの存在と、所有権・公開許諾・企業秘密であることを区別 |
| D087 | 製造手順・配合・設計の説明文 | 規 | 規 | 分限定 | 分限定 | 規 | 拡 | — | Purviewは製造記録・手順、Nightfallは研究開発文書等。独自配合は定義が必要 |
| D088 | ネットワーク・セキュリティ設計 | 規 | 規 | 分 | 文 | 規 | 拡 | — | IPや鍵の検出だけでは設計全体の機密性は確定できない |
| D089 | データベース出力・システムログ | 規 | 分 | 文 | 文 | 規 | 拡 | — | GCはDATABASE_BACKUPとSYSTEM_LOG。含まれる個人情報や秘密は別検知 |
| D090 | 社内固有の案件名・機密語句 | 規 | 規 | 規 | 規 | 規 | 規 | 規 | 辞書登録済みの語は候補。未知の案件の秘密性は推定できない |
| D091 | 第三者から預かった秘密資料 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 表示・内容は候補。契約・受領経緯・利用許諾を外部情報で照合 |

### 画像や生体情報

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D092 | 顔や人物の画像 | 未 | 画 | 未 | 画限定 | 非 | 拡 | — | GCは顔や人物の存在。NightfallのSELFIE_IMAGEは正面の単独人物等に限定 |
| D093 | 旅券・免許証・身分証の画像 | 未 | 画 | 未 | 画 | 非 | 拡 | — | 写っている種類の分類であり、証明書の真正性検証ではない |
| D094 | カードの画像 | 未 | 未 | 未 | 画 | 非 | 拡 | — | 文字読取りによる番号検知とカード物体の分類を区別 |
| D095 | 手書き署名の画像 | 未 | 画 | 未 | 未 | 非 | 拡 | — | GCは署名の存在。署名者の本人認証ではない |
| D096 | 車のナンバープレート画像 | 未 | 画 | 未 | 未 | 非 | 拡 | — | GCは画像中の物体。日本の番号の全文字読取りを保証しない |
| D097 | 指紋・虹彩・声紋の本人照合 | 外 | 外 | 外 | 外 | 非 | 外 | — | 専用の生体照合と登録情報が必要。画像・音声の存在検出とは別 |
| D098 | CAD図面・回路図の技術的秘密 | 未 | 未 | 未 | 未 | 未 | 拡 | — | 文字部分の検出と形状・回路・製法の意味理解を区別。汎用保証は確認できない |
| D099 | 音声・動画内の会話内容 | 非 | 拡 | 未 | 非 | 非 | 拡 | — | 外部の文字起こしや動画解析を組み合わせる案。本文検査の機能だけでは足りない |

### 内容検査だけでは確定できない判断

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D100 | 公開済みか未公表か | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 公開台帳・発表履歴・対象版との照合が必要 |
| D101 | 法的な営業秘密に当たるか | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 管理状況や公知性など、本文以外の事実が必要 |
| D102 | 本人の同意・利用目的の適合 | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 同意記録・目的・提供先・処理経緯を照合 |
| D103 | 保存や外部共有が業務上許可か | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 所属・権限・共有状態・契約・例外許可が必要 |
| D104 | 合成値・架空人物か実在者か | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 形式や文脈だけで真実性を保証しない |
| D105 | 伏字・断片からの同一人物の確定 | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 他の対応情報なしに確定しない。似た文字列を本人と同一視しない |
| D106 | 複数資料を結合した再識別の可否 | 外 | 外 | 外 | 外 | 外 | 外 | 外 | 利用できる補助情報と結合条件を含む別評価が必要 |
| D107 | 暗号化され鍵を取得できない本文 | 不可 | 不可 | 条件 | 不可 | 不可 | 不可 | 不可 | 復号権限と鍵がなければ本文を検査できない。Purviewは保護方式・権限による例外を個別確認 |

### 国籍と教育と追加の業務情報

| ID | 項目 | GW | GC | MS | NF | AM | PR | GL | 補完と限界 |
|---|---|---|---|---|---|---|---|---|---|
| D108 | 国籍・出生国の明示記述 | 規 | 標 | 規 | 文 | 規 | 標限定 | — | GCのCOUNTRY_DEMOGRAPHIC、PRのNRP。地名の存在だけで国籍を確定しない |
| D109 | 在留資格・移民状態 | 規 | 標 | 文 | 文 | 規 | 拡 | — | GCのIMMIGRATION_STATUS。カード番号の検出とは別 |
| D110 | 学歴・成績・試験結果 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 様式と対象者との関係が必要。点数だけでは成績と確定しない |
| D111 | 生活保護・福祉給付の記録 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 制度名・本人との関係・支給記録を分けて判断 |
| D112 | 家庭相談・虐待・DVの記録 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 相談者・被害者・加害者・一般説明を区別。語句一致だけで事実認定しない |
| D113 | 勤怠・休職・労務の記録 | 規 | 規 | 分限定 | 分限定 | 規 | 拡 | — | 人事文書という広い分類の候補。病気による休職との関係は別 |
| D114 | 仕入先・受発注・取引条件 | 規 | 規 | 分限定 | 分限定 | 規 | 拡 | — | 調達・請求書等の近接分類。交渉条件が秘密かは契約・公表状態も必要 |
| D115 | AIへの指示文・学習資料 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 指示の改ざん検知とは別。独自の指示文が秘密かは組織の定義が必要 |
| D116 | 学習済みモデルの重み・数値配列 | 規 | 規 | 未 | 未 | 規 | 拡 | — | 対応形式と属性で候補化。数値だけで所有権や学習元の個人情報を確定できない |
| D117 | 入退室・警備・施設配置の情報 | 規 | 規 | 文 | 文 | 規 | 拡 | — | 施設の名称・配置図・警備運用の意味判断と、現在の許可状態を分ける |

## 標準検知の代表的な識別子

項目表の「標」「分」「画」は以下のような公開定義に対応する。識別子は製品ごとに異なり、同じ名前でも検査範囲・言語・精度は同一ではない。下表は追跡用の代表例であり、製品の全検知器を複製した一覧ではない。

| 対象 | 公開仕様上の例 | 根拠 |
|---|---|---|
| 氏名・住所 | GW：Name occurrence。GC：PERSON_NAME、STREET_ADDRESS。MS：All full names、Japan physical addresses。NF：PERSON_NAME、STREET_ADDRESS。PR：PERSON、LOCATION | G1、C1、M1、M5、M6、N1、P1。PRのLOCATIONは住所全体ではない |
| 日本の番号 | GC：JAPAN_INDIVIDUAL_NUMBER、JAPAN_DRIVERS_LICENSE_NUMBER、JAPAN_PASSPORT、JAPAN_BANK_ACCOUNT。MS：Japanese My Number Personal等。NF：JAPAN_MY_NUMBER | C1、M1、N1。GWも日本の4種類を列挙[G1] |
| 端末・位置 | GC：IP_ADDRESS、IMEI_HARDWARE_ID、ADVERTISING_ID、LOCATION_COORDINATES。AM：LATITUDE_LONGITUDE。NF：LAT_LNG | C1、A1、N1 |
| カード | GC：CREDIT_CARD_DATA。AM：CREDIT_CARD_NUMBER、CREDIT_CARD_SECURITY_CODE、CREDIT_CARD_EXPIRATION | C1、A1。集約種類と個別種類を区別 |
| 医療 | GC：MEDICAL_TERM、BLOOD_TYPE、MEDICAL_RECORD_NUMBER。PR：MEDICAL_DISEASE_DISORDER、MEDICAL_MEDICATION等は追加モデル | C1、P1。医療用語の検出は本人との関係を保証しない |
| 思想信条等 | GC：RELIGIOUS_TERM、POLITICAL_TERM、TRADE_UNION、SEXUAL_ORIENTATION、MARITAL_STATUS。PR：NRP | C1、P1。語の存在と本人の属性を区別 |
| 鍵・秘密 | GC：OPENAI_API_KEY、ANTHROPIC_API_KEY、PASSWORD。NF：API_KEY、PASSWORD_IN_CODE。GL：openai-api-key、anthropic-api-key、private-key | C1、N1、K1。任意の秘密文字列をすべて発見する保証ではない |
| 文書分類 | GC：DOCUMENT_TYPE/HR/RESUME、DOCUMENT_TYPE/R&D/SOURCE_CODE。NF：FILE_CUSTOMER_LIST、FILE_M_AND_A、FILE_BACKGROUND_OR_CRIMINAL。MS：Resume、Source code等 | C1、N1、M2。文書の種類と、公開状態・法的な秘密性を分ける |
| 画像 | GC：OBJECT_TYPE/PERSON/FACE、OBJECT_TYPE/PERSON/SIGNATURE。NF：SELFIE_IMAGE、PASSPORT_IMAGE | C1、N1。本人認証や偽造検査ではない |

## どこまでを検知成功と数えるか

| 段階 | 成功したといえること | まだ分からないこと |
|---|---|---|
| 読取り | 本文・画像・対象範囲を取得し解析できた | 検知器が対象の意味を捉えたか |
| 箇所の検知 | 氏名・番号・鍵などの候補と位置を得た | 実在性、本人との関係、業務上の許可 |
| 文書分類 | 医療記録・財務資料等の候補になった | 全機密箇所、正確な項目値、公開状態 |
| 関係の判断 | 誰の病歴・給与・信条かを本文等から判定した | 記述の真実性、同意・契約・権限 |
| 運用判断 | 現在の場所・共有・許可と照合して対応を決めた | 取得できない情報や、将来の変化 |

例えば「ある病気についての説明」「本人がその病気である」「本人の家族がその病気だった」「本人はその病気ではない」は同じ医療用語を含み得る。語の一致だけで4つを同じ病歴として登録しない。公開されている特許文書や公開ソースコードを検出しても、流出した企業秘密と確定したことにはならない。この区別は本調査の設計上の判断である。

## 項目の対応を無効にし得る入力条件

| 条件 | 比較表への影響 | 必要な追加処理・確認 |
|---|---|---|
| 画像・画像だけのPDF | 文字検知器だけでは本文がない | OCR（画像からの文字読取り）または画像分類。番号読取りと物体分類を別評価 |
| 手書き・縦書き・低解像度 | 読取り失敗で標準検知も失敗し得る | 日本語と画質ごとの試験 |
| ZIP等の圧縮内部 | 展開しなければ内部の文字は見えない | 対応形式、深さ、件数、展開後容量、個別の失敗を確認 |
| 暗号化・閲覧制限 | 内容を取得できなければ本文検査はできない | 復号権限と保護方式。保存媒体の暗号化と文書自体の暗号化を区別 |
| 表の別セル・別ページ | 名前と値・周辺語句が離れる | 抽出順序と検知範囲。関係を復元する処理が必要 |
| 伏字・分割・符号化 | 既知形式が崩れ、文字列だけでは復元できない場合がある | 認可された復号・正規化。欠損した内容を生成して補わない |
| 大容量・大量の検知 | 先頭だけの解析・結果打切りがあり得る | 検査範囲を記録し、未検査を問題なしにしない |
| 音声・動画 | 文字検査APIに音声の意味理解が備わるとは限らない | 文字起こし・画像抽出を別の処理として設計 |

製品ごとの形式・容量・Drive接続条件は[形式と精度の比較](dlp_detection_formats_accuracy_matrix_20261111.md)に整理済み。Macieは画像の内容検査を行わず、S3内の対応形式を対象とする[A3]。MSの外部サービス接続は公開試験版で、PDFや暗号化ファイルなどの制約がある[M7]。主表のMS列を、そのままDrive内で実行できる機能一覧にはしない。

## 類似サービスの追加候補

全117項目の標準検知器を公開資料から個別照合できていないため、以下を同じ粒度の○×表へ追加していない。一般的な「個人情報や秘密を分類」という説明から、日本の番号や短い氏名の対応を推測しない。

| サービス | 公開情報で確認できる方向性 | 個別項目について残る確認 |
|---|---|---|
| BigID | 形式規則、機械学習、自然言語処理、属性・文脈、独自分類を組み合わせる | 日本の番号・氏名・住所の検知器、接続先別の抽出、分類結果の取得条件。詳細は[既存調査](bigid_dlp_api_constraints_20261111.md) [X1] |
| Box Shield／Shield Pro | 通常のデータ種類・語句による分類と、説明文からのAI文書分類を提供 | 通常分類にはOCRなし。AI分類は画像対応と抽出上限が別。Box内の分類をDrive監視とは扱わない [X2] |
| Teleskope | 個人・医療・支払い・秘密情報と独自項目の文脈分類、分類・伏字化API | 国・言語・個別検知器・精度を照合。入力検査APIと既存保存先の全検知一覧を区別 [X3,X4] |

「高精度」「99%」等の提供者の数値は、対象項目・日本語・評価集合・見逃し率が同条件で示されない限り、比較の得点に使わない。

## API連携のしやすさ

ここでの評価は公開された入口と自作範囲からの設計上の判断で、導入時間の実測ではない。検査APIがあっても、本文取得の権限や保存先への接続は別途必要になる。

| 選択肢 | 本文を渡す検査 | 既存の検知結果を取得 | 規則・判定の扱い | 自作が必要な範囲 |
|---|---|---|---|---|
| Workspace DLP | 任意本文の検査入口とは分ける | Reports APIで規則監査記録。抜粋と全箇所一覧は別 | Policy APIで対応する規則・検知器を管理 | Driveの現在属性との照合、人の判定、許可、通知。複数APIの組合せ [G3,G4] |
| Sensitive Data Protection | content:inspectで本文・対応画像等を検査 | 自社で呼出し結果を保存。Workspaceの違反記録を取得するAPIではない | 検査条件・独自検知器・テンプレートを管理 | 保存先からの取得、形式抽出、予約、台帳、業務判断、通知。自作検査の入口を作りやすい [C2,C3,C4] |
| Nightfall Developer API | 本文検査の公開例あり | Native SaaS側の一覧とDeveloperの呼出し結果を区別 | 規則・検知器を指定。利用する機能のAPI対応を確認 | API検査と接続先の違反を同じ台帳へ集約する処理 [N5] |
| Macie | 任意文字列の同期検査APIとしては扱わない | S3検査の検知結果をAPIで収集 | 独自識別規則と検査ジョブ | S3以外からの搬入、処理待ち、抽出範囲、業務判断 [A1,A2] |
| Presidio | 自社運用の検査処理として組み込める | 自社で結果を保存 | 自分で認識器・モデル・規則を管理 | 配備、更新、抽出、認可、保存、通知の運用全体 [P1] |
| Gitleaks | コマンド実行や部品利用で秘密検査へ組み込む | 出力した検知を自社で収集 | 公開規則と独自設定 | 検査対象の取得、実行、鍵の状態確認、失効対応 [K1,K2] |
| Teleskope | Classify／Classify Collectionを公開 | Metadata APIで接続先の分類記録を扱う説明 | 契約・機能・個別APIの対応を確認 | 全件取得・版対応・見逃し測定・人の許可の契約を別途設計 [X4] |

今回のDrive中心の拡張では、既存のWorkspace DLPの結果を集め、Driveの場所・共有状態で許可を判定する。その上で、警告のない文書もSensitive Data Protectionや自作検知へ渡し、検知漏れを評価する構成が候補になる。APIを追加しただけでGoogle内部のモデルが学習するわけではない。[APIを使う適応型運用設計](adaptive_dlp_api_control_design_20261112.md)

## 追加検知を作る際の優先順

1. **形式が決まったもの**：カード、日本の識別番号、既知の鍵は標準検知器を選び、表記・形式別に検証する。
2. **組織固有のもの**：顧客番号、案件名、社内語句は形式規則・辞書・既知の値との照合を追加する。
3. **文脈が必要なもの**：人事、病歴、契約、製造や研究の秘密は、文書分類と箇所抽出を分けて評価する。
4. **外部の事実が必要なもの**：本人との対応、公開状態、同意、許可、鍵の失効は、台帳と現在の属性で判断する。

標準検知数の多さだけでは選定しない。同じ検知対象を番号単位に細分した製品と、大きな集約種類で表す製品は件数が異なる。必要な項目について、合成資料と正解箇所を用意し、適合率（検出したうち正しかった割合）、再現率（対象を見つけられた割合）、未検査率、人の確認負荷を測る。一般説明・否定・家族歴・公開資料・試験値も入れ、機微な語を含むだけの誤検知を測る。

## 公開出典

本調査の製品能力は、以下の公開本文・仕様・公開ソースコードを基に整理した。実データ、管理画面、契約者限定資料、認証情報は使用しない。取得URL・日時・本文の照合値は[出典台帳](sensitive_information_detection_item_sources_20261112.json)、全117項目の機械可読な判定表は[JSON](sensitive_information_detection_items_20261112.json)を参照。

| 番号 | 公開資料 | 確認対象 |
|---|---|---|
| G1 | [Google Workspace predefined content detectors](https://knowledge.workspace.google.com/admin/security/how-to-use-predefined-content-detectors) | 番号・氏名・用語・認証情報の標準一覧 |
| G2 | [Google Workspace custom content detectors](https://knowledge.workspace.google.com/admin/security/custom-content-detectors) | 語句・正規表現による独自検知 |
| G3 | [Rules Audit Activity Events](https://developers.google.com/workspace/admin/reports/v1/appendix/activity/rules) | 検知記録・抜粋・対象の項目 |
| G4 | [Policy API settings](https://docs.cloud.google.com/identity/docs/concepts/supported-policy-api-settings) | 規則・検知器の変更対応 |
| C1 | [Sensitive Data Protection infoType reference](https://docs.cloud.google.com/sensitive-data-protection/docs/infotypes-reference) | 標準種類、集約種類、文書・画像分類、地域制約 |
| C2 | [Custom infoType detectors](https://docs.cloud.google.com/sensitive-data-protection/docs/creating-custom-infotypes) | 辞書・形式規則と追加検知 |
| C3 | [content.inspect](https://docs.cloud.google.com/sensitive-data-protection/docs/reference/rest/v2/projects.content/inspect) | 検査APIと処理・出力の上限 |
| C4 | [Inspect images](https://docs.cloud.google.com/sensitive-data-protection/docs/inspecting-images) | 画像内文字と画像検査 |
| M1 | [Purview sensitive information type definitions](https://learn.microsoft.com/en-us/purview/sit-sensitive-information-type-entity-definitions) | 標準項目の一覧 |
| M2 | [Purview trainable classifier definitions](https://learn.microsoft.com/en-us/purview/trainable-classifiers-definitions?view=o365-worldwide) | 文書種類、対応言語と形式、ソースコードの限界 |
| M3 | [Create custom sensitive information types](https://learn.microsoft.com/en-us/purview/sit-create-a-custom-sensitive-information-type) | 独自規則・辞書、日本語の処理 |
| M4 | [Learn about trainable classifiers](https://learn.microsoft.com/en-us/purview/trainable-classifiers-learn-about) | 独自文書分類、公開後の再学習の制約 |
| M5 | [All full names](https://learn.microsoft.com/en-us/purview/sit-defn-all-full-names) | 日本を含む氏名の検知 |
| M6 | [Japan physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-japan-physical-addresses) | 日本の住所検知 |
| M7 | [DLP for non-Microsoft connected apps](https://learn.microsoft.com/en-us/purview/dlp-non-microsoft-connected-applications) | 外部接続先と試験提供・形式の制約 |
| M8 | [Japan resident registration number](https://learn.microsoft.com/en-us/purview/sit-defn-japan-resident-registration-number) | 桁数と周辺語句 |
| N1 | [Nightfall Detector Glossary](https://help.nightfall.ai/detection_platform/detection_glossary) | 個別項目・文書・画像分類、試験提供の注記 |
| N2 | [Nightfall custom detectors](https://help.nightfall.ai/detection_platform/custom_detectors) | 辞書・形式規則・独自検知の入口 |
| N3 | [Prompt-based file classifier](https://help.nightfall.ai/detection_platform/custom_detectors/create-a-prompt-based-file-classifier) | 意味による文書分類と対象入力 |
| N4 | [Prompt-based entity detector](https://help.nightfall.ai/detection_platform/custom_detectors/create-an-entity-detector-using-a-prompt) | 意味による箇所抽出と対象入力 |
| N5 | [Nightfall API quickstart](https://help.nightfall.ai/developer-api/introduction/quickstart) | 本文検査の呼出し例 |
| A1 | [Macie managed identifiers by type](https://docs.aws.amazon.com/macie/latest/user/mdis-reference-quick.html) | 対応国、標準項目、必須の周辺語句 |
| A2 | [Macie custom identifiers](https://docs.aws.amazon.com/macie/latest/user/custom-data-identifiers.html) | 独自の形式規則と周辺語句 |
| A3 | [Macie supported storage and formats](https://docs.aws.amazon.com/macie/latest/user/discovery-supported-storage.html) | S3、画像非対応、圧縮と抽出の条件 |
| P1 | [Presidio supported entities](https://presidio.dataprivacystack.org/supported_entities/) | 標準認識器と任意追加の医療モデル |
| K1 | [Gitleaks default rules](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml) | 提供者別の秘密検知規則 |
| K2 | [Gitleaks repository](https://github.com/gitleaks/gitleaks) | 対象と実行方式、独自規則 |
| X1 | [BigID discovery and classification](https://bigid.com/discovery-classification/) | 独自規則・機械学習・文脈による分類 |
| X2 | [Box Shield FAQ](https://support.box.com/hc/en-us/articles/360043696834-Shield-Frequently-Asked-Questions) | 通常分類とAI分類、画像・抽出の条件 |
| X3 | [Teleskope Understand](https://www.teleskope.ai/products/understand) | 独自項目と文書の文脈分類 |
| X4 | [Teleskope API Service](https://docs.teleskope.ai/the-platform/api-service) | Classify、Scrub、Metadataの入口 |
| L1 | [個人情報保護委員会 通則編](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/) | 個人情報と要配慮個人情報の概念。検知製品の分類と法的該当性は別 |
