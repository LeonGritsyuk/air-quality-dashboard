export interface Measurement {
  id: number;
  bucket_ts: string;
  measured_at: string;
  pm01: number | null;
  pm02: number | null;
  pm10: number | null;
  pm003_count: number | null;
  pm02_compensated: number | null;
  atmp: number | null;
  atmp_compensated: number | null;
  rhum: number | null;
  rhum_compensated: number | null;
  rco2: number | null;
  wifi: number | null;
}

export interface AggregatedPoint {
  bucket_ts: string;
  pm01_avg: number | null;
  pm02_avg: number | null;
  pm02_min: number | null;
  pm02_max: number | null;
  pm10_avg: number | null;
  rco2_avg: number | null;
  rco2_min: number | null;
  rco2_max: number | null;
  atmp_avg: number | null;
  rhum_avg: number | null;
  sample_count: number;
}

export interface MeasuresResponse {
  resolution: "raw" | "aggregated";
  from_ts: string;
  to_ts: string;
  raw: Measurement[];
  aggregated: AggregatedPoint[];
}

export interface HealthStatus {
  status: string;
  database: string;
  sensor: string;
  last_measurement_at: string | null;
  timezone: string;
}

/** A single point normalized for charting, regardless of raw/aggregated source. */
export interface ChartPoint {
  ts: string;
  pm01: number | null;
  pm02: number | null;
  pm02Min: number | null;
  pm02Max: number | null;
  pm10: number | null;
  rco2: number | null;
  rco2Min: number | null;
  rco2Max: number | null;
  atmp: number | null;
  rhum: number | null;
}

export type RangeKey = "today" | "yesterday" | "7d" | "30d" | "custom";
