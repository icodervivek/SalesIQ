import type {
  CategoryPerf,
  Dataset,
  DatasetListItem,
  FilterOptions,
  ForecastResult,
  RegionPerf,
  SummaryKpis,
  TopProduct,
  TrainingRun,
  TrendPoint,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore non-JSON error body */
    }
    throw new ApiError(detail, res.status);
  }

  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  uploadDataset: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Dataset>("/api/datasets/upload", { method: "POST", body: form });
  },

  listDatasets: () => request<DatasetListItem[]>("/api/datasets"),
  getDataset: (id: number) => request<Dataset>(`/api/datasets/${id}`),

  filters: (datasetId: number) => request<FilterOptions>(`/api/analytics/filters?dataset_id=${datasetId}`),

  summary: (datasetId: number, params: Record<string, string | undefined> = {}) =>
    request<SummaryKpis>(`/api/analytics/summary?${buildQuery({ dataset_id: String(datasetId), ...params })}`),

  trends: (datasetId: number, freq: "D" | "W" | "M", params: Record<string, string | undefined> = {}) =>
    request<{ trend: TrendPoint[] }>(`/api/analytics/trends?${buildQuery({ dataset_id: String(datasetId), freq, ...params })}`),

  topProducts: (datasetId: number, params: Record<string, string | undefined> = {}) =>
    request<{ top_products: TopProduct[] }>(`/api/analytics/top-products?${buildQuery({ dataset_id: String(datasetId), ...params })}`),

  regions: (datasetId: number) => request<{ regions: RegionPerf[] }>(`/api/analytics/regions?dataset_id=${datasetId}`),
  categories: (datasetId: number) => request<{ categories: CategoryPerf[] }>(`/api/analytics/categories?dataset_id=${datasetId}`),

  trainModels: (datasetId: number, productId: string | null, region: string | null, testSize: number) =>
    request<TrainingRun>("/api/models/train", {
      method: "POST",
      body: JSON.stringify({ dataset_id: datasetId, product_id: productId || null, region: region || null, test_size: testSize }),
    }),

  listTrainingRuns: (datasetId: number) => request<TrainingRun[]>(`/api/models?dataset_id=${datasetId}`),

  createForecast: (
    datasetId: number,
    modelName: string | null,
    horizon: number,
    trainingRunId?: number,
    productId?: string | null,
    region?: string | null
  ) =>
    request<ForecastResult>("/api/forecast", {
      method: "POST",
      body: JSON.stringify({
        dataset_id: datasetId,
        model_name: modelName,
        horizon,
        training_run_id: trainingRunId,
        product_id: productId || null,
        region: region || null,
      }),
    }),

  forecastHistory: (datasetId: number) => request<ForecastResult[]>(`/api/forecast/history?dataset_id=${datasetId}`),

  exportForecastUrl: (forecastId: number) => `${API_BASE_URL}/api/forecast/${forecastId}/export`,
};

function buildQuery(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.set(key, value);
  });
  return search.toString();
}

export { ApiError };
