# Data Contract — Elexon Wind Forecast Pilot

> This is a target contract. Source-specific names, required query parameters, units, pagination and revision semantics must be filled in from official documentation and live smoke tests. Do not treat this document as proof that the data has been retrieved.

## 1. Source datasets

### Actual generation
- Dataset: `FUELHH`
- Filter: `fuelType = WIND`
- Target field: `startTime` (delivery interval start)
- Target field: `generation` (actual wind generation; confirm unit and null semantics)
- Preserve source settlement date/period and identifiers when available.

### Forecast generation
- Dataset: `WINDFOR`, or a verified official historical wind forecast endpoint.
- Target field: `startTime` (delivery interval being forecast)
- Target field: `publishTime` (when forecast became available)
- Target field: `generation` (forecast wind generation; confirm unit and null semantics)
- Preserve source identifiers/version fields when available.

Official documentation links:
- FUELHH stream: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- WINDFOR stream: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- Endpoint catalogue: https://bmrs.elexon.co.uk/api-documentation/endpoint
- Official wind forecast history endpoint to inspect: https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/history

## 2. Required source investigation record

Complete this table after smoke tests.

| Question | Observed answer / evidence |
|---|---|
| Exact endpoint used for actuals | `GET https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream` |
| Actual query parameters | `settlementDateFrom` (YYYY-MM-DD), `settlementDateTo` (YYYY-MM-DD), `fuelType=WIND` |
| Exact endpoint used for historical forecasts | `GET https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream` |
| Forecast query parameters | `publishDateTimeFrom` (ISO-8601 UTC), `publishDateTimeTo` (ISO-8601 UTC) |
| Response format and envelope | Direct JSON array `[...]` (streamed, no outer envelope wrapper) |
| Generation unit | Megawatts (MW), integer values (e.g. 13756, 12079) |
| Timestamp format and timezone | ISO-8601 UTC with 'Z' suffix (e.g. `2026-01-01T00:00:00Z`); `startTime` is delivery interval start, `publishTime` is publication instant |
| Resolution | `FUELHH`: 30-minute half-hourly (48 settlement periods/day); `WINDFOR`: 60-minute hourly (every hour on the hour `:00`) |
| Pagination / page size / maximum range | `/stream` endpoints return unpaginated JSON arrays. Full month range (1-31 Jan 2026) succeeded in a single request (1,488 actual records, 18,104 forecast records) |
| Null semantics | No null values observed in January 2026 (0 nulls in FUELHH, 0 nulls in WINDFOR). Nullable maintained in schema for missingness |
| Duplicate/revision behavior | `FUELHH`: 0 duplicates on `startTime`. `WINDFOR`: 0 duplicates on composite key `(publishTime, startTime)` |
| January 2026 coverage | 100% complete. FUELHH: exactly 1,488 records (31 days × 48 SPs). WINDFOR: 18,104 records across Jan 2026 |
| Historical publication versions available | Verified. Exactly 8 forecast runs published per day (typically 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC), yielding 8 day-ahead vintages per delivery hour |
| Request timestamp / HTTP status / record count | Tested 2026-10-25; FUELHH 2-day returned HTTP 200 (96 records); WINDFOR 1-day (2026-01-14) returned HTTP 200 (584 records); 31-day queries both HTTP 200 |

Raw response samples saved in `docs/samples/fuelhh_wind_sample.json` and `docs/samples/windfor_sample.json`.

## 3. Internal normalized records

The following are conceptual fields; adapt to verified source schema.

### `actual_generation`
- `id`: internal primary key
- `start_time_utc`: normalized ISO-8601 UTC instant
- `settlement_date`: source value if present
- `settlement_period`: source value if present
- `fuel_type`: must be `WIND` for records used in analysis
- `generation_mw`: numeric actual generation, nullable if source says missing
- `source_record_id`: source ID if available
- `fetched_at_utc`: ingestion timestamp

### `wind_forecasts`
- `id`: internal primary key
- `start_time_utc`: normalized delivery interval start
- `publish_time_utc`: normalized forecast publication instant
- `settlement_date`: source value if present
- `settlement_period`: source value if present
- `generation_mw`: numeric forecast generation, nullable if source says missing
- `source_record_id`: source ID/version if available
- `fetched_at_utc`: ingestion timestamp

### `ingestion_runs`
- `id`
- `dataset`
- `requested_from`
- `requested_to`
- `started_at_utc`
- `finished_at_utc`
- `status`
- `records_received`
- `records_inserted`
- `records_skipped`
- `error_summary`

Do not finalize the uniqueness constraints until source revisions/duplicates are understood. Distinct `publishTime` values for the same delivery interval must be retained.

## 4. Time and selection contract

- Normalize timestamps as timezone-aware instants, stored/compared in UTC.
- Preserve source settlement date and settlement period for market-facing display.
- Keep `startTime` and `publishTime` semantically separate.
- A forecast is eligible only if it targets the delivery interval and `publishTime <= cutoff_instant_utc`.
- For each interval, select the eligible record with the latest publication time.
- Cutoff is calculated from the documented decision date, local market timezone and configured local time.
- When publication times tie, use verified source revision/version semantics; otherwise flag ambiguity rather than inventing a tie-breaker.
- Join actuals by normalized delivery interval and any source-specific interval key needed to avoid false matches.

## 5. API response expectations

For every returned chart/metric dataset, include enough metadata to explain:
- selected decision date/range
- cutoff local time and timezone
- resolved cutoff instant or per-day cutoff rule
- source datasets/endpoints
- data extraction time
- expected, actual, forecast and matched interval counts
- coverage percentage and missing-data warnings
- metric definitions and units

## 6. Quality checks

- Verify expected interval count from source settlement calendar; do not blindly assume every day has exactly 48 intervals because settlement conventions and clock changes can affect counts.
- Check start/end boundaries for the selected decision-date interpretation.
- Check missing, duplicate and out-of-order timestamps.
- Check nonnumeric, null and implausible values without silently coercing them.
- Check all forecast publication times against the selected cutoff.
- Check selected forecast is the latest eligible vintage, not the latest record overall.
- Keep a reproducible ingestion summary with query ranges and counts.
