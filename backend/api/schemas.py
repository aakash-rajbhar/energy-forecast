"""Pydantic schemas for typed API request validation and response models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestionRunInfo(BaseModel):
    dataset: str
    requested_from: str
    requested_to: str
    finished_at_utc: str
    status: str


class HealthResponse(BaseModel):
    status: str
    database_accessible: bool
    actual_records_count: int
    forecast_records_count: int
    distinct_forecast_vintages: int
    available_decision_from: Optional[str] = None
    available_decision_to: Optional[str] = None
    recent_ingestion_runs: List[IngestionRunInfo] = []


class MetricSummary(BaseModel):
    matched_count: int
    expected_count: int
    coverage_pct: float
    mae_mw: Optional[float] = None
    rmse_mw: Optional[float] = None
    bias_mw: Optional[float] = None
    overforecast_share_pct: Optional[float] = None
    underforecast_share_pct: Optional[float] = None
    min_error_mw: Optional[float] = None
    max_error_mw: Optional[float] = None
    p10_error_mw: Optional[float] = None
    p50_error_mw: Optional[float] = None
    p90_error_mw: Optional[float] = None
    p90_abs_error_mw: Optional[float] = None


class HourlyMetric(BaseModel):
    hour: int
    count: int
    mae_mw: Optional[float] = None
    bias_mw: Optional[float] = None
    mean_actual_mw: Optional[float] = None
    mean_forecast_mw: Optional[float] = None


class IntervalRecord(BaseModel):
    start_time_utc: str
    settlement_date: Optional[str] = None
    settlement_period: Optional[int] = None
    actual_mw: Optional[float] = None
    forecast_mw: Optional[float] = None
    error_mw: Optional[float] = None
    forecast_publish_time_utc: Optional[str] = None
    status: str  # "MATCHED", "MISSING_FORECAST", "MISSING_ACTUAL"


class OverviewResponse(BaseModel):
    decision_date: str
    delivery_date: str
    cutoff_local: str
    timezone: str
    cutoff_utc: str
    provenance_dataset_actual: str = "FUELHH (WIND)"
    provenance_dataset_forecast: str = "WINDFOR"
    metrics: MetricSummary
    hourly_breakdown: List[HourlyMetric]
    intervals: List[IntervalRecord]


class TimeseriesResponse(BaseModel):
    decision_from: str
    decision_to: str
    cutoff_local: str
    timezone: str
    metrics: MetricSummary
    hourly_breakdown: List[HourlyMetric]
    intervals: List[IntervalRecord]


class CoverageSummary(BaseModel):
    decision_from: str
    decision_to: str
    total_delivery_days: int
    expected_intervals: int
    actual_intervals_found: int
    forecast_intervals_found: int
    matched_intervals: int
    coverage_pct: float


class ErrorDetail(BaseModel):
    detail: str
    error_code: str
