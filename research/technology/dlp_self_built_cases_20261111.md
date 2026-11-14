# 機密情報の検知台帳と許可判定を自作する公開事例

調査日：2026年11月11日。対象は、保存先の巡回、個人情報・秘密の検知、結果の一覧、人の判定、既知問題の再通知抑制を組み合わせる自作システム。公開一次資料から、本番の自社基盤、公開実装、公式構築例、組込み部品の17系統を比較した。独立17社や本番完成品17件を意味しない。

**今回の要件をそのまま満たす公開完成品が17件あるわけではない。** 日本語Google Driveの具体的実装は `truefinder/pii_in_google_drive`、日本語の局所検知部品は `fuseji`、判定を残して既知結果を再通知しない設計は `detect-secrets`、人の確定判定とモデルの推測を分ける本番設計はMeta、承認付きの処理手順はAWSの構築例が参考になる。OpenAI Privacy Filterは手元で実行できる専用検知モデルであり、その利用アプリや日本語向け追加学習例も公開されている。

公開コードは[取得時の版・利用許諾・保守状態](dlp_self_built_code_sources_20261111.json)を確認し、主要例の実装を読んだ。サービス接続、モデルの実行、精度測定、実運用の安全性検証は行っていない。以下の「未確認」は、公開資料から要件を証明できない状態を示す。

用語：APIはソフトウェア同士の呼出し口、OCRは画像からの文字読取り、JSONは項目名と値を持つデータ形式を指す。公開重みモデルは学習済みの数値を入手して自前の環境で実行できるモデル、追加学習は既存モデルを追加の事例で調整すること。以下の「基準一覧」は、過去の検知を保存して新規の検知と区別するための一覧である。

## 実装と設計の比較

| 系統・根拠 | 種類 | 保存先・日本語・形式 | 判定・記録・再通知抑制 | 制約・自作で追加するもの |
|---|---|---|---|---|
| 1. [truefinder/pii_in_google_drive](https://github.com/truefinder/pii_in_google_drive) | 日本語の公開実装 | SheetsのリンクからDriveファイルを取得し、OpenAI APIで日本語の個人情報を判定 | 有無・種別件数・理由をSheetsへ記録。処理済み行のスキップ | 全Driveの継続監視・承認台帳ではない。PDF本文未抽出、先頭6,000文字、例外失効・差分通知は別実装 |
| 2. [Meta PAIの2026年事例](https://engineering.fb.com/2026/06/25/security/privacy-aware-infrastructure-in-the-ai-native-era-an-asset-classification-case-study/) | 本番の自社基盤 | データ資源・項目・経路等の文脈を使い、曖昧なものへ大規模言語モデルを適用 | 人の確定判定を追記型・版付きで保存。モデル提案を確定ラベルに自動昇格させず、規則への反映も人が承認 | 日本語Drive製品や導入可能な公開完成コードではない。再通知抑制の完成機能の証明ではなく、判定管理の設計根拠 |
| 3. [Yelp detect-secrets](https://github.com/Yelp/detect-secrets) | 企業発の公開実装 | コード内の鍵・秘密。ファイル・Gitの登録前検査 | 検出の基準一覧を保存し、人が真偽を判定。既知の秘密は登録前警告から分離可能 | 氏名・電話の一般検知、Drive、PDF・画像抽出は別。未検出を保証しない |
| 4. [Gitleaks](https://github.com/gitleaks/gitleaks) | 公開検知ツール | Git履歴・ディレクトリー・標準入力の秘密 | 既知検出一覧を基準として新規だけ出力。規則・場所等の許可設定 | 基準一覧の結果は新規出力から消えるため、全件台帳を別に保持する。個人情報一般のモデルではない |
| 5. [fuseji](https://github.com/sserada/fuseji) | 日本語の公開部品 | 日本語の電話・住所・個人番号等、追加のGiNZAで人名。文字列・JSON・処理記録 | 置換・伏字・指紋等と、Langfuse・Presidio等への組込み例 | Drive巡回・通知・承認は別。画像・PDFの直接処理は対象外。種別ごとの現行対応と将来予定を区別 |
| 6. [Presidio](https://github.com/data-privacy-stack/presidio) | 拡張可能な公開部品 | 文字・画像。固有名抽出、形式規則、検査数字、独自検知器 | 検出箇所・種別と匿名化処理をアプリへ組み込む | 日本語用の言語処理・検知器を構成する必要。巡回・許可判定・通知管理は別 |
| 7. [Capital One DataProfiler](https://github.com/capitalone/DataProfiler) | 企業発の公開部品 | CSV等の構造化データ・非構造化データの統計と意味分類 | データの分類・統計を保存先ごとに収集する基盤に使える | Drive監視やOK／NG承認の完成品ではない。日本語の属性別精度は未確認 |
| 8. [PIICatcher](https://github.com/tokern/piicatcher) | 公開データベース検査 | データベース・分析基盤の列を検査し、Amundsen／DataHub等へ分類を連携 | 資源・列の分類を一覧へ反映 | Driveファイル・画像とは対象が異なる。**2026年1月26日に保管専用化**されており、依存更新・保守を要評価 |
| 9. [TheMoMatthias/Anonymizer](https://github.com/TheMoMatthias/Anonymizer) | 手元で使う公開アプリ | Word・Excel・PowerPoint・PDF。Presidio、追加のOCR | 検出種別の確認、変更内容の表示、伏字版と監査JSONの保存 | 継続監視ではない。言語モデル・OCR実行環境が必要。取得時の公開木に利用許諾ファイルを確認できず、再利用条件を要確認 |
| 10. [Google Cloudの検査結果分析例](https://docs.cloud.google.com/sensitive-data-protection/docs/analyzing-and-reporting) | 公式構築例 | Cloud Storageの氏名・電話等を検査し、結果をBigQueryへ保存 | 検査結果の台帳化、照会・集計。通知経路と分けて設計可能 | Driveを直接巡回する例ではない。人の許可・変更時失効・再通知抑制は追加する |
| 11. [AWS Macieの承認付き処理例](https://aws.amazon.com/blogs/security/use-macie-to-discover-sensitive-data-as-part-of-automated-data-pipelines/) | 公式構築例 | S3への投入をMacie・Step Functionsで検査 | 人がApprove／Denyを選び、承認なら移動、拒否なら削除する例 | 承認が同じ値の恒久許可になる仕様ではない。例の拒否操作は削除であり、分類記録だけ欲しい用途では変更する |
| 12. [AWSの複数アカウント修正手順](https://aws.amazon.com/blogs/security/building-sensitive-data-remediation-workflows-in-multi-account-aws-environments/) | 公式構築例 | S3の検出を集約、Step FunctionsとLambdaで判断 | DynamoDBへ隔離状態、Teams通知、API経由で隔離解除 | 隔離解除と将来の再通知停止は別。元データの移動を伴う。Drive接続・日本語検出は別 |
| 13. [AWSの2026年自動検査例](https://aws.amazon.com/blogs/architecture/automate-custom-pii-detection-at-scale-with-amazon-macie-and-step-functions/) | 公式構築例 | 新規S3投入をEventBridgeからMacieへ。独自の識別番号も検査 | CSV／JSON報告、通知と保存先の分離 | 起動が速くても検査完了は同義でない。記事の例は約15〜20分。多数の小ファイルではジョブの集約・費用管理が必要 |
| 14. [OpenAI Privacy Filter](https://github.com/openai/privacy-filter) | 専用の公開重みモデル | 手元で文字列の氏名・住所・電話・秘密等8種の箇所を検知 | 検出箇所を台帳の入力にでき、追加学習可能 | ファイル抽出、OCR、Drive、許可・通知は別。日本語の合成評価はあるが、完全匿名化や実業務精度の保証ではない |
| 15. [textsift](https://github.com/teamchong/textsift) | Privacy Filter利用アプリ | ブラウザー・手元の実行環境、コマンド、Git登録前・継続検査への組込み | 検知と伏字化、開発手順内での機密検査 | モデルは英語中心。Drive巡回・承認済み台帳は別。上流の日本語評価を自作アプリの実測値と混同しない |
| 16. [privacy-filter-jp-GGUF](https://huggingface.co/sumeshi/privacy-filter-jp-GGUF) | 第三者の日本語追加学習例 | 日本語の氏名・住所・業務文脈。手元の専用実行器で利用 | 日本語追加学習・評価・変換の例 | 実験段階。106例の小規模な評価は本番保証でない。OpenAI公式の日本語版ではない。専用モデル形式の実行器を確認 |
| 17. [Claudeの内容分類例](https://platform.claude.com/docs/en/about-claude/use-case-guides/content-moderation)と[OpenAIの入力保護](https://developers.openai.com/api/docs/guides/agent-builder-safety#use-guardrails-for-user-inputs) | API・処理手順の公式構築部品 | 内容のプライバシー分類、個人情報の伏字化等 | 自社分類を定義し、判定結果に応じて処理を分岐 | 2社の別機能を「1つの完成品」と数えない。どちらもDrive巡回・全件台帳・人の承認・通知抑制は追加開発 |

本番事例として扱ったのは、当事者が自社運用を説明するMetaの基盤である。企業発の公開コードやクラウド提供者の構築例は、それだけで特定顧客の本番利用・精度を証明しない。

## 日本語Drive実装のコード確認

`truefinder/pii_in_google_drive`は今回の目的に近いため、READMEの対応表だけでなく、取得した固定版の実装を確認した。調査結果は次のとおり。

| 確認点 | 固定版の実装 | 今回の要件への意味 |
|---|---|---|
| 入力範囲 | Sheetsのリンク列からDriveの識別子を取得して処理 | フォルダー全体の継続発見ではない |
| 結果 | 個人情報有無、種別件数、短い理由をSheetsへ書く | 検知値と位置の全件一覧、人の許可判定、通知管理は別 |
| 文字上限 | 抽出文字を先頭6,000文字へ切り詰める | 後半の情報を見つける保証がない。部分検査として記録すべき |
| PDF | 本文を抽出せず、名前・容量と抽出できない旨をモデルへ渡す | PDF内容を検査済みと扱ってはいけない |
| Forms・Drawings | 本文の代わりに名前等へ依存する処理 | 実体を読めないことを検査エラー・未検査として扱う必要 |
| Office等 | 形式変換を試み、失敗時に名前や失敗文へ戻る経路 | 「拡張子が分岐にある」と「本文を抽出できた」を分ける |
| モデル入力 | ファイル名・リンク・抽出内容等をOpenAI APIへ送信 | 手元だけで検査する方式ではない |
| API保持 | READMEは分析後削除を述べるが、該当の呼出しコードだけでは提供者側の保持条件を証明できない | READMEの表明を、契約・APIの保持設定の保証へ拡張しない |

根拠は固定版の[本文抽出](https://github.com/truefinder/pii_in_google_drive/blob/91eaf0712f269a9846081d9e5d469c2d1d8c20ee/pii_file_extractors.gs#L514)、[6,000文字制限](https://github.com/truefinder/pii_in_google_drive/blob/91eaf0712f269a9846081d9e5d469c2d1d8c20ee/pii_file_extractors.gs#L645)、[モデルへ送る内容](https://github.com/truefinder/pii_in_google_drive/blob/91eaf0712f269a9846081d9e5d469c2d1d8c20ee/pii_analyzer.gs#L39)、[結果の記録](https://github.com/truefinder/pii_in_google_drive/blob/91eaf0712f269a9846081d9e5d469c2d1d8c20ee/pii_main.gs#L74)。記載はコードを読んだ結果であり、実行結果ではない。

## 判定登録と再通知抑制を実装する参考

| 公開例 | 借りられる設計 | そのまま満たさない要件 |
|---|---|---|
| detect-secrets | 全検出の基準一覧と人の真偽判定を保存し、既知・新規を分離する | 基準一覧にある実際の秘密も新規警告から外れる。未解決NGを追跡する台帳は必要 |
| Gitleaks | 過去の検出一覧を読み、新規だけ報告する | 過去検出が消えたのか、単に再報告しないのかは新規報告だけで判断できない |
| Meta PAI | 人の確定ラベルとモデルの推奨を別管理。確定結果は追記・版管理。承認された規則へ還元する | Drive用の通知と例外台帳は公開されていない |
| AWS承認・隔離 | 検知、状態保存、人の許可、後続処理を分離する | 許可の期限・情報種別・フォルダー・内容変更後の失効は独自設計が必要 |
| Google検出結果の保存 | 検知をデータベースに残し、その上で必要な通知だけ選ぶ | 個別の承認、同じ情報の同一性、例外の取り消しは追加実装 |

detect-secretsの人による判定と基準一覧の保持は、[固定版README](https://github.com/Yelp/detect-secrets/blob/5e141933554a0b74e7341841f318be21e895339c/README.md)を根拠とする。Gitleaksの基準一覧使用後の報告が新規だけになる点は、[固定版README](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/README.md)に明記される。これらは、全件台帳を残す要件に対しては、そのままの通知出力とは別に台帳を設ける必要がある。

## 自作構成に落とす場合の設計案

今回の要件は、検知処理から警告を直接送るより、まず検知台帳へ保存し、保存場所・属性・判定・規則を評価して通知する構成に適している。以下は公開事例から組み立てた設計案であり、既存実装の動作説明ではない。

| 段階 | 保存・処理するもの | 具体的な条件 |
|---|---|---|
| 1. 巡回 | Driveのファイル識別子、版、所有者、親フォルダー、共有状態、変更時刻 | 差分取得に加え定期的に全体照合。移動・共有変更も対象にする |
| 2. 本文抽出 | 読めた範囲と、未対応・失敗・部分検査の状態 | PDFや画像を読めないとき、陰性や検査完了にしない |
| 3. 検知 | 属性、箇所、検知器と版、信頼度 | 日本語の形式規則・固有名抽出と、Privacy Filter等を比較。精度を自社の試験資料で測る |
| 4. 全件台帳 | 許可・不許可に関係なく検出記録を保存 | 指定フォルダーの氏名・電話も絞り込んで認知できる |
| 5. 許可判定 | 場所×属性×共有先×有効期間、判定理由・担当・日時 | ファイル全体の無視より狭い条件を使う |
| 6. 通知判定 | 通知対象か、既知問題か、未解決か | 許可場所の氏名・電話は通知しない。同じ場所の秘密鍵、場所外の氏名は通知する |
| 7. 再評価 | 内容・場所・共有・規則・検知器の変更 | 許可の適用条件が崩れたら再通知。単なる再保存と区別 |

検知の正誤、機密か否か、業務上の許可、通知するかを別項目にする。例えば「正しく電話番号を検知、機密情報に該当、顧客管理フォルダー内では業務上許可、通知なし」と保存する。これを誤検知ラベルに変えると、学習用の正解まで誤ってしまう。

値の照合には、平文をそのまま台帳に持つか、鍵付きのハッシュ等を使うかを決める。単純なハッシュだけでは電話番号等の候補を総当たりできるため、「ハッシュなら原文を推測できない」とは扱わない。表記正規化と照合鍵の変更も版管理する。

## 自作案の制約比較

| 方式 | 利点 | 費用・保守・見逃しの制約 |
|---|---|---|
| OpenAI Privacy Filterを手元で実行 | 原文を外へ送らず、8種類の箇所をまとめて検出する候補 | 実行環境、前処理、モデル更新、日本語精度の評価が必要。専用の日本識別番号検証を併用 |
| fuseji・Presidio・GiNZA等 | 日本語固有の形式規則と人名抽出を分離して調整できる | 未知の氏名・住所の曖昧性、規則保守、画像抽出、依存関係の管理 |
| OpenAI API・Claude API | 文脈や独自の機密区分を説明して分類できる | 入力の外部送信、呼出し費用、処理時間、モデル変更、原文中の指示に影響される問題への対処 |
| Cloud DLP／Macie等のAPI | 検査と保存先の仕組みを組み合わせやすい | 提供地域・対応形式・容量・検査課金・非同期処理、Drive接続は別 |
| 公開小規模アプリを改造 | 画面や抽出の初期実装を再利用できる | 利用許諾・依存保守・抽出失敗・認証・保持を確認。公開コードであることは本番利用の保証ではない |

公開事例を比較する段階で、取得したPIICatcherは保管専用化されていた。またPresidioの現在の公開先は `data-privacy-stack/presidio`であり、Microsoftの商用Purviewと同じ保守・契約を期待しない。利用許諾と取得時点の版は取得台帳を参照。

## OpenAIとAnthropicについての補足

OpenAIは2026年4月22日にPrivacy Filterを公開している。これは標準の文章生成APIとも、Agent Builderの入力保護とも別の、専用の公開重みモデルである。モデル・ライセンス・日本語評価の数値と条件は[制約比較](dlp_product_limitations_and_build_options_20261111.md#openaiとanthropicの提供範囲)にまとめた。[公式発表](https://openai.com/index/introducing-openai-privacy-filter/)、[モデル説明資料](https://cdn.openai.com/pdf/c66281ed-b638-456a-8ce1-97e9f5264a90/OpenAI-Privacy-Filter-Model-Card.pdf)

Anthropicの公式例ではPrivacyを含む独自基準で内容分類を組めるが、これをDrive用の全件巡回・承認・通知管理の完成品とは扱わない。また、内部のプライバシー分析技術の説明と、顧客向けの独立した検知モデルの配布は区別する。[Claudeの公式例](https://platform.claude.com/docs/en/about-claude/use-case-guides/content-moderation)

特定製品の精度を他社より低いとする第三者のREADME記述は、そのまま比較結果へ採用していない。Privacy Filterの日本語追加学習例も、元モデル・派生版・小規模な独自評価を区別し、OpenAI公式の日本語モデルと呼ばない。
