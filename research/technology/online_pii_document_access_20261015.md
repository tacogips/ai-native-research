# 個人情報文書をオンライン閲覧に限定する方式と製品

調査日：2026-10-15。公開公式文書のみ。有償環境の操作、通信監査、端末残存調査は実施していない。未確認は機能の不在を意味しない。

## 結論と要件の分け方

**通常のファイル保存・印刷・同期を禁止し、認証した相手だけにオンライン閲覧させるサービスは存在する。ただし「端末へ情報が一切届かない」「画面撮影まで完全禁止」とは異なる。** 原本ファイルの取得、表示用データの受信、端末への永続保存、画面の複製を別に扱う必要がある。

閲覧する以上、表示情報は端末に届く。Boxの公開表示ライブラリもAPIから変換済み表示データ等を取得すると説明する。原本の保存を許さない設定だけでは、ブラウザーの一時領域、表示データ、端末の記録までゼロとは証明できない。GoogleとDigifyも別手段の内容再共有・画面複製への限界を明記している。[Box表示方式](https://github.com/box/box-content-preview/blob/master/README.md)、[Googleの制限](https://support.google.com/drive/answer/2494893?hl=en)、[Digify画面保護](https://help.digify.com/en/articles/2820319-screen-shield-with-screenshot-protection)

比較対象は次の6系統。SharePointとOneDriveは同じ管理機構として数えた。VDR（Virtual Data Room：権限と閲覧履歴を管理する仮想資料室）やDRM（Digital Rights Management：複製や利用の権限を制御する技術）は、いずれも設定範囲の確認が必要である。

| 系統 | オンライン限定に使う機能 | 認証・失効の要点 | 要求との隔たり |
|---|---|---|---|
| Box | Previewer、共有権限、透かし | Viewerは保存可。権限の重複・モバイル例外を確認 | Previewerでも管理者設定次第でモバイルのオフライン保存可 |
| SharePoint / OneDrive | サイト単位BlockDownloadPolicy、非管理端末の制限、共有リンク単位制限 | 認証と端末条件は別機構。所有者・特定グループの除外可 | サービス側app-onlyアプリは方針除外。全API経路の禁止ではない |
| Dropbox DocSend | 閲覧リンク、保存無効、宛先許可、期限 | メール検証リンクは最大1時間、同一端末。認証済み状態は2週間 | TXT/RTF/圧縮ファイル等は保存でしか閲覧できない |
| Digify | 保存・印刷禁止、宛先指定、期限、Screen Shield | メールOTP、厳格な再検証、利用者単位失効 | 画面保護にOS/ブラウザー依存の例外。PPADは保護付き保存の別方式 |
| FINAL CODE（FinalCode） | Browser Viewの原ファイル取出し・コピー・印刷権限 | メールOTP、閲覧者・期限設定 | 暗号化したBrowser Viewファイルを配布。ローカルファイル皆無ではない |
| Google Drive / Docs等 | 利用者役割別の保存・コピー・印刷制限、共有解除 | 外部訪問者はメールPIN、7日後再検証 | PIN共有だけでは保存禁止にならない。別手段の再共有は防ぎきれない |

出典は以下の各節。価格順位・精度順位ではなく、公開条件の比較である。

## Box：ViewerとPreviewer、透かしを混同しない

Viewerは閲覧に加えてダウンロード・印刷できる。Previewerは保存・印刷を許さない閲覧用の役割で、Business/Enterpriseの管理者が有効化する。追加役割はフォルダー向けで、単一ファイルへの招待はEditor/Viewerのみ。複数の権限を持つ場合は緩い方が優先される。Previewerのモバイルでのオフライン保存を許す管理設定も存在する。**「Previewerにした」という一条件だけで端末内保存皆無としない。** [権限表と例外](https://support.box.com/hc/en-us/articles/360044196413-Understanding-Collaborator-Permission-Levels)（保存原本 `box_roles.txt`）

透かしは抑止・追跡の機能。Viewerは透かし付きファイルを保存でき、Owner等は原本を保存できる。透かし付きでもオフライン利用できる場合がある。表示対応形式も異なる。Boxの表示用開発ライブラリには保存ボタンの表示設定と権限範囲の指定が別々にあり、ボタン非表示を認可と同一視しない。独自組込み時は透かし付き保存の `downloadWM` 設定も別途確認する。[透かし](https://support.box.com/hc/en-us/articles/360044195253-Watermarking-Files)、[表示用ライブラリ](https://github.com/box/box-content-preview/blob/master/README.md)

Box Previewは対応形式・容量の制約があるため、表示不能時に原本の保存へ誘導しない運用が必要。今回Boxの外部閲覧者OTP、すべてのAPI/管理者アクセス、失効後の既存キャッシュ削除までは確認していない。[Previewの制約](https://support.box.com/hc/en-us/articles/360044195013-Introducing-Box-Preview)

## SharePoint / OneDrive：三つの異なる制御

**サイト単位**のBlockDownloadPolicyはEntra Conditional Access（利用者・端末等の条件に応じた接続制御）なしで適用できる。ブラウザー内の利用に限定し、保存・印刷・同期、Officeデスクトップアプリ等を制限する。サイト間移動も禁止する。所有者・指定グループの除外設定があり、読取り専用は追加設定。サービス内部でapp-onlyとして動くウイルス検査・検索等は例外なので、別アプリの権限付与も管理する必要がある。[公式仕様](https://learn.microsoft.com/en-us/sharepoint/block-download-from-sites)（`ms_block.txt` L27–55）

適用にはSharePoint Advanced Managementの前提条件を満たす必要がある。現在の公式資料は指定の基本契約に加え、少なくとも1人へのMicrosoft Copilotライセンス割当、またはSAM Plan 1追加契約等の経路を列挙する。管理者権限・PowerShell環境も必要。個別契約の解釈を価格推奨に広げない。[最新の前提条件](https://learn.microsoft.com/en-us/sharepoint/sharepoint-advanced-management-prerequisites)

**非管理端末だけ**を制限する方法はEntra Conditional Accessを利用する別方式。ブラウザー限定で保存・印刷・同期・アプリ接続を制限できるが、管理端末は原則としてフルアクセスとなる。対応OS/ブラウザー、編集許可、旧式認証の遮断が重要で、旧式のアプリは端末制約を強制できない場合がある。プレビュー不能ファイルの扱いを許可側にすると保存可能になる条件もあるため、全形式を閲覧不能にしてよいかを決める。[端末条件と例外](https://learn.microsoft.com/en-us/sharepoint/control-access-from-unmanaged-devices)

**共有リンク単位**にもBlock downloadがあり、表示可能な対応形式を対象にする。管理者の `BlockDownloadLinksFileType` はOfficeのみ/表示対応形式の範囲を変える。サイト全体や他の権限経路まで同時に閉じる制御とは同一ではない。[リンク設定](https://support.microsoft.com/en-us/onedrive/block-downloads-for-view-only-files-in-sharepoint-and-onedrive)

画面撮影、管理者のエクスポート、バックアップ等の全取得経路、既存コピーの回収はこのダウンロード方針だけから保証できない。これは公開方針の適用範囲からの推論であり、回避の操作試験結果ではない。

## DocSend：メール欄への入力と実際の検証を分ける

Allow downloadsを無効にし、期限と許可宛先を設定できる。Require emailへの入力とVerify emailのメール検証は同じではない。検証機能はAdvanced/Advanced Data Rooms/Enterprise向けで、検証メール内のリンクは最大1時間有効、最初に開いた同一端末での操作を求める。ただし訪問者の検証済み状態は2週間続き、端末・メール変更時等を除き追加リンクで再検証不要。**毎回OTPを要求する設計と同一ではない。** [認証仕様](https://help.dropbox.com/share/dropbox-docsend-email-authentication)、[共有設定](https://help.dropbox.com/share/dropbox-docsend-link-settings-in-content-library)

許可するメールアドレス/ドメインの制限も別途設定し、認証と組み合わせる。転送されたURLの所持だけで個人を特定しない。[宛先の制限](https://help.dropbox.com/share/dropbox-docsend-restrict-access-allow-or-block-viewers)

重要な例外はdownload-only形式。TXT/RTF、圧縮形式、40MB超の表計算等は表示できず、Allow downloadingが有効になる。透かしも非対応。オンライン限定なら対象を事前に表示可能な形式へ変換するか受入れを拒否する必要がある。一般に許可済みの保存コピーは、その後のリンク停止で回収できるとは限らない。[公式の形式一覧](https://help.dropbox.com/share/dropbox-docsend-download-only-files)

## Digify：OTPと宛先指定を組み合わせる

Document Securityは保存と印刷を別途制限し、宛先指定とStricter email verificationでアクセスごとのメール確認を選べる。保存を許すと印刷も許可される点に注意する。[送付設定](https://help.digify.com/en/articles/662954-sending-files-with-document-security)

メールOTPはパスワードを持たない既存受信者/資料室ゲストの既定経路。管理者によるログイン方式の制限は自社チームの会員に適用され、外部受信者・ゲストには適用されないと明記される。内部設定を外部共有にも自動適用と考えない。Security Presetsで送付設定を固定できるが、設定変更後も過去に送ったファイルには旧設定が残る。[認証範囲](https://help.digify.com/en/articles/13492796-how-to-use-password-login-instead-of-otp-in-digify)、[固定設定の範囲](https://help.digify.com/en/articles/580523-creating-editing-security-presets-for-your-team)

Screen Shieldの2026-08-18公式説明は表示領域の縮小、撮影操作を検出した場合や別窓へ移動した際の非表示/ぼかしを説明する。一方で全ページの画面撮影・結合の可能性や、OS/ブラウザーによって阻止できない操作を明記する。透かしは受信者への抑止・追跡を補助する。[画面保護](https://help.digify.com/en/articles/2820319-screen-shield-with-screenshot-protection)

期限・受信者の取消しはオンライン閲覧の制御に使える。**PPADは暗号化ファイルをダウンロードして利用する別機構**であり、保存禁止の代わりではない。現行資料にはオフライン利用・再接続時の記録同期の説明と即時取消しの説明が併存するため、切断中の取消し反映時間は未確認とする。開封案内ではbeta表記も残り、契約・展開状況は導入前に確認する。[オンラインDRM](https://help.digify.com/en/articles/1083354-secure-your-pdfs-e-books-for-online-selling-with-digify-s-drm)、[PPAD資料室](https://help.digify.com/en/articles/17342300-ppad-for-data-rooms)、[開封案内](https://help.digify.com/en/articles/10327041-how-to-open-ppad-files)

## FINAL CODE：ブラウザー利用とファイル無配布は違う

国内サービスのBrowser Viewは相手への専用クライアント導入なしで閲覧でき、メールOTP、閲覧者・期限、印刷・画面透かしを設定できる。公式の税理士法人事例はBrowser View暗号化ファイルをメール添付する利用である。**オンライン上の一箇所だけにファイルを置く方式とは異なる。** [公式機能説明・事例](https://www.finalcode.com/jp/news/blog/2024/022601/)

取得した現行スタートアップガイドは第10版、©2026。ユーザー別に原ファイルの取出し、コピー、印刷を制御する。100MB上限、表示不能の形式は元データのダウンロードのみとなる条件、印刷のプリンター制御が働かない制約を明記する。一般の印刷権限とプリンター種類による制御を混同しない。元ファイルの取出し不可・表示対象形式・ライセンス有効性を確認する必要がある。既存ローカル暗号化ファイルの存在まで禁止する要件には、そのまま適合しない。[第10版ガイド](https://secure.finalcode.com/manual/finalcode_bv_manual_jp.pdf)

## Google Drive / Docs：訪問者PINだけでは保存禁止にならない

非Googleアカウントの訪問者にもメールPINで共有でき、確認後7日間利用できる。7日はアクセス権そのものの自動終了ではなく、再確認して継続可能。訪問者は個別ファイルの保存もできるため、PIN導入だけでは目的を満たさない。[訪問者の仕様](https://support.google.com/drive/answer/9195194?hl=en)

別途、所有者が役割別に保存・コピー・印刷を制限する。現行文書ではEditorへの制限や、所有者にも適用する管理者DLP規則の説明がある。古いViewer/Commenterだけの説明に固定しない。公式は別の方法による内容共有を完全には阻止できないと明記する。共有フォルダーから継承する権限にも注意し、不要時はアクセスを削除する。[現行の制限](https://support.google.com/drive/answer/2494893?hl=en)

## メールOTPは強い本人認証と同一ではない

OTPはワンタイムの認証番号。メールOTPは主としてメールボックスへのアクセスを確認する。個人への権限付与、端末の安全性、画面の記録禁止は別問題であり、メールが侵害されれば影響する。

NIST SP 800-63B-4は手入力OTPをフィッシング耐性ありとせず、帯域外認証にメールを使わないよう規定する。ただし同規格は、メールアドレス確認用のコードと回復コードをこの認証手続の禁止対象から明示的に除外する。これは同規格の認証要件であり、すべての商用メール確認を違法・無意味とする判断ではない。FIDO2/WebAuthnのように正しい接続先に認証を結び付ける方式、SSO（組織で一元化した認証）と短い認証有効時間を検討する。SSOを導入したという名前だけでも耐性は保証されない。[NIST §§3.1.3、3.2.5](https://pages.nist.gov/800-63-4/sp800-63b.html)

## 採用前の確認項目と保存資料

公開/合成データを使う正規の導入試験では、役割を重複させた場合、管理/非管理端末、表示不能形式、モバイルのオフライン設定、外部受信者の再認証、印刷、認可済みAPI/連携アプリ、共有解除後の再表示を確認する。取得できない形式を保存許可へ切り替える例外や、旧共有リンク・旧設定・既存コピーも管理する。

ブラウザー内に個人情報の平文が届くこと自体を避けたい場合は、文書原本を丸ごと共有せず必要項目だけを伏字/部分表示する業務画面、または管理端末・遠隔実行を含む別の制御が必要になる。これは比較からの設計上の推論。画面を正規利用者へ見せつつ、記憶・撮影等の全再現まで消す保証ではない。

[取得台帳](online_pii_document_sources_20261015.json)にURL、取得時刻、原本SHA-256、本文可否を保存した。原本は `research/disclosures/raw/online_pii_20261015/documents/`。HTMLは取得時点の資料で、将来の変更を自動追跡しない。Box表示ライブラリREADMEは移動するmasterのスナップショットで、固定commitのコード監査ではない。取得失敗したBox APIページは本文根拠に採用していない。研究論文と遠隔ブラウザー/業務画面の方式は別担当が調査する。
