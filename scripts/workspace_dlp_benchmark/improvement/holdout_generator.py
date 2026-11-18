#!/usr/bin/env python3
"""DLP 評価用の独立ホールドアウト（架空資料）を生成する。値はすべて架空。"""
import json
import random
import string
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent / "holdout_cases.json"
rng = random.Random(20261118)

ITEMS = [
    "individual", "license", "passport", "residence_card", "health_insurance", "pension",
    "employment_insurance", "card", "bank", "assets", "annual_income", "private_insurance",
    "job_history", "education", "employer", "family", "medical_history", "health_checkup",
    "disability", "race", "creed", "social_status", "criminal_record", "criminal_procedure",
    "crime_victim", "password_plain", "password_hash", "email", "phone", "address", "name",
]


# ---------- 補助：カード番号（Luhn）とハッシュ値 ----------
def luhn_check_digit(body: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def luhn_ok(num: str) -> bool:
    return luhn_check_digit(num[:-1]) == num[-1]


def make_card(prefix: str) -> str:
    body = prefix + "".join(rng.choice(string.digits) for _ in range(15 - len(prefix)))
    return body + luhn_check_digit(body)


def make_non_luhn16() -> str:
    body = "".join(rng.choice(string.digits) for _ in range(15))
    good = luhn_check_digit(body)
    bad = str((int(good) + 3) % 10)
    return body + bad


def g4(n: str, sep: str = " ") -> str:
    return sep.join(n[i:i + 4] for i in range(0, 16, 4))


def fw(s: str) -> str:
    """半角英数記号を全角に変換する。"""
    out = []
    for ch in s:
        o = ord(ch)
        if 0x21 <= o <= 0x7E:
            out.append(chr(o + 0xFEE0))
        elif ch == " ":
            out.append("　")
        else:
            out.append(ch)
    return "".join(out)


B64 = string.ascii_letters + string.digits + "./"
STD64 = string.ascii_letters + string.digits + "+/"


def rs(alphabet: str, n: int) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


CARDS = [make_card(p) for p in ("4539", "5412", "3568", "4916", "5203", "3530")]
NONLUHN = make_non_luhn16()
CARD_AMB = make_card("4980")

BCRYPT1 = "$2b$12$" + rs(B64, 22) + rs(B64, 31)
BCRYPT2Y = "$2y$10$" + rs(B64, 22) + rs(B64, 31)
ARGON = "$argon2id$v=19$m=65536,t=3,p=4$" + rs(STD64, 22) + "$" + rs(STD64, 43)
SHA512C_1 = "$6$" + rs(B64, 16) + "$" + rs(B64, 86)
SHA512C_2 = "$6$rounds=656000$" + rs(B64, 16) + "$" + rs(B64, 86)
PBKDF2 = "pbkdf2_sha256$600000$" + rs(string.ascii_letters + string.digits, 22) + "$" + rs(STD64, 43) + "="
HEX64 = rs("0123456789abcdef", 64)
HEX64B = rs("0123456789abcdef", 64)
HEX40 = rs("0123456789abcdef", 40)

# ---------- 事例定義 ----------
CASES = []
_counter = defaultdict(int)
KIND_ABBR = {"positive": "pos", "negative": "neg", "ambiguous": "amb"}


def C(item, kind, style, text, extra=(), amb=(), note=""):
    _counter[(item, kind)] += 1
    present = []
    if kind == "positive":
        present.append(item)
    present.extend(e for e in extra if e not in present)
    ambiguous = list(amb)
    if kind == "ambiguous" and item not in ambiguous:
        ambiguous.insert(0, item)
    CASES.append({
        "case_id": f"{item}-{KIND_ABBR[kind]}-{_counter[(item, kind)]}",
        "item": item,
        "kind": kind,
        "style": style,
        "text": text,
        "present": present,
        "ambiguous": ambiguous,
        "note": note,
    })


P, N, A = "positive", "negative", "ambiguous"

# individual
C("individual", P, "heading", "個人番号：4829 1736 5502\n氏名：宮之原 透", ["name"], note="見出しと値が同じ行、空白区切り")
C("individual", P, "sentence", "年末調整の書類に記載漏れがあったため、本人のマイナンバー 731948205617 を追記して再提出しました。", note="文中に連続12桁")
C("individual", P, "table", "社員番号\t氏名\t個人番号\nE-1042\t桐生 美咲\t503827196448\nE-1043\t大河内 修\t281605937214", ["name"], note="タブ区切り表")
C("individual", P, "form_multiline", "給与支払報告書（個人別明細書）\n受給者番号\n00318\n個人番号\n841602739558", note="見出しと値が別行")
C("individual", P, "chat_or_list", "[10:12] 総務A: 新入社員の番号届いてます\n[10:13] 総務A: 小此木 遥さんのは 2650-1938-4471 です\n[10:14] 人事B: 了解、システムに入れます", ["name"], note="チャット、ハイフン区切り")
C("individual", P, "variant_notation", "My Number (Individual Number): ３９０７−４４１８−２６０５", note="英語見出し＋全角数字＋全角マイナス")
C("individual", N, "similar_number", "ご注文番号：482917365502\nお届け予定日：11月21日\n商品：見本ブランド 加湿器 KS-200", note="12桁の注文番号")
C("individual", N, "general_text", "個人番号は住民票を有する全ての人に1人1つ指定される12桁の番号で、社会保障・税・災害対策の分野に限って利用されます。", note="制度の一般説明")
C("individual", N, "empty_or_masked", "個人番号：＿＿＿＿ ＿＿＿＿ ＿＿＿＿\n（番号確認書類の写しを添付してください）", note="空欄の帳票")
C("individual", N, "business_doc", "架空ソリューションズ株式会社では、マイナンバー収集・保管業務の代行サービスを提供しています。料金は社員1名あたり月額50円からです。", note="サービス案内")
C("individual", A, "other", "個人番号：****-****-5517（下4桁のみ表示）", note="下4桁だけ残した部分伏字")

# license
C("license", P, "heading", "運転免許証番号：301845290617\n有効期限：2029年08月14日")
C("license", P, "sentence", "社用車の利用登録のため、免許証の番号 442103958174 を控えさせていただきました。")
C("license", P, "table", "運転者\t免許証番号\t種類\n根津 亮平\t621907384452\t中型\n芦原 志保\t305518927640\t普通", ["name"])
C("license", P, "form_multiline", "車両使用許可申請書\n運転者の免許証番号\n290614735822\n免許の条件等：眼鏡等")
C("license", P, "chat_or_list", "・レンタカー予約確認\n・運転者：申込者本人\n・免許証No. 5317-0298-4461 を受付で提示済み", note="箇条書き、4-4-4区切り")
C("license", P, "variant_notation", "Driver's License No.: ４０１２３８７６５１９０", note="英語見出し＋全角数字")
C("license", N, "similar_number", "部品番号 718204953306 の在庫は残り12個です。", note="12桁の部品番号")
C("license", N, "general_text", "運転免許証の番号は12桁で、交付した公安委員会や初回交付の年などを表す数字が含まれます。紛失した場合は警察署等で再交付を申請します。")
C("license", N, "empty_or_masked", "免許証番号：●●●●●●●●●●●●\n確認者印：＿＿")
C("license", N, "business_doc", "見本ドライビングスクールでは普通免許コースを随時受付中です。入校から卒業まで最短16日、料金は税込298,000円です。")
C("license", A, "other", "運転免許証番号（末尾4桁）：4461\n本人確認済み", note="末尾4桁のみ")

# passport
C("passport", P, "heading", "旅券番号：TK4829173")
C("passport", P, "sentence", "出張者の旅券番号は MZ5017382 で、有効期限は2031年3月です。")
C("passport", P, "table", "Name\tPassport No.\tExpiry\nKIRYU MISAKI\tTR6093814\t2030-05-11", ["name"], note="英語の表、ローマ字氏名")
C("passport", P, "form_multiline", "海外渡航届\n旅券番号\nRE7238016\n渡航先：見本共和国（架空）")
C("passport", P, "chat_or_list", "件名：航空券手配の件\n\n航空券の手配にあたり、パスポート番号（TS3390175）のご確認をお願いします。\n架空トラベル 予約センター", note="メール本文")
C("passport", P, "variant_notation", "パスポートＮｏ．：ＭＫ０４７１２９３", note="全角英数")
C("passport", N, "similar_number", "型番 TR5509127 の交換フィルターは現在在庫切れです。", note="英字2＋数字7の型番")
C("passport", N, "general_text", "日本の一般旅券には有効期間10年のものと5年のものがあり、申請は住民登録をしている都道府県の旅券窓口で行います。")
C("passport", N, "empty_or_masked", "旅券番号：＿＿＿＿＿＿＿＿＿（渡航前に記入）")
C("passport", N, "business_doc", "架空トラベルの海外ツアーにご参加の際は、パスポートの残存有効期間が6か月以上必要です。")
C("passport", A, "other", "旅券番号：TK48*****（照合済み）", note="上位のみ残した部分伏字")

# residence_card
C("residence_card", P, "heading", "在留カード番号：UH38201746KQ")
C("residence_card", P, "sentence", "採用予定者の在留カード（番号 EK59302817GT）を確認し、就労制限がないことを確認しました。")
C("residence_card", P, "table", "社員ID\t在留カード番号\t在留期限\nF-021\tRN70419352FX\t2027/06/30\nF-022\tTA28390461LB\t2026/12/15")
C("residence_card", P, "form_multiline", "外国人雇用状況届出書\n在留カードの番号\nPQ61028374ZM\n在留資格：技術・人文知識・国際業務")
C("residence_card", P, "chat_or_list", "@人事 来週入社の方の在留カード番号 WB40193827ND を台帳に転記お願いします", note="チャット")
C("residence_card", P, "variant_notation", "Residence Card No. ＳＫ ４０１９３８２７ ＮＤ", note="全角＋空白区切り")
C("residence_card", N, "similar_number", "製造ロット：LT20481937QA　出荷日 2026/10/02", note="同じ形のロット番号")
C("residence_card", N, "general_text", "在留カードは中長期在留者に交付され、番号は英字2文字・数字8桁・英字2文字の計12文字で構成されます。")
C("residence_card", N, "empty_or_masked", "在留カード番号：XX00000000XX（記入例）\n※実際の番号を記入してください", note="記入例のダミー値")
C("residence_card", N, "business_doc", "見本行政書士事務所では在留期間更新許可申請の代行を承ります。報酬は税込44,000円からです。")
C("residence_card", A, "other", "在留カード番号の下4桁：17GT（本人確認時に照合）", note="下4桁のみ")

# health_insurance
C("health_insurance", P, "heading", "保険者番号：06138274\n記号：3021　番号：458")
C("health_insurance", P, "sentence", "高額療養費の申請書には、被保険者証の記号番号（記号 71 番号 2094）と保険者番号 01130427 を記入しました。")
C("health_insurance", P, "table", "氏名\t保険者番号\t記号\t番号\n戸叶 智子\t32130518\t205\t1187", ["name"])
C("health_insurance", P, "form_multiline", "被保険者資格取得届\n被保険者証の記号・番号\n8014-2271\n保険者番号\n06271935")
C("health_insurance", P, "chat_or_list", "- 保険証の情報（コピーより）\n  - 保険者番号 39131046\n  - 記号 12 番号 337")
C("health_insurance", P, "variant_notation", "Health Insurance: Insurer No. ０６１３０９７２ / Symbol ４５ / No. １０２８")
C("health_insurance", N, "similar_number", "受付番号 06138274-0012 にて資料請求を承りました。", note="8桁＋枝番の受付番号")
C("health_insurance", N, "general_text", "保険者番号は8桁で、法別番号・都道府県番号・保険者別番号・検証番号から構成されます。")
C("health_insurance", N, "empty_or_masked", "記号：＿＿＿＿　番号：＿＿＿＿\n保険者番号：＿＿＿＿＿＿＿＿")
C("health_insurance", N, "business_doc", "架空健康保険組合のご案内：加入事業所数 320、被保険者数 約4万人。保健事業として人間ドックの費用補助を行っています。")
C("health_insurance", A, "other", "保険者番号：06138274（架空健康保険組合）", note="保険者番号だけでは個人を特定しない")

# pension
C("pension", P, "heading", "基礎年金番号：4102-738195")
C("pension", P, "sentence", "年金事務所に照会したところ、本人の基礎年金番号は 1395-204718 で間違いないとの回答でした。")
C("pension", P, "table", "氏名\t基礎年金番号\t資格取得日\n赤羽 大地\t6027-183945\t2019/04/01", ["name"])
C("pension", P, "form_multiline", "国民年金被保険者関係届\n被保険者の基礎年金番号\n2281-509364")
C("pension", P, "chat_or_list", "社労士さんへのメール：\n先日の資格喪失の件、該当者の年金番号は 3940-226718 です。ご確認ください。")
C("pension", P, "variant_notation", "Basic Pension No. ７７２０ー４８１０３６", note="全角数字＋長音記号をハイフン代わり")
C("pension", N, "similar_number", "配送状況のお問い合わせ番号：5208-417390", note="4-6桁の問合せ番号")
C("pension", N, "general_text", "基礎年金番号は公的年金制度で共通して使用する番号で、現在はマイナンバーとの紐付けが進んでいます。")
C("pension", N, "empty_or_masked", "基礎年金番号：＿＿＿＿－＿＿＿＿＿＿")
C("pension", N, "business_doc", "見本社会保険労務士法人：年金相談、各種年金の請求代行、就業規則の作成を承ります。")
C("pension", A, "other", "基礎年金番号（下6桁）：738195", note="下6桁のみ")

# employment_insurance
C("employment_insurance", P, "heading", "雇用保険被保険者番号：5013-482917-3")
C("employment_insurance", P, "sentence", "資格取得届には、本人から提出された被保険者番号 2208-731946-5 を記入して手続します。")
C("employment_insurance", P, "table", "社員番号\t被保険者番号\t取得年月日\nE-2201\t4419-302871-6\t2022/04/01\nE-2202\t6031-582094-1\t2022/04/01")
C("employment_insurance", P, "form_multiline", "雇用保険被保険者資格取得届\n１．被保険者番号\n3307-195820-4\n２．取得区分：新規")
C("employment_insurance", P, "chat_or_list", "A: 中途の方、雇用保険の番号わかりました？\nB: はい、1742-608315-9 でした", note="チャット")
C("employment_insurance", P, "variant_notation", "Employment Insurance No: ５５１０－２０３９４７－８")
C("employment_insurance", N, "similar_number", "部品番号 7302-114958-6 の納期を確認しています。", note="4-6-1形の部品番号")
C("employment_insurance", N, "general_text", "雇用保険被保険者番号は11桁で、事業所が変わっても原則として同じ番号を使い続けます。")
C("employment_insurance", N, "empty_or_masked", "被保険者番号：□□□□-□□□□□□-□")
C("employment_insurance", N, "business_doc", "見本職業紹介所の求人案内：雇用保険・社会保険完備、賞与年2回、交通費全額支給。")

# card
c = CARDS
C("card", P, "heading", f"カード番号：{g4(c[0])}\n有効期限：09/29")
C("card", P, "sentence", f"お客様より電話で決済のご依頼があり、カード番号 {c[1]} にて処理済みです。", note="16桁連続")
C("card", P, "table", f"会員ID\tカード番号\t有効期限\nM-3301\t{g4(c[2], '-')}\t11/28")
C("card", P, "form_multiline", f"クレジットカード決済依頼書\nカード番号\n{g4(c[3], '-')}\n名義人\nMIYANOHARA TORU", ["name"])
C("card", P, "chat_or_list", f"#経理 出張費の立替、法人カード {g4(c[4])} で決済しました。明細は月末に回します。")
C("card", P, "variant_notation", f"Card No.：{fw(g4(c[5], '-'))}", note="全角数字とハイフン")
C("card", N, "similar_number", f"注文番号：{NONLUHN}\nお支払い方法：代金引換", note="Luhn不一致の16桁注文番号")
C("card", N, "general_text", "クレジットカード番号は通常16桁で、最後の1桁は Luhn アルゴリズムによる検査数字です。")
C("card", N, "empty_or_masked", "ご登録カード：**** **** **** 4821（有効期限 03/28）", note="下4桁のみの伏字")
C("card", N, "business_doc", "見本カードのご案内：年会費永年無料、ポイント還元率1.0%、旅行傷害保険付帯。")
C("card", A, "other", f"カード番号：{CARD_AMB[:4]} {CARD_AMB[4:6]}** **** {CARD_AMB[12:]}", note="先頭6桁と末尾4桁のみ")

# bank
C("bank", P, "heading", "振込先：架空銀行 見本支店 普通 3048192")
C("bank", P, "sentence", "給与の振込口座を試験信用金庫 本店営業部の当座 7102384 に変更したいとの申し出がありました。")
C("bank", P, "table", "氏名\t銀行\t支店\t種別\t口座番号\n瀬能 和也\t例示銀行\t駅前支店\t普通\t5520917", ["name"])
C("bank", P, "form_multiline", "口座振替依頼書\n金融機関名：架空銀行\n支店名：見本台支店\n預金種目\n普通\n口座番号\n6391027\n口座名義（カナ）\nセノウ カズヤ", ["name"])
C("bank", P, "chat_or_list", "お世話になっております。報酬のお振込先は以下のとおりです。\n・見本ネット銀行 第一営業支店（101）\n・普通預金 4428105", note="メール本文")
C("bank", P, "variant_notation", "Bank: Kaku Bank (架空銀行), Branch: Mihon (No. 213)\nAccount Type: Savings / Account No.: ０８７３２１６")
C("bank", N, "similar_number", "支店コード 213 の ATM（機番 4428105）の保守作業を11月20日に実施します。", note="7桁の機器番号")
C("bank", N, "general_text", "銀行の口座番号は通常7桁で、金融機関コード・支店番号・預金種目と組み合わせて口座を特定します。")
C("bank", N, "empty_or_masked", "口座番号：＊＊＊＊＊＊＊（ご本人確認後に表示）")
C("bank", N, "business_doc", "架空銀行は2026年4月に見本支店を駅前支店へ統合しました。店舗数は全国で48店です。")
C("bank", A, "other", "請求書\nお振込先：例示銀行 本店営業部 普通 1203948\n口座名義：架空商事株式会社", note="法人名義の口座")

# assets
C("assets", P, "heading", "預金残高：3,482,105円（2026年10月末時点）\n名義：宮之原 透", ["name"])
C("assets", P, "sentence", "面談では、本人が見本電機の株式を1,200株保有しており、評価額は約540万円とのことだった。")
C("assets", P, "table", "（申込者本人の資産）\n資産\t金額\n普通預金\t1,204,330円\n定期預金\t5,000,000円\n住宅ローン残高\t▲21,870,000円")
C("assets", P, "form_multiline", "住宅ローン借換申込書\n現在の借入残高\n18,420,000円\n毎月返済額\n87,300円")
C("assets", P, "chat_or_list", "相続相談メモ（相談者名義の財産）\n- 預金 約800万円\n- 自宅土地（評価額 2,300万円）\n- 証券口座の投資信託 約350万円")
C("assets", P, "variant_notation", "Account balance (personal): JPY ３，９０２，４１８\nHoldings: 見本ホールディングス 普通株式 500株")
C("assets", N, "similar_number", "受注残高：3,482,105円（見本工業向け案件）", note="法人の受注残")
C("assets", N, "general_text", "（例示）家計調査の貯蓄現在高は平均値が中央値を大きく上回る傾向があり、一部の高額世帯が平均を押し上げています。")
C("assets", N, "empty_or_masked", "預金残高：＊＊＊＊＊＊円（ログイン後に表示）")
C("assets", N, "business_doc", "架空商事株式会社 会社概要：資本金 1億円、総資産 85億円、従業員数 420名。", note="法人の資産")
C("assets", A, "other", "資産状況：「老後資金は十分ある」と本人談（金額不明）", note="金額のない漠然とした言及")

# annual_income
C("annual_income", P, "heading", "年収：6,240,000円")
C("annual_income", P, "sentence", "昨年の源泉徴収票によれば、本人の給与収入は年間512万円だった。")
C("annual_income", P, "table", "社員番号\t氏名\t2025年給与総額\nE-1042\t桐生 美咲\t7,380,400", ["name"])
C("annual_income", P, "form_multiline", "所得証明書\n令和7年中の所得金額\n4,126,000円\n（給与収入 5,800,000円）")
C("annual_income", P, "chat_or_list", "面接メモ（候補者A）\n・現年収 720万（基本給＋賞与）\n・希望年収 800万")
C("annual_income", P, "variant_notation", "Annual income: ¥9.8M (FY2025)\n本人所得：９８０万円")
C("annual_income", N, "similar_number", "年商：6,240,000,000円（見本工業 2025年度）", note="法人の売上")
C("annual_income", N, "general_text", "所得税は所得が高くなるほど税率が上がる累進課税で、税率は5%から45%までの7段階です。")
C("annual_income", N, "empty_or_masked", "年収：＿＿＿＿万円（任意記入）")
C("annual_income", N, "business_doc", "【求人票】架空ロジスティクス株式会社 営業職\n想定年収 450万〜650万円（経験・能力による）")
C("annual_income", A, "other", "年収帯：600〜800万円（匿名アンケートの回答）", note="匿名の幅のある回答")

# private_insurance
C("private_insurance", P, "heading", "保険証券番号：SN-2024-0815327\n保険種類：終身医療保険")
C("private_insurance", P, "sentence", "本人は見本生命の定期保険（証券番号 7730192845）に加入しており、死亡保険金受取人は法定相続人と指定されている。")
C("private_insurance", P, "table", "契約者\t保険会社\t証券番号\t保険金額\n大河内 修\t架空生命\tKL40291837\t3,000万円", ["name"])
C("private_insurance", P, "form_multiline", "保険金請求書\n証券番号\nAX-882034761\n被保険者氏名\n芦原 志保", ["name"])
C("private_insurance", P, "chat_or_list", "保険の見直し相談\n- 架空損保 自動車保険 証券No. 0019-4720-38\n- 年間保険料 68,400円\n- 満期 2027/03/01")
C("private_insurance", P, "variant_notation", "Policy No.: ＰＬ－５５０１９２８３\nInsured: 本人 / Beneficiary: 法定相続人")
C("private_insurance", N, "similar_number", "見積番号 SN-2025-0193822 の内容でオフィス家具を発注します。", note="同形の見積番号")
C("private_insurance", N, "general_text", "終身保険は保障が一生涯続く生命保険で、解約返戻金がある商品が一般的です。")
C("private_insurance", N, "empty_or_masked", "証券番号：＿＿＿＿＿＿＿＿　受取人：＿＿＿＿")
C("private_insurance", N, "business_doc", "架空生命保険株式会社 新商品のご案内：がん保険『みほんケア』月額1,980円から。")
C("private_insurance", A, "other", "生命保険：加入あり（保険会社・内容は不明）", note="加入の有無のみ")

# job_history
C("job_history", P, "heading", "職歴：2014年4月 架空商事株式会社 入社／2019年3月 同社 退社", note="過去の勤務のみ（現勤務先なし）")
C("job_history", P, "sentence", "本人は新卒で見本システム株式会社に入り、SEとして6年勤務した後、2023年に試験ネットワークス株式会社へ転職した。", ["employer"])
C("job_history", P, "table", "期間\t会社名\t職種\n2010/04-2016/09\t例示製作所株式会社\t生産技術\n2016/10-2021/03\t見本工業株式会社\t品質保証\n2021/04-現在\t架空化学株式会社\t品質管理課長", ["employer"])
C("job_history", P, "form_multiline", "職務経歴書\n氏名\n根津 亮平\n経歴\n2012年 架空建設株式会社 入社（施工管理）\n2020年 一身上の都合により退職", ["name"])
C("job_history", P, "chat_or_list", "@採用 候補者の方、前職は試験銀行に8年、その前は見本証券に3年いたそうです", note="過去の勤務のみ")
C("job_history", P, "variant_notation", "Work Experience:\nApr 2015 – Mar 2022  Kaku Trading Co. (架空商事), Sales\nApr 2022 – Present  Mihon Foods (見本食品), Marketing", ["employer"])
C("job_history", N, "general_text", "職務経歴書は、これまでの業務内容や実績を具体的に記載する書類です。")
C("job_history", N, "empty_or_masked", "職歴：＿＿＿＿＿＿＿＿＿＿＿\n（新卒の方は記入不要）")
C("job_history", N, "business_doc", "架空商事株式会社 沿革：1985年 創業／2001年 見本物産を吸収合併／2020年 株式上場", note="会社の沿革")
C("job_history", N, "business_doc", "【求人】見本テクノロジー株式会社 経験者採用\n応募資格：実務経験3年以上（転職回数不問）")
C("job_history", A, "other", "職歴：大手メーカーにて約10年勤務（社名非公開）", note="社名・時期が曖昧")

# education
C("education", P, "heading", "学歴：2012年3月 見本大学 経済学部 卒業")
C("education", P, "sentence", "本人は2018年に架空工業大学大学院の修士課程を修了している。")
C("education", P, "table", "年月\t学歴\n2008年3月\t試験県立みほん高等学校 卒業\n2012年3月\t例示大学 文学部 卒業")
C("education", P, "form_multiline", "履歴書\n氏名\n戸叶 智子\n最終学歴\n見本女子大学 家政学部 卒業（2016年）", ["name"])
C("education", P, "chat_or_list", "面談メモ：候補者は架空高専の電気工学科を卒業後、見本大学工学部に編入して卒業している")
C("education", P, "variant_notation", "Education: B.Sc. in Physics, Mihon University (見本大学), graduated March 2017")
C("education", N, "general_text", "学校教育法では、大学の修業年限は原則として4年とされています。")
C("education", N, "empty_or_masked", "最終学歴：□中学 □高校 □短大・専門 □大学 □大学院（いずれかに✓）")
C("education", N, "business_doc", "見本大学 学校案内：経済学部・工学部の2学部、在学生数 約5,200名、就職率 97.8%。")
C("education", N, "business_doc", "【求人】応募資格：大卒以上（学部・学科不問）")
C("education", A, "other", "大学では経済を学んでいたとのこと（学校名・卒業の有無は不明）")

# employer
C("employer", P, "heading", "勤務先：架空商事株式会社 経理部")
C("employer", P, "sentence", "申込者は見本電機株式会社の大阪工場に勤務している。")
C("employer", P, "table", "氏名\t勤務先\t役職\n瀬能 和也\t試験ネットワークス株式会社\t主任", ["name"])
C("employer", P, "form_multiline", "住宅ローン申込書\n勤務先名称\n例示物流株式会社\n所属部署\n配送管理課")
C("employer", P, "chat_or_list", "緊急連絡先メモ\n・平日日中は勤務先（見本化学株式会社 研究所）にいるとのこと")
C("employer", P, "variant_notation", "Employer: Kaku Logistics Inc. (架空ロジスティクス株式会社)\nPosition: Accountant")
C("employer", N, "general_text", "勤務先の情報は、ローン審査で返済能力を判断する材料の一つとされます。")
C("employer", N, "empty_or_masked", "勤務先：＿＿＿＿＿＿＿＿＿＿　電話：＿＿＿＿＿＿")
C("employer", N, "business_doc", "会社概要\n社名：架空商事株式会社\n設立：1985年\n従業員数：420名\n事業内容：食品卸売")
C("employer", N, "business_doc", "【求人】見本電機株式会社 大阪工場 製造スタッフ募集（時給1,400円）")
C("employer", A, "other", "勤務先：都内のIT企業（社名は非公開）", note="社名なし")

# family
C("family", P, "heading", "家族構成：妻（41歳）、長男（12歳）、長女（8歳）")
C("family", P, "sentence", "申告者は母親（78歳）と二人暮らしで、母親を扶養に入れている。")
C("family", P, "table", "続柄\t氏名\t年齢\t扶養\n妻\t宮之原 綾\t39\t有\n長男\t宮之原 蓮\t10\t有", ["name"])
C("family", P, "form_multiline", "扶養控除等（異動）申告書\n控除対象扶養親族\n続柄\n長女\n年齢\n17歳")
C("family", P, "chat_or_list", "1on1メモ\n- 子どもは小学生が2人\n- 配偶者は単身赴任中")
C("family", P, "variant_notation", "Family: Spouse (age 36), 2 children (ages 6 and 3)\n扶養人数：３名")
C("family", N, "general_text", "国の統計では、単独世帯の割合が長期的に増加傾向にあります。")
C("family", N, "empty_or_masked", "家族構成：続柄＿＿　年齢＿＿　扶養 □有 □無")
C("family", N, "business_doc", "見本ホテル ファミリープラン：大人2名・小学生2名まで1室28,000円（朝食付き）")
C("family", N, "general_text", "所得税の扶養控除は、その年の12月31日現在で16歳以上の扶養親族がいる場合に適用されます。")
C("family", A, "other", "婚姻状況：既婚", note="婚姻状況のみ")

# medical_history
C("medical_history", P, "heading", "既往歴：2021年 2型糖尿病（内服治療中）")
C("medical_history", P, "sentence", "本人は昨年10月にうつ病と診断され、現在も月1回心療内科に通院している。")
C("medical_history", P, "table", "受診日\t医療機関\t診断名\n2026/03/04\t見本クリニック\t急性胃腸炎\n2026/08/19\t架空総合病院\t右手首骨折")
C("medical_history", P, "form_multiline", "休職届\n傷病名\n腰椎椎間板ヘルニア\n療養期間\n2026年11月1日〜12月31日")
C("medical_history", P, "chat_or_list", "部長、すみません。娘がインフルエンザと診断されたので明日はお休みをいただきます。", amb=["family"], note="家族の診断。娘の存在は家族構成として判断保留")
C("medical_history", P, "variant_notation", "Medical history: Hypertension (dx 2019), on amlodipine 5mg\n既往：高血圧症")
C("medical_history", N, "general_text", "糖尿病は血糖値が慢性的に高くなる病気で、食事療法・運動療法・薬物療法を組み合わせて治療します。")
C("medical_history", N, "empty_or_masked", "既往歴：＿＿＿＿＿＿（該当があれば記入）")
C("medical_history", N, "business_doc", "架空総合病院 診療科案内：内科・外科・整形外科・小児科。外来受付 8:30〜11:30。")
C("medical_history", N, "general_text", "疾患コード E11 の当月請求件数：128件（全体集計）", note="集計値")
C("medical_history", A, "other", "既往歴：なし", note="否定")

# health_checkup
C("health_checkup", P, "heading", "健康診断結果：HbA1c 6.9%（判定 D 要精密検査）")
C("health_checkup", P, "sentence", "今年の定期健診で、本人の血圧は158/96で要再検査と判定された。")
C("health_checkup", P, "table", "項目\t結果\t判定\nLDLコレステロール\t172 mg/dL\tC\nγ-GTP\t118 U/L\tD")
C("health_checkup", P, "form_multiline", "定期健康診断個人票\n氏名\n赤羽 大地\n総合判定\nC（要経過観察）\n腹囲\n92.5cm", ["name"])
C("health_checkup", P, "chat_or_list", "産業医面談メモ\n・健診で肝機能（ALT 76）が要再検\n・本人は飲酒量を減らすと回答")
C("health_checkup", P, "variant_notation", "Health check (2026): BMI ２７．４, BP 142/90 → 判定：要指導")
C("health_checkup", N, "general_text", "LDLコレステロールの基準値は一般に140 mg/dL未満とされています。")
C("health_checkup", N, "empty_or_masked", "総合判定：A・B・C・D・E（該当に○）")
C("health_checkup", N, "business_doc", "見本健診センター 人間ドック基本コース 税込42,000円、オプションで胃カメラを追加できます。")
C("health_checkup", N, "general_text", "当社の2026年度定期健康診断の受診率は98.2%でした（全社集計）。", note="集計値")
C("health_checkup", A, "other", "健康診断：受診済み（結果は異常なし）", note="異常なしのみ")

# disability
C("disability", P, "heading", "障害者手帳：身体障害者手帳 2級（下肢機能障害）")
C("disability", P, "sentence", "本人は聴覚に障害があり、会議では文字通訳を利用している。")
C("disability", P, "table", "社員番号\t手帳種別\t等級\nE-3307\t精神障害者保健福祉手帳\t3級\nE-3312\t療育手帳\tB2")
C("disability", P, "form_multiline", "障害者雇用状況報告 個票\n障害の種類\n視覚障害\n手帳の等級\n1級")
C("disability", P, "chat_or_list", "来客対応メモ：明日の面接者は車いすを使用されているので、1階の会議室を確保してください。")
C("disability", P, "variant_notation", "Disability certificate: Class ３ (physical)\n障がい者手帳：所持")
C("disability", N, "general_text", "障害者雇用促進法は、一定規模以上の事業主に法定雇用率以上の障害者の雇用を義務付けています。")
C("disability", N, "empty_or_masked", "障害の有無：□有　□無（任意）")
C("disability", N, "business_doc", "架空ユニバーサル株式会社は、バリアフリー対応の会議室予約システムを提供しています。")
C("disability", N, "general_text", "当社の障害者雇用率は2.8%です（2026年6月1日現在、全社）。", note="集計値")
C("disability", A, "other", "配慮事項：長時間の立ち作業は避けたい（本人申告）", note="障害を推知させるだけ")

# race
C("race", P, "heading", "民族：アイヌ（本人申告）")
C("race", P, "sentence", "調査票には、本人の父方が在日コリアンの家系であるとの記載があった。")
C("race", P, "table", "氏名\t民族的出自\n見本 ジョアン\t日系ブラジル人", ["name"])
C("race", P, "form_multiline", "面談記録\n本人の民族的背景\n琉球民族であると自認")
C("race", P, "chat_or_list", "（不適切な採用メモの例）\n・候補者はクルド系とのこと")
C("race", P, "variant_notation", "Ethnicity: Han Chinese\n人種・民族：漢民族")
C("race", N, "general_text", "人種差別撤廃条約は1965年に国連総会で採択されました。")
C("race", N, "empty_or_masked", "民族：＿＿＿（この欄は記入しないでください）")
C("race", N, "business_doc", "見本エスニック食堂：タイ料理・ベトナム料理を提供。ランチ 1,100円から。")
C("race", N, "general_text", "アイヌ施策推進法は、アイヌの人々の誇りが尊重される社会の実現を目的としています。")
C("race", A, "other", "国籍：ブラジル", note="国籍のみ")

# creed
C("creed", P, "heading", "信仰：キリスト教（プロテスタント）")
C("creed", P, "sentence", "本人は見本党の党員で、地域支部の役員も務めている。")
C("creed", P, "table", "氏名\t所属宗教団体\n宮之原 透\t架空教会", ["name"])
C("creed", P, "form_multiline", "身上調査票（不適正項目）\n支持政党\n試験改革党")
C("creed", P, "chat_or_list", "懇親会の件、桐生 美咲さんはイスラム教徒なので、豚肉とお酒なしのメニューでお願いします。", ["name"])
C("creed", P, "variant_notation", "Religion: Buddhist (Jodo Shinshu)\n宗派：浄土真宗")
C("creed", N, "general_text", "日本国憲法第20条は信教の自由を保障しています。")
C("creed", N, "empty_or_masked", "宗教：＿＿＿（任意・空欄可）")
C("creed", N, "business_doc", "架空寺院 年間行事のご案内：除夜の鐘、春秋のお彼岸法要。")
C("creed", N, "general_text", "（例示）世論調査では「支持政党なし」と答えた人の割合が最も高かった。", note="集計")
C("creed", A, "other", "出身校：見本学院高等学校（キリスト教系）を卒業", ["education"], note="宗教系学校の卒業から信条を推知させるだけ")

# social_status
C("social_status", P, "heading", "身元調査報告：対象者の出身地は同和地区とされる")
C("social_status", P, "sentence", "本人が被差別部落の出身であることを理由に、交際に反対されたとの相談を受けた。")
C("social_status", P, "table", "対象者\t調査事項\t結果\n瀬能 和也\t出自\t旧部落出身の記載あり", ["name"])
C("social_status", P, "form_multiline", "身元調査票（違法な調査の例）\n本籍地の地区区分\n同和対象地区\n照会方法\n興信所経由")
C("social_status", P, "chat_or_list", "相談窓口ログ：相談者は、自身が部落出身であることを職場で暴露されたと訴えている。")
C("social_status", P, "variant_notation", "Social origin: Buraku descent (noted in background check)\n社会的身分：部落出身")
C("social_status", N, "general_text", "部落差別の解消の推進に関する法律は2016年に施行されました。")
C("social_status", N, "empty_or_masked", "本籍：＿＿＿（採用選考では記入を求めません）")
C("social_status", N, "business_doc", "見本人権啓発センター 研修案内：同和問題の歴史と現状（2時間）")
C("social_status", N, "general_text", "社会的身分による差別は、日本国憲法第14条で禁止されています。")
C("social_status", A, "other", "本籍地：見本県架空郡試験町大字例示", note="本籍のみで推知させるだけ")

# criminal_record
C("criminal_record", P, "heading", "前科：2018年 道路交通法違反（罰金30万円）")
C("criminal_record", P, "sentence", "応募者は過去に窃盗罪で懲役1年・執行猶予3年の刑を受けたことがある。")
C("criminal_record", P, "table", "氏名\t罪名\t刑\n根津 亮平\t詐欺\t懲役2年6月", ["name"])
C("criminal_record", P, "form_multiline", "賞罰\n罰\n2020年 傷害罪により罰金刑")
C("criminal_record", P, "chat_or_list", "内部通報メモ\n・取引先の担当者に横領の前科があるとの匿名情報")
C("criminal_record", P, "variant_notation", "Criminal record: Convicted of fraud (2019), 2 years (suspended)\n前科：有")
C("criminal_record", N, "general_text", "刑法では、刑の執行を終わってから一定期間を経過すると刑の言渡しは効力を失うと定められています。")
C("criminal_record", N, "empty_or_masked", "賞罰：あり・なし（ありの場合の内容：＿＿＿＿）")
C("criminal_record", N, "general_text", "（例示）再犯者率はここ数年おおむね5割前後で推移している。", note="統計")
C("criminal_record", N, "business_doc", "見本法律事務所 刑事弁護の費用：着手金33万円から。")
C("criminal_record", A, "other", "賞罰：なし", note="否定")

# criminal_procedure
C("criminal_procedure", P, "heading", "処分状況：2026年9月12日 逮捕、9月30日 不起訴（嫌疑不十分）")
C("criminal_procedure", P, "sentence", "社員の大河内 修が、昨夜酒気帯び運転の疑いで現行犯逮捕されたと警察から連絡があった。", ["name"])
C("criminal_procedure", P, "table", "日付\t手続\n2026/05/02\t書類送検\n2026/06/18\t略式起訴")
C("criminal_procedure", P, "form_multiline", "少年事件記録（写）\n事件の種類\n窃盗\n手続の状況\n家庭裁判所に送致、審判期日 12月3日")
C("criminal_procedure", P, "chat_or_list", "総務チャット：営業部の社員が傷害容疑で取り調べを受けているそうです。本人から明日休むと連絡がありました。")
C("criminal_procedure", P, "variant_notation", "Status: Indicted (起訴) on 2026-10-01; trial pending\n被告人：本人")
C("criminal_procedure", N, "general_text", "刑事訴訟法では、司法警察員は逮捕から48時間以内に被疑者を検察官に送致しなければなりません。")
C("criminal_procedure", N, "general_text", "（例示）昨年の刑法犯の認知件数は前年を上回った。", note="統計")
C("criminal_procedure", N, "business_doc", "見本法律事務所：少年事件・刑事事件の初回相談無料（30分）")
C("criminal_procedure", N, "empty_or_masked", "身柄の状況：＿＿＿（該当なしの場合は空欄）")
C("criminal_procedure", A, "other", "長期欠勤の理由：「警察の関係」とだけ聞いている", note="推知させるだけ")

# crime_victim
C("crime_victim", P, "heading", "被害状況：2026年8月 特殊詐欺被害（被害額 280万円）")
C("crime_victim", P, "sentence", "本人は先月、帰宅途中にひったくりの被害に遭い、警察に被害届を提出した。")
C("crime_victim", P, "table", "相談者\t被害内容\t届出\n芦原 志保\tストーカー被害\t済", ["name"])
C("crime_victim", P, "form_multiline", "犯罪被害者等給付金 支給申請書\n被害の種類\n傷害\n被害日\n2026年4月7日")
C("crime_victim", P, "chat_or_list", "人事より：来週から在宅勤務を許可します。DV被害で避難中とのことなので、住所は社内でも非開示にしてください。")
C("crime_victim", P, "variant_notation", "Victim of: Burglary (2026-02)\n被害者：本人／被害届 受理済")
C("crime_victim", N, "general_text", "特殊詐欺の被害は高齢者に多く、各地で注意が呼びかけられています。")
C("crime_victim", N, "general_text", "犯罪被害者等基本法は2004年に成立しました。")
C("crime_victim", N, "business_doc", "見本セキュリティ株式会社：ホームセキュリティ月額3,300円。空き巣対策に。")
C("crime_victim", N, "empty_or_masked", "被害の有無：□有　□無")
C("crime_victim", A, "other", "相談内容：近隣住民とのトラブル（詳細は本人の希望により記載しない）", note="犯罪被害か不明")

# password_plain
C("password_plain", P, "heading", "初期パスワード：Kx7#mP2qL9")
C("password_plain", P, "sentence", "VPN のパスワードは Mihon!2026sec に変更しておきました。")
C("password_plain", P, "table", "user\tpassword\nuser01\tQw8$zR41uT\nuser02\tsakura0412!")
C("password_plain", P, "form_multiline", "Wi-Fi 接続情報\nSSID\nKAKU-OFFICE-5G\nパスワード\nf3Gh9-kLm2-Pq7x")
C("password_plain", P, "chat_or_list", "#infra 本番DBの root パス、とりあえず `Tst_r00t#77` にしてあります（後で変えます）")
C("password_plain", P, "variant_notation", "DB_HOST=db.kaku-shoji.example\nDB_PASSWORD=Ex4mple_Pw!93", note="設定ファイル形式")
C("password_plain", N, "empty_or_masked", "パスワード：********")
C("password_plain", N, "general_text", "パスワードは12文字以上で、英大文字・小文字・数字・記号を含めてください。")
C("password_plain", N, "other", "PASSWORD_MIN_LENGTH=12\npassword_reset_token_expire=3600", note="設定名だけで値はパスワードでない")
C("password_plain", N, "business_doc", "見本パスワードマネージャー：月額300円で家族5人まで利用できます。")
C("password_plain", A, "other", "パスワードのヒント：最初に飼った犬の名前", note="ヒントのみ")

# password_hash
C("password_hash", P, "heading", f"password_hash: {BCRYPT1}", note="bcrypt")
C("password_hash", P, "sentence", f"移行対象ユーザーのハッシュ値は {ARGON} で、再ハッシュは不要です。", note="argon2id")
C("password_hash", P, "table", f"id\temail\tpassword_hash\n1042\tuser1042@kaku-shoji.example\t{SHA512C_1}", ["email"], note="sha512-crypt")
C("password_hash", P, "form_multiline", f"admin:\n  password:\n    {PBKDF2}", note="pbkdf2、値が別行")
C("password_hash", P, "chat_or_list", f"ログ抜粋：shadow ファイルの1行\nbackup:{SHA512C_2}:19700:0:99999:7:::", note="rounds付き sha512-crypt")
C("password_hash", P, "variant_notation", f'PASSWORD_HASH="{BCRYPT2Y}"', note="$2y$ 形式")
C("password_hash", N, "similar_number", f"SHA-256 (setup-2.4.1.zip) = {HEX64}", note="ファイルのチェックサム")
C("password_hash", N, "similar_number", f"コミット {HEX40} で設定ファイルの誤字を修正しました。", note="コミットハッシュ")
C("password_hash", N, "general_text", "bcrypt の値はソルトとコスト係数を含む形式で、$2b$ などの接頭辞で始まります。")
C("password_hash", N, "empty_or_masked", "password_hash: [REDACTED]")
C("password_hash", A, "other", f"token_digest: {HEX64B}", note="パスワード由来か不明なダイジェスト")

# email
C("email", P, "heading", "メール：tm.1042@kaku-shoji.example")
C("email", P, "sentence", "請求書のPDFは s.kaneda1988@mail.example 宛てに送ってください。")
C("email", P, "table", "No\tE-mail\n1\tabc.mihon@ex-mail.example\n2\tz-77k@post.example")
C("email", P, "form_multiline", "連絡先\nメールアドレス\nmorning.coffee.42@example.test")
C("email", P, "chat_or_list", "From: 架空商事 総務部 <soumu@kaku-shoji.example>\nTo: you@shiken.example\n件名：健康診断日程のご案内", note="メールヘッダー")
C("email", P, "variant_notation", "E-mail：user0815＠mihon-net.example", note="全角＠")
C("email", N, "similar_number", "パッケージ @mihon/ui@3.2.1 をインストールしてください。", note="パッケージ指定")
C("email", N, "general_text", "メールアドレスは「ローカル部＠ドメイン」の形式で表されます。")
C("email", N, "empty_or_masked", "メールアドレス：t***@***.example（伏字）")
C("email", N, "similar_number", "公式SNSアカウント：@mihon_official", note="SNSのハンドル")
C("email", A, "other", "連絡先：yamada [at] shiken.example", note="難読化表記")

# phone
C("phone", P, "heading", "電話番号：090-4821-7365")
C("phone", P, "sentence", "折り返しは携帯の 080 3392 1047 までお願いしますとのこと。")
C("phone", P, "table", "氏名\t内線\t携帯\n桐生 美咲\t2041\t070-5518-2093", ["name"])
C("phone", P, "form_multiline", "緊急連絡先\n電話\n06-6948-2173")
C("phone", P, "chat_or_list", "伝言メモ：取引先の担当者から電話あり。03-5839-2047 に折り返し希望。")
C("phone", P, "variant_notation", "TEL：０９０（２２１８）４４７０\nMobile: +81 90-2218-4470", note="全角括弧と国番号表記")
C("phone", N, "similar_number", "部品番号 080-3392-104A は廃番になりました。", note="電話に似た部品番号")
C("phone", N, "similar_number", "注文日時 2026-03-04 10:47　伝票番号 0312-4458-90", note="伝票番号")
C("phone", N, "empty_or_masked", "電話番号：090-****-****")
C("phone", N, "general_text", "携帯電話の番号は070・080・090などで始まる11桁です。")
C("phone", A, "other", "代表電話：03-6823-1940（架空商事株式会社 本社）", note="法人の代表番号")

# address
C("address", P, "heading", "住所：東京都練馬区みほん台3丁目14番7号")
C("address", P, "sentence", "本人は大阪府堺市北区例示町2-8-15のアパートに住んでいる。")
C("address", P, "table", "氏名\t住所\n根津 亮平\t神奈川県川崎市中原区試験町1-22-3 見本ハイツ203", ["name"])
C("address", P, "form_multiline", "現住所\n〒064-0821\n北海道札幌市中央区架空通西18丁目2番5号")
C("address", P, "chat_or_list", "配達先メモ：福岡県福岡市早良区見本ケ丘4丁目6-11、不在時は宅配ボックスへ")
C("address", P, "variant_notation", "Address: 2-9-4 Mihondai, Aoba-ku, Sendai-shi, Miyagi\n宮城県仙台市青葉区見本台２－９－４")
C("address", N, "general_text", "住居表示制度では、街区符号と住居番号を組み合わせて住所を表します。")
C("address", N, "empty_or_masked", "住所：東京都練馬区＊＊＊＊＊＊", note="市区町村以降が伏字")
C("address", N, "business_doc", "架空商事株式会社 東京支店は2026年12月に移転します（移転先は追ってお知らせします）。")
C("address", N, "general_text", "郵便番号 064-0821 の地域は札幌市中央区にあります。", note="番地なし")
C("address", A, "other", "本社所在地：東京都千代田区見本町1-2-3（架空商事株式会社）", note="法人の所在地")

# name
C("name", P, "heading", "氏名：宮之原 透")
C("name", P, "sentence", "本日の打合せには、先方から桐生 美咲様がご出席されました。")
C("name", P, "table", "No\t氏名\tフリガナ\n1\t大河内 修\tオオコウチ オサム\n2\t戸叶 智子\tトガノウ トモコ")
C("name", P, "form_multiline", "申請者\n氏名（自署）\n芦原 志保")
C("name", P, "chat_or_list", "議事録\n出席者：瀬能 和也、赤羽 大地、根津 亮平\n議題：年末調整スケジュール")
C("name", P, "variant_notation", "Name: MIYANOHARA Toru\n氏名：ミヤノハラ　トオル")
C("name", N, "business_doc", "見本電機株式会社 製品名：みほんクリーナー Z")
C("name", N, "empty_or_masked", "氏名：＿＿＿＿＿＿＿（楷書で記入）")
C("name", N, "general_text", "日本で多い姓には佐藤、鈴木、高橋などがあります。", note="姓の一般論")
C("name", N, "similar_number", "会議室名：桜・楓・椿（予約はポータルから）", note="人名に似た語")
C("name", A, "other", "記入例：山田 太郎", note="記入例の見本氏名")


def main():
    ids = [c["case_id"] for c in CASES]
    assert len(ids) == len(set(ids))
    for c in CASES:
        for k in c["present"] + c["ambiguous"]:
            assert k in ITEMS, (c["case_id"], k)
        assert not set(c["present"]) & set(c["ambiguous"]), c["case_id"]
    OUT.write_text(json.dumps(CASES, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(CASES)} cases to {OUT}")


if __name__ == "__main__":
    main()
