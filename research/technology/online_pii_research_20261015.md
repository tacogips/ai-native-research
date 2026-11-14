# 個人情報を配布しない利用と出力審査の関連研究

確認日：2026年10月15日。2025〜2026年の査読論文、先行公開、研究環境の仕様を中心に確認した。認証を強くする研究と、原文を配布せず計算や閲覧だけを許す研究は目的が違う。ここでは後者と、外へ出す結果の管理を主に扱う。

## 論文と仕様の位置付け

| 研究・仕様 | 時点と種別 | 仕組み | 集中管理への示唆と限界 |
|---|---|---|---|
| *PICACHV: Formally Verified Data Use Policy Enforcement for Secure Data Analytics* | USENIX Security 2025、査読付き会議論文 | 分析処理の計画にデータ利用方針を適用し、許可する計算・結果を管理。形式的な証明と隔離計算環境を組み合わせる | 保管場所だけでなく「どう使えるか」を実行時に制御する。ブラウザーの保存禁止や全処理の安全性を証明する研究ではない |
| *A Multi-Language Toolkit for the Semi-Automated Checking of Research Outputs* | IEEE Transactions on Privacy 2025。先行公開は2022年、確認版は2025-04-29のv4 | SACROという出力審査補助。集計・図・統計モデルの検査結果と理由を整理し、人による審査へつなぐ | 元データを外へ出さなくても出力で漏れるため、持ち出す結果を審査する。補助ソフトだけで任意の外部送信を遮断するものではない |
| *A Hierarchical Approach for Assessing the Vulnerability of Tree-Based Classification Models to Membership Inference Attack* | Transactions on Data Privacy 19巻1号、2026年。先行公開の確認版は2025-06-12のv2 | 学習条件と学習後の木構造から危険なモデルを絞り、計算負荷の高い攻撃試験へ回す | 学習済みモデルも持出し審査の対象。木系分類器が対象で、LLM一般や全攻撃に対する安全性証明ではない |
| *RELEASE-AI: A lifecycle framework for artificial intelligence development and disclosure control in trusted research environments* | 先行公開2025-09-19、大学保管庫への登録2026-03-31。査読前資料 | 設計から開発・評価・出力審査・公開までの役割と手順を整理する | 完成後だけでなく、最初に持ち出せる成果物を決める参考。今回確認したのは著者所属機関の公開説明で、PDF全文は取得できなかった |
| 「ターゲティング広告配信におけるデータクリーンルームの４機能とその個人情報保護法の下での評価」 | 猪谷誠一。誌面年2025、J-STAGE公開2026-03-27、査読付き研究ノート | 広告向けの機能を4類型、データの流れを23パターンに分けて法的に分析 | 原文を直接見せないことだけで義務が消えると考えない。著者の広告分野の分析を、全クリーンルームへの一律の法的結論に広げない |
| *TrustDS: policy-compiled governance and verifiable evidence for cross-cloud marketplace analytics under explicit security assumptions* | Scientific Reports、2026-04-18、確認ページに更新表示あり | 同意・用途・保存地域・保護予算を実行計画と許可状態へ反映し、結果公開時の証拠を残す | 許可取消しと証拠を処理途中にも反映する参考。新しい暗号方式や任意の計算基盤に対する完全な安全性証明ではない |
| *Standard Architecture for Trusted Research Environments*（SATRE） | 仕様2.0.1、2026-07-23。論文ではなく共同の設計仕様 | 情報管理・計算環境・データ管理・支援・連携の要件。出力と学習成果物の取扱いも含む | 閲覧・計算・持出し・責任分担をまとめて設計する基準。法令や製品認証と同義ではない |

原論文・公式資料：[PICACHV](https://www.usenix.org/conference/usenixsecurity25/presentation/chen-haobin)、[SACRO](https://arxiv.org/abs/2212.02935)、[木系モデルの研究と2026年掲載情報](https://arxiv.org/abs/2502.09396)、[RELEASE-AI](https://uwe-repository.worktribe.com/output/15864836/release-ai-a-lifecycle-framework-for-artificial-intelligence-development-and-disclosure-control-in-trusted-research-environments)、[猪谷論文全文](https://www.jstage.jst.go.jp/article/jicp/9/2/9_63/_html/-char/ja)、[TrustDS](https://www.nature.com/articles/s41598-026-48740-8)、[SATRE](https://satre-specification.readthedocs.io/en/main/)。

## 本文から確認した実装上の条件

### PICACHVの保証は対象と仮定を伴う

関係代数という表の計算を表す枠組みに利用方針を対応付け、Polarsへ組み込んで評価している。隔離計算環境が安全であることを仮定し、その環境自体の脆弱性やハードウェアの観測による攻撃は対象外。TPC-Hでの評価には未対応機能を使う問い合わせを含めず、方針ファイルの読込み時間も端から端までの測定から除外する。実行計画を作る計画器は正しく動くと信頼し、実行可能な利用方針も人が用意する前提がある。処理全体の完全な検証は将来課題とする。実験上の追加負荷を、任意の業務アプリへそのまま一般化しない。保管庫に全データを集めるだけではなく、計算計画で用途を制限する点が重要である。[本文§3・§7](https://www.usenix.org/system/files/usenixsecurity25-chen-haobin.pdf)

### SACROは人による審査と一緒に使う

Python、R、Stataで生成する結果の検査を補助し、問題と軽減策、判断履歴を整理する。論文は人による確認を置き換える目的ではないと明示する。集計表の件数だけでなく、他の結果との組合せによる開示も考える必要がある。処理機が自由に通信・書出しできる状態は別に制限する。[2025年版本文](https://arxiv.org/pdf/2212.02935v4)

### モデルを持ち出す場合も原文の持出しとは別に審査する

木系モデルの研究は、決定木、Random Forest、XGBoostについて、学習条件を先に選別し、学習後の構造を調べ、その後に学習データへの参加を推測する攻撃試験を行う。軽い検査で安全を認定するものではない。論文はモデルの予測精度と漏洩危険が同じ指標ではないと示す。2026年の掲載情報は確認できたが、雑誌PDFはHTTP403のため、精読には公開先行版を使った。掲載版との差分比較はしていない。[先行版v2](https://arxiv.org/pdf/2502.09396v2)

### 日本の法的分析では機能ごとのデータの流れを追う

猪谷論文はデータ拡充、統計・モデル作成、広告への利用、効果測定を分ける。第三者に原文を表示しないという技術上の説明と、データを取り扱う主体・提供の法的評価は別という示唆がある。社内だけの閲覧基盤、広告連携、共同分析を同じ条件で判断しない。[本文§4〜§6](https://www.jstage.jst.go.jp/article/jicp/9/2/9_63/_html/-char/ja)

### TrustDSは方針と許可状態を処理へ結び付ける

許可された目的・同意・地域等を処理計画へ変換し、結果の公開時点に使った状態を証拠と関連付ける。評価には公開された複数分野のデータと、別に限定した二者間の計算試験を使う。全処理が暗号学的に安全だという一般保証や企業での運用実績とは区別する。公開本文のデータ提供説明には、成果物の保管先を将来の登録として述べる箇所もあり、再現性が独立に確認できたとは扱わない。[本文の貢献・評価・データ提供説明](https://www.nature.com/articles/s41598-026-48740-8)

## 2026年の仕様と運用への取り込み

SATRE 2.0.1は版の日付が2026年7月23日。出力管理3.3.07は手作業で確認できない出力への方針を必須とし、3.3.09は出力審査基準と判断を機械可読な記録として保持することを述べるが、正式な重要度の区分はOptional（任意）である。本文のshouldと、仕様上の必須・推奨・任意の区分を分け、すべての出力を人が目視すれば足りるとも、学習済み係数なら審査不要とも考えない。[仕様PDF](https://satre-specification.readthedocs.io/_/downloads/en/stable/pdf/)

組織の分析環境では、原データを移さず計算を持ち込む、結果を仮置きする、出力審査をする、許可した成果だけを公開する流れが参考となる。SACRO等はこの出口の補助に使い、認証・権限・ネットワーク・ファイル書出し制御は環境側に持たせる。

## OTPと認証の標準

NIST SP 800-63B-4は、ワンタイムパスワード（OTP）を使い捨ての認証情報として扱う一方、手入力するOTPは偽の認証画面への誘導に耐える認証ではないとする。使い捨てであることと、本人が正しいサイトで認証したことを結び付ける性質は別である。高い保護が必要な職員向けには、FIDO/WebAuthn等によるフィッシング耐性のある認証を比較する。ダウンロード禁止、期限、再認証、利用許可の取消しは別に設計する。[NIST認証標準](https://pages.nist.gov/800-63-4/sp800-63b.html)

メールで届く確認コード、認証器のOTP、短命なAPI認証情報、データを置き換える代替IDは別物である。同じ「トークン」という呼称だけで、原文の非配布や本人認証の強さを判断しない。

## 保存と確認範囲

[取得台帳](online_pii_research_sources_20261015.json)に公開URL・取得日時・原本と抽出本文のSHA-256・失敗を保存した。PICACHV、SACRO、木系モデル先行版はPDF、猪谷論文とTrustDSはHTML全文、SATREはPDF本文を確認。RELEASE-AIは公開書誌・概要のみの確認に限定する。公開PDFの取得失敗を、本文精読済みや保守終了の証拠としない。
