"""標準のunittest実行でv3の追加試験も漏らさない。"""
import unittest
from pathlib import Path


def load_tests(loader, tests, pattern):
    # 呼出元の探索基点を変更しないよう、独立したローダーを使う。
    extended = Path(__file__).resolve().parent / 'extended'
    return unittest.TestLoader().discover(str(extended), pattern='test_*.py', top_level_dir=str(extended))
