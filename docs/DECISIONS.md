# Technical Decisions

## Why Databricks?
South African banks (FNB, Nedbank, Absa, Standard Bank) run Databricks internally for large-scale data processing. Building this project on Databricks makes the work directly transferable to those environments. It also demonstrates comfort with enterprise-grade tooling rather than just local Python scripts.

## Why Delta Lake over plain Parquet?
Delta Lake gives us ACID transactions, schema enforcement, and time travel on top of Parquet. In a real bank environment you need to be able to roll back bad ingestion runs and audit what data looked like at a specific point in time. Plain Parquet cannot do this.

## Why medallion architecture (Bronze / Silver / Gold)?
- **Bronze** — raw data is preserved forever. If the Silver transformation has a bug, we can reprocess from Bronze without re-ingesting from source.
- **Silver** — clean, typed, standardised data that multiple downstream consumers can trust.
- **Gold** — pre-aggregated business tables that analysts can query without needing to understand the raw schema.

This is the standard pattern used at SA banks, Discovery, Multichoice, and most large data teams.

## Why synthetic data instead of real data?
Real SA banking transaction data is not publicly available for obvious regulatory reasons (POPIA, PCI-DSS). Generating synthetic data that mirrors realistic SA spending patterns — SA merchants, SA pay cycles, SA customer segments — demonstrates understanding of the domain without exposing real customer information.

## Why partition Silver transactions by year and month?
Transaction tables grow to hundreds of millions of rows over time. Partitioning by year/month means queries filtered to a specific period (e.g. "last 3 months") only scan the relevant partitions rather than the full table — drastically reducing query time and cost.
