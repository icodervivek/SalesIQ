from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import MAX_UPLOAD_MB
from app.database import get_db
from app.models.db_models import Dataset
from app.models.schemas import DatasetListItem, DatasetOut
from app.services.dataset_service import DatasetIngestionError, ingest_csv

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_MB}MB limit.")

    try:
        dataset = ingest_csv(db, file.filename, raw_bytes)
    except DatasetIngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _dataset_to_out(dataset)


@router.get("", response_model=list[DatasetListItem])
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.execute(select(Dataset).order_by(Dataset.uploaded_at.desc())).scalars().all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return _dataset_to_out(dataset)


def _dataset_to_out(dataset: Dataset) -> dict:
    return {
        "id": dataset.id,
        "filename": dataset.filename,
        "uploaded_at": dataset.uploaded_at,
        "row_count": dataset.row_count,
        "cleaned_row_count": dataset.cleaned_row_count,
        "validation_report": json.loads(dataset.validation_report),
        "cleaning_summary": json.loads(dataset.cleaning_summary),
    }
