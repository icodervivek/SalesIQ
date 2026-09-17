from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset, TrainingRun
from app.models.schemas import TrainRequest
from app.services import training_service
from app.services.dataset_service import load_cleaned_dataframe

router = APIRouter(prefix="/api/models", tags=["models"])


@router.post("/train")
def train_models(payload: TrainRequest, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, payload.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    full_df = load_cleaned_dataframe(dataset)
    df = full_df
    if payload.product_id:
        df = df.loc[df["product_id"] == payload.product_id]
    if payload.region and "region" in df.columns:
        df = df.loc[df["region"] == payload.region]
    if df.empty:
        raise HTTPException(status_code=404, detail="No data matches the selected product/region filter.")

    scope_label = ", ".join(
        filter(None, [f"product:{payload.product_id}" if payload.product_id else None, f"region:{payload.region}" if payload.region else None])
    ) or "overall"
    scope_col = "product_id" if payload.product_id else ("region" if payload.region else None)
    scope_value = payload.product_id or payload.region

    try:
        run = training_service.train_models(db, dataset, df, scope_label, payload.test_size, full_df, scope_col, scope_value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return training_service.training_run_to_dict(run)


@router.get("")
def list_training_runs(dataset_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(TrainingRun).order_by(TrainingRun.created_at.desc())
    if dataset_id:
        stmt = stmt.where(TrainingRun.dataset_id == dataset_id)
    runs = db.execute(stmt).scalars().all()
    return [training_service.training_run_to_dict(r) for r in runs]


@router.get("/{run_id}")
def get_training_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(TrainingRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found.")
    return training_service.training_run_to_dict(run)
