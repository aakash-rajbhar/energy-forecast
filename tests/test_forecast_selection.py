"""Unit tests for forecast vintage selection with cutoff constraint."""

from backend.services.forecast_selection import select_latest_eligible_forecasts


def test_select_forecast_multiple_vintages():
    # 3 vintages for the same delivery interval 2026-01-15T12:00:00Z
    records = [
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T07:30:00Z", "generation_mw": 11000},
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T11:30:00Z", "generation_mw": 11350},
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T15:30:00Z", "generation_mw": 11850},
    ]

    # Cutoff at 12:00: only 07:30 and 11:30 are eligible; 11:30 is newest
    res = select_latest_eligible_forecasts(records, cutoff_utc="2026-01-14T12:00:00Z")
    assert "2026-01-15T12:00:00Z" in res
    assert res["2026-01-15T12:00:00Z"]["publish_time_utc"] == "2026-01-14T11:30:00Z"
    assert res["2026-01-15T12:00:00Z"]["generation_mw"] == 11350


def test_select_forecast_cutoff_boundary_exact_match():
    # Cutoff exactly at 15:30:00Z
    # Rule: publishTime <= cutoff, so 15:30:00Z IS eligible
    records = [
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T11:30:00Z", "generation_mw": 11350},
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T15:30:00Z", "generation_mw": 11850},
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T15:30:01Z", "generation_mw": 11900},
    ]

    res = select_latest_eligible_forecasts(records, cutoff_utc="2026-01-14T15:30:00Z")
    assert res["2026-01-15T12:00:00Z"]["publish_time_utc"] == "2026-01-14T15:30:00Z"
    assert res["2026-01-15T12:00:00Z"]["generation_mw"] == 11850


def test_select_forecast_just_after_cutoff_excluded():
    # If the only forecast was published 1 second after cutoff, it must NOT be selected
    records = [
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T15:30:01Z", "generation_mw": 11900},
    ]

    res = select_latest_eligible_forecasts(records, cutoff_utc="2026-01-14T15:30:00Z")
    assert "2026-01-15T12:00:00Z" not in res


def test_select_forecast_no_eligible_record():
    records = [
        {"start_time_utc": "2026-01-15T12:00:00Z", "publish_time_utc": "2026-01-14T18:30:00Z", "generation_mw": 12000},
    ]
    # Cutoff earlier than any publication
    res = select_latest_eligible_forecasts(records, cutoff_utc="2026-01-14T09:00:00Z")
    assert len(res) == 0


def test_select_forecast_multiple_delivery_intervals():
    records = [
        {"start_time_utc": "2026-01-15T10:00:00Z", "publish_time_utc": "2026-01-14T15:30:00Z", "generation_mw": 10000},
        {"start_time_utc": "2026-01-15T11:00:00Z", "publish_time_utc": "2026-01-14T15:30:00Z", "generation_mw": 10500},
    ]
    res = select_latest_eligible_forecasts(records, cutoff_utc="2026-01-14T15:30:00Z")
    assert len(res) == 2
    assert res["2026-01-15T10:00:00Z"]["generation_mw"] == 10000
    assert res["2026-01-15T11:00:00Z"]["generation_mw"] == 10500
