"""Ingestion service for pulling Elexon data and storing into SQLite."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Dict, Optional, Tuple

from backend.db import DEFAULT_DB_PATH, get_db_connection, init_db
from backend.services.normalization import (
    normalize_actual_record,
    normalize_forecast_record,
)
from backend.sources.elexon import (
    ElexonAPIError,
    fetch_fuelhh_stream,
    fetch_windfor_stream,
)


def now_utc_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_ingestion_run(
    conn: sqlite3.Connection,
    dataset: str,
    requested_from: str,
    requested_to: str,
    started_at_utc: str,
    finished_at_utc: str,
    status: str,
    records_received: int,
    records_inserted: int,
    records_skipped: int,
    error_summary: Optional[str] = None,
) -> int:
    """Insert a record into the ingestion_runs audit table."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO ingestion_runs (
            dataset, requested_from, requested_to, started_at_utc,
            finished_at_utc, status, records_received, records_inserted,
            records_skipped, error_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dataset,
            requested_from,
            requested_to,
            started_at_utc,
            finished_at_utc,
            status,
            records_received,
            records_inserted,
            records_skipped,
            error_summary,
        ),
    )
    conn.commit()
    return cursor.lastrowid or 0


def ingest_actuals(
    settlement_date_from: str,
    settlement_date_to: str,
    fuel_type: str = "WIND",
    db_path: Optional[Path] = None,
) -> Tuple[int, int, int]:
    """Fetch and ingest actual generation records from FUELHH into SQLite.
    
    Returns:
        (records_received, records_inserted, records_skipped)
    """
    started_at = now_utc_iso()
    init_db(db_path)
    conn = get_db_connection(db_path, read_only=False)

    received_count = 0
    inserted_count = 0
    skipped_count = 0

    try:
        raw_records = fetch_fuelhh_stream(
            settlement_date_from=settlement_date_from,
            settlement_date_to=settlement_date_to,
            fuel_type=fuel_type,
        )
        received_count = len(raw_records)
        fetched_at = now_utc_iso()

        cursor = conn.cursor()
        for raw in raw_records:
            try:
                norm = normalize_actual_record(raw, fetched_at_utc=fetched_at)
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO actual_generation (
                        start_time_utc, settlement_date, settlement_period,
                        fuel_type, generation_mw, source_record_id, fetched_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        norm["start_time_utc"],
                        norm["settlement_date"],
                        norm["settlement_period"],
                        norm["fuel_type"],
                        norm["generation_mw"],
                        norm["source_record_id"],
                        norm["fetched_at_utc"],
                    ),
                )
                if cursor.rowcount > 0:
                    inserted_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                skipped_count += 1

        conn.commit()
        finished_at = now_utc_iso()
        record_ingestion_run(
            conn=conn,
            dataset=f"FUELHH_{fuel_type}",
            requested_from=settlement_date_from,
            requested_to=settlement_date_to,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            status="SUCCESS",
            records_received=received_count,
            records_inserted=inserted_count,
            records_skipped=skipped_count,
        )
        return received_count, inserted_count, skipped_count

    except Exception as e:
        finished_at = now_utc_iso()
        record_ingestion_run(
            conn=conn,
            dataset=f"FUELHH_{fuel_type}",
            requested_from=settlement_date_from,
            requested_to=settlement_date_to,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            status="FAILED",
            records_received=received_count,
            records_inserted=inserted_count,
            records_skipped=skipped_count,
            error_summary=str(e),
        )
        raise
    finally:
        conn.close()


def ingest_forecasts(
    publish_date_time_from: str,
    publish_date_time_to: str,
    db_path: Optional[Path] = None,
) -> Tuple[int, int, int]:
    """Fetch and ingest wind forecast records from WINDFOR into SQLite.
    
    Returns:
        (records_received, records_inserted, records_skipped)
    """
    started_at = now_utc_iso()
    init_db(db_path)
    conn = get_db_connection(db_path, read_only=False)

    received_count = 0
    inserted_count = 0
    skipped_count = 0

    try:
        raw_records = fetch_windfor_stream(
            publish_date_time_from=publish_date_time_from,
            publish_date_time_to=publish_date_time_to,
        )
        received_count = len(raw_records)
        fetched_at = now_utc_iso()

        cursor = conn.cursor()
        for raw in raw_records:
            try:
                norm = normalize_forecast_record(raw, fetched_at_utc=fetched_at)
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO wind_forecasts (
                        start_time_utc, publish_time_utc, settlement_date,
                        settlement_period, generation_mw, source_record_id, fetched_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        norm["start_time_utc"],
                        norm["publish_time_utc"],
                        norm["settlement_date"],
                        norm["settlement_period"],
                        norm["generation_mw"],
                        norm["source_record_id"],
                        norm["fetched_at_utc"],
                    ),
                )
                if cursor.rowcount > 0:
                    inserted_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                skipped_count += 1

        conn.commit()
        finished_at = now_utc_iso()
        record_ingestion_run(
            conn=conn,
            dataset="WINDFOR",
            requested_from=publish_date_time_from,
            requested_to=publish_date_time_to,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            status="SUCCESS",
            records_received=received_count,
            records_inserted=inserted_count,
            records_skipped=skipped_count,
        )
        return received_count, inserted_count, skipped_count

    except Exception as e:
        finished_at = now_utc_iso()
        record_ingestion_run(
            conn=conn,
            dataset="WINDFOR",
            requested_from=publish_date_time_from,
            requested_to=publish_date_time_to,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            status="FAILED",
            records_received=received_count,
            records_inserted=inserted_count,
            records_skipped=skipped_count,
            error_summary=str(e),
        )
        raise
    finally:
        conn.close()


def get_db_stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Retrieve summary counts and date ranges from the database."""
    conn = get_db_connection(db_path, read_only=True)
    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*), MIN(start_time_utc), MAX(start_time_utc) FROM actual_generation")
        act_row = cur.fetchone()

        cur.execute("SELECT COUNT(*), COUNT(DISTINCT publish_time_utc), MIN(publish_time_utc), MAX(publish_time_utc) FROM wind_forecasts")
        fc_row = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM ingestion_runs")
        run_count = cur.fetchone()[0]

        return {
            "actual_count": act_row[0] if act_row else 0,
            "actual_min_time": act_row[1] if act_row else None,
            "actual_max_time": act_row[2] if act_row else None,
            "forecast_count": fc_row[0] if fc_row else 0,
            "forecast_vintages_count": fc_row[1] if fc_row else 0,
            "forecast_min_pub": fc_row[2] if fc_row else None,
            "forecast_max_pub": fc_row[3] if fc_row else None,
            "ingestion_runs_count": run_count,
        }
    finally:
        conn.close()
