#!/usr/bin/env python3
"""v3のファイル構造・全バイト・生成元を固定基準と照合する。通信なし。"""
import argparse
import hashlib
import json
from pathlib import Path

import build

HERE = Path(__file__).resolve().parent
BASELINE = HERE / 'dataset-reference.json'
SOURCES = ('build.py', 'catalog.py', 'samples.py', '../dataset.py', 'reproduce.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(dataset):
    dataset = Path(dataset)
    if not dataset.is_dir() or dataset.is_symlink():
        raise ValueError('実体のあるデータセットディレクトリを指定してください')
    paths = sorted(dataset.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('シンボリックリンクは比較対象にできません')
    truth = json.loads((dataset / 'ground_truth.json').read_text(encoding='utf-8'))
    return {
        'schema_version': 1,
        'dataset_version': build.VERSION,
        'truth_revision': build.TRUTH_REVISION,
        'case_count': len(truth),
        'split_counts': {s: sum(r['split'] == s for r in truth) for s in ('開発', '評価')},
        'sources': {name: digest(HERE / name) for name in SOURCES},
        'directories': [p.relative_to(dataset).as_posix() for p in paths if p.is_dir()],
        'files': {p.relative_to(dataset).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)}
                  for p in paths if p.is_file()},
    }


def verify(dataset, reference=BASELINE):
    expected = json.loads(Path(reference).read_text(encoding='utf-8'))
    actual = snapshot(dataset)
    differences = [key for key in actual if actual[key] != expected.get(key)]
    differences += [key for key in expected if key not in actual]
    if differences:
        raise ValueError('再現基準と一致しません: ' + ', '.join(differences))
    return {'status': '一致', 'files': len(actual['files']), 'cases': actual['case_count'],
            'directories': actual['directories'], 'reference_sha256': digest(Path(reference))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    make = sub.add_parser('make', help='新規生成後に固定基準と照合する')
    make.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('verify', help='既存の生成物を固定基準と照合する')
    check.add_argument('--dataset', type=Path, required=True)
    record = sub.add_parser('record', help='意図した仕様変更時だけ、新規パスへ比較基準を書き出す')
    record.add_argument('--dataset', type=Path, required=True)
    record.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'record':
        data = json.dumps(snapshot(args.dataset), ensure_ascii=False, indent=2) + '\n'
        with args.output.open('xb') as stream:
            stream.write(data.encode('utf-8'))
        result = {'reference': str(args.output), 'status': '作成。採用前に差分を確認してください'}
    else:
        if args.command == 'make':
            build.make(args.output)
        result = verify(args.output if args.command == 'make' else args.dataset)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
