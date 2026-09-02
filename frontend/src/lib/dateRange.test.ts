import { describe, expect, it } from "vitest";
import { resolveRange, formatDateInput, parseDateInput } from "@/lib/dateRange";

describe("resolveRange", () => {
  const now = new Date(2026, 8, 2, 14, 30, 0); // Sep 2, 2026, 14:30 local

  it("today spans from midnight to now", () => {
    const { from, to } = resolveRange("today", now);
    expect(from.getHours()).toBe(0);
    expect(from.getDate()).toBe(2);
    expect(to).toEqual(now);
  });

  it("yesterday spans the full previous day", () => {
    const { from, to } = resolveRange("yesterday", now);
    expect(from.getDate()).toBe(1);
    expect(from.getHours()).toBe(0);
    expect(to.getDate()).toBe(1);
    expect(to.getHours()).toBe(23);
  });

  it("7d covers the last 7 calendar days including today", () => {
    const { from, to } = resolveRange("7d", now);
    const diffDays = Math.round((to.getTime() - from.getTime()) / 86_400_000);
    expect(diffDays).toBeGreaterThanOrEqual(6);
    expect(diffDays).toBeLessThanOrEqual(7);
  });

  it("30d covers roughly the last 30 days", () => {
    const { from } = resolveRange("30d", now);
    const diffDays = Math.round((now.getTime() - from.getTime()) / 86_400_000);
    expect(diffDays).toBeGreaterThanOrEqual(29);
  });
});

describe("date input formatting round-trip", () => {
  it("formats and parses back to the same calendar day", () => {
    const d = new Date(2026, 8, 2);
    const formatted = formatDateInput(d);
    expect(formatted).toBe("2026-09-02");
    const parsed = parseDateInput(formatted);
    expect(parsed.getFullYear()).toBe(2026);
    expect(parsed.getMonth()).toBe(8);
    expect(parsed.getDate()).toBe(2);
  });
});
