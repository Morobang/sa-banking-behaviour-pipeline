"""
helpers.py
----------
Shared utility functions used across the pipeline.
"""

from pyspark.sql import DataFrame
from datetime import datetime


def log(stage: str, message: str):
    """Simple pipeline logger."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{stage.upper()}] {message}")


def row_count(df: DataFrame, label: str = "") -> int:
    """Count rows and print with label."""
    count = df.count()
    if label:
        print(f"  Row count [{label}]: {count:,}")
    return count


def null_report(df: DataFrame) -> None:
    """Print null counts for every column."""
    from pyspark.sql import functions as F
    null_counts = df.select([
        F.sum(F.col(c).isNull().cast("int")).alias(c)
        for c in df.columns
    ])
    print("Null counts per column:")
    null_counts.show(vertical=True)


def describe_numeric(df: DataFrame, cols: list) -> None:
    """Quick descriptive stats on numeric columns."""
    df.select(cols).describe().show()
