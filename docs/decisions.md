# Decision Log and Assumptions

Status labels: **OPEN** = must be resolved; **PROPOSED** = working default requiring evidence; **DECIDED** = accepted project choice.

## D-001 - Meaning of January 2026
**Status: DECIDED (reversible)**

Headline view = **delivery days in January 2026** (1 to 31 Jan). The relevant decisions are made on the day before (31 Dec to 30 Jan). Rationale: clean 31-day month, and the assignment's fields (`startTime`) are delivery times. Ingest a wider window (delivery 31 Dec 2025 to 1 Feb 2026, plus forecast vintages published in the days before) so the "decision dates in January" reading can be offered as a UI option without re-ingesting. State the interpretation on the dashboard, README and demo.

## D-002 - Historical forecast vintages
**Status: DECIDED**

Verified via `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream`. The endpoint supports full-range queries for January 2026 and returned 18,104 records. NGESO publishes 8 forecast runs per day (typically 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC). Each delivery hour has up to 8 distinct day-ahead vintages published on D-1. Resolution of WINDFOR is 60 minutes (hourly, on the hour).

## D-003 - Procurement cutoff
**Status: DECIDED**

Default: **D-1 15:30 UK local time (UTC in Jan)**. Rationale:
1. NGESO publishes an official forecast vintage exactly at `15:30:00Z` on all 31 days in January 2026.
2. 15:30 coincides with the EPEX SPOT UK Day-Ahead Half-Hourly auction gate closure.
3. Boundary condition: With rule `publishTime <= cutoff`, the 15:30:00Z run is the latest eligible vintage for the 15:30 cutoff.
UI and API support configurable cutoff choices (e.g., 09:00, 11:00, 12:00, 15:30, 17:00) with 15:30 as the documented default.

## D-004 — Stack
**Status: DECIDED**

- Frontend: React + TypeScript + Vite, deployed to Vercel.
- Backend: Python + FastAPI.
- Storage: SQLite.
- Docker for reproducible local development.
- Backend hosting: still to be selected; persistent storage support is a requirement.

## D-005 — Data source
**Status: DECIDED**

Use Elexon BMRS national wind data only, as required by the assignment. Actual generation uses `FUELHH` filtered to `fuelType = WIND`. Forecasts use `WINDFOR` or a verified official historical wind forecast endpoint. No third-party market or weather data.

## D-006 — Error sign
**Status: DECIDED**

`error_mw = actual_mw - forecast_mw`. Positive means actual generation exceeded the forecast; negative means forecast was above actual generation.

## D-007 — Metrics
**Status: DECIDED**

MAE, RMSE, mean signed error/bias and overforecast share. Calculate only over valid matched actual/forecast pairs. Always report sample size and coverage. Do not use MAPE as the main metric due zero/near-zero actuals.

## D-008 — Missing and duplicate data
**Status: DECIDED in principle; schema-dependent details OPEN**

Never convert missing generation to zero. Preserve missingness and show coverage. Investigate duplicate/revised source records before choosing a uniqueness constraint or tie-breaker. Preserve distinct forecast publication vintages.

## D-009 - Storage and hosting
**Status: DECIDED**

January 2026 is a fixed historical window, so the dataset is static. Ingestion runs offline via a CLI that builds a SQLite file; the file is committed (or built at deploy) and opened **read-only** by the API. Hosting: single Vercel project (React frontend + FastAPI as a Python function), no CORS or persistent disk needed. Check current Vercel Python limits early in Phase 5. Docker is for local, reproducible development. Limitation to state: no live refresh.

## D-010 - Decision-support layer
**Status: DECIDED**

Beyond the metrics, include (a) error by hour of day or forecast lead time, and (b) an empirical error band (e.g. P10 to P90 of past error) around the forecast, expressed in MW. No price, savings or trading claims.
