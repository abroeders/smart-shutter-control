import { afterEach, describe, expect, it } from "vitest";
import "../src/index";
import { BASE, KITCHEN, LIVING, fakeHass } from "./fixtures";

async function mount(hass = fakeHass(), config: Record<string, unknown> = {}) {
  const card = document.createElement("smart-shutter-card") as any;
  card.setConfig({ type: "custom:smart-shutter-card", device_id: LIVING, ...config });
  card.hass = hass;
  document.body.appendChild(card);
  await card.updateComplete;
  const drawing = card.shadowRoot.querySelector("ssc-drawing");
  if (drawing) await drawing.updateComplete;
  return card;
}

/** jsdom has no PointerEvent and no layout: a MouseEvent and a fixed box are enough. */
function pointer(type: string, clientY: number): Event {
  return Object.assign(new MouseEvent(type, { clientY, bubbles: true }), { pointerId: 1 });
}

function layout(drawing: any) {
  const svg = drawing.shadowRoot.querySelector("svg");
  svg.getBoundingClientRect = () => ({ top: 0, left: 0, width: 240, height: 262, right: 240, bottom: 262 });
  return svg;
}

const text = (card: any) => card.shadowRoot.textContent.replace(/[\s\u00a0]+/g, " ");

afterEach(() => {
  document.body.innerHTML = "";
});

describe("card", () => {
  it("registers itself in the card picker", () => {
    expect((window as any).customCards.some((c: any) => c.type === "smart-shutter-card" && c.preview)).toBe(true);
  });

  it("shows one shutter with its status", async () => {
    const card = await mount();
    const t = text(card);
    for (const s of ["Living room", "Automatic", "62 %", "partly open", "Sun on the window", "Next: 16:55 dusk 35 %", "then 17:10 closed", "Sleep in"]) expect(t).toContain(s);
    const drawing = card.shadowRoot.querySelector("ssc-drawing");
    expect(drawing.shadowRoot.querySelector("line.max")).not.toBeNull();
    expect(drawing.shadowRoot.textContent).toContain("max 80\u00a0%");
    expect(card.getGridOptions()).toEqual({ columns: 12, min_columns: 6, rows: "auto" });
  });

  it("drags the shutter to a position", async () => {
    const hass = fakeHass();
    const card = await mount(hass);
    const drawing = card.shadowRoot.querySelector("ssc-drawing");
    const svg = layout(drawing);
    svg.dispatchEvent(pointer("pointerdown", 100));
    svg.dispatchEvent(pointer("pointermove", 140));
    await drawing.updateComplete;
    expect(drawing.shadowRoot.querySelector(".target")).not.toBeNull();
    svg.dispatchEvent(pointer("pointerup", 140.5)); // y 140.5 of 262 → bar half way: 50 %
    expect(hass.calls).toEqual([{ domain: "cover", service: "set_cover_position", data: { entity_id: "cover.living", position: 50 } }]);
  });

  it("does not move on a tap, and only to an end during a storm", async () => {
    const hass = fakeHass({ "binary_sensor.storm": { state: "on", attributes: {} } });
    const card = await mount(hass);
    expect(text(card)).toContain("Storm: only open/closed");
    const drawing = card.shadowRoot.querySelector("ssc-drawing");
    const svg = layout(drawing);
    svg.dispatchEvent(pointer("pointerdown", 100));
    svg.dispatchEvent(pointer("pointerup", 101));
    expect(hass.calls).toEqual([]);
    svg.dispatchEvent(pointer("pointerdown", 100));
    svg.dispatchEvent(pointer("pointerup", 120)); // 60 %: open
    expect(hass.calls[0].data.position).toBe(100);
  });

  it("works with the keyboard", async () => {
    const hass = fakeHass();
    const card = await mount(hass);
    const drawing = card.shadowRoot.querySelector("ssc-drawing");
    const svg = drawing.shadowRoot.querySelector("svg");
    expect(svg.getAttribute("role")).toBe("slider");
    for (const key of ["ArrowDown", "ArrowDown", "Enter"]) svg.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
    svg.dispatchEvent(new KeyboardEvent("keydown", { key: "End", bubbles: true }));
    svg.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    expect(hass.calls.map((c) => c.data.position)).toEqual([52, 0]);
  });

  it("calls open, stop and close and the switches", async () => {
    const hass = fakeHass();
    const card = await mount(hass);
    const buttons = [...card.shadowRoot.querySelectorAll(".buttons button")] as HTMLElement[];
    buttons.forEach((b) => b.click());
    card.shadowRoot.querySelector(".switch.automatic").click();
    card.shadowRoot.querySelector(".switch.sleep-in").click();
    expect(hass.calls.map((c) => `${c.domain}.${c.service} ${c.data.entity_id}`)).toEqual([
      "cover.open_cover cover.living",
      "cover.stop_cover cover.living",
      "cover.close_cover cover.living",
      "switch.turn_off switch.living_automatic",
      "switch.turn_on switch.living_sleep_in",
    ]);
  });

  it("offers resume during a manual pause", async () => {
    const hass = fakeHass({ "binary_sensor.living_manual_pause": { state: "on", attributes: { until: "next phase" } } });
    const card = await mount(hass);
    expect(text(card)).toContain("until the next phase");
    card.shadowRoot.querySelector(".resume").click();
    expect(hass.calls[0]).toMatchObject({ domain: "button", service: "press", data: { entity_id: "button.living_resume" } });
  });

  it("follows the integration's language, and the card's own option", async () => {
    const hass = fakeHass({ "sensor.living_reason": { state: "sun", attributes: { target_position: 30, max_position: 80, language: "nl" } } });
    expect(text(await mount(hass))).toContain("Zon op het raam");
    document.body.innerHTML = "";
    expect(text(await mount(hass, { language: "en" }))).toContain("Sun on the window");
  });

  it("shows all shutters of a base controller", async () => {
    const hass = fakeHass();
    const card = await mount(hass, { device_id: BASE });
    const tiles = card.shadowRoot.querySelectorAll(".tile");
    expect(tiles.length).toBe(2);
    expect(text(card)).toContain("All shutters");
    expect(text(card)).toContain("Kitchen");
    expect(text(card)).toContain("closed · Sleeping in");
    expect(card.getGridOptions().columns).toBe("full");
    let info = "";
    card.addEventListener("hass-more-info", (e: any) => (info = e.detail.entityId));
    (tiles[0] as HTMLElement).click();
    expect(info).toBe("cover.kitchen");
    card.shadowRoot.querySelector(".switch.sleep-in-all").click();
    expect(hass.calls[0]).toMatchObject({ service: "turn_on", data: { entity_id: "switch.sleep_in_all" } });
  });

  it("explains a missing device", async () => {
    expect(text(await mount(fakeHass(), { device_id: undefined }))).toContain("Choose a shutter");
    document.body.innerHTML = "";
    expect(text(await mount(fakeHass(), { device_id: "nope" }))).toContain("Device not found");
    expect(KITCHEN).toBeTruthy();
  });
});
