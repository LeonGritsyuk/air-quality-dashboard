import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { statusFor, type THRESHOLDS } from "@/lib/thresholds";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: number | null;
  unit: string;
  decimals?: number;
  metric?: keyof typeof THRESHOLDS;
}

export function MetricCard({ label, value, unit, decimals = 1, metric }: Props) {
  const status = metric ? statusFor(metric, value) : "unknown";
  const accent =
    status === "good"
      ? "border-l-good"
      : status === "elevated"
        ? "border-l-elevated"
        : status === "poor"
          ? "border-l-poor"
          : "border-l-hairline";

  return (
    <Card className={cn("border-l-4", accent)}>
      <CardContent className="pt-5">
        <div className="text-sm text-ink-muted">{label}</div>
        <div className="mt-1.5 flex items-baseline gap-1.5">
          <span className="font-display text-3xl font-semibold tabular-nums text-ink">
            {value === null ? "—" : value.toFixed(decimals)}
          </span>
          <span className="text-sm text-ink-faint">{unit}</span>
        </div>
        {metric && (
          <div className="mt-2">
            <StatusBadge status={status} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
