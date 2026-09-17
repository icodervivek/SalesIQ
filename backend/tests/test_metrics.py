import numpy as np

from ml.evaluation.metrics import evaluate_forecast, mape, mae, rmse, r_squared


def test_perfect_forecast_has_zero_error():
    y_true = np.array([10, 20, 30, 40])
    y_pred = np.array([10, 20, 30, 40])
    assert mae(y_true, y_pred) == 0
    assert rmse(y_true, y_pred) == 0
    assert mape(y_true, y_pred) == 0
    assert r_squared(y_true, y_pred) == 1.0


def test_mape_handles_zero_actuals_without_error():
    y_true = np.array([0, 0, 5])
    y_pred = np.array([1, 2, 5])
    value = mape(y_true, y_pred)
    assert np.isfinite(value)
    assert value >= 0


def test_evaluate_forecast_returns_all_metrics():
    result = evaluate_forecast(np.array([10, 12, 14]), np.array([9, 13, 15]))
    assert set(result.keys()) == {"mae", "rmse", "mape", "r2"}
    assert all(np.isfinite(v) for v in result.values())
