"""FastAPI routes for wind forecast analysis and evaluation."""

from datetime import datetime, timedelta
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import (
    CoverageSummary,
    HealthResponse,
    HourlyMetric,
    IntervalRecord,
    MetricSummary,
    OverviewResponse,
    TimeseriesResponse,
)
from backend.repositories import (
    get_actuals_in_range,
    get_available_decision_date_range,
    get_forecasts_for_delivery_range,
    get_health_metadata,
)
from backend.services.forecast_selection import select_latest_eligible_forecasts
from backend.services.metrics import calculate_hourly_breakdown, calculate_metrics

router = APIRouter()

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_REGEX = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def validate_date(date_str: str, param_name: str) -> None:
    if not DATE_REGEX.match(date_str):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format for '{param_name}': '{date_str}'. Expected format YYYY-MM-DD.",
        )
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid calendar date for '{param_name}': '{date_str}'.",
        )


def validate_cutoff(cutoff_str: str) -> None:
    if not TIME_REGEX.match(cutoff_str):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format for 'cutoff': '{cutoff_str}'. Expected HH:MM in 24-hour time.",
        )


def process_single_day(
    decision_date_str: str,
    cutoff_time_str: str,
) -> Dict[str, Any]:
    """Process forecast selection, matching, and metrics for a single decision day."""
    decision_dt = datetime.strptime(decision_date_str, "%Y-%m-%d").date()
    delivery_dt = decision_dt + timedelta(days=1)
    delivery_date_str = delivery_dt.strftime("%Y-%m-%d")

    start_delivery_utc = f"{delivery_date_str}T00:00:00Z"
    end_delivery_utc = f"{delivery_date_str}T23:30:00Z"
    cutoff_utc = f"{decision_date_str}T{cutoff_time_str}:00Z"

    # Fetch actuals and forecasts from repository
    actual_rows = get_actuals_in_range(start_delivery_utc, end_delivery_utc)
    forecast_rows = get_forecasts_for_delivery_range(start_delivery_utc, f"{delivery_date_str}T23:00:00Z")

    # Select latest eligible forecast per delivery interval using vintage rule
    selected_fc = select_latest_eligible_forecasts(forecast_rows, cutoff_utc=cutoff_utc)

    # Index actuals by start_time_utc
    actuals_by_time = {r["start_time_utc"]: r for r in actual_rows}

    # WINDFOR delivers 24 hourly intervals per day.
    # We construct interval records for all 24 hourly intervals (and optionally include half-hourly if actuals exist)
    all_times = sorted(set(list(actuals_by_time.keys()) + list(selected_fc.keys())))

    interval_records: List[Dict[str, Any]] = []
    for t in all_times:
        act = actuals_by_time.get(t)
        fc = selected_fc.get(t)

        act_mw = act["generation_mw"] if act else None
        fc_mw = fc["generation_mw"] if fc else None

        if act_mw is not None and fc_mw is not None:
            err = round(act_mw - fc_mw, 2)
            status = "MATCHED"
        elif fc_mw is not None:
            err = None
            status = "MISSING_ACTUAL"
        else:
            err = None
            status = "MISSING_FORECAST"

        sp_date = act["settlement_date"] if act else (fc["settlement_date"] if fc else None)
        sp_num = act["settlement_period"] if act else (fc["settlement_period"] if fc else None)
        pub_time = fc["publish_time_utc"] if fc else None

        interval_records.append({
            "start_time_utc": t,
            "settlement_date": sp_date,
            "settlement_period": sp_num,
            "actual_mw": act_mw,
            "forecast_mw": fc_mw,
            "error_mw": err,
            "forecast_publish_time_utc": pub_time,
            "status": status,
        })

    # Expected count for hourly wind forecasts is 24 intervals per delivery day
    expected_count = 24
    metrics = calculate_metrics(interval_records, expected_count=expected_count)
    hourly = calculate_hourly_breakdown(interval_records)

    return {
        "decision_date": decision_date_str,
        "delivery_date": delivery_date_str,
        "cutoff_local": cutoff_time_str,
        "timezone": "Europe/London (GMT/UTC)",
        "cutoff_utc": cutoff_utc,
        "metrics": metrics,
        "hourly_breakdown": hourly,
        "intervals": interval_records,
    }


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """System health check and metadata endpoint."""
    meta = get_health_metadata()
    min_dec, max_dec = get_available_decision_date_range()
    return HealthResponse(
        status=meta["status"],
        database_accessible=meta["database_accessible"],
        actual_records_count=meta["actual_records_count"],
        forecast_records_count=meta["forecast_records_count"],
        distinct_forecast_vintages=meta["distinct_forecast_vintages"],
        available_decision_from=min_dec,
        available_decision_to=max_dec,
        recent_ingestion_runs=meta["recent_ingestion_runs"],
    )


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    decision_date: str = Query("2026-01-14", description="Decision date (YYYY-MM-DD)"),
    cutoff: str = Query("15:30", description="Procurement cutoff time (HH:MM)"),
) -> OverviewResponse:
    """Overview metrics, chart timeseries, and hourly error breakdown for a single decision date."""
    validate_date(decision_date, "decision_date")
    validate_cutoff(cutoff)

    data = process_single_day(decision_date, cutoff)
    return OverviewResponse(**data)


@router.get("/timeseries", response_model=TimeseriesResponse)
def get_timeseries(
    decision_from: str = Query("2026-01-01", description="Start decision date (YYYY-MM-DD)"),
    decision_to: str = Query("2026-01-31", description="End decision date (YYYY-MM-DD)"),
    cutoff: str = Query("15:30", description="Procurement cutoff time (HH:MM)"),
) -> TimeseriesResponse:
    """Multi-day timeseries and aggregated performance metrics."""
    validate_date(decision_from, "decision_from")
    validate_date(decision_to, "decision_to")
    validate_cutoff(cutoff)

    d_from = datetime.strptime(decision_from, "%Y-%m-%d").date()
    d_to = datetime.strptime(decision_to, "%Y-%m-%d").date()

    if d_from > d_to:
        raise HTTPException(
            status_code=400,
            detail=f"decision_from ({decision_from}) cannot be after decision_to ({decision_to}).",
        )

    all_intervals: List[Dict[str, Any]] = []
    total_days = (d_to - d_from).days + 1

    curr = d_from
    while curr <= d_to:
        day_str = curr.strftime("%Y-%m-%d")
        day_res = process_single_day(day_str, cutoff)
        all_intervals.extend(day_res["intervals"])
        curr += timedelta(days=1)

    # 24 forecast intervals expected per delivery day
    expected_count = total_days * 24
    overall_metrics = calculate_metrics(all_intervals, expected_count=expected_count)
    overall_hourly = calculate_hourly_breakdown(all_intervals)

    return TimeseriesResponse(
        decision_from=decision_from,
        decision_to=decision_to,
        cutoff_local=cutoff,
        timezone="Europe/London (GMT/UTC)",
        metrics=overall_metrics,
        hourly_breakdown=overall_hourly,
        intervals=all_intervals,
    )


@router.get("/intervals", response_model=List[IntervalRecord])
def get_intervals(
    decision_date: str = Query("2026-01-14", description="Decision date (YYYY-MM-DD)"),
    cutoff: str = Query("15:30", description="Procurement cutoff time (HH:MM)"),
) -> List[IntervalRecord]:
    """Interval-by-interval table dataset for tabular inspection."""
    validate_date(decision_date, "decision_date")
    validate_cutoff(cutoff)

    data = process_single_day(decision_date, cutoff)
    return [IntervalRecord(**it) for it in data["intervals"]]


@router.get("/coverage", response_model=CoverageSummary)
def get_coverage(
    decision_from: str = Query("2026-01-01", description="Start decision date (YYYY-MM-DD)"),
    decision_to: str = Query("2026-01-31", description="End decision date (YYYY-MM-DD)"),
) -> CoverageSummary:
    """Data completeness audit across decision date range."""
    validate_date(decision_from, "decision_from")
    validate_date(decision_to, "decision_to")

    d_from = datetime.strptime(decision_from, "%Y-%m-%d").date()
    d_to = datetime.strptime(decision_to, "%Y-%m-%d").date()

    if d_from > d_to:
        raise HTTPException(
            status_code=400,
            detail=f"decision_from ({decision_from}) cannot be after decision_to ({decision_to}).",
        )

    delivery_start = (d_from + timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00Z"
    delivery_end = (d_to + timedelta(days=1)).strftime("%Y-%m-%d") + "T23:30:00Z"

    actuals = get_actuals_in_range(delivery_start, delivery_end)
    forecasts = get_forecasts_for_delivery_range(delivery_start, delivery_end)

    total_days = (d_to - d_from).days + 1
    expected_intervals = total_days * 24

    act_times = set(r["start_time_utc"] for r in actuals)
    fc_times = set(r["start_time_utc"] for r in forecasts)
    matched_times = act_times.intersection(fc_times)

    cov_pct = round((len(matched_times) / expected_intervals * 100.0), 2) if expected_intervals > 0 else 0.0

    return CoverageSummary(
        decision_from=decision_from,
        decision_to=decision_to,
        total_delivery_days=total_days,
        expected_intervals=expected_intervals,
        actual_intervals_found=len(act_times),
        forecast_intervals_found=len(fc_times),
        matched_intervals=len(matched_times),
        coverage_pct=cov_pct,
    )
