import type { HealthStatus, Measurement, MeasuresResponse } from "@/types/api";
import type { DateRange } from "@/lib/dateRange";
import { rangeToSearchParams } from "@/lib/dateRange";

// In dev, Vite proxies /api -> the backend (see vite.config.ts).
// In production, nginx (see frontend/Dockerfile + nginx.conf) does the same,
// so the frontend never needs to know the backend's real address.
const BASE = "/api";

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new ApiError("Could not reach the API. Is the backend running?");
  }
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore body parse errors */
    }
    throw new ApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

export function getLatestMeasurement(): Promise<Measurement> {
  return request<Measurement>("/measures/latest");
}

export function getMeasures(range: DateRange): Promise<MeasuresResponse> {
  const params = rangeToSearchParams(range);
  return request<MeasuresResponse>(`/measures?${params.toString()}`);
}

export function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/health");
}

export { ApiError };
