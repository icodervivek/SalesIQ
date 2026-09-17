from __future__ import annotations

import json

import pandas as pd
from sqlalchemy.orm import Session

from app.models.db_models import Dataset, TrainingRun
from ml.forecasting.pipeline import run_training_and_evaluation


def train_models(
    db: Session,
    dataset: Dataset,
    df: pd.DataFrame,
    scope_label: str,
    test_size: int,
    full_df: pd.DataFrame | None = None,
    scope_col: str | None = None,
    scope_value: str | None = None,
) -> TrainingRun:
    report, _daily = run_training_and_evaluation(
        df, test_size=test_size, full_transactions=full_df, scope_col=scope_col, scope_value=scope_value
    )

    run = TrainingRun(
        dataset_id=dataset.id,
        group_by=scope_label,
        best_model=report.best_model,
        results_json=json.dumps([r.__dict__ for r in report.results]),
        anomalies_json=json.dumps(report.anomalies),
        series_length=report.series_length,
        test_size=report.test_size,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def training_run_to_dict(run: TrainingRun) -> dict:
    return {
        "id": run.id,
        "dataset_id": run.dataset_id,
        "created_at": run.created_at,
        "group_by": run.group_by,
        "best_model": run.best_model,
        "series_length": run.series_length,
        "test_size": run.test_size,
        "results": json.loads(run.results_json),
        "anomalies": json.loads(run.anomalies_json),
    }
