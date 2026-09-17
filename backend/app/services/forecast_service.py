from __future__ import annotations

import json

import pandas as pd
from sqlalchemy.orm import Session

from app.models.db_models import Dataset, ForecastRun
from ml.features.feature_engineering import aggregate_daily_series
from ml.forecasting.pipeline import forecast_future

MAX_HORIZON = 180


def generate_forecast(
    db: Session,
    dataset: Dataset,
    df: pd.DataFrame,
    model_name: str | None,
    horizon: int,
    training_run_id: int | None,
    product_id: str | None = None,
    region: str | None = None,
) -> ForecastRun:
    horizon = max(1, min(horizon, MAX_HORIZON))

    filtered = df
    if product_id:
        filtered = filtered.loc[filtered["product_id"] == product_id]
    if region:
        filtered = filtered.loc[filtered["region"] == region]
    if filtered.empty:
        raise ValueError("No data matches the selected product/region filter.")

    daily = aggregate_daily_series(filtered)
    scope_col = "product_id" if product_id else ("region" if region else None)
    scope_value = product_id or region
    result = forecast_future(daily, model_name or "", horizon, full_transactions=df, scope_col=scope_col, scope_value=scope_value)

    run = ForecastRun(
        dataset_id=dataset.id,
        training_run_id=training_run_id,
        model_name=result["model"],
        horizon=horizon,
        result_json=json.dumps(result),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def forecast_run_to_dict(run: ForecastRun) -> dict:
    result = json.loads(run.result_json)
    return {
        "id": run.id,
        "dataset_id": run.dataset_id,
        "created_at": run.created_at,
        "model_name": run.model_name,
        "horizon": run.horizon,
        "dates": result["dates"],
        "forecast": result["forecast"],
        "lower_bound": result["lower_bound"],
        "upper_bound": result["upper_bound"],
    }
