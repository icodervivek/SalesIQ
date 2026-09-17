"""Baseline forecasters: seasonal-naive and moving-average.

These exist to give every "smarter" model a bar to clear. A model that
cannot beat a 7-day seasonal-naive baseline is not adding value, no matter
how sophisticated it is.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class SeasonalNaiveForecaster:
    """Forecasts day t as the value observed 7 days earlier (weekly seasonality)."""

    name = "Baseline (Seasonal Naive)"

    def __init__(self, season_length: int = 7):
        self.season_length = season_length
        self._history: pd.Series | None = None

    def fit(self, y: pd.Series) -> "SeasonalNaiveForecaster":
        self._history = y.copy()
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if self._history is None or len(self._history) < self.season_length:
            raise ValueError("Not enough history to seasonal-naive forecast.")
        tail = self._history.values[-self.season_length:]
        reps = int(np.ceil(horizon / self.season_length))
        return np.tile(tail, reps)[:horizon]


class MovingAverageForecaster:
    """Forecasts every future day as the trailing N-day average."""

    name = "Baseline (Moving Average)"

    def __init__(self, window: int = 7):
        self.window = window
        self._history: pd.Series | None = None

    def fit(self, y: pd.Series) -> "MovingAverageForecaster":
        self._history = y.copy()
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if self._history is None or len(self._history) < self.window:
            raise ValueError("Not enough history to compute moving average.")
        avg = float(self._history.values[-self.window:].mean())
        return np.full(horizon, avg)
