// Visual editor: the device (a shutter, or a base controller for all its shutters) and the language.

import { LitElement, html } from "lit";
import { LANGUAGES, localizer } from "./localize";
import { DOMAIN, type CardConfig, type HomeAssistant } from "./types";

export function editorSchema(t: (k: string) => string) {
  return [
    { name: "device_id", selector: { device: { integration: DOMAIN } } },
    {
      name: "language",
      selector: {
        select: {
          mode: "dropdown",
          options: [{ value: "auto", label: t("language_auto") }, ...LANGUAGES.map((l) => ({ value: l, label: l === "nl" ? "Nederlands" : "English" }))],
        },
      },
    },
  ];
}

export class SmartShutterCardEditor extends LitElement {
  static properties = { hass: { attribute: false }, _config: { state: true } };

  hass?: HomeAssistant;
  _config?: CardConfig;

  setConfig(config: CardConfig) {
    this._config = config;
  }

  private changed(ev: CustomEvent) {
    const value = { ...ev.detail.value };
    if (!value.language || value.language === "auto") delete value.language;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: value }, bubbles: true, composed: true }));
  }

  render() {
    if (!this.hass || !this._config) return html``;
    const t = localizer(this._config.language || this.hass.locale?.language);
    return html`<ha-form
      .hass=${this.hass}
      .data=${{ ...this._config, language: this._config.language || "auto" }}
      .schema=${editorSchema(t)}
      .computeLabel=${(s: { name: string }) => t(s.name)}
      @value-changed=${this.changed}
    ></ha-form>`;
  }
}
