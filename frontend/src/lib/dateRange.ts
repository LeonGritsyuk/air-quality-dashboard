import type { RangeKey } from "@/types/api";

export interface DateRange {
  from: Date;
  to: Date;
}

function startOfDay(d: Date): Date {
  const copy = new Date(d);
  copy.setHours(0, 0, 0, 0);
  return copy;
}

function endOfDay(d: Date): Date {
  const copy = new Date(d);
  copy.setHours(23, 59, 59, 999);
  return copy;
}

/**
 * Resolve a named range key into a concrete from/to Date pair, anchored to
 * `now` (injectable for testing). All ranges use the browser's local
 * timezone, which is the natural choice for a single-household dashboard
 * (see README for the timezone-handling rationale).
 */
export function resolveRange(key: RangeKey, now: Date = new Date()): DateRange {
  switch (key) {
    case "today":
      return { from: startOfDay(now), to: now };
    case "yesterday": {
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      return { from: startOfDay(yesterday), to: endOfDay(yesterday) };
    }
    case "7d": {
      const from = new Date(now);
      from.setDate(from.getDate() - 6);
      return { from: startOfDay(from), to: now };
    }
    case "30d": {
      const from = new Date(now);
      from.setDate(from.getDate() - 29);
      return { from: startOfDay(from), to: now };
    }
    case "custom":
      return { from: startOfDay(now), to: now };
  }
}

export function formatDateInput(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function parseDateInput(value: string): Date {
  const [y, m, d] = value.split("-").map(Number);
  return new Date(y, (m ?? 1) - 1, d ?? 1);
}

/** Builds the query-string params used both for the API call and the URL. */
export function rangeToSearchParams(range: DateRange): URLSearchParams {
  return new URLSearchParams({
    from: range.from.toISOString(),
    to: range.to.toISOString(),
  });
}
