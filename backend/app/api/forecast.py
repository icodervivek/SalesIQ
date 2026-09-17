from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset, ForecastRun
from app.models.schemas import ForecastRequest
from app.services import forecast_service
from app.services.dataset_service import load_cleaned_dataframe

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.post("")
def create_forecast(payload: ForecastRequest, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, payload.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    df = load_cleaned_dataframe(dataset)
    try:
        run = forecast_service.generate_forecast(
            db,
            dataset,
            df,
            payload.model_name,
            payload.horizon,
            payload.training_run_id,
            product_id=payload.product_id,
            region=payload.region,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return forecast_service.forecast_run_to_dict(run)


@router.get("/history")
def forecast_history(dataset_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(ForecastRun).order_by(ForecastRun.created_at.desc()).limit(50)
    if dataset_id:
        stmt = stmt.where(ForecastRun.dataset_id == dataset_id)
    runs = db.execute(stmt).scalars().all()
    return [forecast_service.forecast_run_to_dict(r) for r in runs]


@router.get("/{forecast_id}/export")
def export_forecast_csv(forecast_id: int, db: Session = Depends(get_db)):
    run = db.get(ForecastRun, forecast_id)
    if not run:
        raise HTTPException(status_code=404, detail="Forecast not found.")
    data = forecast_service.forecast_run_to_dict(run)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "forecast", "lower_bound", "upper_bound"])
    for i, date in enumerate(data["dates"]):
        writer.writerow([date, data["forecast"][i], data["lower_bound"][i], data["upper_bound"][i]])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=forecast_{forecast_id}.csv"},
    )
