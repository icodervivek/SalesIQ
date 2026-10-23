import numpy as np
import pandas as pd

from ml.features.feature_engineering import aggregate_daily_series, compute_peer_average_series
from ml.forecasting import pipeline
from ml.models.xgboost_model import XGBoostForecaster


def _daily_with_exogenous(days: int = 90) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=days, freq="D")
    rng = np.random.default_rng(3)
    transactions = pd.DataFrame(
        {
            "date": dates,
            "product_id": "P1",
            "units_sold": rng.integers(10, 30, size=days),
            "revenue": rng.uniform(1000, 3000, size=days),
            "discount": rng.choice([0, 5, 10], size=days),
            "marketing_spend": rng.uniform(0, 500, size=days),
        }
    )
    return aggregate_daily_series(transactions)


def test_xgboost_forecaster_trains_and_predicts_with_exogenous_features():
    daily = _daily_with_exogenous()
    peer_avg = compute_peer_average_series(daily.assign(product_id="P1"), scope_col=None, scope_value=None)

    model = XGBoostForecaster().fit(daily, peer_avg=peer_avg)
    predictions = model.predict(horizon=10)

    assert len(predictions) == 10
    assert (predictions >= 0).all()
    assert np.isfinite(predictions).all()


def test_xgboost_forecaster_persists_last_exogenous_values_into_the_future():
    """The recursive forecast loop has no future discount/marketing plan to
    work from, so it persists the last observed value forward. Verify this
    behaviorally: two otherwise-identical series that end on very different
    discount levels should produce different forecasts, proving the
    persisted value actually reaches the model rather than being dropped.
    """
    base = _daily_with_exogenous()

    low_discount = base.copy()
    low_discount.loc[low_discount.index[-1], "discount"] = 0.0
    high_discount = base.copy()
    high_discount.loc[high_discount.index[-1], "discount"] = 80.0

    pred_low = XGBoostForecaster().fit(low_discount).predict(horizon=5)
    pred_high = XGBoostForecaster().fit(high_discount).predict(horizon=5)

    assert not np.allclose(pred_low, pred_high)


def test_training_clips_fit_values_but_validates_against_actual_sales(monkeypatch):
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    transactions = pd.DataFrame(
        {
            "date": dates,
            "product_id": "P1",
            "units_sold": [10] * 53 + [11] * 7,
            "revenue": [100.0] * 53 + [110.0] * 7,
        }
    )
    transactions.loc[30, "units_sold"] = 100
    transactions.loc[30, "revenue"] = 1000

    fit_units = {}

    class FakeBaseline:
        name = "fake baseline"

        def fit(self, values):
            fit_units["baseline"] = values.copy()
            return self

        def predict(self, horizon):
            return np.zeros(horizon)

    class FakeXGBoost:
        name = "fake XGBoost"

        def fit(self, daily, peer_avg=None):
            fit_units["xgboost"] = daily["units_sold"].copy()
            return self

        def predict(self, horizon):
            return np.zeros(horizon)

    monkeypatch.setattr(pipeline, "SeasonalNaiveForecaster", FakeBaseline)
    monkeypatch.setattr(pipeline.SarimaForecaster, "is_available", staticmethod(lambda: False))
    monkeypatch.setattr(pipeline, "XGBoostForecaster", FakeXGBoost)

    report, daily = pipeline.run_training_and_evaluation(transactions, test_size=7)
    actual = report.results[0].actuals

    assert fit_units["baseline"].sum() < transactions.iloc[:-7]["units_sold"].sum()
    assert fit_units["xgboost"].sum() < transactions.iloc[:-7]["units_sold"].sum()
    assert actual == transactions.iloc[-7:]["units_sold"].tolist()
    assert int(daily["units_sold"].sum()) == int(transactions["units_sold"].sum())
