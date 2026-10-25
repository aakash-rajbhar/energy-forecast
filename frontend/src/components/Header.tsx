import React from "react";
import { CalendarRange, Clock, Database, Wind } from "lucide-react";
import { Badge } from "./ui/badge";
import type { HealthResponse } from "@/types";

interface HeaderProps {
  health: HealthResponse | null;
  cutoff: string;
}

export const Header: React.FC<HeaderProps> = ({ health, cutoff }) => {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-canvas/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1320px] flex-col gap-3 px-4 py-3 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ink text-surface shadow-sm">
            <Wind className="h-[18px] w-[18px]" strokeWidth={1.75} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-[15px] font-semibold tracking-[-0.01em] text-ink">
                UK Wind Forecast Accuracy
              </h1>
              <Badge
                variant="outline"
                className="px-1.5 py-0 text-[9px] uppercase tracking-[0.12em]"
              >
                Pilot
              </Badge>
            </div>
            <p className="text-[11px] text-ink-muted">
              Day-ahead wind forecast vs. actual · Elexon BMRS
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-ink-soft">
          <span className="inline-flex items-center gap-1.5">
            <Database
              className="h-3.5 w-3.5 text-ink-muted"
              strokeWidth={1.75}
            />
            {health ? (
              <span>
                <span className="font-medium text-ink tabular-nums">
                  {health.actual_records_count.toLocaleString("en-GB")}
                </span>{" "}
                actuals
                <span className="mx-1 text-line-strong">/</span>
                <span className="font-medium text-ink tabular-nums">
                  {health.distinct_forecast_vintages}
                </span>{" "}
                vintages
              </span>
            ) : (
              <span>Dataset status unavailable</span>
            )}
          </span>

          {health?.available_decision_from && health?.available_decision_to && (
            <span className="hidden items-center gap-1.5 text-ink-muted sm:inline-flex">
              <CalendarRange className="h-3.5 w-3.5" strokeWidth={1.75} />
              <span className="tabular-nums">
                {health.available_decision_from} → {health.available_decision_to}
              </span>
            </span>
          )}

          <span className="inline-flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-ink-muted" strokeWidth={1.75} />
            Cutoff
            <strong className="font-semibold text-ink tabular-nums">
              {cutoff} UTC
            </strong>
          </span>

          <span className="inline-flex items-center gap-1.5 text-positive">
            <span
              className="h-1.5 w-1.5 rounded-full bg-positive"
              aria-hidden="true"
            />
            Elexon BMRS
          </span>
        </div>
      </div>
    </header>
  );
};
