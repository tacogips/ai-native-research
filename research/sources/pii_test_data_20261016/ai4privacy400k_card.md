
---
license: other
license_name: license.md
language:
- en
- fr
- de
- it
- es
- nl
task_categories:
- text-classification
- token-classification
- table-question-answering
- question-answering
- zero-shot-classification
- summarization
- feature-extraction
- text-generation
- translation
- fill-mask
- tabular-classification
- tabular-to-text
- table-to-text
- text-retrieval
- other
multilinguality:
- multilingual
tags:
- legal
- business
- psychology
- privacy
- gdpr
- euaiact
- aiact
- pii
- sensitive
size_categories:
- 100K<n<1M
pretty_name: Ai4Privacy PII 300k Dataset
source_datasets:
- original
configs:
- config_name: default
  data_files:
  - split: train
    path: "data/train/*.jsonl"
  - split: validation
    path: "data/validation/*.jsonl"
---

> 👉 **Looking for the newest release?** The current flagship is [ai4privacy/pii-masking-openpii-1.5m](https://huggingface.co/datasets/ai4privacy/pii-masking-openpii-1.5m). 1.6M samples, 30 languages, 19 PII classes, Asia Pacific extension.?** The current flagship is [ai4privacy/pii-masking-openpii-1m](https://huggingface.co/datasets/ai4privacy/pii-masking-openpii-1m). 1.4M samples, 23 languages, 19 PII classes.

# Purpose and Features

🌍 World's largest open dataset for privacy masking 🌎

The dataset is useful to train and evaluate models to remove personally identifiable and sensitive information from text, especially in the context of AI assistants and LLMs. 


# AI4Privacy Dataset Analytics 📊

## Dataset Overview
- **Total entries:** 406,896
- **Total tokens:** 20,564,179
- **Total PII tokens:** 2,357,029
- **Number of PII classes in public dataset:** 17
- **Number of PII classes in extended dataset:** 63

## Language Distribution 🌍
- English (en): 85,321
- Italian (it): 81,007
- French (fr): 80,249
- German (de): 79,880
- Dutch (nl): 38,916
- Spanish (es): 41,523

## Locale Distribution 🌎
- United Kingdom (GB) 🇬🇧: 41,853
- United States (US) 🇺🇸: 43,468
- Italy (IT) 🇮🇹: 40,629
- France (FR) 🇫🇷: 40,026
- Switzerland (CH) 🇨🇭: 119,440
- Netherlands (NL) 🇳🇱: 38,916
- Germany (DE) 🇩🇪: 41,041
- Spain (ES) 🇪🇸: 41,523

## Dataset Split
- Train: 325,517 (80.00%)
- Validation: 81,379 (20.00%)

## Key Facts 🔑
- This is synthetic data! Generated using proprietary algorithms - no privacy violations! 🛡️
- 6 languages in total with strong localisation in 8 jurisdictions.
- The extended dataset includes a total of 63 PII classes, providing even more comprehensive coverage of sensitive information.
- Synthetic data generated using proprietary algorithms
  - No privacy violations!

For more information about the extended dataset or to discuss partnership opportunities, please contact us at partnerships@ai4privacy.com 📧

# Getting started

Option 1: Python
```terminal
  pip install datasets
```
```python
from datasets import load_dataset
dataset = load_dataset("ai4privacy/pii-masking-400k")
```

# Text entry lengths and PII distributions
This is the 4th iteration of the pii-masking series datasets and we have further improved it by improving the average text entry length.
The current distribution of sensitive data and PII tokens:
![PII Type Distribution](pii_type_distribution_pii_400k.png)

# Compatible Machine Learning Tasks:
- Tokenclassification. Check out a HuggingFace's [guide on token classification](https://huggingface.co/docs/transformers/tasks/token_classification).
  - [ALBERT](https://huggingface.co/docs/transformers/model_doc/albert), [BERT](https://huggingface.co/docs/transformers/model_doc/bert), [BigBird](https://huggingface.co/docs/transformers/model_doc/big_bird), [BioGpt](https://huggingface.co/docs/transformers/model_doc/biogpt), [BLOOM](https://huggingface.co/docs/transformers/model_doc/bloom), [BROS](https://huggingface.co/docs/transformers/model_doc/bros), [CamemBERT](https://huggingface.co/docs/transformers/model_doc/camembert), [CANINE](https://huggingface.co/docs/transformers/model_doc/canine), [ConvBERT](https://huggingface.co/docs/transformers/model_doc/convbert), [Data2VecText](https://huggingface.co/docs/transformers/model_doc/data2vec-text), [DeBERTa](https://huggingface.co/docs/transformers/model_doc/deberta), [DeBERTa-v2](https://huggingface.co/docs/transformers/model_doc/deberta-v2), [DistilBERT](https://huggingface.co/docs/transformers/model_doc/distilbert), [ELECTRA](https://huggingface.co/docs/transformers/model_doc/electra), [ERNIE](https://huggingface.co/docs/transformers/model_doc/ernie), [ErnieM](https://huggingface.co/docs/transformers/model_doc/ernie_m), [ESM](https://huggingface.co/docs/transformers/model_doc/esm), [Falcon](https://huggingface.co/docs/transformers/model_doc/falcon), [FlauBERT](https://huggingface.co/docs/transformers/model_doc/flaubert), [FNet](https://huggingface.co/docs/transformers/model_doc/fnet), [Funnel Transformer](https://huggingface.co/docs/transformers/model_doc/funnel), [GPT-Sw3](https://huggingface.co/docs/transformers/model_doc/gpt-sw3), [OpenAI GPT-2](https://huggingface.co/docs/transformers/model_doc/gpt2), [GPTBigCode](https://huggingface.co/docs/transformers/model_doc/gpt_bigcode), [GPT Neo](https://huggingface.co/docs/transformers/model_doc/gpt_neo), [GPT NeoX](https://huggingface.co/docs/transformers/model_doc/gpt_neox), [I-BERT](https://huggingface.co/docs/transformers/model_doc/ibert), [LayoutLM](https://huggingface.co/docs/transformers/model_doc/layoutlm), [LayoutLMv2](https://huggingface.co/docs/transformers/model_doc/layoutlmv2), [LayoutLMv3](https://huggingface.co/docs/transformers/model_doc/layoutlmv3), [LiLT](https://huggingface.co/docs/transformers/model_doc/lilt), [Longformer](https://huggingface.co/docs/transformers/model_doc/longformer), [LUKE](https://huggingface.co/docs/transformers/model_doc/luke), [MarkupLM](https://huggingface.co/docs/transformers/model_doc/markuplm), [MEGA](https://huggingface.co/docs/transformers/model_doc/mega), [Megatron-BERT](https://huggingface.co/docs/transformers/model_doc/megatron-bert), [MobileBERT](https://huggingface.co/docs/transformers/model_doc/mobilebert), [MPNet](https://huggingface.co/docs/transformers/model_doc/mpnet), [MPT](https://huggingface.co/docs/transformers/model_doc/mpt), [MRA](https://huggingface.co/docs/transformers/model_doc/mra), [Nezha](https://huggingface.co/docs/transformers/model_doc/nezha), [Nyströmformer](https://huggingface.co/docs/transformers/model_doc/nystromformer), [QDQBert](https://huggingface.co/docs/transformers/model_doc/qdqbert), [RemBERT](https://huggingface.co/docs/transformers/model_doc/rembert), [RoBERTa](https://huggingface.co/docs/transformers/model_doc/roberta), [RoBERTa-PreLayerNorm](https://huggingface.co/docs/transformers/model_doc/roberta-prelayernorm), [RoCBert](https://huggingface.co/docs/transformers/model_doc/roc_bert), [RoFormer](https://huggingface.co/docs/transformers/model_doc/roformer), [SqueezeBERT](https://huggingface.co/docs/transformers/model_doc/squeezebert), [XLM](https://huggingface.co/docs/transformers/model_doc/xlm), [XLM-RoBERTa](https://huggingface.co/docs/transformers/model_doc/xlm-roberta), [XLM-RoBERTa-XL](https://huggingface.co/docs/transformers/model_doc/xlm-roberta-xl), [XLNet](https://huggingface.co/docs/transformers/model_doc/xlnet), [X-MOD](https://huggingface.co/docs/transformers/model_doc/xmod), [YOSO](https://huggingface.co/docs/transformers/model_doc/yoso)
- Text Generation: Mapping the unmasked_text to to the masked_text or privacy_mask attributes. Check out HuggingFace's [guide to fine-tunning](https://huggingface.co/docs/transformers/v4.15.0/training)
  - [T5 Family](https://huggingface.co/docs/transformers/model_doc/t5), [Llama2](https://huggingface.co/docs/transformers/main/model_doc/llama2)

# Information regarding the rows:
- Each row represents a json object with a natural language text that includes placeholders for PII.
- Sample row:
  - "source_text" shows a natural text containing PII
    - "Subject: Group Messaging for Admissions Process\n\nGood morning, everyone,\n\nI hope this message finds you well. As we continue our admissions processes, I would like to update you on the latest developments and key information. Please find below the timeline for our upcoming meetings:\n\n- wynqvrh053 - Meeting at 10:20am\n- luka.burg - Meeting at 21\n- qahil.wittauer - Meeting at quarter past 13\n- gholamhossein.ruschke - Meeting at 9:47 PM\n- pdmjrsyoz1460 "
  - "target_text" contains a masked version of the source text
    - "Subject: Group Messaging for Admissions Process\n\nGood morning, everyone,\n\nI hope this message finds you well. As we continue our admissions processes, I would like to update you on the latest developments and key information. Please find below the timeline for our upcoming meetings:\n\n- [USERNAME] - Meeting at [TIME]\n- [USERNAME] - Meeting at [TIME]\n- [USERNAME] - Meeting at [TIME]\n- [USERNAME] - Meeting at [TIME]\n- [USERNAME] "
  - "privacy_mask" contains the information explicit format for privacy mask labels
    - [{"value": "wynqvrh053", "start": 287, "end": 297, "label": "USERNAME"}, {"value": "10:20am", "start": 311, "end": 318, "label": "TIME"}, {"value": "luka.burg", "start": 321, "end": 330, "label": "USERNAME"}, {"value": "21", "start": 344, "end": 346, "label": "TIME"}, {"value": "qahil.wittauer", "start": 349, "end": 363, "label": "USERNAME"}, {"value": "quarter past 13", "start": 377, "end": 392, "label": "TIME"}, {"value": "gholamhossein.ruschke", "start": 395, "end": 416, "label": "USERNAME"}, {"value": "9:47 PM", "start": 430, "end": 437, "label": "TIME"}, {"value": "pdmjrsyoz1460", "start": 440, "end": 453, "label": "USERNAME"}], 
  - "span_labels" displays the exact mapping spans of the private information within the text
    - [[440, 453, "USERNAME"], [430, 437, "TIME"], [395, 416, "USERNAME"], [377, 392, "TIME"], [349, 363, "USERNAME"], [344, 346, "TIME"], [321, 330, "USERNAME"], [311, 318, "TIME"], [287, 297, "USERNAME"]], 
  - "mberttokens" indicates the breakdown of the text into tokens associated with multi-lingual bert
    - ["Sub", "##ject", ":", "Group", "Mess", "##aging", "for", "Ad", "##mission", "##s", "Process", "Good", "morning", ",", "everyone", ",", "I", "hope", "this", "message", "finds", "you", "well", ".", "As", "we", "continue", "our", "admission", "##s", "processes", ",", "I", "would", "like", "to", "update", "you", "on", "the", "latest", "developments", "and", "key", "information", ".", "Please", "find", "below", "the", "time", "##line", "for", "our", "upcoming", "meetings", ":", "-", "w", "##yn", "##q", "##vr", "##h", "##0", "##53", "-", "Meeting", "at", "10", ":", "20", "##am", "-", "luka", ".", "bu", "##rg", "-", "Meeting", "at", "21", "-", "q", "##ahi", "##l", ".", "wit", "##tau", "##er", "-", "Meeting", "at", "quarter", "past", "13", "-", "gh", "##ola", "##mh", "##osse", "##in", ".", "rus", "##ch", "##ke", "-", "Meeting", "at", "9", ":", "47", "PM", "-", "p", "##d", "##m", "##jr", "##sy", "##oz", "##14", "##60"]
  - mbert_bio_labels demonstrates the labels associated with the BIO labelling task in Machine Learning using the mbert tokens.
    - ["O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O", "B-USERNAME", "I-USERNAME", "I-USERNAME", "O", "O", "O", "O", "O", "O", "O", "B-TIME", "I-TIME", "I-TIME", "O", "B-USERNAME", "I-USERNAME", "O", "O", "O", "B-TIME", "I-TIME", "I-USERNAME", "I-USERNAME", "I-USERNAME", "I-USERNAME", "I-USERNAME", "I-USERNAME", "I-USERNAME", "O", "O", "O", "O", "B-TIME", "I-TIME", "I-TIME", "I-TIME", "I-TIME", "I-TIME", "I-TIME", "I-TIME", "I-TIME", "I-TIME", "O", "B-USERNAME", "I-USERNAME"],"
  - "id": indicates the ID of the entry for future reference and feedback
    - "40767A"
  - "language": content of the language
    - "en"
   - "locale": content of the locale associated with the data
  -  "split": type of the machine learning set
    - "train" or "validation"
  
*note for the nested objects, we store them as string to maximise compability between various software.

# About Us:

At Ai4Privacy, we are commited to building the global seatbelt of the 21st century for Artificial Intelligence to help fight against potential risks of personal information being integrated into data pipelines.

Newsletter & updates: [www.Ai4Privacy.com](www.Ai4Privacy.com)
- Looking for ML engineers, developers, beta-testers, human in the loop validators (all languages)
- Integrations with already existing open solutions
- Ask us a question on discord: [https://discord.gg/kxSbJrUQZF](https://discord.gg/kxSbJrUQZF)

# Roadmap and Future Development

- Carbon neutral
- Additional benchmarking methods for NER
- Better multilingual and especially localisation
- Continuously increase the training and testing sets

# Known Issues

- Weird usage of the PII which will be resolved with the next release

# Use Cases and Applications

**Chatbots**: Incorporating a PII masking model into chatbot systems can ensure the privacy and security of user conversations by automatically redacting sensitive information such as names, addresses, phone numbers, and email addresses.

**Customer Support Systems**: When interacting with customers through support tickets or live chats, masking PII can help protect sensitive customer data, enabling support agents to handle inquiries without the risk of exposing personal information.

**Email Filtering**: Email providers can utilize a PII masking model to automatically detect and redact PII from incoming and outgoing emails, reducing the chances of accidental disclosure of sensitive information.

**Data Anonymization**: Organizations dealing with large datasets containing PII, such as medical or financial records, can leverage a PII masking model to anonymize the data before sharing it for research, analysis, or collaboration purposes.

**Social Media Platforms**: Integrating PII masking capabilities into social media platforms can help users protect their personal information from unauthorized access, ensuring a safer online environment.

**Content Moderation**: PII masking can assist content moderation systems in automatically detecting and blurring or redacting sensitive information in user-generated content, preventing the accidental sharing of personal details.

**Online Forms**: Web applications that collect user data through online forms, such as registration forms or surveys, can employ a PII masking model to anonymize or mask the collected information in real-time, enhancing privacy and data protection.

**Collaborative Document Editing**: Collaboration platforms and document editing tools can use a PII masking model to automatically mask or redact sensitive information when multiple users are working on shared documents.

**Research and Data Sharing**: Researchers and institutions can leverage a PII masking model to ensure privacy and confidentiality when sharing datasets for collaboration, analysis, or publication purposes, reducing the risk of data breaches or identity theft.

**Content Generation**: Content generation systems, such as article generators or language models, can benefit from PII masking to automatically mask or generate fictional PII when creating sample texts or examples, safeguarding the privacy of individuals.

(...and whatever else your creative mind can think of)

# Licensing

Academic use is encouraged with proper citation provided it follows similar license terms*. Commercial entities should contact us at licensing@ai4privacy.com for licensing inquiries and additional data access.*

* Terms apply. See [LICENSE.md](LICENSE.md) for full details.

# Support and Maintenance

AI4Privacy is a project affiliated with [Ai Suisse SA](https://www.aisuisse.com/).


## p5y Data Analytics

This dataset is built on the [p5y](https://p5y.org) framework - think of it as i18n but for privacy. Just as i18n (internationalization) translates content into different locales, p5y translates sensitive data into privacy-safe formats through a standardized 3-step approach:

1. **Awareness** - Scan and markup private entities in unstructured text, producing a structured privacy mask with entity types, distribution, density, and risk assessment.
2. **Protection** - Control identified personal data through masking, pseudonymization, or k-anonymization, tailored to the specific use case and regulatory requirements.
3. **Quality Assurance** - Measure remaining privacy risk after anonymization, evaluating de-anonymization risks through expert annotation and automated assessment.

Learn more at [p5y.org](https://p5y.org)
