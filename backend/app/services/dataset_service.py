from __future__ import annotations

import io
import json

import pandas as pd
from sqlalchemy.orm import Session

from app.config import DATASETS_DIR
from app.models.db_models import Dataset
from ml.preprocessing.cleaning import clean_sales_data
from ml.preprocessing.validation import validate_dataset


class DatasetIngestionError(Exception):
    pass


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

    dataset = Dataset(
        filename=filename,
        storage_path="",
        row_count=report.row_count,
        cleaned_row_count=len(cleaned_df),
        validation_report=json.dumps(report.to_dict()),
        cleaning_summary=json.dumps(cleaning_summary.to_dict()),
    )
    db.add(dataset)
    db.flush()  # assigns dataset.id

    storage_path = DATASETS_DIR / f"dataset_{dataset.id}_clean.csv"
    cleaned_df.to_csv(storage_path, index=False)
    dataset.storage_path = str(storage_path)

    db.commit()
    db.refresh(dataset)
    return dataset


def load_cleaned_dataframe(dataset: Dataset) -> pd.DataFrame:
    df = pd.read_csv(dataset.storage_path)
    df["date"] = pd.to_datetime(df["date"])
    return df
