# AIを隔離して動かす実行環境の選び方

確認日：2026年10月27日。公開された公式文書と公開実装の説明を調査した。対象は、AIが生成したコード、コマンド、外部のプログラムを実行する環境。製品導入、侵入試験、性能・費用の実測は行っていない。提供者の説明と、本稿の選定案・試験案を区別する。

**選ぶ対象は「隔離方式」「環境を作成・破棄する管理機能」「外部への操作権限」の三つである。** 仮想機械で実行を隔離しても、渡したファイル、許可した通信先、認証情報の権限は利用できる。業務データの保護には、これらの制限をAIの外側で強制する構成が必要になる。gVisorの公式資料も、隔離は安全な全体設計の代替にならないと説明する。[S3]

既存の[17技術・基盤の比較](agent_os_sandbox_deep_dive_20261007.md)を補い、実行環境の選定と受入試験に絞る。既存資料にある2026年10月7日時点の版・初期設定は、本稿の日付の仕様へ自動的に読み替えない。

2026年11月3日追記：[未許可URLへの送信を防ぐ通信隔離](ai_egress_url_data_exfiltration_controls_20261103.md)で、DNS・転送・許可済みサービスへの持出し、外部の代理部による制御を追加調査した。

2026年11月4日追記：[Compose・eBPF・代替技術と公開実例](ai_container_ebpf_alternatives_and_examples_20261104.md)に、Firecrackerを必須としない構成、GPUでのLLM推論、E2Bの自社設備・GCE配置を補足した。

## 1. 何を隔離するか

「sandbox」は、信用できない処理のアクセス範囲を制限する環境を指す。本稿では次の境界を分けて考える。

| 境界 | 防ぎたいこと | 設計上の確認点 |
|---|---|---|
| 実行機械 | ホストや別の実行環境への侵入 | OSの中核であるカーネルを共有するか。仮想化部分とホストの更新責任は誰か |
| ファイル | 機密の読取り、原本の削除、後で実行される不正設定の埋込み | 共有する範囲、読取りと書込みの区別、成果物を取り戻す方法 |
| 通信 | 情報持出し、社内サービスへの接続 | 外向き通信の既定拒否、名前解決、内部IP、公開接続口の認証 |
| 認証・認可 | 秘密鍵の盗難、許可範囲を超える代理操作 | 秘密値の外部保管、短い有効期限、対象・操作の制約 |
| 資源 | CPU、記憶、保存領域、実行時間、費用の使い切り | 子プロセスを含む上限と、外から強制停止できる仕組み |
| 状態・管理 | 別利用者の状態の再利用、自分の制約や監査記録の改変 | 利用者と環境の対応、復元用複製の管理、管理APIの外部配置 |

表は本調査の設計整理である。モデルへの「禁止事項」の指示や、実行前の確認画面だけでは、OSや仮想化による隔離の代わりにならない。

## 2. 隔離方式の違い

| 方式 | 仕組み | 適した用途の案 | 限界・確認点 | 出典 |
|---|---|---|---|---|
| OSの権限制限：Landlock等 | プロセスと子プロセスのファイル・通信権限を制限 | 手元の補助処理。別の隔離方式への追加防御 | カーネルは共有。利用可能な制限はOS・機能の版に依存 | [S1] |
| 通常のDockerコンテナ | 名前空間で資源の見え方を分離し、資源上限・権限制限を適用 | 管理下の処理の再現、開発環境の分離 | カーネル共有。Docker管理用の接続口や広いホスト共有を渡すと境界を弱める | [S2] |
| gVisor | 利用者空間の実装がLinuxのシステム呼出しを処理し、ホストへの直接接触を減らす | 対応するLinux処理、多数の独立した実行環境 | 互換性・性能の確認が必要。通信規則と資源上限は別途設定 | [S3] |
| 小型仮想機械：Firecracker等 | ハードウェア仮想化を使い、個別のカーネルを持つ | 信用できないコード、利用者ごとの分離 | 仮想化部も更新が必要。Firecracker単体では環境管理・認可は完成しない | [S4] |
| Kata Containers | コンテナの管理体系に仮想機械の境界を組み合わせる | Kubernetesを使った自社管理の実行基盤 | 仮想化方式・設定と、Podなどの共有単位を確認する | [S5] |
| Wasmtime / WASI | WebAssemblyの記憶領域を制限し、明示した外部機能を与える | 小さな計算・変換処理を道具として提供 | 一般のLinux環境と互換ではない。与えた外部関数・ファイル権限は利用できる | [S6] |

gVisorと仮想機械の安全性を、名称だけで一列に順位付けすることはできない。gVisor自身も、仮想化の有無だけでは安全性を決められないと説明する。共有CPUなどから情報が漏れる経路についても、ホスト側の対策が必要である。[S3]

## 3. 実際に使うための候補

以下は提供者が公開している構成であり、独立した侵入耐性の検証結果ではない。

| 候補 | 公開資料で確認できた構成 | 用途の案と確認事項 |
|---|---|---|
| Docker Sandboxes | ローカル環境はAIごとの小型仮想機械。ホスト領域を共有しない方式、直接共有、複製方式がある | 手元の開発AI向け。通常のDockerコンテナと区別する。直接共有は書込みを即時反映。クラウド版は別条件 [S7][S8] |
| E2B | 環境ごとのFirecracker小型仮想機械。外向き通信は初期設定で有効 | 自作AIから隔離Linuxを呼び出す候補。`allowInternetAccess: false` 等で通信を明示的に制限する [S9][S10] |
| Modal Sandboxes | gVisorまたは個別Linux仮想機械。通信の全遮断・IP範囲・ドメイン制限 | 計算処理の実行候補。方式を指定・確認する。ドメイン制限は試験提供で、全遮断以外ではDNSに制限がないという注意がある [S11] |
| Daytona | 現行v0文書は通常コンテナ、Linux仮想機械、Windows、GPU等の種別を区別。v2文書は初期開発版としてFirecracker構成を説明 | 開発道具や画面操作を含む候補。「Daytonaなら常に小型仮想機械」と扱わず、版と環境種別を指定する [S12][S13][S14] |
| Kubernetes Agent Sandbox | 作成、保存、停止・再開などを管理。低層の隔離は`RuntimeClass`経由でgVisorやKata等へ委ねる | 自社のKubernetes基盤で多数の環境を管理する候補。導入だけでは強い隔離にならない [S15] |
| Azure Container Apps dynamic sessions | Hyper-Vによる分離。組込みコード実行用と独自コンテナ用の実行枠 | Azureで短時間のコード実行を提供する候補。環境の識別子と利用者の対応をアプリ側で管理する [S16][S17] |
| Amazon Bedrock AgentCore Code Interpreter | コード実行用の管理サービス。`SANDBOX`、`PUBLIC`、`VPC`の通信方式 | AWSでのコード実行候補。`SANDBOX`でもS3へ接続できる。通信方式とAWS資源への実行権限を別々に縮小する [S18] |

価格、起動時間、契約上の保証、日本国内だけで処理できるかは本稿では比較していない。資料上の構成が自社の処理に適するかは、下記の試験を行って判断する。

## 4. 見落としやすい条件

### 仮想機械でも共有ファイルの変更は可能

Docker Sandboxesの直接共有では、AIによる編集がホストへそのまま反映される。共有されたGitの自動実行設定や開発設定は、後に人が通常操作をした際の実行経路にもなる。複製方式は成果物を取り込む前に確認する構成に向く。ただし読取り専用の共有は、読める機密情報を減らすこととは別である。[S8]

### 秘密鍵を見せなくても、その権限を使える場合がある

Docker SandboxesのSSH署名代理では、秘密鍵自体はホストに残るが、内部から署名を要求できる。転送は初期設定で有効という説明があり、v3 kitsでは機能の明示要求も条件になる。導入時は実際の構成で確認する。秘密値の窃取防止に加えて、接続先と実行できる操作を制限する必要がある。[S19]

### 外向き通信の「制限」と「全遮断」は違う

E2Bは明示しなければ外へ接続できる。ModalのIP・ドメインの制限とDNSの扱いも同一ではない。AgentCoreの`SANDBOX`も完全な通信断を意味しない。名称から推定せず、接続できる相手と経路を列挙して確かめる。[S10][S11][S18]

### 実行部分だけを隔離しても外部モデルへの送信は残る

以下は情報の流れに基づく本調査の解釈である。ファイルの内容をAIの入力として外部の推論APIへ送れば、コードの実行先を隔離していても、その情報は外へ出る。推論API、外部の道具、ブラウザ、実行環境について、それぞれ何を送るかを設計する。機密情報を外へ出せない場合には、隔離方式とは別に推論先を選ぶ。

## 5. 用途ごとの選定案

| 要件 | 最初に比較する候補 | 選定理由・条件 |
|---|---|---|
| 手元で開発AIを動かす | Docker Sandboxesのローカル版、専用仮想機械 | 作業領域とホストの境界を管理しやすい。共有しない方式か複製方式から検討 |
| 自作AIにPythonやコマンドを実行させる | E2B、Modal、Daytonaの仮想機械種別 | 作成・実行・破棄をAPIで接続する構成を比較。外向き通信は必要範囲へ限定 |
| 自社設備・自社クラウド内に置く | gVisor、Kata、Firecracker。多数の管理にはKubernetes Agent Sandbox | OS更新、通信、認証、監査、状態の破棄を運用できることが前提 |
| 既存のAzure / AWSへ統合する | Azure dynamic sessions / AgentCore Code Interpreter | 既存の認可と接続。ただしコード実行用の権限を管理部から分離 |
| 決まった変換・計算だけを許す | Wasmtime / WASI | 任意のLinuxコマンドを与える必要がない処理で検討 |

この表は本調査の提案であり、全候補を実測して決めた順位ではない。AIモデル自体の推論をGPUで動かす場合は、GPU共有、専有、対応する実行方式を追加調査する。本稿のLinuxコード実行の比較をそのまま適用しない。

## 6. 推奨する役割分担

本調査の構成案では、外側の管理部が利用者、目的、対象データ、時間・費用の上限を確認し、作業ごとに隔離環境を作る。内部には必要なデータの複製と限定した道具だけを渡す。管理基盤のAPIキーやホストのDocker管理用接続口は渡さない。

外部APIへの操作は、必要に応じて隔離環境の外の代理部へ委ねる。代理部は宛先だけでなく、対象資源、読取り・書込み、送信内容を確認する。AIからの任意の通信を中継するだけの代理では、操作範囲は縮まらない。

成果物は外側で差分・内容を確認してから取り込む。停止と記録保存も外側から行う。復元用複製を使う場合は、過去の秘密値や利用者のデータが再出現しないよう、利用者の対応と保存期限を管理する。

## 7. 導入時の受入試験案

以下は未実施の試験案。実データ・実際の秘密鍵を使わず、検証用の環境と架空データで確認する。

| 試験 | 確認する結果 |
|---|---|
| 範囲外ファイルの読取り・書込み、リンク経由のアクセス | ホストの対象外領域へ到達しない。共有領域内で何が読めるかも記録 |
| 未許可の外向き接続、DNS、IPv6、内部IP・クラウドの機械情報取得先への接続 | 禁止した経路を実際に遮断。必要な正規接続は成功 |
| 許可したサービスの別アカウント・別保存先への送信 | ドメインだけでなく、受信主体と操作範囲を制限できる |
| 別利用者の環境ID・公開接続口へのアクセス | 他者の環境へ接続できず、利用者との対応が外側で検証される |
| CPU・記憶・ディスク・出力の大量消費 | 上限内で停止し、他の実行へ過大な影響を与えない |
| 取消し後の子プロセス・常駐処理 | 外側から停止でき、取消し後も動き続けない |
| 隔離機構や通信規則の適用失敗 | 無制限の実行へ切り替わらず停止する |
| 停止・再開、複製、破棄後の再作成 | 利用者をまたいでデータ・認証状態を再利用しない |
| 自動実行設定を含む成果物の変更 | 取り込み前に検出・確認でき、ホストで自動実行しない |
| ログ・監査設定の変更要求 | 内部から外側の制約・原記録を変更できない |

機能試験に加え、対象のOS・仮想化部・製品版の更新と再試験を運用条件にする。Firecrackerの公式資料も、ホストと内部OS、CPUの制御ソフトウェアの継続更新を求める。[S4]

## 出典

すべて公開資料。確認日は2026年10月27日。更新される文書のため、導入時には対象版で再確認する。

- [S1] Linux Kernel, [Landlock: unprivileged access control](https://www.kernel.org/doc/html/latest/userspace-api/landlock.html)。プロセス・子プロセスの権限制限。
- [S2] Docker, [Docker Engine security](https://docs.docker.com/engine/security/)。名前空間、資源制限、管理部の攻撃面。
- [S3] gVisor, [Security Model](https://gvisor.dev/docs/architecture_guide/security/)。システム呼出しの仲介、仮想機械との比較、保護範囲の限界。
- [S4] Firecracker, [Production Host Setup Recommendations](https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md)。KVM、ホスト更新、実行制約。
- [S5] Kata Containers, [Learn](https://katacontainers.io/learn/)。コンテナ管理と仮想機械の組合せ。
- [S6] Wasmtime, [Security](https://docs.wasmtime.dev/security.html)。WebAssemblyとWASIの権限モデル。
- [S7] Docker, [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/)。ローカル・クラウドの区別。
- [S8] Docker, [Isolation layers](https://docs.docker.com/ai/sandboxes/security/isolation/)。小型仮想機械と共有領域、成果物による後続実行の注意。
- [S9] E2B, [Security and compliance](https://e2b.dev/security)。Firecrackerと実行環境ごとの隔離。非公開の監査報告書は参照していない。
- [S10] E2B, [Internet access](https://docs.e2b.dev/network/internet-access)。初期設定と通信制限。
- [S11] Modal, [Networking and security](https://modal.com/docs/guide/sandbox-networking)。実行方式、外向き通信、DNSの制限事項。
- [S12] Daytona, [Sandboxes](https://www.daytona.io/docs/en/sandboxes/)。現行文書の環境種別。公開Markdown版も確認。
- [S13] Daytona, [Isolation](https://www.daytona.io/docs/en/isolation/)。現行文書の境界・種別。公開Markdown版も確認。
- [S14] Daytona, [v2 Isolation](https://www.daytona.io/docs/en/v2/isolation/)。初期開発版のFirecracker構成。
- [S15] Kubernetes SIG Apps, [Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox)。環境管理と低層の隔離の役割分担。
- [S16] Microsoft, [Dynamic sessions in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/sessions)。Hyper-Vと実行枠の種別。
- [S17] Microsoft, [Use dynamic sessions](https://learn.microsoft.com/en-us/azure/container-apps/sessions-usage)。利用者と環境識別子の管理責任。
- [S18] AWS, [Code Interpreter resource management](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-resource-management.html)。通信方式と実行権限。
- [S19] Docker, [Manage credentials](https://docs.docker.com/ai/sandboxes/configuration/credentials/)。SSH署名代理の条件と権限。
