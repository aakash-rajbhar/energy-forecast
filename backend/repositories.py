"""Read-only repository for querying actuals, forecasts, and ingestion metadata."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.db import DEFAULT_DB_PATH, get_db_connection


def get_actuals_in_range(
    start_time_from: str,
    start_time_to: str,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Retrieve actual wind generation records whose delivery start is in [start_time_from, start_time_to]."""
    conn = get_db_connection(db_path, read_only=True)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, start_time_utc, settlement_date, settlement_period, fuel_type, generation_mw, fetched_at_utc
            FROM actual_generation
            WHERE start_time_utc >= ? AND start_time_utc <= ? AND fuel_type = 'WIND'
            ORDER BY start_time_utc ASC
            """,
            (start_time_from, start_time_to),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_forecasts_for_delivery_range(
    start_time_from: str,
    start_time_to: str,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all forecast vintages targeting delivery intervals in [start_time_from, start_time_to]."""
    conn = get_db_connection(db_path, read_only=True)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, start_time_utc, publish_time_utc, settlement_date, settlement_period, generation_mw, source_record_id
            FROM wind_forecasts
            WHERE start_time_utc >= ? AND start_time_utc <= ?
            ORDER BY start_time_utc ASC, publish_time_utc ASC
            """,
            (start_time_from, start_time_to),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_available_decision_date_range(db_path: Optional[Path] = None) -> Tuple[Optional[str], Optional[str]]:
    """Determine the available range of decision dates from ingested actuals and forecasts.
    
    A decision date D is supported if delivery date D+1 has actuals.
    """
    conn = get_db_connection(db_path, read_only=True)
    try:
        cur = conn.cursor()
        cur.execute("SELECT MIN(start_time_utc), MAX(start_time_utc) FROM actual_generation")
        row = cur.fetchone()
        if not row or not row[0] or not row[1]:
            return None, None

        min_act = row[0][:10]
        max_act = row[1][:10]

        # Delivery day D+1 corresponds to decision day D
        min_delivery = datetime.strptime(min_act, "%Y-%m-%d").date()
        max_delivery = datetime.strptime(max_act, "%Y-%m-%d").date()

        min_decision = (min_delivery - timedelta(days=1)).strftime("%Y-%m-%d")
        max_decision = (max_delivery - timedelta(days=1)).strftime("%Y-%m-%d")
        return min_decision, max_decision
    finally:
        conn.close()


def get_health_metadata(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Retrieve health information including table counts and last ingestion run."""
    conn = get_db_connection(db_path, read_only=True)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM actual_generation")
        actual_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*), COUNT(DISTINCT publish_time_utc) FROM wind_forecasts")
        fc_row = cur.fetchone()
        forecast_count = fc_row[0]
        vintages_count = fc_row[1]

        cur.execute(
            """
            SELECT dataset, requested_from, requested_to, finished_at_utc, status
            FROM ingestion_runs
            ORDER BY id DESC LIMIT 5
            """
        )
        recent_runs = [dict(r) for r in cur.fetchall()]

        return {
            "status": "healthy",
            "database_accessible": True,
            "actual_records_count": actual_count,
            "forecast_records_count": forecast_count,
            "distinct_forecast_vintages": vintages_count,
            "recent_ingestion_runs": recent_runs,
        }
    finally:
        conn.close()
