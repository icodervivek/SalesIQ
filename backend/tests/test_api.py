import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.config import DATASETS_DIR
from app.database import SessionLocal, init_db
from app.main import app
from app.models.db_models import Dataset

init_db()  # ensure tables exist for the module-scoped TestClient below
client = TestClient(app)


def _sample_csv_bytes(days: int = 90) -> bytes:
    dates = pd.date_range("2024-01-01", periods=days, freq="D")
    rng = np.random.default_rng(1)
    df = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "product_id": "P001",
            "product_name": "Laptop Pro",
            "category": "Electronics",
            "region": "North",
            "units_sold": rng.integers(5, 25, size=days),
            "unit_price": 60000.0,
            "discount": 0,
            "marketing_spend": 0,
            "revenue": rng.integers(5, 25, size=days) * 60000.0,
        }
    )
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.read()


@pytest.fixture(scope="module")
def uploaded_dataset_id():
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sample.csv", _sample_csv_bytes(), "text/csv")},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_rejects_non_csv():
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("sample.txt", b"not a csv", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_and_list_datasets(uploaded_dataset_id):
    response = client.get("/api/datasets")
    assert response.status_code == 200
    ids = [d["id"] for d in response.json()]
    assert uploaded_dataset_id in ids


def test_reuploading_identical_dataset_does_not_create_duplicate(uploaded_dataset_id):
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("same-data.csv", _sample_csv_bytes(), "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["id"] == uploaded_dataset_id


def test_existing_identical_datasets_are_grouped_and_deleted():
    upload_response = client.post(
        "/api/datasets/upload",
        files={"file": ("original.csv", _sample_csv_bytes(days=94), "text/csv")},
    )
    assert upload_response.status_code == 200, upload_response.text
    dataset_id = upload_response.json()["id"]

    with SessionLocal() as db:
        original = db.get(Dataset, dataset_id)
        assert original is not None
        duplicate_path = DATASETS_DIR / "legacy_duplicate.csv"
        duplicate_path.write_bytes(Path(original.storage_path).read_bytes())
        duplicate = Dataset(
            filename="duplicate.csv",
            storage_path=str(duplicate_path),
            row_count=original.row_count,
            cleaned_row_count=original.cleaned_row_count,
            validation_report=original.validation_report,
            cleaning_summary=original.cleaning_summary,
        )
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)
        duplicate_id = duplicate.id

    listed = client.get("/api/datasets")
    assert listed.status_code == 200
    matching = [row for row in listed.json() if row["id"] in (dataset_id, duplicate_id)]
    assert len(matching) == 1
    assert matching[0]["duplicate_count"] == 2

    delete_response = client.delete(f"/api/datasets/{matching[0]['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/datasets/{dataset_id}").status_code == 404
    assert client.get(f"/api/datasets/{duplicate_id}").status_code == 404


def test_delete_dataset_removes_it():
    upload_response = client.post(
        "/api/datasets/upload",
        files={"file": ("to-delete.csv", _sample_csv_bytes(days=92), "text/csv")},
    )
    assert upload_response.status_code == 200, upload_response.text
    dataset_id = upload_response.json()["id"]

    response = client.delete(f"/api/datasets/{dataset_id}")
    assert response.status_code == 204

    missing_dataset = client.get(f"/api/datasets/{dataset_id}")
    assert missing_dataset.status_code == 404


def test_analytics_summary(uploaded_dataset_id):
    response = client.get(f"/api/analytics/summary?dataset_id={uploaded_dataset_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["total_units_sold"] > 0
    assert body["total_revenue"] > 0


def test_train_and_forecast_flow(uploaded_dataset_id):
    train_response = client.post("/api/models/train", json={"dataset_id": uploaded_dataset_id, "test_size": 14})
    assert train_response.status_code == 200, train_response.text
    train_body = train_response.json()
    assert len(train_body["results"]) >= 2
    assert train_body["best_model"]

    forecast_response = client.post(
        "/api/forecast",
        json={"dataset_id": uploaded_dataset_id, "model_name": train_body["best_model"], "horizon": 7},
    )
    assert forecast_response.status_code == 200, forecast_response.text
    forecast_body = forecast_response.json()
    assert len(forecast_body["forecast"]) == 7
    assert len(forecast_body["dates"]) == 7

    export_response = client.get(f"/api/forecast/{forecast_body['id']}/export")
    assert export_response.status_code == 200
    assert "date,forecast" in export_response.text
