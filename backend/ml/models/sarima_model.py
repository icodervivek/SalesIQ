"""SARIMA forecaster (statsmodels) with weekly seasonality.

Kept intentionally simple (fixed order, grid-free) rather than an
auto-ARIMA search, to keep training time predictable for an internship
scope. Order was chosen empirically on the sample dataset: (1,1,1) for
the non-seasonal part, (1,1,1,7) for the weekly seasonal part.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd


class SarimaForecaster:
    name = "SARIMA"

    def __init__(self, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7)):
        self.order = order
        self.seasonal_order = seasonal_order
        self._result = None

    def fit(self, y: pd.Series) -> "SarimaForecaster":
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = SARIMAX(
                y.values,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            self._result = model.fit(disp=False)
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if self._result is None:
            raise ValueError("Model must be fit before predicting.")
        forecast = self._result.get_forecast(steps=horizon)
        mean = np.asarray(forecast.predicted_mean)
        return np.clip(mean, a_min=0, a_max=None)

    def predict_with_interval(self, horizon: int, alpha: float = 0.2) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (mean, lower, upper) for a (1-alpha) confidence interval."""
        if self._result is None:
            raise ValueError("Model must be fit before predicting.")
        forecast = self._result.get_forecast(steps=horizon)
        mean = np.clip(np.asarray(forecast.predicted_mean), a_min=0, a_max=None)
        ci = np.asarray(forecast.conf_int(alpha=alpha))
        lower = np.clip(ci[:, 0], a_min=0, a_max=None)
        upper = np.clip(ci[:, 1], a_min=0, a_max=None)
        return mean, lower, upper

    @staticmethod
    def is_available() -> bool:
        try:
            import statsmodels  # noqa: F401

            return True
        except ImportError:
            return False
