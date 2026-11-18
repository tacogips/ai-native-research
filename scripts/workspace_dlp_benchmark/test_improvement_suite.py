"""標準のunittest実行で改善案の検証試験（improvement/）も漏らさない。"""
import unittest
from pathlib import Path


def load_tests(loader, tests, pattern):
    improvement = Path(__file__).resolve().parent / 'improvement'
    return unittest.TestLoader().discover(str(improvement), pattern='test_*.py', top_level_dir=str(improvement))
