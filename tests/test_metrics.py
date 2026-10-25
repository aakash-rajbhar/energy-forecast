"""Unit tests for metrics calculation, error sign, missing data handling, and percentiles."""

import math
import pytest

from backend.services.metrics import (
    calculate_hourly_breakdown,
    calculate_metrics,
    calculate_percentile,
)


def test_calculate_metrics_basic():
    # 4 intervals:
    # 1. act=100, fc=90  -> err = +10 (under-forecast)
    # 2. act=80,  fc=90  -> err = -10 (over-forecast)
    # 3. act=120, fc=100 -> err = +20 (under-forecast)
    # 4. act=70,  fc=90  -> err = -20 (over-forecast)
    intervals = [
        {"start_time_utc": "2026-01-15T00:00:00Z", "actual_mw": 100, "forecast_mw": 90},
        {"start_time_utc": "2026-01-15T01:00:00Z", "actual_mw": 80, "forecast_mw": 90},
        {"start_time_utc": "2026-01-15T02:00:00Z", "actual_mw": 120, "forecast_mw": 100},
        {"start_time_utc": "2026-01-15T03:00:00Z", "actual_mw": 70, "forecast_mw": 90},
    ]

    # errors: [+10, -10, +20, -20]
    # abs_errors: [10, 10, 20, 20] -> sum = 60 / 4 = 15.0
    # sq_errors: [100, 100, 400, 400] -> sum = 1000 / 4 = 250 -> sqrt(250) = 15.81
    # bias: (10 - 10 + 20 - 20) / 4 = 0.0
    # overforecasts: 2 out of 4 -> 50.0%
    res = calculate_metrics(intervals, expected_count=4)
    assert res["matched_count"] == 4
    assert res["expected_count"] == 4
    assert res["coverage_pct"] == 100.0
    assert res["mae_mw"] == 15.0
    assert res["rmse_mw"] == pytest.approx(15.81, rel=1e-2)
    assert res["bias_mw"] == 0.0
    assert res["overforecast_share_pct"] == 50.0
    assert res["underforecast_share_pct"] == 50.0


def test_calculate_metrics_error_sign():
    # If actual = 12000, forecast = 10000 -> actual exceeded forecast (under-forecast) -> err = +2000
    intervals = [
        {"start_time_utc": "2026-01-15T12:00:00Z", "actual_mw": 12000, "forecast_mw": 10000},
    ]
    res = calculate_metrics(intervals, expected_count=1)
    assert res["bias_mw"] == 2000.0
    assert res["overforecast_share_pct"] == 0.0
    assert res["underforecast_share_pct"] == 100.0

    # If actual = 8000, forecast = 10000 -> forecast exceeded actual (over-forecast) -> err = -2000
    intervals2 = [
        {"start_time_utc": "2026-01-15T12:00:00Z", "actual_mw": 8000, "forecast_mw": 10000},
    ]
    res2 = calculate_metrics(intervals2, expected_count=1)
    assert res2["bias_mw"] == -2000.0
    assert res2["overforecast_share_pct"] == 100.0
    assert res2["underforecast_share_pct"] == 0.0


def test_calculate_metrics_missing_data_not_zero():
    # Rule 4: Missing stays missing. Valid matched pairs only.
    # Total expected: 4
    # 1. complete
    # 2. missing actual (None)
    # 3. missing forecast (None)
    # 4. complete
    intervals = [
        {"start_time_utc": "2026-01-15T00:00:00Z", "actual_mw": 100, "forecast_mw": 90},
        {"start_time_utc": "2026-01-15T01:00:00Z", "actual_mw": None, "forecast_mw": 90},
        {"start_time_utc": "2026-01-15T02:00:00Z", "actual_mw": 120, "forecast_mw": None},
        {"start_time_utc": "2026-01-15T03:00:00Z", "actual_mw": 70, "forecast_mw": 80},
    ]
    res = calculate_metrics(intervals, expected_count=4)
    assert res["matched_count"] == 2
    assert res["expected_count"] == 4
    assert res["coverage_pct"] == 50.0
    # Matched errors: (100-90)=+10, (70-80)=-10
    assert res["mae_mw"] == 10.0
    assert res["bias_mw"] == 0.0


def test_calculate_metrics_zero_matched():
    intervals = [
        {"start_time_utc": "2026-01-15T00:00:00Z", "actual_mw": None, "forecast_mw": 90},
    ]
    res = calculate_metrics(intervals, expected_count=24)
    assert res["matched_count"] == 0
    assert res["mae_mw"] is None
    assert res["rmse_mw"] is None
    assert res["bias_mw"] is None
    assert res["coverage_pct"] == 0.0


def test_calculate_percentile():
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]
    p50 = calculate_percentile(vals, 50.0)
    assert p50 == 30.0
    p10 = calculate_percentile(vals, 10.0)
    assert p10 == pytest.approx(14.0)
    p90 = calculate_percentile(vals, 90.0)
    assert p90 == pytest.approx(46.0)


def test_hourly_breakdown():
    intervals = [
        {"start_time_utc": "2026-01-15T00:00:00Z", "actual_mw": 100, "forecast_mw": 90},
        {"start_time_utc": "2026-01-16T00:00:00Z", "actual_mw": 110, "forecast_mw": 90},
        {"start_time_utc": "2026-01-15T01:00:00Z", "actual_mw": 200, "forecast_mw": 220},
    ]
    breakdown = calculate_hourly_breakdown(intervals)
    assert len(breakdown) == 24
    h0 = breakdown[0]
    assert h0["hour"] == 0
    assert h0["count"] == 2
    assert h0["mae_mw"] == 15.0  # (|10| + |20|) / 2
    assert h0["bias_mw"] == 15.0 # (10 + 20) / 2

    h1 = breakdown[1]
    assert h1["hour"] == 1
    assert h1["count"] == 1
    assert h1["mae_mw"] == 20.0
    assert h1["bias_mw"] == -20.0  # 200 - 220
