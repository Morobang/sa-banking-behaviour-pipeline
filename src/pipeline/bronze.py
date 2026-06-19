"""
bronze.py
---------
Bronze layer ingestion — lands raw CSV data into Delta Lake as-is.
No transformations. Full history. Audit columns added only.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from datetime import datetime


def get_spark() -> SparkSession:
    return SparkSession.builder.appName("sa-banking-bronze").getOrCreate()


def ingest_raw_csv(spark: SparkSession, path: str, table_name: str, bronze_path: str) -> DataFrame:
    """
    Read a raw CSV file and write it to the Bronze Delta table.
    Adds ingestion audit columns — no other changes to the data.
    """
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(path)

    df = df.withColumn("_ingested_at", F.current_timestamp()) \
           .withColumn("_source_file", F.lit(path)) \
           .withColumn("_batch_id", F.lit(datetime.now().strftime("%Y%m%d%H%M%S")))

    output_path = f"{bronze_path}/{table_name}"
    df.write.format("delta").mode("append").save(output_path)

    print(f"[BRONZE] {table_name}: {df.count():,} rows written to {output_path}")
    return df


def read_bronze(spark: SparkSession, table_name: str, bronze_path: str) -> DataFrame:
    """Read a Bronze Delta table."""
    return spark.read.format("delta").load(f"{bronze_path}/{table_name}")
