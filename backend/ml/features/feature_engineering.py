"""Feature engineering for time-series sales forecasting.

Operates on a *daily aggregated* series (a single product/region/global
series with one row per date). All lag/rolling features are computed
strictly from the past — no feature uses information from t or later
other than the calendar features, which prevents target leakage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LAGS = (1, 7, 14, 30)
ROLLING_WINDOWS = (7, 14, 30)


def aggregate_daily_series(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    """Aggregates transaction-level rows into a complete daily time series.

    If group_cols is given (e.g. ["product_id"]), aggregates per group and
    fills any missing calendar days within each group's date range with 0
    sales so lag/rolling windows are well-defined (a gap in the series is
    not the same as "no demand", but for forecasting purposes a missing day
    is treated as zero recorded sales, which is documented as an assumption
    in the README).
    """
    group_cols = group_cols or []
    agg_map = {"units_sold": "sum", "revenue": "sum"}
    if "discount" in df.columns:
        agg_map["discount"] = "mean"
    if "marketing_spend" in df.columns:
        agg_map["marketing_spend"] = "sum"
    if "unit_price" in df.columns:
        agg_map["unit_price"] = "mean"

    daily = df.groupby(group_cols + ["date"], as_index=False).agg(agg_map)

    if not group_cols:
        full_range = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
        daily = daily.set_index("date").reindex(full_range)
        daily.index.name = "date"
        fill_cols = [c for c in agg_map if c in daily.columns]
        daily[fill_cols] = daily[fill_cols].fillna(0.0)
        daily = daily.reset_index()
        return daily

    frames = []
    for keys, sub in daily.groupby(group_cols):
        full_range = pd.date_range(sub["date"].min(), sub["date"].max(), freq="D")
        sub = sub.set_index("date").reindex(full_range)
        sub.index.name = "date"
        fill_cols = [c for c in agg_map if c in sub.columns]
        sub[fill_cols] = sub[fill_cols].fillna(0.0)
        keys_tuple = keys if isinstance(keys, tuple) else (keys,)
        for col, val in zip(group_cols, keys_tuple):
            sub[col] = val
        frames.append(sub.reset_index())

    return pd.concat(frames, ignore_index=True)


def add_calendar_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    df = df.copy()
    dt = df[date_col]
    df["day"] = dt.dt.day
    df["day_of_week"] = dt.dt.dayofweek
    df["week"] = dt.dt.isocalendar().week.astype(int)
    df["month"] = dt.dt.month
    df["quarter"] = dt.dt.quarter
    df["year"] = dt.dt.year
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_month_start"] = dt.dt.is_month_start.astype(int)
    df["is_month_end"] = dt.dt.is_month_end.astype(int)
    return df


def add_lag_and_rolling_features(
    df: pd.DataFrame,
    target_col: str = "units_sold",
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    df = df.sort_values((group_cols or []) + ["date"]).copy()
    grouped = df.groupby(group_cols) if group_cols else None

    def series_for(col: str) -> pd.Series:
        return grouped[col] if grouped is not None else df[col]

    for lag in LAGS:
        df[f"lag_{lag}"] = series_for(target_col).shift(lag) if grouped is None else grouped[target_col].shift(lag)

    for window in ROLLING_WINDOWS:
        shifted = grouped[target_col].shift(1) if grouped is not None else df[target_col].shift(1)
        if grouped is not None:
            df[f"rolling_mean_{window}"] = shifted.groupby(df[group_cols[0]] if len(group_cols) == 1 else [df[c] for c in group_cols]).transform(
                lambda s: s.rolling(window, min_periods=max(2, window // 2)).mean()
            )
            df[f"rolling_std_{window}"] = shifted.groupby(df[group_cols[0]] if len(group_cols) == 1 else [df[c] for c in group_cols]).transform(
                lambda s: s.rolling(window, min_periods=max(2, window // 2)).std()
            )
        else:
            df[f"rolling_mean_{window}"] = shifted.rolling(window, min_periods=max(2, window // 2)).mean()
            df[f"rolling_std_{window}"] = shifted.rolling(window, min_periods=max(2, window // 2)).std()

    # Recent growth rate: percentage change vs 7 days prior (using lagged values only).
    df["growth_rate_7"] = (df["lag_1"] - df["lag_7"]) / df["lag_7"].replace(0, np.nan)
    df["growth_rate_7"] = df["growth_rate_7"].fillna(0.0)

    df["rolling_std_7"] = df["rolling_std_7"].fillna(0.0)
    df["rolling_std_14"] = df.get("rolling_std_14", pd.Series(0, index=df.index)).fillna(0.0)
    df["rolling_std_30"] = df.get("rolling_std_30", pd.Series(0, index=df.index)).fillna(0.0)

    return df


EXOGENOUS_COLUMNS = ["discount", "marketing_spend", "peer_avg_units"]


def ensure_feature_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Guarantees every requested column exists (filled with 0.0 if absent).

    Used for the exogenous columns (discount, marketing_spend, peer_avg_units),
    which are only present when the source dataset supplies them / when a
    peer-group benchmark was computed upstream — the model should still run
    without them rather than raise a KeyError.
    """
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = df[col].fillna(0.0)
    return df


def compute_peer_average_series(
    transactions: pd.DataFrame,
    scope_col: str | None = None,
    scope_value: str | None = None,
    target_col: str = "units_sold",
) -> pd.Series:
    """Average per-product daily demand across the relevant peer group —
    the "product/category/region aggregate" feature called for by the
    assignment spec (§7.3).

    - Product-level scope (`scope_col="product_id"`): peer group is every
      product in the same *category*, so the model can see "is this product
      moving with or against its category?".
    - Region-level scope (`scope_col="region"`): peer group is every product
      sold in that region.
    - No scope (global/company-wide series): peer group is the whole
      dataset, giving "average demand per active product" as a normalizing
      business-context signal.

    Returns a Series indexed by date, already shifted back one day (i.e.
    the value attached to date *t* is the peer group's average as of
    *t-1*). This is deliberate: the same-day peer total is just as unknown
    at forecast time as the target itself (nobody knows today's
    company-wide sales before the day is over), so using it un-lagged would
    let the model learn a near-perfect same-day proxy for its own target
    during training that is unavailable — and therefore useless, or worse,
    actively misleading — when actually forecasting the future.
    """
    if "date" not in transactions.columns or target_col not in transactions.columns:
        return pd.Series(dtype=float, name="peer_avg_units")

    df = transactions.copy()

    peer_group = df
    if scope_col == "product_id" and scope_value and "category" in df.columns and "product_id" in df.columns:
        matching = df.loc[df["product_id"] == scope_value, "category"]
        if not matching.empty:
            peer_group = df.loc[df["category"] == matching.iloc[0]]
    elif scope_col == "region" and scope_value and "region" in df.columns:
        peer_group = df.loc[df["region"] == scope_value]

    daily_totals = peer_group.groupby("date")[target_col].sum()
    if "product_id" in peer_group.columns:
        daily_product_counts = peer_group.groupby("date")["product_id"].nunique().replace(0, np.nan)
        peer_avg = (daily_totals / daily_product_counts).fillna(0.0)
    else:
        peer_avg = daily_totals.fillna(0.0)

    if len(peer_avg) > 0:
        full_range = pd.date_range(peer_avg.index.min(), peer_avg.index.max(), freq="D")
        peer_avg = peer_avg.reindex(full_range).ffill().fillna(0.0)

    peer_avg = peer_avg.shift(1).fillna(0.0)
    peer_avg.name = "peer_avg_units"
    return peer_avg


def attach_exogenous_features(daily_df: pd.DataFrame, peer_avg: pd.Series | None = None) -> pd.DataFrame:
    """Merges discount/marketing_spend (already aggregated onto `daily_df`
    by `aggregate_daily_series`, when the source dataset has them) and the
    peer-group benchmark onto the daily series, filling gaps with 0.
    """
    df = daily_df.copy()
    if peer_avg is not None:
        df = df.merge(peer_avg.rename("peer_avg_units"), left_on="date", right_index=True, how="left")
    return ensure_feature_columns(df, EXOGENOUS_COLUMNS)


def build_feature_matrix(
    daily_df: pd.DataFrame,
    target_col: str = "units_sold",
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Full feature-engineering pipeline: calendar + lag/rolling + growth + exogenous."""
    df = attach_exogenous_features(daily_df)
    df = add_calendar_features(df)
    df = add_lag_and_rolling_features(df, target_col=target_col, group_cols=group_cols)
    return df


FEATURE_COLUMNS = (
    ["day", "day_of_week", "week", "month", "quarter", "year", "is_weekend", "is_month_start", "is_month_end"]
    + [f"lag_{lag}" for lag in LAGS]
    + [f"rolling_mean_{w}" for w in ROLLING_WINDOWS]
    + [f"rolling_std_{w}" for w in ROLLING_WINDOWS]
    + ["growth_rate_7"]
    + EXOGENOUS_COLUMNS
)
