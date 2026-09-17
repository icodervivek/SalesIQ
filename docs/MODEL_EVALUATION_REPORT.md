# SalesIQ — Model Evaluation Report

This report documents the modeling approach, validation strategy, and results
produced by running the training pipeline (`POST /api/models/train`) on the
bundled synthetic dataset (`data/sample_sales.csv`, ~24 months, 10 products,
4 regions). Exact metric values will differ slightly by machine/library
version since XGBoost and SARIMA both have minor non-determinism; the
**relative ordering** of models is stable and is what this report focuses on.

## 1. Validation Strategy

A **chronological holdout** is used: the last *N* days (default 14, capped at
20% of series length) are held out as a test set, and every model is fit
**only** on the data before that cutoff. No shuffling is performed at any
point — shuffling a time series before splitting would let the model see
future values during training, which is the single most common form of
leakage in forecasting projects and was the first thing this pipeline was
designed to avoid.

This is a single-fold holdout rather than a rolling/expanding backtest. That
tradeoff was made deliberately for this assignment: a single holdout is fast
enough to run synchronously inside an API request (a few seconds), while a
proper walk-forward backtest (retraining at every step) would take
meaningfully longer per model and would need to move to a background job
(see `12. Advanced / Bonus Features → Background training jobs`). The
**Limitations** section below documents this explicitly.

## 2. Models Compared

| Model | Type | Notes |
|---|---|---|
| Baseline (Seasonal Naive) | Rule-based | Forecasts day *t* as the value observed 7 days earlier. Captures weekly seasonality with zero training cost. |
| SARIMA(1,1,1)(1,1,1,7) | Statistical | Classical time-series model with an explicit weekly seasonal component (`statsmodels`). |
| XGBoost (Lag + Calendar + Exogenous Features) | Machine learning | Gradient-boosted trees over lag (1/7/14/30), rolling mean/std (7/14/30), growth-rate, calendar features, and exogenous business features (discount, marketing spend, and a product/category/region peer-group benchmark — see §5.1). Multi-step forecasts are produced recursively. |

A moving-average baseline is also implemented (`ml/models/baseline.py`) but
the seasonal-naive baseline is used as the primary reference since daily
retail sales in this dataset have strong weekly seasonality (weekend uplift),
which a flat moving average cannot represent.

## 3. Metrics

- **MAE** — average absolute error in units; the most interpretable metric
  for a business stakeholder ("we are off by ~X units/day on average").
- **RMSE** — penalizes large misses more heavily than MAE; useful for
  flagging models that are occasionally very wrong even if usually close.
- **MAPE** — percentage error, with a 1-unit floor on the denominator so
  zero/near-zero actual days do not produce infinite or extreme values.
- **R²** — reported for context only, as instructed by the assignment spec;
  it is not used to select the final model because R² does not penalize
  forecast bias or scale the same way as MAE/RMSE for series with strong
  seasonality.

The final model is selected by **lowest RMSE on the holdout set**, since RMSE
is more sensitive than MAE to the large, business-relevant misses (e.g.
missing a demand spike before a promotion).

## 4. Results (global daily series, 14-day holdout)

These are actual measured values from `POST /api/models/train` on the
bundled `data/sample_sales.csv` (29,330 raw rows → 28,979 clean rows, 731-day
global series, last 14 days held out) — not illustrative placeholders. Minor
XGBoost non-determinism aside, re-running training reproduces this ordering.

| Model | MAE | RMSE | MAPE | R² |
|---|---|---|---|---|
| Baseline (Seasonal Naive) | 32.93 | 41.21 | 4.99% | 0.834 |
| SARIMA(1,1,1)(1,1,1,7) | 41.63 | 48.68 | 6.05% | 0.768 |
| **XGBoost (Lag + Calendar + Exogenous Features)** | **33.72** | **36.97** | **5.05%** | **0.866** |

**Selected model: XGBoost** (lowest holdout RMSE). Note the seasonal-naive
baseline is unusually strong here (MAPE under 5%) because the synthetic
dataset's weekly seasonality is clean and regular — a realistic reminder from
§20 of the spec that a sophisticated model isn't automatically much better
than a good baseline. XGBoost still wins on RMSE (fewer large misses, e.g.
around the November–December demand ramp) and is the model exposed by
default in `/api/forecast`; SARIMA remains available as an interpretable
statistical cross-check with native confidence intervals. For a *single*
product's series (smaller sample, noisier), SARIMA sometimes wins instead —
e.g. scoping training to `product_id=P001` (Laptop Pro) on this same dataset
gives SARIMA RMSE 5.59 vs. XGBoost RMSE 7.55, and the dashboard's automatic
model selection picks up on that per run rather than hard-coding one winner.

## 5. Feature Importance (XGBoost)

### 5.1 Exogenous features (product/category/region aggregate, discount, marketing spend)

Per §7.3 of the assignment spec, three exogenous features were added beyond
lag/calendar features:

- **`discount`, `marketing_spend`** — the same-day aggregated values from the
  daily series, used as *known/planned* inputs (a business typically decides
  today's promotion before observing today's sales, not after).
- **`peer_avg_units`** — a product/category/region aggregate: the peer
  group's average per-product demand (same category when scoped to a
  product, same region when scoped to a region, whole dataset otherwise).
  **Critically, this is computed one day lagged**, not same-day. An earlier
  version of this feature used the same-day peer total, which for the
  global (unscoped) series is almost exactly `target ÷ product_count` — a
  near-perfect same-day proxy for the very thing being predicted. In-sample
  that produced a deceptively excellent fit; at actual forecast time (where
  today's company-wide total is obviously not known in advance) it collapsed
  to RMSE ~150 because the model had learned to lean on information it would
  never really have. Lagging the feature by one day fixed this and is the
  reason `compute_peer_average_series` in `ml/features/feature_engineering.py`
  explicitly shifts the series — this is called out here because it's exactly
  the kind of leakage the assignment's validation-strategy section warns
  about, just in feature engineering rather than train/test splitting.

On the bundled dataset these three features individually rank mid-to-low in
importance for the *global* series (`peer_avg_units` ~15th of 23, `discount`
~16th, `marketing_spend` ~21st) — expected, since promotions in the synthetic
data are randomized per product-day and mostly wash out once aggregated
company-wide. They matter more at product-level scope, where a single
product's own discount pattern is a larger share of its day-to-day variance.

### 5.2 Overall ranking (global series)

1. `lag_7` — same weekday last week (dominant: weekly seasonality is the
   strongest signal in this dataset).
2. `is_weekend` — weekend uplift.
3. `lag_14` — two weeks prior, same weekday.
4. `day_of_week`, `rolling_mean_7`, `month` — recent level and monthly effects.

This matches intuition: weekly seasonality and recent momentum dominate,
which is also why the seasonal-naive baseline is already so competitive on
this dataset — and why it's the correct baseline to beat rather than a straw
man.

## 6. Why Not Just Use the Most "Sophisticated" Model?

Per the assignment's guidance (`20. Important ML Considerations`), a more
complex model is not automatically better. LSTM/GRU was evaluated as an
option and intentionally **not** implemented as a third model for this
submission: with ~24 months of daily data per segment, a deep sequence model
has a high risk of overfitting relative to XGBoost/SARIMA, adds a heavy
TensorFlow/PyTorch dependency, and — critically — would not be interpretable
enough to explain to a business stakeholder why a forecast moved. XGBoost was
preferred over a deep model specifically because `feature_importances()` (see
`ml/models/xgboost_model.py`) gives a defensible, auditable explanation.

## 7. Limitations

- **Single-fold holdout**, not a full walk-forward backtest. Metrics reflect
  performance on one 14-day window, not an average across many. A production
  system should retrain and re-evaluate on a rolling basis.
- **Missing days are treated as zero recorded sales** during aggregation
  (`aggregate_daily_series`), not as "unknown". For a real business this
  should be revisited — a missing day could mean "store closed" or "no data
  submitted", which are very different from "zero demand".
- **Exogenous features are limited to what the dataset provides.** `discount`,
  `marketing_spend`, and a lagged product/category/region peer-average are
  wired into XGBoost (§5.1), but a holiday calendar, stockout flags, and
  competitor pricing are not modeled — none of those are present in the
  dataset spec (§6) at all, so there's nothing to wire in without a richer
  source dataset.
- **`discount`/`marketing_spend` are assumed to be known in advance** (a
  planned promotion, not a same-day reaction to sales) and, for future
  forecast dates where no plan exists, are persisted forward at their last
  observed level rather than genuinely forecast. A real deployment would
  instead take a promotions calendar as an explicit forecast input.
- **Prediction intervals are approximate for XGBoost.** SARIMA provides
  proper statistical confidence intervals; XGBoost's interval is a residual-
  based heuristic (`ml/forecasting/pipeline.py::forecast_future`) and should
  be treated as an uncertainty *indicator*, not a calibrated interval.
- **New products with no history** cannot be forecast by this pipeline —
  there is no cold-start model. They would need a category-average or
  similar-product fallback, which is out of scope for this assignment.
- Forecasts assume historical patterns continue; they do not and cannot
  account for future structural changes (new competitors, macro shifts,
  supply disruptions) that are not represented in the training window.

## 8. Production Improvement Path

1. Replace the single holdout with expanding-window backtesting, run as a
   background job (Celery/RQ) rather than synchronously in the API.
2. Extend exogenous features with a holiday calendar and, if available,
   competitor pricing/stockout signals; pass `discount`/`marketing_spend` to
   SARIMA as `exog` too (currently XGBoost-only).
3. Add per-segment (product × region) models with a fallback to the global
   model when a segment has insufficient history.
4. Track experiments with MLflow so metric regressions are caught before a
   model is promoted.
5. Add drift monitoring — alert when live MAPE materially exceeds the
   validation MAPE, which signals the model needs retraining.
