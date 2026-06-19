"""
transaction_generator.py
------------------------
Generates realistic synthetic South African retail banking transaction data.
Produces ~500,000 transactions across ~10,000 customers over 24 months.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid

# ── Seed for reproducibility ──────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

# ── SA Merchant ecosystem ──────────────────────────────────────────────────────
MERCHANTS = {
    "grocery": [
        ("Shoprite", "SHOPRITE", 80, 800),
        ("Checkers", "CHECKERS", 80, 1200),
        ("Pick n Pay", "PICK N PAY", 60, 900),
        ("Woolworths Food", "WOOLWORTHS", 100, 2000),
        ("Spar", "SPAR", 50, 600),
        ("Boxer", "BOXER", 40, 400),
    ],
    "fuel": [
        ("Engen", "ENGEN", 300, 1200),
        ("Shell", "SHELL", 300, 1200),
        ("BP", "BP", 300, 1200),
        ("Sasol", "SASOL", 300, 1200),
        ("Total", "TOTAL", 300, 1200),
    ],
    "telecoms": [
        ("Vodacom Airtime", "VODACOM", 10, 100),
        ("MTN Airtime", "MTN", 10, 100),
        ("Cell C Airtime", "CELL C", 10, 50),
        ("Telkom Mobile", "TELKOM", 10, 100),
        ("Vodacom Data", "VODACOM DATA", 50, 299),
        ("MTN Data", "MTN DATA", 50, 299),
    ],
    "streaming": [
        ("Netflix", "NETFLIX", 99, 199),
        ("DStv", "DSTV", 109, 839),
        ("Showmax", "SHOWMAX", 99, 179),
        ("Spotify", "SPOTIFY", 59, 59),
    ],
    "banking_fees": [
        ("Monthly Account Fee", "BANK FEE", 50, 200),
        ("ATM Withdrawal Fee", "ATM FEE", 5, 10),
        ("Transaction Fee", "TXN FEE", 1, 5),
    ],
    "fast_food": [
        ("KFC", "KFC", 50, 300),
        ("Nandos", "NANDOS", 80, 400),
        ("McDonald's", "MCDONALDS", 50, 250),
        ("Steers", "STEERS", 50, 200),
        ("Chicken Licken", "CHICKEN LICKEN", 40, 180),
    ],
    "pharmacy": [
        ("Clicks", "CLICKS", 30, 800),
        ("Dis-Chem", "DIS-CHEM", 30, 1000),
        ("Alpha Pharm", "ALPHA PHARM", 20, 300),
    ],
    "transport": [
        ("Uber", "UBER", 30, 300),
        ("Bolt", "BOLT", 25, 200),
        ("Gautrain", "GAUTRAIN", 15, 80),
    ],
    "load_shedding": [
        ("Builders Warehouse", "BUILDERS", 50, 3000),
        ("Makro Generator", "MAKRO", 500, 8000),
        ("Incredible Connection", "INCREDIBLE", 100, 5000),
        ("Candles & Lamps", "GAME STORES", 30, 200),
    ],
    "insurance": [
        ("Discovery Life", "DISCOVERY", 200, 2000),
        ("Old Mutual", "OLD MUTUAL", 150, 1500),
        ("Sanlam", "SANLAM", 150, 1500),
    ],
}

# ── Customer segments ──────────────────────────────────────────────────────────
SEGMENTS = {
    "salaried_professional": {
        "weight": 0.35,
        "income_range": (18000, 80000),
        "income_day": 25,
        "spending_intensity": "high",
    },
    "salaried_entry_level": {
        "weight": 0.30,
        "income_range": (5000, 17999),
        "income_day": 25,
        "spending_intensity": "medium",
    },
    "informal_income": {
        "weight": 0.20,
        "income_range": (2000, 8000),
        "income_day": None,  # irregular
        "spending_intensity": "low",
    },
    "sassa_recipient": {
        "weight": 0.15,
        "income_range": (350, 2090),
        "income_day": 1,
        "spending_intensity": "very_low",
    },
}

# ── Province list ──────────────────────────────────────────────────────────────
PROVINCES = [
    "Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape",
    "Limpopo", "Mpumalanga", "North West", "Free State", "Northern Cape"
]


def generate_customers(n: int = 10000) -> pd.DataFrame:
    """Generate a customer master table."""
    customers = []
    segment_names = list(SEGMENTS.keys())
    segment_weights = [SEGMENTS[s]["weight"] for s in segment_names]

    for i in range(n):
        segment = random.choices(segment_names, weights=segment_weights, k=1)[0]
        seg = SEGMENTS[segment]
        income_min, income_max = seg["income_range"]
        monthly_income = round(random.uniform(income_min, income_max), 2)

        customers.append({
            "customer_id": f"CUS{str(i+1).zfill(6)}",
            "segment": segment,
            "province": random.choice(PROVINCES),
            "monthly_income": monthly_income,
            "income_day": seg["income_day"],
            "spending_intensity": seg["spending_intensity"],
            "account_opened": (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 900))).date(),
        })

    return pd.DataFrame(customers)


def _get_merchant(category: str) -> tuple:
    """Pick a random merchant from a category."""
    return random.choice(MERCHANTS[category])


def _spending_categories_for_segment(segment: str) -> list:
    """Return weighted category list based on customer segment."""
    base = [
        ("grocery", 30),
        ("telecoms", 20),
        ("fast_food", 10),
        ("pharmacy", 5),
        ("banking_fees", 10),
    ]
    if segment in ("salaried_professional", "salaried_entry_level"):
        base += [("fuel", 10), ("streaming", 8), ("transport", 5), ("insurance", 7)]
    if segment == "salaried_professional":
        base += [("load_shedding", 5)]
    if segment == "informal_income":
        base += [("transport", 10)]

    categories = [c for c, _ in base]
    weights = [w for _, w in base]
    return categories, weights


def generate_transactions(customers: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate transaction records for all customers across the date range."""
    transactions = []
    total_days = (end_date - start_date).days

    for _, customer in customers.iterrows():
        cust_id = customer["customer_id"]
        segment = customer["segment"]
        income = customer["monthly_income"]
        income_day = customer["income_day"]
        intensity = customer["spending_intensity"]

        # How many transactions per month roughly
        txn_per_month = {
            "very_low": random.randint(5, 15),
            "low": random.randint(15, 30),
            "medium": random.randint(30, 60),
            "high": random.randint(60, 120),
        }[intensity]

        categories, weights = _spending_categories_for_segment(segment)

        # Generate transactions month by month
        current = start_date
        while current <= end_date:
            month_txns = random.randint(int(txn_per_month * 0.7), int(txn_per_month * 1.3))

            # Income deposit
            if income_day:
                deposit_date = current.replace(day=min(income_day, 28))
                transactions.append({
                    "transaction_id": str(uuid.uuid4()),
                    "customer_id": cust_id,
                    "transaction_date": deposit_date + timedelta(hours=random.randint(6, 10)),
                    "amount": round(income * random.uniform(0.95, 1.05), 2),
                    "transaction_type": "CREDIT",
                    "merchant_name": "SALARY DEPOSIT" if segment != "sassa_recipient" else "SASSA GRANT",
                    "merchant_category": "income",
                    "channel": "EFT",
                    "province": customer["province"],
                    "segment": segment,
                })
            else:
                # Informal — random deposits throughout month
                for _ in range(random.randint(1, 4)):
                    dep_day = random.randint(1, 28)
                    dep_date = current.replace(day=dep_day)
                    transactions.append({
                        "transaction_id": str(uuid.uuid4()),
                        "customer_id": cust_id,
                        "transaction_date": dep_date + timedelta(hours=random.randint(8, 17)),
                        "amount": round(random.uniform(200, income * 0.5), 2),
                        "transaction_type": "CREDIT",
                        "merchant_name": "CASH DEPOSIT",
                        "merchant_category": "income",
                        "channel": "ATM",
                        "province": customer["province"],
                        "segment": segment,
                    })

            # Spending transactions
            for _ in range(month_txns):
                cat = random.choices(categories, weights=weights, k=1)[0]
                merchant_name, merchant_code, min_amt, max_amt = _get_merchant(cat)
                txn_day = random.randint(1, 28)
                txn_date = current.replace(day=txn_day)

                # Month-end squeeze — spend less after 20th if low income
                if txn_day > 20 and segment in ("sassa_recipient", "informal_income"):
                    max_amt = max_amt * 0.4

                transactions.append({
                    "transaction_id": str(uuid.uuid4()),
                    "customer_id": cust_id,
                    "transaction_date": txn_date + timedelta(
                        hours=random.randint(7, 21),
                        minutes=random.randint(0, 59)
                    ),
                    "amount": round(random.uniform(min_amt, max_amt), 2),
                    "transaction_type": "DEBIT",
                    "merchant_name": merchant_name,
                    "merchant_category": cat,
                    "channel": random.choices(["POS", "MOBILE", "ONLINE", "ATM"], weights=[50, 30, 15, 5])[0],
                    "province": customer["province"],
                    "segment": segment,
                })

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

    df = pd.DataFrame(transactions)
    df = df.sort_values("transaction_date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("Generating customers...")
    customers = generate_customers(n=10000)
    print(f"  {len(customers):,} customers generated")

    print("Generating transactions...")
    start = datetime(2023, 1, 1)
    end = datetime(2024, 12, 31)
    transactions = generate_transactions(customers, start, end)
    print(f"  {len(transactions):,} transactions generated")

    print("Saving to data/raw/...")
    customers.to_csv("data/raw/customers.csv", index=False)
    transactions.to_csv("data/raw/transactions.csv", index=False)
    print("Done!")
