import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

export const projectRoot = resolve(import.meta.dirname, "..");

export function readManifest(root = projectRoot) {
  return JSON.parse(readFileSync(join(root, "diagrams", "manifest.json"), "utf8"));
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function rendererPath(root) {
  return join(root, "node_modules", "@mermaid-js", "mermaid-cli", "src", "cli.js");
}

export function renderDiagram(root, manifest, diagram, outputOverride = null) {
  const source = join(root, diagram.source);
  const output = outputOverride ?? join(root, diagram.output);
  const config = join(root, manifest.renderer.config);
  mkdirSync(dirname(output), { recursive: true });
  execFileSync(
    process.execPath,
    [
      rendererPath(root),
      "--input",
      source,
      "--output",
      output,
      "--configFile",
      config,
      "--backgroundColor",
      "transparent",
    ],
    { cwd: root, stdio: "inherit" },
  );
  return output;
}

export function provenanceRecord(root, manifest, diagram, output) {
  const sourceBytes = readFileSync(join(root, diagram.source));
  const outputBytes = readFileSync(output);
  return {
    schema_version: 1,
    diagram_id: diagram.id,
    path: diagram.output.replaceAll("\\", "/"),
    derived_from: [diagram.source.replaceAll("\\", "/")],
    upstream_authority: diagram.upstream_authority,
    generator: `${manifest.renderer.package}@${manifest.renderer.version}`,
    generator_config: manifest.renderer.config,
    source_sha256: sha256(sourceBytes),
    output_sha256: sha256(outputBytes),
    truth_status: diagram.truth_status,
    review_status: diagram.review_status,
  };
}

export function writeProvenance(path, record) {
  writeFileSync(path, `${JSON.stringify(record, null, 2)}\n`, "utf8");
}
