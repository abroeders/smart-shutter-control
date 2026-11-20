// Finds the integration's devices and their entities by translation key, so renamed entities keep working.

import { DOMAIN, type HomeAssistant } from "./types";

/** translation key → entity_id of the integration's entities on one device */
export function deviceEntities(hass: HomeAssistant, deviceId: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const e of Object.values(hass.entities ?? {})) {
    if (e.platform === DOMAIN && e.device_id === deviceId && e.translation_key) out[e.translation_key] = e.entity_id;
  }
  return out;
}

/** A shutter device has the integration's cover; the base controller has none. */
export function isShutter(hass: HomeAssistant, deviceId: string): boolean {
  return "shutter" in deviceEntities(hass, deviceId);
}

export function deviceName(hass: HomeAssistant, deviceId: string): string {
  const d = hass.devices?.[deviceId];
  return d?.name_by_user || d?.name || deviceId;
}

/** All devices with entities of the integration, base controllers first, then by name. */
export function integrationDevices(hass: HomeAssistant): string[] {
  const ids = new Set<string>();
  for (const e of Object.values(hass.entities ?? {})) if (e.platform === DOMAIN && e.device_id) ids.add(e.device_id);
  return [...ids].sort(
    (a, b) => Number(isShutter(hass, a)) - Number(isShutter(hass, b)) || deviceName(hass, a).localeCompare(deviceName(hass, b)),
  );
}

export function shuttersOf(hass: HomeAssistant, baseId: string): string[] {
  return integrationDevices(hass).filter((id) => hass.devices?.[id]?.via_device_id === baseId && isShutter(hass, id));
}

export function baseOf(hass: HomeAssistant, shutterId: string): string | undefined {
  return hass.devices?.[shutterId]?.via_device_id ?? undefined;
}
