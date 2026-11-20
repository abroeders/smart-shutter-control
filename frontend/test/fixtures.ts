import type { HomeAssistant } from "../src/types";

export const BASE = "base1";
export const LIVING = "dev_living";
export const KITCHEN = "dev_kitchen";
const P = "smart_shutter_control";
const ts = "2026-11-18T12:00:00+00:00";

const entity = (device: string, key: string, id: string) => ({ [id]: { entity_id: id, device_id: device, platform: P, translation_key: key } });

export function fakeHass(states: Record<string, any> = {}, extra: Partial<HomeAssistant> = {}): HomeAssistant & { calls: any[] } {
  const calls: any[] = [];
  const s = (state: string, attributes: Record<string, any> = {}) => ({ entity_id: "", state, attributes, last_updated: ts });
  const base: Record<string, any> = {
    "cover.living": s("open", { current_position: 62 }),
    "sensor.living_reason": s("sun", { target_position: 30, max_position: 80, language: null }),
    "sensor.living_next_action": s("2026-11-18T15:55:00+00:00", {
      phase: "dusk",
      position: 35,
      following: [
        { at: "2026-11-18T16:10:00+00:00", phase: "night", position: 0 },
        { at: "2026-11-19T07:00:00+00:00", phase: "slit", position: "slit" },
      ],
    }),
    "sensor.living_stand": s("partly_open"),
    "sensor.living_phase": s("day"),
    "switch.living_automatic": s("on"),
    "switch.living_sleep_in": s("off"),
    "binary_sensor.living_manual_pause": s("off", { until: null }),
    "button.living_resume": s("unknown"),
    "cover.kitchen": s("closed", { current_position: 0 }),
    "sensor.kitchen_reason": s("sleep_in", { target_position: 0, max_position: 100 }),
    "switch.kitchen_automatic": s("on"),
    "binary_sensor.storm": s("off"),
    "binary_sensor.frost": s("off"),
    "switch.sleep_in_all": s("off"),
  };
  return {
    calls,
    states: { ...base, ...states },
    entities: {
      ...entity(LIVING, "shutter", "cover.living"),
      ...entity(LIVING, "reason", "sensor.living_reason"),
      ...entity(LIVING, "next_action", "sensor.living_next_action"),
      ...entity(LIVING, "stand", "sensor.living_stand"),
      ...entity(LIVING, "phase", "sensor.living_phase"),
      ...entity(LIVING, "automatic", "switch.living_automatic"),
      ...entity(LIVING, "sleep_in", "switch.living_sleep_in"),
      ...entity(LIVING, "manual_pause", "binary_sensor.living_manual_pause"),
      ...entity(LIVING, "resume", "button.living_resume"),
      ...entity(KITCHEN, "shutter", "cover.kitchen"),
      ...entity(KITCHEN, "reason", "sensor.kitchen_reason"),
      ...entity(KITCHEN, "automatic", "switch.kitchen_automatic"),
      ...entity(BASE, "storm", "binary_sensor.storm"),
      ...entity(BASE, "frost", "binary_sensor.frost"),
      ...entity(BASE, "sleep_in_all", "switch.sleep_in_all"),
      "cover.other": { entity_id: "cover.other", device_id: "x", platform: "zwave_js", translation_key: null },
    },
    devices: {
      [BASE]: { id: BASE, name: "House" },
      [LIVING]: { id: LIVING, name: "Living room", via_device_id: BASE },
      [KITCHEN]: { id: KITCHEN, name: "Kitchen", via_device_id: BASE },
    },
    locale: { language: "en" },
    config: { time_zone: "Europe/Amsterdam" },
    callService: async (domain: string, service: string, data?: Record<string, unknown>) => {
      calls.push({ domain, service, data });
    },
    ...extra,
  };
}
