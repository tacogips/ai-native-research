# 全社PCに常駐して機密データを監視する製品

調査日：2026年10月16日。公開公式資料に基づく比較。機能の記載は提供者の説明であり、実機での精度・負荷・遮断成功率は未検証。価格順位・性能順位は付けない。

## 結論と分類

目的に最も近い製品分野は **Endpoint DLP（端末での情報漏えい防止）**。PCに常駐する小さな監視ソフトウェアを配布し、中央の管理画面で検知条件・通知・遮断を管理する。ただし、以下は別の機能である。

| 目的 | 分野 | 例 |
|---|---|---|
| PCに置くべきでない個人情報・機密ファイルを見つける | 保存データの探索・分類 | P-Pointer File Security、Netwrix Endpoint ProtectorのeDiscovery |
| 機密情報のUSBコピー、外部送信、印刷などを検知・制限する | Endpoint DLP | Microsoft Purview、Fortra DLP、Cyberhaven、MIND |
| 誰がどこへファイルを動かしたか調べる | 内部不正リスク管理・操作記録 | Mimecast Incydr、SKYSEA Client View、LANSCOPE |
| ウイルス、侵入、ランサムウェアの活動を検知・対処する | EPP（端末の予防保護）・EDR（端末での侵害検知と対応） | DLPとは別の評価対象。同一会社・同一常駐ソフトウェアでも契約機能を確認する |

ここでいう「不正」は、データだけで自動的に決まるものではない。「顧客名簿を個人PCの指定外フォルダに保存」「人事資料を個人のクラウドへ送信」のように、情報の内容・保存場所・持ち主・操作・送信先と組織の規則を組み合わせて定義する。

## 製品比較

| 製品 | 公開資料で確認できる機能 | 比較時の注意 | 一次資料 |
|---|---|---|---|
| Microsoft Purview Endpoint DLP | 機密情報の種類や分類ラベルを使って、USB、印刷、ネットワーク共有、ブラウザー経由の送信などを監査・警告・遮断 | Windows/macOSで機能差。対象端末と対象ユーザーの両方を規則の範囲に含める必要がある。全ディスクの定期棚卸し機能と同一視しない | [公式仕様](https://learn.microsoft.com/en-us/purview/endpoint-dlp-learn-about) |
| Cyberhaven | 常駐ソフトウェア、ブラウザー拡張、クラウド接続を組み合わせ、コピー・編集・共有の経路と内容を利用して分類・保護 | データの来歴だけを使う判断と、本文・画像文字認識を使う判断がある。「常に本文を読まない製品」ではない。公式はWindows/macOS/Linux対応を案内するが、機能同等性は別途確認 | [構成と来歴追跡](https://www.cyberhaven.com/product/how-data-lineage-works) |
| MIND Endpoint DLP | 常駐ソフトウェアによるローカルファイルの継続的探索・分類、ブラウザー操作の検知、危険な持ち出しへの対処を案内 | 「継続的」「リアルタイム」は提供者の説明。対象形式・操作・OSごとの機能と処理時間は実証試験で確認 | [端末向け製品](https://mind.io/solutions/data-source-endpoint) |
| Fortra DLP（Digital Guardian系） | Windows/macOS/Linuxの端末で保存中・使用中・移動中のデータを検査。監視、遮断、対処。通信切断中の保護も案内 | 全OS・全アプリで同じ検査や遮断ができるとは限らない。対象構成の仕様が必要 | [公式製品説明](https://www.fortra.com/solutions/data-protection/data-loss-prevention) |
| Netwrix Endpoint Protector | Device Controlは機器制御、Content Aware Protectionは内容に基づく保護、eDiscoveryは保存済みデータの探索。eDiscoveryはWindows/macOS/Linuxの定期・単発検査や隔離・暗号化・削除に対応 | eDiscoveryは別ライセンス。週次・月次などの予約検査と、操作時の遮断を区別する | [eDiscovery仕様](https://docs.netwrix.com/docs/endpointprotector/admin/ed_module/edmodule) |
| Mimecast Incydr（旧Code42系） | サービスとして動く常駐ソフトウェアがファイル移動を観測し、クラウドで警告・調査に利用 | 持ち出しが疑われるとファイルの写しをクラウドへ保存する場合がある。内容検査は任意の追加構成。全保存ファイルの内容検査とは区別 | [構成とデータ収集](https://mimecastsupport.zendesk.com/hc/en-us/articles/42666107367571-Incydr-architecture) |
| CrowdStrike Falcon Data Security / Data Protection | Falconの常駐ソフトウェアと管理画面を利用し、端末・ブラウザー・生成AIへの情報移動を分類・監視・制御 | 通常の侵害検知機能を契約しているだけでデータ保護機能まで使えるとは限らない。製品範囲、OS、契約を確認 | [公式説明](https://www.crowdstrike.com/en-us/platform/data-security/) |
| P-Pointer File Security | PC・ファイルサーバ内の個人情報を探索。更新ファイルの差分検査、ファイル更新時の自動検査、規則に基づく移動・削除、中央管理 | Windowsのサービスとして動作。Windows以外のファイルサーバをWindows端末経由で調べる機能は、他OSのPCに常駐する機能とは異なる。あらゆる送信経路の遮断製品として扱わない | [公式機能](https://www.ppointer.jp/product) |
| SKYSEA Client View | ファイル作成・コピー、ブラウザー経由のアップロード、クリップボード、印刷などの操作記録 | 操作記録の取得と、本文からの機密分類は別機能。必要な検査は連携製品・追加構成を確認 | [操作記録](https://www.skyseaclientview.net/function/log/) |
| LANSCOPE Endpoint Manager | 全社端末の資産管理、ファイル・Webの操作記録、USB利用制御、規則違反通知 | 自社設置版・クラウド版で仕様差。操作記録だけでは機密本文を分類したことにはならない | [公式機能一覧](https://www.lanscope.jp/lp/asset/) |

## 「常駐」「常時監視」の読み方

常駐とは、利用者が検査ボタンを押さなくても監視用の処理が動いていること。ファイルの作成・更新時に内容を調べる方式、USBや送信操作の時点で判断する方式、保存済みファイルを予約検査する方式は異なる。管理画面もすべてが即時更新とは限らない。

具体的に、Purviewはファイル作成・変更時の分類を説明している一方、端末へ一度も保存していないファイルは検査・分類できず、WordからUSBへ直接保存する例では検査・遮断できないと明記している。P-Pointerは更新時の検査を有効にできる。NetwrixのeDiscoveryは単発・週次・月次などの検査を提供する。[Purview](https://learn.microsoft.com/en-us/purview/endpoint-dlp-learn-about)、[P-Pointer](https://www.ppointer.jp/product)、[Netwrix](https://docs.netwrix.com/docs/endpointprotector/admin/ed_module/edmodule)。

## これまでの構想に対する選び方

以下は公開機能からの設計上の判断で、製品の性能順位ではない。

- **PCに顧客情報を残させたくない**：P-Pointer、Netwrixの保存データ探索から比較する。中央の保管先へ移す運用と組み合わせる。
- **個人のクラウド・USB・生成AIへの持ち出しを止めたい**：Purview、Cyberhaven、MIND、Fortra、Netwrixの内容に基づく保護を比較する。既存Falcon環境ではData Protectionの追加条件も調べる。
- **まず全社のファイル操作を把握したい**：SKYSEA、LANSCOPE、Incydrを比較する。操作履歴からの危険度判定と本文検査は分けて評価する。
- **ウイルスやランサムウェアも対象にしたい**：EPP/EDRとDLPの両方を要件にする。機密ファイルの保有が正当でも、暗号化攻撃や侵入の検知は別途必要になる。

導入試験では、対象OS・ブラウザー・ファイル形式、既存ファイルの初回検査、通信切断中の動作、停止・削除を防ぐ仕組み、検査負荷を確認する。警告だけか遮断できるかも操作ごとに区別する。鍵のない暗号化ファイルの本文判定や、端末外からの画面撮影まで保証するものとしては扱わない。

特にこれまでの「機密原文を外部AIへ渡さない」という条件では、**分類処理の実行場所と、通知・証拠として外部へ送る内容を別々に確認する**。常駐型でも、端末内で全処理が完結するとは限らない。Incydrには証拠ファイルのクラウド保存、Cyberhavenにはクラウド側の処理が公式説明に含まれる。[Incydr](https://mimecastsupport.zendesk.com/hc/en-us/articles/42666107367571-Incydr-architecture)、[Cyberhaven](https://www.cyberhaven.com/product/how-data-lineage-works)。

## 関連する既存調査

- [PCへ原文を配布しないオンライン集中管理](online_pii_centralized_management_20261015.md)：中央保管と閲覧・代理処理。今回の常駐監視は、例外的なダウンロードや持ち出しの検知を補完できる。
- [保存場所を横断する機密情報の警告システム](telescreen_related_systems_20261009.md)：クラウドストレージや業務サービスも含む比較。

## 確認・訂正

公式機能・構成説明を確認し、本文の根拠を各行へ付した。表を読み直し、操作記録だけの製品を内容分類製品と同列に扱わないよう訂正した。OS対応という記載から全機能の同等性を推定せず、旧Code42とMimecast Incydrも別製品として重複計上していない。本稿は公開資料の確認と自己レビューであり、独立した第三者レビュー・実機試験は未実施。
