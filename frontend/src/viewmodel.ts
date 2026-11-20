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

const num = (v: unknown): number | null => (v === null || v === undefined || v === "" || isNaN(Number(v)) ? null : Number(v));

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

/** The inputs of the view through the window: sun and weather from the base controller, the window's direction. */
export function outsideInputs(hass: HomeAssistant, base: Record<string, string>, own: Record<string, string>, now = new Date()): SceneInputs {
  const attrs = (id?: string) => (id ? hass.states[id]?.attributes ?? {} : {});
  const sun = attrs(base.sun_factor);
  const storm = base.storm ? hass.states[base.storm] : undefined;
  return {
    now,
    latitude: hass.config?.latitude ?? 52,
    longitude: hass.config?.longitude ?? 5,
    sunAzimuth: num(sun.sun_azimuth),
    sunElevation: num(sun.sun_elevation),
    windowAzimuth: num(attrs(own.sun_on_window).window_azimuth),
    weather: sun.weather ?? null,
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
  if (isNaN(d.getTime())) return "";
  try {
    return new Intl.DateTimeFormat(language, { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: hass.config?.time_zone }).format(d);
  } catch {
    return new Intl.DateTimeFormat(language, { hour: "2-digit", minute: "2-digit", hour12: false }).format(d);
  }
}

export function positionText(position: number | "slit" | null, t: Translate): string {
  if (position === null) return "–";
  if (position === "slit") return t("slit");
  if (position <= 0) return t("closed");
  if (position >= 100) return t("open");
  return `${position} %`;
}

export interface StatusLines {
  stand: string;
  reason: string;
  detail: string;
  next: string | null;
  then: string | null;
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
    then: second ? `${t("then")} ${action(second)}` : null,
    chip: !m.automatic ? "off" : m.paused ? "manual_pause" : "automatic",
  };
}
