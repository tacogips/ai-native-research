# CCPA・GDPRに対応できるAI提供事業者と、日本法の候補選定への使い方

確認日：2026年11月9日。対象：民間企業が個人データを入力する、企業向け生成AI・大規模言語モデル（文章等を理解・生成するAI）の外部サービス。公開一次資料だけに基づく事前調査。

## 結論

**CCPA・GDPRへの対応を支える契約・機能を提供するAI事業者はある。** OpenAI、Anthropic、Microsoft、AWS、Google Cloud、Mistral AIの6社は公開契約本文に根拠を確認できた。Cohereも両法への対応を公表しており追加候補になるが、本調査では個別のデータ処理契約本文まで確認していない。

ただし、ここで確認したのは「適法な利用を構成するための契約・機能」であり、**事業者全体やあらゆる利用方法の適法性を認定したものではない。** 日本の個人情報保護法への適合は、利用目的、入力する情報、契約相手、実際の取扱いと設定を含めて別途評価する。CCPA・GDPRの対応実績は、候補を絞る資料にはなるが、日本法への適合の代用にはならない。[GDPR本文](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)、[CCPA公式解説](https://www.oag.ca.gov/privacy/ccpa)、[個人情報保護委員会の生成AI注意喚起](https://www.ppc.go.jp/files/pdf/230602_alert_generative_AI_service.pdf)

## 用語と確認の範囲

| 用語 | 本資料での意味 |
|---|---|
| GDPR | EUの一般データ保護規則。本人の権利、適法な処理の根拠、安全管理、委託、域外移転などを規定する |
| CCPA | California Consumer Privacy Act。本資料ではCPRA（California Privacy Rights Act）による改正と関連規則を含むカリフォルニア州の制度を指す |
| DPA | Data Processing Addendum / Agreement。個人データ処理の目的、指示、秘密保持、再委託、削除、事故時の協力等を定める契約 |
| 管理者・処理者 | GDPRのcontroller / processor。処理の目的・手段を決める者と、その指示で処理する者。サービスの処理ごとに役割が変わり得る |
| サービス提供者 | CCPAのservice provider。契約で定めた業務目的等の範囲で事業者の個人情報を処理する者。一般語の「提供事業者」と区別する |
| SCC | Standard Contractual Clauses。欧州委員会の標準契約条項。一定の域外移転を支える仕組みで、日本法上の移転要件を自動的に満たす証明ではない |
| ZDR | Zero Data Retention。応答後に入力・出力を保存しない取扱い。対象機能、承認、例外は事業者ごとに異なる |
| API | ソフトウェアからAI等を呼び出す接続口。会話画面のサービスと契約・保存条件が異なることがある |

GDPR第28条は処理者の選定と契約、第32条は安全管理、第44条以降は域外移転を規定する。顧客側の第6条の処理根拠や第9条の特別な種類の個人データの条件などは、DPA締結だけでは満たせない。CCPAも事業者とサービス提供者を区別し、本人への通知や権利対応等を顧客側に残す。[GDPR本文](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)、[CCPA公式解説](https://www.oag.ca.gov/privacy/ccpa)

以下の「契約確認」は公開条項を確認したという意味で、監督機関による包括的な承認や、運用実態の監査結果ではない。ISO/IEC 27001（情報セキュリティ管理の規格）やSOC 2（組織の統制に関する保証報告）の取得表示も、両法への適合判定とは分ける。

## 事業者・製品別の比較

| 事業者と対象 | GDPRへの公開根拠 | CCPAへの公開根拠 | 日本法調査へ進める条件・未確認点 | 確認水準 |
|---|---|---|---|---|
| **OpenAI**：API、ChatGPT Enterprise / Business等の事業用契約対象 | DPA第1〜4節に処理者の役割、本人請求への支援、再委託、削除、SCC等 | DPA第5節に販売・共有や契約外利用・結合の制限等 | APIの学習不使用は原則。保存期間、ZDR承認、会話・ファイル等の保存、契約対象を分けて確認 | 契約確認。[DPA](https://openai.com/policies/data-processing-addendum/)、[APIの取扱い](https://developers.openai.com/api/docs/guides/your-data) |
| **Anthropic**：Claudeの商用契約、Claude API | DPAに処理者の役割、本人請求支援、再委託、SCC | DPA A.12、B.3等にservice providerへの読み替えと販売・共有・目的外利用・結合制限。CCPAの名称表示だけに依存しない根拠 | 商用は原則学習不使用だが評価・不具合報告の送信は例外。モデル別の保存義務と会話履歴を確認 | 契約確認。[DPA](https://www.anthropic.com/legal/data-processing-addendum)、[学習方針](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training) |
| **Microsoft**：Azure OpenAIを含むMicrosoft Foundryの「Models sold by Azure」 | DPAのGDPR条項、Attachment 1、SCC等。製品の公式資料が適用DPAを指定 | DPAの「California Consumer Privacy Act (CCPA)」節に目的制限と販売禁止 | 顧客データを許可なく基盤モデル学習に使わない。配備方式、監視、保存機能を指定。Foundry内の他の販売・運営方式へ一律に広げない | 契約確認。2026年11月版の本文を取得・抽出。[DPA配布元](https://www.microsoft.com/licensing/docs/view/Microsoft-Products-and-Services-Data-Protection-Addendum-DPA)、[製品の取扱い](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy) |
| **AWS**：Amazon Bedrock | AWS DPAおよびService Terms 1.14.1〜1.14.4にSCC等 | Service Terms 1.14.5がAWS CCPA Termsを組み込み、同条項に販売・共有・目的外利用等の制限 | モデルと地域ごとに保存設定を確認。`none`が使えないモデルや、監視目的の保存・人による確認を要する場合がある | 契約確認。[Service Terms](https://aws.amazon.com/service-terms/)、[DPA](https://d1.awsstatic.com/legal/aws-dpa/aws-dpa.pdf)、[CCPA Terms](https://d1.awsstatic.com/legal/aws-ccpa/aws-ccpa-terms.pdf) |
| **Google Cloud**：Vertex AIの生成AI系資料から案内されるGemini Enterprise Agent Platform等の契約対象 | Cloud DPAの役割・安全管理・再委託・欧州法／SCC条項 | 同DPA Appendix 3「California」に販売・共有・目的外利用・結合等の制限 | 許可・指示なしの学習はしない。検索・地図参照、会話状態等には別の保存条件。第三者モデルも対象契約と運営主体を確認 | 契約確認。[Cloud DPA](https://cloud.google.com/terms/data-processing-addendum)、[生成AIの取扱い](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention) |
| **Mistral AI**：商用契約の対象製品・有料API | DPAがGDPRを明示し、処理者義務、本人請求、監査、域外移転を規定 | DPA第12.2節にCCPAの販売・共有・契約外利用・結合制限 | DPA第2.3節は学習等で管理者となる場合を規定。学習停止の適用と評価送信の例外を確認。ZDRは承認済みの従量課金・対象APIに限定 | 契約確認。[DPA](https://legal.mistral.ai/terms/data-processing-addendum/)、[ZDR条件](https://help.mistral.ai/en/articles/347612-can-i-activate-zero-data-retention-zdr) |
| **Cohere**：有料のCohere SaaS Platform、専用配置・他社基盤への配置は別評価 | Trust CenterがGDPR対応とDPAの提供を説明 | 同所にCCPAの対応表示。ただし個別DPA本文の条項検証は未実施 | 学習停止設定、有料契約、DPAの取得・締結が条件。Client License Agreement第6節の適用契約では、DPA未締結で個人情報を処理させない義務がある | 方針・締結条件確認。契約本文の追加確認が必要。[Trust Center](https://trustcenter.cohere.com/?format=html)、[企業向けデータ方針](https://cohere.com/enterprise-data-commitments)、[Client License Agreement](https://cohere.com/client-license-agreement) |

6社の契約内容は完全に同じではない。Cohereの証拠の不足は「非対応」を意味しない。一方、対応表示だけで他の6社と同じ条項があるとも判断しない。製品の商用契約と個人向け無料・有料契約、試用APIを混同しない。

## 学習不使用と保存・閲覧の区別

| 対象 | 確認できた条件 | 選定時に外せない確認 |
|---|---|---|
| OpenAI API | 明示的な共有を選ばない限り学習に使わない。不正利用監視の記録は原則最大30日だが延長例外あり。ZDRには事前承認が必要 | ZDRでも対象外機能の状態保存、画像・ファイル、Private Retention / Safety Retention等の例外を確認。「全データが一切残らない」と表現しない |
| Anthropic | 商用は原則学習不使用。一般FAQはAPIの標準保存を30日以内と説明する一方、API文書には通常の会話内容の非保存とCovered Modelsの30日保存を記載 | 両文書を一律の保存日数へ丸めず、利用モデル、ZDR契約、保存を伴う機能を特定。評価送信した会話等は学習利用と最大5年保存の対象になり得る |
| Azureの対象モデル | 許可・指示なしに基盤モデル学習へ利用しない。Microsoftが提供・監視し、当該方式の入力はOpenAI等のモデル開発元に提供しない | 会話・ファイル等の保存と不正利用監視、人による確認、Global / DataZone等の処理範囲を確認 |
| Amazon Bedrock | `none`は入力・出力の永続保存をしない設定。`default`等ではモデルの要件が関係する。`none`と非互換なモデルの呼出しは遮断 | 保存設定は地域別。`store=false`だけでは監視用保存を排除できない。顧客側で有効化する呼出記録や外部機能の保存も別途確認 |
| Google Cloudの対象生成AI | 許可・指示なしに学習しない。監視、検索・地図参照、会話状態等は別条件 | 一部Advanced AI機能ではZDRが不可能な場合がある。Google Search参照は最大3日、Google Maps参照は30日の保存を記載。機能を使わない場合へこの日数を広げない |
| Mistral AI | 学習停止とZDRは独立。有料の状態を保持しないAPI呼出しについてZDRを申請可能 | 会話、エージェント（複数の処理を実行するAI）、ファイル等はZDR対象外。評価送信時の入力・出力の利用を止める運用も必要 |
| Cohere SaaS Platform | 学習停止設定を提供。入力・出力の記録は原則30日で削除するが法令・契約・不正利用の例外あり。承認済みZDRもある | 学習停止は設定変更後のデータに適用。専用配置・他社基盤では入力・出力をCohereが受け取らないという説明を、通常のSaaSへ流用しない |

出典：[OpenAI API](https://developers.openai.com/api/docs/guides/your-data)、[Anthropic API](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)、[Anthropic保存FAQ](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)、[Anthropic学習・評価送信](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training)、[Azure](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy)、[Bedrock保存](https://docs.aws.amazon.com/bedrock/latest/userguide/data-retention.html)、[Google Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention)、[Mistral AI](https://help.mistral.ai/en/articles/347612-can-i-activate-zero-data-retention-zdr)、[Cohere](https://cohere.com/enterprise-data-commitments)。

**30日保存があることだけで違法とはならず、ZDRであることだけで適法にもならない。** 保存の目的・必要性・契約・本人への説明等を評価する。また、推論（回答生成）時に原文を処理すること自体は、ZDRでも生じる。

## 日本の個人情報保護法の調査へ移す方法

以下は公開法令解釈に基づく調査設計であり、上記7社の日本法適合を確定する評価ではない。

### 1. 同じ会社でも契約経路を分ける

OpenAI直契約とAzure OpenAI、Anthropic直契約とAmazon Bedrockでは、個人データの取扱いに責任を負う相手が異なる。さらに、クラウド上でモデル開発元が運営する提供方式もある。例えばAnthropicのAPI文書は、Google管理とAnthropic管理の提供方式、Amazon BedrockとClaude Platform on AWSを区別する。ブランド名から契約相手を推定せず、注文書・約款・製品仕様を対応付ける。[Anthropicの処理者の区別](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)、[Azureの対象範囲](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy)

### 2. 学習停止を入口にし、委託としての条件を確認する

個人情報保護委員会は、個人情報の入力が利用目的の必要な範囲内か、本人同意なく入力した個人データが回答生成以外の目的で取り扱われないか、学習に使われないか等を確認するよう注意喚起している。**学習不使用だけで委託と確定せず**、監視・評価・製品改善・人による閲覧等の目的と範囲、再委託、契約と実態を確認する。[生成AI注意喚起](https://www.ppc.go.jp/files/pdf/230602_alert_generative_AI_service.pdf)

安全管理、委託先の監督、漏えい等の報告、本人からの開示・訂正・利用停止等への対応も確認する。GDPR上のprocessorと日本法上の委託先は、用語を置き換えるだけで同じ判断になるものではない。[通則ガイドライン](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)

### 3. 国外への提供を、国内保存と別に判断する

外国にある第三者への提供については、本人同意、委員会が定める同等水準国、相当措置を継続して講ずる体制、法定の例外等のどの経路を用いるかを確認する。相当措置の体制を根拠にする場合は、継続実施の確保と本人への情報提供等も必要になる。SCCがあることは契約確認の材料になるが、日本法の要件を自動充足しない。[外国にある第三者への提供編](https://www.ppc.go.jp/personalinfo/legal/guidelines_offshore/)

国内の保存場所だけでは判断できない。委員会Q12-4は、外国事業者が取り扱う場合、国内サーバでも原則として外国にある第三者への提供に当たり得ると説明し、日本国内での取扱い等についての例外も示す。契約法人・取扱いの実態・国外からのアクセス・再委託を確認する。[Q12-4](https://www.ppc.go.jp/all_faq_index/faq1-q12-4/)

また、クラウド事業者が個人データを「取り扱わない」場合のQ7-53を、原文を外部AIに処理させる利用へ確認なしに適用しない。人が読まないこと、学習しないこと、保存しないことは、それぞれ別の条件である。[Q7-53](https://www.ppc.go.jp/all_faq_index/faq1-q7-53/)

### 4. 要配慮個人情報を別に審査する

病歴など、日本法の要配慮個人情報の取得・提供等は個別に確認する。Anthropicの公開DPA Schedule 1とMistral AIのDPA Exhibit 1には、GDPRの特別な種類の個人データを「None」とする記載がある。これだけで全サービスでの取扱禁止を断定しないが、標準DPAだけで病歴等まで受託可能と判断せず、対象契約・用途制限・追加合意を確認する。日本法の要配慮個人情報とGDPRの特別な種類の個人データの範囲も同一ではない。[Anthropic DPA](https://www.anthropic.com/legal/data-processing-addendum)、[Mistral AI DPA](https://legal.mistral.ai/terms/data-processing-addendum/)、[通則ガイドライン](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)

## 次回調査用の確認票

各社につき「会社名」だけでなく、次の1行を一つの候補として管理する。

`契約法人 × 製品 × 契約版 × モデル・版 × 機能 × 処理地域 × 保存・学習設定`

| 確認項目 | 取得する公開証拠／契約確認事項 | 日本法上の主な検討 |
|---|---|---|
| 入力データと目的 | 氏名、問い合わせ履歴、病歴等の種類と、要約・検索・回答等の目的 | 利用目的の範囲、必要最小化、要配慮個人情報 |
| 契約・責任主体 | 注文書に適用される法人、商用約款、DPA、製品特約 | 委託・第三者提供、責任分担 |
| 学習・二次利用 | 既定値、停止設定、評価送信、不正利用監視、匿名化後の利用 | 委託目的内の取扱いか、追加の根拠が必要か |
| 保存と削除 | 入出力、添付、会話、検索用派生データ、監視記録、予備の複製の期限と例外 | 不要後の消去、本人の利用停止等への対応、安全管理 |
| 人による閲覧 | 支援担当、監視担当、権限、アクセス元の国、操作記録 | 安全管理、監督、外国での取扱い |
| 再委託 | 再委託先一覧、所在地、業務内容、追加通知、異議申立て | 再委託先を含む監督と移転経路 |
| 国外への提供 | 受領主体と所在国、移転根拠、継続確認の方法 | 第28条の同意・例外・相当措置と情報提供 |
| 権利対応 | 個人単位の検索、開示、訂正、削除等への支援と期限 | 自社の本人対応を履行できるか |
| 事故・監査 | 顧客への事故通知、調査協力、監査権、責任制限 | 委員会報告・本人通知・委託先監督を行えるか |
| 機能追加 | 外部検索、他サービス接続、処理を実行するAIの送信先 | 元の契約・移転判断に含まれるか |
| 業種・契約要件 | 医療・金融・行政の規律、顧客から預かった情報の契約 | 個人情報保護法に加わる制約 |

この表は、[通則ガイドライン](https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/)、[国外提供ガイドライン](https://www.ppc.go.jp/personalinfo/legal/guidelines_offshore/)、[生成AI注意喚起](https://www.ppc.go.jp/files/pdf/230602_alert_generative_AI_service.pdf)と各社の条件を照合して作成した調査案。

## 調査の優先順と検索の引継ぎ

以下の順番は、本調査の提案であり、適法性や安全性の順位ではない。

1. **既に利用する企業基盤がある場合：Microsoft、AWS、Google Cloud。** 既存契約・権限管理との対応を確認しやすい候補として、対象モデル・地域・保存条件を固定して調べる。
2. **モデル提供元と直接契約したい場合：OpenAI、Anthropic。** 商用契約とAPIを入口に、保存機能・監視・国外提供の条件を確認する。
3. **提供形態の比較を広げる場合：Mistral AI、Cohere。** 学習停止、個人情報を扱える契約、ZDR、専用配置等を具体化する。CohereはまずDPA本文の取得・確認が必要。

日本法に向けた追加検索では、次の組合せを使う。社名を入れ替え、検索結果の要約ではなく公開原本を読む。

| 目的 | 検索語の例 |
|---|---|
| 日本法への契約対応 | `社名 個人情報保護法 委託 外国 第三者 契約` / `社名 APPI data processing addendum` |
| 処理者の役割 | `社名 data processing addendum controller processor CCPA service provider` |
| 学習と評価送信 | `製品名 training opt out feedback commercial` |
| 保存例外 | `製品名 zero data retention abuse monitoring files conversations` |
| 国外移転・再委託 | `社名 subprocessors processing locations international transfers` |
| 国内候補の拡張 | `生成AI 法人 個人情報保護法 学習利用 再委託 データ保存`。国内企業であることだけで適合判定しない |

この7社は候補の存在を確かめるための標本であり、世界のAI事業者を網羅した一覧ではない。国内事業者、業務特化AI、画像・音声専業、公開モデルを自社で運用する方式の比較は次段階とする。

## 証拠の状態と残る限界

- 契約・製品仕様・当局資料の公開本文を確認した。非公開の監査報告、ログイン後の管理画面、個別契約や営業回答は使用していない。
- Microsoft DPAは公式の2026年11月版DOCXから文章を抽出し、CCPA節とGDPR関係節を確認した。文書の見た目の検証を行った成果物ではない。
- Anthropicには保存説明の対象範囲が異なる公開文書が併存する。FAQの30日とAPI文書の非保存記載から、全モデル・全契約に共通する既定値を断定していない。
- Cohereは公開の対応表示・企業向け方針・Client License Agreementを確認したが、個別DPAの監査・通知・移転等の条項は未確認。
- 各社の全処理の適法性、学習元データの適法性、過去・現在の行政処分や訴訟の網羅確認、実際の削除・地域制限の実機試験は含まない。各社の公表・契約上の約束と実証結果を区別する。
- 日本法の最終審査では、利用開始時に施行されている法令・ガイドラインを再確認する。本資料は改正法の未施行規定を先取りして適用するものではない。

再利用用：[7社の比較CSV](ai_vendor_ccpa_gdpr_comparison_20261109.csv)、[出典確認台帳](ai_vendor_ccpa_gdpr_sources_20261109.json)。

関連調査：[国内保存と処理地域](../technology/enterprise_llm_japan_residency_20261014.md)、[個人情報の定義と分類例](../technology/pii_definitions_and_classification_examples_20261008.md)。過去資料の製品条件は当時の確認結果であり、今回の条件へ自動的に引き継がない。
