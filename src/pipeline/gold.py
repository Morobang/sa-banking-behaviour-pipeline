"""
gold.py
-------
Gold layer — customer spending intelligence.
Produces business-ready aggregated tables that analysts can query directly.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def build_customer_monthly_summary(txn_df: DataFrame) -> DataFrame:
    """
    Per customer, per month summary:
    - Total spend
    - Total income received
    - Transaction count
    - Unique merchant count
    - Top spending category
    - Month-end spend ratio (spend after 20th vs full month)
    """
    debits = txn_df.filter(F.col("transaction_type") == "DEBIT")
    credits = txn_df.filter(F.col("transaction_type") == "CREDIT")

    monthly_spend = debits.groupBy("customer_id", "txn_year", "txn_month").agg(
        F.sum("amount").alias("total_spend"),
        F.count("transaction_id").alias("debit_txn_count"),
        F.countDistinct("merchant_name").alias("unique_merchants"),
        F.avg("amount").alias("avg_txn_amount"),
        F.max("amount").alias("max_txn_amount"),
    )

    month_end_spend = debits.filter(F.col("is_month_end")).groupBy("customer_id", "txn_year", "txn_month").agg(
        F.sum("amount").alias("month_end_spend")
    )

    monthly_income = credits.groupBy("customer_id", "txn_year", "txn_month").agg(
        F.sum("amount").alias("total_income_received"),
        F.count("transaction_id").alias("credit_txn_count"),
    )

    # Top category per customer per month
    cat_spend = debits.groupBy("customer_id", "txn_year", "txn_month", "merchant_category").agg(
        F.sum("amount").alias("cat_spend")
    )
    window = Window.partitionBy("customer_id", "txn_year", "txn_month").orderBy(F.desc("cat_spend"))
    top_cat = cat_spend.withColumn("rank", F.rank().over(window)).filter(F.col("rank") == 1) \
                       .select("customer_id", "txn_year", "txn_month", F.col("merchant_category").alias("top_category"))

    # Join everything
    result = monthly_spend \
        .join(monthly_income, ["customer_id", "txn_year", "txn_month"], "left") \
        .join(month_end_spend, ["customer_id", "txn_year", "txn_month"], "left") \
        .join(top_cat, ["customer_id", "txn_year", "txn_month"], "left")

    # Month-end stress ratio — what % of spending happens after 20th
    result = result.withColumn(
        "month_end_stress_ratio",
        F.round(F.col("month_end_spend") / F.col("total_spend"), 4)
    )

    # Spend-to-income ratio
    result = result.withColumn(
        "spend_to_income_ratio",
        F.round(F.col("total_spend") / F.col("total_income_received"), 4)
    )

    result = result.withColumn("_gold_processed_at", F.current_timestamp())
    return result


def build_customer_profile(txn_df: DataFrame, customer_df: DataFrame) -> DataFrame:
    """
    Lifetime customer profile:
    - Average monthly spend
    - Most used channel
    - Most shopped merchant category
    - Estimated income band
    - Financial stress flag
    """
    debits = txn_df.filter(F.col("transaction_type") == "DEBIT")

    # Most used channel
    channel_counts = debits.groupBy("customer_id", "channel").agg(F.count("*").alias("cnt"))
    w = Window.partitionBy("customer_id").orderBy(F.desc("cnt"))
    top_channel = channel_counts.withColumn("rank", F.rank().over(w)).filter(F.col("rank") == 1) \
                                .select("customer_id", F.col("channel").alias("preferred_channel"))

    # Overall spend stats
    spend_stats = debits.groupBy("customer_id").agg(
        F.sum("amount").alias("lifetime_spend"),
        F.count("transaction_id").alias("lifetime_txn_count"),
        F.avg("amount").alias("avg_txn_value"),
        F.countDistinct("merchant_category").alias("category_diversity"),
    )

    # High month-end stress flag — if >60% of spend is after 20th on average
    monthly = build_customer_monthly_summary(txn_df)
    stress = monthly.groupBy("customer_id").agg(
        F.avg("month_end_stress_ratio").alias("avg_stress_ratio"),
        F.avg("spend_to_income_ratio").alias("avg_spend_to_income"),
    )
    stress = stress.withColumn("is_financially_stressed", F.col("avg_stress_ratio") > 0.6)

    result = customer_df \
        .join(spend_stats, "customer_id", "left") \
        .join(top_channel, "customer_id", "left") \
        .join(stress, "customer_id", "left")

    result = result.withColumn("_gold_processed_at", F.current_timestamp())
    return result


def write_gold(df: DataFrame, table_name: str, gold_path: str):
    """Write a Gold table to Delta Lake."""
    output_path = f"{gold_path}/{table_name}"
    df.write.format("delta").mode("overwrite").save(output_path)
    print(f"[GOLD] {table_name}: {df.count():,} rows written to {output_path}")


def read_gold(spark: SparkSession, table_name: str, gold_path: str) -> DataFrame:
    """Read a Gold Delta table."""
    return spark.read.format("delta").load(f"{gold_path}/{table_name}")
