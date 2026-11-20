// What tests verify the lunar phase and position calculations.

import { describe, expect, it } from "vitest";
import { moonPhase, moonPosition } from "../src/moon";

describe("moon", () => {
  it("finds the November 2026 full moon", () => {
    const phase = moonPhase(new Date("2026-11-24T12:00:00Z"));
    expect(phase).toBeGreaterThanOrEqual(0.45);
    expect(phase).toBeLessThanOrEqual(0.55);
  });

  it("finds the November 2026 new moon", () => {
    const phase = moonPhase(new Date("2026-11-09T07:00:00Z"));
    expect(phase < 0.03 || phase > 0.97).toBe(true);
  });

  it("keeps phases normalized across many dates", () => {
    for (let i = -4000; i < 4000; i += 13) {
      const phase = moonPhase(new Date(Date.UTC(2000, 0, 1) + i * 86400000));
      expect(phase).toBeGreaterThanOrEqual(0);
      expect(phase).toBeLessThan(1);
    }
  });

  it("returns plausible and seasonally plausible positions", () => {
    for (const iso of ["2026-11-24T11:00:00Z", "2026-11-24T23:00:00Z"]) {
      const position = moonPosition(new Date(iso), 52, 5);
      expect(position.elevation).toBeGreaterThanOrEqual(-90);
      expect(position.elevation).toBeLessThanOrEqual(90);
      expect(position.azimuth).toBeGreaterThanOrEqual(0);
      expect(position.azimuth).toBeLessThan(360);
    }
    const midnight = moonPosition(new Date("2026-11-24T23:00:00Z"), 52, 5);
    expect(midnight.azimuth).toBeGreaterThanOrEqual(135);
    expect(midnight.azimuth).toBeLessThanOrEqual(225);
    expect(midnight.elevation).toBeGreaterThan(30);
    expect(moonPosition(new Date("2026-11-24T11:00:00Z"), 52, 5).elevation).toBeLessThan(0);
  });
});

describe("moon position against the sun's geometry", () => {
  it("rises in the east and sets in the west around full moon", () => {
    // full moon: rises around sunset (east), sets around sunrise (west)
    const evening = moonPosition(new Date("2026-11-24T16:30:00Z"), 52, 5);
    const morning = moonPosition(new Date("2026-11-25T07:30:00Z"), 52, 5);
    expect(evening.azimuth).toBeGreaterThan(30);
    expect(evening.azimuth).toBeLessThan(110);
    expect(morning.azimuth).toBeGreaterThan(250);
    expect(morning.azimuth).toBeLessThan(330);
  });
});
