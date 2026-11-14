# 個人情報を端末へ保存させない遠隔利用環境：サービスと研究運用

調査日：2026-10-15。公開された提供者・運営機関の一次資料のみ。実サービス契約、管理画面での設定、端末上の通信・削除試験は行っていない。ここでいうPIIは個人を識別し得る情報の総称で、法令別の定義を統一するものではない。原本・抽出本文・取得失敗は[資料台帳](online_pii_remote_sources_20261015.json)に区別して保存した。

## 結論：原ファイルを持たせない仕組みはあるが、OTPだけでは実現しない

**中央で処理し、原ファイルの端末保存・コピー・印刷を止める方式は既に実用化されている。** ただし「端末に原ファイルを保存しない」「端末が原文の文字列を処理しない」「利用者に個人単位の原データを見せない」は別の要件である。画面を見せる環境は画面上の内容を利用者へ開示する。画像からの文字認識、撮影、手書きまで完全に消せるという保証はしない。

OTP（使い捨て認証コード）は入口で利用者を確認する認証の一方式であり、ログイン後のコピー禁止ではない。例えばAWSは本人確認をIdP（認証を提供する基盤）へ任せる一方、コピー・ファイル転送・印刷を別設定にしている。NHS SDEも二要素認証と成果物の持出審査を別に運用する。[AW04][AW06][NH02]

## 1. 方式の違い

| 方式 | 中央で行うこと | 端末へ届くもの | 要件への適合と注意 |
|---|---|---|---|
| 遠隔ブラウザの画素転送 | Webサイトの読込・実行・描画 | 画面の画像と操作の通信 | 原HTMLやDOM（ページ構造）の非送信を狙える。画面に表示した個人情報は見える。AWS Secure Browserはこの方式。[AW07] |
| 遠隔ブラウザの描画命令転送 | Web実行を遠隔に置き描画を分離 | 図形や文字の描画命令等 | 動画・画素だけとは異なる。CloudflareのNVR（ネットワーク経由のベクトル描画）はこの方式で、端末への原ファイル非配布と、端末への可視内容の非到達を混同しない。[CF04][CF05] |
| VDI（中央の仮想デスクトップ） | OS、アプリ、分析、原データ処理 | 遠隔画面・入力と、許可された転送経路 | ファイル共有・クリップボード・プリンタ・USB等の転送機能があるため、各経路の制限が必要。AVD/W365が代表。[MS03][MS04][MS06] |
| 管理された企業用ブラウザ | 端末ブラウザでの操作に企業規則を適用 | 通常のWeb処理に必要な内容も端末で扱う | Islandは操作制限に近いが、遠隔画素転送や「端末で平文を扱わない」と同一でない。暗号化した端末内保存という別機能もある。[IS01][IS02] |
| 安全な分析環境・コードをデータへ送る方式 | 中央のデータを分析し、出力を審査 | 認可された画面、審査後の結果。OpenSAFELYでは研究者は集計結果だけを見る | 原データを見せる一般VDIより狭い権限を設計できる。中央で複製を管理する方式と、元のデータ管理者の環境へ処理を送る分散方式がある。[ON01][OS01][OS02][OS05] |

「完全オンライン」は原ファイルを端末に配らないという運用目標として定義すると評価しやすい。画面データや一時的な表示処理まで一切端末へ届かないという意味では、閲覧自体が成立しない。

## 2. 企業利用向けの比較

### AWS WorkSpaces Secure Browser：画素転送だが新規受付の停止予定に注意

AWSは遠隔のChromeを実行し、HTML・DOMを端末へ送らずWeb内容を画面として転送する説明をしている。ただし公式の一般説明にある機密データの非送信という表現は、画面に見える内容や許可したファイル転送まで無かったことにする保証ではない。[AW07]

`create-user-settings` は `copy-allowed`、`paste-allowed`、`download-allowed`、`upload-allowed`、`print-allowed` をそれぞれ `Enabled` / `Disabled` で指定する。APIで指定が必須という事実から、管理画面の既定がすべて禁止とは推定しない。ツールバーのクリップボード・ファイル転送にも方向別の操作制御がある。URL許可/拒否やVPC等の接続制御は、中央のブラウザから外部サービスへ送る経路にも必要。[AW03][AW04][AW06]

**2026-10-29から新規顧客受付を停止予定。既存顧客は継続利用できる。** AWSは移行候補として、WorkSpaces Applicationsの自社管理Chromeで同種の画素転送を実現する方式を説明する。代替のすべての制御・運用負担が同じとまでは検証していない。[AW02]

今回のSecure Browser公開資料から、一般的な端末OSの画面撮影を必ず禁止する機能は確認できなかった。製品名が近いWorkSpaces Personalの機能を移して記載しない。

### Azure Virtual Desktop / Windows 365：転送制御と画面保護の対応条件を分ける

AVDの新規ホストプールでは2025年7月にコピー、ドライブ、低水準USB、プリンタの転送を既定無効にする変更が案内された。Windows 365も新規作成・再作成したCloud PCについてコピー・印刷の既定無効が説明される。**既存環境の自動変更を意味しない。** OS自体では禁止されず、ホストプール、Intune、Group Policy等の制限のうち厳しいものが適用される。[MS03][MS04][MS05][MS06]

同一提供者の一般的なRDP設定ページには許可値の既定表が残るため、今回の既定値は変更履歴と各転送の専用ページを優先して読んだ。導入時には既存の設定を実際に取得して確定する。[MS08]

画面キャプチャ保護は、対応するOS機能やAPIによる撮影を遮断する別機能。中央ホストでの設定は「端末側のみ」または「端末と中央ホスト側」を選べる。Windows/macOSの対応アプリに加え、2026年の資料ではiOS/AndroidやWindows上のWeb接続も、対応するIntune MAM（アプリ単位の管理）と条件付きアクセスの適用下で許可される。WebはEdge for Businessの保護済み業務プロファイル等が条件で、任意ブラウザ全般の対応ではない。このWeb構成は個人のWindows端末と別組織が管理するWindows端末が対象で、別組織管理はEdge 147以降等が条件。保護方針を配る同じテナント（組織の管理単位）が管理する端末は対象外で、条件付きアクセスが適用されるとブラウザ接続できない。該当端末では、中央ホストに画面保護を設定してネイティブWindows Appから接続する方法が案内される。設定の割当だけでは反映確認にならず、新規接続と実際の撮影試験が必要。[MS01]

透かしのQRコードは撮影元セッションを追跡する抑止策であり、写真撮影の阻止ではない。AVD経由でなくホストへ直接RDP接続すると透かしが適用されないという例外もある。[MS02]

さらに**Display Protectionは試験提供**で、表示ストリームを端末の保護された描画経路で復号する別機能。対応は物理Windows 11上のWindows Appに限られ、Web・macOS等へは広げない。ハードウェア保護の要求やHDCP（表示機器間の保護）によって接続条件が変わる。[MS07]

### Cloudflare Browser Isolation：既定許可と中央Web間の移動が重要

NVRによる描画命令転送で、2026年4月にCanvasの描画命令転送も案内された。既定で全通信が隔離されるわけではなく、GatewayのHTTP規則にIsolateを追加する必要がある。[CF03][CF04][CF05]

隔離したページでも、コピー、貼付、端末へのダウンロード、アップロード、印刷は**既定許可**。ダウンロードは「遠隔ブラウザで閲覧のみ」、コピー/貼付は「遠隔ブラウザ内のみ」に制限できる。ただし端末へのダウンロードを禁止しても、遠隔環境内へのダウンロードは止まらない。端末からのアップロード禁止だけでは、クラウドのファイル管理や別の隔離ページから取得したファイルの再送信も止まらない。追加のHTTP規則等が必要。[CF02]

転送経路にも制限がある。たとえば既に隔離された通信では、宛先IPに基づく別の遮断規則が適用されない場合が公式に説明される。クライアントを切断して通常接続できる経路があるため、アプリ側で隔離経路だけに入口を限定する設計が必要というのが本稿の推論である。今回の資料には画面撮影の全面的な禁止仕様はない。[CF03][CF04]

Cloudflare側はTLS通信を復号し、通信ログを保持する説明がある。「原データを一箇所」としても、サービス提供者の処理とログの保存先は別途調べる。[CF01]

### Island：管理ブラウザであり、遠隔のみに置く保証とは別

公式はダウンロード、印刷、画面撮影、コピー/貼付を細かい規則で制御すると説明する。一方、公開技術資料には端末のキャッシュ、Cookie、保存パスワード、文書の保存領域を暗号化する機構がある。これは端末内処理・保存を認めて保護する方式も含むことを示し、「端末に一切データを持たせない」と同一ではない。[IS01][IS02]

また公開監査資料には、クリック、キー入力、画面、利用者・端末等を記録し、他のログ基盤へ送る機能の説明がある。このPDFの現行版への適用範囲・改訂日は今回未確定である。監査を強化すると原文を含む別の記録ができる可能性がある。既定の録画状態、保存地域・期間、OS別の撮影防止の詳細、全管理機能の契約条件は今回の公開資料だけでは未確認。提供者の宣伝上の撮影制御を、任意の外部カメラや侵害済みOSへの完全対策としない。[IS03]

## 3. 国・医療の実運用：原データの閲覧や出力自体を狭める

| 運営と利用目的 | 中央・分散処理と認証 | 持出し・出力の制御 | 適用範囲と限界 |
|---|---|---|---|
| ONS Secure Research Service：英国統計の認定研究 | 認定された研究者と承認された研究、許可された場所/環境、直接識別子を除いたデータを組み合わせる | 出力を審査し、識別につながらないか確認する。公表方針では電子メール・一般インターネット・印刷を利用させず研究環境からの持出しを制限 | 一般顧客向けPII閲覧サービスではない。「安全な人・研究・場所・データ・出力」の五つを組み合わせる設計が参考。技術方式の全詳細や現行の端末キャプチャ遮断は未確認。[ON01][ON02] |
| NHS England SDE：医療データの分析 | クラウド内の仮想デスクトップ、Databricks/RStudio等。二要素認証後、DSA（データ共有契約）や研究単位を選択 | Safe Output Service以外の持出しは禁止とし、画面撮影・共有・手書きも規則上禁止。出力審査では少数件、コード内の未申告データ、Git履歴にも注意 | 「規則上禁止」はOSが技術的に必ず撮影を遮断する証拠ではない。RStudio資料は審査要否をDSA依存と明記しており、全契約一律の手動審査と断定しない。[NH01][NH02][NH03] |
| OpenSAFELY：患者データへ分析コードを送る | 模擬データで作ったコードをデータ管理者の安全な環境で実行。通常の研究者は患者単位のデータを直接閲覧せず、集計結果・ログを見る | 結果は安全な環境で確認し、訓練済み担当者の独立した二重審査後に外部へ出す。操作・コードの監査を重視 | 患者データの管理を一個の新しい倉庫へ全部移す方式ではなく、元の管理者内へ処理を持ち込める。運用・品質調査のための限定された開発者権限は別にあり「誰も原データを読めない」ではない。[OS01][OS02][OS03][OS05] |

NHS SDEのRStudioで「Downloads」に保存される説明は**仮想デスクトップ内のフォルダ**を指す。手元のPCへのダウンロードと同一視しない。その後の外部出力は別手順である。[NH03]

OpenSAFELYの公開説明は、2026年1月時点でOptum保有データへの研究アクセスを資金合意待ちで一時停止と記す。取得時点の説明であり、TPP等を含む全サービスの停止とは解釈しない。[OS04]

OpenSAFELYは表示可能な生の個人データ自体を狭めるため、悪意のある利用者の画面撮影も気にする設計の参考になる。ただしログや集計結果からの開示もあり得るので、出力の検査は不要にならない。データアクセス方針では通常の研究者と、承認された運用担当者等の原データアクセスを明示的に分けている。[OS02]

## 4. 導入時に確認する受入条件（公開資料からの設計上の提案）

1. **アプリへ入る経路を限定する。** 中央データのAPI、ストレージ、通常ブラウザ、別RDP接続で直接取得できないか。OTPを通るポータルだけ制限しても元の入口が開いていれば不足。
2. **画面以外の持出しを止める。** コピー、ドライブ、ファイル、印刷、USB、音声、外部メール/ファイル共有、遠隔環境内からのアップロードを別に評価する。ダウンロードボタンを消すだけとは区別する。
3. **端末条件を固定する。** 管理端末、対応アプリ・版、ブラウザプロファイル、OS、適用済み規則を確認する。未対応端末の接続を拒否するのか、保護がないまま許可するのかも試験する。
4. **原データの表示量を減らす。** 必要な列だけ、部分伏字、一件ごとの理由/再認証、担当ごとの権限を設計する。分析用途なら集計結果だけを閲覧できるOpenSAFELY型を検討する。
5. **出力を審査し監査記録も最小化する。** 原ファイルに加え、画面録画、キー入力ログ、分析ログ、例外時のダンプ、外部の監査保存先の権限・期間・削除を決める。
6. **物理的な撮影は別に扱う。** 端末の画面保護、透かし、利用場所、契約・教育は組み合わせるが、外部カメラをソフトだけで完全阻止できるという保証を求めない。

ここでの対策は主としてアクセスと出力の管理である。中央アプリや分析処理は通常、必要な原データを平文で扱う。秘密計算やゼロ知識証明によって処理者にも原文を見せないという保証とは異なる。

## 5. 保存状況と調査境界

直接取得したHTML/PDFは本文を抽出し、原本と抽出にSHA-256を記録した。AWSの旧URL/ルートにはHTTP200の転送案内しかないものがあり、本文の根拠から外して現名称のページAW07を取得した。NHSの3ページとOpenSAFELY説明ページは直接取得403のため、Web取得ツールで読めた行付き本文抽出を別保存し、HTML原本の取得成功とは区別した。OS04の保存抽出は表示範囲が一部のため、二重審査等は別に取得できたOS03も根拠とする。

今回の7群は代表構造の比較であり、Citrix等の全VDI製品、全契約・料金、データ地域、日本の医療制度適合、アクセシビリティ用の文字送信、端末メモリの全状態までを網羅した監査ではない。2026年の更新は取得時点の公式公開本文による。研究論文の比較は別稿の範囲。

## 一次資料

[AW02]: https://docs.aws.amazon.com/workspaces-web/latest/adminguide/workspaces-secure-browser-maintenance-mode.html "Amazon WorkSpaces Secure Browser availability change - Amazon WorkSpaces Secure BrowserAmazon WorkSpaces Secure Browser availability change - Amazon WorkSpaces Secure Browser"

[AW03]: https://docs.aws.amazon.com/workspaces-web/latest/adminguide/toolbar-controls.html "Managing toolbar controls in Amazon WorkSpaces Secure Browser - Amazon WorkSpaces Secure BrowserManaging toolbar controls in Amazon WorkSpaces Secure Browser - Amazon WorkSpaces Secure Browser"

[AW04]: https://docs.aws.amazon.com/cli/latest/reference/workspaces-web/create-user-settings.html "create-user-settings — AWS CLI 2.38.1 Command Reference"

[MS01]: https://learn.microsoft.com/en-us/azure/virtual-desktop/screen-capture-protection "Screen capture protection in Azure Virtual Desktop - Azure Virtual Desktop | Microsoft Learn"

[MS02]: https://learn.microsoft.com/en-us/azure/virtual-desktop/watermarking "Watermarking in Azure Virtual Desktop - Azure Virtual Desktop | Microsoft Learn"

[MS03]: https://learn.microsoft.com/en-us/azure/virtual-desktop/redirection-configure-clipboard "Configure clipboard redirection over the Remote Desktop Protocol - Azure Virtual Desktop | Microsoft Learn"

[MS04]: https://learn.microsoft.com/en-us/azure/virtual-desktop/redirection-configure-printers "Configure printer redirection over the Remote Desktop Protocol - Azure Virtual Desktop | Microsoft Learn"

[MS05]: https://learn.microsoft.com/en-us/azure/virtual-desktop/whats-new "What's new in Azure Virtual Desktop? - Azure - Azure Virtual Desktop | Microsoft Learn"

[MS06]: https://learn.microsoft.com/en-us/windows-365/enterprise/manage-rdp-device-redirections "Manage device RDP redirections for Cloud PCs. | Microsoft Learn"

[MS07]: https://learn.microsoft.com/en-us/windows-365/enterprise/windows-cloud-display-protection "Display Protection for Windows 365 and Azure Virtual Desktop | Microsoft Learn"

[MS08]: https://learn.microsoft.com/en-us/azure/virtual-desktop/customize-rdp-properties "Set custom RDP properties on a host pool in Azure Virtual Desktop - Azure Virtual Desktop | Microsoft Learn"

[CF01]: https://developers.cloudflare.com/cloudflare-one/remote-browser-isolation/ "Remote browser isolation · Cloudflare One docs"

[CF02]: https://developers.cloudflare.com/cloudflare-one/remote-browser-isolation/isolation-policies/ "Isolation policies · Cloudflare One docs"

[CF03]: https://developers.cloudflare.com/cloudflare-one/remote-browser-isolation/setup/ "Set up Browser Isolation · Cloudflare One docs"

[CF04]: https://developers.cloudflare.com/cloudflare-one/remote-browser-isolation/known-limitations/ "Known limitations - Browser Isolation · Cloudflare One docs"

[CF05]: https://developers.cloudflare.com/changelog/post/2026-04-10-canvas-remoting-performance/ "Canvas Remoting optimizes performance for productivity applications · Changelog"

[IS01]: https://www.island.io/enterprise-browser "Island Enterprise Browser. You decide what the browser does."

[IS02]: https://connect.island.io/hubfs/Analyst%20Reports/Island%20Browser%20Isolation%20%26%20Attack%20Surface%20Reduction%20-%20White%20Paper.pdf "IS02 official PDF"

[IS03]: https://connect.island.io/hubfs/White%20Papers/Enterprise%20Browser%20for%20Auditing.pdf "IS03 official PDF"

[ON01]: https://www.ons.gov.uk/aboutus/whatwedo/statistics/requestingstatistics/secureresearchservice/aboutthesecureresearchservice "About the Secure Research Service - Office for National Statistics"

[ON02]: https://www.ons.gov.uk/file?uri=%2Faboutus%2Ftransparencyandgovernance%2Fdatastrategy%2Fdatapolicies%2Fonsresearchanddataaccesspolicy%2Fattachmentresearchanddataaccesspolicy.pdf "ON02 official PDF"

[NH01]: https://digital.nhs.uk/services/secure-data-environment-service/introduction/safe-outputs "NHS Safe outputs"

[NH02]: https://digital.nhs.uk/services/secure-data-environment-service/introduction/accessing-the-sde-and-the-desktop "NHS Accessing SDE"

[NH03]: https://digital.nhs.uk/services/secure-data-environment-service/access-and-support-for-the-secure-data-environment/user-guides/using-rstudio-in-sde/output-your-results/ "NHS RStudio Output your results"

[OS01]: https://docs.opensafely.org/how-opensafely-works/ "A high level overview of how OpenSAFELY works - OpenSAFELY documentation"

[OS02]: https://docs.opensafely.org/data-access-policy/ "OpenSAFELY Data Access Policy - OpenSAFELY documentation"

[OS03]: https://docs.opensafely.org/security-levels/ "Security - OpenSAFELY documentation"

[OS04]: https://www.opensafely.org/os-in-detail/ "OpenSAFELY in detail"

[OS05]: https://docs.opensafely.org/federation/ "Federated analytics - OpenSAFELY documentation"

[AW06]: https://docs.aws.amazon.com/workspaces-web/latest/adminguide/infrastructure-security.html "Infrastructure security in Amazon WorkSpaces Secure Browser - Amazon WorkSpaces Secure BrowserInfrastructure security in Amazon WorkSpaces Secure Browser - Amazon WorkSpaces Secure Browser"

[AW07]: https://docs.aws.amazon.com/workspaces-web/latest/adminguide/what-is-workspaces-secure-browser.html "What is Amazon WorkSpaces Secure Browser? - Amazon WorkSpaces Secure BrowserWhat is Amazon WorkSpaces Secure Browser? - Amazon WorkSpaces Secure Browser"

## 独立レビュー後の補強

2026-10-15の[独立レビュー](online_pii_review_documents_to_remote_20261015.md)を受け、AVD/W365のWeb画面保護について同じ組織管理のWindows端末が対象外となる条件をMS01本文で再確認し、個人端末・別組織管理・ネイティブアプリを区別した。またNVR比較の「中央の原ファイル不保存」を、比較対象である「端末への原ファイル非配布」へ訂正した。
