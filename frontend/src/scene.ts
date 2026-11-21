// What you see through the window (#30, #34): light, sky, sun and moon, clouds, weather, season and wind.
// Pure: no DOM.

import { moonPhase, moonPosition } from "./moon";
import { sunPosition } from "./sun";

export type Light = "night" | "twilight" | "day";
export type Season = "spring" | "summer" | "autumn" | "winter";
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
  /** the weather entity's cloud coverage in %, null when it has none */
  cloudCoverage: number | null;
  /** 0 … 1: measured light against clear sky (PV power, light sensors or the facade sensor); null when unknown */
  sunFactor: number | null;
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

/** The cloud in front of the sun: how opaque, and how far aside (in sun radii) it has slid. */
export interface Veil {
  opacity: number;
  offset: number;
}

/** The light on the sun's side of the sky: where (x, may lie outside the window) and how strong (0 … 1). */
export interface SideLight {
  x: number;
  strength: number;
}

/** The landscape of this window: hill shape (offsets as fractions of the height) and trees. */
export interface Landscape {
  hill: [number, number, number, number];
  trees: { x: number; height: number }[];
}

export interface Scene {
  light: Light;
  /** sky gradient, top and bottom colour */
  sky: [string, string];
  /** 0 … 1: how visible the stars are */
  stars: number;
  sun: Place | null;
  /** 0 … 1: the opacity of the sun's glow */
  glow: number;
  /** the cloud in front of the sun; null when the sun is bright or not in view */
  veil: Veil | null;
  /** today's path of the sun through this window, as one or more pieces */
  path: Place[][];
  moon: MoonInView | null;
  /** 0 … 1: cloud cover */
  cover: number;
  /** number of separate clouds, 0 … 6 */
  cloudCount: number;
  /** a closed grey cloud layer */
  overcast: boolean;
  sideLight: SideLight | null;
  landscape: Landscape;
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
const FULL = ["rainy", "pouring", "snowy", "snowy-rainy", "lightning", "lightning-rainy", "hail", "exceptional"];
const COVER: Record<string, number> = { sunny: 0.05, "clear-night": 0.05, partlycloudy: 0.4, windy: 0.3, "windy-variant": 0.5, cloudy: 0.9, fog: 0.9 };
/** From this cloud cover the sky is grey with a closed layer. */
export const OVERCAST_FROM = 0.8;
/** From this sun factor the sun is bright: no cloud in front of it. */
export const BRIGHT_FROM = 0.9;
export const MAX_CLOUDS = 6;

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
  const relative = relativeAzimuth(azimuth, windowAzimuth);
  if (Math.abs(relative) > HALF_VIEW) return null;
  const x = 0.5 + relative / (2 * HALF_VIEW);
  return { x: Math.min(0.94, Math.max(0.06, x)), y: heightInView(elevation) };
}

/** Degrees to the right of the window's direction (−180 … 180). */
function relativeAzimuth(azimuth: number, windowAzimuth: number | null): number {
  return windowAzimuth === null ? 0 : ((azimuth - windowAzimuth + 540) % 360) - 180;
}

function heightInView(elevation: number): number {
  return HORIZON - Math.min(elevation, 60) / 60 * (HORIZON - TOP);
}

/**
 * Cloud cover 0 … 1: the weather entity's cloud coverage, else its condition. By day the measured light (sun
 * factor) counts three times as much: the weather is for a wide area, the sensors see this house now.
 */
export function cloudCover(weather: string | null, cloudCoverage: number | null, sunFactor: number | null): number {
  const reported = cloudCoverage !== null ? cloudCoverage / 100 : FULL.includes(weather ?? "") ? 1 : COVER[weather ?? ""] ?? 0.3;
  const cover = sunFactor === null ? reported : (reported + 3 * (1 - sunFactor)) / 4;
  return Math.round(Math.max(0, Math.min(1, cover)) * 100) / 100;
}

/** The cloud in front of a sun in view: opaque at a low sun factor, sliding aside as it rises, gone when bright. */
export function veil(sunFactor: number | null, cover: number): Veil | null {
  if (sunFactor === null) return cover < 0.1 ? null : { opacity: cover, offset: 0 };
  if (sunFactor >= BRIGHT_FROM) return null;
  const share = Math.max(0, sunFactor) / BRIGHT_FROM;
  return { opacity: Math.round(0.9 * (1 - share) * 100) / 100, offset: Math.round(share * 2.5 * 100) / 100 };
}

/** Today's path of the sun as seen through this window, in pieces where it is above the horizon and in view. */
export function sunPath(date: Date, latitude: number, longitude: number, windowAzimuth: number | null): Place[][] {
  const start = new Date(date);
  start.setHours(0, 0, 0, 0);
  const pieces: Place[][] = [];
  let piece: Place[] = [];
  for (let minute = 0; minute <= 24 * 60; minute += 10) {
    const position = sunPosition(new Date(start.getTime() + minute * 60000), latitude, longitude);
    const relative = relativeAzimuth(position.azimuth, windowAzimuth);
    if (position.elevation >= 0 && Math.abs(relative) <= HALF_VIEW) {
      piece.push({ x: 0.5 + relative / (2 * HALF_VIEW), y: heightInView(position.elevation) });
    } else if (piece.length) {
      pieces.push(piece);
      piece = [];
    }
  }
  if (piece.length) pieces.push(piece);
  return pieces.filter((p) => p.length > 1);
}

/** The light on the sun's side: strongest at a low sun, fading as the sun goes further behind the house. */
export function sideLight(sunAzimuth: number | null, sunElevation: number | null, windowAzimuth: number | null, cover: number): SideLight | null {
  if (sunAzimuth === null || sunElevation === null || sunElevation < -6) return null;
  const relative = relativeAzimuth(sunAzimuth, windowAzimuth);
  const behind = Math.max(0, Math.abs(relative) - HALF_VIEW) / 80; // 0 in view, 1 at 150° aside
  if (behind >= 1) return null;
  const low = 1 - Math.min(Math.max(sunElevation, 0), 40) / 40;
  const strength = Math.round(0.7 * low * (1 - behind) * (1 - 0.7 * cover) * 100) / 100;
  if (strength < 0.05) return null;
  return { x: Math.max(-0.3, Math.min(1.3, 0.5 + relative / (2 * HALF_VIEW))), strength };
}

function seededRandom(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value = (Math.imul(value, 1664525) + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

/** The landscape seen through a window: fixed per 10° of window direction, so every direction has its own. */
export function landscape(windowAzimuth: number | null): Landscape {
  const sector = windowAzimuth === null ? 18 : Math.round(((windowAzimuth % 360) + 360) % 360 / 10) % 36;
  const random = seededRandom(7919 * (sector + 1));
  const hill: Landscape["hill"] = [0, 0, 0, 0].map(() => Math.round((random() * 0.12 - 0.07) * 1000) / 1000) as Landscape["hill"];
  const count = 2 + Math.floor(random() * 2);
  const trees = Array.from({ length: count }, (_, i) => ({
    x: Math.round(((i + 0.2 + random() * 0.6) / count) * 100) / 100,
    height: Math.round((0.12 + random() * 0.11) * 100) / 100,
  }));
  return { hill, trees };
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

function skyColours(light: Light, elevation: number | null, cover: number): [string, string] {
  const overcast = cover >= OVERCAST_FROM;
  if (light === "night") return overcast ? ["#1b1f2a", "#2e3440"] : ["#0d1442", "#283593"];
  if (light === "twilight") return overcast ? ["#4a4f63", "#7a6f80"] : ["#3949ab", "#ff8a65"];
  if (overcast) return ["#78909c", "#b0bec5"];
  if (cover >= 0.55) return ["#6f9fc8", "#cfd8dc"]; // hazy
  const low = elevation !== null && elevation < 12;
  return low ? ["#64b5f6", "#ffe0b2"] : ["#42a5f5", "#bbdefb"];
}

export function sceneFor(inputs: SceneInputs): Scene {
  const weather = inputs.weather ?? "";
  const light = lightFor(inputs.sunElevation);
  const sunFactor = light === "day" ? inputs.sunFactor : null;
  const cover = cloudCover(inputs.weather, inputs.cloudCoverage, sunFactor);
  const overcast = cover >= OVERCAST_FROM;
  const precipitation: Precipitation =
    weather === "pouring" ? "pouring" : weather === "snowy-rainy" ? "sleet" : weather === "snowy" ? "snow" : RAIN.includes(weather) ? "rain" : "none";
  // under a closed layer the sun is still drawn, dimmed behind the clouds, so its place stays visible
  const sun = light === "day" ? placeInWindow(inputs.sunAzimuth, inputs.sunElevation, inputs.windowAzimuth) : null;
  let moon: MoonInView | null = null;
  if (light !== "day" && !overcast) {
    const phase = moonPhase(inputs.now);
    const position = moonPosition(inputs.now, inputs.latitude, inputs.longitude);
    const place = placeInWindow(position.azimuth, position.elevation, inputs.windowAzimuth);
    const visible = phase > 0.03 && phase < 0.97; // no new moon
    if (place && visible) moon = { ...place, phase };
  }
  const clear = 1 - cover;
  const stars = overcast ? 0 : (light === "night" ? 1 : light === "twilight" ? Math.max(0, Math.min(1, -(inputs.sunElevation ?? 0) / 6)) : 0) * Math.min(1, clear * 1.5);
  const swayDeg = sway(inputs.wind, inputs.gust, inputs.storm);
  const dim = light === "night" ? 0.65 : light === "twilight" ? 0.35 : overcast ? 0.15 : 0;
  return {
    light,
    sky: skyColours(light, inputs.sunElevation, cover),
    stars,
    sun,
    glow: sun ? Math.round(0.25 * (sunFactor ?? clear) * 100) / 100 : 0,
    veil: sun ? veil(sunFactor, cover) : null,
    path: light === "night" ? [] : sunPath(inputs.now, inputs.latitude, inputs.longitude, inputs.windowAzimuth),
    moon,
    cover,
    cloudCount: overcast ? 0 : Math.round(cover * MAX_CLOUDS),
    overcast,
    sideLight: light === "night" ? null : sideLight(inputs.sunAzimuth, inputs.sunElevation, inputs.windowAzimuth, cover),
    landscape: landscape(inputs.windowAzimuth),
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
