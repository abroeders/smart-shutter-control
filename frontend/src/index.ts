// Entry point: defines the elements and registers the card in the card picker.

import { CARD_TAG, EDITOR_TAG, SmartShutterCard } from "./card";
import { DRAWING_TAG, ShutterDrawing } from "./drawing";
import { SmartShutterCardEditor } from "./editor";

function define(tag: string, element: CustomElementConstructor) {
  if (!customElements.get(tag)) customElements.define(tag, element);
}

define(DRAWING_TAG, ShutterDrawing);
define(EDITOR_TAG, SmartShutterCardEditor);
define(CARD_TAG, SmartShutterCard);

const w = window as unknown as { customCards?: unknown[] };
w.customCards = w.customCards ?? [];
if (!w.customCards.some((c: any) => c.type === CARD_TAG)) {
  w.customCards.push({
    type: CARD_TAG,
    name: "Smart Shutter",
    description: "A shutter you can drag to a position, with buttons and its status; or all shutters of a base controller.",
    preview: true,
    documentationURL: "https://github.com/abroeders/smart-shutter-control/blob/main/docs/card.md",
  });
}
