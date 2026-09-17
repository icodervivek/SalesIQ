"""Deterministic cleaning pipeline for raw sales data.

Design principle: every transformation is logged into a `CleaningSummary`
so the API/dashboard can show *what* was done to the data, not just the
final result. This keeps the pipeline auditable, which matters more than
being clever for a forecasting system that business decisions depend on.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ml.preprocessing.validation import REQUIRED_COLUMNS


@dataclass
class CleaningSummary:
    input_rows: int
    output_rows: int
    dropped_invalid_dates: int = 0
    dropped_duplicates: int = 0
    dropped_missing_required: int = 0
    dropped_negative_values: int = 0
    imputed_unit_price: int = 0
    imputed_discount: int = 0
    imputed_marketing_spend: int = 0
    clipped_outliers: int = 0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__


def clean_sales_data(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningSummary]:
    df = raw_df.copy()
    input_rows = len(df)
    summary = CleaningSummary(input_rows=input_rows, output_rows=0)

    # 1. Parse dates, drop unparsable rows.
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = df["date"].isna()
    summary.dropped_invalid_dates = int(invalid_dates.sum())
    df = df.loc[~invalid_dates].copy()

    # 2. Drop exact duplicates.
    before = len(df)
    df = df.drop_duplicates()
    summary.dropped_duplicates = before - len(df)

    # 3. Coerce numeric columns; anything unparsable becomes NaN.
    numeric_cols = [c for c in ("units_sold", "unit_price", "discount", "marketing_spend", "revenue") if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Drop rows missing a required field that cannot be safely imputed
    #    (units_sold / revenue are the target signal — imputing them would
    #    fabricate demand, so those rows are removed instead).
    required_present = [c for c in REQUIRED_COLUMNS if c in df.columns]
    before = len(df)
    df = df.dropna(subset=[c for c in required_present if c in ("date", "product_id", "product_name", "units_sold", "revenue")])
    summary.dropped_missing_required = before - len(df)

    # 5. Remove structurally invalid negative values (units/revenue/price
    #    cannot be negative for a sale).
    before = len(df)
    mask = pd.Series(True, index=df.index)
    for col in ("units_sold", "revenue", "unit_price"):
        if col in df.columns:
            mask &= df[col].isna() | (df[col] >= 0)
    df = df.loc[mask]
    summary.dropped_negative_values = before - len(df)

    # 6. Impute recommended/optional numeric fields using per-product median
    #    (falls back to global median), rather than dropping the row.
    if "unit_price" in df.columns and df["unit_price"].isna().any():
        summary.imputed_unit_price = int(df["unit_price"].isna().sum())
        df["unit_price"] = df.groupby("product_id")["unit_price"].transform(lambda s: s.fillna(s.median()))
        df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())

    if "discount" in df.columns:
        summary.imputed_discount = int(df["discount"].isna().sum())
        df["discount"] = df["discount"].fillna(0.0)

    if "marketing_spend" in df.columns:
        summary.imputed_marketing_spend = int(df["marketing_spend"].isna().sum())
        df["marketing_spend"] = df["marketing_spend"].fillna(0.0)

    for col in ("category", "region"):
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # 7. Winsorize extreme outliers in units_sold per product (clip rather
    #    than drop, so legitimate demand spikes are dampened, not erased —
    #    a large spike is business signal, not necessarily an error).
    if "units_sold" in df.columns:
        def clip_group(s: pd.Series) -> pd.Series:
            if len(s) < 10:
                return s
            upper = s.quantile(0.995)
            return s.clip(upper=upper)

        clipped = df.groupby("product_id")["units_sold"].transform(clip_group)
        summary.clipped_outliers = int((clipped != df["units_sold"]).sum())
        df["units_sold"] = clipped

    df = df.sort_values("date").reset_index(drop=True)
    summary.output_rows = len(df)
    if summary.output_rows == 0:
        summary.notes.append("All rows were removed during cleaning — check the source file.")

    return df, summary
