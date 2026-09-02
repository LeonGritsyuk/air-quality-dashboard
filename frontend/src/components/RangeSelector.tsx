import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";
import { formatDateInput, parseDateInput } from "@/lib/dateRange";
import type { RangeKey } from "@/types/api";

const OPTIONS: { key: RangeKey; label: string }[] = [
  { key: "today", label: "Today" },
  { key: "yesterday", label: "Yesterday" },
  { key: "7d", label: "7 days" },
  { key: "30d", label: "30 days" },
  { key: "custom", label: "Custom" },
];

interface Props {
  value: RangeKey;
  onChange: (key: RangeKey) => void;
  customFrom: Date;
  customTo: Date;
  onCustomChange: (from: Date, to: Date) => void;
}

export function RangeSelector({ value, onChange, customFrom, customTo, onCustomChange }: Props) {
  return (
    <div className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
      <TabsPrimitive.Root value={value} onValueChange={(v) => onChange(v as RangeKey)}>
        <TabsPrimitive.List className="inline-flex rounded-sm border border-hairline bg-surface p-0.5">
          {OPTIONS.map((opt) => (
            <TabsPrimitive.Trigger
              key={opt.key}
              value={opt.key}
              className={cn(
                "rounded-sm px-3 py-1.5 text-sm font-medium text-ink-muted transition-colors",
                "data-[state=active]:bg-ink data-[state=active]:text-white"
              )}
            >
              {opt.label}
            </TabsPrimitive.Trigger>
          ))}
        </TabsPrimitive.List>
      </TabsPrimitive.Root>

      {value === "custom" && (
        <div className="flex items-center gap-2 text-sm">
          <input
            type="date"
            aria-label="From date"
            className="rounded-sm border border-hairline bg-surface px-2 py-1.5 text-ink"
            value={formatDateInput(customFrom)}
            onChange={(e) => {
              if (!e.target.value) return;
              onCustomChange(parseDateInput(e.target.value), customTo);
            }}
          />
          <span className="text-ink-faint">to</span>
          <input
            type="date"
            aria-label="To date"
            className="rounded-sm border border-hairline bg-surface px-2 py-1.5 text-ink"
            value={formatDateInput(customTo)}
            onChange={(e) => {
              if (!e.target.value) return;
              const to = parseDateInput(e.target.value);
              to.setHours(23, 59, 59, 999);
              onCustomChange(customFrom, to);
            }}
          />
        </div>
      )}
    </div>
  );
}
