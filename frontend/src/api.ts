import type {
  CoverageSummary,
  HealthResponse,
  OverviewResponse,
  TimeseriesResponse,
} from "./types";

const BASE_URL = "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    let errorDetail = `API request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // fallback
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export async function fetchOverview(
  decisionDate: string,
  cutoff: string,
): Promise<OverviewResponse> {
  const params = new URLSearchParams({
    decision_date: decisionDate,
    cutoff: cutoff,
  });
  return request<OverviewResponse>(`/api/overview?${params.toString()}`);
}

export async function fetchTimeseries(
  decisionFrom: string,
  decisionTo: string,
  cutoff: string,
): Promise<TimeseriesResponse> {
  const params = new URLSearchParams({
    decision_from: decisionFrom,
    decision_to: decisionTo,
    cutoff: cutoff,
  });
  return request<TimeseriesResponse>(`/api/timeseries?${params.toString()}`);
}

export async function fetchCoverage(
  decisionFrom: string,
  decisionTo: string,
): Promise<CoverageSummary> {
  const params = new URLSearchParams({
    decision_from: decisionFrom,
    decision_to: decisionTo,
  });
  return request<CoverageSummary>(`/api/coverage?${params.toString()}`);
}
