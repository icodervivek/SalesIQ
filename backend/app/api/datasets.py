from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.config import DATASETS_DIR, MAX_UPLOAD_MB
from app.database import get_db
from app.models.db_models import Dataset
from app.models.schemas import DatasetListItem, DatasetOut
from app.services.dataset_service import (
    DatasetIngestionError,
    delete_dataset_group,
    ingest_csv,
    list_unique_datasets,
)

router = APIRouter(prefix="/api/datasets", tags=["datasets"])
logger = logging.getLogger(__name__)


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
    return [
        {
            "id": dataset.id,
            "filename": dataset.filename,
            "uploaded_at": dataset.uploaded_at,
            "row_count": dataset.row_count,
            "cleaned_row_count": dataset.cleaned_row_count,
            "duplicate_count": duplicate_count,
        }
        for dataset, duplicate_count in list_unique_datasets(db)
    ]


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    try:
        storage_paths = delete_dataset_group(db, dataset)
    except OSError as exc:
        db.rollback()
        logger.exception("Could not remove dataset %s from the database.", dataset_id)
        raise HTTPException(status_code=500, detail="Could not delete the dataset.") from exc

    datasets_dir = DATASETS_DIR.resolve()
    for storage_path in storage_paths:
        path = Path(storage_path)
        try:
            if path.resolve().parent != datasets_dir:
                logger.error("Refusing to remove dataset file outside storage directory: %s", path)
                continue
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.exception("Dataset %s was removed, but its file could not be deleted.", dataset_id)
            raise HTTPException(
                status_code=500,
                detail="Dataset was removed, but its stored file could not be deleted.",
            ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
