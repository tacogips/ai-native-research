---
language:
- ja
- en
license: mit
pipeline_tag: fill-mask
library_name: transformers
---

# ModernBERT-Ja-310M

This repository provides Japanese ModernBERT trained by [SB Intuitions](https://www.sbintuitions.co.jp/).

[ModernBERT](https://arxiv.org/abs/2412.13663) is a new variant of the BERT model that combines local and global attention, allowing it to handle long sequences while maintaining high computational efficiency.
It also incorporates modern architectural improvements, such as [RoPE](https://arxiv.org/abs/2104.09864).

Our ModernBERT-Ja-310M is trained on a high-quality corpus of Japanese and English text comprising **4.09T tokens**, featuring a vocabulary size of 102,400 and a sequence length of **8,192** tokens.


## How to Use


You can use our models directly with the transformers library v4.48.0 or higher:

```bash
pip install -U "transformers>=4.48.0"
```

Additionally, if your GPUs support Flash Attention 2, we recommend using our models with Flash Attention 2.

```
pip install flash-attn --no-build-isolation
```

### Example Usage

```python
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer, pipeline

model = AutoModelForMaskedLM.from_pretrained("sbintuitions/modernbert-ja-310m", torch_dtype=torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained("sbintuitions/modernbert-ja-310m")
fill_mask = pipeline("fill-mask", model=model, tokenizer=tokenizer)

results = fill_mask("おはようございます、今日の天気は<mask>です。")

for result in results:
    print(result)
# {'score': 0.54296875, 'token': 16416, 'token_str': '晴れ', 'sequence': 'おはようございます、今日の天気は晴れです。'}
# {'score': 0.17578125, 'token': 28933, 'token_str': '曇り', 'sequence': 'おはようございます、今日の天気は曇りです。'}
# {'score': 0.13671875, 'token': 92339, 'token_str': 'くもり', 'sequence': 'おはようございます、今日の天気はくもりです。'}
# {'score': 0.06494140625, 'token': 2988, 'token_str': '雨', 'sequence': 'おはようございます、今日の天気は雨です。'}
# {'score': 0.019775390625, 'token': 10547, 'token_str': '晴', 'sequence': 'おはようございます、今日の天気は晴です。'}
```

## Model Series

We provide ModernBERT-Ja in several model sizes. Below is a summary of each model.

|ID| #Param. | #Param.<br>w/o Emb.|Dim.|Inter. Dim.|#Layers|
|-|-|-|-|-|-|
|[sbintuitions/modernbert-ja-30m](https://huggingface.co/sbintuitions/modernbert-ja-30m)|37M|10M|256|1024|10|
|[sbintuitions/modernbert-ja-70m](https://huggingface.co/sbintuitions/modernbert-ja-70m)|70M|31M|384|1536|13|
|[sbintuitions/modernbert-ja-130m](https://huggingface.co/sbintuitions/modernbert-ja-130m)|132M|80M|512|2048|19|
|**[sbintuitions/modernbert-ja-310m](https://huggingface.co/sbintuitions/modernbert-ja-310m)**|315M|236M|768|3072|25|

For all models,
the vocabulary size is 102,400,
the head dimension is 64,
and the activation function is GELU.  
The configuration for global attention and sliding window attention consists of 1 layer + 2 layers (global–local–local).  
The sliding window attention window context size is 128, with global_rope_theta set to 160,000 and local_rope_theta set to 10,000.


## Model Description

We constructed the ModernBERT-Ja-310M model through a three-stage training process, which follows the original [ModernBERT](https://huggingface.co/answerdotai/ModernBERT-base).

First, we performed pre-training using a large corpus.
Next, we conducted two phases of context length extension.

1. **Pre-training**
  - Training with **3.51T tokens**, including Japanese and English data extracted from web corpora.
  - The sequence length is 1,024 with [best-fit packing](https://arxiv.org/abs/2404.10830).
  - Masking rate is **30%** (with 80-10-10 rule).
2. **Context Extension (CE): Phase 1**
  - Training with **430B tokens**, comprising high-quality Japanese and English data.
  - The sequence length is **8,192** with [best-fit packing](https://arxiv.org/abs/2404.10830).
  - Masking rate is **30%** (with 80-10-10 rule).
3. **Context Extension (CE): Phase 2**
  - Training with **150B tokens**, comprising high-quality Japanese data.
  - The sequence length is **8,192** without sequence packing.
  - Masking rate is **15%** (with 80-10-10 rule).
   
The key differences from the original ModernBERT are:
1. It is pre-trained on Japanese and English corpora, leading to a total of approximately 4.09T training tokens.
2. We observed that decreasing the mask rate in Context Extension Phase 2 from 30% to 15% improved the model's performance.

### Tokenization and Vocabulary

We use the tokenizer and vocabulary from [sbintuitions/sarashina2-13b](https://huggingface.co/collections/sbintuitions/sarashina-6680c6d6ab37b94428ca83fb).  
Specifically, we employ a [SentencePiece](https://github.com/google/sentencepiece) tokenizer with a unigram language model and byte fallback.  

We do not apply pre-tokenization using a Japanese tokenizer.  
Therefore, users can directly input raw sentences into the tokenizer without any additional preprocessing.  

### Intended Uses and Limitations

You can use this model for masked language modeling, but it's mostly intended to be fine-tuned on a downstream task.
Note that this model is not designed for text generation.
When you want to generate a text, please use a text generation model such as [Sarashina](https://huggingface.co/collections/sbintuitions/sarashina-6680c6d6ab37b94428ca83fb).

Since the unigram language model is used as a tokenizer, the token boundaries often do not align with the morpheme boundaries, resulting in poor performance in token classification tasks such as named entity recognition and span extraction.


## Evaluation

We evaluated our model on 12 datasets, including JGLUE, across various tasks:
- Knowledge-based tasks: [JCommonsenseQA (JComQA)](https://github.com/yahoojapan/JGLUE), [RCQA](https://www.cl.ecei.tohoku.ac.jp/rcqa/)
- Japanese linguistic acceptability classification: [JCoLA](https://github.com/osekilab/JCoLA)
- Natural Language Inference (NLI) tasks: [JNLI](https://github.com/yahoojapan/JGLUE), [JSICK](https://github.com/verypluming/JSICK), [JSNLI](https://nlp.ist.i.kyoto-u.ac.jp/?%E6%97%A5%E6%9C%AC%E8%AA%9ESNLI%28JSNLI%29%E3%83%87%E3%83%BC%E3%82%BF%E3%82%BB%E3%83%83%E3%83%88), [Kyoto University RTE (KU RTE)](https://nlp.ist.i.kyoto-u.ac.jp/index.php?Textual+Entailment+%E8%A9%95%E4%BE%A1%E3%83%87%E3%83%BC%E3%82%BF)
- Semantic Textual Similarity (STS) task: [JSTS](https://github.com/yahoojapan/JGLUE)
- Various classification tasks: [Livedoor news corpus (Livedoor)](https://www.rondhuit.com/download.html), [LLM-jp Toxicity (Toxicity)](https://llm-jp.nii.ac.jp/llm/2024/08/07/llm-jp-toxicity-dataset.html), [MARC-ja](https://github.com/yahoojapan/JGLUE), [WRIME v2 (WRIME)](https://github.com/ids-cv/wrime)

These tasks are short-sequence evaluation tasks, and we aligned our settings with those of existing models.  
While the maximum sequence length varies across tasks, it does not exceed 512.  
We set the sequence length and other experimental configurations per task, ensuring that the settings remain consistent across models.

For hyperparameters, we explored the following ranges:  
- Learning rate: `{5e-6, 1e-5, 2e-5, 3e-5, 5e-5, 1e-4}`
- Number of epochs:  
  - Tasks with a large number of instances: `{1, 2}`  
  - Tasks with fewer instances: `{3, 5, 10}`

In the experiments, we loaded several Japanese models that are publicly available on HuggingFace using `AutoModel` and constructed classification models by appending a classification head consisting of a linear layer, a GELU activation function, and another linear layer.
This was done because HuggingFace's `AutoModelForSequenceClassification` comes with different implementations for each model, and using them directly would result in classification heads that differ from one model to another.

For the embeddings fed into the classification layer, we used the embedding of the special token at the beginning of the sentence.
That is, `[CLS]` in BERT and `<s>` in RoBERTa. 
Note that our model does not perform the next sentence prediction (NSP) task during pretraining, so `<s>` is added at the beginning of the sentence, not `<cls>`.
Therefore, we used the `<s>` token for classification.

We conducted evaluations using 5-fold cross-validation.
That is, we trained the model on the `train` set and evaluated it on the `validation` set.
After determining the optimal hyperparameters (learning rate, epochs) based on the average performance on the `validation` sets, we report the average performance on the `test` sets with the hyperparameters.

For datasets without predefined splits, we first set aside 10% of the data as the test set and then performed 5-fold cross-validation on the remaining data.
For datasets such as some tasks in **JGLUE**, where only `train` and `validation` sets are publicly available,
we treated the `validation` set as the `test` set and performed 5-fold cross-validation on the remaining data.  
For datasets with predefined `train`, `validation`, and `test` sets, we simply trained and evaluated the model five times with different random seeds and used the model with the best average evaluation score on the `validation` set to measure the final score on the `test` set.  


### Evaluation Results

| Model | #Param. | #Param.<br>w/o Emb. | **Avg.** | [JComQA](https://github.com/yahoojapan/JGLUE)<br>(Acc.) | [RCQA](https://www.cl.ecei.tohoku.ac.jp/rcqa/)<br>(Acc.) | [JCoLA](https://github.com/osekilab/JCoLA)<br>(Acc.) | [JNLI](https://github.com/yahoojapan/JGLUE)<br>(Acc.) | [JSICK](https://github.com/verypluming/JSICK)<br>(Acc.) | [JSNLI](https://nlp.ist.i.kyoto-u.ac.jp/?%E6%97%A5%E6%9C%AC%E8%AA%9ESNLI%28JSNLI%29%E3%83%87%E3%83%BC%E3%82%BF%E3%82%BB%E3%83%83%E3%83%88)<br>(Acc.) | [KU RTE](https://nlp.ist.i.kyoto-u.ac.jp/index.php?Textual+Entailment+%E8%A9%95%E4%BE%A1%E3%83%87%E3%83%BC%E3%82%BF)<br>(Acc.) | [JSTS](https://github.com/yahoojapan/JGLUE)<br>(Spearman's ρ) | [Livedoor](https://www.rondhuit.com/download.html)<br>(Acc.) | [Toxicity](https://llm-jp.nii.ac.jp/llm/2024/08/07/llm-jp-toxicity-dataset.html)<br>(Acc.) | [MARC-ja](https://github.com/yahoojapan/JGLUE)<br>(Acc.) | [WRIME](https://github.com/ids-cv/wrime)<br>(Acc.) |
| ------ | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| [ModernBERT-Ja-30M](https://huggingface.co/sbintuitions/modernbert-ja-30m) | 37M | 10M | 85.67 | 80.95 | 82.35 | 78.85 | 88.69 | 84.39 | 91.79 | 61.13 | 85.94 | 97.20 | 89.33 | 95.87 | 91.61 | 
| [ModernBERT-Ja-70M](https://huggingface.co/sbintuitions/modernbert-ja-70m) | 70M | 31M | 86.77 | 85.65 | 83.51 | 80.26 | 90.33 | 85.01 | 92.73 | 60.08 | 87.59 | 96.34 | 91.01 | 96.13 | 92.59 | 
| [ModernBERT-Ja-130M](https://huggingface.co/sbintuitions/modernbert-ja-130m) | 132M | 80M | 88.95 | 91.01 | 85.28 | 84.18 | 92.03 | 86.61 | 94.01 | 65.56 | 89.20 | 97.42 | 91.57 | 96.48 | 93.99 |
| [**ModernBERT-Ja-310M**](https://huggingface.co/sbintuitions/modernbert-ja-310m)<br>(this model) | 315M | 236M | <u>**89.83**</u> | 93.53 | 86.18 | 84.81 | 92.93 | 86.87 | 94.48 | 68.79 | 90.53 | 96.99 | 91.24 | 96.39 | 95.23 |
|  | | |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [LINE DistillBERT](https://huggingface.co/line-corporation/line-distilbert-base-japanese)| 68M | 43M | 85.32 | 76.39 | 82.17 | 81.04 | 87.49 | 83.66 | 91.42 | 60.24 | 84.57 | 97.26 | 91.46 | 95.91 | 92.16
| [Tohoku BERT-base v3](https://huggingface.co/tohoku-nlp/bert-base-japanese-v3)| 111M | 86M | 86.74 | 82.82 | 83.65 | 81.50 | 89.68 | 84.96 | 92.32 | 60.56 | 87.31 | 96.91 | 93.15 | 96.13 | 91.91 |
| [LUKE-japanese-base-lite](https://huggingface.co/studio-ousia/luke-japanese-base-lite)| 133M | 107M | 87.15 | 82.95 | 83.53 | 82.39 | 90.36 | 85.26 | 92.78 | 60.89 | 86.68 | 97.12 | 93.48 | 96.30 | 94.05 |
| [Kyoto DeBERTa-v3](https://huggingface.co/ku-nlp/deberta-v3-base-japanese)| 160M | 86M | 88.31 | 87.44 | 84.90 | 84.35 | 91.91 | 86.22 | 93.41 | 63.31 | 88.51 | 97.10 | 92.58 | 96.32 | 93.64 |
|  | | |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [KoichiYasuoka/modernbert-base-japanese-wikipedia](https://huggingface.co/KoichiYasuoka/modernbert-base-japanese-wikipedia)| 160M | 110M | 82.41 | 62.59 | 81.19 | 76.80 | 84.11 | 82.01 | 90.51 | 60.48 | 81.74 | 97.10 | 90.34 | 94.85 | 87.25 |
| [llm-jp/llm-jp-modernbert-base](https://huggingface.co/llm-jp/llm-jp-modernbert-base)| 187M | 110M | 86.75 | 84.29 | 83.99 | 78.00 | 90.28 | 83.76 | 93.40 | 60.32 | 87.71 | 96.64 | 92.13 | 96.33 | 94.09 |
|  | | |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [Tohoku BERT-large char v2](https://huggingface.co/cl-tohoku/bert-large-japanese-char-v2)| 311M | 303M | 87.23 | 85.08 | 84.20 | 81.79 | 90.55 | 85.25 | 92.63 | 61.29 | 87.64 | 96.55 | 93.26 | 96.25 | 92.29 |
| [Tohoku BERT-large v2](https://huggingface.co/tohoku-nlp/bert-large-japanese-v2)| 337M | 303M | 88.36 | 86.93 | 84.81 | 82.89 | 92.05 | 85.33 | 93.32 | 64.60 | 89.11 | 97.64 | 94.38 | 96.46 | 92.77 |
| [Waseda RoBERTa-large (Seq. 512)](https://huggingface.co/nlp-waseda/roberta-large-japanese-seq512-with-auto-jumanpp)| 337M | 303M | 88.37 | 88.81 | 84.50 | 82.34 | 91.37 | 85.49 | 93.97 | 61.53 | 88.95 | 96.99 | 95.06 | 96.38 | 95.09 |
| [Waseda RoBERTa-large (Seq. 128)](https://huggingface.co/nlp-waseda/roberta-large-japanese-with-auto-jumanpp)| 337M | 303M | 88.36 | 89.35 | 83.63 | 84.26 | 91.53 | 85.30 | 94.05 | 62.82 | 88.67 | 95.82 | 93.60 | 96.05 | 95.23 |
| [LUKE-japanese-large-lite](https://huggingface.co/studio-ousia/luke-japanese-large-lite)| 414M | 379M | 88.94 | 88.01 | 84.84 | 84.34 | 92.37 | 86.14 | 94.32 | 64.68 | 89.30 | 97.53 | 93.71 | 96.49 | 95.59 |
| [RetrievaBERT](https://huggingface.co/retrieva-jp/bert-1.3b)| 1.30B | 1.15B | 86.79 | 80.55 | 84.35 | 80.67 | 89.86 | 85.24 | 93.46 | 60.48 | 87.30 | 97.04 | 92.70 | 96.18 | 93.61 |
|  | | |  |  |  |  |  |  |  |  |  |  |  |  |  |
| [hotchpotch/mMiniLMv2-L6-H384](https://huggingface.co/hotchpotch/mMiniLMv2-L6-H384)| 107M | 11M | 81.53 | 60.34 | 82.83 | 78.61 | 86.24 | 77.94 | 87.32 | 60.48 | 80.48 | 95.55 | 86.40 | 94.97 | 87.20 |
| [hotchpotch/mMiniLMv2-L12-H384](https://huggingface.co/hotchpotch/mMiniLMv2-L12-H384)| 118M | 21M | 82.59 | 62.70 | 83.77 | 78.61 | 87.69 | 79.58 | 87.65 | 60.48 | 81.55 | 95.88 | 90.00 | 94.89 | 88.28 |
| [mBERT](https://huggingface.co/google-bert/bert-base-multilingual-cased)| 178M | 86M | 83.48 | 66.08 | 82.76 | 77.32 | 88.15 | 84.20 | 91.25 | 60.56 | 84.18 | 97.01 | 89.21 | 95.05 | 85.99 |
| [XLM-RoBERTa-base](https://huggingface.co/FacebookAI/xlm-roberta-base)| 278M | 86M | 84.36 | 69.44 | 82.86 | 78.71 | 88.14 | 83.17 | 91.27 | 60.48 | 83.34 | 95.93 | 91.91 | 95.82 | 91.20 |
| [XLM-RoBERTa-large](https://huggingface.co/FacebookAI/xlm-roberta-large)| 560M | 303M | 86.95 | 80.07 | 84.47 | 80.42 | 92.16 | 84.74 | 93.87 | 60.48 | 88.03 | 97.01 | 93.37 | 96.03 | 92.72 |

The evaluation results are shown in the table.
`#Param.` represents the number of parameters in both the input embedding layer and the Transformer layers, while `#Param. w/o Emb.` indicates the number of parameters in the Transformer layers only.

According to our evaluation results, **our ModernBERT-Ja-310M archives state-of-the-art performance** across the evaluation tasks, even when compared with much larger models.  
Despite being a long-context model capable of processing sequences of up to 8,192 tokens, our ModernBERT-Ja-310M also exhibited strong performance in short-sequence evaluations.

## Ethical Considerations

ModernBERT-Ja-310M may produce representations that reflect biases.  
When you use this model for masked language modeling, it may generate biases or harmful expressions.

## License

[MIT License](https://huggingface.co/sbintuitions/modernbert-ja-310m/blob/main/LICENSE)

## Citation

```bibtex
@misc{
    modernbert-ja,
	author = {Tsukagoshi, Hayato and Li, Shengzhe and Fukuchi, Akihiko and Shibata, Tomohide},
	title = {{ModernBERT-Ja}},
	howpublished = {\url{https://huggingface.co/collections/sbintuitions/modernbert-ja-67b68fe891132877cf67aa0a}},
    url = {https://huggingface.co/collections/sbintuitions/modernbert-ja-67b68fe891132877cf67aa0a},
	year = {2025},
}
```