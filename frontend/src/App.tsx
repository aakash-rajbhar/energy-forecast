import React, { useState, useEffect, useCallback } from "react";
import { AlertTriangle, Layers, RefreshCw } from "lucide-react";
import { Header } from "./components/Header";
import { Controls } from "./components/Controls";
import { MetricCards } from "./components/MetricCards";
import { ForecastChart } from "./components/ForecastChart";
import { IntervalTable } from "./components/IntervalTable";
import { ProvenanceCard } from "./components/ProvenanceCard";
import { Button } from "./components/ui/button";
import { fetchHealth, fetchOverview, fetchTimeseries, fetchCoverage } from "./api";
import type {
  CoverageSummary,
  HealthResponse,
  HourlyMetric,
  IntervalRecord,
  MetricSummary,
} from "./types";

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [mode, setMode] = useState<"single" | "range">("single");
  const [decisionDate, setDecisionDate] = useState("2026-01-14");
  const [decisionFrom, setDecisionFrom] = useState("2026-01-01");
  const [decisionTo, setDecisionTo] = useState("2026-01-31");
  const [cutoff, setCutoff] = useState("15:30");

  const [deliveryDate, setDeliveryDate] = useState("2026-01-15");
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);
  const [hourlyBreakdown, setHourlyBreakdown] = useState<HourlyMetric[]>([]);
  const [intervals, setIntervals] = useState<IntervalRecord[]>([]);
  const [coverage, setCoverage] = useState<CoverageSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load health metadata once on mount
  useEffect(() => {
    fetchHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.warn("Could not load health info:", err));
  }, []);

  // Main data fetch function
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (mode === "single") {
        const overview = await fetchOverview(decisionDate, cutoff);
        setDeliveryDate(overview.delivery_date);
        setMetrics(overview.metrics);
        setHourlyBreakdown(overview.hourly_breakdown);
        setIntervals(overview.intervals);
      } else {
        const [tsData, covData] = await Promise.all([
          fetchTimeseries(decisionFrom, decisionTo, cutoff),
          fetchCoverage(decisionFrom, decisionTo),
        ]);
        setMetrics(tsData.metrics);
        setHourlyBreakdown(tsData.hourly_breakdown);
        setIntervals(tsData.intervals);
        setCoverage(covData);
      }
    } catch (err: unknown) {
      console.error("Fetch error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "An error occurred while fetching forecast evaluation data.",
      );
    } finally {
      setLoading(false);
    }
  }, [mode, decisionDate, decisionFrom, decisionTo, cutoff]);

  useEffect(() => {
    // The request is the external system this effect synchronises with.
    // oxlint-disable-next-line react/set-state-in-effect
    loadData();
  }, [loadData]);

  return (
    <div className="flex min-h-screen flex-col bg-canvas font-sans text-ink">
      <a
        href="#dashboard"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:rounded-lg focus:bg-ink focus:px-3 focus:py-2 focus:text-xs focus:text-white"
      >
        Skip to dashboard
      </a>

      <Header health={health} cutoff={cutoff} />

      <main
        id="dashboard"
        className="mx-auto w-full max-w-[1320px] flex-1 px-4 py-6 sm:px-6 lg:px-8"
      >
        <Controls
          mode={mode}
          setMode={setMode}
          decisionDate={decisionDate}
          setDecisionDate={setDecisionDate}
          decisionFrom={decisionFrom}
          setDecisionFrom={setDecisionFrom}
          decisionTo={decisionTo}
          setDecisionTo={setDecisionTo}
          cutoff={cutoff}
          setCutoff={setCutoff}
          deliveryDate={mode === "single" ? deliveryDate : undefined}
          onRefresh={loadData}
          loading={loading}
        />

        {error && (
          <div
            role="alert"
            className="mb-5 flex flex-col gap-3 rounded-xl border border-negative/20 bg-negative-soft px-4 py-3.5 text-negative sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle
                className="mt-0.5 h-4 w-4 shrink-0"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              <div>
                <h2 className="text-xs font-semibold text-ink">
                  Could not load evaluation data
                </h2>
                <p className="mt-0.5 text-[11px] leading-relaxed">{error}</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              className="w-full border-negative/25 bg-surface text-negative hover:bg-surface-subtle sm:w-auto"
            >
              <RefreshCw
                className="mr-1.5 h-3.5 w-3.5"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              Retry
            </Button>
          </div>
        )}

        {loading && !metrics && (
          <div className="animate-pulse space-y-5" aria-label="Loading dashboard">
            <div className="h-[132px] rounded-xl border border-line bg-surface" />
            <div className="h-[460px] rounded-xl border border-line bg-surface" />
            <div className="h-[320px] rounded-xl border border-line bg-surface" />
          </div>
        )}

        {!loading && metrics && (
          <>
            {mode === "range" && coverage && (
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface px-4 py-2.5 text-[11px]">
                <div className="flex items-center gap-2 text-ink-soft">
                  <Layers
                    className="h-3.5 w-3.5 text-accent"
                    strokeWidth={1.75}
                    aria-hidden="true"
                  />
                  <span>
                    Range evaluated:{" "}
                    <strong className="font-semibold text-ink tabular-nums">
                      {coverage.total_delivery_days} delivery days
                    </strong>{" "}
                    <span className="text-ink-muted tabular-nums">
                      ({coverage.decision_from} → {coverage.decision_to})
                    </span>
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-ink-muted">
                  <span>
                    Expected{" "}
                    <strong className="font-medium text-ink tabular-nums">
                      {coverage.expected_intervals}
                    </strong>
                  </span>
                  <span>
                    Matched{" "}
                    <strong className="font-medium text-ink tabular-nums">
                      {coverage.matched_intervals}
                    </strong>
                  </span>
                  <span>
                    Coverage{" "}
                    <strong className="font-medium text-ink tabular-nums">
                      {coverage.coverage_pct}%
                    </strong>
                  </span>
                </div>
              </div>
            )}

            <MetricCards metrics={metrics} />

            <ForecastChart
              intervals={intervals}
              hourlyBreakdown={hourlyBreakdown}
              cutoff={cutoff}
            />

            <IntervalTable intervals={intervals} cutoff={cutoff} />

            <ProvenanceCard />
          </>
        )}
      </main>

      <footer className="border-t border-line bg-canvas py-4 text-[11px] text-ink-muted">
        <div className="mx-auto flex max-w-[1320px] flex-col items-center justify-between gap-2 px-4 sm:flex-row sm:px-6 lg:px-8">
          <span>
            UK day-ahead wind forecast accuracy pilot · Elexon BMRS open data
          </span>
          <span className="font-mono text-[10px]">
            FastAPI read-only backend · React + TypeScript + Tailwind
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
