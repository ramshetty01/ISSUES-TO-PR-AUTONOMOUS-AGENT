import { describe, expect, it } from "vitest";

import {
  formatCost,
  formatTokens,
  percentOfCap,
} from "../src/lib/format-cost.js";
import {
  durationBetween,
  formatDuration,
} from "../src/lib/format-duration.js";

describe("formatCost", () => {
  it("renders free tier as Free", () => {
    expect(formatCost(0)).toBe("Free");
    expect(formatCost(-1)).toBe("Free");
  });
  it("renders sub-cent and normal dollars", () => {
    expect(formatCost(0.004)).toBe("<$0.01");
    expect(formatCost(1.239)).toBe("$1.24");
  });
  it("guards non-finite", () => {
    expect(formatCost(Number.NaN)).toBe("—");
  });
});

describe("formatTokens", () => {
  it("scales units", () => {
    expect(formatTokens(950)).toBe("950");
    expect(formatTokens(1_200)).toBe("1.2k");
    expect(formatTokens(3_400_000)).toBe("3.4M");
  });
});

describe("percentOfCap", () => {
  it("clamps to 0..100", () => {
    expect(percentOfCap(50, 200)).toBe(25);
    expect(percentOfCap(300, 200)).toBe(100);
    expect(percentOfCap(5, 0)).toBe(0);
  });
});

describe("formatDuration", () => {
  it("scales units", () => {
    expect(formatDuration(820)).toBe("820ms");
    expect(formatDuration(1_200)).toBe("1.2s");
    expect(formatDuration(184_000)).toBe("3m 4s");
    expect(formatDuration(3_720_000)).toBe("1h 2m");
  });
  it("guards invalid", () => {
    expect(formatDuration(-1)).toBe("—");
  });
});

describe("durationBetween", () => {
  it("computes across ISO timestamps", () => {
    expect(
      durationBetween("2026-01-01T00:00:00Z", "2026-01-01T00:03:04Z"),
    ).toBe("3m 4s");
  });
  it("returns dash for invalid input", () => {
    expect(durationBetween("nope", "also-nope")).toBe("—");
  });
});
