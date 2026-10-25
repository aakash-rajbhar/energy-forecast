"""Pure functions for error metrics, accuracy evaluation, and empirical planning margins."""

import math
from typing import Any, Dict, List, Optional


def calculate_percentile(sorted_values: List[float], p: float) -> Optional[float]:
    """Calculate the p-th percentile (0 <= p <= 100) using linear interpolation."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]

    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    return d0 + d1


def calculate_metrics(
    intervals: List[Dict[str, Any]],
    expected_count: int,
) -> Dict[str, Any]:
    """Calculate MAE, RMSE, bias (mean signed error), overforecast share, and coverage.
    
    Error sign convention:
        error = actual - forecast
    Positive error means actual exceeded forecast (under-forecast).
    Negative error means forecast exceeded actual (over-forecast).
    Over-forecast occurs when forecast > actual (error < 0).

    Rules:
    - Missing data stays missing: only intervals with valid numeric actual AND forecast are included.
    - No missing-as-zero coercion.

    Args:
        intervals: List of dicts with 'start_time_utc', 'actual_mw', 'forecast_mw'.
        expected_count: Total expected delivery intervals in the evaluated period.

    Returns:
        Summary dict containing all primary metrics and planning margin statistics.
    """
    valid_pairs: List[Dict[str, Any]] = []
    errors: List[float] = []
    abs_errors: List[float] = []
    sq_errors: List[float] = []
    overforecast_count = 0

    for item in intervals:
        actual = item.get("actual_mw")
        forecast = item.get("forecast_mw")

        # Strict check: both must be non-None numeric
        if actual is not None and forecast is not None:
            err = float(actual) - float(forecast)
            valid_pairs.append(item)
            errors.append(err)
            abs_errors.append(abs(err))
            sq_errors.append(err ** 2)
            if forecast > actual:
                overforecast_count += 1

    n = len(valid_pairs)
    coverage_pct = round((n / expected_count * 100.0), 2) if expected_count > 0 else 0.0

    if n == 0:
        return {
            "matched_count": 0,
            "expected_count": expected_count,
            "coverage_pct": coverage_pct,
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
            "overforecast_share_pct": None,
            "underforecast_share_pct": None,
            "min_error_mw": None,
            "max_error_mw": None,
            "p10_error_mw": None,
            "p50_error_mw": None,
            "p90_error_mw": None,
            "p90_abs_error_mw": None,
        }

    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(sq_errors) / n)
    bias = sum(errors) / n
    overforecast_share = (overforecast_count / n) * 100.0
    underforecast_share = 100.0 - overforecast_share

    sorted_errors = sorted(errors)
    sorted_abs = sorted(abs_errors)

    return {
        "matched_count": n,
        "expected_count": expected_count,
        "coverage_pct": coverage_pct,
        "mae_mw": round(mae, 2),
        "rmse_mw": round(rmse, 2),
        "bias_mw": round(bias, 2),
        "overforecast_share_pct": round(overforecast_share, 2),
        "underforecast_share_pct": round(underforecast_share, 2),
        "min_error_mw": round(min(errors), 2),
        "max_error_mw": round(max(errors), 2),
        "p10_error_mw": round(calculate_percentile(sorted_errors, 10.0), 2),
        "p50_error_mw": round(calculate_percentile(sorted_errors, 50.0), 2),
        "p90_error_mw": round(calculate_percentile(sorted_errors, 90.0), 2),
        "p90_abs_error_mw": round(calculate_percentile(sorted_abs, 90.0), 2),
    }


def calculate_hourly_breakdown(intervals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group intervals by delivery hour of day (0-23 UTC) and calculate metrics for each hour."""
    by_hour: Dict[int, List[Tuple[float, float]]] = {h: [] for h in range(24)}

    for item in intervals:
        start_time = item.get("start_time_utc")
        actual = item.get("actual_mw")
        forecast = item.get("forecast_mw")

        if not start_time or actual is None or forecast is None:
            continue

        try:
            # hour is character 11:13 in ISO string 'YYYY-MM-DDTHH:MM:SSZ'
            hour = int(start_time[11:13])
            by_hour[hour].append((float(actual), float(forecast)))
        except (ValueError, IndexError):
            continue

    breakdown: List[Dict[str, Any]] = []
    for h in range(24):
        pairs = by_hour[h]
        if not pairs:
            breakdown.append({
                "hour": h,
                "count": 0,
                "mae_mw": None,
                "bias_mw": None,
                "mean_actual_mw": None,
                "mean_forecast_mw": None,
            })
            continue

        count = len(pairs)
        errors = [act - fc for act, fc in pairs]
        mae = sum(abs(e) for e in errors) / count
        bias = sum(errors) / count
        mean_act = sum(act for act, _ in pairs) / count
        mean_fc = sum(fc for _, fc in pairs) / count

        breakdown.append({
            "hour": h,
            "count": count,
            "mae_mw": round(mae, 2),
            "bias_mw": round(bias, 2),
            "mean_actual_mw": round(mean_act, 2),
            "mean_forecast_mw": round(mean_fc, 2),
        })

    return breakdown

