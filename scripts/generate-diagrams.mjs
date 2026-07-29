import { readManifest, projectRoot, provenanceRecord, renderDiagram, writeProvenance } from "./diagram-lib.mjs";

const manifest = readManifest();
for (const diagram of manifest.diagrams) {
  const output = renderDiagram(projectRoot, manifest, diagram);
  writeProvenance(`${output}.provenance.json`, provenanceRecord(projectRoot, manifest, diagram, output));
  console.log(`generated ${diagram.id}`);
}
