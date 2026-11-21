import { describe, expect, it } from "vitest";
import {
  HORIZON, cloudCover, landscape, lightFor, placeInWindow, sceneFor, season, sideLight, sunPath, sway, veil, type SceneInputs,
} from "../src/scene";
import { sunPosition } from "../src/sun";

const base: SceneInputs = {
  now: new Date("2026-07-01T12:00:00Z"),
  latitude: 52,
  longitude: 5,
  sunAzimuth: 180,
  sunElevation: 55,
  windowAzimuth: 180,
  weather: "sunny",
  cloudCoverage: null,
  sunFactor: null,
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
    expect(s).toMatchObject({ light: "day", cloudCount: 0, overcast: false, precipitation: "none", season: "summer", stars: 0, moon: null, sway: 0 });
    expect(s.sun).not.toBeNull();
  });

  it("shows rain, snow, fog and lightning by the weather", () => {
    const w = (weather: string) => sceneFor({ ...base, weather });
    expect(w("rainy").precipitation).toBe("rain");
    expect(w("pouring").precipitation).toBe("pouring");
    expect(w("snowy")).toMatchObject({ precipitation: "snow", snowGround: true, overcast: true, glow: 0 });
    expect(w("snowy").sun).not.toBeNull(); // dimmed behind the layer, its place stays visible
    expect(w("snowy-rainy").precipitation).toBe("sleet");
    expect(w("fog").fog).toBe(true);
    expect(w("lightning-rainy")).toMatchObject({ lightning: true, precipitation: "rain" });
    expect(w("partlycloudy").cloudCount).toBe(2);
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

  it("takes the cloud cover from the weather, by day mostly from the measured light", () => {
    expect(cloudCover("sunny", null, null)).toBe(0.05);
    expect(cloudCover("cloudy", null, null)).toBe(0.9);
    expect(cloudCover("rainy", null, null)).toBe(1);
    expect(cloudCover("cloudy", 30, null)).toBe(0.3); // the entity's cloud coverage wins over its condition
    expect(cloudCover(null, null, null)).toBe(0.3);
    // a station says cloudy, the panels see 92 % of clear sky: mostly blue
    expect(cloudCover("cloudy", null, 0.92)).toBeCloseTo(0.285, 2);
    expect(cloudCover("sunny", null, 0.1)).toBeGreaterThan(0.6);
  });

  it("counts the clouds by the cover and closes the layer from 80 %", () => {
    const at = (sunFactor: number) => sceneFor({ ...base, weather: "partlycloudy", sunFactor });
    expect(at(1).cloudCount).toBe(1);
    expect(at(0.5).cloudCount).toBe(3);
    expect(at(0.1)).toMatchObject({ overcast: false, cloudCount: 5 });
    expect(sceneFor({ ...base, weather: "cloudy", sunFactor: 0.05 })).toMatchObject({ overcast: true, cloudCount: 0 });
    expect(sceneFor({ ...base, weather: "cloudy", sunFactor: 0.05 }).sky).toEqual(["#78909c", "#b0bec5"]);
  });

  it("puts a cloud in front of a dim sun that slides aside as the sun breaks through", () => {
    expect(veil(0.95, 0.2)).toBeNull();
    expect(veil(0, 0.9)).toEqual({ opacity: 0.9, offset: 0 });
    const dim = veil(0.3, 0.5)!;
    const brighter = veil(0.6, 0.5)!;
    expect(brighter.opacity).toBeLessThan(dim.opacity);
    expect(brighter.offset).toBeGreaterThan(dim.offset);
    expect(veil(null, 0.05)).toBeNull();
    expect(veil(null, 0.6)).toEqual({ opacity: 0.6, offset: 0 });
    const s = sceneFor({ ...base, sunFactor: 0.4 });
    expect(s.veil).not.toBeNull();
    expect(s.glow).toBe(0.1);
    expect(sceneFor({ ...base, sunAzimuth: 0 }).veil).toBeNull(); // no sun in view, no veil
  });

  it("computes the sun's position", () => {
    // Amsterdam area, 21 June, 11:40 UTC: about solar noon, high in the south
    const summer = sunPosition(new Date("2026-06-21T11:40:00Z"), 52, 5);
    expect(summer.azimuth).toBeGreaterThan(175);
    expect(summer.azimuth).toBeLessThan(185);
    expect(summer.elevation).toBeGreaterThan(60);
    expect(summer.elevation).toBeLessThan(62);
    const winter = sunPosition(new Date("2026-12-21T11:45:00Z"), 52, 5);
    expect(winter.elevation).toBeGreaterThan(14);
    expect(winter.elevation).toBeLessThan(15.5);
  });

  it("draws the sun's path as seen through the window", () => {
    const highest = (pieces: { y: number }[][]) => Math.min(...pieces.flat().map((p) => p.y));
    const june = sunPath(new Date("2026-06-21T12:00:00Z"), 52, 5, 180);
    const december = sunPath(new Date("2026-12-21T12:00:00Z"), 52, 5, 180);
    expect(june.length).toBe(1);
    expect(highest(june)).toBeLessThan(highest(december)); // higher in summer
    const xs = june[0].map((p) => p.x);
    expect(xs[xs.length - 1]).toBeGreaterThan(xs[0]); // east (left) to west (right) through a south window
    expect(sunPath(new Date("2026-12-21T12:00:00Z"), 52, 5, 0)).toEqual([]); // a north window in winter
    const northSummer = sunPath(new Date("2026-06-21T12:00:00Z"), 52, 5, 0);
    expect(northSummer.length).toBeGreaterThan(0); // early and late, low at the sides
    expect(Math.max(...northSummer.flat().map((p) => p.y))).toBeGreaterThan(HORIZON - 0.15);
  });

  it("gives every window direction its own landscape", () => {
    expect(landscape(182)).toEqual(landscape(178)); // the same 10°
    expect(landscape(0)).not.toEqual(landscape(180));
    const l = landscape(90);
    expect(l.trees.length).toBeGreaterThanOrEqual(2);
    expect(l.trees.length).toBeLessThanOrEqual(3);
    for (const tree of l.trees) expect(tree.x).toBeGreaterThan(0);
  });

  it("lights the sun's side of the sky, most at a low sun", () => {
    const morning = sideLight(100, 5, 180, 0.1)!;
    expect(morning.x).toBeLessThan(0.5); // the sun is to the left of a south window
    const noon = sideLight(180, 40, 180, 0.1);
    expect(noon === null || noon.strength < morning.strength).toBe(true);
    expect(sideLight(0, 5, 180, 0.1)).toBeNull(); // behind the house
    expect(sideLight(100, 5, 180, 0.9)!.strength).toBeLessThan(morning.strength);
  });
});
