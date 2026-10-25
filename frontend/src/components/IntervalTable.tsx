import React, { useState, useMemo } from "react";
import {
  CheckCircle,
  Download,
  Search,
  SearchX,
  Table as TableIcon,
  TriangleAlert,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { cn } from "@/lib/utils";
import type { IntervalRecord } from "@/types";

interface IntervalTableProps {
  intervals: IntervalRecord[];
  cutoff: string;
}

const numberOne = new Intl.NumberFormat("en-GB", {
  maximumFractionDigits: 1,
});

export const IntervalTable: React.FC<IntervalTableProps> = ({
  intervals,
  cutoff,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const filtered = useMemo(() => {
    return intervals.filter((item) => {
      const matchesSearch =
        item.start_time_utc.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.settlement_date && item.settlement_date.includes(searchTerm)) ||
        (item.settlement_period !== null &&
          `sp ${item.settlement_period}`.includes(searchTerm.toLowerCase()));

      const matchesStatus =
        filterStatus === "ALL" || item.status === filterStatus;

      return matchesSearch && matchesStatus;
    });
  }, [intervals, searchTerm, filterStatus]);

  const totalPages = Math.ceil(filtered.length / pageSize) || 1;
  const safePage = Math.min(currentPage, totalPages);
  const paginated = useMemo(() => {
    const start = (safePage - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  }, [filtered, safePage, pageSize]);

  const clearFilters = () => {
    setSearchTerm("");
    setFilterStatus("ALL");
    setCurrentPage(1);
  };

  const exportCSV = () => {
    const headers = [
      "start_time_utc",
      "settlement_date",
      "settlement_period",
      "forecast_mw",
      "actual_mw",
      "error_mw",
      "forecast_publish_time_utc",
      "status",
    ];
    const rows = filtered.map((it) => [
      it.start_time_utc,
      it.settlement_date ?? "",
      it.settlement_period ?? "",
      it.forecast_mw ?? "",
      it.actual_mw ?? "",
      it.error_mw ?? "",
      it.forecast_publish_time_utc ?? "",
      it.status,
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((r) => r.join(",")),
    ].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `wind_forecast_accuracy_cutoff_${cutoff}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Card className="mb-5">
      <CardHeader className="flex flex-col gap-4 border-b border-line pb-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-sm">
            <TableIcon
              className="h-4 w-4 text-ink-muted"
              strokeWidth={1.75}
              aria-hidden="true"
            />
            <span>Interval evaluation</span>
            <Badge variant="secondary" className="font-mono text-[10px]">
              {filtered.length} intervals
            </Badge>
          </CardTitle>
          <CardDescription>
            Audit individual interval values, forecast vintages and signed
            error.
          </CardDescription>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-ink-muted"
              strokeWidth={1.75}
              aria-hidden="true"
            />
            <input
              type="search"
              placeholder="Search timestamp or SP…"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              aria-label="Search intervals by timestamp or settlement period"
              className="h-8 w-52 rounded-lg border border-line bg-surface-subtle pl-8 pr-3 text-xs text-ink placeholder:text-ink-muted focus:border-accent/40 focus:outline-none focus:ring-2 focus:ring-accent/10"
            />
          </div>

          <Select
            value={filterStatus}
            onValueChange={(value) => {
              setFilterStatus(value);
              setCurrentPage(1);
            }}
          >
            <SelectTrigger
              aria-label="Filter intervals by status"
              className="w-[172px]"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All statuses</SelectItem>
              <SelectItem value="MATCHED">Matched pairs only</SelectItem>
              <SelectItem value="MISSING_FORECAST">
                Missing forecast only
              </SelectItem>
              <SelectItem value="MISSING_ACTUAL">Missing actual only</SelectItem>
            </SelectContent>
          </Select>

          <Button
            size="sm"
            variant="outline"
            onClick={exportCSV}
            className="h-8 gap-1.5 text-xs"
          >
            <Download className="h-3.5 w-3.5" strokeWidth={1.75} />
            <span>Export CSV</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-xs">
            <thead className="border-b border-line bg-surface-subtle text-[10px] uppercase tracking-[0.08em] text-ink-muted">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Delivery start (UTC)
                </th>
                <th scope="col" className="px-3 py-3 font-semibold">
                  Settlement
                </th>
                <th scope="col" className="px-3 py-3 text-right font-semibold">
                  Forecast (MW)
                </th>
                <th scope="col" className="px-3 py-3 text-right font-semibold">
                  Actual (MW)
                </th>
                <th scope="col" className="px-3 py-3 text-right font-semibold">
                  Error (MW)
                </th>
                <th scope="col" className="px-4 py-3 font-semibold">
                  Forecast vintage
                </th>
                <th scope="col" className="px-4 py-3 text-center font-semibold">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {paginated.length > 0 ? (
                paginated.map((item, idx) => {
                  const error = item.error_mw;
                  const isPositive = error !== null && error >= 0;

                  return (
                    <tr
                      key={item.start_time_utc + idx}
                      className="transition-colors hover:bg-surface-subtle"
                    >
                      <td className="px-4 py-2.5 font-mono text-ink tabular-nums">
                        {item.start_time_utc}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-ink-muted tabular-nums">
                        {item.settlement_date ? (
                          <span>
                            {item.settlement_date.slice(5)} · SP{" "}
                            {item.settlement_period}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-medium text-accent tabular-nums">
                        {item.forecast_mw !== null
                          ? numberOne.format(item.forecast_mw)
                          : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-medium text-ink tabular-nums">
                        {item.actual_mw !== null
                          ? numberOne.format(item.actual_mw)
                          : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono font-semibold tabular-nums">
                        {error !== null ? (
                          <span
                            className={cn(
                              isPositive ? "text-positive" : "text-negative",
                            )}
                          >
                            {isPositive ? "+" : ""}
                            {numberOne.format(error)}
                          </span>
                        ) : (
                          <span className="font-normal text-ink-muted">—</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-[11px] text-ink-soft">
                        {item.forecast_publish_time_utc ? (
                          item.forecast_publish_time_utc
                        ) : (
                          <span className="font-sans italic text-ink-muted">
                            No vintage ≤ cutoff
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        {item.status === "MATCHED" ? (
                          <Badge
                            variant="success"
                            className="gap-1 px-1.5 py-0.5 text-[10px]"
                          >
                            <CheckCircle
                              className="h-2.5 w-2.5"
                              strokeWidth={2}
                              aria-hidden="true"
                            />
                            Matched
                          </Badge>
                        ) : (
                          <Badge
                            variant="warning"
                            className="gap-1 px-1.5 py-0.5 text-[10px]"
                          >
                            <TriangleAlert
                              className="h-2.5 w-2.5"
                              strokeWidth={2}
                              aria-hidden="true"
                            />
                            {item.status === "MISSING_FORECAST"
                              ? "No forecast"
                              : "No actual"}
                          </Badge>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-16">
                    <div className="mx-auto flex max-w-sm flex-col items-center gap-3 text-center">
                      <SearchX
                        className="h-6 w-6 text-ink-muted"
                        strokeWidth={1.5}
                        aria-hidden="true"
                      />
                      <div>
                        <p className="text-sm font-medium text-ink">
                          No intervals match this view
                        </p>
                        <p className="mt-1 text-xs leading-relaxed text-ink-muted">
                          Adjust the search or status filter to inspect the
                          interval-level detail.
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={clearFilters}
                      >
                        Clear filters
                      </Button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex flex-col gap-2 border-t border-line bg-surface-subtle px-4 py-3 text-[11px] sm:flex-row sm:items-center sm:justify-between">
            <span className="text-ink-muted">
              Page{" "}
              <strong className="font-semibold text-ink tabular-nums">
                {safePage}
              </strong>{" "}
              of{" "}
              <strong className="font-semibold text-ink tabular-nums">
                {totalPages}
              </strong>{" "}
              · {filtered.length} rows
            </span>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={safePage <= 1}
                onClick={() =>
                  setCurrentPage(Math.max(1, safePage - 1))
                }
                className="h-7 px-2.5 text-[11px]"
              >
                Previous
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={safePage >= totalPages}
                onClick={() =>
                  setCurrentPage(Math.min(totalPages, safePage + 1))
                }
                className="h-7 px-2.5 text-[11px]"
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
