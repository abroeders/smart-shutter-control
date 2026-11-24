// What the card shows for one shutter, from the states of its entities (no DOM).

import { baseOf, deviceEntities, deviceName } from "./entities";
import type { Translate } from "./localize";
import type { SceneInputs } from "./scene";
import type { HomeAssistant } from "./types";

export interface NextAction {
  at: string;
  phase: string;
  position: number | "slit";
}

export interface Decision {
  rule: string;
  priority: number;
  result: "target" | "cap" | "final" | "floor" | "none";
  position?: number | null;
  applied?: boolean;
  why?: string;
  values?: Record<string, unknown>;
}

export interface DecisionLine {
  rule: string;
  text: string;
  applied: boolean;
}

export interface ShutterModel {
  deviceId: string;
  name: string;
  entities: Record<string, string>;
  position: number | null;
  moving: "opening" | "closing" | null;
  /** fully closed (module at its end): only then are the slats pressed together */
  closed: boolean;
  stand: string | null;
  reason: string | null;
  decision: Decision[];
  target: number | null;
  max: number;
  phase: string | null;
  automatic: boolean;
  sleepIn: boolean;
  paused: boolean;
  pausedUntil: string | null;
  next: NextAction[];
  storm: boolean;
  frost: boolean;
  language: string | null;
  /** what the view through the window is made of (#30) */
  outside: SceneInputs;
}

const num = (v: unknown): number | null => (v === null || v === undefined || v === "" || Number.isNaN(Number(v)) ? null : Number(v));
const isDecision = (value: unknown): value is Decision => {
  if (!value || typeof value !== "object") return false;
  const entry = value as Record<string, unknown>;
  return (
    typeof entry.rule === "string" &&
    ["target", "cap", "final", "floor", "none"].includes(String(entry.result)) &&
    (entry.values === undefined || (typeof entry.values === "object" && entry.values !== null && !Array.isArray(entry.values)))
  );
};

export function shutterModel(hass: HomeAssistant, deviceId: string): ShutterModel {
  const e = deviceEntities(hass, deviceId);
  const st = (key: string) => (e[key] ? hass.states[e[key]] : undefined);
  const base = baseOf(hass, deviceId);
  const b = base ? deviceEntities(hass, base) : {};
  const on = (id?: string) => (id ? hass.states[id]?.state === "on" : false);
  const cover = st("shutter");
  const reason = st("reason");
  const nextAction = st("next_action");
  const next: NextAction[] = [];
  if (nextAction && !["unknown", "unavailable"].includes(nextAction.state) && nextAction.attributes.phase) {
    next.push({ at: nextAction.state, phase: nextAction.attributes.phase, position: nextAction.attributes.position });
    for (const f of nextAction.attributes.following ?? []) next.push({ at: f.at, phase: f.phase, position: f.position });
  }
  const pause = st("manual_pause");
  const state = cover?.state;
  return {
    deviceId,
    name: deviceName(hass, deviceId),
    entities: e,
    position: num(cover?.attributes.current_position),
    moving: state === "opening" || state === "closing" ? state : null,
    closed: state === "closed",
    stand: st("stand")?.state ?? null,
    reason: reason?.state ?? null,
    decision: Array.isArray(reason?.attributes.decision) ? reason.attributes.decision.filter(isDecision) : [],
    target: num(reason?.attributes.target_position),
    max: num(reason?.attributes.max_position) ?? 100,
    phase: st("phase")?.state ?? null,
    automatic: st("automatic")?.state !== "off",
    sleepIn: on(e.sleep_in),
    paused: on(e.manual_pause),
    pausedUntil: pause?.attributes.until ?? null,
    next,
    storm: on(b.storm),
    frost: on(b.frost),
    language: reason?.attributes.language ?? null,
    outside: outsideInputs(hass, b, e),
  };
}

/**
 * The inputs of the view through the window: sun and weather from the base controller, the window's direction,
 * and the measured light (the shutter's own facade sensor when it has one, else the base controller's).
 */
export function outsideInputs(hass: HomeAssistant, base: Record<string, string>, own: Record<string, string>, now = new Date()): SceneInputs {
  const attrs = (id?: string) => (id ? hass.states[id]?.attributes ?? {} : {});
  const sun = attrs(base.sun_factor);
  const storm = base.storm ? hass.states[base.storm] : undefined;
  const window = attrs(own.sun_on_window);
  const factor = num(window.sun_factor) ?? num(base.sun_factor ? hass.states[base.sun_factor]?.state : undefined);
  return {
    now,
    latitude: hass.config?.latitude ?? 52,
    longitude: hass.config?.longitude ?? 5,
    sunAzimuth: num(sun.sun_azimuth),
    sunElevation: num(sun.sun_elevation),
    windowAzimuth: num(window.window_azimuth),
    weather: sun.weather ?? null,
    cloudCoverage: num(sun.cloud_coverage),
    sunFactor: factor === null ? null : Math.max(0, Math.min(1, factor / 100)),
    wind: num(storm?.attributes.wind),
    gust: num(storm?.attributes.gust),
    storm: storm?.state === "on",
  };
}

/** Card language: the card's own option, else the integration's setting, else the user's profile. */
export function cardLanguage(hass: HomeAssistant, configured: string | undefined, model?: ShutterModel | null): string {
  return configured || model?.language || hass.locale?.language || hass.language || "en";
}

export function formatTime(iso: string, hass: HomeAssistant, language: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  try {
    return new Intl.DateTimeFormat(language, { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: hass.config?.time_zone }).format(d);
  } catch {
    return new Intl.DateTimeFormat(language, { hour: "2-digit", minute: "2-digit", hour12: false }).format(d);
  }
}

// reasons that mean the sun lowered the shutter (#73)
const SUN_REASONS = new Set(["heat", "glare"]);

/** The card offers "Sun has left the window" only while the sun lowered the shutter (#73). */
export function showSunLeft(model: ShutterModel): boolean {
  return Boolean(model.entities.sun_left) && model.reason !== null && SUN_REASONS.has(model.reason);
}

export function positionText(position: number | "slit" | null, t: Translate): string {
  if (position === null) return "–";
  if (position === "slit") return t("slit");
  if (position <= 0) return t("closed");
  if (position >= 100) return t("open");
  return `${position} %`;
}

function decisionNumber(value: unknown, language: string): string {
  const n = num(value);
  if (n === null) return String(value ?? "");
  try {
    return new Intl.NumberFormat(language, { maximumFractionDigits: 1 }).format(n);
  } catch {
    return String(n);
  }
}

function decisionTemplate(template: string, values: Record<string, unknown>, language: string, t: Translate): string {
  return template.replace(/\{(\w+)\}/g, (_match, key: string) => {
    const value = values[key];
    if (value === undefined || value === null) return "–";
    if (key === "phase") return t(`phase_${value}`);
    if (key === "duration") return String(value);
    return decisionNumber(value, language);
  });
}

function decisionDuration(seconds: unknown, language: string, t: Translate): string {
  const value = num(seconds);
  if (value === null) return "";
  const minutes = value >= 60;
  const duration = decisionNumber(minutes ? Math.ceil(value / 60) : Math.ceil(value), language);
  return decisionTemplate(t(minutes ? "decision_minutes" : "decision_seconds"), { duration }, language, t);
}

// reasons whose values are temperatures, in °C in the trace (#65)
const TEMPERATURE_WHY = new Set(["too_cold", "within_limits", "not_cold"]);
const TEMPERATURE_KEYS = ["outdoor", "limit", "room", "room_limit", "forecast", "forecast_limit"];

/** A temperature from the trace (°C) in the user's unit, with the unit (#65). */
function decisionTemperature(value: unknown, unit: string, language: string): string {
  const n = num(value);
  if (n === null) return "–";
  return `${decisionNumber(unit === "°F" ? (n * 9) / 5 + 32 : n, language)} ${unit === "°F" ? "°F" : "°C"}`;
}

/** Turns the reason sensor's decision trace into localized lines for the card. */
const RESULT_KEYS: Partial<Record<Decision["result"], string>> = {
  cap: "decision_at_most",
  final: "decision_final",
  floor: "decision_at_least",
};

export function decisionLines(decisions: Decision[], t: Translate, language = "en", temperatureUnit = "°C"): DecisionLine[] {
  return decisions.map((entry) => {
    const values = entry.values ?? {};
    const whyValues = { ...values };
    if (entry.why === "waiting" || entry.why === "leaving") whyValues.duration = decisionDuration(values.seconds, language, t);
    if (entry.why && TEMPERATURE_WHY.has(entry.why)) {
      for (const key of TEMPERATURE_KEYS) {
        if (values[key] !== undefined && values[key] !== null) whyValues[key] = decisionTemperature(values[key], temperatureUnit, language);
      }
    }
    let whyKey = `why_${entry.why}`;
    if (entry.why === "too_cold") {
      if (values.room !== undefined && values.room_limit !== undefined) whyKey += "_room";
      if (values.forecast !== undefined && values.forecast_limit !== undefined) whyKey += "_forecast";
    }
    const why = entry.why ? decisionTemplate(t(whyKey), whyValues, language, t) : "";
    const position = entry.position === undefined ? null : entry.position;
    const result = position === null
      ? t(entry.result === "final" ? "decision_hold" : entry.result === "floor" ? "decision_at_least_slit" : "decision_nothing")
      : decisionTemplate(
          t(RESULT_KEYS[entry.result] ?? "decision_to"),
          { position: decisionNumber(position, language) },
          language,
          t,
        );
    const text = entry.result === "none"
      ? why || t("decision_nothing")
      : [result, why ? `(${why})` : ""].filter(Boolean).join(" ");
    return { rule: t(`rule_${entry.rule}`), text, applied: entry.applied === true };
  });
}

export interface StatusLines {
  stand: string;
  reason: string;
  detail: string;
  next: string | null;
  after: string | null;
  chip: "automatic" | "manual_pause" | "off";
}

export function statusLines(m: ShutterModel, t: Translate, time: (iso: string) => string): StatusLines {
  const stand = m.stand && !["unknown", "unavailable"].includes(m.stand) ? t(m.stand) : "";
  const reason = m.reason ? t(`reason_${m.reason}`) : "";
  let detail = "";
  if (m.paused) {
    const until = m.pausedUntil === "next phase" || !m.pausedUntil ? t("next_phase") : time(m.pausedUntil);
    detail = `${t("until")} ${until}`;
  } else if (m.target !== null) {
    const toward = m.position !== null && Math.abs(m.target - m.position) > 1 ? `→ ${positionText(m.target, t)}` : "";
    detail = [toward, m.phase ? t(`phase_${m.phase}`) : ""].filter(Boolean).join(" · ");
  }
  // "16:55 dusk 35 %", "17:10 closed", "08:00 slit", "08:30 open"
  const action = (a: NextAction) =>
    [time(a.at), a.phase === "dusk" ? t("phase_dusk") : "", positionText(a.position, t)].filter(Boolean).join(" ");
  const [first, second] = m.next;
  return {
    stand,
    reason,
    detail,
    next: first ? `${t("next")}: ${action(first)}` : null,
    after: second ? `${t("after")} ${action(second)}` : null,
    chip: !m.automatic || m.reason === "paused" ? "off" : m.paused ? "manual_pause" : "automatic",
  };
}
