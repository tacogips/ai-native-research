#!/usr/bin/env python3
"""公開資料を取得し、原本・抽出本文・取得記録を保存する。標準ライブラリとPopplerを使用。"""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import urllib.request
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / 'research/disclosures/raw/privacy_20261007'
RECORD = ROOT / 'research/disclosures/privacy_retrieval_20261007.json'

# 日付を含むURLは今回確認した版を固定する。再取得時も最新版に自動置換しない。
SOURCES = [
 ('ppc_simple', 'はじめての個人情報保護法 シンプルレッスン', 'https://www.ppc.go.jp/files/pdf/simple_lesson_2022.pdf'),
 ('ppc_handbook', '民間事業者向け 個人情報保護法 ハンドブック', 'https://www.ppc.go.jp/files/pdf/APPI_handbook_for_company2022.pdf'),
 ('ppc_general', '個人情報保護法ガイドライン 通則編', 'https://www.ppc.go.jp/files/pdf/260614_guidelines01.pdf'),
 ('ppc_foreign', '個人情報保護法ガイドライン 外国にある第三者への提供編', 'https://www.ppc.go.jp/files/pdf/251212_guidelines02.pdf'),
 ('ppc_anonymization', '個人情報保護法ガイドライン 仮名加工情報 匿名加工情報編', 'https://www.ppc.go.jp/files/pdf/260401_guidelines04.pdf'),
 ('ppc_qa', '個人情報保護法ガイドラインに関するQ&A', 'https://www.ppc.go.jp/files/pdf/250701_APPI_QA.pdf'),
 ('ppc_supplementary', 'EU及び英国域内から十分性認定により移転を受けた個人データの補完的ルール', 'https://www.ppc.go.jp/files/pdf/Supplementary_Rules_jp.pdf'),
 ('ppc_reform_2026', '令和8年改正 個人情報保護法等の一部を改正する法律について', 'https://www.ppc.go.jp/files/pdf/260717_kaiseihounitsuite.pdf'),
 ('ppc_reform_law', '令和8年改正法 条文', 'https://www.ppc.go.jp/files/pdf/260717_houritsu.pdf'),
 ('ipa_sme', '中小企業の情報セキュリティ対策ガイドライン 第4.0版', 'https://www.ipa.go.jp/security/guide/sme/ug65p90000019cbk-att/sme_guideline_v4.0.pdf'),
 ('ftc_personal', 'Protecting Personal Information A Guide for Business', 'https://www.ftc.gov/system/files/documents/plain-language/pdf-0136_proteting-personal-information.pdf'),
 ('nist_pf10', 'NIST Privacy Framework Version 1.0', 'https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.01162020.pdf'),
 ('oecd_privacy', 'OECD Privacy Guidelines OECD LEGAL 0188', 'https://legalinstruments.oecd.org/public/doc/114/114.en.pdf'),
 ('privacy_manifesto', 'The Privacy Engineer\'s Manifesto', 'https://link.springer.com/content/pdf/10.1007/978-1-4302-6356-2.pdf'),
 ('hoepman', 'Privacy Design Strategies', 'https://arxiv.org/pdf/1210.6621'),
 ('narayanan', 'Robust De-anonymization of Large Sparse Datasets', 'https://systems.cs.columbia.edu/private-systems-class/papers/Narayanan2008Robust.pdf'),
 ('dwork_roth', 'The Algorithmic Foundations of Differential Privacy', 'https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf'),
 ('gdpr', 'GDPR 官報掲載原文', 'https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A32016R0679'),
 ('gdpr_ja', 'GDPR 条文 個人情報保護委員会の仮日本語訳', 'https://www.ppc.go.jp/files/pdf/gdpr-provisions-ja.pdf'),
 ('gdpr_preface_ja', 'GDPR 前文 個人情報保護委員会の仮日本語訳', 'https://www.ppc.go.jp/files/pdf/gdpr-preface-ja.pdf'),
 ('crs_us', 'Preemption and Privacy Law', 'https://www.congress.gov/crs_external_products/R/PDF/R48667/R48667.2.pdf'),
 ('edpb_basics', 'EDPB Data protection basics', 'https://www.edpb.europa.eu/sme/learn-the-basics/data-protection-basics_en'),
 ('edpb_compliance', 'EDPB Be compliant', 'https://www.edpb.europa.eu/sme/be-compliant/be-compliant_en'),
 ('edpb_home', 'EDPB Data protection guide for small business', 'https://www.edpb.europa.eu/sme_en'),
 ('edpb_rights', 'EDPB Respect individuals rights', 'https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en'),
 ('edpb_breaches', 'EDPB Data breaches', 'https://www.edpb.europa.eu/sme/assess-the-risks/data-breaches_en'),
 ('cppa_faq', 'California Privacy Protection Agency FAQ', 'https://www.cppa.ca.gov/faq.html'),
 ('ftc_security', 'Start with Security A Guide for Business', 'https://www.ftc.gov/business-guidance/resources/start-security-guide-business'),
 ('nist_status', 'NIST Privacy Framework 公開状況', 'https://www.nist.gov/privacy-framework'),
 ('ppc_reform_status', '令和8年改正法 公開状況', 'https://www.ppc.go.jp/personalinfo/legal/r8kaiseihogohou/'),
]

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'li', 'tr', 'br'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.hidden:
            self.hidden -= 1
    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

def fetch(source):
    ident, title, url = source
    rec = {'id': ident, 'title': title, 'source_url': url,
           'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=50) as response:
            data = response.read()
            rec['resolved_url'] = response.url
            rec['content_type'] = response.headers.get('Content-Type', '')
        if not data:
            raise ValueError('応答本文が空')
        is_pdf = data.startswith(b'%PDF-')
        if not is_pdf and 'html' not in rec['content_type'].lower():
            raise ValueError('PDFまたはHTMLではない応答')
        if not is_pdf and ('.pdf' in url or ident in ('hoepman', 'gdpr')):
            raise ValueError('PDF要求に対してHTMLが返された')
        path = RAW / (ident + ('.pdf' if is_pdf else '.html'))
        path.write_bytes(data)
        txt = RAW / (ident + '.txt')
        rec.update(local_file=str(path.relative_to(ROOT)), bytes=len(data),
                   sha256=hashlib.sha256(data).hexdigest(), format='pdf' if is_pdf else 'html')
        if is_pdf:
            result = subprocess.run(['pdftotext', '-layout', str(path), str(txt)], capture_output=True, text=True, check=True)
            info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, check=True).stdout
            rec['pages'] = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
        else:
            parser = TextParser()
            parser.feed(data.decode('utf-8', errors='replace'))
            txt.write_text(re.sub(r'\n[ \t\r]*\n+', '\n\n', ''.join(parser.parts)), encoding='utf-8')
        rec.update(text_file=str(txt.relative_to(ROOT)), text_characters=len(txt.read_text()), status='取得済み')
    except Exception as exc:
        rec.update(status='取得失敗', error=str(exc))
    return rec

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        records = list(executor.map(fetch, SOURCES))
    RECORD.write_text(json.dumps({'retrieved_at': '2026-10-07', 'raw_storage': str(RAW.relative_to(ROOT)),
        'note': '原本と抽出本文はGit管理外。PDF頁番号は先頭を1とする。HTMLは原本保存と本文抽出。',
        'documents': records}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for rec in records:
        print(rec['id'], rec['status'], rec.get('pages', 'HTML'), rec.get('bytes', ''), rec.get('error', ''), flush=True)

if __name__ == '__main__':
    main()
