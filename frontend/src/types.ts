export interface IngestionRunInfo {
  dataset: string;
  requested_from: string;
  requested_to: string;
  finished_at_utc: string;
  status: string;
}

export interface HealthResponse {
  status: string;
  database_accessible: boolean;
  actual_records_count: number;
  forecast_records_count: number;
  distinct_forecast_vintages: number;
  available_decision_from: string | null;
  available_decision_to: string | null;
  recent_ingestion_runs: IngestionRunInfo[];
}

export interface MetricSummary {
  matched_count: number;
  expected_count: number;
  coverage_pct: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  overforecast_share_pct: number | null;
  underforecast_share_pct: number | null;
  min_error_mw: number | null;
  max_error_mw: number | null;
  p10_error_mw: number | null;
  p50_error_mw: number | null;
  p90_error_mw: number | null;
  p90_abs_error_mw: number | null;
}

export interface HourlyMetric {
  hour: number;
  count: number;
  mae_mw: number | null;
  bias_mw: number | null;
  mean_actual_mw: number | null;
  mean_forecast_mw: number | null;
}

export interface IntervalRecord {
  start_time_utc: string;
  settlement_date: string | null;
  settlement_period: number | null;
  actual_mw: number | null;
  forecast_mw: number | null;
  error_mw: number | null;
  forecast_publish_time_utc: string | null;
  status: 'MATCHED' | 'MISSING_ACTUAL' | 'MISSING_FORECAST' | string;
}

export interface OverviewResponse {
  decision_date: string;
  delivery_date: string;
  cutoff_local: string;
  timezone: string;
  cutoff_utc: string;
  provenance_dataset_actual: string;
  provenance_dataset_forecast: string;
  metrics: MetricSummary;
  hourly_breakdown: HourlyMetric[];
  intervals: IntervalRecord[];
}

export interface TimeseriesResponse {
  decision_from: string;
  decision_to: string;
  cutoff_local: string;
  timezone: string;
  metrics: MetricSummary;
  hourly_breakdown: HourlyMetric[];
  intervals: IntervalRecord[];
}

export interface CoverageSummary {
  decision_from: string;
  decision_to: string;
  total_delivery_days: number;
  expected_intervals: number;
  actual_intervals_found: number;
  forecast_intervals_found: number;
  matched_intervals: number;
  coverage_pct: number;
}
