from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DATASETS_DIR
from app.models.db_models import Dataset
from ml.preprocessing.cleaning import clean_sales_data
from ml.preprocessing.validation import validate_dataset


class DatasetIngestionError(Exception):
    pass


def _cleaned_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, lineterminator="\n").encode("utf-8")


def _dataset_fingerprint(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ingest_csv(db: Session, filename: str, raw_bytes: bytes) -> Dataset:
    try:
        raw_df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise DatasetIngestionError(f"Could not parse CSV: {exc}") from exc

    if raw_df.empty:
        raise DatasetIngestionError("Uploaded file contains no rows.")

    report = validate_dataset(raw_df)
    if not report.is_valid:
        raise DatasetIngestionError("; ".join(report.warnings) or "Dataset failed validation.")

    cleaned_df, cleaning_summary = clean_sales_data(raw_df)
    if cleaned_df.empty:
        raise DatasetIngestionError("All rows were removed during cleaning; please check the source file.")

    cleaned_bytes = _cleaned_csv_bytes(cleaned_df)
    fingerprint = hashlib.sha256(cleaned_bytes).hexdigest()
    validation_json = json.dumps(report.to_dict())
    cleaning_json = json.dumps(cleaning_summary.to_dict())
    existing_datasets = db.execute(
        select(Dataset).order_by(Dataset.uploaded_at.desc())
    ).scalars().all()
    for existing in existing_datasets:
        try:
            if (
                _dataset_fingerprint(existing.storage_path) == fingerprint
                and existing.validation_report == validation_json
                and existing.cleaning_summary == cleaning_json
            ):
                return existing
        except FileNotFoundError:
            continue

    dataset = Dataset(
        filename=filename,
        storage_path="",
        row_count=report.row_count,
        cleaned_row_count=len(cleaned_df),
        validation_report=validation_json,
        cleaning_summary=cleaning_json,
    )
    db.add(dataset)
    db.flush()  # assigns dataset.id

    storage_path = DATASETS_DIR / f"dataset_{dataset.id}_clean.csv"
    storage_path.write_bytes(cleaned_bytes)
    dataset.storage_path = str(storage_path)

    db.commit()
    db.refresh(dataset)
    return dataset


def list_unique_datasets(db: Session) -> list[tuple[Dataset, int]]:
    datasets = db.execute(
        select(Dataset).order_by(Dataset.uploaded_at.desc())
    ).scalars().all()
    grouped: dict[str, tuple[Dataset, int]] = {}

    for dataset in datasets:
        try:
            fingerprint = _dataset_fingerprint(dataset.storage_path)
        except FileNotFoundError:
            fingerprint = f"missing:{dataset.id}"

        if fingerprint in grouped:
            canonical, count = grouped[fingerprint]
            grouped[fingerprint] = (canonical, count + 1)
        else:
            grouped[fingerprint] = (dataset, 1)

    return list(grouped.values())


def delete_dataset_group(db: Session, dataset: Dataset) -> list[str]:
    try:
        fingerprint = _dataset_fingerprint(dataset.storage_path)
    except FileNotFoundError:
        fingerprint = f"missing:{dataset.id}"

    datasets = db.execute(select(Dataset)).scalars().all()
    matching = []
    for candidate in datasets:
        try:
            if _dataset_fingerprint(candidate.storage_path) == fingerprint:
                matching.append(candidate)
        except FileNotFoundError:
            if candidate.id == dataset.id:
                matching.append(candidate)

    storage_paths = list({candidate.storage_path for candidate in matching})
    for candidate in matching:
        db.delete(candidate)
    db.commit()

    return storage_paths


def load_cleaned_dataframe(dataset: Dataset) -> pd.DataFrame:
    df = pd.read_csv(dataset.storage_path)
    df["date"] = pd.to_datetime(df["date"])
    return df
