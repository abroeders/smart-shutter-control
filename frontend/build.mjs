// Builds the card into the integration's frontend folder. `--check-size` fails above the size budget.
import { build } from "esbuild";
import { statSync } from "node:fs";

const OUT = "../custom_components/smart_shutter_control/frontend/smart-shutter-card.js";
const BUDGET = 80 * 1024;

await build({
  entryPoints: ["src/index.ts"],
  bundle: true,
  minify: true,
  format: "esm",
  target: "es2021",
  outfile: OUT,
  legalComments: "eof",
  logLevel: "info",
});

if (process.argv.includes("--check-size")) {
  const size = statSync(OUT).size;
  console.log(`bundle size: ${(size / 1024).toFixed(1)} kB (budget ${BUDGET / 1024} kB)`);
  if (size > BUDGET) process.exit(1);
}
