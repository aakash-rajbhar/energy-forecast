"""Tests for database initialization, uniqueness constraints, and deduplication."""

import tempfile
from pathlib import Path
import pytest

from backend.db import get_db_connection, init_db
from backend.services.ingestion import (
    get_db_stats,
    record_ingestion_run,
)


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)
        yield db_path


def test_actual_generation_uniqueness(temp_db):
    conn = get_db_connection(temp_db)
    cur = conn.cursor()

    # Insert first record
    cur.execute(
        """
        INSERT INTO actual_generation (
            start_time_utc, settlement_date, settlement_period, fuel_type, generation_mw, source_record_id, fetched_at_utc
        ) VALUES ('2026-01-01T00:00:00Z', '2026-01-01', 1, 'WIND', 13756.0, 'FUELHH', '2026-10-25T21:00:00Z')
        """
    )
    conn.commit()

    # Attempt inserting duplicate with INSERT OR IGNORE
    cur.execute(
        """
        INSERT OR IGNORE INTO actual_generation (
            start_time_utc, settlement_date, settlement_period, fuel_type, generation_mw, source_record_id, fetched_at_utc
        ) VALUES ('2026-01-01T00:00:00Z', '2026-01-01', 1, 'WIND', 13756.0, 'FUELHH', '2026-10-25T21:00:00Z')
        """
    )
    conn.commit()
    assert cur.rowcount == 0

    cur.execute("SELECT COUNT(*) FROM actual_generation")
    assert cur.fetchone()[0] == 1
    conn.close()


def test_forecast_vintages_preserved_and_deduplicated(temp_db):
    conn = get_db_connection(temp_db)
    cur = conn.cursor()

    # Vintage 1: published at 11:30 for delivery at 15:00
    cur.execute(
        """
        INSERT INTO wind_forecasts (
            start_time_utc, publish_time_utc, settlement_date, settlement_period, generation_mw, source_record_id, fetched_at_utc
        ) VALUES ('2026-01-15T15:00:00Z', '2026-01-14T11:30:00Z', '2026-01-15', 31, 10000.0, 'WINDFOR', '2026-10-25T21:00:00Z')
        """
    )
    # Vintage 2: published at 15:30 for the SAME delivery interval at 15:00
    cur.execute(
        """
        INSERT INTO wind_forecasts (
            start_time_utc, publish_time_utc, settlement_date, settlement_period, generation_mw, source_record_id, fetched_at_utc
        ) VALUES ('2026-01-15T15:00:00Z', '2026-01-14T15:30:00Z', '2026-01-15', 31, 10500.0, 'WINDFOR', '2026-10-25T21:00:00Z')
        """
    )
    conn.commit()

    # Both vintages MUST be preserved
    cur.execute("SELECT COUNT(*) FROM wind_forecasts WHERE start_time_utc = '2026-01-15T15:00:00Z'")
    assert cur.fetchone()[0] == 2

    # Duplicate of Vintage 2 must be ignored
    cur.execute(
        """
        INSERT OR IGNORE INTO wind_forecasts (
            start_time_utc, publish_time_utc, settlement_date, settlement_period, generation_mw, source_record_id, fetched_at_utc
        ) VALUES ('2026-01-15T15:00:00Z', '2026-01-14T15:30:00Z', '2026-01-15', 31, 10500.0, 'WINDFOR', '2026-10-25T21:00:00Z')
        """
    )
    conn.commit()
    assert cur.rowcount == 0

    cur.execute("SELECT COUNT(*) FROM wind_forecasts")
    assert cur.fetchone()[0] == 2
    conn.close()


def test_ingestion_runs_logging(temp_db):
    conn = get_db_connection(temp_db)
    run_id = record_ingestion_run(
        conn=conn,
        dataset="TEST_DATA",
        requested_from="2026-01-01",
        requested_to="2026-01-02",
        started_at_utc="2026-10-25T21:00:00Z",
        finished_at_utc="2026-10-25T21:01:00Z",
        status="SUCCESS",
        records_received=100,
        records_inserted=98,
        records_skipped=2,
        error_summary=None,
    )
    assert run_id > 0

    stats = get_db_stats(temp_db)
    assert stats["ingestion_runs_count"] == 1
    conn.close()
