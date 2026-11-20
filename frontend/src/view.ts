// What the cartoon scene looks like through the window glass.

import { css, svg, type CSSResult, type SVGTemplateResult } from "lit";
import type { Scene } from "./scene";

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

export function renderView(scene: Scene, box: Box, animated: boolean): SVGTemplateResult {
  const gradientId = "ssc-view-sky";
  const clipId = "ssc-view-precip";
  const hillTop = box.y + 0.72 * box.h;

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
  const hillD = `M ${box.x} ${hillTop} C ${box.x + 0.22 * box.w} ${hillTop - 0.08 * box.h}, ${box.x + 0.42 * box.w} ${hillTop + 0.03 * box.h}, ${box.x + 0.58 * box.w} ${hillTop - 0.05 * box.h} S ${box.x + 0.82 * box.w} ${hillTop + 0.02 * box.h}, ${box.x + box.w} ${hillTop - 0.02 * box.h} L ${box.x + box.w} ${box.y + box.h} L ${box.x} ${box.y + box.h} Z`;

  const treeSpecs = [
    { fx: 0.25, base: hillTop + 0.01 * box.h, height: 0.19 * box.h },
    { fx: 0.72, base: hillTop + 0.015 * box.h, height: 0.22 * box.h },
    { fx: 0.50, base: hillTop - 0.025 * box.h, height: 0.13 * box.h },
  ];
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

  const cloudTemplates: SVGTemplateResult[] = [];
  if (scene.clouds === "few") {
    const cloudData = [{ x: 0.18, y: 0.18 }, { x: 0.68, y: 0.28 }];
    for (const cloud of cloudData) {
      const cx = box.x + cloud.x * box.w;
      const cy = box.y + cloud.y * box.h;
      cloudTemplates.push(svg`<g class=${animated ? "cloud drift" : "cloud"} opacity="0.95">
        <ellipse cx=${cx - 8} cy=${cy} rx="10" ry="5" fill="#fff"></ellipse>
        <ellipse cx=${cx + 2} cy=${cy - 4} rx="12" ry="8" fill="#fff"></ellipse>
        <ellipse cx=${cx + 14} cy=${cy} rx="11" ry="5" fill="#fff"></ellipse>
      </g>`);
    }
  } else if (scene.clouds === "overcast") {
    const colors = ["#90a4ae", "#78909c"];
    for (let i = 0; i < 4; i++) {
      const cx = box.x + (0.08 + i * 0.28) * box.w;
      const cy = box.y + (0.12 + (i % 2) * 0.06) * box.h;
      cloudTemplates.push(svg`<g class=${animated ? "cloud drift" : "cloud"} opacity="0.95">
        <ellipse cx=${cx - 10} cy=${cy} rx="13" ry="7" fill=${colors[i % 2]}></ellipse>
        <ellipse cx=${cx + 2} cy=${cy - 5} rx="16" ry="11" fill=${colors[i % 2]}></ellipse>
        <ellipse cx=${cx + 16} cy=${cy} rx="14" ry="7" fill=${colors[i % 2]}></ellipse>
      </g>`);
    }
  }

  return svg`
    <defs>
      <linearGradient id=${gradientId} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color=${scene.sky[0]}></stop>
        <stop offset="1" stop-color=${scene.sky[1]}></stop>
      </linearGradient>
      <clipPath id=${clipId}><rect x=${box.x} y=${box.y} width=${box.w} height=${box.h}></rect></clipPath>
    </defs>
    <g class="sky"><rect x=${box.x} y=${box.y} width=${box.w} height=${box.h} fill=${`url(#${gradientId})`}></rect></g>
    ${scene.stars > 0 && scene.clouds !== "overcast" ? svg`<g class="stars" opacity=${scene.stars}>${starTemplates}</g>` : ""}
    ${scene.moon ? svg`<g class="moon">
      <circle cx=${box.x + scene.moon.x * box.w} cy=${box.y + scene.moon.y * box.h} r=${0.095 * box.w} fill="#fff8e1" opacity="0.15"></circle>
      ${moonPath(box.x + scene.moon.x * box.w, box.y + scene.moon.y * box.h, 0.07 * box.w, scene.moon.phase)}
    </g>` : ""}
    ${scene.sun ? svg`<g class="sun">
      <circle cx=${box.x + scene.sun.x * box.w} cy=${box.y + scene.sun.y * box.h} r=${0.13 * box.w} fill="#ffd54f" opacity="0.25"></circle>
      <circle class="sun-disc" cx=${box.x + scene.sun.x * box.w} cy=${box.y + scene.sun.y * box.h} r=${0.08 * box.w} fill="#ffd54f"></circle>
    </g>` : ""}
    ${scene.clouds !== "none" ? svg`<g class="clouds">${cloudTemplates}</g>` : ""}
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
