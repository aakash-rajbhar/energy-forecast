"""Elexon BMRS API client for FUELHH and WINDFOR streams."""

import json
from typing import Any, Dict, List
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
DEFAULT_TIMEOUT_SECONDS = 60


class ElexonAPIError(Exception):
    """Raised when an Elexon BMRS API request fails."""

    def __init__(self, url: str, status_code: int, message: str) -> None:
        self.url = url
        self.status_code = status_code
        self.message = message
        super().__init__(f"Elexon API error {status_code} for {url}: {message}")


def _fetch_json_stream(endpoint_url: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
    """Fetch raw JSON stream from Elexon API endpoint."""
    query_string = urllib.parse.urlencode(params)
    full_url = f"{endpoint_url}?{query_string}" if query_string else endpoint_url
    req = urllib.request.Request(
        full_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "energy-forecast-pilot/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            raw_bytes = resp.read()
            text = raw_bytes.decode("utf-8")
            return json.loads(text)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise ElexonAPIError(url=full_url, status_code=e.code, message=err_body)
    except urllib.error.URLError as e:
        raise ElexonAPIError(url=full_url, status_code=0, message=str(e.reason))


def fetch_fuelhh_stream(
    settlement_date_from: str,
    settlement_date_to: str,
    fuel_type: str = "WIND",
) -> List[Dict[str, Any]]:
    """Fetch half-hourly generation outturn stream from Elexon BMRS.
    
    Args:
        settlement_date_from: Start date in YYYY-MM-DD
        settlement_date_to: End date in YYYY-MM-DD
        fuel_type: Fuel type filter, default 'WIND'
    """
    endpoint = f"{BASE_URL}/datasets/FUELHH/stream"
    params = {
        "settlementDateFrom": settlement_date_from,
        "settlementDateTo": settlement_date_to,
        "fuelType": fuel_type,
    }
    return _fetch_json_stream(endpoint, params)


def fetch_windfor_stream(
    publish_date_time_from: str,
    publish_date_time_to: str,
) -> List[Dict[str, Any]]:
    """Fetch wind generation forecast stream from Elexon BMRS.
    
    Args:
        publish_date_time_from: ISO-8601 UTC string (e.g. 2026-01-01T00:00:00Z)
        publish_date_time_to: ISO-8601 UTC string (e.g. 2026-01-31T23:59:59Z)
    """
    endpoint = f"{BASE_URL}/datasets/WINDFOR/stream"
    params = {
        "publishDateTimeFrom": publish_date_time_from,
        "publishDateTimeTo": publish_date_time_to,
    }
    return _fetch_json_stream(endpoint, params)
