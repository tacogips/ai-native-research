---
title: "AI-native 企業・専門サービス・既存企業の転換と失敗事例"
author: codex
kind: survey
status: research
created: 2026-10-05
verified: 2026-10-05
---

# AI-native 企業・専門サービス・既存企業の転換と失敗事例

[専門用語の日本語説明](../glossary_ja.md)。製品名・論文の原題・コードは原表記を保持する。

2026年10月6日に[35の企業・サービス群の比較](ai_native_company_cases_expanded_20261006.md)と[企業の法務・経理・人事の20事例](enterprise_legal_finance_hr_cases_20261006.md)を追加した。本資料は2026年10月5日時点の報告として読む。現行のHarper、Crosby、Pilot、Mercor等の説明は新しい比較を参照。

## 対象と読み方

Apple Notes の今日のコンソール写真の⑤「企業事例・全社展開」を再調査した。写真には Harper / Panta、法務・会計・保険の成果まで担うサービス、国内外の既存企業、品質低下・撤回・事業停止が指定されている。製品の自己紹介、当事者の導入発表、比較研究を分け、自律化の範囲と人の責任を確認した。

AI-native はこのレポートでは「AI が業務・サービスの構成に組み込まれている企業」を含む。AI-only（全企業活動が人なしで完結）の達成を意味しない。各社の公表値は独立監査された共通 benchmark ではない。設計への含意は本調査の推論である。

## 1. Harper: 保険仲介そのものを運営する

Harper は米国の商業保険 brokerage。YC 掲載では完全自律 brokerage を目標として記述し、Harper Hub による form、carrier 探索、顧客対応を説明する。到達済みの無人運営と読み替えない。[YC の企業・launch 掲載](https://www.ycombinator.com/companies/harper)

公式 privacy policy は、文書分類・抽出、内部 review 用メール案、task・follow-up 整理、従業員の通話支援を AI の用途として示す。最終判断と保険成立には licensed professionals / carriers の確認を残す。内部業務由来の fine-tuned モデル、golden dataset、judge、monitoring、高リスクの human review も記載する。[Harper policy](https://www.harperinsure.com/privacypolicy)

**推論:** 参照すべき単位は、文書からの抽出だけではなく、顧客・案件・必要書類・相手先回答・次の task・例外をつなぐ業務状態。専門家が承認した修正を学習へ反映しても、本番評価・変更管理は別に置く。公開資料から自律完了率や誤成立率、独立した監査結果は確認できない。

## 2. Panta: 工程間の coordination と人の gate

写真の Panta は、保険仲介の **pantainsure.com** に対応する YC W26 の企業を対象にした。同名の指数投資プラットフォーム panta.ai やドイツの PANTA OS を混ぜない。[YC 企業掲載](https://www.ycombinator.com/companies/panta)

創業者の launch 説明では、Mac Mini 上の AI operators が file system、portal、form、email、call 等を扱う。申請、follow-up、保険証明、更新を工程として挙げ、高リスクには人の approval gates と audit logs を持つと説明する。これは当事者の実装説明であり、ログや source code を第三者が検証した結果ではない。[同 launch 掲載](https://www.ycombinator.com/companies/panta)

公式サイトは免許を持つ broker の review と、適合する案件で初回見積りの median 48時間を掲げる。分母が全案件ではなく in-appetite accounts であることに注意する。YC では2025年創業、公式サイトでは Est. 2024 と表示され、創業年の差は未解決。[Panta 公式](https://pantainsure.com/)

**推論:** 「書類を生成した」ではなく「誰から何が返ってきたら次工程へ進めるか」を状態機械にする点が重要。端末上の万能エージェントを再現するより、初期は portal adapter、型付き Action、callback、期限、例外 queue、承認済み payload の照合を設計する。大量同時処理や operations entirely automated という表現は、自社導入で実証するまで性能目標と区別する。

## 3. 法務・会計・保険のサービス形態

| 事例 | 提供形態と確認した境界 | 設計の参照点 | 公開証拠の限界 |
|---|---|---|---|
| Crosby（法務） | AI と lawyers-in-the-loop の hybrid law firm。2025年6月17日の発表で1,000件超の契約 review と median 58分を公表 | 契約 review の成果物と弁護士判断を一体で提供 | 2025年発表時の自己申告。現在の SLA、日本法、自律率は不明。[公式発表](https://crosby.ai/blog/introducing-crosby-the-worlds-first-hybrid-law-firm) |
| Basis + Baker Tilly（会計） | Basis は会計向け agent platform。Baker Tilly は2026年4月28日に managed services 内の collaboration を発表し、取引処理、仕訳支援、照合、分析等を対象とする | ledger・証憑・reconciliation・review-ready output と人の oversight | 提携発表は全顧客への展開完了や自律決算の実証ではない。[導入当事者発表](https://www.bakertilly.com/news/baker-tilly-collaborates-with-basis)、[Basis](https://www.getbasis.ai/) |
| Harper / Panta（保険） | 自ら brokerage を運営し内部 AI を利用。高リスクに専門家の責任 | task、資料、顧客連絡、審査、成立、更新をつなぐ | licensed human gate を持つため AI-only の証明にしない。上記資料参照 |
| Harvey / LegalOn（法務 tool） | review・research・workflow を専門家へ提供 | Word、playbook、出典、bulk review、既存案件との接続 | SaaS の提供と法務サービスの法的責任を混同しない。[法務比較](../legal_domain/ai_native_operations_20261005.md) |

「成果まで担う」には、tool SaaS、managed service、免許を持つ事業者の内部自動化という異なる契約形態がある。実装に共通する論点は、人の関与を task ごとに定義し、評価・例外・監査を業務状態と接続すること。公開資料から各社が同じ段階移行方式を採用していると断定はできない。

## 4. 既存企業の転換: 国内外

### 国内: パナソニック コネクト

2026年7月29日の公式発表は、2025年度に78.8万時間・総労働時間3.4%の削減、月間 unique user 61%を報告する。50の社内システムの構造化データと非構造化データを整備し、2026年から生成 AI と接続する実装段階を説明する。2030年10%削減は目標であって実績ではない。[公式発表](https://news.panasonic.com/jp/press/jn260729-1)

**推論:** 全社 chat 導入だけでなく、データの統合・社員の習熟・業務への接続・削減時間の再配分が必要。発表値は企業の推計であり、AI が全社業務の3.4%を無人完了した割合とは解釈しない。

### 国内法務: 森・濱田松本 / Harvey

2024年の当事者発表は Harvey との提携、Vault、期間を伴う日本市場での API の exclusive 利用、文書 review・draft・research への利用を説明する。日本の法律実務と汎用海外 tool の接続事例だが、自社の日本語精度・契約条件の証明ではない。[事務所の公式資料](https://www.morihamada.com/en/news/articles/2024/159.html)

### 海外法務: Harvey の企業法務顧客

Harvey の2025年12月の記事は Repsol の96% adoption と弁護士当たり週4〜6時間削減、Deutsche Telekom の週5時間程度等を紹介する。これらは vendor 掲載の顧客推計であり、独立した対照実験ではない。[公式事例](https://www.harvey.ai/blog/how-harveys-legal-team-uses-harvey-to-work-smarter)

**推論:** 自社の rollout では業務 owner を決め、use case、期待品質、教育、利用範囲、作業と待ち時間、削減時間の使い道を同時に測る。adoption は正しい判断の割合ではなく、時短は自律完了率ではない。

### 海外サポート: Klarna

2025年の Form 20-F は AI assistant が customer service chats の80%を処理したと記載し、人を希望する顧客への対応も継続する dual-track を説明する（PDF p.187、本文 p.184）。また生成 AI を credit underwriting に利用しないと記載する。[会社の年次報告書](https://s205.q4cdn.com/644747736/files/doc_financials/2025/q4/Klarna-Group-plc-20-F-2025.pdf)

**推論:** CS の高い利用率から与信までの包括的自律化を推定しない。channel・task ごとに、AI への配分と人の対応を別に測定する。会話数ベースの80%は正しく解決した全業務の80%という値ではない。

## 5. 失敗・反動・事業停止

| 類型 | 証拠と時点 | 自社設計に反映する点 |
|---|---|---|
| 品質低下・人の再導入 | Klarna CEO が2025年6月に人による service を語った報道がある（二次）。現行の一次資料で確認できるのは上記20-Fの dual-track | 「AI 撤回」「全て成功」の二択にしない。人への切替・苦情・再問合せを測る。[報道](https://techcrunch.com/2025/06/04/klarna-ceo-says-company-will-use-humans-to-offer-vip-customer-service/) |
| tool 利用で実作業が遅くなる | METR の2025年 RCT は熟練 OSS 開発者16人、246 task で19%長い所要時間。対象は early-2025 tools と特定 repo | 主観の時短を実測と分ける。法務への率の転用は不可。[研究者の解説](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)、[論文](https://arxiv.org/abs/2507.09089) |
| 現行効果の推計が不安定 | METR は2026年2月の追跡実験で選択 bias と並行 agent 利用時の時間測定の難しさを説明 | 古い19%を2026年全般の効果として引用しない。現在の task と利用形態で比較を再設計する。[追跡報告](https://metr.org/blog/2026-02-24-uplift-update/) |
| AI 製品の事業化・継続に失敗 | Tome の公式 help 掲載は Slides を2025年4月30日に sunset、事業として成立させられなかったと説明。今回は検索サービスに残る公式本文抜粋で確認、直接取得は404 | export、data portability、依存サービスの終了、契約の exit を設計する。[旧公式告知（現在404）](https://tome.app/help/en/articles/10744234-tome-slides-is-sunsetting-on-april-30th-2025) |
| cloud 依存機能とデータアクセス終了 | Humane の公式 support 掲載は consumer Ai Pin の server 接続を2025年2月28日に終了し機能・data access が失われると説明。同様に検索掲載の抜粋のみで確認、直接取得は名前解決失敗 | self-hosting と cloud 利用の差だけでなく、正本・export・移行期限を点検する。[旧公式告知（現在取得不可）](https://support.humane.com/hc/en-us/articles/34374173951373-Important-Update-for-Consumer-Ai-Pin-Customers) |

Tome / Humane は AI-only company の自律業務の失敗事例ではなく、AI 企業・製品の事業継続リスクの反例である。品質やモデルだけが停止原因だったとの因果関係はこの資料から確定しない。Tome Slides の終了を法人そのものの消滅とも同一視しない。

## 6. この repo の設計へ持ち帰るもの

1. **判断ログ:** 案件、入力版、モデル版、根拠、承認、実行、結果をつなぐ。広告の「完全自律」より、対象 task と高リスクの gate を検証する。
2. **例外対応:** 欠落資料、回答なし、曖昧な相手、複雑な条件、訂正、期限超過を人へ返せる状態にする。
3. **工程間の引き継ぎ:** 一つの生成物より、依頼→確認→承認→実行→回収の状態・ID・責任を持つ。
4. **評価に応じた自律度:** 下書きから限定自律へ進めるのは本調査の設計案。企業の削減率をそのまま昇格基準にしない。
5. **全社展開:** 品質、工数、教育、運用 owner、削減時間の再配分と data readiness を一緒に管理する。
6. **終了への備え:** 正本、export、adapter の置換、credential 失効、人の業務継続を受入条件にする。

公開情報から「会社全体が AI のみで継続運営できる」との強い証拠は今回得られていない。一方、専門家の gate を残しつつ coordination と定型処理を広く自動化する事例は、法務を起点とする[業務設計](../legal_domain/ai_native_operations_20261005.md)の具体的な比較対象になる。
