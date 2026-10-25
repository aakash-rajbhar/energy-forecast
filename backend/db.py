"""Database connection and schema setup for SQLite."""

from pathlib import Path
import sqlite3
from typing import Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "energy.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS actual_generation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time_utc TEXT NOT NULL,
    settlement_date TEXT,
    settlement_period INTEGER,
    fuel_type TEXT NOT NULL DEFAULT 'WIND',
    generation_mw REAL,
    source_record_id TEXT,
    fetched_at_utc TEXT NOT NULL,
    CONSTRAINT uq_actual_start_fuel UNIQUE (start_time_utc, fuel_type)
);

CREATE INDEX IF NOT EXISTS idx_actual_start_time ON actual_generation (start_time_utc);
CREATE INDEX IF NOT EXISTS idx_actual_settlement_date ON actual_generation (settlement_date);

CREATE TABLE IF NOT EXISTS wind_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time_utc TEXT NOT NULL,
    publish_time_utc TEXT NOT NULL,
    settlement_date TEXT,
    settlement_period INTEGER,
    generation_mw REAL,
    source_record_id TEXT,
    fetched_at_utc TEXT NOT NULL,
    CONSTRAINT uq_forecast_pub_start UNIQUE (publish_time_utc, start_time_utc)
);

CREATE INDEX IF NOT EXISTS idx_forecast_start_time ON wind_forecasts (start_time_utc);
CREATE INDEX IF NOT EXISTS idx_forecast_publish_time ON wind_forecasts (publish_time_utc);
CREATE INDEX IF NOT EXISTS idx_forecast_lookup ON wind_forecasts (start_time_utc, publish_time_utc);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset TEXT NOT NULL,
    requested_from TEXT NOT NULL,
    requested_to TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    finished_at_utc TEXT NOT NULL,
    status TEXT NOT NULL,
    records_received INTEGER NOT NULL,
    records_inserted INTEGER NOT NULL,
    records_skipped INTEGER NOT NULL,
    error_summary TEXT
);
"""


def get_db_connection(
    db_path: Optional[Path] = None, read_only: bool = False
) -> sqlite3.Connection:
    """Open a SQLite database connection with row factory enabled."""
    target_path = Path(db_path or DEFAULT_DB_PATH)
    if read_only:
        uri = f"file:{target_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(target_path.as_posix())
        conn.execute("PRAGMA journal_mode=WAL;")

    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize schema tables and indexes."""
    conn = get_db_connection(db_path, read_only=False)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
