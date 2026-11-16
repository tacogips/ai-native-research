"""実行証拠の保存境界と時刻・指紋の共通処理。"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]


def private_path(path):
    path = Path(path).resolve()
    if path.is_relative_to(REPOSITORY):
        raise ValueError('実行設定・識別子・観測・報告はリポジトリ外へ置いてください')
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def write_private(path, value):
    path = private_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 作成直後から所有者だけに読ませる。既存報告は最後に置換する。
    import os
    import tempfile
    descriptor, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('時刻にはUTCとの時差が必要です')
    return parsed.astimezone(timezone.utc)


def now():
    return datetime.now(timezone.utc).isoformat()


def input_file(dataset, relative):
    root = (Path(dataset) / 'drive_upload').resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('検査資料の参照が入力範囲外、または通常ファイルではありません')
    return path
