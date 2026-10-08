# 機密情報管理の新興企業と投資会社の調査

調査日：2026年10月7日。2026年10月8日にYC・投資会社・企業発表を再確認し、MINDの直近調達と医療機関の利用説明を追加した。企業・YC・投資会社・買収企業・米国証券取引委員会（SEC）の公開資料を確認した。金額は発表時の原通貨。資金調達の一覧は今回一次資料で確認できた公表ラウンドであり、未公表分を含む完全な履歴ではない。

## 1. 今回の問いへの回答

企業の機密情報を分類し、外部AIへの入力や共有を制御する新興企業は存在する。YCではStrac、Candor Security、PromptArmor、Superagent、compliant-llmを確認した。国内では2026年1月設立のAlmureが新しく、AcompanyとEAGLYSには機密計算分野の事業・資金提供の実績がある。

以前の問いとの対応では、**機密かどうかの文脈判定はHarmonic Security、Teleskope、Candor Security、メールの本文と宛先の関係はBonfy.AI、処理する事業者から内容を隠す基盤はConfident Security、Almure、Acompany**が候補になる。これは公開機能による候補選定で、同じ評価用データによる精度順位ではない。Bonfy.AIは2026年9月に買収済みで、現在の独立企業としては扱わない。根拠は以下の各行に示す。

## 2. 用語と、混同すると設計を誤る点

| 用語 | この資料での意味 |
|---|---|
| DLP（Data Loss Prevention） | 機密情報の持ち出しを検出し、警告・遮断・削除などを行う仕組み |
| DSPM（Data Security Posture Management） | 保存場所、機密性、アクセス権、外部公開などを横断的に把握し、危険な状態を直す管理 |
| 文脈による分類 | 単語だけでなく、文書の意味、利用者、業務、送り先などから機密性・共有の妥当性を判断すること |
| AIの利用制御 | AIへの入力・出力・道具の呼び出しに検査を挟み、許可された操作だけを実行させること |
| 機密計算／TEE（Trusted Execution Environment） | ハードウェアで保護された実行領域で処理し、クラウド運営者などから処理中のデータを隔離する技術 |
| シード、シリーズA・Bなど | 事業の初期や成長段階で行う資金調達の呼称。段階名だけでは成熟度・性能を判断できない |
| 主導投資家 | 当該調達を中心となって取りまとめる投資家 |

**「外部の管理者が平文を読めない」と「分類モデル自身が平文を処理しない」は別条件である。** TEE内で通常のAI推論を行う方式では、保護領域の内部でモデルが内容を処理する。今回の企業群の公開資料から、企業文書の汎用的な意味分類を完全準同型暗号や多者間計算だけで行う商用サービスを確認した、とは結論できない。

完全準同型暗号は暗号化したまま演算する技術、多者間計算は入力を複数者に分けて共同計算する技術、ゼロ知識証明は秘密を明かさずある主張の成立を証明する技術である。実行環境の正当性を遠隔確認する「リモート認証」はゼロ知識証明と同義ではない。技術の詳細は[平文を読まない機密分類](confidentiality_classification_without_plaintext_20261007.md)と[ゼロ知識証明の調査](zero_knowledge_sensitive_data_research_20261007.md)を参照。

## 3. YC採択企業

WはWinter、冬期の採択回を表す。YC掲載のActiveはYC上の表示であり、本調査が事業継続や顧客環境での稼働を監査した結果ではない。

| 企業 | 設立・YC採択 | 提供内容と今回の関心との関係 | 投資・確認できた調達 | 一次資料 |
|---|---|---|---|---|
| Strac | 2021年設立、W2022 | 業務クラウド、端末、AIへの機密情報の流出を検出し、遮断・伏字化など。Google WorkspaceとMicrosoft 365を含む広い対象 | YC、FUSEの投資先として確認。会社の採用説明に350万米ドルのシード調達を記載 | [YC](https://www.ycombinator.com/companies/strac)、[製品](https://www.strac.io/ai-governance)、[調達の会社説明](https://www.ycombinator.com/companies/strac/jobs)、[FUSE](https://careers.fuse.vc/companies/strac) |
| Candor Security | 2024年設立、W2025 | 利用者・活動の文脈を使うDLP。機密性と内部からの流出リスクを扱う。会社は顧客ごとに隔離した環境、クラウド・自社設備への配置を説明 | YC確認。追加の調達額・投資家は今回の一次資料で未確認 | [YC](https://www.ycombinator.com/companies/candor-security)、[製品・処理環境](https://candor.security/) |
| PromptArmor | 2023年設立、W2024 | 現在はAIサービスの利用に伴う危険の調査・継続把握が中心。外部サービスの接続権限やデータ方針などを扱う。文書分類を強制する装置とは役割が異なる | YC確認。追加の調達額・投資家は未確認 | [YC](https://www.ycombinator.com/companies/promptarmor)、[現行製品](https://www.promptarmor.com/) |
| Superagent | 2024年設立、W2024 | AIの入力文脈・実行時操作の制御に加え、現在はコード・依存関係・侵入経路の検査へ対象を拡大。独自業務AIの情報流出対策に関連 | YC確認。追加の調達額・投資家は未確認 | [YC](https://www.ycombinator.com/companies/superagent)、[現行製品](https://www.superagent.sh/) |
| compliant-llm / CompliantLLM | 2023年設立、W2023 | 外部生成AIとのやり取りを監視。過去の活動、役割、アクセス権を考慮する。以前のFiddleCubeから事業内容が変化 | YC確認。追加の調達額・投資家は未確認 | [YCの現行紹介と過去の発表](https://www.ycombinator.com/companies/compliant-llm) |

StracやCandorの紹介にDLPと書かれていることだけで、Outlook・Gmailの全送信経路でCCの禁止先を必ず遮断できるとは判断しない。CompliantLLMの「全ての漏えいを検出」という会社の表現も、検出率100%を実証した結果として扱わない。

Superagentは2026年10月の現行サイトで総合的なセキュリティ業務の自動化を前面に出している。YC紹介だけを読んで、外部AI入力の検査専業として比較すると現在の対象を取り違える。[現行サイト](https://www.superagent.sh/)

YCの現行標準条件は合計50万米ドルで、12.5万米ドルが株式7%相当、37.5万米ドルは将来の条件に連動して転換する別契約である。合計50万米ドルが単純に7%だけに対応するわけではない。この標準条件から各社の総調達額を推定してはいけない。[YC Standard Deal](https://www.ycombinator.com/deal)

## 4. 文脈による機密分類・企業データ管理

| 企業 | 製品の焦点 | 今回確認した資金調達 | 主な投資家 | 一次資料 |
|---|---|---|---|---|
| MIND | 2023年設立。本文と業務の文脈から機密性を分類し、端末、メール、業務クラウド、生成AIへの持ち出しを検出・遮断 | 2026年9月17日、7,200万米ドルのシリーズB。累計1億1,200万米ドル | Crosspoint Capital Partnersが主導、YL Ventures、Paladin Capital Groupが参加 | [会社の調達発表](https://mind.io/newsroom/mind-raises-usd72m-series-b-funding-to-bring-complete-dlp-to-the-ai-era)、[設立年・投資家紹介](https://www.ylventures.com/)、[YL Venturesの出資理由](https://www.ylventures.com/news-and-insights/blog/minds-series-a-signals-the-future-of-dlp/) |
| Harmonic Security | AIの利用状況と業務の文脈を考慮し、機密情報の送信を検出・制御。2023年8月設立 | 2024年10月、1,750万米ドルのシリーズA | N47が主導。Ten Eleven Venturesも会社の投資関係者として確認 | [製品](https://www.harmonic.security/)、[沿革](https://www.harmonic.security/about)、[N47の投資発表](https://www.n47.com/insights/data-protection-in-the-age-of-ai-next47-leads-harmonic-securitys-series-a) |
| Teleskope | 文書の意味による分類と、機密性・共有状態・社内方針に応じた修正。通知を出すだけでなく対処を進める設計 | 2025年11月公表、2,500万米ドルのシリーズA。累計3,220万米ドル | M13が主導、Primary Venture Partners、Lerer Hippeau | [調達発表](https://www.businesswire.com/news/home/20251031409379/en/Teleskope-Raises-%2425-Million-to-Accelerate-Adoption-of-the-Industrys-First-Agentic-Data-Security-Platform)、[M13](https://www.m13.co/article/meet-teleskope-moving-data-security-from-alerts-to-remediation)、[製品](https://www.teleskope.ai/products/data-reasoning-layer) |
| Sentra | データの保存場所・機密性・権限を把握するDSPM。CopilotやGeminiが参照する情報の過剰な共有を調べる用途にも関係 | 2025年4月22日、5,000万米ドルのシリーズB。累計1億米ドル超 | Key1 Capitalが主導、Bessemer Venture Partners、Zeev Ventures、Standard Investments、Munich Re Ventures | [調達発表](https://sentra.io/news/sentra-closes-50-million-series-b-amid-surging-demand-for-securing-data-for-ai-adoption)、[AI向け説明](https://sentra.io/learn/evaluate-dspm-dlp-copilot-gemini) |

MINDの2026年9月の会社発表には、Children’s Hospital Los Angelesの情報システム責任者が、端末からAIへ患者情報が入力されることの検出・遮断に利用しているとの説明がある。National Geographic Societyも、機密文書への区分付与と公開共有の制限を説明している。会社が掲載した利用者の発言であり、日本語での検出精度や全経路での遮断を独立検証した結果ではない。[会社発表](https://mind.io/newsroom/mind-raises-usd72m-series-b-funding-to-bring-complete-dlp-to-the-ai-era)

YL Venturesはサイバーセキュリティ分野に特化する投資会社で、MINDの初期調達を主導したと説明する。2025年6月の出資理由は、保存データの危険把握と持ち出し防止を統合し、文脈を使った検出と対処を進める点にある。[投資会社の紹介](https://www.ylventures.com/)、[投資理由](https://www.ylventures.com/news-and-insights/blog/minds-series-a-signals-the-future-of-dlp/)

Teleskopeでは、判断の確信が低い場合に人へ回す運用や、方針に基づく修正を説明している。「機密文書だから全て削除する」よりも、共有範囲を業務に合わせる用途に近い。将来の製品発表予定は調査日時点の提供機能として数えていない。[Data Reasoning Layer](https://www.teleskope.ai/products/data-reasoning-layer)

Sentraの顧客環境内での検査という説明は、外部へ本文を送らない構成を検討する材料になる。ただし、分類器が平文を処理しないことや、分類結果・管理情報も一切外へ出ないことまで意味しない。[SentraのAI向け説明](https://sentra.io/learn/evaluate-dspm-dlp-copilot-gemini)

会社の精度・削減率の宣伝値は比較の順位付けに採用しなかった。日本語の契約書、短いメール、添付文書を含む共通の評価用データが公開されていないためである。

## 5. 処理事業者にも内容を見せないAI基盤と国内企業

| 企業 | 技術・対象 | 調達・資金提供 | 投資家・資金提供者 | 一次資料 |
|---|---|---|---|---|
| Confident Security | CONFSEC / OpenPCC。TEE、実行環境の遠隔検証、通信の保護などを組み合わせ、AI推論を保護。分類モデルそのものではなく保護された処理基盤 | 2025年11月5日の発表で500万米ドルのシード調達を記載 | Decibel、Ex/Ante、South Park Commons、Halcyon、SAIF | [製品](https://confident.security/)、[SDK](https://docs.confident.security/sdks/python)、[OpenPCC・調達発表](https://www.businesswire.com/news/home/20251105013372/en/Confident-Security-Launches-OpenPCC-an-Open-Source-Standard-that-Protects-Data-Shared-with-AI-Models) |
| Almure | 2026年1月設立。金融・製造・医療・防衛などの機密データを扱うAIの実行基盤を開発。ハードウェアによる隔離・暗号化を説明 | 2026年4月15日、2億円のシード調達 | Genesia VenturesのGV-4、Dual Bridge Capital、NEX-T Tokai Innovation Fund（Prime Partners / 東海東京証券共同運営） | [会社発表](https://prtimes.jp/main/html/rd/p/000000004.000179806.html)、[Genesia Ventures](https://www.genesiaventures.com/investment-almure/) |
| Acompany | 機密計算を事業化。2026年の調達発表ではConfidential AI Suiteを含む機密保護付きAIサービスを説明 | 2025年5月14日、11億円のシリーズB。別に2026年4月14日、9.6億円の融資等による調達を公表 | シリーズB：SBI Investmentが主導、GLOBIS Capital Partners、Central Japan Innovation Capital。2026年の資金提供：北國銀行、あおぞら企業投資、Funds Startups、りそな銀行、日本政策金融公庫 | [2025年出資](https://www.acompany.tech/news/25-0514-1)、[2026年融資等](https://prtimes.jp/main/html/rd/p/000000130.000046917.html) |
| EAGLYS | 暗号化したデータの計算・活用に取り組む国内企業。BIPROGYと資本業務提携 | 2025年8月25日契約、9月4日発表。出資額は未公表 | BIPROGY。事業会社との提携であり、投資会社による調達と分ける | [会社発表](https://eaglys.co.jp/resource/news/250904)、[BIPROGYのPDF](https://www.biprogy.com/pdf/news/nr_250904.pdf) |

Confident Securityには2025年7月の420万米ドルの発表もあるが、11月の500万米ドルと足して920万米ドルとは記載しない。OpenPCC対応モデル・サーバーと検証設定を必要とするため、通常の公開AIのAPIに同じ入力を送るだけで同等の保護が得られる仕組みでもない。[OpenPCCの発表](https://www.businesswire.com/news/home/20251105013372/en/Confident-Security-Launches-OpenPCC-an-Open-Source-Standard-that-Protects-Data-Shared-with-AI-Models)、[SDKの設定](https://docs.confident.security/sdks/python)

Almureは新規性の高い候補だが、出資発表の研究開発目標を、銀行や病院での導入完了・認証取得として扱わない。Acompanyの2026年9.6億円は出資だけで構成された次のシリーズ調達ではなく、融資等を含む資金調達である。[Almureの投資発表](https://www.genesiaventures.com/investment-almure/)、[Acompanyの資金調達発表](https://prtimes.jp/main/html/rd/p/000000130.000046917.html)

## 6. メールの文脈判定に近いBonfy.AIと、買収・成長企業

### Bonfy.AI：内容と共有相手を組み合わせる例

Bonfy.AIは会社の方針や取引関係を踏まえて、人やAIが作成した内容の危険を調べる。現行サイトはMicrosoftのメール、Google WorkspaceのGmail・Drive・Directoryとの連携を掲載する。メールの本文だけでなく「この内容をこの相手に共有してよいか」という問いに近い候補である。[現行製品](https://www.bonfy.ai/)

2025年6月26日の公開開始時の会社発表では、2024年に確保した950万米ドルのシード資金を記載。TLV Partnersが主導し、Saban Venturesが参加した。ページの後日の更新日を、資金調達日や公開開始日と取り違えない。[会社の公開開始発表](https://blog.bonfy.ai/news-room/press-release-bonfy.ai-launches-from-stealth-to-guard-against-genai-risks-with-adaptive-content-security-platform)

**Kiteworksは2026年9月8日にBonfy.AIの買収を発表した。** 発表は送信前に内容と送信者、受信者、取引関係、経路、業務目的を考慮する方向を説明している。現在の比較では「買収済みの製品」と明示する。[買収企業の発表](https://www.kiteworks.com/company/press-releases/kiteworks-acquires-bonfy-ai/)

CCに競合企業や別案件の関係者が混入した場合の確実な遮断には、全宛先の渡し方、名簿・案件権限、添付の解析、判定失敗時の動作、端末や送信経路ごとの実装を確認する必要がある。会社の文脈判定という説明だけで、この動作を確認済みとはしない。既存の[メール誤送信防止調査](email_misdirection_ai_controls_20261007.md)の検証項目と組み合わせる。

### 新設企業と区別して比較する企業

| 企業 | 比較する理由 | 公表された調達・状態 | 一次資料 |
|---|---|---|---|
| Cyberhaven | データがどこから来て、コピー・加工・移動されたかという来歴を使う情報保護 | 2025年4月2日、1億米ドルのシリーズD。StepStoneが主導、Schroders、Industry Venturesが参加。成長段階の比較対象 | [調達・事業説明](https://www.cyberhaven.com/press-releases/cyberhaven-raises-100-million-series-d-at-1-billion-valuation) |
| Nightfall AI | 業務クラウドのデータ保護・機密情報検出の比較対象 | 2022年8月10日、4,000万米ドルのシリーズB。WestBridge Capitalが主導、Next Play Capital、Bain Capital Ventures、Venrock、Pear VCが参加。2026年の新規調達としては扱わない | [当時の会社発表](https://www.nightfall.ai/blog/nightfall-ai-raises-40-million-series-b-to-expand-cloud-data-protection-platform) |
| Prompt Security | 生成AIの利用・入力・実行に対する保護の市場で買収が進んでいる例 | SentinelOneが2025年8月5日に買収契約を発表。年次報告書では2025年9月5日の完了を記載。独立企業から除外 | [買収契約発表](https://www.sentinelone.com/press/sentinelone-to-acquire-prompt-security-to-advance-genai-security/)、[SEC掲載の年次報告書](https://www.sec.gov/Archives/edgar/data/1583708/000158370826000035/sentineloneincfy2026annuala.pdf) |

## 7. 投資会社自身の情報から分かる投資の着眼点

以下は今回確認した出資と説明の対応表であり、各投資会社の全投資方針を要約したものではない。

| 投資会社・組織 | この分野で確認した企業 | 公表資料から読み取れる着眼点 | 資料 |
|---|---|---|---|
| Y Combinator | Strac、Candor Security、PromptArmor、Superagent、compliant-llm | データ保護、AIサービスの危険把握、AIの操作制御など複数の対象への採択がある。採択だけで製品性能を証明するものではない | [企業一覧](https://www.ycombinator.com/companies)、[投資条件](https://www.ycombinator.com/deal)、上記各社ページ |
| FUSE | Strac | 投資先として確認。今回の資料から独自の投資理由までは確定しない | [投資先紹介](https://careers.fuse.vc/companies/strac) |
| YL Ventures / Crosspoint Capital Partners / Paladin Capital Group | MIND | 機密情報の分類、保存状態の把握、持ち出し防止を統合する方向。YL Venturesは初期から出資、Crosspointは2026年シリーズBを主導 | [YL Venturesの投資理由](https://www.ylventures.com/news-and-insights/blog/minds-series-a-signals-the-future-of-dlp/)、[調達発表内の主導投資家コメント](https://mind.io/newsroom/mind-raises-usd72m-series-b-funding-to-bring-complete-dlp-to-the-ai-era) |
| N47 | Harmonic Security | AI利用で増える非構造化データの保護、業務の内容を理解する分類への期待 | [主導投資の説明](https://www.n47.com/insights/data-protection-in-the-age-of-ai-next47-leads-harmonic-securitys-series-a) |
| M13 | Teleskope | 警告を増やすだけでなく、意味を判定し、方針に基づく修正まで進めるデータ管理 | [投資理由](https://www.m13.co/article/meet-teleskope-moving-data-security-from-alerts-to-remediation) |
| TLV Partners | Bonfy.AI（現在は買収済み） | AIツールだけでなく、人・AIが作る情報の内容と組織の業務文脈を保護する方向 | [Why We Invested in Bonfy.AI](https://www.tlv.partners/why-we-invested-in-bonfy/) |
| Genesia Ventures | Almure | AIが作成したコードの実行と、金融・製造・医療・防衛で必要な機密保護・導入要件への対応 | [出資背景とGV-4](https://www.genesiaventures.com/investment-almure/) |
| South Park Commonsなど | Confident Security | AI活用と情報保護を両立する共通の処理基盤。South Park Commonsの投資家によるコメントを掲載 | [会社発表内の投資家コメント](https://www.businesswire.com/news/home/20251105013372/en/Confident-Security-Launches-OpenPCC-an-Open-Source-Standard-that-Protects-Data-Shared-with-AI-Models) |

そのほか、SentraのKey1 Capital、Bessemer Venture Partners等、TeleskopeのPrimary Venture Partners・Lerer Hippeau、Confident SecurityのDecibel・Ex/Ante・Halcyon・SAIF、AcompanyのSBI Investment・GLOBIS Capital Partners・Central Japan Innovation Capitalを会社の調達発表で確認した。これらについて、会社の発表から投資会社自身の詳細な理念や全投資領域を推定していない。

資料を横断すると、投資対象には「文脈を理解して共有を制御する製品」「データと権限を把握し修正する製品」「外部事業者からも内容を保護する処理基盤」の三方向が見える。これは本調査の分類であり、投資額の市場全体に占める比率や将来の収益性を測った結果ではない。

## 8. 検討する順序と実機で確認する項目

| 解決したい問題 | 公開機能に基づく比較候補 | 確認する項目 |
|---|---|---|
| 機密かどうかを文脈から分類 | MIND、Harmonic Security、Teleskope、Candor Security | 日本語、契約・研究・医療の語彙、短文、誤検出、会社固有の情報、処理場所 |
| 公開AIへ社員が貼り付ける情報の制御 | Strac、Harmonic Security。AI利用の調査にはPromptArmor | 貼り付け・添付・ブラウザー以外の経路、遮断の時点、ログへの本文保存 |
| メール本文・添付とTo/CC/BCCの整合性 | Bonfy.AI、前回調査のProofpoint・KnowBe4等 | 全宛先を対象にするか、外部ドメインだけでなく案件の権限を扱えるか、Outlook/Gmail・携帯端末・API送信 |
| 保存データやAI検索の過剰権限 | Sentra、Teleskope、Candor Security | 権限変更の反映、検索・派生文書の権限、修正前承認、復元 |
| 基盤の運営者にも本文を見せたくない | Confident Security、Almure、Acompany | 保護領域、実行するコード・モデルの検証、鍵、検証失敗時の停止、出力と監査記録 |
| モデル自身にも平文を処理させたくない | 準同型暗号・多者間計算の研究を別途評価 | 対応する分類器、長文・日本語、遅延、費用、出力からの漏えい。今回の新興企業の紹介だけでは達成を確認できない |

製品を比較する際は、共通の評価用文書に「機密でないが機密らしい文」「機密だが番号・定型語を含まない文」「同じ本文でも宛先で許可が変わるメール」を含める。この確認によって、単純な検出性能と、業務上の共有可否の判断を分けて評価できる。

## 9. 保存資料・検証の範囲

- [取得台帳](sensitive_data_startup_sources_20261007.json)：取得時刻、URL、保存場所、SHA-256、PDF頁数、抽出本文の量、失敗理由。
- [再取得用スクリプト](../../scripts/download_sensitive_data_startup_materials.py)。原本と抽出本文は `research/disclosures/raw/startup_sensitive_data_20261007/` に保存し、Git管理対象外とする。
- 39件を取得対象とし、35件（HTML 34件、PDF 1件・2頁）を保存した。Business WireのTeleskope・Confident Securityの発表は時間切れ、CompliantLLMのサイトは転送処理、SECの年次報告書はHTTP 403で直接取得できなかった。閲覧による確認と直接保存を区別し、これらを取得成功に数えない。実際の成功・失敗は台帳の `status` が正とする。
- 資金調達日は発表本文と投資会社の説明・沿革を優先した。特にTeleskopeの過去記事の再掲載、Bonfy.AIのページ更新、Acompanyの出資と融資を区別した。
- 製品説明と会社公表の顧客の声を読んだが、契約、実環境、検出精度、銀行・医療機関での非公開導入は検証していない。顧客のロゴだけで全社導入や具体的な遮断条件を推定しない。

### 2026年10月8日の追加取得

MINDの調達発表を原本・抽出本文として追加保存した。YL Venturesの投資先紹介・出資理由は閲覧で確認したが、直接取得はHTTP 403で失敗した。追加取得は3件中1件成功。[追加取得台帳](sensitive_data_startup_additional_sources_20261008.json)。上記39件の初回取得数には追加分を含めない。
