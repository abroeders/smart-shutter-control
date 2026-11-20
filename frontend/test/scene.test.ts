import { describe, expect, it } from "vitest";
import { HORIZON, lightFor, placeInWindow, sceneFor, season, sway, type SceneInputs } from "../src/scene";

const base: SceneInputs = {
  now: new Date("2026-07-01T12:00:00Z"),
  latitude: 52,
  longitude: 5,
  sunAzimuth: 180,
  sunElevation: 55,
  windowAzimuth: 180,
  weather: "sunny",
  wind: 5,
  gust: 8,
  storm: false,
};

describe("scene", () => {
  it("lights the sky by the sun elevation", () => {
    expect([-20, -3, 0, 30].map((e) => lightFor(e))).toEqual(["night", "twilight", "day", "day"]);
  });

  it("places the sun as seen through the window", () => {
    expect(placeInWindow(180, 55, 180)!.x).toBeCloseTo(0.5); // south window at noon: in the middle
    expect(placeInWindow(120, 20, 90)!.x).toBeGreaterThan(0.5); // east window, sun south-east: to the right
    expect(placeInWindow(60, 20, 90)!.x).toBeLessThan(0.5);
    expect(placeInWindow(270, 20, 90)).toBeNull(); // behind the house
    expect(placeInWindow(180, -2, 180)).toBeNull(); // below the horizon
    const low = placeInWindow(180, 1, 180)!;
    const high = placeInWindow(180, 50, 180)!;
    expect(low.y).toBeLessThan(HORIZON);
    expect(high.y).toBeLessThan(low.y);
  });

  it("knows the season in both hemispheres", () => {
    const d = (m: number) => new Date(Date.UTC(2026, m - 1, 15));
    expect([1, 4, 7, 10, 12].map((m) => season(d(m), 52))).toEqual(["winter", "spring", "summer", "autumn", "winter"]);
    expect(season(d(7), -33)).toBe("winter");
    expect(season(d(1), -33)).toBe("summer");
  });

  it("sways the trees with the wind, harder in a storm", () => {
    expect(sway(5, 8, false)).toBe(0);
    const gentle = sway(25, 35, false);
    const strong = sway(65, 90, false);
    expect(gentle).toBeGreaterThan(0);
    expect(strong).toBeGreaterThan(gentle);
    expect(sway(65, 90, true)).toBeGreaterThan(strong);
  });

  it("builds a summer day with the sun in front of the window", () => {
    const s = sceneFor(base);
    expect(s).toMatchObject({ light: "day", clouds: "none", precipitation: "none", season: "summer", stars: 0, moon: null, sway: 0 });
    expect(s.sun).not.toBeNull();
  });

  it("shows rain, snow, fog and lightning by the weather", () => {
    const w = (weather: string) => sceneFor({ ...base, weather });
    expect(w("rainy").precipitation).toBe("rain");
    expect(w("pouring").precipitation).toBe("pouring");
    expect(w("snowy")).toMatchObject({ precipitation: "snow", snowGround: true, clouds: "overcast", sun: null });
    expect(w("snowy-rainy").precipitation).toBe("sleet");
    expect(w("fog").fog).toBe(true);
    expect(w("lightning-rainy")).toMatchObject({ lightning: true, precipitation: "rain" });
    expect(w("partlycloudy").clouds).toBe("few");
  });

  it("shows stars and the moon at night, none when overcast", () => {
    // full moon of 24 November 2026, around local midnight, a south window
    const night: SceneInputs = { ...base, now: new Date("2026-11-24T23:00:00Z"), sunAzimuth: 0, sunElevation: -55 };
    const s = sceneFor(night);
    expect(s.light).toBe("night");
    expect(s.stars).toBe(1);
    expect(s.sun).toBeNull();
    expect(s.moon).not.toBeNull();
    expect(s.moon!.phase).toBeGreaterThan(0.45);
    expect(s.moon!.phase).toBeLessThan(0.55);
    const cloudy = sceneFor({ ...night, weather: "cloudy" });
    expect(cloudy.stars).toBe(0);
    expect(cloudy.moon).toBeNull();
  });
});
