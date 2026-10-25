"""Pure function for selecting the latest eligible forecast vintage per delivery interval."""

from typing import Any, Dict, List, Optional


def select_latest_eligible_forecasts(
    forecast_records: List[Dict[str, Any]],
    cutoff_utc: str,
) -> Dict[str, Dict[str, Any]]:
    """Select the newest eligible forecast vintage for each delivery interval.
    
    A forecast is eligible if and only if:
        publish_time_utc <= cutoff_utc

    For each delivery interval (start_time_utc), the eligible record with the
    maximum publish_time_utc is chosen.

    Args:
        forecast_records: List of dicts with 'start_time_utc', 'publish_time_utc', 'generation_mw'.
        cutoff_utc: Canonical ISO-8601 UTC string (e.g. '2026-01-14T15:30:00Z').

    Returns:
        Dict mapping start_time_utc -> selected forecast dict.
        Intervals with no eligible forecast are omitted from the dictionary.
    """
    # Group eligible records by delivery interval start_time_utc
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for record in forecast_records:
        start_time = record.get("start_time_utc")
        pub_time = record.get("publish_time_utc")

        if not start_time or not pub_time:
            continue

        # Eligibility check: publish_time <= cutoff
        if pub_time <= cutoff_utc:
            if start_time not in grouped:
                grouped[start_time] = []
            grouped[start_time].append(record)

    selected: Dict[str, Dict[str, Any]] = {}

    for start_time, records in grouped.items():
        # Sort by publish_time_utc ascending; latest publication will be at the end
        records.sort(key=lambda r: (r["publish_time_utc"], r.get("id", 0)))
        # Latest publication
        best_record = records[-1]
        selected[start_time] = {
            "start_time_utc": best_record["start_time_utc"],
            "publish_time_utc": best_record["publish_time_utc"],
            "generation_mw": best_record.get("generation_mw"),
            "settlement_date": best_record.get("settlement_date"),
            "settlement_period": best_record.get("settlement_period"),
            "source_record_id": best_record.get("source_record_id"),
        }

    return selected
