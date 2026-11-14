# Compose・eBPFと代替技術によるAIの制限：LLM推論と公開実例

確認日：2026年11月4日。[実行環境の選定](ai_execution_sandbox_selection_20261027.md)と[未許可URLへの送信防止](ai_egress_url_data_exfiltration_controls_20261103.md)の補足。公開された公式文書、設定例、利用企業の発言を含む導入報告を確認した。製品導入、GPU推論、通信遮断、攻撃耐性の実機試験は行っていない。

**外向き通信の制限にFirecrackerやeBPFは必須ではない。通常のコンテナに、ホスト側の通信遮断、ファイル・操作の制限、送信内容を認可する代理部を組み合わせる構成も候補になる。** ただし、共有カーネルが侵害される場合に備えた仮想化境界は別の問題である。本稿の推奨構成は設計案であり、以下の実例を組み合わせた完成システムの検証結果ではない。

## 1. Compose、仮想機械、eBPFは役割が違う

| 技術 | 役割 | 単独では保証しないこと |
|---|---|---|
| Docker Compose | 複数コンテナの起動・設定・管理 | 任意URLへの送信禁止、業務操作の認可 [S1] |
| 通常のLinuxコンテナ | 名前空間、権限、資源上限による分離 | カーネル共有に起因する侵入経路の除去 [S2] |
| Firecracker等の仮想機械 | 個別のカーネルと仮想化による追加境界 | 許可した通信・共有ファイルからの情報流出 |
| eBPF | カーネル内の処理に検査・記録・制限を実装する仕組み | 規則なしでの自動隔離、任意のHTTPS本文の認可 |

eBPFという名称は単一の隔離製品を指さない。通信経路に検査を置く実装と、OSの安全性検査へ規則を追加するBPF LSMでは、対象が違う。LSMはLinux Security Modulesの略で、OSが操作の可否を検査する仕組み。BPF LSMの公式例は、記憶領域の保護属性変更を検査して拒否するものである。[S3]

通常のコンテナ＋eBPFでも、ホストのカーネルは信頼対象として残る。カーネル侵害まで想定するなら、専用の仮想機械、gVisor、Kata等を追加で比較する。gVisorはLinuxの呼出しを仲介する別方式で、個別のゲストカーネルを持つ仮想機械と同一ではない。[S4]

## 2. eBPF以外で同じ目的を達成する方法

「eBPF相当」は、何を制御したいかに分けて判断する。以下の機能は置換可能な部分と組み合わせる部分がある。

| 対象 | eBPFを使う候補 | 別の候補 | 限界と選び方 |
|---|---|---|---|
| 接続先IP・ポート、方式 | Cilium等の通信制御 | nftables / iptables、クラウド側のファイアウォール | URLのパス・本文・受信者は別。IPv4・IPv6、転送される通信も対象にする [S5][S6] |
| URLのパス・HTTP操作 | eBPFによる誘導とHTTP代理の組合せ | 外部のHTTP代理、Google Cloud Secure Web Proxy等 | HTTPSの内容検査は暗号化通信の終端等が必要。パケットの遮断だけでは実現しない [S7] |
| ファイル・実行の権限 | BPF LSM、対応するTetragon規則 | AppArmor / SELinux | 管理側が規則を強制。記録だけのモードと遮断モードを区別 [S3][S8][S9] |
| 処理自身と子プロセスの権限縮小 | 対象を限定したeBPF規則 | Landlock | 利用可能な機能はOS・ABIの版に依存。ネットワーク規則はポート単位で、URL許可一覧とは違う [S10] |
| OS呼出しの削減 | 対応する検査箇所での操作拒否 | seccomp | 呼出し番号や引数の検査。任意のファイル名・URLの認可器にはならない [S11][S12] |
| 観測・監査 | Tetragon、Cilium/Hubble等 | OSの監査記録、ファイアウォール・代理部のログ | 観測できることと送信前に阻止できることは別 |

seccompはBPF形式のフィルターを使うが、一般にここで比較しているeBPFの通信・LSMプログラムとは異なる仕組みである。「eBPFを導入しない構成」と「BPFという技術を一切使わない構成」は区別する。Linux公式資料も、seccomp単独を完全な隔離環境とはしていない。[S12]

**Composeを使う小規模構成の案：** nftables等でAIコンテナの直接通信を閉じ、AppArmorまたはSELinux、既定のseccomp、最小限の権限と共有領域を組み合わせ、外向き操作は外側の代理部へ限定する。eBPFを使わずに達成できる部分を先に定義し、実行主体ごとの動的な制御や観測が必要ならeBPF基盤を比較する。

Dockerは独自の通信規則を生成する。ホストの`INPUT`・`OUTPUT`だけを見て制約が有効と判断せず、コンテナの転送経路を確認する。Docker公式資料も、公開ポートの通信がufwの想定する経路を迂回する条件を説明している。iptablesとnftablesのどちらを使うかで設定方法も変わる。[S6]

## 3. eBPFを入れれば自動的に防げるわけではない

Tetragonは、対応する呼出しの戻り値を変更して操作を拒否する方法と、`SIGKILL`で処理を終了させる方法を説明する。後者だけでは、検出のきっかけとなった書込み等が完了しないという保証はない。送信防止では、実際の送信・操作を拒否する位置で強制する必要がある。[S13]

ホスト側に置いた規則でも、AIへホスト管理権限や規則変更権限を渡せば保護を弱める。eBPFプログラム、設定API、対象プロセスとの対応を管理側で保護し、コンテナの再作成、子プロセス、規則の再読込み、管理用プロセスの再起動後も制限が続くか確認する。これは本調査の受入条件案である。

通信のIP・ポート制限だけでは、HTTPSに暗号化されたパス・本文や、許可済みサービス内の別組織への送信を判定できない。外側の代理部で宛先、組織、対象資源、HTTP操作、送信項目を確認する設計は、eBPFの有無にかかわらず必要になる。[既存の通信隔離調査](ai_egress_url_data_exfiltration_controls_20261103.md)

## 4. LLMも動かせるか

**コンテナ内でCPU・GPUを使ってLLMを動かし、その処理をeBPF等で制限する構成は可能。** eBPF自体をLLMの推論実行基盤にするという意味ではない。推論は通常のプログラムが行い、eBPF等は周囲の通信・操作を制約する。

vLLMはGPUを利用する公式Dockerイメージと実行例を公開している。[S14] Docker ComposeにもGPUを指定する公式設定例がある。[S15] 両者は、GPU推論をコンテナで動かすための部品が存在する根拠になるが、eBPFと組み合わせた情報非流出の証明にはならない。

以下は本調査の役割分担案。

| 処理 | 配置・権限 | 許可する通信の案 |
|---|---|---|
| LLM推論 | GPU付き専用コンテナ。必要なモデルを事前配置 | 管理部からの推論要求とその応答。外部への新規接続は原則禁止 |
| 計画・道具の選択 | 管理されたAIアプリ | 推論先と限定した道具だけ |
| 生成コード・コマンド | 別の作業用コンテナ | 必要な内部の接続先だけ。推論用GPUや管理鍵を渡す必要があるか個別判断 |
| 外部への操作 | 管理側の代理部 | 認可した組織・対象・操作だけ |
| 規則・監査 | ホストまたは別の管理環境 | AI側から変更不可 |

モデル・イメージの取得や更新に必要な接続と、機密を投入した後の実行時通信は分ける。モデルを事前配置しても、実装固有の計測送信・追加取得がないか試験する。外向きの新規接続を閉じても、許可した推論応答へ機密を含める経路は残るため、推論APIの利用者と応答の搬出も認可する。

GPUドライバーや、渡した機器へのアクセスも信頼対象になる。eBPFを使うだけでGPU記憶の分離まで保証するとはしない。vLLMの起動例にはホストとの共有や機器依存の権限設定が含まれる場合があるので、実行例をそのまま機密処理用の最小権限設定とは扱わない。[S14]

## 5. 公開実例：導入報告と設定例を区別する

| 実例 | 資料の種類 | 確認できること | その資料だけでは確認できないこと |
|---|---|---|---|
| Bloomberg BQuant Enterprise＋Cilium | 利用企業の発言を含む導入報告 | ポート・ホスト名の通信規則で分析環境の搬出経路を制約し、保存領域のアクセスを管理 [S16] | LLMへの不正指示や任意の符号化による持出しを網羅的に防いだ結果 |
| CiliumのGitHub宛通信制限 | 公式設定・試験例 | `api.github.com`への接続と、未許可の`support.github.com`への失敗を掲載 [S17] | GitHub内の受信組織・本文の制限、DNSでの持出しの完全防止 |
| Tetragonの機密ファイル操作制限 | 公式設定・試験例 | 対象ファイルの読取りを試したプロセスの強制終了と記録 [S18] | すべてのファイル読取り・送信が事前に阻止された保証 |
| Docker AppArmorのNginx例 | 公式設定・試験例 | 指定プロファイルでシェル起動・書込み等が拒否される例 [S8] | 任意のAIにそのまま適用できる権限設定 |
| vLLM Docker＋Compose GPU設定 | 二つの公式実行・設定例 | GPUをコンテナへ割り当ててLLM推論を構成する部品 [S14][S15] | 統合したCompose＋eBPF構成の安全性・性能 |
| NVIDIA OpenShell＋Run:ai＋vLLM | 公式の構築手順 | 管理されたKubernetes上のAI実行と、別の推論処理への接続 [S19] | eBPFだけでの制御、利用企業による本番導入、完全な情報非流出 |

### Bloomberg：情報の搬出制限に近い導入実例

CNCFの導入報告では、BloombergのBQuant EnterpriseチームがCiliumのホスト側の通信規則を使い、ポート・ホスト名を制約したと説明する。独自の分析用保存領域へのアクセス管理と、Hubbleによる通信の可視化も記載されている。[S16]

これは、利用者が分析処理を実行する環境のデータ境界に通信規則を使う実例として有用である。ただし、資料の成果説明は導入報告であり、本調査が攻撃試験や成果を独立に再現したものではない。LLM特有の持出し対策の実証とも区別する。

### Cilium：許可先の制限とDNS規則は別

公式の設定例は、対象Podの`toFQDNs.matchName`で`api.github.com`を許可し、別のホストへの接続失敗を掲載する。一方、同じ例のDNS規則は`matchPattern: "*"`で問い合わせ名を広く許可している。[S17]

本調査の解釈として、機密データの持出し対策に利用する際は、このDNS部分をそのまま採用せず、問い合わせ対象の制限か代理部だけでの名前解決を検討する。Ciliumの設定例を、通常のComposeにそのまま読み込ませることはできない。この例はCiliumを導入したKubernetes用である。

### TetragonとAppArmor：監視・終了・事前拒否の違い

Tetragonの入門例では`/etc/shadow`等の操作を試し、`SIGKILL`による終了を確認する。[S18] 本文の操作制限説明が注意する通り、この例だけから「操作が一切完了していない」とは判定しない。[S13]

対してDockerのAppArmor例は、Nginx用のプロファイルを適用した状態で、シェル起動や書込みが`Permission denied`になる出力を掲載する。[S8] eBPFを使わずに実行権限を制約する具体例になる。汎用シェルを必要とするAIにはそのまま転用せず、必要な権限との差を調べる。

Tetragonにはホストへパッケージとして配置する公式手順もある。[S20] したがって、eBPFによる制約の検討が常にKubernetes導入を前提とするわけではない。ただし、Composeで起動した処理を対象にどう規則を結び付けるかは別途設計・検証する。

### OpenShell＋Run:ai：推論とAIの操作環境を分ける構築例

NVIDIAの公式手順は、Run:aiが管理するKubernetes上にOpenShellのAI実行環境を置き、vLLMまたはNVIDIA NIMで提供するモデルへ接続する方法を説明する。規則を強制するのはOpenShellであり、Run:aiの資源管理と区別している。利用者の所属についても、両製品の管理情報を一致させる必要があると記す。[S19]

これは、LLM推論とコマンド実行を分ける参考例である。OpenShellを「eBPFだけの製品」と分類する根拠にはしない。また、この手順で正規のGitHub書込み等を許可しても、本文に機密が含まれないという保証まで得られるわけではない。

## 6. E2Bを自社設備・GCEに置く場合の補足

E2B Embedは、管理部分とFirecracker実行部分等を一台に置く公開構成で、Docker Composeによる導入手順がある。[S21][S22] **このComposeはE2Bの部品を起動するものであり、Firecrackerを通常のコンテナ隔離に置き換えるものではない。**

| 方式 | 配置と運用 | 確認する条件 |
|---|---|---|
| E2B Embed | 自社Linuxホスト、または自社GCE等の単一機械を自社運用 | KVM、必要な機器・権限、保存領域、外部取得先 [S21][S22] |
| E2B BYOC | 自社クラウド内の環境をE2Bが構築・監視 | 契約、管理側との通信、対象機能。自社だけで運用する方式と区別 [S23] |
| 独自のCompose構成 | 推論・作業・代理を独自に構築 | E2BのAPI・状態管理等をそのまま得られるわけではない |

Embedの公式手順はKVMが必要とし、仮想機械上では入れ子の仮想化を有効にする。GCEの入れ子の仮想化には機械種別の制約があり、E2シリーズ等は対象外である。[S22][S24] 通常のGPUコンテナを動かすためだけなら、入れ子の仮想化を要件にする必要はない。

導入用イメージ等を取得する外部接続があるため、「自社設備で動く」と「外部との接続を一切必要としない」を同一視しない。[S22] また、自社配置でもAIの送信先制限は別に適用する。

## 7. 構成を選ぶ目安と追加試験

以下は本調査の提案である。

| 条件 | 比較する構成 |
|---|---|
| 単一部署・限定した処理、まず通信を止めたい | 専用Linux/GCE＋Compose＋nftables等＋AppArmor/SELinux＋seccomp＋送信代理 |
| 処理ごとの柔軟な制約・詳細な記録が必要 | 上記にeBPF基盤を追加、または対応する制御部を置換 |
| 多数の利用者が任意コードを実行し、共有カーネルの侵害も懸念 | 顧客・案件ごとの仮想機械、gVisor、Kata等を比較。通信・業務認可は併用 |
| GPUでLLMを動かし、AIの操作も許可したい | 推論コンテナと作業環境を分け、GPU・モデル・管理鍵へのアクセスを個別に制約 |

追加の受入試験では、通信の遮断だけでなく、制御対象との対応と強制の継続を確かめる。

- コンテナの作成・再作成・再起動後、子プロセスにも同じ制約があるか。
- 規則読込み失敗、管理部停止、ホスト再起動時に無制限で起動しないか。
- AppArmorの`complain`、SELinuxの`permissive`等、記録だけの状態を遮断済みと判定していないか。[S8][S9]
- Landlockの必要機能がないとき、制限を省略して機密処理を続けないか。対応するABIを実行前に確認する。[S10]
- 強制終了の記録だけで判断せず、管理下の受信先に架空データが到達していないか。
- 外向き全遮断でも、許可したAPI応答・ログ・成果物からの搬出を制約できるか。
- GPUを使う正規の推論が動き、作業用コードから推論サーバーの管理口・別案件のデータへ届かないか。

既存の[通信隔離の受入試験](ai_egress_url_data_exfiltration_controls_20261103.md)と合わせて実施する。各方式が同じ保証を与えるとはせず、試験対象のOS・規則・製品版・処理単位を記録する。

## 出典

すべて2026年11月4日に確認した公開資料。設定例の出力は提供者の掲載内容であり、本調査が実行した結果ではない。更新される文書・`main`の説明は、導入時に採用する固定版で再確認する。

- [S1] Docker, [Why use Compose?](https://docs.docker.com/compose/intro/features-uses/)
- [S2] Docker, [Docker Engine security](https://docs.docker.com/engine/security/)
- [S3] Linux Kernel, [LSM BPF Programs](https://docs.kernel.org/bpf/prog_lsm.html)
- [S4] gVisor, [Security Model](https://gvisor.dev/docs/architecture_guide/security/)
- [S5] Netfilter, [What is nftables?](https://wiki.nftables.org/wiki-nftables/index.php/What_is_nftables%3F)
- [S6] Docker, [Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [S7] Google Cloud, [TLS inspection overview](https://docs.cloud.google.com/secure-web-proxy/docs/tls-inspection-overview)
- [S8] Docker, [AppArmor security profiles](https://docs.docker.com/engine/security/apparmor/)。Nginxの設定例と制限結果。
- [S9] Red Hat, [Getting started with SELinux](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/getting-started-with-selinux_using-selinux)
- [S10] Linux Kernel, [Landlock: unprivileged access control](https://www.kernel.org/doc/html/latest/userspace-api/landlock.html)
- [S11] Docker, [Seccomp security profiles](https://docs.docker.com/engine/security/seccomp/)
- [S12] Linux Kernel, [Seccomp BPF](https://docs.kernel.org/userspace-api/seccomp_filter.html)
- [S13] Tetragon, [Enforcement](https://tetragon.io/docs/concepts/enforcement/)。操作拒否と強制終了の違い。
- [S14] vLLM, [Using Docker](https://docs.vllm.ai/en/latest/deployment/docker/)
- [S15] Docker, [Run Docker Compose services with GPU access](https://docs.docker.com/compose/how-tos/gpu-support/)
- [S16] CNCF, [Bloomberg case study](https://www.cncf.io/case-studies/bloomberg-2/)。BQuant Enterpriseの利用者発言を含む導入報告。
- [S17] Cilium, [Locking Down External Access with DNS-Based Policies](https://docs.cilium.io/en/stable/security/dns/)。閲覧時の表示版1.20.4。
- [S18] Tetragon, [Policy Enforcement](https://tetragon.io/docs/getting-started/enforcement/)
- [S19] NVIDIA, [Running AI Agents with NVIDIA OpenShell on NVIDIA Run:ai](https://docs.nvidia.com/run-ai/self-hosted/v3.0/documentation/tutorials/agent-tutorials/openshell-on-runai)。Run:ai v3.0の公式構築手順。
- [S20] Tetragon, [Deploy with a package](https://tetragon.io/docs/installation/package/)
- [S21] E2B, [Embed](https://github.com/e2b-dev/runtime/blob/main/embed/README.md)
- [S22] E2B, [Embed with Docker Compose](https://github.com/e2b-dev/runtime/blob/main/embed/compose/README.md)
- [S23] E2B, [BYOC](https://docs.e2b.dev/byoc)
- [S24] Google Cloud, [About nested virtualization](https://docs.cloud.google.com/compute/docs/instances/nested-virtualization/overview)
