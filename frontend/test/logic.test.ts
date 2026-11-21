import { describe, expect, it } from "vitest";
import { baseOf, deviceEntities, integrationDevices, isShutter, shuttersOf } from "../src/entities";
import { positionForY, snap, yForPosition } from "../src/geometry";
import { localizer } from "../src/localize";
import { cardLanguage, decisionLines, formatTime, positionText, shutterModel, statusLines } from "../src/viewmodel";
import { BASE, KITCHEN, LIVING, fakeHass } from "./fixtures";

const BOX = { top: 40, bottom: 240 };
/** the status lines with normal spaces instead of the no-break space before % */
const nbsp = <T extends object>(o: T): T => JSON.parse(JSON.stringify(o).replace(/\u00a0/g, " "));

describe("geometry", () => {
  it("maps positions to heights and back", () => {
    expect(yForPosition(100, BOX)).toBe(40);
    expect(yForPosition(0, BOX)).toBe(240);
    expect(yForPosition(50, BOX)).toBe(140);
    expect(yForPosition(130, BOX)).toBe(40);
    expect(positionForY(140, BOX)).toBe(50);
    expect(positionForY(0, BOX)).toBe(100);
    expect(positionForY(400, BOX)).toBe(0);
  });

  it("snaps to the ends during a storm", () => {
    expect(snap(62.4, false)).toBe(62);
    expect(snap(62, true)).toBe(100);
    expect(snap(49, true)).toBe(0);
    expect(snap(-3, false)).toBe(0);
  });
});

describe("entities", () => {
  it("finds the devices and entities by translation key", () => {
    const hass = fakeHass();
    expect(deviceEntities(hass, LIVING).shutter).toBe("cover.living");
    expect(isShutter(hass, LIVING)).toBe(true);
    expect(isShutter(hass, BASE)).toBe(false);
    expect(integrationDevices(hass)).toEqual([BASE, KITCHEN, LIVING]);
    expect(shuttersOf(hass, BASE)).toEqual([KITCHEN, LIVING]);
    expect(baseOf(hass, LIVING)).toBe(BASE);
  });
});

describe("view model", () => {
  const time = (iso: string) => formatTime(iso, fakeHass(), "en");

  it("describes a shutter in the sun", () => {
    const m = shutterModel(fakeHass(), LIVING);
    expect(m).toMatchObject({ position: 62, max: 80, reason: "sun", target: 30, automatic: true, paused: false, storm: false });
    const s = nbsp(statusLines(m, localizer("en"), time));
    expect(s).toEqual({
      stand: "partly open",
      reason: "Sun on the window",
      detail: "→ 30 % · day",
      next: "Next: 16:55 dusk 35 %",
      then: "then 17:10 closed",
      chip: "automatic",
    });
  });

  it("shows the manual pause with its end, in Dutch", () => {
    const hass = fakeHass({
      "binary_sensor.living_manual_pause": { state: "on", attributes: { until: "2026-11-18T15:55:00+00:00" } },
      "sensor.living_reason": { state: "manual", attributes: { target_position: null, max_position: 100, language: "nl" } },
    });
    const m = shutterModel(hass, LIVING);
    const lang = cardLanguage(hass, undefined, m);
    expect(lang).toBe("nl");
    const s = nbsp(statusLines(m, localizer(lang), (iso) => formatTime(iso, hass, lang)));
    expect(s.reason).toBe("Handbediening");
    expect(s.detail).toBe("tot 16:55");
    expect(s.chip).toBe("manual_pause");
    expect(s.next).toBe("Volgende: 16:55 schemer 35 %");
    expect(statusLines({ ...m, pausedUntil: "next phase" }, localizer("en"), time).detail).toBe("until the next phase");
  });

  it("chooses the language: card, integration, profile", () => {
    const hass = fakeHass();
    const m = shutterModel(hass, LIVING);
    expect(cardLanguage(hass, "nl", { ...m, language: "en" })).toBe("nl");
    expect(cardLanguage(hass, undefined, { ...m, language: "nl" })).toBe("nl");
    expect(cardLanguage(hass, undefined, m)).toBe("en");
  });

  it("names positions", () => {
    const t = localizer("nl");
    expect([0, 35, 100, "slit" as const, null].map((p) => positionText(p, t))).toEqual(["dicht", "35\u00a0%", "open", "spleetstand", "–"]);
  });

  it("reads storm and frost from the base controller and the off switch", () => {
    const hass = fakeHass({ "binary_sensor.storm": { state: "on", attributes: {} }, "switch.living_automatic": { state: "off", attributes: {} } });
    const m = shutterModel(hass, LIVING);
    expect(m.storm).toBe(true);
    expect(statusLines(m, localizer("en"), time).chip).toBe("off");
  });

  it("formats decision reasons and results in English and Dutch", () => {
    const decisions = [
      { rule: "glare", priority: 41, result: "cap" as const, position: 40, applied: true, why: "bright", values: { factor: 90, limit: 55 } },
      { rule: "heat", priority: 40, result: "none" as const, why: "too_cold", values: { outdoor: 6, limit: 22 } },
      { rule: "manual", priority: 30, result: "none" as const, why: "waiting", values: { seconds: 180 } },
    ];
    expect(decisionLines(decisions, localizer("en"), "en")).toEqual([
      { rule: "Glare protection", text: "at most 40 % (sun factor 90 % ≥ 55 %)", applied: true },
      { rule: "Heat protection", text: "not warm (6 °C < 22 °C)", applied: false },
      { rule: "Manual control", text: "starts in 3 min", applied: false },
    ]);
    expect(decisionLines(decisions, localizer("nl"), "nl")).toEqual([
      { rule: "Verblinding", text: "hooguit 40 % (zonfactor 90 % ≥ 55 %)", applied: true },
      { rule: "Hittewering", text: "niet warm (6 °C < 22 °C)", applied: false },
      { rule: "Handbediening", text: "start over 3 min", applied: false },
    ]);
  });
});
