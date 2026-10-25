import React, { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  BarChart,
  Bar,
  ReferenceLine,
} from "recharts";
import type { TooltipContentProps } from "recharts";
import {
  BarChart3,
  Info,
  LineChart as LineChartIcon,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "./ui/card";
import { cn } from "@/lib/utils";
import type { HourlyMetric, IntervalRecord } from "@/types";

interface ForecastChartProps {
  intervals: IntervalRecord[];
  hourlyBreakdown: HourlyMetric[];
  cutoff: string;
}

type ChartTooltipProps = Partial<
  Pick<TooltipContentProps<number, string>, "active" | "payload">
>;

interface TimeseriesPoint {
  time: string;
  rawTime: string;
  settlementPeriod: number | null;
  actual: number | null;
  forecast: number | null;
  error: number | null;
  publishTime: string | null;
}

const CHART = {
  grid: "#e7e3db",
  axis: "#6f6962",
  actual: "#1c1b19",
  forecast: "#0e5c4f",
  mae: "#0e5c4f",
  bias: "#b45309",
  reference: "#c9c3b8",
  tooltipBorder: "#e5e1d9",
};

const numberOne = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 1,
});

function formatMw(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "Missing"
    : `${numberOne.format(value)} MW`;
}

const toggleBase =
  "flex min-h-7 items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors";
const toggleSelected = "bg-surface text-ink shadow-sm";
const toggleIdle = "text-ink-soft hover:text-ink";

export const ForecastChart: React.FC<ForecastChartProps> = ({
  intervals,
  hourlyBreakdown,
  cutoff,
}) => {
  const [chartView, setChartView] = useState<"timeseries" | "hourly">(
    "timeseries",
  );

  const formattedTimeseries: TimeseriesPoint[] = intervals.map((item) => ({
    time: `${item.start_time_utc.slice(5, 10)} ${item.start_time_utc.slice(11, 16)}`,
    rawTime: item.start_time_utc,
    settlementPeriod: item.settlement_period,
    actual: item.actual_mw,
    forecast: item.forecast_mw,
    error: item.error_mw,
    publishTime: item.forecast_publish_time_utc,
  }));

  return (
    <Card className="mb-5">
      <CardHeader className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-sm">
            <span>Generation vs eligible forecast</span>
            <span className="rounded border border-line bg-surface-subtle px-1.5 py-0.5 text-[10px] font-medium text-ink-muted">
              MW · UTC
            </span>
          </CardTitle>
          <CardDescription>
            {chartView === "timeseries"
              ? `Delivery interval actual generation compared with the newest forecast published at or before ${cutoff} UTC.`
              : "Average absolute error and signed bias by delivery hour. Positive bias means actual generation exceeded forecast."}
          </CardDescription>
        </div>

        <div
          role="group"
          aria-label="Chart view"
          className="inline-flex shrink-0 rounded-lg border border-line bg-surface-sunken p-0.5"
        >
          <button
            type="button"
            onClick={() => setChartView("timeseries")}
            aria-pressed={chartView === "timeseries"}
            className={cn(
              toggleBase,
              chartView === "timeseries" ? toggleSelected : toggleIdle,
            )}
          >
            <LineChartIcon className="h-3.5 w-3.5" strokeWidth={1.75} />
            Time series
          </button>
          <button
            type="button"
            onClick={() => setChartView("hourly")}
            aria-pressed={chartView === "hourly"}
            className={cn(
              toggleBase,
              chartView === "hourly" ? toggleSelected : toggleIdle,
            )}
          >
            <BarChart3 className="h-3.5 w-3.5" strokeWidth={1.75} />
            Hourly profile
          </button>
        </div>
      </CardHeader>

      <CardContent className="pt-5">
        {chartView === "timeseries" ? (
          <div
            className="h-[360px] w-full"
            role="img"
            aria-label={`Line chart of actual wind generation and the forecast available at ${cutoff} UTC across ${intervals.length} delivery intervals. Interval values are also listed in the table below.`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={formattedTimeseries}
                margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="2 4"
                  stroke={CHART.grid}
                  vertical={false}
                />
                <XAxis
                  dataKey="time"
                  stroke={CHART.axis}
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: CHART.grid }}
                  tickMargin={8}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke={CHART.axis}
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tickMargin={6}
                  width={72}
                  tickFormatter={(value: number) =>
                    `${Math.round(value).toLocaleString("en-GB")} MW`
                  }
                  domain={["auto", "auto"]}
                />
                <Tooltip
                  content={<CustomTooltip />}
                  cursor={{ stroke: CHART.reference, strokeWidth: 1 }}
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  height={30}
                  iconType="plainline"
                  wrapperStyle={{ fontSize: "11px" }}
                  formatter={(value: string) => (
                    <span className="text-ink-soft">{value}</span>
                  )}
                />
                <Line
                  type="monotone"
                  name="Actual generation"
                  dataKey="actual"
                  stroke={CHART.actual}
                  strokeWidth={2.25}
                  dot={false}
                  activeDot={{ r: 4, fill: CHART.actual, strokeWidth: 0 }}
                  connectNulls={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  name={`Cutoff forecast (≤ ${cutoff})`}
                  dataKey="forecast"
                  stroke={CHART.forecast}
                  strokeWidth={2}
                  strokeDasharray="5 3"
                  dot={false}
                  activeDot={{ r: 4, fill: CHART.forecast, strokeWidth: 0 }}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div
            className="h-[360px] w-full"
            role="img"
            aria-label={`Bar chart of hourly mean absolute error and signed bias across delivery hours. Values are also available in the interval table below.`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={hourlyBreakdown}
                margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
              >
                <CartesianGrid
                  strokeDasharray="2 4"
                  stroke={CHART.grid}
                  vertical={false}
                />
                <XAxis
                  dataKey="hour"
                  stroke={CHART.axis}
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: CHART.grid }}
                  tickMargin={8}
                  tickFormatter={(hour: number) =>
                    `${hour.toString().padStart(2, "0")}:00`
                  }
                />
                <YAxis
                  stroke={CHART.axis}
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tickMargin={6}
                  width={64}
                  tickFormatter={(value: number) =>
                    `${Math.round(value).toLocaleString("en-GB")} MW`
                  }
                />
                <ReferenceLine y={0} stroke={CHART.reference} />
                <Tooltip content={<HourlyTooltip />} cursor={{ fill: "#f4f3ef" }} />
                <Legend
                  verticalAlign="top"
                  align="right"
                  height={30}
                  wrapperStyle={{ fontSize: "11px" }}
                  formatter={(value: string) => (
                    <span className="text-ink-soft">{value}</span>
                  )}
                />
                <Bar
                  dataKey="mae_mw"
                  name="Mean absolute error"
                  fill={CHART.mae}
                  radius={[3, 3, 0, 0]}
                  isAnimationActive={false}
                />
                <Bar
                  dataKey="bias_mw"
                  name="Signed bias (actual − forecast)"
                  fill={CHART.bias}
                  radius={[3, 3, 0, 0]}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="mt-4 flex flex-col gap-1.5 border-t border-line pt-3 text-[11px] text-ink-muted sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5">
            <Info
              className="h-3.5 w-3.5 shrink-0 text-ink-muted"
              strokeWidth={1.75}
              aria-hidden="true"
            />
            <span>
              Chart gaps indicate missing data. Zero values are never
              substituted for missing intervals.
            </span>
          </div>
          <span className="font-mono text-[10px]">Timezone: UTC / settlement GMT</span>
        </div>
      </CardContent>
    </Card>
  );
};

const CustomTooltip = ({ active, payload }: ChartTooltipProps) => {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload as TimeseriesPoint | undefined;
  if (!point) return null;

  const isUnder = point.error !== null && point.error >= 0;

  return (
    <div className="min-w-[210px] rounded-lg border border-line bg-surface p-3 text-xs shadow-lg">
      <div className="flex items-center justify-between gap-4 border-b border-line pb-2">
        <span className="font-semibold text-ink tabular-nums">
          {point.rawTime.replace("T", " ").replace("Z", " UTC")}
        </span>
        <span className="font-mono text-[10px] text-ink-muted">
          SP {point.settlementPeriod ?? "—"}
        </span>
      </div>

      <div className="mt-2 space-y-1.5">
        <div className="flex items-center justify-between gap-6">
          <span className="text-ink-soft">Actual</span>
          <span className="font-mono font-medium text-ink tabular-nums">
            {formatMw(point.actual)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-6">
          <span className="text-ink-soft">Cutoff forecast</span>
          <span className="font-mono font-medium text-ink tabular-nums">
            {formatMw(point.forecast)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-6 border-t border-line pt-1.5">
          <span className="text-ink-soft">Error (actual − forecast)</span>
          <span
            className={cn(
              "font-mono font-semibold tabular-nums",
              point.error === null
                ? "text-ink-muted"
                : isUnder
                  ? "text-positive"
                  : "text-negative",
            )}
          >
            {point.error === null
              ? "Missing"
              : `${point.error > 0 ? "+" : ""}${numberOne.format(point.error)} MW`}
          </span>
        </div>
      </div>

      {point.publishTime && (
        <p className="mt-2 border-t border-line pt-1.5 font-mono text-[10px] text-ink-muted">
          Published {point.publishTime}
        </p>
      )}
    </div>
  );
};

const HourlyTooltip = ({ active, payload }: ChartTooltipProps) => {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload as HourlyMetric | undefined;
  if (!point) return null;

  return (
    <div className="rounded-lg border border-line bg-surface p-3 text-xs shadow-lg">
      <div className="border-b border-line pb-1.5 font-semibold text-ink tabular-nums">
        {point.hour.toString().padStart(2, "0")}:00 UTC
      </div>
      <div className="mt-2 space-y-1">
        <div className="flex items-center justify-between gap-6">
          <span className="text-ink-soft">MAE</span>
          <span className="font-mono font-medium text-ink tabular-nums">
            {formatMw(point.mae_mw)}
          </span>
        </div>
        <div className="flex items-center justify-between gap-6">
          <span className="text-ink-soft">Bias</span>
          <span className="font-mono font-medium text-ink tabular-nums">
            {point.bias_mw === null
              ? "Missing"
              : `${point.bias_mw > 0 ? "+" : ""}${numberOne.format(point.bias_mw)} MW`}
          </span>
        </div>
        <div className="mt-1 flex items-center justify-between gap-6 border-t border-line pt-1.5 text-[10px] text-ink-muted">
          <span>Mean actual / forecast</span>
          <span className="font-mono tabular-nums">
            {point.mean_actual_mw === null
              ? "—"
              : numberOne.format(point.mean_actual_mw)}{" "}
            /{" "}
            {point.mean_forecast_mw === null
              ? "—"
              : numberOne.format(point.mean_forecast_mw)}{" "}
            MW
          </span>
        </div>
      </div>
    </div>
  );
};
