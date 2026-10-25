# Demo Script (Maximum 10 Minutes)

The assignment requires two parts: a customer-facing overview (up to 5 minutes) and a technical review (up to 5 minutes). Keep the total under 10 minutes and use an unlisted YouTube video.

## Part 1 — Customer overview (target 4:00–4:30)

1. **Context (30 sec):** “This pilot helps a procurement analyst see the wind forecast available at a day-ahead decision cutoff and compare it with actual generation.”
2. **Cutoff and scope (30 sec):** Explain the selected decision-date interpretation, cutoff assumption, UK timezone and Elexon-only scope.
3. **Dashboard (60 sec):** Show the forecast-vs-actual chart and explain that each forecast is selected using its publication time.
4. **Metrics (60 sec):** Explain MAE, RMSE and bias in MW; clarify error sign and sample size.
5. **Coverage/provenance (45 sec):** Show missing intervals, matched coverage and source provenance. Be candid about any gaps.
6. **Practical value and limitation (30 sec):** Explain how quantified forecast error can inform judgment without claiming it makes trading decisions or guarantees savings.

## Part 2 — Technical review / knowledge transfer (target 4:00–4:30)

1. **Architecture (45 sec):** React/TypeScript frontend, FastAPI backend, SQLite and Elexon source.
2. **Data pipeline (60 sec):** Fetch, validate, normalize timestamps, retain forecast vintages, select latest eligible publication before cutoff, join actuals.
3. **Correctness (60 sec):** Explain UTC matching, missing data handling, duplicate/revision investigation, metric definitions and tests.
4. **Reliability and deployment (45 sec):** Docker, environment variables, CORS, persistent SQLite storage, health endpoint and deployment layout.
5. **Code tour (45 sec):** Point to source client, selection logic, metric module, API schemas, tests and README.
6. **Tradeoffs (30 sec):** Explain what was intentionally left out under the 16-hour cap and known data limitations.

## Recording checklist
- [ ] Both parts included; total duration <= 10 minutes.
- [ ] No fabricated metrics or unsupported data-coverage claims.
- [ ] Dashboard is deployed and works in a fresh/incognito browser.
- [ ] Public repository and deployment URL open without login.
- [ ] README includes AI-tool disclosure.
- [ ] Speak to observed implementation, not planned features.
