from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class ValidationReportOut(BaseModel):
    is_valid: bool
    row_count: int
    missing_required_columns: list[str]
    missing_recommended_columns: list[str]
    invalid_date_rows: int
    duplicate_rows: int
    missing_value_rows: int
    invalid_numeric_rows: int
    negative_value_rows: int
    warnings: list[str]


class DatasetOut(BaseModel):
    id: int
    filename: str
    uploaded_at: dt.datetime
    row_count: int
    cleaned_row_count: int
    validation_report: ValidationReportOut
    cleaning_summary: dict

    model_config = ConfigDict(from_attributes=True)


class DatasetListItem(BaseModel):
    id: int
    filename: str
    uploaded_at: dt.datetime
    row_count: int
    cleaned_row_count: int

    model_config = ConfigDict(from_attributes=True)


class TrainRequest(BaseModel):
    dataset_id: int
    product_id: str | None = None
    region: str | None = None
    test_size: int = 14


class ModelResultOut(BaseModel):
    name: str
    metrics: dict
    predictions: list[float]
    actuals: list[float]
    dates: list[str]


class TrainingRunOut(BaseModel):
    id: int
    dataset_id: int
    created_at: dt.datetime
    group_by: str
    best_model: str
    series_length: int
    test_size: int
    results: list[ModelResultOut]
    anomalies: list[dict]

    model_config = ConfigDict(from_attributes=True)


class ForecastRequest(BaseModel):
    dataset_id: int
    training_run_id: int | None = None
    model_name: str | None = None
    horizon: int = 30
    product_id: str | None = None
    region: str | None = None


class ForecastOut(BaseModel):
    id: int
    dataset_id: int
    created_at: dt.datetime
    model_name: str
    horizon: int
    dates: list[str]
    forecast: list[float]
    lower_bound: list[float]
    upper_bound: list[float]

    model_config = ConfigDict(from_attributes=True)
