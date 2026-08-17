import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

/**
 * check-opacity-scale -- catch Tailwind opacity modifiers that generate nothing.
 *
 * WHY THIS EXISTS
 *   On 2026-08-16 the live site's hero caption was measured at 1.24:1 against a
 *   dark photograph, where 4.5:1 is the bar. The cause was not a colour. The
 *   caption sits in a bar classed `bg-bg/78`, and Tailwind's opacity scale runs
 *   ... 50, 60, 70, 75, 80 ... with no 78. The utility was never generated, so
 *   the bar's computed background was rgba(0, 0, 0, 0) -- not a wrong
 *   background, NO background. The caption was text painted onto a photo.
 *
 *   A sweep found six more doing the same thing silently. Every one had passed
 *   review, because `bg-card/45` reads as a perfectly reasonable instruction.
 *
 *   An off-scale value does not warn, does not error, and does not fall back.
 *   It produces nothing, and nothing looks like a design choice. That is the
 *   whole reason a mechanical check is worth more than another careful reader.
 *
 * WHAT IT DOES NOT DO
 *   It does not judge design. Any value ON the scale passes, however odd.
 *   It only catches values that cannot generate CSS at all.
 *
 * Exit codes:
 *   0  every opacity modifier is on the scale
 *   1  at least one would silently generate nothing
 */

// Tailwind's default opacity scale. Arbitrary values are still possible with
// bracket syntax (bg-bg/[78%]); that form is deliberately allowed through
// because it is explicit about being unusual.
const SCALE = new Set([0, 5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 100]);

const UTIL = /\b((?:bg|text|border|ring|divide|outline|from|via|to|fill|stroke|shadow|placeholder|accent|caret|decoration)-[a-z][a-z0-9-]*)\/(\d+)\b/g;

const SCAN_DIRS = ["app", "components", "content", "config"];
const EXTS = new Set([".tsx", ".ts", ".jsx", ".js", ".mdx", ".md", ".css"]);
const SKIP = new Set(["node_modules", ".next", "out", "dist", ".git"]);

function* walk(dir) {
  if (!fs.existsSync(dir)) return;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP.has(e.name)) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else if (EXTS.has(path.extname(e.name))) yield p;
  }
}

export function checkOpacityScale({ root = process.cwd() } = {}) {
  const findings = [];
  for (const dir of SCAN_DIRS) {
    for (const file of walk(path.join(root, dir))) {
      const text = fs.readFileSync(file, "utf8");
      const lines = text.split("\n");
      lines.forEach((line, i) => {
        // Bracket syntax is explicit and allowed: bg-bg/[78%]
        const stripped = line.replace(/\/\[[^\]]*\]/g, "/[ok]");
        for (const m of stripped.matchAll(UTIL)) {
          const value = Number(m[2]);
          if (!SCALE.has(value)) {
            findings.push({
              file: path.relative(root, file),
              line: i + 1,
              util: m[0],
              nearest: [...SCALE].reduce((a, b) =>
                Math.abs(b - value) < Math.abs(a - value) ? b : a
              ),
            });
          }
        }
      });
    }
  }
  return findings;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const findings = checkOpacityScale({ root: process.cwd() });
  if (findings.length) {
    console.error("opacity-scale: FAIL -- these generate NO css at all:\n");
    for (const f of findings) {
      console.error(
        `  ${f.file}:${f.line}  ${f.util}  -> nearest valid is /${f.nearest}`
      );
    }
    console.error(
      "\nTailwind's opacity scale is 0 5 10 20 25 30 40 50 60 70 75 80 90 95 100."
    );
    console.error(
      "An off-scale value produces no background/colour rather than an error,"
    );
    console.error(
      "which is how a hero caption shipped at 1.24:1 contrast. Use a scale value,"
    );
    console.error("or bracket syntax if you really mean it: bg-bg/[78%].");
    process.exit(1);
  }
  console.log("opacity-scale: PASS -- every opacity modifier is on the scale.");
}
