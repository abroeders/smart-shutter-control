// The shutter drawing: window, box, slats down to the real position. Drag (or ↑/↓, Home, End, Enter) to move it.

import { LitElement, css, html, svg } from "lit";
import { type Box, positionForY, snap, yForPosition } from "./geometry";

export const DRAWING_TAG = "ssc-drawing";
export const VIEW_H = 262;
/** centre of the bottom bar: fully open at the top of the glass, closed on the sill */
export const BAR: Box = { top: 40, bottom: 241 };
const MIN_DRAG_PX = 4;

export class ShutterDrawing extends LitElement {
  static properties = {
    position: { type: Number },
    max: { type: Number },
    moving: { type: String },
    gaps: { type: Boolean },
    storm: { type: Boolean },
    compact: { type: Boolean },
    interactive: { type: Boolean },
    label: { type: String },
    maxLabel: { type: String },
    _drag: { state: true },
  };

  position: number | null = null;
  max = 100;
  moving: string | null = null;
  /** light between the slats: whenever the shutter is not fully closed (only then are they pressed together) */
  gaps = false;
  storm = false;
  compact = false;
  interactive = false;
  label = "";
  maxLabel = "max";
  _drag: number | null = null;
  private startY: number | null = null;
  private moved = false;

  static styles = css`
    :host {
      display: block;
      --ssc-frame: var(--secondary-text-color, #90a4ae);
      --ssc-box: var(--secondary-background-color, #eceff1);
      --ssc-glass-1: #e3f2fd;
      --ssc-glass-2: #90caf9;
      --ssc-slat-1: #eceff1;
      --ssc-slat-2: #b0bec5;
      --ssc-slat-line: #90a4ae;
      --ssc-bar: #546e7a;
      --ssc-accent: var(--primary-color, #1e88e5);
      --ssc-max: var(--warning-color, #ef6c00);
    }
    :host([dark]) {
      --ssc-glass-1: #1a3550;
      --ssc-glass-2: #2b5a85;
      --ssc-slat-1: #607d8b;
      --ssc-slat-2: #455a64;
      --ssc-slat-line: #37474f;
      --ssc-bar: #b0bec5;
    }
    svg {
      display: block;
      width: 100%;
      height: auto;
      outline: none;
    }
    svg.interactive {
      cursor: ns-resize;
      touch-action: none;
    }
    svg:focus-visible .frame {
      stroke: var(--ssc-accent);
    }
    .curtain {
      transition: transform 0.6s ease;
    }
    @media (prefers-reduced-motion: reduce) {
      .curtain {
        transition: none;
      }
    }
    text {
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
  `;

  private viewY(ev: MouseEvent): number | null {
    const r = this.renderRoot.querySelector("svg")?.getBoundingClientRect();
    if (!r || !r.height) return null;
    return ((ev.clientY - r.top) / r.height) * VIEW_H;
  }

  private onDown(ev: PointerEvent) {
    if (!this.interactive) return;
    (ev.currentTarget as Element).setPointerCapture?.(ev.pointerId);
    this.startY = ev.clientY;
    this.moved = false;
    ev.preventDefault();
  }

  private onMove(ev: PointerEvent) {
    if (this.startY === null) return;
    if (!this.moved && Math.abs(ev.clientY - this.startY) < MIN_DRAG_PX) return;
    this.moved = true;
    const y = this.viewY(ev);
    if (y !== null) this._drag = snap(positionForY(y, BAR), this.storm);
  }

  private onUp(ev: PointerEvent) {
    if (this.startY === null) return;
    this.onMove(ev);
    this.startY = null;
    if (this.moved) this.send();
    this._drag = null;
  }

  private onCancel() {
    this.startY = null;
    this._drag = null;
  }

  private onKey(ev: KeyboardEvent) {
    if (!this.interactive) return;
    const from = this._drag ?? this.position ?? 0;
    const step: Record<string, number> = { ArrowUp: from + 5, ArrowDown: from - 5, PageUp: from + 25, PageDown: from - 25, Home: 100, End: 0 };
    if (ev.key in step) {
      // during a storm every key goes to the end in its direction
      this._drag = this.storm ? (step[ev.key] > from ? 100 : 0) : snap(step[ev.key], false);
      ev.preventDefault();
    } else if (ev.key === "Enter" && this._drag !== null) {
      this.send();
      this._drag = null;
      ev.preventDefault();
    } else if (ev.key === "Escape") {
      this._drag = null;
    }
  }

  private send() {
    if (this._drag === null) return;
    this.dispatchEvent(new CustomEvent("set-position", { detail: { position: this._drag }, bubbles: true, composed: true }));
  }

  render() {
    const p = this.position ?? 0;
    const barY = yForPosition(p, BAR);
    const shift = barY - BAR.bottom;
    const handle = this.interactive && !this.compact;
    const maxY = yForPosition(this.max, BAR);
    const viewBox = this.compact ? `46 0 192 ${VIEW_H}` : `-16 0 256 ${VIEW_H}`;
    return html`<svg
      class=${this.interactive ? "interactive" : ""}
      viewBox=${viewBox}
      role=${this.interactive ? "slider" : "img"}
      tabindex=${this.interactive ? "0" : "-1"}
      aria-label=${this.label}
      aria-valuemin="0"
      aria-valuemax="100"
      aria-valuenow=${this._drag ?? p}
      aria-valuetext=${`${this._drag ?? p} %`}
      @pointerdown=${this.onDown}
      @pointermove=${this.onMove}
      @pointerup=${this.onUp}
      @pointercancel=${this.onCancel}
      @keydown=${this.onKey}
    >
      <defs>
        <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="var(--ssc-glass-1)"></stop><stop offset="1" stop-color="var(--ssc-glass-2)"></stop>
        </linearGradient>
        <linearGradient id="slat" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="var(--ssc-slat-1)"></stop><stop offset="1" stop-color="var(--ssc-slat-2)"></stop>
        </linearGradient>
        <pattern id="slats" width="10" height="13" patternUnits="userSpaceOnUse" y="-3">
          <rect width="10" height="13" fill="url(#slat)"></rect><line x1="0" y1="12" x2="10" y2="12" stroke="var(--ssc-slat-line)" stroke-width="1.5"></line>
        </pattern>
        <!-- open slats: between two slats a row of separate slots with bridges; the slots are transparent,
             so the window (and what is outside) shows through -->
        <pattern id="slats-open" width="12" height="13" patternUnits="userSpaceOnUse" x="2" y="-3">
          <rect width="12" height="10.5" fill="url(#slat)"></rect>
          <rect y="10.5" width="3" height="2.5" fill="var(--ssc-slat-line)"></rect>
        </pattern>
        <clipPath id="opening"><rect x="58" y="40" width="168" height="208"></rect></clipPath>
      </defs>
      <rect class="frame" x="52" y="24" width="180" height="230" rx="6" fill="none" stroke="var(--ssc-frame)" stroke-width="4"></rect>
      <rect x="64" y="40" width="156" height="206" fill="url(#glass)"></rect>
      <rect x="58" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <rect x="220" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <g clip-path="url(#opening)">
        <g class="curtain" style=${`transform: translateY(${shift}px)`}>
          <rect class="slats ${this.gaps ? "open" : "closed"}" x="64" y="-170" width="156" height="406" fill=${this.gaps ? "url(#slats-open)" : "url(#slats)"}></rect>
          <rect class="bar" x="60" y="236" width="164" height="10" rx="3" fill="var(--ssc-bar)"></rect>
          ${handle
            ? svg`<rect x="124" y="230" width="36" height="22" rx="11" fill="var(--ssc-accent)" stroke="#fff" stroke-width="2"></rect>
                 <line x1="134" y1="238" x2="150" y2="238" stroke="#fff" stroke-width="2"></line>
                 <line x1="134" y1="244" x2="150" y2="244" stroke="#fff" stroke-width="2"></line>`
            : ""}
        </g>
      </g>
      <rect x="46" y="6" width="192" height="34" rx="6" fill="var(--ssc-box)" stroke="var(--ssc-frame)" stroke-width="3"></rect>
      ${this.moving
        ? svg`<path class="moving" d=${this.moving === "opening" ? "M142 15 l8 10 h-16 z" : "M142 31 l8 -10 h-16 z"} fill="var(--ssc-accent)"></path>`
        : ""}
      ${this.max < 100
        ? svg`<line class="max" x1=${this.compact ? 46 : 28} x2=${this.compact ? 58 : 46} y1=${maxY} y2=${maxY} stroke="var(--ssc-max)" stroke-width="3"></line>
             ${this.compact ? "" : svg`<text x="46" y=${maxY + 15} font-size="11" text-anchor="end" fill="var(--ssc-max)">${this.maxLabel} ${this.max} %</text>`}`
        : ""}
      ${this._drag !== null
        ? svg`<g class="target">
            <rect x="60" y=${yForPosition(this._drag, BAR) - 5} width="164" height="10" rx="3" fill="var(--ssc-accent)" opacity="0.45"></rect>
            <text x="142" y=${yForPosition(this._drag, BAR) - 10} font-size="16" font-weight="700" text-anchor="middle" fill="var(--ssc-accent)">${this._drag} %</text>
          </g>`
        : ""}
    </svg>`;
  }
}
