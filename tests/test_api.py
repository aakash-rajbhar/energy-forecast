"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
import pytest

from backend.api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "health" in response.json()


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_accessible"] is True
    assert data["actual_records_count"] > 0
    assert data["forecast_records_count"] > 0
    assert data["distinct_forecast_vintages"] > 0
    assert data["available_decision_from"] is not None


def test_overview_valid():
    response = client.get("/api/overview?decision_date=2026-01-14&cutoff=15:30")
    assert response.status_code == 200
    data = response.json()
    assert data["decision_date"] == "2026-01-14"
    assert data["delivery_date"] == "2026-01-15"
    assert data["cutoff_local"] == "15:30"
    assert data["cutoff_utc"] == "2026-01-14T15:30:00Z"

    metrics = data["metrics"]
    assert metrics["matched_count"] == 24
    assert metrics["expected_count"] == 24
    assert metrics["coverage_pct"] == 100.0
    assert metrics["mae_mw"] is not None
    assert metrics["rmse_mw"] is not None
    assert metrics["bias_mw"] is not None

    # Hourly breakdown: 24 hours
    assert len(data["hourly_breakdown"]) == 24

    # Intervals list
    assert len(data["intervals"]) >= 24
    first_interval = data["intervals"][0]
    assert "start_time_utc" in first_interval
    assert "actual_mw" in first_interval
    assert "forecast_mw" in first_interval


def test_overview_invalid_date():
    response = client.get("/api/overview?decision_date=not-a-date&cutoff=15:30")
    assert response.status_code == 400
    assert "Invalid format" in response.json()["detail"]


def test_overview_invalid_cutoff():
    response = client.get("/api/overview?decision_date=2026-01-14&cutoff=25:99")
    assert response.status_code == 400
    assert "Invalid format for 'cutoff'" in response.json()["detail"]


def test_timeseries_valid_range():
    response = client.get("/api/timeseries?decision_from=2026-01-01&decision_to=2026-01-07&cutoff=15:30")
    assert response.status_code == 200
    data = response.json()
    assert data["decision_from"] == "2026-01-01"
    assert data["decision_to"] == "2026-01-07"
    metrics = data["metrics"]
    assert metrics["expected_count"] == 7 * 24
    assert metrics["matched_count"] == 7 * 24
    assert metrics["coverage_pct"] == 100.0


def test_timeseries_inverted_range():
    response = client.get("/api/timeseries?decision_from=2026-01-10&decision_to=2026-01-05")
    assert response.status_code == 400
    assert "cannot be after" in response.json()["detail"]


def test_intervals_endpoint():
    response = client.get("/api/intervals?decision_date=2026-01-14&cutoff=15:30")
    assert response.status_code == 200
    intervals = response.json()
    assert isinstance(intervals, list)
    assert len(intervals) >= 24
    assert "status" in intervals[0]


def test_coverage_endpoint():
    response = client.get("/api/coverage?decision_from=2026-01-01&decision_to=2026-01-31")
    assert response.status_code == 200
    data = response.json()
    assert data["total_delivery_days"] == 31
    assert data["expected_intervals"] == 31 * 24
    assert data["coverage_pct"] == 100.0
