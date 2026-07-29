import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join } from "node:path";
import { readManifest, projectRoot, provenanceRecord, renderDiagram } from "./diagram-lib.mjs";

const manifest = readManifest();
const temporary = mkdtempSync(join(tmpdir(), "x64base-diagrams-"));
const findings = [];

try {
  for (const diagram of manifest.diagrams) {
    const expected = join(projectRoot, diagram.output);
    const rendered = join(temporary, basename(diagram.output));
    renderDiagram(projectRoot, manifest, diagram, rendered);
    if (!readFileSync(expected).equals(readFileSync(rendered))) {
      findings.push(`${diagram.id}: generated SVG differs from committed output`);
    }

    const expectedProvenance = `${JSON.stringify(
      provenanceRecord(projectRoot, manifest, diagram, expected),
      null,
      2,
    )}\n`;
    const committedProvenance = readFileSync(`${expected}.provenance.json`, "utf8");
    if (committedProvenance !== expectedProvenance) {
      findings.push(`${diagram.id}: provenance sidecar is stale`);
    }
  }
} finally {
  rmSync(temporary, { recursive: true, force: true });
}

if (findings.length) {
  console.error("diagram check=FAIL");
  for (const finding of findings) console.error(`  - ${finding}`);
  process.exit(2);
}

console.log(`diagram check=PASS diagrams=${manifest.diagrams.length}`);
