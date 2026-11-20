// Parses every ```mermaid block in the given Markdown files. Usage: node scripts/check_mermaid.mjs docs/*.md
// Needs: npm install --no-save mermaid@11 jsdom@24
import { JSDOM } from "jsdom";
import fs from "node:fs";

const dom = new JSDOM("<!doctype html><html><body></body></html>");
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { default: mermaid } = await import("mermaid");
mermaid.initialize({ startOnLoad: false });

let bad = 0;
for (const file of process.argv.slice(2)) {
  const blocks = [...fs.readFileSync(file, "utf8").matchAll(/```mermaid\n([\s\S]*?)```/g)].map((m) => m[1]);
  for (const [i, block] of blocks.entries()) {
    try {
      await mermaid.parse(block);
    } catch (e) {
      bad++;
      console.log(`${file} block ${i + 1}: ${String(e.message || e).split("\n").slice(0, 3).join(" | ")}`);
    }
  }
  console.log(`${file}: ${blocks.length} diagram(s)`);
}
process.exit(bad ? 1 : 0);
