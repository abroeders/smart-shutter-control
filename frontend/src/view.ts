// What the cartoon scene looks like through the window glass.

import { css, svg, type CSSResult, type SVGTemplateResult } from "lit";
import type { Place, Scene } from "./scene";

export interface Box { x: number; y: number; w: number; h: number }

function seededRandom(seed: number): () => number {
  let value = seed >>> 0;
  return () => {
    value = (Math.imul(value, 1664525) + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

export const viewStyles: CSSResult = css`
  .twinkle { transform-box: view-box; transform-origin: center; animation: ssc-twinkle 4s ease-in-out infinite alternate; }
  .drift { transform-box: view-box; animation: ssc-drift 36s ease-in-out infinite alternate; }
  .sway { transform-box: view-box; animation: ssc-sway var(--sway-speed, 2.5s) ease-in-out infinite alternate; }
  .fall { animation: ssc-fall var(--fall-speed, 3s) linear infinite; }
  .flash { animation: ssc-flash 6s linear infinite; }
  @keyframes ssc-twinkle {
    0%, 70% { opacity: 0.45; }
    100% { opacity: 1; }
  }
  @keyframes ssc-drift {
    from { transform: translateX(-6px); }
    to { transform: translateX(6px); }
  }
  @keyframes ssc-sway {
    from { transform: rotate(calc(var(--sway) * -1)); }
    to { transform: rotate(var(--sway)); }
  }
  @keyframes ssc-fall {
    from { transform: translateY(var(--fall-from, -206px)); }
    to { transform: translateY(var(--fall-to, 206px)); }
  }
  @keyframes ssc-flash {
    0%, 92%, 100% { opacity: 0; }
    93%, 95% { opacity: 1; }
    94%, 96% { opacity: 0.15; }
  }
  @media (prefers-reduced-motion: reduce) {
    .twinkle, .drift, .sway, .fall, .flash { animation: none !important; }
  }
`;

function moonPath(cx: number, cy: number, r: number, phase: number): SVGTemplateResult | "" {
  if (phase < 0.03 || phase > 0.97) return "";
  if (phase > 0.97 - 0.0001 || Math.abs(phase - 0.5) < 0.0001) {
    return svg`<circle class="moon-disc" cx=${cx} cy=${cy} r=${r} fill="#fff8e1"></circle>`;
  }
  const waxing = phase < 0.5;
  const rx = r * Math.abs(Math.cos(2 * Math.PI * phase));
  const limbSweep = waxing ? 1 : 0;
  const terminatorSweep = waxing ? 1 : 0;
  const d = `M ${cx} ${cy-r} A ${r} ${r} 0 0 ${limbSweep} ${cx} ${cy+r} A ${rx} ${r} 0 0 ${terminatorSweep} ${cx} ${cy-r} Z`;
  return svg`<path class="moon-disc" d=${d} fill="#fff8e1"></path>`;
}

function cloud(cx: number, cy: number, scale: number, color: string, cls: string, opacity = 0.95): SVGTemplateResult {
  return svg`<g class=${cls} opacity=${opacity}>
    <ellipse cx=${cx - 8 * scale} cy=${cy} rx=${10 * scale} ry=${5 * scale} fill=${color}></ellipse>
    <ellipse cx=${cx + 2 * scale} cy=${cy - 4 * scale} rx=${12 * scale} ry=${8 * scale} fill=${color}></ellipse>
    <ellipse cx=${cx + 14 * scale} cy=${cy} rx=${11 * scale} ry=${5 * scale} fill=${color}></ellipse>
  </g>`;
}

/** Fixed places for up to six clouds, spread over the sky; filled in this order. */
const CLOUD_SLOTS = [
  { x: 0.18, y: 0.18 }, { x: 0.68, y: 0.28 }, { x: 0.45, y: 0.12 },
  { x: 0.86, y: 0.15 }, { x: 0.3, y: 0.34 }, { x: 0.06, y: 0.3 },
];

export function renderView(scene: Scene, box: Box, animated: boolean): SVGTemplateResult {
  const gradientId = "ssc-view-sky";
  const sideId = "ssc-view-side";
  const clipId = "ssc-view-precip";
  const hillTop = box.y + 0.72 * box.h;
  const at = (place: Place) => ({ x: box.x + place.x * box.w, y: box.y + place.y * box.h });

  const stars = seededRandom(20261124);
  const starTemplates: SVGTemplateResult[] = [];
  for (let i = 0; i < 30; i++) {
    const x = box.x + stars() * box.w;
    const y = box.y + stars() * box.h * 0.55;
    const r = 0.6 + stars() * 0.8;
    const twinkle = animated && i % 7 === 0;
    const delay = `${(i % 5) * 0.35}s`;
    starTemplates.push(svg`<circle class=${twinkle ? "star twinkle" : "star"} cx=${x} cy=${y} r=${r} fill="#fff" style=${twinkle ? `animation-delay:${delay};opacity:${scene.stars}` : `opacity:${scene.stars}`}></circle>`);
  }

  const hillColor = scene.snowGround ? "#eceff1"
    : scene.season === "spring" ? "#8bc34a"
    : scene.season === "summer" ? "#7cb342"
    : scene.season === "autumn" ? "#9e9d24"
    : "#a1887f";
  const [h1, h2, h3, h4] = scene.landscape.hill.map((offset) => hillTop + offset * box.h);
  const hillD = `M ${box.x} ${hillTop} C ${box.x + 0.22 * box.w} ${h1}, ${box.x + 0.42 * box.w} ${h2}, ${box.x + 0.58 * box.w} ${h3} S ${box.x + 0.82 * box.w} ${h4}, ${box.x + box.w} ${hillTop - 0.02 * box.h} L ${box.x + box.w} ${box.y + box.h} L ${box.x} ${box.y + box.h} Z`;

  // a tree stands on the hill: the hill's height at its place, roughly
  const hillAt = (fx: number) => hillTop + (fx < 0.5 ? scene.landscape.hill[0] : scene.landscape.hill[2]) * box.h * 0.5 + 0.01 * box.h;
  const treeSpecs = scene.landscape.trees.map((tree) => ({ fx: tree.x, base: hillAt(tree.x), height: tree.height * box.h }));
  const treeTemplates: SVGTemplateResult[] = treeSpecs.map((tree) => {
    const tx = box.x + tree.fx * box.w;
    const ty = tree.base - tree.height;
    const trunkWidth = Math.max(2.5, box.w * 0.018);
    const crownRadius = Math.max(5, tree.height * 0.23);
    const swayClass = animated && scene.sway > 0 ? " sway" : "";
    const staticLean = !animated && scene.sway > 0 ? ` rotate(${scene.sway / 2} ${tx} ${tree.base})` : "";
    const style = `transform-origin:${tx}px ${tree.base}px;--sway:${scene.sway}deg;--sway-speed:${scene.sway > 8 ? "1.2s" : "2.5s"}`;
    let foliage: SVGTemplateResult;
    if (scene.season === "winter") {
      const branchLines = [-1, -0.35, 0.35, 1].map((side) =>
        svg`<line class="branch" x1=${tx} y1=${tree.base - tree.height * 0.58} x2=${tx + side * crownRadius * 1.15} y2=${tree.base - tree.height * (0.68 + Math.abs(side) * 0.15)} stroke="#6d4c41" stroke-width="1.2"></line>`,
      );
      foliage = svg`<g class="winter">${branchLines}${scene.snowGround ? svg`<line x1=${tx - crownRadius} y1=${ty + crownRadius * 0.45} x2=${tx - crownRadius * 0.35} y2=${ty + crownRadius * 0.25} stroke="#eceff1" stroke-width="1.8"></line>` : ""}</g>`;
    } else {
      const colors = scene.season === "spring" ? ["#9ccc65", "#9ccc65", "#9ccc65", "#9ccc65"]
        : scene.season === "summer" ? ["#388e3c", "#43a047", "#388e3c", "#43a047"]
        : ["#ef6c00", "#d84315", "#f9a825", "#ef6c00"];
      const positions = [
        [tx - crownRadius * 0.45, ty + crownRadius * 0.45],
        [tx + crownRadius * 0.45, ty + crownRadius * 0.45],
        [tx, ty],
        [tx, ty + crownRadius * 0.72],
      ];
      foliage = svg`<g class="foliage">${positions.map(([cx, cy], i) => svg`<circle class="crown" cx=${cx} cy=${cy} r=${crownRadius} fill=${colors[i]}></circle>`)}${scene.season === "spring" ? svg`<circle cx=${tx - crownRadius * 0.9} cy=${ty + crownRadius * 0.1} r="1.3" fill="#f8bbd0"></circle><circle cx=${tx + crownRadius * 0.8} cy=${ty + crownRadius * 0.7} r="1.3" fill="#f8bbd0"></circle>` : ""}</g>`;
    }
    return svg`<g class=${`tree${swayClass}`} style=${style} transform=${staticLean || undefined}>
      <rect x=${tx - trunkWidth / 2} y=${tree.base - tree.height * 0.58} width=${trunkWidth} height=${tree.height * 0.58} rx="1" fill="#6d4c41"></rect>
      ${foliage}
    </g>`;
  });

  const precipitationRandom = seededRandom(481516);
  const precipCount = scene.precipitation === "pouring" ? 45 : 25;
  const precipTemplates: SVGTemplateResult[] = [];
  if (scene.precipitation === "rain" || scene.precipitation === "pouring") {
    for (let i = 0; i < precipCount; i++) {
      const x = box.x + precipitationRandom() * box.w;
      const y = box.y + precipitationRandom() * box.h;
      const length = 4 + precipitationRandom() * 3;
      const slant = scene.slant * 0.12;
      const cls = animated ? "fall" : "";
      const duration = `${0.7 + precipitationRandom() * 0.4}s`;
      const delay = `-${precipitationRandom() * 1.1}s`;
      precipTemplates.push(svg`<line class=${cls} x1=${x} y1=${y} x2=${x + slant} y2=${y + length} stroke="#90caf9" stroke-width="1" style=${animated ? `--fall-from:-${box.h}px;--fall-to:${box.h}px;--fall-speed:${duration};animation-delay:${delay}` : ""}></line>`);
    }
  } else if (scene.precipitation === "snow" || scene.precipitation === "sleet") {
    const snowCount = scene.precipitation === "sleet" ? 12 : precipCount;
    for (let i = 0; i < precipCount; i++) {
      const x = box.x + precipitationRandom() * box.w;
      const y = box.y + precipitationRandom() * box.h;
      const r = 1.2 + precipitationRandom() * 1;
      const isDrop = scene.precipitation === "sleet" && i >= snowCount;
      const cls = animated ? "fall" : "";
      const duration = `${4 + precipitationRandom() * 3}s`;
      const delay = `-${precipitationRandom() * 6}s`;
      precipTemplates.push(isDrop
        ? svg`<line class=${cls} x1=${x} y1=${y} x2=${x + scene.slant * 0.12} y2=${y + 5} stroke="#90caf9" stroke-width="1" style=${animated ? `--fall-from:-${box.h}px;--fall-to:${box.h}px;--fall-speed:${duration};animation-delay:${delay}` : ""}></line>`
        : svg`<circle class=${cls} cx=${x} cy=${y} r=${r} fill="#fff" style=${animated ? `--fall-from:-${box.h}px;--fall-to:${box.h}px;--fall-speed:${duration};animation-delay:${delay}` : ""}></circle>`);
    }
  }

  const drift = animated ? "cloud drift" : "cloud";
  const cloudTemplates: SVGTemplateResult[] = CLOUD_SLOTS.slice(0, scene.cloudCount).map((slot) =>
    cloud(box.x + slot.x * box.w, box.y + slot.y * box.h, 1, scene.cover >= 0.55 ? "#eceff1" : "#fff", drift));
  if (scene.overcast) {
    const colors = ["#90a4ae", "#78909c"];
    for (let i = 0; i < 4; i++) {
      const cx = box.x + (0.08 + i * 0.28) * box.w;
      const cy = box.y + (0.12 + (i % 2) * 0.06) * box.h;
      cloudTemplates.push(cloud(cx, cy, 1.3, colors[i % 2], drift));
    }
  }

  const sun = scene.sun ? at(scene.sun) : null;
  const sunRadius = 0.08 * box.w;
  const veilScale = sunRadius / 12; // the cloud is about 3.5 sun radii wide
  const paths = scene.path.map((piece) => piece.map((place) => { const p = at(place); return `${p.x.toFixed(1)},${p.y.toFixed(1)}`; }).join(" "));

  return svg`
    <defs>
      <linearGradient id=${gradientId} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color=${scene.sky[0]}></stop>
        <stop offset="1" stop-color=${scene.sky[1]}></stop>
      </linearGradient>
      ${scene.sideLight ? svg`<radialGradient id=${sideId} gradientUnits="userSpaceOnUse" cx=${box.x + scene.sideLight.x * box.w} cy=${hillTop} r=${0.75 * box.w}>
        <stop offset="0" stop-color="#ffe0b2" stop-opacity=${scene.sideLight.strength}></stop>
        <stop offset="1" stop-color="#ffe0b2" stop-opacity="0"></stop>
      </radialGradient>` : ""}
      <clipPath id=${clipId}><rect x=${box.x} y=${box.y} width=${box.w} height=${box.h}></rect></clipPath>
    </defs>
    <g class="sky"><rect x=${box.x} y=${box.y} width=${box.w} height=${box.h} fill=${`url(#${gradientId})`}></rect>
      ${scene.sideLight ? svg`<rect class="side-light" x=${box.x} y=${box.y} width=${box.w} height=${box.h} fill=${`url(#${sideId})`}></rect>` : ""}</g>
    ${paths.length ? svg`<g class="sun-path" clip-path=${`url(#${clipId})`}>${paths.map((points) => svg`<polyline points=${points} fill="none" stroke="#fff8e1" stroke-opacity="0.55" stroke-width="1" stroke-dasharray="1.5 3" stroke-linecap="round"></polyline>`)}</g>` : ""}
    ${scene.stars > 0 && !scene.overcast ? svg`<g class="stars" opacity=${scene.stars}>${starTemplates}</g>` : ""}
    ${scene.moon ? svg`<g class="moon">
      <circle cx=${box.x + scene.moon.x * box.w} cy=${box.y + scene.moon.y * box.h} r=${0.095 * box.w} fill="#fff8e1" opacity="0.15"></circle>
      ${moonPath(box.x + scene.moon.x * box.w, box.y + scene.moon.y * box.h, 0.07 * box.w, scene.moon.phase)}
    </g>` : ""}
    ${sun ? svg`<g class="sun">
      ${scene.glow > 0 ? svg`<circle class="sun-glow" cx=${sun.x} cy=${sun.y} r=${0.13 * box.w} fill="#ffd54f" opacity=${scene.glow}></circle>` : ""}
      <circle class="sun-disc" cx=${sun.x} cy=${sun.y} r=${sunRadius} fill="#ffd54f" opacity=${scene.veil ? (1 - 0.45 * scene.veil.opacity).toFixed(2) : 1}></circle>
    </g>` : ""}
    ${cloudTemplates.length ? svg`<g class="clouds">${cloudTemplates}</g>` : ""}
    ${sun && scene.veil ? svg`<g class="veil">${cloud(sun.x + scene.veil.offset * sunRadius - 3.5 * veilScale, sun.y + 2 * veilScale, veilScale, "#b0bec5", "veil-cloud", scene.veil.opacity)}</g>` : ""}
    <g class="land" style=${scene.dim > 0 ? `filter: brightness(${(1 - scene.dim).toFixed(2)})` : ""}>
      <path class="hill" d=${hillD} fill=${hillColor}></path>
      ${treeTemplates}
    </g>
    ${scene.precipitation !== "none" ? svg`<g class="precip" clip-path=${`url(#${clipId})`}>${precipTemplates}</g>` : ""}
    ${scene.fog ? svg`<g class="fog">
      <ellipse cx=${box.x + 0.2 * box.w} cy=${box.y + 0.82 * box.h} rx=${0.25 * box.w} ry=${0.05 * box.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${box.x + 0.58 * box.w} cy=${box.y + 0.88 * box.h} rx=${0.32 * box.w} ry=${0.06 * box.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${box.x + 0.9 * box.w} cy=${box.y + 0.78 * box.h} rx=${0.2 * box.w} ry=${0.04 * box.h} fill="#fff" opacity="0.5"></ellipse>
    </g>` : ""}
    ${scene.lightning && animated ? svg`<g class="lightning"><polyline class="flash" points=${`${box.x + 0.72 * box.w},${box.y + 0.08 * box.h} ${box.x + 0.68 * box.w},${box.y + 0.25 * box.h} ${box.x + 0.74 * box.w},${box.y + 0.22 * box.h} ${box.x + 0.69 * box.w},${box.y + 0.42 * box.h}`} fill="none" stroke="#ffd54f" stroke-width="2"></polyline></g>` : ""}
  `;
}
