#!/usr/bin/env python3
"""Jevと施設内判断モデルの公開説明・論文を保存する。モデル重みは取得しない。"""
import concurrent.futures
import json
import download_privacy_materials as base

SOURCES = [
 ('jev_intro','TypeSafe Jev公式説明','https://docs.typesafe.ai/introduction'),
 ('jev_launch','TypeSafe System OneとJev発表','https://typesafe.ai/blog/introducing-system-one-models-and-jev'),
 ('jev_models','TypeSafeモデル提供情報','https://docs.typesafe.ai/models'),
 ('bert','BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding','https://arxiv.org/pdf/1810.04805'),
 ('modernbert_ja_jev','日本語ModernBERT Jev形式モデルカード','https://huggingface.co/argos1111/modernbert-ja-310m-jev'),
 ('jev_local','Jev Local公開実装','https://github.com/Argos1111/jev_local'),
 ('laya','Laya公開モデルと構成','https://huggingface.co/convaiinnovations/laya'),
 ('anyjev','AnyJev公開実装','https://github.com/nokia-applied-research/AnyJev'),
 ('anyjev_paper','AnyJev Technical Report','https://arxiv.org/pdf/2610.00831'),
 ('tacit_17b','Tacit-1.7B公開モデルカード','https://huggingface.co/morriszjm/Tacit-1.7B'),
 ('tacit_4b','Tacit-4B公開モデルカード','https://huggingface.co/morriszjm/Tacit-4B'),
]

def main():
 base.RAW=base.ROOT/'research/disclosures/raw/jev_20261007'
 base.RAW.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  records=list(pool.map(base.fetch,SOURCES))
 target=base.ROOT/'research/technology/jev_local_sources_20261007.json'
 target.write_text(json.dumps({'research_date':'2026-10-07','note':'公開文書・論文のみ取得。重みの取得、実行、精度検証は行っていない。公式と非公式を区別する。','documents':records},ensure_ascii=False,indent=2)+'\n')
 for r in records:print(r['id'],r['status'],r.get('pages','HTML'),flush=True)

if __name__=='__main__':main()
