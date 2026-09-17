export interface ValidationReport {
  is_valid: boolean;
  row_count: number;
  missing_required_columns: string[];
  missing_recommended_columns: string[];
  invalid_date_rows: number;
  duplicate_rows: number;
  missing_value_rows: number;
  invalid_numeric_rows: number;
  negative_value_rows: number;
  warnings: string[];
}

export interface CleaningSummary {
  input_rows: number;
  output_rows: number;
  dropped_invalid_dates: number;
  dropped_duplicates: number;
  dropped_missing_required: number;
  dropped_negative_values: number;
  imputed_unit_price: number;
  imputed_discount: number;
  imputed_marketing_spend: number;
  clipped_outliers: number;
  notes: string[];
}

export interface Dataset {
  id: number;
  filename: string;
  uploaded_at: string;
  row_count: number;
  cleaned_row_count: number;
  validation_report: ValidationReport;
  cleaning_summary: CleaningSummary;
}

export interface DatasetListItem {
  id: number;
  filename: string;
  uploaded_at: string;
  row_count: number;
  cleaned_row_count: number;
}

export interface SummaryKpis {
  total_revenue: number;
  total_units_sold: number;
  average_order_value: number;
  revenue_growth_rate_pct: number;
  date_range: { start: string; end: string };
  num_products: number;
  num_regions: number;
}

export interface TrendPoint {
  date: string;
  revenue: number;
  units_sold: number;
}

export interface TopProduct {
  product_id: string;
  product_name: string;
  revenue: number;
  units_sold: number;
}

export interface RegionPerf {
  region: string;
  revenue: number;
  units_sold: number;
}

export interface CategoryPerf {
  category: string;
  revenue: number;
  units_sold: number;
}

export interface FilterOptions {
  products: { product_id: string; product_name: string }[];
  regions: string[];
  categories: string[];
}

export interface ModelResult {
  name: string;
  metrics: { mae?: number; rmse?: number; mape?: number; r2?: number };
  predictions: number[];
  actuals: number[];
  dates: string[];
}

export interface TrainingRun {
  id: number;
  dataset_id: number;
  created_at: string;
  group_by: string;
  best_model: string;
  series_length: number;
  test_size: number;
  results: ModelResult[];
  anomalies: { date: string; value: number; z_score: number }[];
}

export interface ForecastResult {
  id: number;
  dataset_id: number;
  created_at: string;
  model_name: string;
  horizon: number;
  dates: string[];
  forecast: number[];
  lower_bound: number[];
  upper_bound: number[];
}
