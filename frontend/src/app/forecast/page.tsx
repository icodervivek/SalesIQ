"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, Loader2, PlayCircle, Sparkles, TriangleAlert } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useDatasetContext } from "@/lib/dataset-context";
import { ChartCard, EmptyState, Skeleton } from "@/components/ChartCard";
import { FilterBar } from "@/components/FilterBar";
import { ModelComparisonTable } from "@/components/ModelComparisonTable";
import { ValidationChart } from "@/components/ValidationChart";
import { ForecastChart } from "@/components/ForecastChart";
import { Banner } from "@/components/Banner";
import type { FilterOptions, ForecastResult, TrainingRun } from "@/lib/types";

const HORIZONS = [7, 30, 90];

export default function ForecastPage() {
  const { activeDatasetId } = useDatasetContext();
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [scope, setScope] = useState({ productId: "", region: "", category: "" });
  const [horizon, setHorizon] = useState(30);
  const [customHorizon, setCustomHorizon] = useState("");

  const [training, setTraining] = useState(false);
  const [trainingRun, setTrainingRun] = useState<TrainingRun | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");

  const [forecasting, setForecasting] = useState(false);
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [historical, setHistorical] = useState<{ date: string; units_sold: number }[]>([]);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeDatasetId) return;
    api.filters(activeDatasetId).then(setFilterOptions).catch(() => setFilterOptions(null));
    setTrainingRun(null);
    setForecast(null);
  }, [activeDatasetId]);

  const effectiveHorizon = customHorizon ? Number(customHorizon) : horizon;

  async function handleTrain() {
    if (!activeDatasetId) return;
    setTraining(true);
    setError(null);
    setForecast(null);
    try {
      const run = await api.trainModels(activeDatasetId, scope.productId || null, scope.region || null, 14);
      setTrainingRun(run);
      setSelectedModel(run.best_model);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Training failed.");
    } finally {
      setTraining(false);
    }
  }

  async function handleForecast() {
    if (!activeDatasetId || !selectedModel) return;
    setForecasting(true);
    setError(null);
    try {
      const [fc, trendRes] = await Promise.all([
        api.createForecast(activeDatasetId, selectedModel, effectiveHorizon, trainingRun?.id, scope.productId, scope.region),
        api.trends(activeDatasetId, "D", { product_id: scope.productId || undefined, region: scope.region || undefined }),
      ]);
      setForecast(fc);
      setHistorical(trendRes.trend.slice(-90));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Forecast generation failed.");
    } finally {
      setForecasting(false);
    }
  }

  const chartPoints = useMemo(() => {
    if (!forecast) return [];
    const histPoints = historical.map((h) => ({ date: h.date, historical: h.units_sold }));
    const forecastPoints = forecast.dates.map((date, i) => ({
      date,
      forecast: forecast.forecast[i],
      lower_bound: forecast.lower_bound[i],
      upper_bound: forecast.upper_bound[i],
    }));
    return [...histPoints, ...forecastPoints];
  }, [forecast, historical]);

  const bestResult = trainingRun?.results.find((r) => r.name === selectedModel) ?? trainingRun?.results.find((r) => r.metrics && Object.keys(r.metrics).length);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white">Forecasting</h1>
        <p className="mt-1 text-sm text-gray-500">Train and compare models, then generate a demand forecast for any horizon.</p>
      </div>

      {!activeDatasetId ? (
        <EmptyState title="No dataset selected" description="Upload a dataset first to train forecasting models." />
      ) : (
        <>
          <ChartCard title="1. Scope & Training" subtitle="Choose the forecast scope, then train baseline, SARIMA, and XGBoost models">
            <div className="space-y-4">
              <FilterBar
                options={filterOptions}
                productId={scope.productId}
                region={scope.region}
                category={scope.category}
                onChange={(next) => setScope((prev) => ({ ...prev, ...next }))}
              />
              <button
                onClick={handleTrain}
                disabled={training}
                className="flex items-center gap-2 rounded-xl bg-brand-gradient px-4 py-2.5 text-sm font-medium text-white shadow-glow transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {training ? <Loader2 size={16} className="animate-spin" /> : <PlayCircle size={16} />}
                {training ? "Training models…" : "Train Models"}
              </button>
            </div>
          </ChartCard>

          {error && <Banner tone="error" message={error} />}

          {training && (
            <ChartCard title="Model Comparison" subtitle="Evaluating on a chronological holdout set">
              <Skeleton className="h-40 rounded-xl" />
            </ChartCard>
          )}

          {trainingRun && !training && (
            <>
              <ChartCard
                title="2. Model Comparison"
                subtitle={`Trained on ${trainingRun.series_length} days · held out the last ${trainingRun.test_size} days for validation`}
              >
                <ModelComparisonTable results={trainingRun.results} bestModel={trainingRun.best_model} />
              </ChartCard>

              <ChartCard
                title="Holdout: Actual vs Predicted"
                subtitle="Lower MAE/RMSE/MAPE indicates a better fit on unseen data"
                action={
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="rounded-lg border border-surface-border bg-surface-card px-3 py-1.5 text-xs text-gray-200"
                  >
                    {trainingRun.results
                      .filter((r) => r.metrics && Object.keys(r.metrics).length)
                      .map((r) => (
                        <option key={r.name} value={r.name}>
                          {r.name}
                        </option>
                      ))}
                  </select>
                }
              >
                {bestResult ? <ValidationChart result={bestResult} /> : <EmptyState title="No result" description="Select a model." />}
              </ChartCard>

              {trainingRun.anomalies.length > 0 && (
                <ChartCard title="Detected Anomalies" subtitle="Days that deviate sharply from the recent trend">
                  <div className="flex flex-wrap gap-2">
                    {trainingRun.anomalies.map((a) => (
                      <div key={a.date} className="flex items-center gap-1.5 rounded-lg border border-accent-amber/25 bg-accent-amber/5 px-3 py-1.5 text-xs text-accent-amber">
                        <TriangleAlert size={12} />
                        {a.date} · {a.value.toLocaleString()} units (z={a.z_score})
                      </div>
                    ))}
                  </div>
                </ChartCard>
              )}

              <ChartCard title="3. Generate Forecast" subtitle="Choose a horizon and produce a forward-looking forecast">
                <div className="flex flex-wrap items-end gap-4">
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">Horizon (days)</span>
                    <div className="flex gap-1.5">
                      {HORIZONS.map((h) => (
                        <button
                          key={h}
                          onClick={() => {
                            setHorizon(h);
                            setCustomHorizon("");
                          }}
                          className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                            horizon === h && !customHorizon ? "bg-brand-600/20 text-brand-200 border border-brand-500/40" : "border border-surface-border text-gray-400 hover:text-gray-200"
                          }`}
                        >
                          {h}d
                        </button>
                      ))}
                      <input
                        type="number"
                        placeholder="Custom"
                        value={customHorizon}
                        onChange={(e) => setCustomHorizon(e.target.value)}
                        className="w-24 rounded-lg border border-surface-border bg-surface-card px-3 py-2 text-sm text-gray-200 outline-none focus:border-brand-500"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <span className="text-[11px] font-medium uppercase tracking-wide text-gray-500">Model</span>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="rounded-lg border border-surface-border bg-surface-card px-3 py-2 text-sm text-gray-200"
                    >
                      {trainingRun.results
                        .filter((r) => r.metrics && Object.keys(r.metrics).length)
                        .map((r) => (
                          <option key={r.name} value={r.name}>
                            {r.name}
                            {r.name === trainingRun.best_model ? " (best)" : ""}
                          </option>
                        ))}
                    </select>
                  </div>

                  <button
                    onClick={handleForecast}
                    disabled={forecasting}
                    className="flex items-center gap-2 rounded-xl bg-brand-gradient px-4 py-2.5 text-sm font-medium text-white shadow-glow transition-opacity hover:opacity-90 disabled:opacity-50"
                  >
                    {forecasting ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                    {forecasting ? "Forecasting…" : "Generate Forecast"}
                  </button>
                </div>
              </ChartCard>
            </>
          )}

          {forecast && (
            <ChartCard
              title="Forecast Result"
              subtitle={`${forecast.model_name} · next ${forecast.horizon} days · shaded band = prediction interval`}
              action={
                <a
                  href={api.exportForecastUrl(forecast.id)}
                  className="flex items-center gap-1.5 rounded-lg border border-surface-border px-3 py-1.5 text-xs font-medium text-gray-300 hover:border-brand-500/50 hover:text-white"
                >
                  <Download size={13} />
                  Export CSV
                </a>
              }
            >
              <ForecastChart points={chartPoints} splitDate={historical.length ? historical[historical.length - 1].date : null} />
            </ChartCard>
          )}
        </>
      )}
    </div>
  );
}
