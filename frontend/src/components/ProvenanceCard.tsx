import React from "react";
import { AlertCircle, BookOpen, Clock, ShieldCheck } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";

export const ProvenanceCard: React.FC = () => {
  return (
    <Card className="mb-8">
      <CardHeader className="border-b border-line pb-4">
        <CardTitle className="flex items-center gap-2 text-sm">
          <ShieldCheck
            className="h-4 w-4 text-positive"
            strokeWidth={1.75}
            aria-hidden="true"
          />
          <span>Method and provenance</span>
        </CardTitle>
        <CardDescription>
          How the comparison is assembled, and the limits of this pilot.
        </CardDescription>
      </CardHeader>

      <CardContent className="p-0">
        <div className="grid grid-cols-1 divide-y divide-line md:grid-cols-3 md:divide-x md:divide-y-0">
          <section className="space-y-2.5 p-5 text-xs leading-relaxed text-ink-soft">
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-ink">
              <BookOpen
                className="h-3.5 w-3.5 text-ink-muted"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              Official Elexon datasets
            </h3>
            <p>
              Data is retrieved directly from Elexon BMRS without third-party
              augmentation or synthetic fabrication.
            </p>
            <ul className="space-y-1.5">
              <li>
                <strong className="font-medium text-ink">FUELHH:</strong>{" "}
                half-hourly outturn generation by fuel type, filtered to wind.
              </li>
              <li>
                <strong className="font-medium text-ink">WINDFOR:</strong>{" "}
                national wind generation forecasts, published up to eight times
                daily.
              </li>
            </ul>
          </section>

          <section className="space-y-2.5 p-5 text-xs leading-relaxed text-ink-soft">
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-ink">
              <Clock
                className="h-3.5 w-3.5 text-ink-muted"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              Day-ahead vintage rule
            </h3>
            <p>
              For delivery on day <strong className="text-ink">D</strong>,
              procurement decisions are made on day{" "}
              <strong className="text-ink">D-1</strong>.
            </p>
            <div className="rounded-lg border border-line bg-surface-subtle p-2.5 font-mono text-[11px] text-ink">
              eligible = publishTime ≤ cutoff
              <br />
              selected = max(eligible.publishTime)
            </div>
            <p className="text-[11px]">
              The default cutoff is{" "}
              <strong className="text-ink">15:30 UK time</strong>, aligned with
              the EPEX SPOT UK day-ahead half-hourly auction. It can be changed
              above.
            </p>
          </section>

          <section className="space-y-2.5 p-5 text-xs leading-relaxed text-ink-soft">
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-ink">
              <AlertCircle
                className="h-3.5 w-3.5 text-ink-muted"
                strokeWidth={1.75}
                aria-hidden="true"
              />
              Evaluation and planning margin
            </h3>
            <p>
              <strong className="text-ink">Error</strong> is actual minus
              forecast. Positive values mean actual generation exceeded forecast;
              negative values mean the forecast was higher than outturn.
            </p>
            <p>
              Missing intervals stay missing and are never filled with zero.
              Metrics use matched pairs only.
            </p>
            <p className="text-[11px]">
              <strong className="text-ink">Planning margin</strong> is the 90th
              percentile of absolute error: an empirical MW buffer, not a
              guarantee or trading recommendation.
            </p>
          </section>
        </div>
      </CardContent>
    </Card>
  );
};
