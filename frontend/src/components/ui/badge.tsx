import { cn } from "@/lib/utils";
import type { Status } from "@/lib/thresholds";
import { STATUS_LABEL } from "@/lib/thresholds";

const STYLES: Record<Status, string> = {
  good: "bg-good-bg text-good",
  elevated: "bg-elevated-bg text-elevated",
  poor: "bg-poor-bg text-poor",
  unknown: "bg-hairline/60 text-ink-faint",
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium",
        STYLES[status]
      )}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}
