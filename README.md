# UK Wind Generation Forecast vs Actual Analysis Pilot

An analytical full-stack pilot developed for a UK electricity utility day-ahead procurement desk. The application enables power buyers to evaluate what wind-generation forecasts were available at day-ahead market gate closures, compare them directly against actual generation outturns from Elexon BMRS, quantitatively evaluate forecast error metrics (MAE, RMSE, Bias, Overforecast Share), and determine empirical planning margins (MW) required for thermal backup procurement.

---

## 1. Quick Links

- **Deployed Live Application:** [https://energy-forecast.vercel.app](https://energy-forecast.vercel.app) *(or your deployed Vercel/Heroku URL)*
- **Demo Video (Unlisted YouTube):** [Watch Demo Video](https://youtube.com) *(Part 1: Customer Overview <= 5 min | Part 2: Technical Deep Dive <= 5 min)*
- **GitHub Repository:** [https://github.com/aakash-rajbhar/energy-forecast](https://github.com/aakash-rajbhar/energy-forecast)

---

## 2. Problem Context & Market Setting

UK day-ahead electricity buyers purchase wholesale power one day prior to delivery ($D-1$) to meet forecasted consumer demand on delivery day $D$. Because wind generation is intermittent and weather-dependent, buyers rely heavily on renewable forecasts when deciding how much additional firm generation (e.g. CCGT thermal or peakers) must be procured. 

This product answers three fundamental questions for the procurement team:
1. **What wind generation forecast was actually available** at our specific day-ahead decision cutoff?
2. **How large and biased was the forecast error** when compared to actual generation outturn?
3. **What empirical planning margin (in MW)** must be held to guard against intermittency shortfalls?

---

## 3. Key Market Assumptions & Data Conventions

| Rule / Convention | Implementation & Empirical Evidence |
|---|---|
| **Data Scope** | 100% official **Elexon BMRS Insights API** only. Actuals from `FUELHH/stream` (`fuelType = 'WIND'`); forecasts from `WINDFOR/stream`. No synthetic data. |
| **January 2026 Window** | Headline delivery window covers **1 Jan 2026 to 31 Jan 2026** (744 hours). Decisions for these delivery dates were made on **31 Dec 2025 to 30 Jan 2026**. Database also pre-ingested wider window (30 Dec 2025 – 2 Feb 2026). |
| **Vintage Selection Rule** | For each delivery interval, only forecasts with `publishTime <= cutoff` on decision day $D-1$ are eligible. The selected forecast is `max(publishTime)` among eligible vintages. Never substitutes the latest overall forecast for historical vintages. |
| **Default Cutoff** | **15:30 UK Local Time (UTC in Jan)**. Coincides with the EPEX SPOT UK Day-Ahead Half-Hourly auction gate closure and aligns with an official NGESO forecast publication run at 15:30 UTC. Fully configurable (e.g., 09:00, 12:00, 15:30). |
| **Error Sign** | $\text{Error} = \text{Actual} - \text{Forecast}$ (MW). Positive error = under-forecast (actual outturn exceeded forecast); Negative error = over-forecast (forecast exceeded outturn). |
| **No Missing-As-Zero** | Missing intervals remain strictly missing (never converted to 0). Evaluated metrics only use valid matched pairs, always reporting sample size $n$ and coverage %. |
| **Resolution Difference** | `FUELHH` actuals are published half-hourly (48 settlement periods/day); `WINDFOR` forecasts are published at 60-minute resolution (hourly, 24 periods/day). The chart displays gaps for unforecasted half-hours, and evaluation metrics evaluate the 24 hourly matched pairs (100% coverage of forecast resolution). |
| **Planning Margin** | Calculated as the 90th percentile of absolute error ($P_{90}$ Abs Error, in MW), translating statistical error into an actionable thermal reserve requirement. |

---

## 4. Architecture & System Design

```
+-------------------------------------------------------+
|                 Elexon BMRS API                       |
|   - FUELHH/stream (WIND actuals, 30-min resolution)   |
|   - WINDFOR/stream (Forecast runs, 8x daily)          |
+-------------------------------------------------------+
                           |
                           v  (Offline Ingestion CLI)
+-------------------------------------------------------+
|             Python Ingestion & Normalization          |
|   - ISO-8601 UTC timestamp canonicalization          |
|   - Settlement date & period derivation               |
|   - Audit logging in ingestion_runs table             |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|           SQLite Database (data/energy.db)            |
|   - actual_generation (1,680 records)                 |
|   - wind_forecasts (21,024 records across 288 runs)   |
|   - Ingestion audit logs (WAL mode, read-only in API) |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|             FastAPI Read-Only Backend                 |
|   - Pure forecast selection (publishTime <= cutoff)   |
|   - Pure metrics engine (MAE, RMSE, Bias, P90)        |
|   - Pydantic typed request & response validation      |
+-------------------------------------------------------+
                           |
                           v  (REST / JSON API)
+-------------------------------------------------------+
|        React + TypeScript + Tailwind Frontend         |
|   - Shadcn-styled UI, Lucide icons, Recharts          |
|   - Single-day & date-range multi-day evaluation      |
|   - Interactive actual vs forecast time-series        |
|   - 24-hour diurnal error & bias profile              |
|   - Searchable, filterable interval table + CSV export|
+-------------------------------------------------------+
```

---

## 5. Directory Structure

```text
energy-forecast/
├── backend/
│   ├── __init__.py
│   ├── cli.py                     # Offline CLI for data ingestion and stats
│   ├── db.py                      # SQLite schema initialization and read-only connection helper
│   ├── repositories.py            # Parameterized SQLite queries for actuals and forecasts
│   ├── sources/
│   │   ├── __init__.py
│   │   └── elexon.py              # Elexon BMRS API streaming client
│   ├── services/
│   │   ├── __init__.py
│   │   ├── normalization.py       # Timestamp UTC normalization, validation, settlement calculation
│   │   ├── forecast_selection.py  # Pure function selecting latest eligible vintage <= cutoff
│   │   ├── metrics.py             # Pure functions for MAE, RMSE, Bias, Overforecast %, P90 margin
│   │   └── ingestion.py           # Ingestion orchestrator and ingestion_runs auditor
│   └── api/
│       ├── __init__.py
│       ├── schemas.py             # Pydantic models for responses and errors
│       ├── routes.py              # API endpoints (/api/health, /overview, /timeseries, /intervals, /coverage)
│       └── main.py                # FastAPI application with CORS and static asset mount
├── frontend/
│   ├── src/
│   │   ├── api.ts                 # Typed fetch client with error handling
│   │   ├── types.ts               # TypeScript interfaces matching backend models
│   │   ├── lib/
│   │   │   └── utils.ts           # Shadcn cn utility (clsx + tailwind-merge)
│   │   ├── components/
│   │   │   ├── ui/                # Shadcn card, badge, button primitives
│   │   │   ├── Header.tsx         # Dashboard header with live database stats
│   │   │   ├── Controls.tsx       # Date picker, cutoff selector, market presets
│   │   │   ├── MetricCards.tsx    # KPI cards for MAE, RMSE, Bias, Overforecast %, Planning Margin
│   │   │   ├── ForecastChart.tsx  # Time-series Recharts with gap preservation & hourly profile toggle
│   │   │   ├── IntervalTable.tsx  # Accessible table with pagination, search, status filters, CSV export
│   │   │   └── ProvenanceCard.tsx # Detailed Elexon methodology and audit panel
│   │   ├── App.tsx                # Main dashboard page layout and state management
│   │   ├── index.css              # Tailwind CSS v4 design tokens and custom styles
│   │   └── main.tsx               # React DOM entrypoint
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts             # Vite configuration with proxy and path aliases
├── data/
│   └── energy.db                  # Precomputed read-only SQLite database (7.5 MB)
├── docs/
│   ├── data-contract.md           # Empirical Elexon schema evidence and response contracts
│   ├── decisions.md               # Architecture decisions (D-001 through D-010)
│   ├── demo-script.md             # Timed 10-minute demo outline (Part 1 and Part 2)
│   └── samples/                   # Raw JSON response samples from Elexon BMRS
├── tests/
│   ├── test_normalization.py      # Tests for timestamp parsing, UTC normalization, nulls
│   ├── test_ingestion.py          # Tests for database constraints, multi-vintage retention
│   ├── test_forecast_selection.py # Tests for cutoff boundaries (<= cutoff vs > cutoff)
│   ├── test_metrics.py            # Tests for MAE, RMSE, signed bias, missing data handling, P90
│   └── test_api.py                # FastAPI integration tests covering all endpoints
├── Dockerfile                     # Multi-stage container build (Node frontend build + Python runtime)
├── docker-compose.yml             # Single-command local startup
├── pyproject.toml                 # Pytest configuration
├── requirements.txt               # Python production dependencies
├── vercel.json                    # Vercel deployment configuration
└── README.md                      # Complete project documentation
```

---

## 6. How to Run Locally

### Option A: Using Docker (Recommended for clean clone)

No local Python or Node environment required.

```bash
# 1. Clone the repository
git clone https://github.com/aakash-rajbhar/energy-forecast.git
cd energy-forecast

# 2. Build and start the unified application
docker compose up --build

# 3. Open http://localhost:8000 in your browser
```

The container automatically builds the React frontend, packages the precomputed SQLite database, and serves both the FastAPI API and the frontend dashboard on port `8000`.

---

### Option B: Running Without Docker

#### Prerequisites
- Python 3.11+ (Python 3.12 / 3.14 supported)
- Node.js 20+ and npm

#### 1. Start the Backend API
```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
pip install pytest httpx

# (Optional) Run the offline ingestion CLI to refresh data from Elexon
python -m backend.cli ingest

# Start FastAPI server on port 8000
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

#### 2. Start the Frontend Development Server
In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` (or the port output by Vite) in your browser.

---

## 7. Running Verification Tests

Run the full backend test suite covering boundary conditions, multiple vintages, missing data, and API responses:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run pytest with verbose output
pytest -v
```

All 31 test cases validate:
- Cutoff boundary: records published at exactly `cutoff` are eligible; records published 1 second after are excluded.
- Retention of all distinct forecast publication vintages per interval.
- Missing generation values remain `None` and are never coerced to zero.
- Error sign convention strictly follows `actual - forecast`.
- API validation errors (400) on invalid date formats or inverted ranges.

Verify frontend TypeScript type checking and production bundle:
```bash
cd frontend
npm run build
```

---

## 8. Offline Ingestion CLI Reference

The offline CLI builds and inspects the read-only SQLite database:

```bash
# View summary database statistics
python -m backend.cli stats

# Ingest custom range from Elexon BMRS
python -m backend.cli ingest \
  --settlement-from 2025-12-30 \
  --settlement-to 2026-02-02 \
  --publish-from 2025-12-29T00:00:00Z \
  --publish-to 2026-02-02T23:59:59Z
```

---

## 9. AI Tools Disclosure

In accordance with the assignment guidelines, the following AI tools and models were utilized during the development of this project:
- **Google DeepMind Gemini (Advanced Agentic Assistant):** Used for domain research on Elexon BMRS endpoints, architecture planning, pure function design (forecast selection and metrics calculation), and test generation.
- All retrieved API contracts, sample responses, and metrics were empirically verified against live Elexon BMRS APIs without synthetic data fabrication.
