"""Tree-based (XGBoost) forecaster using lag + calendar features.

Multi-step forecasts are produced recursively: predict t+1, append it to
the history, recompute lag/rolling features, predict t+2, and so on. This
is the standard approach for turning a single-step regressor into a
multi-horizon forecaster without training a separate model per horizon.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ml.features.feature_engineering import (
    EXOGENOUS_COLUMNS,
    FEATURE_COLUMNS,
    add_calendar_features,
    add_lag_and_rolling_features,
    attach_exogenous_features,
)


class XGBoostForecaster:
    name = "XGBoost (Lag + Calendar Features)"

    def __init__(self, **xgb_params):
        self.params = {
            "n_estimators": 300,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "random_state": 42,
            "objective": "reg:squarederror",
            **xgb_params,
        }
        self._model = None
        self._history: pd.DataFrame | None = None
        self._target_col = "units_sold"

    def fit(self, daily_df: pd.DataFrame, target_col: str = "units_sold", peer_avg: pd.Series | None = None) -> "XGBoostForecaster":
        from xgboost import XGBRegressor

        self._target_col = target_col
        df = attach_exogenous_features(daily_df, peer_avg=peer_avg)
        df = add_calendar_features(df)
        df = add_lag_and_rolling_features(df, target_col=target_col)
        train_df = df.dropna(subset=FEATURE_COLUMNS)

        X = train_df[FEATURE_COLUMNS]
        y = train_df[target_col]

        self._model = XGBRegressor(**self.params)
        self._model.fit(X, y)
        # Exogenous columns are carried forward into the future (see predict())
        # under a persistence assumption: absent a forward-looking discount/
        # marketing-spend plan, the model assumes recent levels continue.
        self._history = df[["date", target_col] + EXOGENOUS_COLUMNS].copy()
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if self._model is None or self._history is None:
            raise ValueError("Model must be fit before predicting.")

        history = self._history.copy()
        last_date = history["date"].max()
        # Persist the most recently observed discount / marketing spend /
        # peer-average level forward — the model has no visibility into
        # future promotional plans, so "no signal" is approximated as
        # "conditions stay as they last were" (documented assumption).
        last_exogenous = history.iloc[-1][EXOGENOUS_COLUMNS].to_dict()
        predictions = []

        for step in range(1, horizon + 1):
            next_date = last_date + pd.Timedelta(days=step)
            next_row = {"date": [next_date], self._target_col: [np.nan]}
            next_row.update({col: [val] for col, val in last_exogenous.items()})
            working = pd.concat([history, pd.DataFrame(next_row)], ignore_index=True)
            working = add_calendar_features(working)
            working = add_lag_and_rolling_features(working, target_col=self._target_col)
            row = working.iloc[[-1]][FEATURE_COLUMNS].fillna(0.0)
            pred = float(self._model.predict(row)[0])
            pred = max(0.0, pred)
            predictions.append(pred)
            history = pd.concat(
                [history, pd.DataFrame({**next_row, self._target_col: [pred]})],
                ignore_index=True,
            )

        return np.array(predictions)

    def feature_importances(self) -> dict:
        if self._model is None:
            return {}
        return dict(sorted(zip(FEATURE_COLUMNS, self._model.feature_importances_.tolist()), key=lambda kv: -kv[1]))
