import { describe, expect, it } from "vitest";
import { normalizeToChartPoints } from "@/lib/chartData";
import type { MeasuresResponse } from "@/types/api";

describe("normalizeToChartPoints", () => {
  it("prefers compensated PM2.5/temp/humidity for raw points", () => {
    const response: MeasuresResponse = {
      resolution: "raw",
      from_ts: "2026-09-02T00:00:00Z",
      to_ts: "2026-09-02T01:00:00Z",
      raw: [
        {
          id: 1,
          bucket_ts: "2026-09-02T00:00:00Z",
          measured_at: "2026-09-02T00:00:05Z",
          pm01: 3.0,
          pm02: 4.0,
          pm10: 5.0,
          pm003_count: 100,
          pm02_compensated: 4.5,
          atmp: 20.0,
          atmp_compensated: 20.5,
          rhum: 40.0,
          rhum_compensated: 41.0,
          rco2: 500,
          wifi: -60,
        },
      ],
      aggregated: [],
    };

    const points = normalizeToChartPoints(response);

    expect(points).toHaveLength(1);
    expect(points[0].pm02).toBe(4.5);
    expect(points[0].atmp).toBe(20.5);
    expect(points[0].rhum).toBe(41.0);
  });

  it("maps aggregated points including min/max bands", () => {
    const response: MeasuresResponse = {
      resolution: "aggregated",
      from_ts: "2026-08-01T00:00:00Z",
      to_ts: "2026-08-10T00:00:00Z",
      raw: [],
      aggregated: [
        {
          bucket_ts: "2026-08-01T00:00:00Z",
          pm01_avg: 2.0,
          pm02_avg: 3.0,
          pm02_min: 2.0,
          pm02_max: 4.0,
          pm10_avg: 6.0,
          rco2_avg: 500,
          rco2_min: 450,
          rco2_max: 600,
          atmp_avg: 21.0,
          rhum_avg: 42.0,
          sample_count: 4,
        },
      ],
    };

    const points = normalizeToChartPoints(response);

    expect(points).toHaveLength(1);
    expect(points[0].pm02Min).toBe(2.0);
    expect(points[0].pm02Max).toBe(4.0);
    expect(points[0].rco2).toBe(500);
  });
});
