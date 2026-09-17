"""End-to-end training, validation, and forecasting orchestration.

Validation strategy: chronological holdout. The last `test_size` days of
the series are held out as a test set; models are fit only on the data
before that cutoff, so no future information leaks into training. This is
the minimum bar for time-series validation described in the assignment
spec (section 7.4) — a rolling/expanding-window backtest is noted as a
natural extension in the README/limitations section.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ml.evaluation.metrics import evaluate_forecast
from ml.features.feature_engineering import aggregate_daily_series, compute_peer_average_series
from ml.models.baseline import SeasonalNaiveForecaster
from ml.models.sarima_model import SarimaForecaster
from ml.models.xgboost_model import XGBoostForecaster


@dataclass
class ModelResult:
    name: str
    metrics: dict
    predictions: list[float]
    actuals: list[float]
    dates: list[str]


@dataclass
class TrainingReport:
    series_length: int
    test_size: int
    results: list[ModelResult] = field(default_factory=list)
    best_model: str = ""
    anomalies: list[dict] = field(default_factory=list)


MIN_HISTORY_DAYS = 45


def detect_anomalies(daily: pd.DataFrame, target_col: str = "units_sold", z_threshold: float = 3.0) -> list[dict]:
    """Flags days whose value deviates more than `z_threshold` rolling
    standard deviations from a 14-day rolling mean — a simple, explainable
    anomaly signal appropriate for a business dashboard.
    """
    s = daily[target_col]
    rolling_mean = s.rolling(14, min_periods=7).mean()
    rolling_std = s.rolling(14, min_periods=7).std().replace(0, np.nan)
    z = (s - rolling_mean) / rolling_std
    flagged = daily.loc[z.abs() > z_threshold]
    return [
        {"date": row["date"].strftime("%Y-%m-%d"), "value": float(row[target_col]), "z_score": round(float(z.loc[idx]), 2)}
        for idx, row in flagged.iterrows()
    ]


def run_training_and_evaluation(
    transactions: pd.DataFrame,
    test_size: int = 14,
    full_transactions: pd.DataFrame | None = None,
    scope_col: str | None = None,
    scope_value: str | None = None,
) -> tuple[TrainingReport, pd.DataFrame]:
    """Aggregates transactions into a daily series, trains baseline +
    SARIMA + XGBoost, evaluates all three on a chronological holdout, and
    returns a comparison report plus the aggregated daily series (reused
    later for the final forecast).

    Callers wanting product- or region-level forecasting should filter
    `transactions` to that product/region *before* calling this function
    (see app.services.training_service) — the resulting single series is
    then a clean per-segment demand signal rather than a re-aggregated mix.

    `full_transactions` (the unfiltered dataset) plus `scope_col`/`scope_value`
    are optional and, when given, are used to compute the product/category/
    region peer-average benchmark feature the XGBoost model uses (see
    `ml.features.feature_engineering.compute_peer_average_series`).
    """
    daily = aggregate_daily_series(transactions).sort_values("date").reset_index(drop=True)

    if len(daily) < MIN_HISTORY_DAYS:
        raise ValueError(f"At least {MIN_HISTORY_DAYS} days of history are required to train and validate models (found {len(daily)}).")

    peer_avg = compute_peer_average_series(full_transactions if full_transactions is not None else transactions, scope_col, scope_value)

    test_size = min(test_size, max(7, len(daily) // 5))
    train_daily = daily.iloc[:-test_size]
    test_daily = daily.iloc[-test_size:]

    y_train = train_daily.set_index("date")["units_sold"]
    y_test = test_daily["units_sold"].values
    test_dates = test_daily["date"].dt.strftime("%Y-%m-%d").tolist()

    report = TrainingReport(series_length=len(daily), test_size=test_size)

    # --- Baseline ---
    baseline = SeasonalNaiveForecaster().fit(y_train)
    baseline_pred = baseline.predict(test_size)
    report.results.append(
        ModelResult(
            name=baseline.name,
            metrics=evaluate_forecast(y_test, baseline_pred),
            predictions=baseline_pred.tolist(),
            actuals=y_test.tolist(),
            dates=test_dates,
        )
    )

    # --- SARIMA (optional dependency) ---
    if SarimaForecaster.is_available():
        try:
            sarima = SarimaForecaster().fit(y_train)
            sarima_pred = sarima.predict(test_size)
            report.results.append(
                ModelResult(
                    name=sarima.name,
                    metrics=evaluate_forecast(y_test, sarima_pred),
                    predictions=sarima_pred.tolist(),
                    actuals=y_test.tolist(),
                    dates=test_dates,
                )
            )
        except Exception as exc:  # SARIMA can fail to converge on short/odd series
            report.results.append(
                ModelResult(name=f"{SarimaForecaster.name} (failed: {exc})", metrics={}, predictions=[], actuals=[], dates=[])
            )

    # --- XGBoost ---
    xgb = XGBoostForecaster().fit(train_daily, peer_avg=peer_avg)
    xgb_pred = xgb.predict(test_size)
    report.results.append(
        ModelResult(
            name=xgb.name,
            metrics=evaluate_forecast(y_test, xgb_pred),
            predictions=xgb_pred.tolist(),
            actuals=y_test.tolist(),
            dates=test_dates,
        )
    )

    valid_results = [r for r in report.results if r.metrics]
    report.best_model = min(valid_results, key=lambda r: r.metrics["rmse"]).name if valid_results else ""
    report.anomalies = detect_anomalies(daily)

    return report, daily


def forecast_future(
    daily: pd.DataFrame,
    model_name: str,
    horizon: int,
    full_transactions: pd.DataFrame | None = None,
    scope_col: str | None = None,
    scope_value: str | None = None,
) -> dict:
    """Refits the chosen model on the FULL daily series and forecasts
    `horizon` days beyond the last observed date. Returns point forecasts
    and, where supported, a prediction interval.
    """
    y_full = daily.set_index("date")["units_sold"]
    last_date = daily["date"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")
    future_date_strs = [d.strftime("%Y-%m-%d") for d in future_dates]

    if model_name.startswith("SARIMA"):
        model = SarimaForecaster().fit(y_full)
        mean, lower, upper = model.predict_with_interval(horizon)
        return {
            "model": model.name,
            "dates": future_date_strs,
            "forecast": mean.tolist(),
            "lower_bound": lower.tolist(),
            "upper_bound": upper.tolist(),
        }

    if model_name.startswith("XGBoost"):
        peer_avg = compute_peer_average_series(full_transactions if full_transactions is not None else daily, scope_col, scope_value)
        model = XGBoostForecaster().fit(daily, peer_avg=peer_avg)
        pred = model.predict(horizon)
        # Empirical interval derived from residual std of in-sample fit as a
        # lightweight uncertainty proxy (documented as an approximation).
        residual_std = float(np.std(y_full.diff().dropna())) if len(y_full) > 1 else 0.0
        spread = residual_std * np.sqrt(np.arange(1, horizon + 1))
        return {
            "model": model.name,
            "dates": future_date_strs,
            "forecast": pred.tolist(),
            "lower_bound": np.clip(pred - spread, 0, None).tolist(),
            "upper_bound": (pred + spread).tolist(),
        }

    # Default / fallback: seasonal-naive baseline.
    model = SeasonalNaiveForecaster().fit(y_full)
    pred = model.predict(horizon)
    return {
        "model": model.name,
        "dates": future_date_strs,
        "forecast": pred.tolist(),
        "lower_bound": (pred * 0.85).tolist(),
        "upper_bound": (pred * 1.15).tolist(),
    }
