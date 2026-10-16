# 文書担当から遠隔環境稿への独立レビュー

確認日：2026-10-15。対象：[遠隔環境稿](online_pii_remote_environments_20261015.md)・[取得台帳](online_pii_remote_sources_20261015.json)。公開原本の主要境界と、公式ページの再取得で確認した。実製品操作・端末残存・通信の試験ではない。

## 判定

**重要な結論の訂正は見つからなかった。** 補足1件と用語修正1件を提案する。すべての製品ページ・版・契約の網羅監査ではない。

| ID | 程度 | 指摘・提案 | 根拠 |
|---|---|---|---|
| R-R1 | 補足 | AVD/Windows 365のWeb画面保護で、同じテナントが管理する端末は当該Intune MAM構成の対象外と明記すると導入判断が容易。個人端末、別組織管理端末、ネイティブWindows Appを区別する | 保存MS01.txt L157–169、L222–231、L469。別組織管理はEdge147以降等の条件 |
| R-R2 | 表記 | 方式表NVR行「中央の原ファイル不保存」は、比較意図から「端末への原ファイル非配布」の誤記ではないか確認する | 本文は中央でWebを実行し描画命令を送る説明。中央で原本を保存しない保証を比較していない |

## 支持された主要境界

- **AWS提供予定**：AW02原本および公式再取得で2026-10-29の新規顧客停止、既存顧客継続を確認。サービス全体の終了と記載していない。代替WorkSpaces Applicationsは画素転送を行えるが、下流SSO、方針のライブ更新、統合監査等には追加設定/差がある。稿が完全同等と断定しないのは適切。[公式変更案内](https://docs.aws.amazon.com/workspaces-web/latest/adminguide/workspaces-secure-browser-maintenance-mode.html)
- **画素と原文非送信**：AW07はHTML/DOM非送信、AW02は画像転送を説明する。許可された転送・表示内容まで消えるとしない境界は妥当。
- **MSの異なる保護機構**：MS01は特定OS機能/APIによる画面取得制限であり、転送制御を別に必要とする。MS07はPreview、物理Windows11上のWindows Appのみ、ハードウェア必須時は不適合端末を拒否、そうでなければソフトウェア保護への切替を説明する。Web全般へ一般化していない。MS03/MS04/MS05/MS06の新規環境の既定値と既存環境の区別、透かしと撮影阻止の区別も支持。[画面保護](https://learn.microsoft.com/en-us/azure/virtual-desktop/screen-capture-protection)、[Display Protection](https://learn.microsoft.com/en-us/windows-365/enterprise/windows-cloud-display-protection)
- **Cloudflare**：CF02.txt L962–1022に各操作の既定許可、L1001に遠隔側への保存は別制御、L1010に第三者クラウド/別隔離ページからの再送を説明。CF04.txt L892はNVRが動画でなく描画命令、L947–950は隔離中の宛先IP等の規則制約。稿はこれらを区別する。[方針](https://developers.cloudflare.com/cloudflare-one/remote-browser-isolation/isolation-policies/)、[制約](https://developers.cloudflare.com/cloudflare-one/remote-browser-isolation/known-limitations/)
- **Island**：IS02 PDFはローカル保存領域の暗号化、IS03 PDFはクリック/キー入力/画面等の記録を説明。端末処理を含む管理ブラウザーと遠隔実行を分離し、記録の個人情報保持経路にも言及するのは適切。
- **研究運用の境界**：OS02は通常研究者の集計結果・ログと、許可を持つ運用担当者等の患者データアクセスを分ける。OS03末尾Level4は訓練済み出力確認者による独立二重審査を明記。稿の「誰も原データを読めないとはしない」は支持される。[アクセス方針](https://docs.opensafely.org/data-access-policy/)、[データ階層](https://docs.opensafely.org/security-levels/)

NHS三文書とOS04は直接原本ではなくWeb取得ツール抽出であることを稿と台帳が明記している。NHSのDownloadsを仮想デスクトップ内の領域として扱うのは適切。ただし全契約条件の現在の適用、実際のOSによる画面阻止、出力審査運用の実効性は独立実証していない。本文でも規則上禁止と技術上強制を区別している。

## 改善後の再確認

2026-10-15、R-R1/R-R2の反映を本文で再確認した。Web画面保護の同一テナント管理端末の非対応と、個人端末・他組織管理端末・ネイティブアプリの違いを明示し、NVRの比較語も端末への原ファイル非配布へ修正済み。確認した原本との不整合は残っていない。
