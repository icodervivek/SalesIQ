from __future__ import annotations

import pandas as pd


def summary_kpis(df: pd.DataFrame) -> dict:
    total_revenue = float(df["revenue"].sum())
    total_units = int(df["units_sold"].sum())
    avg_order_value = float(df["revenue"].sum() / max(len(df), 1))

    daily = df.groupby(df["date"].dt.date)["revenue"].sum().sort_index()
    growth_rate = 0.0
    if len(daily) >= 14:
        recent = daily.iloc[-7:].sum()
        previous = daily.iloc[-14:-7].sum()
        if previous > 0:
            growth_rate = round((recent - previous) / previous * 100, 2)

    return {
        "total_revenue": round(total_revenue, 2),
        "total_units_sold": total_units,
        "average_order_value": round(avg_order_value, 2),
        "revenue_growth_rate_pct": growth_rate,
        "date_range": {
            "start": df["date"].min().strftime("%Y-%m-%d"),
            "end": df["date"].max().strftime("%Y-%m-%d"),
        },
        "num_products": int(df["product_id"].nunique()),
        "num_regions": int(df["region"].nunique()) if "region" in df.columns else 0,
    }


def revenue_trend(df: pd.DataFrame, freq: str = "D") -> list[dict]:
    series = df.groupby(pd.Grouper(key="date", freq=freq)).agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum")).reset_index()
    return [
        {"date": row["date"].strftime("%Y-%m-%d"), "revenue": round(float(row["revenue"]), 2), "units_sold": int(row["units_sold"])}
        for _, row in series.iterrows()
    ]


def top_products(df: pd.DataFrame, n: int = 10) -> list[dict]:
    grouped = (
        df.groupby(["product_id", "product_name"])
        .agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(n)
    )
    return [
        {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "revenue": round(float(row["revenue"]), 2),
            "units_sold": int(row["units_sold"]),
        }
        for _, row in grouped.iterrows()
    ]


def regional_performance(df: pd.DataFrame) -> list[dict]:
    if "region" not in df.columns:
        return []
    grouped = df.groupby("region").agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum")).reset_index().sort_values("revenue", ascending=False)
    return [
        {"region": row["region"], "revenue": round(float(row["revenue"]), 2), "units_sold": int(row["units_sold"])}
        for _, row in grouped.iterrows()
    ]


def category_performance(df: pd.DataFrame) -> list[dict]:
    if "category" not in df.columns:
        return []
    grouped = df.groupby("category").agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum")).reset_index().sort_values("revenue", ascending=False)
    return [
        {"category": row["category"], "revenue": round(float(row["revenue"]), 2), "units_sold": int(row["units_sold"])}
        for _, row in grouped.iterrows()
    ]


def list_products(df: pd.DataFrame) -> list[dict]:
    return (
        df[["product_id", "product_name"]]
        .drop_duplicates()
        .sort_values("product_name")
        .to_dict("records")
    )


def list_regions(df: pd.DataFrame) -> list[str]:
    if "region" not in df.columns:
        return []
    return sorted(df["region"].dropna().unique().tolist())
