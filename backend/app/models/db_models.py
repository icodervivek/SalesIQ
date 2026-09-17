from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    cleaned_row_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_report: Mapped[str] = mapped_column(Text, default="{}")
    cleaning_summary: Mapped[str] = mapped_column(Text, default="{}")

    training_runs: Mapped[list["TrainingRun"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    forecasts: Mapped[list["ForecastRun"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    group_by: Mapped[str] = mapped_column(String(100), default="")
    best_model: Mapped[str] = mapped_column(String(200), default="")
    results_json: Mapped[str] = mapped_column(Text, default="[]")
    anomalies_json: Mapped[str] = mapped_column(Text, default="[]")
    series_length: Mapped[int] = mapped_column(Integer, default=0)
    test_size: Mapped[int] = mapped_column(Integer, default=0)

    dataset: Mapped["Dataset"] = relationship(back_populates="training_runs")


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    training_run_id: Mapped[int | None] = mapped_column(ForeignKey("training_runs.id"), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    model_name: Mapped[str] = mapped_column(String(200))
    horizon: Mapped[int] = mapped_column(Integer)
    result_json: Mapped[str] = mapped_column(Text, default="{}")

    dataset: Mapped["Dataset"] = relationship(back_populates="forecasts")
