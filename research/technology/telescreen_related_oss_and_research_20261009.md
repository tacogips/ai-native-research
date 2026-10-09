# ストレージ等の機密検出・問題管理に関連する公開実装と研究

調査日：2026-10-09。公開資料だけから比較した。ここでの対象は、ファイル・オブジェクトストレージ・データベース・業務ツール等を継続検査し、警告を問題として集約して担当・修正・再確認・再発まで追う仕組みである。特定の非公開実装を説明・推測していない。原本は `research/disclosures/raw/telescreen_related_20261009/oss/`、固定コミット・取得日・保存ハッシュは [資料台帳](telescreen_related_oss_sources_20261009.json) に記録した。実際の認証情報、制限付きの研究データセット、モデル API、認証先への有効性確認を使用していない。製品仕様は公式の説明、公開実装の保存境界は固定コードの静的分析である。

## 1. 結論：検出器・問題管理・データ分類を組み合わせる

公開実装だけで近い構成を作れる。TruffleHog / Gitleaks / detect-secrets は認証情報の検出器、DefectDojo は結果の取り込み・重複排除・解決・再発の追跡、OpenMetadata はデータベース等の列やサンプルからの個人情報分類を提供する。ただし、これらを合わせただけで「認証情報・個人情報・企業秘密の全文を横断して監視し、原文を残さず、修正を検証する完成品」になるわけではない。[TH] [DSREADME] [DOREIMPORT] [OMCLASS]

GitGuardian と TruffleHog Enterprise は完成品として比較対象に近い。通知の集約や修正の進捗管理を含むが、企業秘密一般の意味分類や個人情報一般の検出までを認証情報の検出と同一視しない。また、自社配置、原秘密を保存しないこと、外部へ送信しないこと、平文を読まないことは四つの別条件である。以下はそれぞれ区別している。[GitGuardian incidents](https://docs.gitguardian.com/platform/getting-started/first-incident)、[TruffleHog Enterprise data handling](https://trufflesecurity.com/docs/how-we-handle-your-data)。

| 対象 | 区分・対象内容 | 取得・継続検査 | 警告を問題として管理 | 自社配置・追加検査器 | 原文を残さない要件への注意 |
|---|---|---|---|---|---|
| GitGuardian Platform | 商用完成品、主に秘密・認証情報 | コード、CI、業務ツール、ストレージ、独自ソース | 同じ秘密の出現を一つの問題にまとめ、通知・修正・再発を扱う | 自社配置あり。独自データ源と独自検出器は別 | 製品別・収集経路別に確認。最新 Endpoint Protection の端末走査は原ファイルを管理画面へ送らず、ハッシュ・伏字情報・端末属性を送る。有効性検証は端末から認証情報の提供元APIへ直接送信する別経路 |
| TruffleHog Enterprise | 商用完成品、秘密・認証情報 | Slack・Drive等。S3を含む対応源と配置制約は公式表 | 統合画面・状態・共有・出現箇所・分析 | 自社配置/提供者配置。源によって制約 | 公式説明は原秘密を永続保存せず指紋・伏字・属性を保存。公開版 CLI とは異なる |
| TruffleHog 公開版 | 検出器 | Git・ファイル・S3・GCS等。実行の継続化は別途必要 | CLI結果。企業全体の担当・解決・再発管理を別途作る | 自社実行、独自正規表現・検証先 | 標準 plain/JSON が原秘密を出力。既定の有効性確認で認証先通信 |
| Gitleaks | 検出器 | Git履歴・ディレクトリ・標準入力。S3は取得処理を別途作る | 基準結果との比較・除外はあるが問題台帳ではない | 自社実行、正規表現・エントロピー・複合規則 | `redact` 既定0。付けるだけなら100。補助検出結果・自由記述も別に確認 |
| Yelp detect-secrets | 検出器＋基準結果の監査 | ファイル・事前コミット検査等 | baseline と audit。担当割当等は外部管理 | 自社実行、検出プラグイン・除外・有効性検査 | baseline は SHA-1。実行中は原秘密、既定の確認対応検出器は外部通信 |
| DefectDojo 公開版 | 検査結果の問題管理 | 各検出器のレポートを取得・再取り込み | 正規化、重複、状態、履歴、再発を扱う | 自社配置、独自 parser/API | Gitleaks parser は Secret/Match を記述へ保存。結果の伏字化を先に行う |
| OpenMetadata | データ目録・品質・分類、領域別の利用許諾 | DB/Storage/Messaging分類の実装あり。取得源ごとの対応を確認 | データ資産・タグ・品質の管理。秘密の失効確認とは異なる | 自社配置可能。分類実装に利用目的制約のある公開ライセンス | HEAD schema のサンプル保存は false。分類器は平文サンプルを扱う |
| DataHub | データ目録・問題 API・分類拡張 | 接続先のメタデータとサンプル取得を統合可能 | データ資産の active/resolved 問題 | 自社配置・独自分類器 | 最新安定版の旧標準分類器は削除済み。古いPII説明を現行の既定動作としない |
| OpenDLP / MyDLP | 歴史的な公開DLP | エージェント/ネットワーク等の旧構成 | 旧世代の管理機能 | 原コード取得可能 | 取得対象の最終コミットは2014年。現在の保守・安全な稼働を確認できず、新規採用候補とは分ける |

検出器の欄は [TH] [THCUSTOM] [GLCONFIG] [DSREADME]、問題管理は [DODEDUPE] [DOREIMPORT]、データ分類は [OMCLASS] [DHREMOVED] [DHINCIDENT] が根拠。商用の対応源は [TruffleHog source matrix](https://trufflesecurity.com/docs/connect-sources)、[GitGuardian custom sources](https://docs.gitguardian.com/internal-monitoring/integrate-sources/bring-your-own-sources)、[GitGuardian self-hosting](https://docs.gitguardian.com/self-hosting/home)、[Endpoint Protection](https://docs.gitguardian.com/endpoint-protection/core-concepts) を参照。

## 2. 2026-10-09 の更新状況

GitHub公式APIの最新公開リリースと、取得した既定ブランチ先頭を別々に保存した。「新しいコミットがある」と「そのコードが公開安定版に含まれる」は同じではない。

| リポジトリ | 取得HEADのコミット日 | 取得時の最新公開リリース・公開日 |
|---|---|---|
| trufflesecurity/trufflehog | 2026-10-08 | v3.99.2・2026-10-08 |
| gitleaks/gitleaks | 2026-07-22 | v8.30.1・2026-03-21 |
| Yelp/detect-secrets | 2026-04-02 | v1.5.0・2024-05-06 |
| DefectDojo/django-DefectDojo | 2026-10-05 | 3.4.0・2026-10-05 |
| datahub-project/datahub | 2026-10-08 | v1.7.0.1・2026-09-03 |
| open-metadata/OpenMetadata | 2026-10-08 | 2.0.4-release・2026-10-06 |
| GitGuardian/ggshield | 2026-10-08 | v1.55.0・2026-09-24 |
| ezarko/opendlp | 2014-05-15 | latest release API は404、未確認 |
| mydlp/mydlp | 2014-02-27 | latest release API は404、未確認 |

日付は元のコミット日時/リリースのUTC日付。固定SHA全文とAPI原本は [台帳](telescreen_related_oss_sources_20261009.json)。OpenDLPには同名の別のPythonツールもあるため、ここでは旧OpenDLPの公開ミラー `ezarko/opendlp` と明示した。リリースAPIの404は「保守中止」の公式声明ではない。2014年で止まる取得原本から、2026年の運用・互換・修正体制を実証できないという判断である。

## 3. 原秘密・伏字・ハッシュ・外部送信：固定コード監査

### TruffleHog：公開版とEnterpriseの不保持仕様を分ける

公開版 `PlainPrinter` は `r.Raw` を Raw result として表示する。JSON は `Raw`、複合秘密の `RawV2`、`Redacted`、`SecretParts` を同時に直列化する。`Redacted` が存在しても原秘密が消えたことにはならない。CLIをCIログや問題台帳へ接続すると、その出力が新たな秘密の保管場所になり得る。[THPLAIN] [THJSON]

`--no-verification` が未指定なら有効性確認を止めない設定である。GitHub検出器は `verify` が有効な場合にトークンを渡し、基底実装は Authorization ヘッダーで GitHub APIへ送る。S3オブジェクトを自社環境で読んでいても、見つかったGitHub等の鍵を確認する通信は別に発生する。`--only-verified` / 結果フィルターは「外部送信しない」設定ではなく、送信後の判定の利用である。[THMAIN] [THVERIFY] [THREQ]

Enterprise の公式説明は、原認証情報を処理中RAMに置き、永続保存は指紋・伏字・出現属性だけとする。自社側scannerの説明でも外部認証先への読取専用APIによる確認と、管理側への属性送信を区別する。この仕様は非公開製品コードの独立検証ではない。また、Goの不要オブジェクト回収についての説明はRAMの確実な上書き消去やスワップ・異常終了ダンプまでの保証を実証するものではない。[公式データ取扱い](https://trufflesecurity.com/docs/how-we-handle-your-data)、[Slack掲載の提供者申告](https://slack.com/marketplace/A09FCJ4LHAT-trufflehog-enterprise)。

### Gitleaks：0が既定、100も全フィールドの匿名化ではない

`--redact` の格納既定値は **0**。説明にある default 100% は「値なしでフラグを付けた場合」で、`NoOptDefVal="100"` と対応する。20なら約80%の先頭が残る。100以上なら主たる Secret は `REDACTED`、その Secret と同じ文字列だけを Line/Match 内で置換する。[GLFLAG] [GLREDACT]

従って、`--redact=100` を明示し、レポート内の独立したPII・別秘密・コミットメッセージを別に除去する必要がある。加えて固定HEADの `PrintRequiredFindings` は複合規則の補助 Secret を直接表示し、主Secretの Redact は補助リストを操作しない。これが発生するのは補助検出結果を持つ表示経路であり、「すべての実行で漏れる」という主張ではない。現状の静的評価では、100%というフラグ名だけを根拠に全出力の原秘密不保持を保証できない。[GLREDACT] [GLFILTER]

JSON reporter は Finding をそのまま符号化する。Fingerprint は commit/file/rule/line または file/rule/line で、秘密値の暗号学的指紋ではない。ファイル移動・行変化・異なる場所への同じ鍵の出現をまとめるには別の同一性設計が必要。Gitleaksの形式検出を認証先での有効性確認と混同しない。[GLJSON] [GLFINGER]

### detect-secrets：baselineは原秘密を含まないが実行中は含む

`PotentialSecret` は平文 `secret_value` を保持し、baseline の JSON には `hashed_secret=SHA1(secret)`、検出種、ファイル、行、確認状態等を出す。SHA-1に個別saltや秘密鍵を追加するコードではない。低エントロピーの社内パスワード等に対する辞書照合への耐性や、匿名化を保証するものではない。[DSHASH]

既定の verification policy は対応検出器の `verify` を呼ぶ。Slack例は auth.test に token を送信し、Webhook例はそのURLへ空textをPOSTする。すべての検出器が確認APIを持つわけではない。`--no-verify` でフィルターを無効化し、外向き通信制限も併用する。ローカル実行・ハッシュbaselineという二つの事実だけでは、秘密が認証先へ送られないことは言えない。[DSVERIFY] [DSSEND]

### DefectDojo：正規化しても不保持にはならない

Gitleaks取り込みは Secret と Match を Finding の description に連結する。内部の重複用MD5には title+secret+line が使われるが、ハッシュにしたから説明から平文が消えるわけではない。[DOGITLEAKS]

TruffleHog v3取り込みは表示記述に Redacted を使い、Raw/RawV2 は重複識別の入力に使う。コミッターのメールアドレスも Committer として記述へ保存される（固定コード127・151行）。秘密を伏せても個人情報の最小化は別途必要である。StructuredData と ExtraData は記述に入るので、その中身や原アップロード、ログ、添付の保存方針も別途監査する。これも全製品DBへの原文不保持証明ではない。[DOTRUFFLE]

## 4. 問題の集約・解決・再発と修正の確認

GitGuardian は同じ秘密の出現を一つの incident にまとめ、新規発生・再発で通知する。既に未解決の問題に出現が増えただけでは同じ通知を繰り返さない。コード上にまだ秘密が見えるかを presence check で確認するが、コードから消えたことと認証情報が失効したことは別に扱う。元コミットを履歴から外しても、参照のないコミットがVCS上で取得可能な場合がある。[incident管理](https://docs.gitguardian.com/platform/getting-started/first-incident)、[調査・存在確認](https://docs.gitguardian.com/internal-monitoring/remediate/investigate-incidents)。

DefectDojo の Reimport は同じ Test に最新検査を入れ、新規を作成、既存を維持、消えた問題を設定次第で閉鎖、閉鎖済みが戻れば設定次第で再開する。APIの close_old_findings は既定 true と文書化される。従ってS3走査が部分失敗した、権限が減った、検出器を変えた、暗号化/大容量ファイルを読めなかった等の欠落を「修正済み」としてはいけない。閉鎖は完了した同じ監視範囲の再検査だけで行う設計を推奨する。[DOREIMPORT]

重複方式は検出器ごとの unique ID / hash / legacy 等を設定できる。違う製品や別ルールが同じ鍵を検出しても、そのまま一つになる保証はない。正規化で最低限、対象源ID、オブジェクトIDと版、出現位置、検出器/規則/版、秘密の鍵付き指紋、所有者、初回/最終確認、検査の範囲と完了状態を持たせる。これは公開機構を踏まえた設計案であり、DefectDojo既定の全実装内容ではない。[DODEDUPE] [GLFINGER]

## 5. 個人情報・企業秘密とDB/Storageの検査

OpenMetadata の取得HEADはDB・Storage・Messagingの分類workflowを選び、sampler→PII processor→sinkの経路を作る。PII分類器は列名・型・平文サンプルを組み合わせ、PresidioのAnalyzerEngineと規則等を使う。Presidioは個人情報の検出/置換ライブラリであり、それだけでは取得権限、継続走査、担当割当、問題の履歴を備えた完成品ではない。[OMCLASS] [OMHEUR]

この固定HEADの DB/Storage schema は **storeSampleData=false、enableAutoClassification=true、confidence=80、sampleDataCount=50、language=en**。古い公式ページのサンプル保存 true という説明をこの版の既定値へ移してはいけない。false は保存設定であり、サンプルを検出器が平文で読まないことでも、全ログ・デバッグ出力・外部sinkの不保持でもない。ストレージ対応も構造化されたcontainerのサンプル分類と、あらゆる文書本文・バイナリを全文検査するDLPを同一視しない。[OMDB] [OMSTORE]

公開コード中の分類領域 `ingestion/LICENSE` は Collate Community License で、競合する提供等の Excluded Purpose に制約がある。リポジトリ全体の宣伝的な「open source」の呼称だけで全機構を同じ利用許諾と扱わない。[OMLICENSE]

DataHub はデータ資産への問題の登録・active/resolved状態・APIによる自動登録を持つ。一方、取得HEADと最新安定 **v1.7.0.1** の classifier registry は旧 `acryl-datahub-classify` の依存未保守を理由にbuilt-in datahub分類器を削除し、独自Classifierの登録枠を残している。registryのコメントは旧機能を使う版として1.6.0.5を挙げるが、古い版へ固定することを推奨するものではない。現行版で「PII自動検出がそのまま既定で使える」とは記載しない。[DHINCIDENT] [DHREMOVED] [DHSTABLE] [DHCLASS]

秘密鍵・メール住所の形式と、未公開価格戦略、顧客別条件、研究成果、取締役会議事録等の企業秘密の判定は異なる。自社辞書・規則・既存分類ラベル・所有部門・共有範囲を第一段階に使い、必要ならローカル分類モデルを追加する。暗号化DBを目録化することやタグの継承だけを「本文を読まない意味分類」の事例に数えない。

## 6. 原論文4本：何を測ったか

4本の原PDFと抽出全文を保存し、方法・評価・限界・運用上の意味を確認した。加えて `2504.18784` と `2608.04523` は今後の比較用に原PDFを取得したが、今回の根拠として採用していない。F1は適合率と再現率の調和平均で、陽性クラス・平均方法・候補抽出後か全文か・対象源が違えば直接比較できない。

### IssueGuard（2602.08072、取得PDFはv3、2026-04-08）

[原論文](https://arxiv.org/pdf/2602.08072)。Chrome拡張＋FastAPI＋正規表現候補抽出＋微調整CodeBERTの研究実装。GitHub/GitLabのIssue入力を検査し、200文字の文脈を使う。54,148候補、真の秘密5,881、75/10/15%の学習/検証/試験分割。表1のF1 **92.70%**（適合率92.49・再現率92.91）は候補分類で、正規表現が見落とした全文中の秘密までを含む到達率ではない。178公開リポジトリへの別評価は秘密クラスF1 **64.20%**、macro F1 **81.60%**。表と本文には比較モデルのF1表記の小差もあり、単一の高い値だけを取り出して比較しない。

50人の課題実験で、各10件のIssueを用いる。手動課題で66%が見落としたという結果は、実会社での漏洩率66%でも、継続導入後の被害減少率でもない。平均198msは特定CPU/GPU条件。論文の正規表現・モデル・候補集合・評価装置を変えた場合は再測定が必要。

公開コードも固定した。拡張はdescription全体を localhost:8000/detectへPOSTする。cacheキーはSHA256(context+candidate)、保存値は判定だが、CACHE HIT/MISS の print は候補の先頭50文字を出し、応答はall_candidatesを返す。よって実装をそのまま運用して「原文不保持」と呼べない。文字列が短ければ先頭50文字が秘密全体になり得る。[IGSEND] [IGCACHE] [IGLOG] [IGRETURN] [IGCONFIG]

### AssetHarvester（2403.19072、取得PDFはv2、2024-11-20）

[原論文](https://arxiv.org/pdf/2403.19072)。秘密と対応資産の組を静的解析し、通知へ「何にアクセスする鍵なのか」を付ける研究。4種DB、188リポジトリ、1,791組。正規表現、CodeQLのデータフロー、近傍行の推定を併用する。組の検出でTP1,626・FP34・FN165、報告適合率97%・再現率90%・F1 94%。SQL Serverは25組中8組を検出し再現率32%、F1 48%。全秘密の分類F1や、DB内のPII本文分類のF1ではない。 データフローは最新スナップショットで計算しており、過去コミットだけに残る組をそのまま捕捉する保証もない。

データフローの「FPゼロ」は当該データ・当該手法の結果で、全言語・動的処理への保証ではない。SecretBench由来で、Pythonを含むリポジトリを選び、対応資産を見つけられなかった323候補を外している。基礎データに無い86秘密も追加発見したため、基礎データの網羅性は限定される。別15リポジトリで42組を発見、18人の回答で15同意という追加検証は、全候補の網羅的再現率を測る分母ではない。表VIの一部TP/FP併記は表頭と比率が整合しないため、その生数を独自に正しい分母と確定して比較表を作らない。

### RiskHarvester（2502.01020、取得PDFはv1、2025-02-03）

[原論文](https://arxiv.org/pdf/2502.01020)。AssetHarvesterの組へ、DB名・列名から推定する資産価値と接続容易性を加え、対応順を決める研究。188リポジトリ・1,791組のRiskBench。DB/表/列名の抽出は個別分母で、全体TP/FP/FNはDB名1,405/43/86、表677/25/74、列1,222/106/209。対応カテゴリへの意味マッピングは3,673語で適合率85%。要約の95%/90%を「PII本文分類の精度95%」としない。

認証せずにDB本文を読む研究ではなく、コード中の名前等を指標にする。fastTextと文字列類似度に加え、非英語語のGoogle Translation、DNSのplaceholder判定でgpt-4o-2024-08-06へ名前と近傍コード、DNS問い合わせ、Censys検索を使う。従って純ローカル・無外部送信の事例ではない。Censys利用を、研究者が流出鍵を使って実DBへログインしたこととも混同しない。

500人へ依頼して52回答、45/52（約86%）がリスク順へ優先順位を変えた。これは質問実験での選択であり、実運用の修正時間や漏洩削減の実測ではない。リスク点は序数を著者のProtection Pokerで数値へ割り当てた相対順位で、侵害確率・期待損失額ではない。通知に資産と到達性を示す設計は参考になるが、一般の企業文書の機密分類へそのまま適用しない。

### SecretBench（2303.06729、取得PDFはv1、2023-03-12）

[原論文](https://arxiv.org/pdf/2303.06729)。818リポジトリ、49言語、311種類のファイル。97,479は候補出現数で、真秘密15,084、候補の一意文字列27,336、真秘密の一意文字列4,014。手作業ラベルは文脈判断で、有効性を流出鍵で確認していない。これらの数を「現役の異なる97,479鍵」と書かない。

候補の選定にTruffleHog・Gitleaksと761正規表現を使うため、検出器外の任意形式や企業秘密一般の評価集合ではない。原文やコミッターのメールを含むためデータ保護契約下で選択的提供とする。今回そのデータセットを取得していない。同じ秘密の別コミット出現を無造作に学習と試験へ分けないこと、リポジトリ/時期/秘密単位の重複除去を行うことが評価設計上の条件となる。

## 7. 自社配置による構成案と、関連候補の位置づけ

公開部品による構成案は、取得処理→自社内検査→安全な結果形式への変換→問題管理→対象源への修正→同範囲の再検査、である。S3はイベント通知と定期全走査を併用し、版・削除・権限変更・失敗を扱う。Azure Blobや共有ファイルは、取得処理の対応・権限・読み切り確認を別に追加する。S3対応を理由に全共有ファイル/全DBへの組込み対応を主張しない。[TH] [DOREIMPORT]

- 認証情報：TruffleHogを検査隔離環境内で実行し、検証先の許可リストと `--no-verification` を選ぶ。標準出力は外部ログへ流す前に破棄/安全変換する。JSONのRaw以外にRawV2、SecretParts、自由属性も除去する。[THJSON] [THMAIN]
- 形式型の個人情報：Presidio等の検査器を別に接続し、機密検出結果を同じ問題形式へ変換する。全文を問題台帳へ貼り付けず、源内リンクと最小限の伏字を残す。[OMHEUR]
- 企業秘密：部門の分類ラベル・規則・アクセス状態を基に、必要なら自社モデルで候補を分類する。モデル精度と原文不保持は別々に評価する。IssueGuardを採用する場合にもログの変更が必要。[IGLOG]
- 指紋：同じ秘密の集約には鍵付きHMAC等を検討する。テナント別鍵・世代を持ち、指紋の越境照合や辞書攻撃を抑える。これは今回の既定実装の記述ではなく設計提案である。[DSHASH] [GLFINGER]
- 問題管理：DefectDojo等へ安全な記述だけを取り込み、担当・状態・初回/再発・例外理由を管理する。部分走査の欠落では閉鎖しない。元データの除去と鍵の失効を二つの検証に分ける。[DOGITLEAKS] [DOREIMPORT]

Cloud Custodian はクラウド資源の条件選択、イベント、通知や是正処理の規則基盤として関連する。標準のS3公開設定・暗号化等の条件を、オブジェクト本文の秘密検出器と同じ欄に置かない。[公式quickstart](https://cloudcustodian.io/docs/quickstart/index.html)、[公式filter説明](https://www.cloudcustodian.io/docs/filters.html)。[Prowler公式README](https://github.com/prowler-cloud/prowler)も、クラウドの検査・統制・修正案・画面・レポートを説明しており、設定評価と組み合わせる候補である。ただし、今回本文のPII/企業秘密検出やSentry型の再発管理を備えた完成品としては検証していない。原本取得失敗・未確認部分は台帳に明記した。

採用前の検証では、①同じ鍵の複数源を一問題へ集約、②短い秘密もログ/通知/DBに残らない、③確認APIを無効にして外向き通信ゼロ、④部分失敗で既存問題が閉じない、⑤修正後の失効と本文消去を別に確認、⑥再出現で再開、⑦検出器更新で評価集合と通知量の変化を計測、を合成データで試す。この一覧は今後の実装受入条件であり、今回実機実行済みという意味ではない。

## 固定コード出典

[TH]: https://github.com/trufflesecurity/trufflehog/blob/0e427395344c7039c0b15a1147f5782805685b3e/README.md#L244-L288
[THCUSTOM]: https://github.com/trufflesecurity/trufflehog/blob/0e427395344c7039c0b15a1147f5782805685b3e/README.md#L839-L900
[THMAIN]: https://github.com/trufflesecurity/trufflehog/blob/0e427395344c7039c0b15a1147f5782805685b3e/main.go#L40-L110
[THJSON]: https://github.com/trufflesecurity/trufflehog/blob/0e427395344c7039c0b15a1147f5782805685b3e/pkg/output/json.go#L44-L86
[THPLAIN]: https://github.com/trufflesecurity/trufflehog/blob/0e427395344c7039c0b15a1147f5782805685b3e/pkg/output/plain.go#L30-L68
[THVERIFY]: https://github.com/trufflesecurity/trufflehog/blob/0e427395344c7039c0b15a1147f5782805685b3e/pkg/detectors/github/v2/github.go#L75-L115
[THREQ]: https://github.com/trufflesecurity/trufflehog/blob/0e427395344c7039c0b15a1147f5782805685b3e/pkg/detectors/github/v1/github_old.go#L140-L172
[GLFLAG]: https://github.com/gitleaks/gitleaks/blob/b58d3f102cf3a2c84cb7f923d05c25c9b1aed84b/cmd/root.go#L75-L92
[GLREDACT]: https://github.com/gitleaks/gitleaks/blob/b58d3f102cf3a2c84cb7f923d05c25c9b1aed84b/report/finding.go#L77-L126
[GLJSON]: https://github.com/gitleaks/gitleaks/blob/b58d3f102cf3a2c84cb7f923d05c25c9b1aed84b/report/json.go#L1-L17
[GLFINGER]: https://github.com/gitleaks/gitleaks/blob/b58d3f102cf3a2c84cb7f923d05c25c9b1aed84b/detect/detect.go#L709-L718
[GLFILTER]: https://github.com/gitleaks/gitleaks/blob/b58d3f102cf3a2c84cb7f923d05c25c9b1aed84b/detect/utils.go#L136-L166
[GLCONFIG]: https://github.com/gitleaks/gitleaks/blob/b58d3f102cf3a2c84cb7f923d05c25c9b1aed84b/README.md#L383-L407
[DSHASH]: https://github.com/Yelp/detect-secrets/blob/5e141933554a0b74e7341841f318be21e895339c/detect_secrets/core/potential_secret.py#L50-L115
[DSVERIFY]: https://github.com/Yelp/detect-secrets/blob/5e141933554a0b74e7341841f318be21e895339c/detect_secrets/core/usage/filters.py#L166-L184
[DSSEND]: https://github.com/Yelp/detect-secrets/blob/5e141933554a0b74e7341841f318be21e895339c/detect_secrets/plugins/slack.py#L29-L51
[DSREADME]: https://github.com/Yelp/detect-secrets/blob/5e141933554a0b74e7341841f318be21e895339c/README.md#L1-L150
[DOGITLEAKS]: https://github.com/DefectDojo/django-DefectDojo/blob/258344266af19de33d721e511f2fc34834f67bdb/dojo/tools/gitleaks/parser.py#L160-L219
[DOTRUFFLE]: https://github.com/DefectDojo/django-DefectDojo/blob/258344266af19de33d721e511f2fc34834f67bdb/dojo/tools/trufflehog/parser.py#L125-L193
[DOREIMPORT]: https://github.com/DefectDojo/django-DefectDojo/blob/258344266af19de33d721e511f2fc34834f67bdb/docs/content/import_data/import_intro/reimport.md#L8-L73
[DODEDUPE]: https://github.com/DefectDojo/django-DefectDojo/blob/258344266af19de33d721e511f2fc34834f67bdb/docs/content/triage_findings/finding_deduplication/OS__deduplication_tuning.md#L8-L78
[DHREMOVED]: https://github.com/datahub-project/datahub/blob/12a7d7e5d831d282866602b00d3cdfad4a7f1bc2/metadata-ingestion/src/datahub/ingestion/glossary/classifier_registry.py#L1-L21
[DHCLASS]: https://github.com/datahub-project/datahub/blob/12a7d7e5d831d282866602b00d3cdfad4a7f1bc2/metadata-ingestion/src/datahub/ingestion/glossary/classifier.py#L16-L67
[DHINCIDENT]: https://github.com/datahub-project/datahub/blob/12a7d7e5d831d282866602b00d3cdfad4a7f1bc2/docs/incidents/incidents.md#L12-L72
[OMCLASS]: https://github.com/open-metadata/OpenMetadata/blob/fc6a14d76d6ea58c4a13d49991e44e9423dc805a/ingestion/src/metadata/workflow/classification.py#L34-L81
[OMHEUR]: https://github.com/open-metadata/OpenMetadata/blob/fc6a14d76d6ea58c4a13d49991e44e9423dc805a/ingestion/src/metadata/pii/algorithms/classifiers.py#L86-L158
[OMDB]: https://github.com/open-metadata/OpenMetadata/blob/fc6a14d76d6ea58c4a13d49991e44e9423dc805a/openmetadata-spec/src/main/resources/json/schema/metadataIngestion/databaseServiceAutoClassificationPipeline.json#L45-L85
[OMSTORE]: https://github.com/open-metadata/OpenMetadata/blob/fc6a14d76d6ea58c4a13d49991e44e9423dc805a/openmetadata-spec/src/main/resources/json/schema/metadataIngestion/storageServiceAutoClassificationPipeline.json#L36-L73
[OMLICENSE]: https://github.com/open-metadata/OpenMetadata/blob/fc6a14d76d6ea58c4a13d49991e44e9423dc805a/ingestion/LICENSE#L15-L34
[IGCACHE]: https://github.com/disa-lab/IssueGuard/blob/70ed19b9ecc959dc71c27bb7fcc5be67e5a545e4/api/service.py#L50-L123
[IGLOG]: https://github.com/disa-lab/IssueGuard/blob/70ed19b9ecc959dc71c27bb7fcc5be67e5a545e4/api/service.py#L166-L192
[IGRETURN]: https://github.com/disa-lab/IssueGuard/blob/70ed19b9ecc959dc71c27bb7fcc5be67e5a545e4/api/service.py#L215-L252
[IGSEND]: https://github.com/disa-lab/IssueGuard/blob/70ed19b9ecc959dc71c27bb7fcc5be67e5a545e4/IssueGuardExtension/content.js#L1198-L1227
[IGCONFIG]: https://github.com/disa-lab/IssueGuard/blob/70ed19b9ecc959dc71c27bb7fcc5be67e5a545e4/api/config.py#L18-L43
[DHSTABLE]: https://github.com/datahub-project/datahub/blob/e99431ec510d7a2001f815c6bf70913c493af76e/metadata-ingestion/src/datahub/ingestion/glossary/classifier_registry.py
[OPENDLP]: https://github.com/ezarko/opendlp/blob/b02568fdac225bd8c8c237b1120b4657d71556ec/README#L1-L80
[MYDLP]: https://github.com/mydlp/mydlp/blob/14d3fa1da2a212746f24fa2316d62e2b5f1f5ea1/README#L1-L22

## 独立レビューによる補強

2026-10-09の[独立レビュー](telescreen_review_enterprise_to_oss_20261009.md)を受け、GitGuardian Endpointの管理画面送信と提供元APIへの認証情報の有効性検証を分離した。送信属性には機械識別子・ホスト名・端末の利用者名が含まれ、Linux ServerとWindows Serverは同取得資料で試験段階（Beta）とされる。DefectDojoのTruffleHog取り込みがコミッターのメールを記述へ保存する経路も補強した。台帳dojo_dedupeは転送案内のみで本文の根拠に採用せず、重複判定の説明は固定コード原本[DODEDUPE]を使う。これらは公開本文と静的コードの確認であり、実環境の通信・保存・削除試験ではない。
