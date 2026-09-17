"""
Generates additional sample datasets beyond the main sample_sales.csv, each
built to exercise a different part of SalesIQ:

  - fmcg_grocery_sample.csv   : a different business vertical (high-volume,
                                low-price daily grocery items) with weekend
                                and payday seasonality instead of the main
                                dataset's electronics/furniture patterns.
  - minimal_history_sample.csv: exactly at the MIN_HISTORY_DAYS=45 boundary,
                                to test/demonstrate the training endpoint's
                                minimum-history validation.
  - sparse_gaps_sample.csv    : a single product/region series with entire
                                calendar days missing from the source file
                                (not just dirty rows) to exercise
                                aggregate_daily_series's gap-filling.

Usage:
    python scripts/generate_extra_samples.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)


def generate_fmcg_grocery_sample() -> pd.DataFrame:
    start, end = pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-31")
    dates = pd.date_range(start, end, freq="D")

    products = [
        ("G001", "Milk 1L", "Dairy", 55, 220.0),
        ("G002", "Bread Loaf", "Bakery", 45, 140.0),
        ("G003", "Eggs (12)", "Dairy", 90, 95.0),
        ("G004", "Rice 5kg", "Staples", 320, 60.0),
        ("G005", "Cooking Oil 1L", "Staples", 140, 75.0),
        ("G006", "Bananas 1kg", "Produce", 40, 130.0),
        ("G007", "Instant Noodles", "Packaged Foods", 18, 300.0),
    ]
    regions = ["North", "South", "East", "West"]

    rows = []
    for product_id, name, category, price, base_units in products:
        for region in regions:
            region_factor = RNG.uniform(0.7, 1.25)
            for i, date in enumerate(dates):
                # Grocery seasonality: weekend + month-start "payday" spikes,
                # mild upward trend, much higher noise-to-signal than
                # discretionary electronics purchases.
                weekend = 1.4 if date.dayofweek >= 5 else 1.0
                payday = 1.5 if date.day <= 3 else 1.0
                trend = 1 + 0.0003 * i
                noise = RNG.normal(1.0, 0.22)
                units = max(0, int(round(base_units * region_factor * weekend * payday * trend * noise)))

                discount = float(RNG.choice([0, 0, 5, 10], p=[0.7, 0.1, 0.1, 0.1]))
                unit_price = round(price * RNG.uniform(0.96, 1.04), 2)
                revenue = round(units * unit_price * (1 - discount / 100), 2)

                rows.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "product_id": product_id,
                        "product_name": name,
                        "category": category,
                        "region": region,
                        "units_sold": units,
                        "unit_price": unit_price,
                        "discount": discount,
                        "marketing_spend": round(float(RNG.uniform(0, 800)) if RNG.random() < 0.15 else 0.0, 2),
                        "revenue": revenue,
                    }
                )

    return pd.DataFrame(rows).sample(frac=1.0, random_state=11).reset_index(drop=True)


def generate_minimal_history_sample(days: int = 50) -> pd.DataFrame:
    dates = pd.date_range("2025-10-01", periods=days, freq="D")
    rows = []
    for i, date in enumerate(dates):
        units = max(0, int(round(14 + 4 * np.sin(2 * np.pi * i / 7) + RNG.normal(0, 2))))
        unit_price = 1200.0
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "product_id": "M001",
                "product_name": "Desk Lamp",
                "category": "Home Appliances",
                "region": "East",
                "units_sold": units,
                "unit_price": unit_price,
                "discount": 0,
                "marketing_spend": 0,
                "revenue": round(units * unit_price, 2),
            }
        )
    return pd.DataFrame(rows)


def generate_sparse_gaps_sample() -> pd.DataFrame:
    dates = pd.date_range("2024-06-01", "2025-06-30", freq="D")
    # Drop ~12% of calendar days entirely (not present in the file at all) —
    # simulates a POS export with real outage/no-submission gaps.
    keep_mask = RNG.random(len(dates)) > 0.12
    kept_dates = dates[keep_mask]

    rows = []
    for i, date in enumerate(kept_dates):
        units = max(0, int(round(20 + 6 * np.sin(2 * np.pi * date.dayofyear / 365) + RNG.normal(0, 3))))
        unit_price = 850.0
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "product_id": "S001",
                "product_name": "Bluetooth Speaker",
                "category": "Electronics",
                "region": "South",
                "units_sold": units,
                "unit_price": unit_price,
                "discount": 0,
                "marketing_spend": 0,
                "revenue": round(units * unit_price, 2),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    fmcg = generate_fmcg_grocery_sample()
    fmcg.to_csv("data/fmcg_grocery_sample.csv", index=False)
    print(f"Wrote {len(fmcg):,} rows to data/fmcg_grocery_sample.csv")

    minimal = generate_minimal_history_sample()
    minimal.to_csv("data/minimal_history_sample.csv", index=False)
    print(f"Wrote {len(minimal):,} rows to data/minimal_history_sample.csv")

    sparse = generate_sparse_gaps_sample()
    sparse.to_csv("data/sparse_gaps_sample.csv", index=False)
    print(f"Wrote {len(sparse):,} rows to data/sparse_gaps_sample.csv")
