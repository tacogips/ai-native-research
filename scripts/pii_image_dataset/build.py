#!/usr/bin/env python3
"""LIGHTの画像・文書・圧縮資料とDrive配置ディレクトリをまとめて作成する。"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import generate
import generate_all


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--font',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20261113)
    parser.add_argument('--sheetjs-module',type=Path,help='インストール済みxlsxモジュールのパス')
    args=parser.parse_args()
    if args.output.exists():parser.error('新しい出力先を指定してください')
    if not args.font.is_file():parser.error('日本語フォントが存在しません')
    if args.sheetjs_module:os.environ['PII_XLSX_MODULE']=str(args.sheetjs_module.resolve())
    elif 'PII_XLSX_MODULE' not in os.environ:
        local_module=Path(__file__).parent/'node_modules/xlsx'
        if local_module.is_dir():os.environ['PII_XLSX_MODULE']=str(local_module.resolve())
    for command in ['node','zip']:
        if not shutil.which(command):parser.error(command+'が必要です')
    subprocess.run(['node','-e',"require(process.env.PII_XLSX_MODULE ? require('node:path').resolve(process.env.PII_XLSX_MODULE) : 'xlsx')"],check=True)
    # 中間画像を出力の外に置き、同じ画像の二重保存で容量を増やさない。
    with tempfile.TemporaryDirectory(prefix='pii-light-build-') as folder:
        images=Path(folder)/'images'
        generate.generate(images,args.font,args.seed)
        generate_all.main(SimpleNamespace(images=images,output=args.output,font=args.font))
    print('生成完了。verify_all.py・verify_media.py・形式対応表の検証を続けてください。')


if __name__=='__main__':main()
