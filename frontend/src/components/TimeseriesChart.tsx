import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChartPoint } from "@/types/api";

export interface SeriesConfig {
  key: keyof ChartPoint;
  label: string;
  color: string;
  unit: string;
  bandMinKey?: keyof ChartPoint;
  bandMaxKey?: keyof ChartPoint;
}

interface Props {
  title: string;
  data: ChartPoint[];
  series: SeriesConfig[];
  loading: boolean;
  error: string | null;
  spanDays: number;
}

function tickFormatter(spanDays: number) {
  return (value: string) => {
    const date = new Date(value);
    return spanDays <= 1 ? format(date, "HH:mm") : format(date, "MMM d");
  };
}

function tooltipLabelFormatter(spanDays: number) {
  return (value: string) => format(new Date(value), spanDays <= 1 ? "MMM d, HH:mm" : "MMM d, yyyy HH:mm");
}

export function TimeseriesChart({ title, data, series, loading, error, spanDays }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="pt-1">
        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : error ? (
          <div className="flex h-64 flex-col items-center justify-center gap-1 text-center">
            <p className="text-sm font-medium text-ink">Couldn't load this chart</p>
            <p className="text-xs text-ink-faint">{error}</p>
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center gap-1 text-center">
            <p className="text-sm font-medium text-ink">No measurements in this range</p>
            <p className="text-xs text-ink-faint">
              Once the collector records a reading here, it will show up automatically.
            </p>
          </div>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                <CartesianGrid stroke="#DCE4E1" vertical={false} />
                <XAxis
                  dataKey="ts"
                  tickFormatter={tickFormatter(spanDays)}
                  tick={{ fontSize: 12, fill: "#5B6B64" }}
                  axisLine={{ stroke: "#DCE4E1" }}
                  tickLine={false}
                  minTickGap={32}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "#5B6B64" }}
                  axisLine={false}
                  tickLine={false}
                  width={40}
                />
                <Tooltip
                  labelFormatter={tooltipLabelFormatter(spanDays)}
                  contentStyle={{
                    borderRadius: 6,
                    border: "1px solid #DCE4E1",
                    fontSize: 13,
                  }}
                  formatter={(value: number, name: string) => {
                    const s = series.find((s) => s.label === name);
                    return [`${value?.toFixed?.(1) ?? value} ${s?.unit ?? ""}`, name];
                  }}
                />
                {series.map(
                  (s) =>
                    s.bandMinKey &&
                    s.bandMaxKey && (
                      <Area
                        key={`${String(s.key)}-band`}
                        dataKey={s.bandMaxKey as string}
                        stroke="none"
                        fill={s.color}
                        fillOpacity={0.08}
                        isAnimationActive={false}
                        legendType="none"
                        connectNulls
                      />
                    )
                )}
                {series.map((s) => (
                  <Line
                    key={String(s.key)}
                    type="monotone"
                    dataKey={s.key as string}
                    name={s.label}
                    stroke={s.color}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                    connectNulls
                  />
                ))}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
