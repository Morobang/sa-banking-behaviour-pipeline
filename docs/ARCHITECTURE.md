# Architecture

## Pipeline Overview

```
Raw CSV Files
     │
     ▼
┌─────────────┐
│   BRONZE    │  Raw data landed as-is into Delta Lake
│             │  Audit columns added (_ingested_at, _source_file, _batch_id)
│             │  No transformations — full history preserved
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SILVER    │  Cleaned and standardised
│             │  - Deduplication on transaction_id
│             │  - Type casting (amounts → double, dates → timestamp)
│             │  - Merchant name standardisation (UPPER TRIM)
│             │  - Date part columns added (year, month, day, hour)
│             │  - SA-specific flags (is_month_end, is_salary_period, is_weekend)
│             │  - Null and invalid row filtering
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    GOLD     │  Business-ready aggregated intelligence
│             │  - customer_monthly_summary: per customer per month KPIs
│             │  - customer_profile: lifetime profile + financial stress flag
└─────────────┘
```

## Gold Layer Tables

### customer_monthly_summary
One row per customer per month. Used for trend analysis and forecasting.

| Column | Description |
|---|---|
| customer_id | Unique customer identifier |
| txn_year | Year |
| txn_month | Month number |
| total_spend | Total debit spend for the month |
| total_income_received | Total credits received |
| debit_txn_count | Number of debit transactions |
| credit_txn_count | Number of credit transactions |
| unique_merchants | Number of distinct merchants visited |
| avg_txn_amount | Average transaction size |
| max_txn_amount | Largest single transaction |
| top_category | Highest spend merchant category |
| month_end_spend | Total spend from day 20 onwards |
| month_end_stress_ratio | month_end_spend / total_spend |
| spend_to_income_ratio | total_spend / total_income_received |

### customer_profile
One row per customer. Lifetime aggregated view.

| Column | Description |
|---|---|
| customer_id | Unique customer identifier |
| segment | Customer segment (salaried, informal, sassa) |
| province | SA province |
| monthly_income | Declared/estimated monthly income |
| lifetime_spend | Total all-time spend |
| lifetime_txn_count | Total transactions ever |
| avg_txn_value | Average transaction value |
| category_diversity | Number of distinct spending categories used |
| preferred_channel | Most used transaction channel (POS/MOBILE/ONLINE/ATM) |
| avg_stress_ratio | Average month-end stress ratio across all months |
| avg_spend_to_income | Average spend-to-income ratio |
| is_financially_stressed | True if avg_stress_ratio > 0.60 |

## Design Decisions

See [DECISIONS.md](DECISIONS.md) for the reasoning behind each architectural choice.
