---
library_name: onnxruntime
language:
  - ja
tags:
  - ner
  - pii
  - token-classification
  - onnx
  - japanese
license: apache-2.0
pipeline_tag: token-classification
---

# PII-JA-Detection (ONNX)

日本語PII（個人識別情報）検出モデルのONNXエクスポート版です。

## モデル概要

- **ベースモデル**: `tohoku-nlp/bert-base-japanese`
- **タスク**: トークン分類 (BIO tagging)
- **対応PIIタイプ**: 18種類

## 検出可能なPIIタイプ

| タイプ | 説明 |
|--------|------|
| PERSON_NAME | 氏名 |
| ORGANIZATION_NAME | 組織名 |
| PHONE_NUMBER | 電話番号 |
| EMAIL | メールアドレス |
| ADDRESS | 住所 |
| MY_NUMBER | マイナンバー |
| PASSPORT_NUMBER | パスポート番号 |
| DRIVER_LICENSE | 運転免許証番号 |
| INSURANCE_NUMBER | 保険証番号 |
| EMPLOYEE_ID | 社員番号 |
| STUDENT_ID | 学籍番号 |
| BANK_ACCOUNT | 銀行口座番号 |
| CREDIT_CARD | クレジットカード番号 |
| DATE_OF_BIRTH | 生年月日 |
| AGE | 年齢 |
| IP_ADDRESS | IPアドレス |
| URL | URL |
| USERNAME | ユーザー名 |

## 使い方

```python
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

# セッション作成
session = ort.InferenceSession("model.onnx")
tokenizer = AutoTokenizer.from_pretrained(".")

# 推論
text = "田中太郎の電話番号は090-1234-5678です。"
inputs = tokenizer(text, return_tensors="np", padding="max_length", max_length=512)
logits = session.run(None, {
    "input_ids": inputs["input_ids"],
    "attention_mask": inputs["attention_mask"],
})[0]

predictions = np.argmax(logits, axis=-1)
```

## ラベルマッピング

BIOタグ方式（37ラベル）: `O`, `B-PERSON_NAME`, `I-PERSON_NAME`, ...

## 入出力仕様

| 入力 | 形状 | 型 |
|------|------|----|
| input_ids | [batch_size, sequence_length] | int64 |
| attention_mask | [batch_size, sequence_length] | int64 |

| 出力 | 形状 | 型 |
|------|------|----|
| logits | [batch_size, sequence_length, 37] | float32 |
