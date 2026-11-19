"""試験で使用した4種類×4件のファイル属性対照を、通信せず生成する。"""
import argparse
import hashlib
import json
import re
from pathlib import Path

FIND = 'WORKFLOWCONTROL'
MARK = 'NAMECHECK'


def make_pdf(text):
    stream = f'BT /F1 12 Tf 30 740 Td ({text}) Tj ET'.encode('ascii')
    objects = [
        b'<</Type/Catalog/Pages 2 0 R>>',
        b'<</Type/Pages/Kids[3 0 R]/Count 1>>',
        b'<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>',
        f'<</Length {len(stream)}>>\nstream\n'.encode('ascii') + stream + b'\nendstream',
        b'<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>',
    ]
    pdf = b'%PDF-1.4\n'
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += f'{i} 0 obj\n'.encode('ascii') + obj + b'\nendobj\n'
    start = len(pdf)
    index = b''.join(f'{offset:010} 00000 n \n'.encode('ascii') for offset in offsets)
    trailer = f'trailer\n<</Size 6/Root 1 0 R>>\nstartxref\n{start}\n%%EOF\n'.encode('ascii')
    return pdf + b'xref\n0 6\n0000000000 65535 f \n' + index + trailer


FIXTURES = {
    'literal': [
        ('exact', 'plain.txt', FIND, False, 1),
        ('quoted', 'quote.txt', 'Quote: ' + FIND, False, 1),
        ('near', 'near.txt', 'WORKFLOWCONTROX', False, 0),
        ('filename_only', FIND + '.txt', 'unrelated', False, 0),
    ],
    'filename': [
        ('whole', MARK + '.txt', 'unrelated', False, 1),
        ('substring', MARK + '-COPY.txt', 'unrelated', False, 1),
        ('body_only', 'other.txt', MARK, False, 0),
        ('near', 'NAMECHECX.txt', 'unrelated', False, 0),
    ],
    'extension': [
        ('matching_pdf', 'real.pdf', 'fixture', True, 1),
        ('mismatch_pdf', 'fake.pdf', 'fixture', False, 1),
        ('mismatch_dat', 'real.dat', 'fixture', True, 0),
        ('matching_txt', 'real.txt', 'fixture', False, 0),
    ],
    'mime': [
        ('matching_pdf', 'content.pdf', 'fixture', True, 1),
        ('mismatch_pdf', 'content-plain.pdf', 'fixture', False, 0),
        ('mismatch_dat', 'content-pdf.dat', 'fixture', True, 1),
        ('matching_txt', 'content.txt', 'fixture', False, 0),
    ],
}


def make(output, marker):
    if not re.fullmatch(r'DLPVERIFY[A-Z]{8,24}', marker):
        raise ValueError('対照文字列には DLPVERIFY に続けて英大文字を8〜24文字指定してください')
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for item, cases in FIXTURES.items():
        directory = output / item
        directory.mkdir()
        for scenario, name, content, pdf, expected in cases:
            mime = 'application/pdf' if pdf else 'text/plain'
            text = f'DLPHEAD {marker} DLPTAIL {content}'
            data = make_pdf(text) if pdf else text.encode('utf-8')
            path = directory / name
            path.write_bytes(data)
            rows.append({
                'item': item, 'scenario': scenario, 'file': path.relative_to(output).as_posix(),
                'display_name': name, 'upload_mime_type': mime, 'condition_truth': expected,
                'sha256': hashlib.sha256(data).hexdigest(),
            })
    (output / 'property_ground_truth.json').write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8',
    )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--marker', required=True)
    args = parser.parse_args()
    make(args.output, args.marker)


if __name__ == '__main__':
    main()
