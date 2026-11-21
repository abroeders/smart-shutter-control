// The card: one shutter (drawing, buttons, status, switches) or all shutters of a base controller.

import { LitElement, css, html, nothing } from "lit";
import { deviceEntities, integrationDevices, isShutter, shuttersOf } from "./entities";
import { localizer, type Translate } from "./localize";
import { sceneFor } from "./scene";
import type { CardConfig, HomeAssistant } from "./types";
import { cardLanguage, decisionLines, formatTime, positionText, shutterModel, statusLines, type ShutterModel } from "./viewmodel";

export const CARD_TAG = "smart-shutter-card";
export const EDITOR_TAG = "smart-shutter-card-editor";
export const NARROW_PX = 360;

const ICONS = {
  up: "M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",
  stop: "M18,18H6V6H18V18Z",
  down: "M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z",
};

export class SmartShutterCard extends LitElement {
  static properties = { hass: { attribute: false }, _config: { state: true }, _narrow: { state: true }, _decisionOpen: { state: true } };

  hass?: HomeAssistant;
  _config?: CardConfig;
  _narrow = false;
  _decisionOpen = false;
  private observer?: ResizeObserver;

  static getConfigElement(): HTMLElement {
    return document.createElement(EDITOR_TAG);
  }

  static getStubConfig(hass: HomeAssistant): CardConfig {
    return { type: `custom:${CARD_TAG}`, device_id: integrationDevices(hass)[0] };
  }

  setConfig(config: CardConfig): void {
    if (!config) throw new Error("Invalid configuration");
    this._config = { ...config };
  }

  getCardSize(): number {
    return 6;
  }

  /** Sections dashboard: one shutter at least half a section; the overview takes the full width. */
  getGridOptions() {
    const overview = !!(this.hass && this._config?.device_id && !isShutter(this.hass, this._config.device_id));
    return { columns: overview ? "full" : 12, min_columns: 6, rows: "auto" };
  }

  connectedCallback(): void {
    super.connectedCallback();
    if (typeof ResizeObserver !== "undefined") {
      this.observer = new ResizeObserver((entries) => {
        const width = entries[0]?.contentRect.width ?? 0;
        if (width) this._narrow = width < NARROW_PX;
      });
      this.observer.observe(this);
    }
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.observer?.disconnect();
  }

  private call(domain: string, service: string, entityId?: string, data: Record<string, unknown> = {}) {
    if (!this.hass || !entityId) return;
    this.hass.callService(domain, service, { entity_id: entityId, ...data });
  }

  private toggle(entityId: string | undefined, on: boolean) {
    this.call(entityId?.split(".")[0] ?? "switch", on ? "turn_off" : "turn_on", entityId);
  }

  private moreInfo(entityId?: string) {
    if (!entityId) return;
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  render() {
    const hass = this.hass;
    const id = this._config?.device_id;
    if (!hass || !this._config) return nothing;
    const t0 = localizer(cardLanguage(hass, this._config.language));
    if (!id) return html`<ha-card><div class="message">${t0("no_device")}</div></ha-card>`;
    if (!hass.devices?.[id] && !Object.keys(deviceEntities(hass, id)).length)
      return html`<ha-card><div class="message">${t0("not_found")}: ${id}</div></ha-card>`;
    return isShutter(hass, id) ? this.renderShutter(hass, id) : this.renderOverview(hass, id);
  }

  private texts(hass: HomeAssistant, model: ShutterModel | null): { t: Translate; time: (iso: string) => string; lang: string } {
    const lang = cardLanguage(hass, this._config?.language, model);
    return { t: localizer(lang), time: (iso) => formatTime(iso, hass, lang), lang };
  }

  private buttons(m: ShutterModel, t: Translate, small = false) {
    const cover = m.entities.shutter;
    const b = (icon: keyof typeof ICONS, service: string, label: string) =>
      html`<button class="round ${small ? "small" : ""}" title=${label} aria-label=${label} @click=${(e: Event) => {
        e.stopPropagation();
        this.call("cover", service, cover);
      }}>
        <svg viewBox="0 0 24 24"><path d=${ICONS[icon]}></path></svg>
      </button>`;
    return html`${b("up", "open_cover", t("open_cover"))}${b("stop", "stop_cover", t("stop_cover"))}${b("down", "close_cover", t("close_cover"))}`;
  }

  private switch(label: string, entityId: string | undefined, on: boolean, cls: string) {
    if (!entityId) return nothing;
    return html`<button class="switch ${cls}" role="switch" aria-checked=${on ? "true" : "false"} @click=${() => this.toggle(entityId, on)}>
      <span class="track ${on ? "on" : ""}"><span class="knob"></span></span>${label}
    </button>`;
  }

  private warnings(storm: boolean, frost: boolean, t: Translate) {
    return html`${storm ? html`<span class="chip warn storm">⚠ ${t("storm_chip")}</span>` : nothing}${frost
      ? html`<span class="chip warn frost">❄ ${t("frost_chip")}</span>`
      : nothing}`;
  }

  private renderShutter(hass: HomeAssistant, id: string) {
    const m = shutterModel(hass, id);
    const { t, time, lang } = this.texts(hass, m);
    const s = statusLines(m, t, time);
    const decisions = decisionLines(m.decision, t, lang);
    const dark = !!hass.themes?.darkMode;
    return html`<ha-card class=${this._narrow ? "narrow" : ""}>
      <div class="head">
        <div class="name">${m.name}</div>
        <div class="chips"><span class="chip ${s.chip}">${t(s.chip)}</span>${this.warnings(m.storm, m.frost, t)}</div>
      </div>
      <div class="body">
        <ssc-drawing
          ?dark=${dark}
          .position=${m.position}
          .max=${m.max}
          .moving=${m.moving}
          .gaps=${!m.closed}
          .scene=${sceneFor(m.outside)}
          .animated=${true}
          .storm=${m.storm}
          .interactive=${!!m.entities.shutter}
          .label=${`${m.name}: ${t("position")}`}
          .maxLabel=${t("max")}
          @set-position=${(e: CustomEvent) => this.call("cover", "set_cover_position", m.entities.shutter, { position: e.detail.position })}
        ></ssc-drawing>
        <div class="buttons">${this.buttons(m, t)}</div>
        <div class="status">
          <div class="big">${m.position === null ? "–" : `${m.position} %`}</div>
          <div class="sub">${s.stand}</div>
          <div class="line reason">${s.reason}</div>
          <div class="sub">${s.detail}</div>
          ${s.next ? html`<div class="line next">${s.next}</div>` : nothing}
          ${s.then ? html`<div class="sub then">${s.then}</div>` : nothing}
          ${decisions.length
            ? html`<div class="why">
                <button class="why-toggle" type="button" aria-expanded=${this._decisionOpen ? "true" : "false"} aria-controls="decision-list" @click=${() => (this._decisionOpen = !this._decisionOpen)}>
                  ${t("why")}
                </button>
                <div id="decision-list" class="decision-list" ?hidden=${!this._decisionOpen}>
                  ${decisions.map(
                    (line) => html`<div class="decision-line ${line.applied ? "applied" : ""}">${line.rule}: ${line.text}</div>`,
                  )}
                </div>
              </div>`
            : nothing}
        </div>
      </div>
      <div class="switches">
        ${this.switch(t("automatic"), m.entities.automatic, m.automatic, "automatic")}
        ${this.switch(t("sleep_in"), m.entities.sleep_in, m.sleepIn, "sleep-in")}
        ${m.entities.sun_left && hass.states[m.entities.sun_on_window]?.state === "on"
          ? html`<button class="text sun-left" @click=${() => this.call("button", "press", m.entities.sun_left)}>${t("sun_left")}</button>`
          : nothing}
        ${m.paused && m.entities.resume
          ? html`<button class="text resume" @click=${() => this.call("button", "press", m.entities.resume)}>${t("resume")}</button>`
          : nothing}
      </div>
    </ha-card>`;
  }

  private renderOverview(hass: HomeAssistant, baseId: string) {
    const models = shuttersOf(hass, baseId).map((id) => shutterModel(hass, id));
    const { t, time } = this.texts(hass, models[0] ?? null);
    const b = deviceEntities(hass, baseId);
    const on = (key: string) => (b[key] ? hass.states[b[key]]?.state === "on" : false);
    const dark = !!hass.themes?.darkMode;
    return html`<ha-card class="overview">
      <div class="head">
        <div class="name">${t("all_shutters")}</div>
        <div class="chips">${this.warnings(on("storm"), on("frost"), t)}</div>
      </div>
      <div class="grid">
        ${models.map((m) => {
          const s = statusLines(m, t, time);
          const line = [m.position === null ? "–" : positionText(m.position, t), s.reason]
            .filter(Boolean)
            .join(" · ");
          return html`<div class="tile" @click=${() => this.moreInfo(m.entities.shutter)}>
            <ssc-drawing compact ?dark=${dark} .position=${m.position} .max=${m.max} .moving=${m.moving} .gaps=${!m.closed} .scene=${sceneFor(m.outside)}></ssc-drawing>
            <div class="tile-text">
              <div class="tile-name">${m.name}</div>
              <div class="sub ${s.chip === "manual_pause" ? "manual" : ""}">${line}${s.chip === "manual_pause" ? ` · ${s.detail}` : ""}</div>
              <div class="tile-buttons">${this.buttons(m, t, true)}</div>
            </div>
          </div>`;
        })}
      </div>
      <div class="switches">${this.switch(t("sleep_in_all"), b.sleep_in_all, on("sleep_in_all"), "sleep-in-all")}</div>
    </ha-card>`;
  }

  static styles = css`
    :host {
      display: block;
    }
    ha-card {
      padding: 16px;
      box-sizing: border-box;
      color: var(--primary-text-color);
    }
    .message {
      color: var(--secondary-text-color);
    }
    .head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .name {
      font-size: 1.15em;
      font-weight: 600;
    }
    .chips {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .chip {
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 0.85em;
      background: color-mix(in srgb, var(--success-color, #43a047) 15%, transparent);
      color: var(--success-color, #2e7d32);
    }
    .chip.manual_pause,
    .chip.warn {
      background: color-mix(in srgb, var(--warning-color, #ef6c00) 15%, transparent);
      color: var(--warning-color, #e65100);
    }
    .chip.off {
      background: var(--secondary-background-color, #eee);
      color: var(--secondary-text-color);
    }
    .body {
      display: grid;
      grid-template-columns: minmax(140px, 240px) auto 1fr;
      gap: 12px;
      align-items: center;
    }
    .narrow .body {
      grid-template-columns: 1fr auto;
    }
    .narrow .status {
      grid-column: 1 / -1;
    }
    .buttons {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    button {
      font: inherit;
      color: inherit;
      cursor: pointer;
    }
    .round {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      border: none;
      background: var(--secondary-background-color, #eceff1);
      display: grid;
      place-items: center;
      padding: 0;
    }
    .round.small {
      width: 32px;
      height: 32px;
    }
    .round svg {
      width: 22px;
      height: 22px;
      fill: var(--primary-text-color);
    }
    .round.small svg {
      width: 18px;
      height: 18px;
    }
    .round:focus-visible,
    .switch:focus-visible,
    .why-toggle:focus-visible {
      outline: 2px solid var(--primary-color);
    }
    .status .big {
      font-size: 2em;
      font-weight: 700;
      color: var(--primary-color);
      line-height: 1.1;
    }
    .status .line {
      margin-top: 12px;
    }
    .sub {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .why {
      margin-top: 8px;
    }
    .why-toggle {
      border: none;
      background: none;
      color: var(--secondary-text-color);
      font-size: 0.9em;
      padding: 0;
    }
    .decision-list {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .decision-line.applied {
      font-weight: 700;
    }
    .sub.manual {
      color: var(--warning-color, #e65100);
    }
    .switches {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 20px;
      margin-top: 14px;
      align-items: center;
    }
    .switch {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: none;
      background: none;
      padding: 0;
    }
    .track {
      width: 34px;
      height: 18px;
      border-radius: 9px;
      background: var(--disabled-color, #bdbdbd);
      position: relative;
      transition: background 0.2s;
    }
    .track.on {
      background: var(--switch-checked-color, var(--primary-color));
    }
    .knob {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fff;
      transition: left 0.2s;
    }
    .track.on .knob {
      left: 18px;
    }
    .text {
      border: 1px solid var(--primary-color);
      border-radius: 16px;
      background: none;
      color: var(--primary-color);
      padding: 4px 12px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 12px;
    }
    .tile {
      display: grid;
      grid-template-columns: 72px 1fr;
      gap: 10px;
      align-items: center;
      cursor: pointer;
    }
    .tile-name {
      font-weight: 600;
    }
    .tile-buttons {
      display: flex;
      gap: 6px;
      margin-top: 6px;
    }
  `;
}

