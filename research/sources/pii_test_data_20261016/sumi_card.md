---
license: cc-by-sa-4.0
language:
- ja
task_categories:
- token-classification
tags:
- pii
- privacy
- japanese
- synthetic
- named-entity-recognition
size_categories:
- 10K<n<100K
---

# Sumi — synthetic Japanese PII corpus

**This dataset contains no real personal information.** Every name, address, phone
number, email address, date of birth, bank account, member ID and My-Number-shaped
digit string is generated with a seeded RNG and inserted into the text **while
recording the offsets**, so the gold spans are correct by construction rather than
recovered by searching afterwards.

Built for [Sumi](https://github.com/NagaYu/sumi), a Japanese PII detector.

## Why this dataset exists

Japanese PII detection fails in a specific way: surnames that are also ordinary
nouns (森 "forest", 林 "woods", 泉 "spring", 大和, 青木), place names that are also
surnames (長野, 福島, 千葉, 山口), company names built from surnames, honorific
boundaries (様 / さん / 氏 / 殿, and the many uses of 様 that are not personal at
all), part numbers that look like phone numbers, and facility names that look like
addresses. This corpus makes those confusions the point rather than an accident.

## Important notes

- **No real personal data.** Surnames are drawn from an approximation of the public
  frequency distribution; addresses combine real public place names with
  **randomised** block/lot numbers; email addresses only ever use reserved domains
  (`example.com`, `example.co.jp`, `example.ne.jp`, `.test`, `.invalid`, …).
- **Identifiers with check digits are format-valid and value-invalid by
  construction.** Card-shaped numbers deliberately fail Luhn and My-Number-shaped
  numbers deliberately fail the official check-digit algorithm, so no usable number
  can be produced. The project's test suite asserts this over thousands of samples.
- This dataset **does not certify compliance** with any law or regulation. It is
  material for training and evaluating detectors, and makes no completeness claim.

## Splits

| split | documents | gold spans |
|---|---:|---:|
| train | 12000 | 107426 |
| validation | 1500 | 13496 |
| test | 2000 | 17899 |
| ood | 520 | 1964 |
| negatives | 2000 | 0 |

`negatives` contains **zero gold spans**. Anything a detector finds there is by
definition a false positive, which is what makes the false-positive rate measurable.

`ood` is the **template-independent** evaluation split. `train` / `validation` /
`test` are generated from business-document templates (email, meeting minutes,
application forms, support tickets), so measuring only on `test` would reward a
model that merely memorised the template slots. `ood` inserts the same synthetic PII
directly into Wikipedia / statute / literary prose, with each carrier sentence
phrased so the label is genuinely valid. **Report both.**

## Gold spans by type (train + validation + test)

| type | Japanese | count |
|---|---|---:|
| NAME | 氏名 | 63778 |
| ADDRESS | 住所 | 11003 |
| PHONE | 電話番号 | 21979 |
| EMAIL | メールアドレス | 12925 |
| DOB | 生年月日 | 6881 |
| BANK_ACCOUNT | 金融口座 | 4955 |
| CREDIT_CARD | カード番号 | 2029 |
| MYNUMBER | マイナンバー様式 | 1301 |
| MEMBER_ID | 会員番号 | 7078 |
| POSTAL_CODE | 郵便番号 | 6892 |

## Hard-negative kinds

Deliberately confusable material, mixed into the positive documents and forming the
entire `negatives` split.

| kind | count |
|---|---:|
| address_like_facility | 2706 |
| common_noun_surname | 2735 |
| company_as_person | 2769 |
| date_like_nondob | 2798 |
| honorific_boundary | 2690 |
| number_like_id | 2798 |
| phone_like_id | 2741 |
| place_as_person | 2655 |

- `common_noun_surname` — surnames that are also ordinary nouns (森 / 林 / 泉 / 大和 / 青木)
- `place_as_person` — prefecture and city names that are also common surnames, used as places
- `company_as_person` — company names built from surname morphemes
- `honorific_boundary` — 様 / さん / 氏 / 殿 with and without a person, including
  お客様, 皆様, 仕様, 同様, 様式 where 様 is not a person at all
- `phone_like_id` — part numbers, order numbers, ISBNs and dates shaped like phone numbers
- `address_like_facility` — civic buildings and stations that read like addresses
- `number_like_id` — bill numbers, statute numbers, quantities that look like account numbers
- `date_like_nondob` — contract, issue and meeting dates that are not birth dates

## Base text licences

Synthetic PII is inserted into openly-licensed Japanese prose. Each row records its
source and licence in `source_license` / `source_ref`.

| source | licence | url | note |
|---|---|---|---|
| wikipedia_ja | CC BY-SA 4.0 | https://ja.wikipedia.org/ |  |
| egov_law | Public Domain (Japanese Copyright Act, Article 13) | https://laws.e-gov.go.jp/ |  |
| aozora | Public Domain (Aozora Bunko, copyright expired) | https://www.aozora.gr.jp/ |  |

The synthetic parts (templates, PII values, hard negatives) are CC0-1.0. Rows
containing Wikipedia-derived prose inherit CC BY-SA 4.0, which is why the dataset as
a whole is published under CC BY-SA 4.0.

## Fields

- `doc_id` (string), `text` (string)
- `spans`: JSON-encoded list of `{start, end, label, text, score, source, meta}`.
  `start` / `end` are **Python character indices into the NFKC-normalised text**,
  half-open `[start, end)` — not byte offsets.
- `subset`, `genre`, `source_license`, `source_ref`, `negative_kinds`, `meta`

## Loading

```python
from datasets import load_dataset
import json

ds = load_dataset("NagaYu/sumi-ja-pii-corpus")
row = ds["test"][0]
spans = json.loads(row["spans"])
for s in spans:
    assert row["text"][s["start"]:s["end"]] == s["text"]
```

## Reproduce

```bash
python3 scripts/build_dataset.py --train 12000 \
  --val 1500 --test 2000 \
  --neg 2000 --seed 0
```
