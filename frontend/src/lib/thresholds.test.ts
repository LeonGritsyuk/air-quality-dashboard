import { describe, expect, it } from "vitest";
import { statusFor } from "@/lib/thresholds";

describe("statusFor", () => {
  it("returns unknown for null values", () => {
    expect(statusFor("rco2", null)).toBe("unknown");
  });

  it("classifies CO2 bands correctly", () => {
    expect(statusFor("rco2", 500)).toBe("good");
    expect(statusFor("rco2", 900)).toBe("elevated");
    expect(statusFor("rco2", 1500)).toBe("poor");
  });

  it("classifies PM2.5 bands correctly", () => {
    expect(statusFor("pm02", 4.2)).toBe("good");
    expect(statusFor("pm02", 20)).toBe("elevated");
    expect(statusFor("pm02", 50)).toBe("poor");
  });

  it("treats the boundary value as still within the lower band", () => {
    expect(statusFor("rco2", 800)).toBe("good");
    expect(statusFor("rco2", 801)).toBe("elevated");
  });
});
