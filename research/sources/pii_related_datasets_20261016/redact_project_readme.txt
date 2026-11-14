<div align="center">

# REDACT

### A Systematically Controlled Multilingual Benchmark for Personal Information Detection

**Accepted to the EMNLP 2026 Industry Track**

[![EMNLP 2026](https://img.shields.io/badge/EMNLP%202026-Industry%20Track-4C78A8)](https://2026.emnlp.org/)
[![arXiv](https://img.shields.io/badge/arXiv-2606.19881-b31b1b.svg)](https://arxiv.org/abs/2606.19881)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Dataset-FFD21E?logo=huggingface&logoColor=000)](https://huggingface.co/datasets/guneeshv/REDACT-PII-Benchmark)
[![Code](https://img.shields.io/badge/Code-MIT-2ea44f)](LICENSE)
[![Dataset Terms](https://img.shields.io/badge/Data-REDACT%20Terms-d97706)](DATASET_TERMS.md)

**13,427 records · 324,078 entity annotations · 51 canonical entity types · 25 languages · 9 scripts · 4,127 surface-form patterns**

[Paper](https://arxiv.org/abs/2606.19881) · [Dataset](https://huggingface.co/datasets/guneeshv/REDACT-PII-Benchmark) · [Schema](data/schema.md) · [Evaluation](evaluation/README.md) · [Generation](generation/README.md)

</div>

---

## Why REDACT?

REDACT is a multilingual benchmark for evaluating **character-span detection and canonical PII type classification** under controlled variation. Rather than treating PII detection as a single aggregate score, REDACT is designed to expose where detectors succeed and fail across language, entity type, disclosure form, and policy-sensitivity slices.

| Controlled coverage | Multilingual breadth | Disclosure-aware analysis |
|---|---|---|
| 9 generation axes with strength-2 pairwise coverage | 25 languages across 9 scripts | Gold `disclosed`, `disclosure_form`, and `sensitivity_tier` metadata |
| 51 canonical entity types | 453-621 records per language | F5 recall by disclosure form and F6 recall by sensitivity tier |
| 4,127 surface-form patterns | Native-script and code-switched examples | Aggregate, per-type, and per-language F1 |

### At a glance

| Records | Entity annotations | Entity types | Languages | Scripts | Surface-form patterns |
|---:|---:|---:|---:|---:|---:|
| **13,427** | **324,078** | **51** | **25** | **9** | **4,127** |

---

## Benchmark results

All five systems were evaluated on the same locked, language-stratified **1,000-record split** with 40 records per language. Partial-overlap micro-F1 is the primary aggregate metric.

| Detector | Partial micro-F1 | Macro F1 | Exact micro-F1 |
|---|---:|---:|---:|
| Presidio | 0.195 | 0.063 | 0.145 |
| GLiNER-multi | 0.320 | 0.224 | 0.293 |
| OpenAI Privacy Filter | 0.512 | 0.254 | 0.171 |
| GPT-4.1 | 0.597 | 0.565 | 0.558 |
| **Claude Sonnet 4.6** | **0.636** | **0.619** | **0.602** |

REDACT also reports two gold-stratified diagnostic views:

- **F5:** recall by disclosure form
- **F6:** recall by sensitivity tier

These slices reveal detector-specific failure structure that aggregate F1 can hide. Precision and F1 remain the primary metrics for aggregate, per-entity-type, and per-language evaluation.

> [!NOTE]
> The obfuscated disclosure-form slice contains only **15 gold entities** in the locked evaluation split, so those recall values should be interpreted descriptively.

<details>
<summary><strong>Support counts in the locked 1,000-record evaluation split</strong></summary>

<br>

| Sensitivity tier | Complete | Partial | Obfuscated | Total |
|---|---:|---:|---:|---:|
| HIGH | 3,833 | 247 | 5 | 4,085 |
| MEDIUM | 14,909 | 110 | 7 | 15,026 |
| LOW | 5,078 | 7 | 3 | 5,088 |
| **Total** | **23,820** | **364** | **15** | **24,199** |

</details>

The canonical camera-ready detector report is [`reports/11_stratified_f1_v2.json`](reports/11_stratified_f1_v2.json).

---

## What is released?

| Resource | Description |
|---|---|
| [`data/pii_benchmark_full.json`](data/pii_benchmark_full.json) | Full 13,427-record benchmark corpus |
| [`data/pii_benchmark_sample1000.json`](data/pii_benchmark_sample1000.json) | Locked 1,000-record detector evaluation split |
| [`data/schema.md`](data/schema.md) | Record, entity, and metadata schema |
| [`catalog/PII_Pattern_Catalog_v4_MASTER.md`](catalog/PII_Pattern_Catalog_v4_MASTER.md) | 4,127-pattern surface-form catalog |
| [`evaluation/`](evaluation/) | Detector evaluation and scoring code |
| [`generation/`](generation/) | Generation prompts, samplers, and pipeline artifacts |
| [`reports/`](reports/) | Precomputed corpus and detector reports |

The 1,000-record subset is the official evaluation split used for the five reported detector systems. The remaining 12,427 records are also released as part of the benchmark corpus.

The large JSON files are stored with Git LFS. The [Hugging Face mirror](https://huggingface.co/datasets/guneeshv/REDACT-PII-Benchmark) is usually the easiest way to download the corpus.

---

## What does a REDACT annotation contain?

The headline task is **character-span detection plus classification into one of 51 canonical entity types**.

Each gold entity additionally carries:

| Field | Values | Meaning |
|---|---|---|
| `disclosed` | `true`, `false` | Whether the mention is an actual disclosure in context |
| `disclosure_form` | `complete`, `partial`, `obfuscated` | How completely the entity value is surfaced |
| `sensitivity_tier` | `HIGH`, `MEDIUM`, `LOW` | Operational benchmark label used for stratified analysis |

These metadata fields are **gold analysis attributes**. Systems are not required to predict them in the headline detector experiment.

Example entity annotation:

```json
{
  "entity_type": "Full_Name",
  "entity_string": "María García",
  "start": 19,
  "end": 31,
  "mention_index": 0,
  "disclosed": true,
  "disclosure_form": "complete",
  "sensitivity_tier": "MEDIUM"
}
```

Sensitivity tiers are operational benchmark labels for controlled analysis. They should not be interpreted as universal re-identification-risk rankings or legal advice.

---

## Construction pipeline

REDACT controls nine record-level axes: **domain, format, difficulty, length, density, code-switching, language, adjacency, and co-occurrence pattern**.

```mermaid
flowchart LR
    A["Sampling<br/>9 controlled axes"] --> B["Generation<br/>16 hard rules"]
    B --> C["Deterministic<br/>span alignment"]
    C --> D["Conditional<br/>verification"]
    D --> E["Repair and<br/>normalization"]
    E --> F["Near-duplicate<br/>filtering"]
    F --> G["Release<br/>audits"]
    G --> H["13,427<br/>records"]
```

A strength-2 covering array produces **5,510 configurations**, and paired-sweep mode contributes **890 additional configurations**, giving **6,400 planned configurations per run**.

<details>
<summary><strong>Release lineage</strong></summary>

<br>

```text
6,400 configurations/run x 3 planned runs
        = 19,200 planned generation slots
                    |
                    v
             14,285 loaded
                    |
        - 814 structurally invalid records
                    |
                    v
             13,471 records
                    |
        - 44 near duplicates
                    |
                    v
             13,427 released
```

</details>

Generation uses **16 hard rules**. The prompt artifact contains 10 core few-shot anchors plus one paired-sweep-specific example. Historical generation artifacts are preserved for provenance; publication-facing definitions in this README and [`data/schema.md`](data/schema.md) should be treated as the current benchmark documentation.

See [`generation/README.md`](generation/README.md) for the reproducibility overview.

---

## Quality assurance

The release combines deterministic checks, model-based assessment, and human validation.

| Check | Result |
|---|---:|
| Final offset alignment | **99.657%** |
| Canonical entity-type compliance after structural filtering | **100%** |
| Minimum records per canonical type | **50+** |
| Realized pairwise axis-value coverage | **98.2%** |
| Manual entity validation | **510 entities, 10 per type** |
| Entity-type agreement with gold | **99.1%** |
| Span agreement with gold | **99.1%** |
| `disclosed` agreement with gold | **99.7%** |
| Disclosure-form agreement with gold | **99.8%** |
| Inter-annotator raw agreement | **96.4%** |
| Sensitivity-tier agreement | **90.5%** |
| Missed-entity rate in separate 25-record audit | **< 3.3%** |

The G-Eval quality panel uses three model families: GPT-5.2, Claude Sonnet 4.6, and Gemini 2.5 Pro.

---

## Evaluation protocol

See [`evaluation/README.md`](evaluation/README.md) for the full scoring and reproducibility protocol.

Three span-matching modes are supported:

| Mode | Criterion |
|---|---|
| **Exact** | Coincident character-span boundaries |
| **Partial** | Any same-type span overlap, used as the primary metric |
| **Fuzzy** | At least 50% overlap of the shorter span |

Reported analyses include:

- aggregate micro-F1 and macro-F1
- per-entity-type F1
- per-language F1
- F5 recall by disclosure form
- F6 recall by sensitivity tier

---

## Quick start

### Clone with Git LFS

```bash
git lfs install
git clone https://github.com/guneeshvats/REDACT-PII-Benchmark.git
cd REDACT-PII-Benchmark
git lfs pull
```

Or download the corpus from [Hugging Face](https://huggingface.co/datasets/guneeshv/REDACT-PII-Benchmark) after accepting the dataset terms.

### Load the corpus

```python
import json

with open("data/pii_benchmark_full.json", encoding="utf-8") as f:
    records = json.load(f)

print(len(records))  # 13427

record = records[0]
print(record["axes"]["language"])
print(record["entities"][0])
```

---

## Languages

REDACT contains 25 language variants across 9 scripts:

`AR` · `CS` · `DA` · `DE` · `EN` · `ES` · `FI` · `FR` · `FR_CA` · `HE` · `HI` · `HU` · `IT` · `JA` · `KO` · `NL` · `NO` · `PT_BR` · `PT_EU` · `RU` · `SV` · `TH` · `TR` · `ZH_CN` · `ZH_TW`

Each language contributes **453-621 records** to the released corpus.

---

## Repository map

```text
.
├── README.md
├── LICENSE
├── DATASET_TERMS.md
├── data/
│   ├── pii_benchmark_full.json
│   ├── pii_benchmark_sample1000.json
│   └── schema.md
├── catalog/
│   ├── PII_Pattern_Catalog_v4_MASTER.md
│   ├── pattern_seed_data_v4.json
│   └── co_to_v4_mapping.json
├── generation/
│   ├── README.md
│   ├── prompts/
│   ├── samplers/
│   ├── seed/
│   └── sygra_graph/
├── evaluation/
│   ├── README.md
│   ├── scripts/
│   ├── judge/
│   └── manual_validation/
├── docs/
│   ├── methodology.md
│   ├── metrics_reference.md
│   ├── generation_guide.md
│   ├── runbook.md
│   └── PROVENANCE.md
└── reports/
    ├── README.md
    ├── 06_stats.json
    └── 11_stratified_f1_v2.json
```

---

## Licensing and intended use

The repository uses separate terms for code and data:

- **Code and general repository documentation:** MIT License, see [`LICENSE`](LICENSE).
- **Dataset artifacts and pattern catalog:** REDACT Dataset Terms, see [`DATASET_TERMS.md`](DATASET_TERMS.md).

The dataset is intended for research, evaluation, auditing, education, and defensive privacy work. The corpus contains synthetic identifiers rather than real personal data, but some formats are deliberately realistic because detector evaluation requires structural plausibility.

---

## Citation

If you use REDACT, please cite:

```bibtex
@inproceedings{vats2026redact,
  title     = {REDACT: A Systematically Controlled Multilingual Benchmark for Personal Information Detection},
  author    = {Guneesh Vats and Anubha Agrawal and Shikha Singhal and Ajita Dash and Praison Selvaraj and Vidhan Jhawar and Ranga Prasad Chenna and Bharadwaj Y M G},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing: Industry Track},
  year      = {2026},
  note      = {To appear}
}
```

Preprint: [arXiv:2606.19881](https://arxiv.org/abs/2606.19881)

---

## Authors

**Guneesh Vats · Anubha Agrawal · Shikha Singhal · Ajita Dash · Praison Selvaraj · Vidhan Jhawar · Ranga Prasad Chenna · Bharadwaj Y M G**

<div align="center">

If REDACT is useful in your work, please consider citing the paper and starring the repository.

</div>
