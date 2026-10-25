import React from "react";
import {
  Activity,
  AlertCircle,
  Layers,
  Percent,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { MetricSummary } from "@/types";

interface MetricCardsProps {
  metrics: MetricSummary;
}

const numberZero = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 0,
});

const numberOne = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 1,
});

function formatMw(value: number | null): string {
  return value === null ? "—" : numberZero.format(value);
}

function formatPct(value: number | null): string {
  return value === null ? "—" : `${numberOne.format(value)}%`;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ metrics }) => {
  const bias = metrics.bias_mw;
  const isBiasPositive = bias !== null && bias >= 0;
  const isOverforecastHeavy = (metrics.overforecast_share_pct ?? 0) > 50;
  const hasPartialCoverage = metrics.coverage_pct < 100;

  const items = [
    {
      label: "MAE",
      value: formatMw(metrics.mae_mw),
      unit: "MW",
      helper: "Mean absolute error",
      icon: Activity,
    },
    {
      label: "RMSE",
      value: formatMw(metrics.rmse_mw),
      unit: "MW",
      helper: "Penalises large errors",
      icon: AlertCircle,
    },
    {
      label: "Mean bias",
      value:
        bias === null
          ? "—"
          : `${isBiasPositive ? "+" : ""}${formatMw(bias)}`,
      unit: "MW",
      helper:
        bias === null
          ? "Actual minus forecast"
          : isBiasPositive
            ? "Actual exceeded forecast"
            : "Forecast exceeded actual",
      icon: isBiasPositive ? TrendingUp : TrendingDown,
      valueClass: isBiasPositive ? "text-positive" : "text-negative",
    },
    {
      label: "Overforecast share",
      value: formatPct(metrics.overforecast_share_pct),
      unit: null,
      helper:
        metrics.overforecast_share_pct === null
          ? "Share of intervals above forecast"
          : isOverforecastHeavy
            ? "Majority of intervals overforecast"
            : "Majority of intervals underforecast",
      icon: Percent,
      valueClass: isOverforecastHeavy ? "text-warning" : undefined,
    },
    {
      label: "Planning margin",
      value: formatMw(metrics.p90_abs_error_mw),
      unit: "MW",
      helper: "P90 absolute error buffer",
      icon: ShieldAlert,
    },
    {
      label: "Coverage",
      value: formatPct(metrics.coverage_pct),
      unit: null,
      helper: `${metrics.matched_count} of ${metrics.expected_count} intervals matched`,
      icon: Layers,
      valueClass: hasPartialCoverage ? "text-warning" : undefined,
    },
  ];

  return (
    <section
      aria-labelledby="summary-heading"
      className="mb-5 overflow-hidden rounded-xl border border-line bg-surface shadow-[0_1px_2px_rgba(28,27,25,0.04)]"
    >
      <div className="flex flex-col gap-2 border-b border-line px-5 py-3.5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2
            id="summary-heading"
            className="text-sm font-semibold tracking-tight text-ink"
          >
            Forecast error summary
          </h2>
          <p className="mt-0.5 text-[11px] text-ink-muted">
            Error = actual − forecast · matched pairs only · MW
          </p>
        </div>
        <div className="text-[11px] text-ink-soft">
          <span className="font-semibold text-ink tabular-nums">
            {metrics.matched_count}
          </span>{" "}
          of{" "}
          <span className="tabular-nums">{metrics.expected_count}</span>{" "}
          intervals matched
          <span className="mx-1.5 text-line-strong" aria-hidden="true">
            /
          </span>
          <span
            className={cn(
              "font-semibold tabular-nums",
              hasPartialCoverage ? "text-warning" : "text-positive",
            )}
          >
            {formatPct(metrics.coverage_pct)}
          </span>{" "}
          coverage
        </div>
      </div>

      <div className="grid grid-cols-2 gap-px bg-line md:grid-cols-3 xl:grid-cols-6">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="bg-surface px-5 py-4">
              <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-ink-muted">
                <Icon
                  className="h-3.5 w-3.5 text-ink-muted"
                  strokeWidth={1.75}
                  aria-hidden="true"
                />
                {item.label}
              </div>
              <div className="mt-2.5 flex items-baseline gap-1">
                <span
                  className={cn(
                    "text-[26px] font-semibold leading-none tracking-[-0.02em] text-ink tabular-nums",
                    item.valueClass,
                  )}
                >
                  {item.value}
                </span>
                {item.unit && (
                  <span className="text-[11px] font-medium text-ink-muted">
                    {item.unit}
                  </span>
                )}
              </div>
              <p className="mt-2 text-[11px] leading-snug text-ink-muted">
                {item.helper}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
};
