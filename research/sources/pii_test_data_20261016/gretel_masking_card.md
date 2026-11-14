---
license: apache-2.0
task_categories:
- text-classification
- text-generation
language:
- en
tags:
- datadesigner
- synthetic
- domain-specific
- text
- NER
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: validation
    path: data/validation-*
  - split: test
    path: data/test-*
---

<center>
<img src="pii_masking_en-v1.png" width=600>
</center>

# Gretel Synthetic Domain-Specific Documents Dataset (English)

This dataset is a synthetically generated collection of documents enriched with Personally Identifiable Information (PII) and Protected Health Information (PHI) entities spanning multiple domains. 
Created using Gretel Navigator with mistral-nemo-2407 as the backend model, it is specifically designed for fine-tuning Gliner models. 
The dataset contains document passages featuring PII/PHI entities from a wide range of domain and document types, making it an ideal resource for tasks such as Named Entity Recognition (NER), text classification, and domain-specific document analysis

## Key Features

This dataset is designed to provide a comprehensive resource for developing and fine-tuning models in tasks involving sensitive information across various domains.

- **Synthetic Data Generation**: This dataset is entirely synthetically generated using Gretel Navigator, ensuring a rich variety of realistic and diverse data samples that have undergone automated validation for quality and consistency.
- **Entity Extraction for PII/PHI**: Documents contain a wide range of PII and PHI entities, including names, dates, and unique identifiers, categorized by type. This provides a valuable foundation for training models on tasks like NER, PII detection, and sensitive data redaction.
- **Diverse Real-World Contexts**: The dataset covers multiple industries such as finance, healthcare, cybersecurity, and others, providing broad coverage across different document types and enhancing model generalization.
- **Document Descriptions**: Each document includes a description that outlines its structure and typical contents, aiding in document classification and understanding.

## Dataset Column Descriptions

The dataset includes several key columns, each providing vital information for understanding and utilizing the documents effectively in various AI and NLP tasks:

- **uid**: A unique identifier for each document, ensuring traceability and easy reference.
- **domain**: Represents the industry or sector to which the document belongs (e.g., healthcare, finance, technology). (see Domain Distribution below).
- **document_type**:  Specifies the category or format of the document within a given domain (e.g., invoices, contracts, medical records).
- **document_description**: Provides a detailed overview of the document’s structure, typical fields, and its intended purpose, offering additional context for document classification tasks.
- **text**: The core text content of the document, serving as a rich data source for various NLP tasks such as text classification, NER, and more.
- **entities**: A list of extracted PII/PHI entities within the document. Each entity is annotated with its type (e.g., name, address, date of birth), facilitating tasks like entity recognition and sensitive information extraction.

## Dataset Statistics and Distribution

This dataset is split into training (50k records), validation (5k), and test (5k) sets, with a distribution across multiple domains and entity types.

### Domain Distribution

The dataset contains documents from a wide range of domains, making it suitable for various industrial applications and research purposes.

| Domain | Train | Validation | Test |
| --- | --- | --- | --- |
| aerospace-defense | 1067 | 108 | 106 |
| agriculture-food-services | 1121 | 114 | 122 |
| authentication-services | 939 | 99 | 88 |
| automotive | 1112 | 103 | 97 |
| aviation | 1062 | 99 | 81 |
| banking | 1013 | 103 | 118 |
| biometrics | 1281 | 103 | 113 |
| blockchain | 1034 | 101 | 105 |
| cloud-services | 1065 | 120 | 118 |
| code-review | 659 | 56 | 66 |
| compliance-regulation | 1249 | 148 | 147 |
| cryptography | 1197 | 119 | 104 |
| cybersecurity | 927 | 104 | 103 |
| data-privacy | 1395 | 144 | 138 |
| defense-security | 1077 | 95 | 103 |
| digital-certificates | 1072 | 103 | 97 |
| digital-payments | 947 | 102 | 112 |
| e-commerce | 730 | 85 | 65 |
| education | 972 | 104 | 95 |
| energy-utilities | 1024 | 113 | 115 |
| finance | 1001 | 102 | 94 |
| financial-services | 1027 | 94 | 117 |
| government | 1224 | 124 | 111 |
| healthcare | 1207 | 108 | 133 |
| healthcare-administration | 1194 | 131 | 118 |
| human-resources | 933 | 80 | 79 |
| identity-verification | 1298 | 118 | 121 |
| information-technology | 808 | 73 | 87 |
| insurance | 1087 | 106 | 116 |
| internet-services | 1074 | 119 | 115 |
| legal-documents | 790 | 73 | 68 |
| logistics-transportation | 1291 | 147 | 130 |
| manufacturing | 1283 | 124 | 125 |
| marine | 1049 | 104 | 99 |
| media-entertainment | 864 | 93 | 81 |
| networking | 1097 | 109 | 92 |
| non-profit-charity | 920 | 86 | 85 |
| pharmaceuticals-biotechnology | 1273 | 133 | 152 |
| public-sector | 1234 | 124 | 119 |
| real-estate | 882 | 100 | 91 |
| retail-consumer-goods | 977 | 96 | 99 |
| security | 1155 | 119 | 111 |
| supply-chain | 1206 | 113 | 125 |
| technology-software | 917 | 93 | 79 |
| telecommunications | 1005 | 105 | 123 |
| transportation | 1286 | 143 | 134 |
| travel-hospitality | 975 | 60 | 103 |

### Entity Type Distribution

The dataset includes a broad variety of entity types, focusing heavily on PII and PHI to support privacy-enhancing model development.

| Entity Type | Train | Validation | Test |
| --- | --- | --- | --- |
| medical_record_number | 26031 | 2589 | 2658 |
| date_of_birth | 23684 | 2345 | 2331 |
| ssn | 16877 | 1734 | 1661 |
| date | 11740 | 1170 | 1157 |
| first_name | 11421 | 1098 | 1172 |
| email | 10891 | 1104 | 1049 |
| last_name | 10804 | 1040 | 1057 |
| customer_id | 10023 | 1025 | 1033 |
| employee_id | 9945 | 988 | 1005 |
| name | 9688 | 1015 | 980 |
| street_address | 8576 | 939 | 869 |
| phone_number | 8537 | 884 | 904 |
| ipv4 | 8235 | 817 | 896 |
| credit_card_number | 6469 | 634 | 663 |
| license_plate | 6000 | 613 | 579 |
| address | 5563 | 551 | 563 |
| user_name | 3252 | 305 | 338 |
| device_identifier | 2253 | 213 | 249 |
| bank_routing_number | 2158 | 210 | 257 |
| date_time | 2043 | 206 | 211 |
| company_name | 1950 | 177 | 185 |
| unique_identifier | 1842 | 189 | 189 |
| biometric_identifier | 1552 | 129 | 137 |
| account_number | 1328 | 134 | 141 |
| city | 1321 | 138 | 128 |
| certificate_license_number | 1307 | 133 | 124 |
| time | 1104 | 112 | 106 |
| postcode | 955 | 93 | 104 |
| vehicle_identifier | 941 | 101 | 98 |
| coordinate | 814 | 62 | 85 |
| country | 767 | 78 | 71 |
| api_key | 731 | 83 | 60 |
| ipv6 | 622 | 61 | 66 |
| password | 569 | 64 | 59 |
| health_plan_beneficiary_number | 446 | 48 | 41 |
| national_id | 425 | 44 | 46 |
| tax_id | 303 | 31 | 23 |
| url | 287 | 40 | 23 |
| state | 284 | 24 | 27 |
| swift_bic | 209 | 22 | 28 |
| cvv | 96 | 11 | 3 |
| pin | 27 | 4 | 2 |

## Fine-Tuned Models

We have fine-tuned multiple models using this dataset, which are available on Hugging Face:

- [`gretelai/gretel-gliner-bi-small-v1.0`](https://huggingface.co/gretelai/gretel-gliner-bi-small-v1.0)
- [`gretelai/gretel-gliner-bi-base-v1.0`](https://huggingface.co/gretelai/gretel-gliner-bi-base-v1.0)
- [`gretelai/gretel-gliner-bi-large-v1.0`](https://huggingface.co/gretelai/gretel-gliner-bi-large-v1.0)

These models are specifically designed for high-quality PII/PHI detection focusing on the entity types listed in this dataset.

## Citation and Usage

If you use this dataset in your research or applications, please cite it as:

```bibtex
@dataset{gretel-pii-docs-en-v1,
  author       = {Gretel AI},
  title        = {GLiNER Models for PII Detection through Fine-Tuning on Gretel-Generated Synthetic Documents},
  year         = {2024},
  month        = {10},
  publisher    = {Gretel},
}
```

For questions, issues, or additional information, please visit our [Synthetic Data Discord](https://gretel.ai/discord) community or reach out to [gretel.ai](https://gretel.ai/).