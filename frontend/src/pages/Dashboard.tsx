import { useCallback, useEffect, useMemo, useState } from "react";
import { MetricCard } from "@/components/MetricCard";
import { RangeSelector } from "@/components/RangeSelector";
import { TimeseriesChart, type SeriesConfig } from "@/components/TimeseriesChart";
import { getHealth, getLatestMeasurement, getMeasures, ApiError } from "@/lib/api";
import { normalizeToChartPoints } from "@/lib/chartData";
import { formatDateInput, resolveRange, type DateRange } from "@/lib/dateRange";
import type { ChartPoint, HealthStatus, Measurement, RangeKey } from "@/types/api";

function readRangeFromUrl(): { key: RangeKey; range: DateRange } {
  const params = new URLSearchParams(window.location.search);
  const from = params.get("from");
  const to = params.get("to");
  if (from && to) {
    const range = { from: new Date(from), to: new Date(to) };
    if (!Number.isNaN(range.from.getTime()) && !Number.isNaN(range.to.getTime())) {
      return { key: "custom", range };
    }
  }
  return { key: "today", range: resolveRange("today") };
}

function writeRangeToUrl(range: DateRange) {
  const params = new URLSearchParams({
    from: formatDateInput(range.from),
    to: formatDateInput(range.to),
  });
  const url = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState(null, "", url);
}

export function Dashboard() {
  const initial = useMemo(readRangeFromUrl, []);
  const [rangeKey, setRangeKey] = useState<RangeKey>(initial.key);
  const [range, setRange] = useState<DateRange>(initial.range);

  const [latest, setLatest] = useState<Measurement | null>(null);
  const [latestError, setLatestError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const [points, setPoints] = useState<ChartPoint[]>([]);
  const [chartLoading, setChartLoading] = useState(true);
  const [chartError, setChartError] = useState<string | null>(null);

  const refreshLatest = useCallback(() => {
    getLatestMeasurement()
      .then((m) => {
        setLatest(m);
        setLatestError(null);
      })
      .catch((e) => {
        setLatest(null);
        setLatestError(e instanceof ApiError ? e.message : "Failed to load latest reading");
      });
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    refreshLatest();
    const id = setInterval(refreshLatest, 60_000);
    return () => clearInterval(id);
  }, [refreshLatest]);

  useEffect(() => {
    setChartLoading(true);
    setChartError(null);
    getMeasures(range)
      .then((res) => setPoints(normalizeToChartPoints(res)))
      .catch((e) => {
        setPoints([]);
        setChartError(e instanceof ApiError ? e.message : "Failed to load measurements");
      })
      .finally(() => setChartLoading(false));
  }, [range]);

  function handleRangeKeyChange(key: RangeKey) {
    setRangeKey(key);
    if (key === "custom") return; // wait for explicit dates
    const resolved = resolveRange(key);
    setRange(resolved);
    writeRangeToUrl(resolved);
  }

  function handleCustomChange(from: Date, to: Date) {
    const resolved = { from, to };
    setRange(resolved);
    writeRangeToUrl(resolved);
  }

  const spanDays = Math.max(1, (range.to.getTime() - range.from.getTime()) / 86_400_000);

  const pmSeries: SeriesConfig[] = [
    { key: "pm01", label: "PM1.0", color: "#5B6B64", unit: "µg/m³" },
    { key: "pm02", label: "PM2.5", color: "#2F7A63", unit: "µg/m³" },
    { key: "pm10", label: "PM10", color: "#B4780F", unit: "µg/m³" },
  ];
  const co2Series: SeriesConfig[] = [
    { key: "rco2", label: "CO2", color: "#2F7A63", unit: "ppm", bandMinKey: "rco2Min", bandMaxKey: "rco2Max" },
  ];
  const tempSeries: SeriesConfig[] = [{ key: "atmp", label: "Temperature", color: "#B0402F", unit: "°C" }];
  const humSeries: SeriesConfig[] = [{ key: "rhum", label: "Humidity", color: "#2F6E7A", unit: "%" }];

  return (
    <div className="min-h-screen bg-bg pb-16">
      <header className="border-b border-hairline bg-surface">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <h1 className="font-display text-xl font-semibold text-ink">Home Air Quality</h1>
            {health && (
              <p className="mt-0.5 text-xs text-ink-faint">
                Sensor {health.sensor === "ok" ? "connected" : "unreachable"} · Database{" "}
                {health.database === "ok" ? "connected" : "unreachable"}
              </p>
            )}
          </div>
          <RangeSelector
            value={rangeKey}
            onChange={handleRangeKeyChange}
            customFrom={range.from}
            customTo={range.to}
            onCustomChange={handleCustomChange}
          />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        {latestError && !latest && (
          <div className="mb-6 rounded-sm border border-poor/30 bg-poor-bg px-4 py-3 text-sm text-poor">
            {latestError}
          </div>
        )}

        <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <MetricCard label="CO2" value={latest?.rco2 ?? null} unit="ppm" decimals={0} metric="rco2" />
          <MetricCard
            label="PM2.5"
            value={latest?.pm02_compensated ?? latest?.pm02 ?? null}
            unit="µg/m³"
            metric="pm02"
          />
          <MetricCard label="PM10" value={latest?.pm10 ?? null} unit="µg/m³" metric="pm10" />
          <MetricCard label="PM1.0" value={latest?.pm01 ?? null} unit="µg/m³" metric="pm01" />
          <MetricCard
            label="Temperature"
            value={latest?.atmp_compensated ?? latest?.atmp ?? null}
            unit="°C"
          />
          <MetricCard
            label="Humidity"
            value={latest?.rhum_compensated ?? latest?.rhum ?? null}
            unit="%"
            decimals={0}
          />
        </section>

        <section className="mt-8 space-y-5">
          <TimeseriesChart
            title="CO2"
            data={points}
            series={co2Series}
            loading={chartLoading}
            error={chartError}
            spanDays={spanDays}
          />
          <TimeseriesChart
            title="Particulate matter (PM1.0 / PM2.5 / PM10)"
            data={points}
            series={pmSeries}
            loading={chartLoading}
            error={chartError}
            spanDays={spanDays}
          />
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <TimeseriesChart
              title="Temperature"
              data={points}
              series={tempSeries}
              loading={chartLoading}
              error={chartError}
              spanDays={spanDays}
            />
            <TimeseriesChart
              title="Humidity"
              data={points}
              series={humSeries}
              loading={chartLoading}
              error={chartError}
              spanDays={spanDays}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
