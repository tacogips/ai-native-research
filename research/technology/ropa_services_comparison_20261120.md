# 個人データの処理活動記録（RoPA）サービス比較

調査日 2026年11月20日。対象は OneTrust、TrustArc、Securiti、BigID、Collibra、DataCail、Transcend、Osano、Ketch。DataCail はこの表記で提供元を特定できなかった。類似名で同分野の **DataGrail** を参考枠に掲載し、指定名との同一性は保留した。

## 要約

- **処理活動を自社システムから同期するなら OneTrust、TrustArc、Transcend。** OneTrust は処理活動、資産、委託先、法人に対する専用の台帳APIに加え、外部IDによる作成・更新、関係・階層・状態の操作を公開している。TrustArc は外部IDによる処理活動の同期と更新通知の仕様が具体的。Transcend は台帳を読み書きする GraphQL と構成を同期できる CLI を公開し、管理画面では帳票の版管理、再同期、PDF・CSV出力まで手順が明示されている。
- **検査で見つけた実データと処理活動をつなぐなら BigID と Securiti。** BigID は所在・分類・担当・移転先を処理活動にひも付け、承認と版履歴まで製品資料に記載する。Securiti は保管先の検査と担当者への確認を組み合わせる。専用台帳のAPIを使う場合は、公開仕様で確認できる操作を個別に見極める必要がある。
- **業務担当者と委託先の確認を回すなら TrustArc も候補。** 再確認の予定、通知、評価、委託先・システムの同期を同じ業務記録に結び付ける。Ketch は検出したシステムと契約等からの情報抽出、Osano は評価・本人からの請求との共用、Collibra は企業のデータ資産台帳に処理活動を組み込む用途に向く。
- **公開APIの豊富さと提出用帳票の自動化は別に評価した。** OneTrust、TrustArc、Transcend は台帳連携の公開根拠が厚い。人が画面で提出用帳票を出力できることや、別機能でAPIが豊富なことから、帳票を外部から生成・ダウンロードできるとは判断していない。

## 記録の対象と比較方法

RoPA（Records of Processing Activities）は、EU一般データ保護規則（GDPR）第30条で扱う処理活動の記録。管理者側の記録では、処理の目的、本人・個人データ・受領者の区分、該当する域外移転、可能な場合の消去期限と安全管理措置の概要などを扱う。処理者側では、管理者ごとに実施する処理の区分などを記録する。製品比較では、保管場所の一覧・機密情報の検知結果・Cookie同意の履歴を、組織の業務を単位とする処理活動記録から区別した。[GDPR第30条の原文](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)

APIは他のシステムから機能を呼び出すための接点。点数は付けず、**専用台帳に対する読み書きと関係操作、汎用の資産台帳や検査操作、提出用帳票の生成・取得**を比較した。公開仕様を読んで判定し、契約環境での実行、日本語帳票の表示、契約範囲、各項目の正確性は実測していない。

## 機能比較

| 製品 | 台帳への取り込み・更新 | 人の確認・履歴 | RoPAの出力 | 主な公開資料 |
|---|---|---|---|---|
| **OneTrust Data Mapping Automation** | 処理活動、資産、委託先、法人を関連付ける。既存台帳、評価回答、検出データを使って情報を集める | 評価の依頼と承認を使える。処理活動・資産などの階層と関連を管理 | 専用RoPA報告。British Councilが管理者・処理者の両方の報告を生成したと公表 | [Privacy Automation](https://www.onetrust.com/solutions/privacy-automation/) · [実際の帳票利用](https://www.onetrust.com/customers/british-council/) |
| **TrustArc Data Mapping & Risk Manager** | 業務プロセス・委託先・システムと移転を関連付け、既存資料や説明文から記録を補う。ServiceNow、Salesforce等との同期を案内 | 再確認の予定、通知、評価手順。委託先・域外移転のリスクも関連付ける | 管理者側と処理者側それぞれの専用レポート、複数記録の出力、CSV・Excelによる出力の案内あり | [製品仕様](https://trustarc.com/products/privacy-data-governance/data-mapping-risk-manager/) · [帳票ガイド](https://trustarchelp.zendesk.com/hc/en-us/sections/4402671377683-Generating-Reports-Data-Mapping-Risk-Manager) |
| **Securiti Data Mapping Automation** | 保管先で検出した個人データと、担当者への質問で得た業務情報を結び付け、データの流れを可視化 | 評価を使った確認。承認状態と帳票の版履歴の取得範囲は未確認 | RoPA報告の自動化を明示 | [製品仕様](https://securiti.ai/products/data-mapping/) |
| **BigID RoPA Mapping** | 検査で発見したデータ区分、システム、担当者、委託先、移転先と、利用目的・法的根拠を結び付ける | 担当への確認依頼、承認履歴、版管理、リスク・証拠への関連付けを明示 | 監査用のRoPA要約を出力。出力形式と管理者・処理者別の様式は未確認 | [RoPA Mapping](https://bigid.com/ropa-mapping-app/) |
| **Collibra Data Privacy / Data Catalog** | 標準の Process Register（処理台帳）と Business Process（業務プロセス資産型）を使い、活動と入出力データセットを関連付ける | 担当者への入力依頼、規制別の入力用紙、時刻と変更者を含む変更履歴。帳票の独立した版管理は未確認 | 公式にRoPAを扱う資料がある。現行標準構成の規制帳票、一括出力の専用操作・設定工数は未確認 | [Data Privacy](https://www.collibra.com/products/data-privacy) · [業務プロセス資産型](https://productresources.collibra.com/docs/collibra/latest/Content/DataPrivacy/ProcessRegister/co_bus-proc-asset-type.htm) · [処理台帳](https://productresources.collibra.com/docs/collibra/latest/Content/DataPrivacy/ProcessRegister/ref_process-reg-domain-page.htm) · [規制別入力用紙](https://productresources.collibra.com/docs/collibra/latest/Content/DataPrivacy/Workflows/Options/co_regulation-specific-forms.htm) |
| **DataCail** | 提供元を未特定 | 未確認 | 未確認 | 類似名のDataGrailは下の参考枠 |
| **Transcend Data Inventory / RoPA** | 台帳にシステム、データ項目、委託先、目的、処理活動を集約。接続先の自動探索・分類と承認済み評価回答の同期 | 帳票を再同期しつつ手修正を保持できる。版の保存・復元、表紙の調整が可能 | **PDF・CSV**。処理活動の選択、帳票の版管理、管理者・処理者情報等の表紙項目を操作ガイドで確認 | [RoPA操作ガイド](https://docs.transcend.io/docs/data-inventory/data-reports/quickstart) · [評価回答の同期](https://docs.transcend.io/docs/assessments/data-inventory-integration) |
| **Osano Data Mapping** | シングルサインオン（SSO）からのシステム発見、接続先での分類、資産の担当者への評価を組み合わせる | 役割分担、評価による情報の収集、委託先評価や本人からの請求に連携。独立した帳票版の管理は未確認 | 同じ台帳からRoPAを自動生成すると明示。形式・版の保持は未確認 | [製品仕様](https://www.osano.com/products/data-mapping) |
| **Ketch Data Mapping** | システム、データ区分、処理活動を継続探索し、契約等から情報を抽出すると説明。評価にも同じ台帳を利用 | データ保護影響評価（DPIA）や移転影響評価への情報補完を案内。RoPA自体の承認・版復元は未確認 | 生きた台帳からのRoPA・監査証拠出力を明示。ファイル形式・定時配信は未確認 | [製品仕様](https://www.ketch.com/platform/data-mapping) |
| **参考 DataGrail Live Data Map / ROPA** | 検出したシステムや既存の台帳から入力を補い、処理活動ごとにRoPAを作成 | テンプレート共有、外部協力者への依頼、未確認の警告、変更前後と変更者の記録、定期スナップショットを明示 | 全処理活動と変更履歴をCSV出力。過去版の復元は未確認 | [RoPA製品仕様](https://www.datagrail.io/solutions/record-of-processing-activities/) · [RoPA管理ガイド](https://docs.datagrail.io/docs/ldm/ropa-management/) |

## APIの豊富さと対象範囲

評価は**直接操作を詳しく確認**、**汎用基盤の操作は豊富**、**関連機能または連携説明を確認**、**未確認**の順に記載する。同じ製品でも処理活動、基礎データ、帳票では評価が異なる。Osanoのように資産に処理目的を登録できる場合も、業務を単位とする処理活動を独立して作成・更新できるかを分けて確認した。「未確認」は今回読めた公開資料の範囲を表す。

| 製品 | 台帳・処理活動に対するAPI | 周辺API・実装方式 | 提出用RoPA帳票のAPI |
|---|---|---|---|
| **OneTrust** | **直接操作を詳しく確認。** RESTで一覧（ページ分割・条件抽出）、ID・外部IDの参照、作成、更新、外部IDによる作成と更新の兼用、削除、複製、状態更新。処理活動の親子、台帳間の関連、データ区分等も操作。作成先は `POST /api/inventory/v2/inventories/{schemaName}`。型に `processing-activities`、`vendors`、`assets`、`entities` | OAuth 2.0（権限を委任する認証方式）とアクセス範囲、利用上限の資料を公開 | 帳票専用の生成・取得APIは未確認。[台帳API一覧](https://developer.onetrust.com/onetrust/reference/privacy-automation-data-mapping-automation/llms.txt) · [処理活動の作成仕様](https://developer.onetrust.com/onetrust/reference/createinventoryusingpost) |
| **TrustArc** | **直接操作を詳しく確認。** OAuth 2.0で業務プロセス、ITシステム、関連会社、第三者の参照・登録・更新・削除。業務プロセスは全件・指定日以降の変更を取得し、内部／外部IDで照合。外部IDでの作成・更新の兼用、システムの関連付け・置換・解除を公開 | Amazon SNS（通知配信サービス）からのHTTPS通知をサポート。登録はTrustArc担当経由。通知の内部／外部IDを使いAPIで最新版を取得する方式 | 管理者・処理者の帳票出力は画面で確認。専用APIは未確認。[専用API索引](https://trustarchelp.zendesk.com/hc/en-us/sections/41725263316243-Data-Mapping-Risk-Manager-API) · [業務プロセス](https://trustarchelp.zendesk.com/hc/en-us/sections/49881866581779-Business-Process) · [更新通知](https://trustarchelp.zendesk.com/hc/en-us/articles/50180844978323-Update-Notifications) |
| **Transcend** | **直接操作を詳しく確認。** GraphQL（必要な項目を指定する問い合わせ方式）とCLI（コマンド操作）で Data Inventory の読み書き、YAML形式の台帳の取り込み・書き出し。システム、データ項目・属性の操作を文書・例で確認。処理活動の全項目、関係、削除は利用する操作と版ごとの確認が必要 | REST・OpenAPI・Webhook（事象の外部通知）の公開仕様は本人請求、同意等にも充実。台帳GraphQLとRESTの役割を分ける | 画面のPDF・CSV出力を確認。専用APIは未確認。[台帳API](https://docs.transcend.io/docs/data-inventory/inventory-apis) · [書き込み例](https://docs.transcend.io/docs/data-inventory/inventory-apis/writing-data-using-api) · [REST](https://docs.transcend.io/docs/api-reference) |
| **Collibra** | **汎用基盤の操作は豊富。** RESTで資産・属性・関連を操作し、Import APIでJSON・CSVの一括登録・更新、Output Moduleで検索・出力、Knowledge Graph APIで関連を取得。採用構成の処理活動型・関係・必須項目を先に確定する | 手順設計機能とAPIを組み合わせて承認等を構成 | 汎用出力は可能。専用の提出帳票APIは未確認。[APIの種類と仕様](https://developer.collibra.com/api) |
| **BigID** | **汎用基盤の操作は豊富。** データ源の作成、検査起動、資産台帳の検索・出力、違反等の案件APIを公開。RoPAの処理活動・承認を直接更新する完全な仕様は未確認 | 開発者向け接続機構、本人請求ポータル、拡張アプリ。台帳候補の発見・集約との接続に向く | 製品画面の要約出力を確認。専用APIは未確認。[開発者資料](https://developer.bigid.com/) · [既存のAPI精査](bigid_dlp_api_constraints_20261111.md) |
| **Securiti** | **関連連携を確認。** データ源の探索・分類、RoPAへの連携を製品資料で確認。処理活動の公開読み書き仕様は未確認 | 本人請求向けにアクセス・削除・訂正のプログラム連携を案内。処理活動の外部操作範囲は別途確認 | 専用APIは未確認。[製品資料](https://securiti.ai/products/data-mapping/) · [本人請求の開発者資料](https://securiti.ai/privacy-center/developers/) |
| **Osano** | **資産台帳の操作を確認。** RESTの `/v1/data-discovery/data-stores` でデータストアの一覧・作成、ID指定で取得・更新・無効化。各フィールドの一覧・一括更新・削除、コネクタ・ラベルの一覧も公開。所有者・国・処理目的を更新できる。独立した処理活動レコードの操作は未確認 | API仕様には本人請求・同意管理も含む | 専用APIは未確認。[REST参照](https://developers.osano.com/customer-rest-api) · [OpenAPI定義](https://developers.osano.com/redocusaurus/customer-rest-api.yaml) |
| **Ketch** | **関連連携を確認。** 開発者向けAPI索引は公開。調査時、索引からの詳細参照先は認証画面へ遷移。台帳・処理活動を直接読み書きする公開仕様は未確認 | 同意や本人請求の信号を外部へ転送する公開コード、同意の開発用部品とコマンド操作を確認 | 専用APIは未確認。[開発者向け索引](https://docs.ketch.com/) · [公開コード](https://github.com/ketch-com) · [製品仕様](https://www.ketch.com/platform/data-mapping) |
| **DataCail** | 製品同定が先 | 未確認 | 未確認 |
| **参考 DataGrail** | **関連APIを確認。** 専用の処理活動の作成・更新を裏付ける公開仕様は未確認 | 公開 v2 APIには評価、本人請求、オプトアウト、Webhook、監査ログなどの参照先がある | 専用APIは未確認。[v2 API仕様](https://docs.datagrail.io/api/v2/) · [Live Data Map](https://docs.datagrail.io/docs/ldm/ldm-overview/) |

## 海外の導入事例

「RoPA」は顧客の処理活動記録の運用が公表されたケース。「台帳」は資産目録・データマッピングの利用が公表されたケース。「関連機能」は同意、本人請求、評価などの導入。導入効果は事例の公表主体による説明に基づく。

| 製品 | 組織・地域 | 公開資料で確認した利用 |
|---|---|---|
| **OneTrust** | **British Council（英国）**、**Alfred Kärcher（ドイツ）** | **RoPA。** British Councilでは管理者・処理者として第30条の帳票を生成し、影響評価を台帳に関連付ける。KärcherではExcelベースの処理活動記録から移行し、担当部署に定期的に確認を送り、データ保護責任者が承認する。[British Council](https://www.onetrust.com/customers/british-council/) · [Kärcher](https://www.onetrust.com/customers/alfred-karcher/) |
| **TrustArc** | **HealthLink Dimensions（米国）**、**匿名の消費財企業** | **関連機能・台帳。** HealthLinkは本人請求の自動化とCookie同意。匿名企業は Data Inventory Hub を使い台帳を集約。両事例ともRoPA帳票の利用は未確認。[HealthLink](https://trustarc.com/resource/elevating-healthcare-privacy-healthlink-dimensions-journey-with-trustarc/) · [匿名事例](https://trustarc.com/resource/fortune-500-consumer-products-case-study/) |
| **Securiti** | **QuinStreet（米国）**、**匿名の国際金融サービス事業者** | **関連機能。** QuinStreetはカリフォルニア州の法令対応とデータマッピングの課題を事例動画で説明。匿名企業は個人情報保護業務からデータ・AIの統制に展開。RoPA帳票の利用は未確認。[QuinStreet](https://securiti.ai/videos/quinstreet-case-study/) · [匿名事例](https://securiti.ai/case-studies/privacy-to-ai-readiness-in-18-months/) |
| **BigID** | **Telenor（ノルウェー）** | **台帳・関連機能。** データの探索、本人の権利行使への対応と削除。RoPA帳票の利用は未確認。[事例](https://home.bigid.com/customer-story-telenor-and-bigid) · [公式概要](https://bigid.com/why-bigid/) |
| **Collibra** | **Nationwide Building Society（英国）**、**ASN Bank（オランダ）** | **台帳。** Nationwideは資産と責任者の一覧、規制報告。ASN BankはGDPR対応を背景にデータの所在と処理経路を把握。第30条の帳票利用は未確認。[Nationwide](https://www.collibra.com/customer-stories/nationwide-building-society) · [ASN Bank](https://www.collibra.com/customer-stories/asn-bank) |
| **Transcend** | **GoCardless（英国）**、**Jasper（米国）** | **台帳。** GoCardlessは Data Mapping を評価・同意・本人請求と併用。Jasperも Data Mapping を使用。両社ともRoPA帳票の利用は未確認。[GoCardless](https://transcend.io/case-studies/gocardless-transcend-privacy-migration) · [Jasper](https://transcend.io/case-studies/jasper-transcend-customer-story) |
| **Osano** | **Fender（米国）** | **関連機能。** ウェブサイトのCookie同意を管理。RoPAの利用は未確認。[事例](https://www.osano.com/customers/fender) |
| **Ketch** | **Spreedly（米国）**、**Good Smile Company（日本企業グループの米国向け事業）** | Spreedlyは**関連機能**の同意・利用者設定を先行展開。事例本文でデータマッピングは次段階。Good Smile Companyは**台帳・関連機能**で、データの探索・分類と処理内容の継続的な文書化を説明。第30条帳票は未確認。[Spreedly](https://www.ketch.com/blog/posts/spreedly-payments-case-study) · [Good Smile Company](https://www.ketch.com/blog/posts/good-smile-ccpa-cpra-compliance) |
| **DataCail** | 未特定 | 指定表記で導入を確認できなかった。 |
| **参考 DataGrail** | **Branch（米国）**、**LastPass（米国）**、**MoonPay（米国）**、**Poppulo（アイルランド発）** | **RoPA。** Branchは300を超えるシステムを含むRoPAを維持。LastPassとMoonPayは Live Data Map で関連システムを洗い出し、RoPAの処理活動と関連付ける。Poppuloは処理活動の記録を確認し、高リスクのシステムを関連付ける。提出用帳票の外部API利用は未確認。[Branch](https://www.datagrail.io/customers/branch-spotlight/) · [LastPass](https://www.datagrail.io/customers/lastpass-spotlight/) · [MoonPay](https://www.datagrail.io/customers/moonpay-spotlight/) · [Poppulo](https://www.datagrail.io/customers/poppulo-spotlight/) |

OneTrustのScania（スウェーデン）事例では、担当者が処理活動情報の約70〜80%を地域間で再利用できたと説明している。日本の個人情報保護法も対象として挙がるが、日本法人単独の導入範囲は未公表。[Scania](https://www.onetrust.com/customers/scania/)

## 国内の導入事例と提供状況

国内の実名台帳事例は、**デンソー × OneTrust**。NRIがデンソー法務部に行った公開インタビューでは、個人情報管理台帳と年次点検報告を一体化し、現場がウェブで回答し、法務部が進捗と回答を確認できるようにしたと説明している。欧州グループで先に製品を採用した経緯も出ている。国内事例でGDPR第30条専用帳票の出力を使ったかは未公表。[NRIのデンソー事例](https://aslead.nri.co.jp/ownedmedia/case/post-1787/)

| 製品 | 国内で確認できた範囲 |
|---|---|
| **OneTrust** | デンソーの台帳事例に加え、NRIが個人情報保護委員会の推奨38項目に対応したテンプレート、依頼・確認・修正と版管理を公表。IIJにも国内のデータマッピング提供がある。ライオン・エポック社のIIJ事例はCookie同意での導入。[NRIの発表](https://www.nri.com/jp/news/info/20221020_1.html) · [IIJのデータマッピング](https://portal.bizrisk.iij.jp/data_mapping) · [ライオン](https://www.iij.ad.jp/svcsol/case/lion.html) · [エポック社](https://www.iij.ad.jp/svcsol/case/epoch.html) |
| **BigID** | NRIセキュアが国内での導入・運用支援実績を公表。顧客名とRoPA用途は未公表。SCSKも国内で取り扱う。[NRIセキュア](https://www.nri-secure.co.jp/news/2026/0226) · [SCSK](https://www.scsk.jp/product/common/bigid/index.html) |
| **Collibra** | NRIは国内金融機関向けの導入支援開始を公表。Takedaの企業データ資産台帳事例は対象地域が資料本文に明示されていない。Daiichi Sankyo EuropeとToyota Motor Europeは日系グループの欧州事例。いずれもRoPA用途は未確認。[NRI](https://www.nri.com/jp/news/newsrelease/20191107_1.html) · [Takeda](https://www.collibra.com/resources/deloitte-enterprise-data-catalog-at-takeda) · [Daiichi Sankyo Europe](https://www.collibra.com/customer-stories/daiichi-sankyo-europe) · [Toyota Motor Europe](https://www.collibra.com/customer-stories/toyota-motor-europe) |
| **TrustArc** | アンダーワークスが国内支援を案内するのはCookie同意製品。国内の実名台帳事例は未確認。[国内提供資料](https://www.underworks.co.jp/technology/trustarc) |
| **Securiti** | 日本の個人情報保護法向けの製品説明を公開。国内実名の台帳導入は未確認。[製品説明](https://securiti.ai/solutions/japan-appi/) |
| **Ketch** | Good Smile Company事例は米国向けの法令対応で、国内運用の範囲は未公表。[事例](https://www.ketch.com/blog/posts/good-smile-ccpa-cpra-compliance) |
| **Transcend、Osano、参考 DataGrail** | 国内組織の実名台帳・RoPA事例を今回の公開資料から確認できなかった。 |
| **DataCail** | 指定表記の提供元を確認できなかった。 |

国内用の管理台帳は、個人情報保護委員会が公表するデータマッピングの手引きを項目設計の参考にできる。日本での取扱状況の確認に用いる記録と、GDPR第30条の管理者・処理者向けの帳票は、必要項目と適用範囲をそれぞれ確認する。[個人情報保護委員会のツールキット](https://www.ppc.go.jp/files/pdf/data-mapping_tool-kit.pdf) · [GDPR原文](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)

## 要件別の候補

| 優先する要件 | 候補と確認点 |
|---|---|
| システムや委託先の台帳から処理活動を双方向同期する | **OneTrust、TrustArc、Transcend**。外部IDの再送、処理活動と複数の資産・委託先の関連付け、手修正がある場合の更新、削除時の参照整合性を試す。 |
| 現場の確認と年次点検を国内で回す | **OneTrust**は国内実名事例あり。**TrustArc**は期限付きの再確認、評価、委託先管理が候補。国内テンプレート・支援範囲を地域別に確認する。 |
| データベースや保管先の検知と処理記録を照合する | **BigID、Securiti、Transcend**。検査で得られる所在・種類と、担当者が確定する目的・利用根拠・保持期間の同期経路を確認する。 |
| 既存の全社データ資産台帳に組み込む | **Collibra**。Business Process資産と既存のデータ資産・所有者・関連を結び、必要な帳票・承認手順を設計する。 |
| 規制提出用の帳票を完全自動化する | **台帳の読み書き、帳票生成、版の確定、ファイル取得の4操作**を個別に確認する。利用できるAPIが台帳データに限られる場合は、帳票生成を自社側に置く構成もあり得る。 |

調査には提供元の製品・開発文書、顧客や導入支援事業者の公開資料、国内外の公開検索を使用した。導入事例は実名と対象機能を確認できる範囲で記載した。管理画面への接続、会員限定文書、試験アカウントでの実行は調査範囲外。APIの契約・権限、監査用の過去版取得、国内での出力の言語と書式は導入時の確認事項として残る。
