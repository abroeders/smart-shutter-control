// The parts of Home Assistant's frontend objects the card uses.

export const DOMAIN = "smart_shutter_control";

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_updated?: string;
}

export interface EntityEntry {
  entity_id: string;
  device_id?: string | null;
  platform: string;
  translation_key?: string | null;
}

export interface DeviceEntry {
  id: string;
  name?: string | null;
  name_by_user?: string | null;
  via_device_id?: string | null;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  entities: Record<string, EntityEntry>;
  devices: Record<string, DeviceEntry>;
  locale?: { language: string };
  language?: string;
  config?: { time_zone?: string };
  themes?: { darkMode?: boolean };
  callService(domain: string, service: string, data?: Record<string, unknown>): Promise<unknown>;
}

export interface CardConfig {
  type: string;
  device_id?: string;
  /** en or nl; empty: the integration's language setting, else the user's profile language */
  language?: string;
}
