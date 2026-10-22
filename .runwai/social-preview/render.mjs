// Renders social-preview.html to a 1280x640 PNG for GitHub's social preview.
//
// Pinned on purpose: same input, same bytes out. Run it with `npm install &&
// node render.mjs` from this directory.
import { copyFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));

// The two brand faces, staged out of node_modules so the HTML can reference
// them relatively. Not committed: they are Google Fonts under the OFL, and
// fetching them from a pinned package beats vendoring binaries here.
const FACES = [
  ["@fontsource/barlow-condensed", "barlow-condensed-latin-900-normal.woff2"],
  ["@fontsource/inclusive-sans", "inclusive-sans-latin-400-normal.woff2"],
  ["@fontsource/inclusive-sans", "inclusive-sans-latin-600-normal.woff2"],
];

const fontsDir = path.join(here, "fonts");
mkdirSync(fontsDir, { recursive: true });
for (const [pkg, file] of FACES) {
  copyFileSync(path.join(here, "node_modules", pkg, "files", file), path.join(fontsDir, file));
}

const src = path.join(here, "social-preview.html");
const out = path.join(here, "runwai-social-preview.png");

// Chromium is the renderer because the card is CSS: the brand's offset text
// shadow and color-mix() opacities are not things an SVG rasteriser agrees on.
//
// Normally Playwright supplies its own browser (`npx playwright install
// chromium`). CHROMIUM_PATH is the escape hatch for sandboxes and CI images
// that already ship one and cannot download another.
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
});
const page = await browser.newPage({
  viewport: { width: 1280, height: 640 },
  deviceScaleFactor: 1,
});
await page.goto(pathToFileURL(src).href, { waitUntil: "load" });
// Without this the first paint can land before the woff2 faces are ready and
// the card renders in a fallback font.
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1280, height: 640 } });
await browser.close();

process.stdout.write(`wrote ${path.relative(process.cwd(), out)} (1280x640)\n`);
