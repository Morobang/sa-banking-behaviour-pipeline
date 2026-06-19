"""
silver.py
---------
Silver layer — cleans and standardises Bronze data.
Handles nulls, deduplication, type casting, and merchant category standardisation.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, TimestampType


def clean_transactions(df: DataFrame) -> DataFrame:
    """
    Clean and standardise the raw transactions table.
    - Cast types
    - Drop duplicates
    - Standardise merchant names
    - Add date part columns for partitioning
    - Flag nulls
    """
    df = df.dropDuplicates(["transaction_id"])

    df = df.withColumn("amount", F.col("amount").cast(DoubleType())) \
           .withColumn("transaction_date", F.col("transaction_date").cast(TimestampType())) \
           .withColumn("merchant_name", F.upper(F.trim(F.col("merchant_name")))) \
           .withColumn("merchant_category", F.lower(F.trim(F.col("merchant_category")))) \
           .withColumn("transaction_type", F.upper(F.trim(F.col("transaction_type")))) \
           .withColumn("channel", F.upper(F.trim(F.col("channel"))))

    df = df.withColumn("txn_year", F.year("transaction_date")) \
           .withColumn("txn_month", F.month("transaction_date")) \
           .withColumn("txn_day", F.dayofmonth("transaction_date")) \
           .withColumn("txn_day_of_week", F.dayofweek("transaction_date")) \
           .withColumn("txn_hour", F.hour("transaction_date")) \
           .withColumn("is_weekend", F.col("txn_day_of_week").isin([1, 7]).cast("boolean"))

    df = df.withColumn("is_month_end", F.col("txn_day") >= 20) \
           .withColumn("is_salary_period", F.col("txn_day").between(24, 26))

    df = df.filter(F.col("amount") > 0) \
           .filter(F.col("transaction_id").isNotNull()) \
           .filter(F.col("customer_id").isNotNull())

    df = df.withColumn("_silver_processed_at", F.current_timestamp())

    return df


def clean_customers(df: DataFrame) -> DataFrame:
    """Clean and standardise the customers table."""
    df = df.dropDuplicates(["customer_id"])

    df = df.withColumn("province", F.initcap(F.trim(F.col("province")))) \
           .withColumn("segment", F.lower(F.trim(F.col("segment")))) \
           .withColumn("monthly_income", F.col("monthly_income").cast(DoubleType()))

    df = df.filter(F.col("customer_id").isNotNull()) \
           .filter(F.col("monthly_income") > 0)

    df = df.withColumn("_silver_processed_at", F.current_timestamp())

    return df


def write_silver(df: DataFrame, table_name: str, silver_path: str, partition_by: list = None):
    """Write a cleaned DataFrame to the Silver Delta layer."""
    writer = df.write.format("delta").mode("overwrite")
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    output_path = f"{silver_path}/{table_name}"
    writer.save(output_path)
    print(f"[SILVER] {table_name}: {df.count():,} rows written to {output_path}")


def read_silver(spark: SparkSession, table_name: str, silver_path: str) -> DataFrame:
    """Read a Silver Delta table."""
    return spark.read.format("delta").load(f"{silver_path}/{table_name}")
