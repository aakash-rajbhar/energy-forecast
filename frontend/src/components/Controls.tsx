import React from "react";
import {
  ArrowRight,
  Calendar,
  Clock,
  Filter,
  SlidersHorizontal,
} from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { cn } from "@/lib/utils";

interface ControlsProps {
  mode: "single" | "range";
  setMode: (m: "single" | "range") => void;
  decisionDate: string;
  setDecisionDate: (d: string) => void;
  decisionFrom: string;
  setDecisionFrom: (d: string) => void;
  decisionTo: string;
  setDecisionTo: (d: string) => void;
  cutoff: string;
  setCutoff: (c: string) => void;
  deliveryDate?: string;
  onRefresh: () => void;
  loading: boolean;
}

const fieldClass =
  "flex items-center gap-2 rounded-lg border border-line bg-surface-subtle px-2.5 py-2 transition-colors focus-within:border-accent/40 focus-within:ring-2 focus-within:ring-accent/10";

const labelClass = "text-[11px] font-medium text-ink-muted";

const inputClass =
  "w-full min-w-0 bg-transparent text-xs font-medium text-ink tabular-nums focus-visible:outline-none";

const presetClass =
  "rounded-md border px-2 py-1.5 text-[11px] font-medium transition-colors";

const presetActive =
  "border-accent/20 bg-accent-soft text-accent";
const presetIdle =
  "border-transparent text-ink-soft hover:border-line hover:bg-surface-subtle hover:text-ink";

export const Controls: React.FC<ControlsProps> = ({
  mode,
  setMode,
  decisionDate,
  setDecisionDate,
  decisionFrom,
  setDecisionFrom,
  decisionTo,
  setDecisionTo,
  cutoff,
  setCutoff,
  deliveryDate,
  onRefresh,
  loading,
}) => {
  return (
    <Card className="mb-5">
      <CardContent className="p-4 sm:p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-end gap-2.5">
              <div>
                <span className={cn(labelClass, "mb-1.5 block")}>View</span>
                <div
                  role="group"
                  aria-label="Evaluation mode"
                  className="inline-flex rounded-lg border border-line bg-surface-sunken p-0.5"
                >
                  <button
                    type="button"
                    onClick={() => setMode("single")}
                    aria-pressed={mode === "single"}
                    className={cn(
                      "rounded-md min-h-8 px-3 py-1.5 text-[11px] font-medium transition-colors",
                      mode === "single"
                        ? "bg-surface text-ink shadow-sm"
                        : "text-ink-soft hover:text-ink",
                    )}
                  >
                    Single day
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode("range")}
                    aria-pressed={mode === "range"}
                    className={cn(
                      "rounded-md min-h-8 px-3 py-1.5 text-[11px] font-medium transition-colors",
                      mode === "range"
                        ? "bg-surface text-ink shadow-sm"
                        : "text-ink-soft hover:text-ink",
                    )}
                  >
                    Date range
                  </button>
                </div>
              </div>

              {mode === "single" ? (
                <>
                  <div>
                    <span className={cn(labelClass, "mb-1.5 block")}>
                      Decision date
                    </span>
                    <label className={fieldClass}>
                      <Calendar
                        className="h-3.5 w-3.5 shrink-0 text-ink-muted"
                        strokeWidth={1.75}
                      />
                      <input
                        type="date"
                        value={decisionDate}
                        min="2025-12-30"
                        max="2026-02-01"
                        onChange={(e) => setDecisionDate(e.target.value)}
                        className={cn(inputClass, "cursor-pointer")}
                      />
                    </label>
                  </div>

                  {deliveryDate && (
                    <div className="hidden items-center gap-1.5 pb-2 text-[11px] text-ink-soft sm:flex">
                      <ArrowRight
                        className="h-3 w-3 text-ink-muted"
                        strokeWidth={1.75}
                      />
                      <span>
                        Delivery{" "}
                        <strong className="font-semibold text-ink tabular-nums">
                          {deliveryDate}
                        </strong>
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div>
                    <span className={cn(labelClass, "mb-1.5 block")}>From</span>
                    <label className={fieldClass}>
                      <Calendar
                        className="h-3.5 w-3.5 shrink-0 text-ink-muted"
                        strokeWidth={1.75}
                      />
                      <input
                        type="date"
                        value={decisionFrom}
                        min="2025-12-30"
                        max="2026-02-01"
                        onChange={(e) => setDecisionFrom(e.target.value)}
                        className={cn(inputClass, "cursor-pointer")}
                      />
                    </label>
                  </div>
                  <div>
                    <span className={cn(labelClass, "mb-1.5 block")}>To</span>
                    <label className={fieldClass}>
                      <Calendar
                        className="h-3.5 w-3.5 shrink-0 text-ink-muted"
                        strokeWidth={1.75}
                      />
                      <input
                        type="date"
                        value={decisionTo}
                        min="2025-12-30"
                        max="2026-02-01"
                        onChange={(e) => setDecisionTo(e.target.value)}
                        className={cn(inputClass, "cursor-pointer")}
                      />
                    </label>
                  </div>
                </>
              )}

              <div>
                <span className={cn(labelClass, "mb-1.5 block")}>
                  Procurement cutoff
                </span>
                <label className={cn(fieldClass, "w-[132px]")}>
                  <Clock
                    className="h-3.5 w-3.5 shrink-0 text-ink-muted"
                    strokeWidth={1.75}
                  />
                  <input
                    type="text"
                    inputMode="numeric"
                    pattern="^([01]\d|2[0-3]):[0-5]\d$"
                    value={cutoff}
                    onChange={(e) => setCutoff(e.target.value)}
                    placeholder="15:30"
                    aria-label="Procurement cutoff time in UTC"
                    className={cn(inputClass, "text-center font-semibold")}
                  />
                  <span className="text-[10px] font-medium text-ink-muted">
                    UTC
                  </span>
                </label>
              </div>
            </div>
          </div>

          <Button
            onClick={onRefresh}
            disabled={loading}
            size="sm"
            className="w-full gap-2 xl:w-auto"
          >
            <Filter className="h-3.5 w-3.5" strokeWidth={1.75} />
            <span>{loading ? "Evaluating…" : "Apply cutoff"}</span>
          </Button>
        </div>

        <div className="mt-4 flex flex-col gap-3 border-t border-line pt-3.5 text-[11px] lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 inline-flex items-center gap-1.5 text-ink-muted">
              <SlidersHorizontal
                className="h-3 w-3"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              Cutoff presets
            </span>
            {[
              ["15:30", "15:30 · EPEX half-hourly"],
              ["12:00", "12:00 · Day-ahead auction"],
              ["09:00", "09:00 · Morning run"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => setCutoff(value)}
                aria-pressed={cutoff === value}
                className={cn(
                  presetClass,
                  cutoff === value ? presetActive : presetIdle,
                )}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-ink-muted">
              {mode === "single" ? "Jump to date" : "Range presets"}
            </span>
            {mode === "single" ? (
              <>
                <button
                  type="button"
                  onClick={() => setDecisionDate("2026-01-14")}
                  className={cn(presetClass, presetIdle)}
                >
                  14 Jan · Storm event
                </button>
                <button
                  type="button"
                  onClick={() => setDecisionDate("2026-01-20")}
                  className={cn(presetClass, presetIdle)}
                >
                  20 Jan · High wind
                </button>
                <button
                  type="button"
                  onClick={() => setDecisionDate("2026-01-01")}
                  className={cn(presetClass, presetIdle)}
                >
                  1 Jan · New Year
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setDecisionFrom("2026-01-01");
                    setDecisionTo("2026-01-31");
                  }}
                  className={cn(presetClass, presetIdle)}
                >
                  Full month · 1–31 Jan
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setDecisionFrom("2026-01-01");
                    setDecisionTo("2026-01-07");
                  }}
                  className={cn(presetClass, presetIdle)}
                >
                  Week 1
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setDecisionFrom("2026-01-08");
                    setDecisionTo("2026-01-14");
                  }}
                  className={cn(presetClass, presetIdle)}
                >
                  Week 2
                </button>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
