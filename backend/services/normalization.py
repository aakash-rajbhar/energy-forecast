"""Normalization and validation service for Elexon BMRS data."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


def normalize_to_utc_iso(dt_input: Any) -> str:
    """Normalize a datetime string or object to canonical ISO-8601 UTC string (YYYY-MM-DDTHH:MM:SSZ).
    
    Raises:
        ValueError: If input cannot be parsed or lacks valid date/time.
    """
    if dt_input is None:
        raise ValueError("Timestamp cannot be None")

    if isinstance(dt_input, datetime):
        dt = dt_input
    elif isinstance(dt_input, str):
        cleaned = dt_input.strip()
        if not cleaned:
            raise ValueError("Timestamp string cannot be empty")
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
    else:
        raise ValueError(f"Unsupported timestamp type: {type(dt_input)}")

    if dt.tzinfo is None:
        # Naive datetime: assume UTC per data contract specification
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def calculate_settlement_period_and_date(dt_utc: datetime) -> Tuple[str, int]:
    """Calculate UK settlement date and settlement period (1-48) for a UTC delivery start timestamp."""
    settlement_date = dt_utc.strftime("%Y-%m-%d")
    hour = dt_utc.hour
    minute = dt_utc.minute
    period = (hour * 2) + (1 if minute < 30 else 2)
    return settlement_date, period


def normalize_generation(val: Any) -> Optional[float]:
    """Normalize generation to float, keeping missing/None as None without coercion to zero.
    
    Raises:
        ValueError: If value is negative or cannot be parsed as numeric.
    """
    if val is None or val == "":
        return None
    try:
        fval = float(val)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid numeric generation value: {val!r}")
    if fval < 0:
        raise ValueError(f"Generation cannot be negative: {fval}")
    return fval


def normalize_actual_record(raw: Dict[str, Any], fetched_at_utc: str) -> Dict[str, Any]:
    """Normalize a raw record from FUELHH stream into internal actual_generation record."""
    start_time_utc = normalize_to_utc_iso(raw.get("startTime"))
    generation_mw = normalize_generation(raw.get("generation"))
    fuel_type = str(raw.get("fuelType", "WIND")).strip().upper()

    settlement_date = raw.get("settlementDate")
    settlement_period = raw.get("settlementPeriod")

    # If settlement fields are missing, derive from start_time_utc
    if not settlement_date or settlement_period is None:
        dt = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
        derived_date, derived_sp = calculate_settlement_period_and_date(dt)
        settlement_date = settlement_date or derived_date
        settlement_period = settlement_period if settlement_period is not None else derived_sp

    return {
        "start_time_utc": start_time_utc,
        "settlement_date": str(settlement_date),
        "settlement_period": int(settlement_period),
        "fuel_type": fuel_type,
        "generation_mw": generation_mw,
        "source_record_id": raw.get("dataset") or "FUELHH",
        "fetched_at_utc": fetched_at_utc,
    }


def normalize_forecast_record(raw: Dict[str, Any], fetched_at_utc: str) -> Dict[str, Any]:
    """Normalize a raw record from WINDFOR stream into internal wind_forecasts record."""
    start_time_utc = normalize_to_utc_iso(raw.get("startTime"))
    publish_time_utc = normalize_to_utc_iso(raw.get("publishTime"))
    generation_mw = normalize_generation(raw.get("generation"))

    dt = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
    settlement_date, settlement_period = calculate_settlement_period_and_date(dt)

    return {
        "start_time_utc": start_time_utc,
        "publish_time_utc": publish_time_utc,
        "settlement_date": settlement_date,
        "settlement_period": settlement_period,
        "generation_mw": generation_mw,
        "source_record_id": raw.get("dataset") or "WINDFOR",
        "fetched_at_utc": fetched_at_utc,
    }
