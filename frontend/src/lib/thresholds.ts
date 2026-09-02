export type Status = "good" | "elevated" | "poor" | "unknown";

interface Thresholds {
  good: number; // <= this value is "good"
  elevated: number; // <= this value is "elevated", above is "poor"
}

/**
 * Simple, easy-to-edit thresholds for each metric. These are informal
 * environmental-monitoring bands (not medical guidance) - tune freely.
 */
export const THRESHOLDS: Record<string, Thresholds> = {
  rco2: { good: 800, elevated: 1200 }, // ppm
  pm02: { good: 12, elevated: 35 }, // ug/m3 (PM2.5)
  pm10: { good: 20, elevated: 50 }, // ug/m3
  pm01: { good: 10, elevated: 25 }, // ug/m3
};

export function statusFor(metric: keyof typeof THRESHOLDS, value: number | null): Status {
  if (value === null || Number.isNaN(value)) return "unknown";
  const t = THRESHOLDS[metric];
  if (!t) return "unknown";
  if (value <= t.good) return "good";
  if (value <= t.elevated) return "elevated";
  return "poor";
}

export const STATUS_LABEL: Record<Status, string> = {
  good: "Good",
  elevated: "Elevated",
  poor: "Poor",
  unknown: "No data",
};
