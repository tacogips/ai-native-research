"""拡張版（v3）の項目・グループ・Workspace DLPの検知器対応・独自検知器の定義。

標準検知器の名称は公開の一覧（how-to-use-predefined-content-detectors、2026-11-10版）による。
独自検知器はRE2構文の正規表現と語句一覧で、公開上限（正規表現1,000文字、語句950語・60KB）内に収める。
値はすべて独自の架空例。実在の人物・団体・番号の照会には使わない。
"""

D = '[0-9０-９]'
SEP = '[ 　]*[：:]?[ 　]*'

# 含まれやすい個人情報のグループ。分類ラベルは1グループ1ラベルで設計する。
GROUPS = {
    'G1': '公的番号・本人確認',
    'G2': '金融・資産',
    'G3': '経歴・勤務・家族',
    'G4': '健康・医療（要配慮）',
    'G5': '要配慮（健康以外）',
    'G6': '認証情報',
    'G7': '連絡先・基本属性',
    'G8': '生体・音声・映像',
}

# capability: standard=標準検知器あり / custom=独自検知器で構成 / unsupported=本文検査の対象外
# predefined: 公開一覧の検知器名。日本語文書での動作は公式資料に記載がない。
ITEMS = {
    'individual': dict(name='個人番号', group='G1', legal='個人識別符号・特定個人情報', capability='standard',
                       predefined=['Japan / Individual Number'],
                       regex=[f'(個人番号|マイナンバー){SEP}{D}{{4}}[ -]?{D}{{4}}[ -]?{D}{{4}}']),
    'license': dict(name='運転免許証番号', group='G1', legal='個人識別符号', capability='standard',
                    predefined=["Japan / Driver's License Number"],
                    regex=[f'免許証(番号)?{SEP}{D}{{12}}']),
    'passport': dict(name='旅券番号', group='G1', legal='個人識別符号', capability='standard',
                     predefined=['Japan / Passport', 'Global / Passport'],
                     regex=[f'(旅券|パスポート)(番号)?{SEP}[A-ZＡ-Ｚ]{{2}}{D}{{7}}']),
    'residence_card': dict(name='在留カード番号', group='G1', legal='個人識別符号（現行規則で要確認）', capability='custom',
                           predefined=[],
                           regex=[f'在留カード(番号)?{SEP}[A-Z]{{2}}{D}{{8}}[A-Z]{{2}}']),
    'health_insurance': dict(name='健康保険の記号番号', group='G1', legal='個人識別符号', capability='custom',
                             predefined=[],
                             regex=[f'保険者番号{SEP}{D}{{6,8}}', f'記号{SEP}{D}{{1,8}}[ 　、,]*番号{SEP}{D}{{1,8}}']),
    'pension': dict(name='基礎年金番号', group='G1', legal='個人識別符号', capability='custom',
                    predefined=[], regex=[f'基礎年金番号{SEP}{D}{{4}}-?{D}{{6}}']),
    'employment_insurance': dict(name='雇用保険被保険者番号', group='G1', legal='個人情報（符号該当性は現行規則で要確認）',
                                 capability='custom', predefined=[],
                                 regex=[f'被保険者番号{SEP}{D}{{4}}-?{D}{{6}}-?{D}']),
    'card': dict(name='クレジットカード番号', group='G2', legal='個人情報', capability='standard',
                 predefined=['Global / Credit card number'],
                 regex=[f'カード(番号)?{SEP}{D}{{4}}[ -]?{D}{{4}}[ -]?{D}{{4}}[ -]?{D}{{4}}']),
    'bank': dict(name='銀行口座番号', group='G2', legal='個人情報', capability='standard',
                 predefined=['Japan / Bank Account Number'],
                 regex=[f'(普通|当座|貯蓄)(預金)?[ 　]*(口座番号)?{SEP}{D}{{7}}', f'口座番号{SEP}{D}{{7}}']),
    'assets': dict(name='資産・残高', group='G2', legal='個人情報', capability='custom', predefined=[],
                   regex=[f'(預金残高|預貯金残高|保有株式|評価額|ローン残高|借入残高)[^\\n]{{0,12}}{D}[0-9０-９,，]*[ 　]*(円|万円|株)']),
    'annual_income': dict(name='年収・所得', group='G2', legal='個人情報', capability='custom', predefined=[],
                          regex=[f'(年収|給与支給総額|年間所得|支払金額)[^\\n]{{0,6}}{D}[0-9０-９,，.]*[ 　]*(円|万円)']),
    'private_insurance': dict(name='民間保険の契約', group='G2', legal='個人情報（告知内容は要配慮と重なる）',
                              capability='custom', predefined=[],
                              regex=[f'(保険)?証券番号{SEP}[A-Z0-9][A-Z0-9-]{{5,}}', '(受取人|被保険者)[ 　]*[：:][^\\n]{1,20}']),
    'job_history': dict(name='職歴', group='G3', legal='個人情報', capability='custom',
                        predefined=['Documents / Resume（文書単位）'],
                        regex=[f'{D}{{4}}年[^\\n]{{0,30}}(入社|退社|退職|転職|配属)', '職(務経)?歴[ 　]*[：:]']),
    'education': dict(name='学歴', group='G3', legal='個人情報', capability='custom',
                      predefined=['Documents / Resume（文書単位）'],
                      regex=[f'(大学|大学院|高等学校|専門学校)[^\\n]{{0,15}}(卒業|中退|修了)']),
    'employer': dict(name='勤務先', group='G3', legal='個人情報', capability='custom', predefined=[],
                     regex=['(勤務先|所属先|在籍会社)[ 　]*[：:][^\\n]{2,}',
                            '(株式会社|有限会社)[^\\n。]{0,12}(に勤務|に勤めて|に在籍)']),
    'family': dict(name='家族構成', group='G3', legal='個人情報', capability='custom', predefined=[],
                   regex=[f'(配偶者|長男|長女|次男|次女|扶養親族)[^\\n]{{0,15}}({D}+歳|{D}+人|同居|扶養)', '続柄[ 　]*[：:]']),
    'medical_history': dict(name='病歴・診療', group='G4', legal='要配慮（病歴・診療）', capability='standard',
                            predefined=['Global / Medical context', 'Global / ICD 9-CM Lexicon', 'Global / ICD 10-CM Lexicon'],
                            regex=['(糖尿病|高血圧|うつ病|がん|癌|喘息|肝炎|統合失調症|心筋梗塞)[^\\n]{0,15}(診断|通院|治療|処方|休職|入院|療養)',
                                   '(既往歴|病歴)[ 　]*[：:][ 　]*[^な＿*\\n]'],
                            word_list=['糖尿病', '高血圧', 'うつ病', 'がん', '喘息', '肝炎', '統合失調症', '心筋梗塞']),
    'health_checkup': dict(name='健康診断の結果', group='G4', legal='要配慮（健康診断等の結果）', capability='custom',
                           predefined=['Global / Medical context（語として）'],
                           regex=[f'(血圧|HbA1c|空腹時血糖|LDLコレステロール|BMI)[ 　]*{D}', '(要再検査|要精密検査|特定保健指導の対象)']),
    'disability': dict(name='障害', group='G4', legal='要配慮（心身の機能の障害）', capability='custom', predefined=[],
                       regex=['(身体障害者手帳|療育手帳|精神障害者保健福祉手帳)',
                              '(身体|知的|精神|発達|視覚|聴覚)障害(の診断|がある|を持つ|と診断)']),
    'race': dict(name='人種・民族', group='G5', legal='要配慮（人種）', capability='standard',
                 predefined=['Global / Ethnic group'],
                 regex=['(人種|民族|民族的出自)[ 　]*[：:][^\\n]{1,20}']),
    'creed': dict(name='信条', group='G5', legal='要配慮（信条）', capability='custom', predefined=[],
                  regex=['(信仰|宗教|信条|支持政党)[ 　]*[：:][^\\n]{1,30}', '(党員|信者|入信)']),
    'social_status': dict(name='社会的身分', group='G5', legal='要配慮（社会的身分）', capability='custom', predefined=[],
                          regex=['(被差別部落|部落出身)']),
    'criminal_record': dict(name='犯罪の経歴', group='G5', legal='要配慮（犯罪の経歴）', capability='custom', predefined=[],
                            regex=['(前科|有罪判決|執行猶予|罰金刑|懲役)']),
    'criminal_procedure': dict(name='刑事・少年事件の手続', group='G5', legal='要配慮（刑事事件・少年保護事件の手続）',
                               capability='custom', predefined=[],
                               regex=['(被疑者として|逮捕され|起訴され|書類送検|少年審判|保護観察処分|勾留)']),
    'crime_victim': dict(name='犯罪の被害', group='G5', legal='要配慮（犯罪により害を被った事実）', capability='custom',
                         predefined=[], regex=['(被害届|の被害を受け|被害に遭|被害を相談)']),
    'password_plain': dict(name='平文パスワード', group='G6', legal='法定外の機微情報（認証情報）', capability='standard',
                           predefined=['Credentials and secrets / Password'],
                           regex=['(?i)(password|passwd|pwd|パスワード)[ 　]*[：:=][ 　]*[^ 　*<＿\\n][^ 　\\n]{3,}']),
    'password_hash': dict(name='パスワードの一方向変換値', group='G6', legal='法定外の機微情報（認証情報）', capability='standard',
                          predefined=['Credentials and secrets / Weakly hashed password'],
                          regex=['\\$2[aby]\\$[0-9]{2}\\$[./A-Za-z0-9]{53}', '\\$argon2(id|i|d)\\$v=[0-9]+\\$', '\\$6\\$[^$\\s]{1,16}\\$[./A-Za-z0-9]{86}',
                                 'pbkdf2_sha256\\$[0-9]+\\$', '(?i)(password_hash|passwd_hash|pw_hash)[ 　]*[：:=][ 　]*[0-9a-f]{32,64}']),
    'email': dict(name='メールアドレス', group='G7', legal='個人情報', capability='standard',
                  predefined=['Global / Email address'],
                  regex=['[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}']),
    'phone': dict(name='電話番号', group='G7', legal='個人情報', capability='standard',
                  predefined=['Global / Phone number'],
                  regex=[f'0[789]0-?{D}{{4}}-?{D}{{4}}', f'0{D}{{1,3}}-{D}{{2,4}}-{D}{{4}}']),
    'address': dict(name='住所', group='G7', legal='個人情報', capability='custom', predefined=[],
                    regex=[f'(東京都|北海道|大阪府|京都府|..県|...県)[^\\n]{{1,25}}{D}+(丁目|番地?|号|-{D})']),
    'name': dict(name='氏名', group='G7', legal='個人情報', capability='standard',
                 predefined=['Global / Name occurrence（日本語の動作は未確認）'],
                 regex=['(氏名|お名前|担当者?)[ 　]*[：:][ 　]*[^ 　＿*\\n]{1,6}[ 　][^ 　＿*\\n]{1,6}']),
}

# 文字の本文検査では扱えない項目。生成もしない。
UNSUPPORTED = {
    'face': dict(name='顔写真', group='G8', reason='Workspace DLPに顔・人物画像の標準検知器を公開一覧で確認できない'),
    'voice': dict(name='声の音声', group='G8', reason='音声の文字起こしは本文検査の対象外'),
    'video': dict(name='映像', group='G8', reason='映像の画面文字・音声は本文検査の対象外'),
}

LIMITS = {'regex_chars': 1000, 'word_list_words': 950, 'word_list_bytes': 60 * 1024,
          'custom_detectors_in_rules': 100, 'word_min_alnum': 2}
