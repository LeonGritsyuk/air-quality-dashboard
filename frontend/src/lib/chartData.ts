import type { ChartPoint, MeasuresResponse } from "@/types/api";

export function normalizeToChartPoints(response: MeasuresResponse): ChartPoint[] {
  if (response.resolution === "raw") {
    return response.raw.map((m) => ({
      ts: m.bucket_ts,
      pm01: m.pm01,
      pm02: m.pm02_compensated ?? m.pm02,
      pm02Min: null,
      pm02Max: null,
      pm10: m.pm10,
      rco2: m.rco2,
      rco2Min: null,
      rco2Max: null,
      atmp: m.atmp_compensated ?? m.atmp,
      rhum: m.rhum_compensated ?? m.rhum,
    }));
  }

  return response.aggregated.map((a) => ({
    ts: a.bucket_ts,
    pm01: a.pm01_avg,
    pm02: a.pm02_avg,
    pm02Min: a.pm02_min,
    pm02Max: a.pm02_max,
    pm10: a.pm10_avg,
    rco2: a.rco2_avg,
    rco2Min: a.rco2_min,
    rco2Max: a.rco2_max,
    atmp: a.atmp_avg,
    rhum: a.rhum_avg,
  }));
}
