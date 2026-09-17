import numpy as np
import pandas as pd

from ml.features.feature_engineering import (
    EXOGENOUS_COLUMNS,
    FEATURE_COLUMNS,
    aggregate_daily_series,
    build_feature_matrix,
    compute_peer_average_series,
    ensure_feature_columns,
)


def _sample_transactions() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "date": dates,
            "product_id": "P1",
            "units_sold": rng.integers(5, 20, size=60),
            "revenue": rng.uniform(500, 2000, size=60),
        }
    )


def _multi_product_transactions() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    rng = np.random.default_rng(1)
    frames = []
    for product_id, category in [("P1", "Electronics"), ("P2", "Electronics"), ("P3", "Furniture")]:
        frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "product_id": product_id,
                    "category": category,
                    "units_sold": rng.integers(5, 20, size=30),
                    "revenue": rng.uniform(500, 2000, size=30),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def test_aggregate_daily_series_fills_gaps():
    df = _sample_transactions()
    df = df.drop(df.index[5])  # remove one day to create a gap
    daily = aggregate_daily_series(df)
    expected_days = (df["date"].max() - df["date"].min()).days + 1
    assert len(daily) == expected_days
    assert daily["units_sold"].isna().sum() == 0


def test_lag_features_only_use_past_values():
    daily = aggregate_daily_series(_sample_transactions())
    features = build_feature_matrix(daily)
    # lag_1 at row i must equal units_sold at row i-1
    for i in range(2, 10):
        assert features.loc[i, "lag_1"] == daily.loc[i - 1, "units_sold"]


def test_feature_matrix_has_expected_columns():
    daily = aggregate_daily_series(_sample_transactions())
    features = build_feature_matrix(daily)
    for col in FEATURE_COLUMNS:
        assert col in features.columns


def test_no_leakage_first_row_has_nan_lags():
    daily = aggregate_daily_series(_sample_transactions())
    features = build_feature_matrix(daily)
    assert pd.isna(features.loc[0, "lag_1"])


def test_ensure_feature_columns_fills_missing_with_zero():
    df = pd.DataFrame({"a": [1, 2, 3]})
    out = ensure_feature_columns(df, ["a", "discount", "marketing_spend"])
    assert (out["discount"] == 0.0).all()
    assert (out["marketing_spend"] == 0.0).all()
    assert list(out["a"]) == [1, 2, 3]


def test_peer_average_scoped_to_category_excludes_other_categories():
    transactions = _multi_product_transactions()
    peer_avg = compute_peer_average_series(transactions, scope_col="product_id", scope_value="P1")
    # Peer group for P1 is category "Electronics" (P1 + P2), not P3 (Furniture).
    electronics_only = transactions[transactions["category"] == "Electronics"]
    same_day = electronics_only.groupby("date")["units_sold"].sum() / 2
    # The series is shifted back one day (yesterday's peer average, not
    # today's) so it is causally valid as a forecasting input — see
    # compute_peer_average_series's docstring.
    expected = same_day.shift(1).fillna(0.0)
    pd.testing.assert_series_equal(peer_avg.sort_index(), expected.sort_index(), check_names=False, check_freq=False)


def test_peer_average_is_lagged_not_same_day():
    transactions = _multi_product_transactions()
    peer_avg = compute_peer_average_series(transactions, scope_col=None, scope_value=None)
    same_day_totals = transactions.groupby("date")["units_sold"].sum() / 3

    # First day has no prior day to reference, so it's filled with 0 rather
    # than leaking the same day's own total.
    assert peer_avg.iloc[0] == 0.0
    # The second day's peer average should equal the *first* day's same-day
    # total (i.e. genuinely lagged by one day), not the second day's own.
    assert round(peer_avg.iloc[1], 6) == round(same_day_totals.iloc[0], 6)


def test_build_feature_matrix_includes_exogenous_columns_even_when_absent():
    daily = aggregate_daily_series(_sample_transactions())
    assert "discount" not in daily.columns  # source data has no discount column
    features = build_feature_matrix(daily)
    for col in EXOGENOUS_COLUMNS:
        assert col in features.columns
        assert (features[col] == 0.0).all()
