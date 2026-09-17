"""
Generates a realistic synthetic sales dataset for SalesIQ.

Produces ~24 months of daily transactions across multiple products,
categories and regions with trend, weekly seasonality, yearly seasonality,
promotions, and a handful of intentionally "dirty" rows so the
preprocessing pipeline has real edge cases to handle.

Usage:
    python scripts/generate_sample_data.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

START_DATE = pd.Timestamp("2024-01-01")
END_DATE = pd.Timestamp("2025-12-31")

PRODUCTS = [
    ("P001", "Laptop Pro", "Electronics", 60000, 8.0),
    ("P002", "Wireless Mouse", "Electronics", 900, 25.0),
    ("P003", "Office Chair", "Furniture", 7500, 4.0),
    ("P004", "Standing Desk", "Furniture", 15000, 3.0),
    ("P005", "Running Shoes", "Apparel", 3200, 12.0),
    ("P006", "Winter Jacket", "Apparel", 5400, 6.0),
    ("P007", "Blender", "Home Appliances", 2800, 7.0),
    ("P008", "Air Purifier", "Home Appliances", 9800, 5.0),
    ("P009", "Bluetooth Speaker", "Electronics", 2200, 14.0),
    ("P010", "Yoga Mat", "Fitness", 1200, 18.0),
]

REGIONS = ["North", "South", "East", "West"]


def seasonal_multiplier(date: pd.Timestamp) -> float:
    day_of_year = date.dayofyear
    yearly = 1 + 0.25 * np.sin(2 * np.pi * (day_of_year - 60) / 365)
    weekday = 1.35 if date.dayofweek >= 5 else 1.0
    festive = 1.6 if date.month in (11, 12) else 1.0
    return yearly * weekday * festive


def generate() -> pd.DataFrame:
    rows = []
    dates = pd.date_range(START_DATE, END_DATE, freq="D")

    for product_id, product_name, category, base_price, base_daily_units in PRODUCTS:
        trend_growth = RNG.uniform(0.00015, 0.00045)
        for region in REGIONS:
            region_factor = RNG.uniform(0.6, 1.3)
            for i, date in enumerate(dates):
                trend = 1 + trend_growth * i
                seasonal = seasonal_multiplier(date)
                noise = RNG.normal(1.0, 0.18)
                expected_units = base_daily_units * region_factor * trend * seasonal * noise
                units_sold = max(0, int(round(expected_units)))

                discount = float(RNG.choice([0, 0, 0, 5, 10, 15], p=[0.55, 0.1, 0.1, 0.1, 0.1, 0.05]))
                marketing_spend = round(float(RNG.uniform(500, 6000)) if RNG.random() < 0.3 else 0.0, 2)
                unit_price = round(base_price * RNG.uniform(0.97, 1.03), 2)
                revenue = round(units_sold * unit_price * (1 - discount / 100), 2)

                rows.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "product_id": product_id,
                        "product_name": product_name,
                        "category": category,
                        "region": region,
                        "units_sold": units_sold,
                        "unit_price": unit_price,
                        "discount": discount,
                        "marketing_spend": marketing_spend,
                        "revenue": revenue,
                    }
                )

    df = pd.DataFrame(rows)

    # ---- Inject realistic data-quality issues (for the pipeline to handle) ----
    dirty_idx = RNG.choice(df.index, size=int(len(df) * 0.015), replace=False)
    half = len(dirty_idx) // 5

    df.loc[dirty_idx[:half], "revenue"] = np.nan
    df.loc[dirty_idx[half:2 * half], "units_sold"] = -1
    df.loc[dirty_idx[2 * half:3 * half], "date"] = "not-a-date"
    df.loc[dirty_idx[3 * half:4 * half], "unit_price"] = np.nan
    dup_rows = df.loc[dirty_idx[4 * half:]]
    df = pd.concat([df, dup_rows], ignore_index=True)

    df = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
    return df


if __name__ == "__main__":
    data = generate()
    out_path = "data/sample_sales.csv"
    data.to_csv(out_path, index=False)
    print(f"Wrote {len(data):,} rows to {out_path}")
