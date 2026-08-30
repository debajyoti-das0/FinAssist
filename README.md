# FinAssist — Financial Intelligence Assistant

FinAssist is a financial analytics and compliance assistant that combines structured transaction analysis with compliance-document retrieval. The project is designed around a simple idea: a user should be able to ask questions in normal language and get either data-driven results, compliance guidance, or both.

## What this project demonstrates

- Natural-language financial queries routed to the appropriate processing path
- Text-to-SQL style structured-data analysis for accounts, transactions, and fraud patterns
- SQL safety checks that keep the data-access path read-only
- Retrieval-based compliance guidance for KYC, AML, and fraud-prevention questions
- Query classification for SQL, RAG, and mixed-intent requests
- Fraud exploration using merchant-level and transaction-level analysis
- Quantitative evaluation covering accuracy, safety, retrieval quality, and latency
- An end-to-end fraud investigation workflow

## Project structure

```text
FinAssist/
├── FinAssist_Demo_and_Evaluation.ipynb
├── README.md
├── requirements.txt
└── .gitignore
```

## Quick start

Clone the repository and install the required packages:

```bash
pip install -r requirements.txt
```

Then open:

```text
FinAssist_Demo_and_Evaluation.ipynb
```

The notebook is self-contained and uses a reproducible demonstration dataset, so it can be run without the original local project modules. The outputs are already saved in the notebook and should be visible when GitHub renders it.

## How the notebook is organized

1. Setup and reproducible demonstration environment
2. Database exploration and sample financial records
3. SQL safety guardrails
4. Natural-language query execution examples
5. RAG retrieval for compliance questions
6. Query routing and confidence checks
7. Text-to-SQL and RAG evaluation metrics
8. Performance benchmarks
9. Limitations and failure analysis
10. End-to-end fraud investigation
11. System architecture and final summary

## Evaluation snapshot

The notebook reports the following project evaluation figures:

| Area | Reported result |
|---|---:|
| Text-to-SQL Exact Match | 78% |
| Text-to-SQL Execution Accuracy | 85% |
| RAG Retrieval Accuracy@5 | 84% |
| RAG Groundedness | 90% |
| SQL Injection Prevention (tested set) | 100% |

These numbers are presented as reported evaluation results from the project notebook. They should be reproduced with the original full training/evaluation setup before being used as production benchmarks.

## Notes

- The notebook is designed to be easy to review directly on GitHub.
- Cell outputs are saved before packaging.
- The examples use deterministic synthetic financial data for reproducibility.
- The notebook clearly separates demonstration behavior from reported evaluation figures.
- The current package contains the complete material that was provided for this upload: the evaluation notebook plus the repository documentation and setup files.

## Limitations

The current evaluation scope is intentionally documented in the notebook. In particular, complex SQL, broader regulatory coverage, larger document collections, and production-scale concurrency would need additional validation before deployment in a real financial environment.

## Tech stack

Python · Pandas · NumPy · Jupyter Notebook

---

If you use this repository as a portfolio project, the notebook is the best place to start because it shows the complete workflow, evaluation, limitations, and saved execution results in one file.
