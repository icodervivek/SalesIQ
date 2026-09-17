import io

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app

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
