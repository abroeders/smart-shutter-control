// What tests verify the scene renderer's stable SVG layers and classes.

import { html, render } from "lit";
import { afterEach, describe, expect, it } from "vitest";
import { landscape, type Scene } from "../src/scene";
import { renderView } from "../src/view";

const BOX = { x: 64, y: 40, w: 156, h: 206 };

function baseScene(overrides: Partial<Scene> = {}): Scene {
  return {
    light: "day",
    sky: ["#42a5f5", "#bbdefb"],
    stars: 0,
    sun: null,
    glow: 0.25,
    veil: null,
    path: [],
    moon: null,
    cover: 0,
    cloudCount: 0,
    overcast: false,
    sideLight: null,
    landscape: landscape(180),
    precipitation: "none",
    fog: false,
    lightning: false,
    season: "summer",
    snowGround: false,
    sway: 0,
    slant: 0,
    dim: 0,
    ...overrides,
  };
}

function draw(scene: Scene, animated = false): HTMLElement {
  const container = document.createElement("div");
  render(html`<svg>${renderView(scene, BOX, animated)}</svg>`, container);
  document.body.appendChild(container);
  return container;
}

afterEach(() => {
  document.body.innerHTML = "";
});

describe("view", () => {
  it("shows stars at night and not a sun", () => {
    const root = draw(baseScene({ light: "night", stars: 1 }));
    expect(root.querySelectorAll("g.stars circle").length).toBe(30);
    expect(root.querySelector("g.sun")).toBeNull();
  });

  it("shows a sun in day scenes", () => {
    const root = draw(baseScene({ sun: { x: 0.5, y: 0.3 } }));
    expect(root.querySelector("circle.sun-disc")).not.toBeNull();
  });

  it("uses overcast clouds without stars", () => {
    const root = draw(baseScene({ overcast: true, cover: 0.9, stars: 1 }));
    expect(root.querySelectorAll("g.clouds .cloud").length).toBe(4);
    expect(root.querySelector("g.stars")).toBeNull();
  });

  it("draws as many clouds as the cover asks", () => {
    expect(draw(baseScene({ cloudCount: 3, cover: 0.5 })).querySelectorAll("g.clouds .cloud").length).toBe(3);
    expect(draw(baseScene()).querySelector("g.clouds")).toBeNull();
  });

  it("puts a cloud in front of a dim sun, aside as it brightens", () => {
    const veilX = (offset: number) => {
      const root = draw(baseScene({ sun: { x: 0.5, y: 0.3 }, veil: { opacity: 0.5, offset } }));
      const cloud = root.querySelector("g.veil .veil-cloud")!;
      expect(cloud.getAttribute("opacity")).toBe("0.5");
      return Number(cloud.querySelector("ellipse")!.getAttribute("cx"));
    };
    expect(veilX(2)).toBeGreaterThan(veilX(0));
    expect(draw(baseScene({ sun: { x: 0.5, y: 0.3 } })).querySelector("g.veil")).toBeNull();
  });

  it("draws the sun's path and the light on the sun's side", () => {
    const root = draw(baseScene({ path: [[{ x: 0.1, y: 0.6 }, { x: 0.5, y: 0.4 }, { x: 0.9, y: 0.6 }]], sideLight: { x: 0.2, strength: 0.5 } }));
    expect(root.querySelectorAll("g.sun-path polyline").length).toBe(1);
    expect(root.querySelector("rect.side-light")).not.toBeNull();
  });

  it("draws the landscape of the window direction", () => {
    const trees = (azimuth: number) => draw(baseScene({ landscape: landscape(azimuth) })).querySelectorAll("g.tree").length;
    expect(trees(0)).toBe(landscape(0).trees.length);
    expect(trees(180)).toBe(landscape(180).trees.length);
  });

  it("draws rain lines and snow circles", () => {
    const rain = draw(baseScene({ precipitation: "rain", slant: 8 }));
    expect(rain.querySelectorAll("g.precip line").length).toBeGreaterThanOrEqual(25);
    document.body.innerHTML = "";
    const snow = draw(baseScene({ precipitation: "snow", season: "winter", snowGround: true }));
    expect(snow.querySelectorAll("g.precip circle").length).toBeGreaterThanOrEqual(25);
    expect(snow.querySelector("path.hill")?.getAttribute("fill")).toBe("#eceff1");
  });

  it("draws winter branches instead of crown circles", () => {
    const root = draw(baseScene({ season: "winter", snowGround: true }));
    expect(root.querySelectorAll("circle.crown").length).toBe(0);
    expect(root.querySelectorAll("line.branch").length).toBeGreaterThanOrEqual(9);
  });

  it("animates swaying trees and leaves static scenes unanimated", () => {
    const animated = draw(baseScene({ sway: 6 }), true);
    expect(animated.querySelectorAll("g.tree.sway").length).toBe(3);
    document.body.innerHTML = "";
    const staticView = draw(baseScene({ sway: 6 }), false);
    expect(staticView.querySelector(".twinkle, .drift, .sway, .fall, .flash")).toBeNull();
  });
});
