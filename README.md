# SA Banking Behaviour Pipeline 🏦

A production-style data engineering pipeline that ingests, cleans, and enriches synthetic South African retail banking transaction data — built on Databricks and Delta Lake with a Bronze / Silver / Gold medallion architecture.

---

## The Problem

South African retail banks process millions of transactions daily across channels — POS, EFT, mobile, ATM. Raw transaction data is messy, inconsistent, and not directly useful for business decisions. This pipeline transforms that raw data into a clean, enriched customer spending intelligence layer that analysts and data scientists can query directly.

---

## What This Pipeline Does

| Layer | What Happens |
|---|---|
| **Bronze** | Raw transactions landed as-is into Delta Lake — no changes, full history |
| **Silver** | Cleaned, standardised, deduplicated, merchant categories assigned |
| **Gold** | Customer-level spending intelligence — income detection, spending patterns, month-end stress signals |

---

## SA-Specific Features

- Salary deposit detection aligned to SA pay cycles (25th of month)
- SASSA grant recipient identification (1st of month deposits)
- SA merchant names — Shoprite, Checkers, Capitec, Vodacom, Engen, DStv, etc.
- Load shedding spending spike signals (candles, generators, data purchases)
- Month-end financial stress scoring
- Rand (ZAR) denominated transactions

---

## Stack

| Tool | Purpose |
|---|---|
| **Databricks** | Compute and notebook environment |
| **PySpark** | Distributed data processing |
| **Delta Lake** | Versioned, ACID-compliant storage |
| **Python** | Data generation and utilities |
| **GitHub Actions** | CI — lint and test on every push |

---

## Project Structure

```
sa-banking-behaviour-pipeline/
├── data/                          # Not committed — lives in Databricks DBFS
│   ├── raw/                       # Bronze layer
│   ├── silver/                    # Silver layer
│   └── gold/                      # Gold layer
├── notebooks/
│   ├── 01_generate_data.ipynb     # Synthetic SA transaction data generation
│   ├── 02_bronze_ingestion.ipynb  # Land raw CSV into Delta
│   ├── 03_silver_cleaning.ipynb   # Clean, standardise, categorise
│   ├── 04_gold_features.ipynb     # Customer spending intelligence
│   └── 05_analysis.ipynb          # Business queries and insights
├── src/
│   ├── generator/
│   │   └── transaction_generator.py   # SA synthetic data logic
│   ├── pipeline/
│   │   ├── bronze.py              # Bronze ingestion functions
│   │   ├── silver.py              # Silver transformation functions
│   │   └── gold.py                # Gold feature engineering
│   └── utils/
│       └── helpers.py             # Shared utilities
├── docs/
│   ├── ARCHITECTURE.md            # Pipeline design and decisions
│   ├── DATA_DICTIONARY.md         # Every column explained
│   └── DECISIONS.md               # Why each tech choice was made
├── .github/workflows/ci.yml       # GitHub Actions CI
├── requirements.txt
└── README.md
```

---

## Dataset

Synthetic data generated to reflect realistic South African retail banking patterns. Not real customer data.

- **~500,000 transactions**
- **~10,000 customers**
- **24 months of history** (Jan 2023 – Dec 2024)
- **SA merchant ecosystem** — grocery, fuel, telecoms, streaming, banking fees

---

## Author

**Morobang Tshigidimisa (Rocket)**
Data Engineer & ML Consultant
[github.com/Morobang](https://github.com/Morobang)
