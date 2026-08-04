import { readFileSync } from "node:fs";
import { join } from "node:path";
import { readManifest, projectRoot, provenanceRecord } from "./diagram-lib.mjs";

// Diagram integrity check.
//
// Mermaid renders through headless chromium, whose SVG bytes are NOT stable run
// to run (font metrics / layout floats) even with deterministicIds set. A byte-
// exact re-render comparison therefore can never pass reliably (two renders of
// the same source on the same machine differ). Instead we verify INTERNAL
// CONSISTENCY: the committed provenance sidecar must equal a freshly-computed
// record over the committed SVG + source (their sha256s plus declared renderer/
// metadata). That deterministically catches a committed SVG or source that has
// drifted from its recorded provenance, with no browser dependency. Regenerate
// with `npm run generate:diagrams` (which rewrites SVG + sidecar together) to
// clear a failure.

const manifest = readManifest();
const findings = [];

for (const diagram of manifest.diagrams) {
  const expected = join(projectRoot, diagram.output);

  const expectedProvenance = `${JSON.stringify(
    provenanceRecord(projectRoot, manifest, diagram, expected),
    null,
    2,
  )}\n`;

  // Normalize CRLF so a line-ending policy change cannot masquerade as drift.
  const committedProvenance = readFileSync(`${expected}.provenance.json`, "utf8").replace(
    /\r\n/g,
    "\n",
  );

  if (committedProvenance !== expectedProvenance) {
    findings.push(
      `${diagram.id}: provenance sidecar does not match committed SVG/source (regenerate with npm run generate:diagrams)`,
    );
  }
}

if (findings.length) {
  console.error("diagram check=FAIL");
  for (const finding of findings) console.error(`  - ${finding}`);
  process.exit(2);
}

console.log(`diagram check=PASS diagrams=${manifest.diagrams.length}`);
