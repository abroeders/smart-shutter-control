// Position ↔ height in the drawing. 100 % open puts the bottom bar at the top of the glass.

export interface Box {
  top: number;
  bottom: number;
}

export const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

export function yForPosition(position: number, box: Box): number {
  return box.top + (1 - clamp(position, 0, 100) / 100) * (box.bottom - box.top);
}

export function positionForY(y: number, box: Box): number {
  return Math.round(clamp((box.bottom - y) / (box.bottom - box.top), 0, 1) * 100);
}

/** During a storm only the ends exist (the integration does the same). */
export function snap(position: number, storm: boolean): number {
  const p = clamp(Math.round(position), 0, 100);
  return storm ? (p >= 50 ? 100 : 0) : p;
}
