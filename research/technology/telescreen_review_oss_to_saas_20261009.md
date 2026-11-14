# 独立レビュー：保存データのSaaS検査・問題管理

実施日：2026-10-09。対象：[SaaS報告](telescreen_related_saas_dlp_20261009.md)と[取得台帳](telescreen_related_saas_sources_20261009.json)。保存した公開本文の処理境界、問題の状態、再検査条件、保持条件を照合した。契約の監査、実顧客データの走査、通信計測、精度評価、実環境の削除・再検査試験は実施していない。

## 指摘と解消

**S-R1・重要：elbaの保持条件の誤記。** 初稿の「終了後60日以内」「監査ログ最大2年」は取得原本に支持がなかった。`elba_privacy.txt`のData retention節とGoogle API Data Usage節は、顧客が終了時に削除を要求すれば直ちに、要求がなければサービス終了30日後に全顧客データ（Google含む）を削除すると説明する。請求・会計記録の10年は別の目的・別の記録である。[公式プライバシー方針](https://www.elba.security/privacy-policy)。

著者が本文と台帳の製品別保持説明を訂正した。訂正後の本文と台帳を再照合し、終了時の削除規則と、未確認の運用中の一致箇所・監査ログ保持を分離したことを確認した。この指摘は解消済み。

## 支持を再確認した重要境界

| 対象 | 原本照合の結果 |
|---|---|
| Teleskope Outpost | 標準遠隔分類では抽出テキストを専用処理先へ送信。局所分類はGPUと個別調整を要し、属性・検出結果は送信する。管理者の明示的なpreview要求で一致箇所の文脈が返る。完全自社配置とOutpostを同一視していない。[構成](https://docs.teleskope.ai/setup/deployment/architecture.md)、[Outpost](https://docs.teleskope.ai/setup/deployment/outpost.md) |
| Teleskope問題状態 | Open / In Progress / Resolved / Ignored、通知・待機・操作・状態変更を確認。方針変更による保管済み扱いや手動解決を、原本の再検査成功と断定していない。[Policy Maker](https://docs.teleskope.ai/the-platform/policy-maker) |
| Nightfallの集約 | FindingとEvent、同じファイルと異なるファイルの重複抑制、Driveの本文からの除去・完全削除・ゴミ箱移動の違いを確認。全保存先共通の秘密単位問題IDや全接続先の自動解決保証へ一般化していない。[重複仕様](https://help.nightfall.ai/dashboard/sdp_events/deduplication) |
| Nightfallの保持 | 伏字前findingsの管理者閲覧・出力範囲30日と、Developer APIアップロードファイルの24時間削除を異なる経路として記述。全原文ファイル30日保存や指紋のみ保存とは説明していない。[Events](https://help.nightfall.ai/dashboard/sdp_events)、[API](https://help.nightfall.ai/developer-api/faqs/unique_features) |
| Strac・Candor | 自社配置・非送信は提供者の公開説明として記述し、内部実装の独立検証とはしていない。第三者モデル、日本語性能、問題の再発規則等の未確認領域を残している。 |
| Harmonic | 学習不使用と、推論・観測・記録を区別。保存データの巡回完成品とはしていない。[EULA](https://www.harmonic.security/harmonic-end-user-license-agreement) |

任意の追加確認事項として、Teleskope局所分類でも外部管理系へ接続設定・検査元の認証情報を含む制御用通信がある。現稿の「全処理が局所ではない」という結論と矛盾しないが、導入時には本文だけでなく認証情報の保存場所・権限も確認する。またelbaのEU/US中核保存環境は、機能に応じた補助保存・AI処理の場所まで固定する保証ではない。どちらも原文不保持と別の境界である。

## 取得原本・統合稿の確認

台帳81資料の保存原本と抽出本文について、記録された全ハッシュを再計算し、不一致はなかった。gzip圧縮の未展開本文、500バイト未満の抽出本文は検出しなかった。主要な処理・保持・再検査の主張に使う原本は本文を読めており、ログイン画面だけを仕様本文として使う例は確認しなかった。ハッシュ一致・HTTP成功は製品機能の検証とは別である。

[統合稿](telescreen_related_systems_20261009.md)のTeleskope局所分類とNightfall重複・再検査条件も照合し、SaaS稿と矛盾する重要な保証は確認しなかった。現稿に残る必須訂正はない。
