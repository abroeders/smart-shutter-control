// What you see through the window (#30): light, sky, sun and moon, weather, season and wind. Pure: no DOM.

import { moonPhase, moonPosition } from "./moon";

export type Light = "night" | "twilight" | "day";
export type Season = "spring" | "summer" | "autumn" | "winter";
export type Clouds = "none" | "few" | "overcast";
export type Precipitation = "none" | "rain" | "pouring" | "snow" | "sleet";

export interface SceneInputs {
  now: Date;
  latitude: number;
  longitude: number;
  /** degrees, 0 = north, clockwise; null when unknown */
  sunAzimuth: number | null;
  sunElevation: number | null;
  /** the window's outward direction, degrees as the azimuth */
  windowAzimuth: number | null;
  /** Home Assistant weather condition, e.g. sunny, rainy, snowy */
  weather: string | null;
  /** km/h */
  wind: number | null;
  gust: number | null;
  storm: boolean;
}

/** A place in the view as fractions: x 0 = left, 1 = right; y 0 = top, 1 = bottom. */
export interface Place {
  x: number;
  y: number;
}

export interface MoonInView extends Place {
  /** 0 = new, 0.25 = first quarter, 0.5 = full, 0.75 = last quarter */
  phase: number;
}

export interface Scene {
  light: Light;
  /** sky gradient, top and bottom colour */
  sky: [string, string];
  /** 0 … 1: how visible the stars are */
  stars: number;
  sun: Place | null;
  moon: MoonInView | null;
  clouds: Clouds;
  precipitation: Precipitation;
  fog: boolean;
  lightning: boolean;
  season: Season;
  /** snow lies on the ground */
  snowGround: boolean;
  /** tree sway amplitude in degrees (0 = still) */
  sway: number;
  /** slant of falling rain or snow in degrees, with the wind */
  slant: number;
  /** 0 … 1: darkening of the landscape (night, twilight, heavy weather) */
  dim: number;
}

/** Where the horizon is in the view, as a fraction from the top. */
export const HORIZON = 0.72;
/** The highest place of the sun or moon in the view (a fraction from the top, below the shutter box). */
export const TOP = 0.16;
/** Half the horizontal field of view through the window, in degrees. */
export const HALF_VIEW = 70;

const RAIN = ["rainy", "lightning-rainy"];
const OVERCAST = ["cloudy", "rainy", "pouring", "snowy", "snowy-rainy", "lightning", "lightning-rainy", "hail", "fog", "exceptional"];
const FEW = ["partlycloudy", "windy-variant"];

export function lightFor(elevation: number | null): Light {
  if (elevation === null) return "day";
  if (elevation < -6) return "night";
  if (elevation < 0) return "twilight";
  return "day";
}

/**
 * The place of a body in the window, or null when it is not visible through it: below the horizon, or more
 * than HALF_VIEW degrees to the side (behind the house). Looking out, a smaller azimuth is on the left.
 */
export function placeInWindow(azimuth: number | null, elevation: number | null, windowAzimuth: number | null): Place | null {
  if (azimuth === null || elevation === null || elevation < 0) return null;
  const relative = windowAzimuth === null ? 0 : ((azimuth - windowAzimuth + 540) % 360) - 180;
  if (Math.abs(relative) > HALF_VIEW) return null;
  const x = 0.5 + relative / (2 * HALF_VIEW);
  const y = HORIZON - Math.min(elevation, 60) / 60 * (HORIZON - TOP);
  return { x: Math.min(0.94, Math.max(0.06, x)), y };
}

/** Meteorological seasons; the southern hemisphere is half a year on. */
export function season(date: Date, latitude: number): Season {
  const order: Season[] = ["winter", "spring", "summer", "autumn"];
  const index = Math.floor(((date.getMonth() + 1) % 12) / 3); // Dec–Feb 0, Mar–May 1, …
  return order[latitude < 0 ? (index + 2) % 4 : index];
}

/** Tree sway in degrees from the wind (the stronger of wind and gusts); harder still in a storm. */
export function sway(wind: number | null, gust: number | null, storm: boolean): number {
  const v = Math.max(wind ?? 0, (gust ?? 0) * 0.7);
  let deg = v < 10 ? 0 : v < 40 ? 1 + (v - 10) / 10 : v < 60 ? 4 + (v - 40) / 5 : 8 + Math.min(4, (v - 60) / 10);
  if (storm) deg = Math.max(deg, 10) + 3;
  return Math.round(deg * 10) / 10;
}

function skyColours(light: Light, elevation: number | null, overcast: boolean): [string, string] {
  if (light === "night") return overcast ? ["#1b1f2a", "#2e3440"] : ["#0d1442", "#283593"];
  if (light === "twilight") return overcast ? ["#4a4f63", "#7a6f80"] : ["#3949ab", "#ff8a65"];
  if (overcast) return ["#78909c", "#b0bec5"];
  const low = elevation !== null && elevation < 12;
  return low ? ["#64b5f6", "#ffe0b2"] : ["#42a5f5", "#bbdefb"];
}

export function sceneFor(inputs: SceneInputs): Scene {
  const weather = inputs.weather ?? "";
  const light = lightFor(inputs.sunElevation);
  const overcast = OVERCAST.includes(weather);
  const clouds: Clouds = overcast ? "overcast" : FEW.includes(weather) ? "few" : "none";
  const precipitation: Precipitation =
    weather === "pouring" ? "pouring" : weather === "snowy-rainy" ? "sleet" : weather === "snowy" ? "snow" : RAIN.includes(weather) ? "rain" : "none";
  // behind a closed cloud cover the sun is not seen
  const sun = light === "day" && !overcast ? placeInWindow(inputs.sunAzimuth, inputs.sunElevation, inputs.windowAzimuth) : null;
  let moon: MoonInView | null = null;
  if (light !== "day" && !overcast) {
    const phase = moonPhase(inputs.now);
    const position = moonPosition(inputs.now, inputs.latitude, inputs.longitude);
    const place = placeInWindow(position.azimuth, position.elevation, inputs.windowAzimuth);
    const visible = phase > 0.03 && phase < 0.97; // no new moon
    if (place && visible) moon = { ...place, phase };
  }
  const stars = overcast ? 0 : light === "night" ? 1 : light === "twilight" ? Math.max(0, Math.min(1, -(inputs.sunElevation ?? 0) / 6)) : 0;
  const swayDeg = sway(inputs.wind, inputs.gust, inputs.storm);
  const dim = light === "night" ? 0.65 : light === "twilight" ? 0.35 : overcast ? 0.15 : 0;
  return {
    light,
    sky: skyColours(light, inputs.sunElevation, overcast),
    stars,
    sun,
    moon,
    clouds,
    precipitation,
    fog: weather === "fog",
    lightning: weather === "lightning" || weather === "lightning-rainy",
    season: season(inputs.now, inputs.latitude),
    snowGround: precipitation === "snow" || precipitation === "sleet",
    sway: swayDeg,
    slant: Math.min(30, swayDeg * 2.5),
    dim,
  };
}
