"""Unit tests for normalization and validation logic."""

from datetime import datetime, timezone
import pytest

from backend.services.normalization import (
    calculate_settlement_period_and_date,
    normalize_actual_record,
    normalize_forecast_record,
    normalize_generation,
    normalize_to_utc_iso,
)


def test_normalize_to_utc_iso_valid():
    assert normalize_to_utc_iso("2026-01-15T12:00:00Z") == "2026-01-15T12:00:00Z"
    assert normalize_to_utc_iso("2026-01-15T13:00:00+01:00") == "2026-01-15T12:00:00Z"
    assert normalize_to_utc_iso("2026-01-15T07:00:00-05:00") == "2026-01-15T12:00:00Z"


def test_normalize_to_utc_iso_datetime_object():
    dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert normalize_to_utc_iso(dt) == "2026-01-15T12:00:00Z"


def test_normalize_to_utc_iso_invalid():
    with pytest.raises(ValueError):
        normalize_to_utc_iso(None)
    with pytest.raises(ValueError):
        normalize_to_utc_iso("")
    with pytest.raises(ValueError):
        normalize_to_utc_iso("invalid-date")


def test_settlement_period_and_date():
    # 00:00 -> Period 1
    d1, sp1 = calculate_settlement_period_and_date(datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc))
    assert d1 == "2026-01-15"
    assert sp1 == 1

    # 00:30 -> Period 2
    _, sp2 = calculate_settlement_period_and_date(datetime(2026, 1, 15, 0, 30, tzinfo=timezone.utc))
    assert sp2 == 2

    # 12:00 -> Period 25
    _, sp25 = calculate_settlement_period_and_date(datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc))
    assert sp25 == 25

    # 23:30 -> Period 48
    _, sp48 = calculate_settlement_period_and_date(datetime(2026, 1, 15, 23, 30, tzinfo=timezone.utc))
    assert sp48 == 48


def test_normalize_generation_missing_preserved():
    # Rule: Missing stays missing, never converted to 0
    assert normalize_generation(None) is None
    assert normalize_generation("") is None
    assert normalize_generation(0) == 0.0
    assert normalize_generation("12079") == 12079.0


def test_normalize_generation_invalid():
    with pytest.raises(ValueError):
        normalize_generation("not-a-number")
    with pytest.raises(ValueError, match="cannot be negative"):
        normalize_generation(-50)


def test_normalize_actual_record():
    raw = {
        "dataset": "FUELHH",
        "publishTime": "2026-01-01T00:30:00Z",
        "startTime": "2026-01-01T00:00:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 1,
        "fuelType": "WIND",
        "generation": 13756,
    }
    norm = normalize_actual_record(raw, fetched_at_utc="2026-10-25T21:00:00Z")
    assert norm["start_time_utc"] == "2026-01-01T00:00:00Z"
    assert norm["settlement_date"] == "2026-01-01"
    assert norm["settlement_period"] == 1
    assert norm["fuel_type"] == "WIND"
    assert norm["generation_mw"] == 13756.0
    assert norm["source_record_id"] == "FUELHH"


def test_normalize_forecast_record():
    raw = {
        "dataset": "WINDFOR",
        "publishTime": "2026-01-14T15:30:00Z",
        "startTime": "2026-01-15T12:00:00Z",
        "generation": 11854,
    }
    norm = normalize_forecast_record(raw, fetched_at_utc="2026-10-25T21:00:00Z")
    assert norm["start_time_utc"] == "2026-01-15T12:00:00Z"
    assert norm["publish_time_utc"] == "2026-01-14T15:30:00Z"
    assert norm["settlement_date"] == "2026-01-15"
    assert norm["settlement_period"] == 25
    assert norm["generation_mw"] == 11854.0
