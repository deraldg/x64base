import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

function assertInside(child, parent) {
  const relative = path.relative(parent, child);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`Unsafe local-only output path: ${child}`);
  }
}

export function stripLocalOnlyOutput({ root = process.cwd() } = {}) {
  const outDir = path.resolve(root, "out");
  const outputRoots = [
    outDir,
    path.resolve(root, "dist", "server", "public"),
    path.resolve(root, ".sites-artifact", "dist", "server", "public"),
  ];
  const removedPaths = [];

  for (const outputRoot of outputRoots) {
    const reportsDir = path.resolve(outputRoot, "reports");
    assertInside(reportsDir, outputRoot);
    if (!fs.existsSync(reportsDir)) continue;
    fs.rmSync(reportsDir, { recursive: true, force: true });
    removedPaths.push(reportsDir);
  }

  const staleArtifact = path.resolve(root, "x64base-sites-artifact.tar.gz");
  assertInside(staleArtifact, path.resolve(root));
  if (fs.existsSync(staleArtifact)) {
    fs.rmSync(staleArtifact, { force: true });
    removedPaths.push(staleArtifact);
  }

  return { removedPaths };
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  const result = stripLocalOnlyOutput();
  if (result.removedPaths.length === 0) {
    console.log("No local-only report output found.");
  } else {
    for (const removedPath of result.removedPaths) {
      console.log(`Removed local-only or stale output: ${removedPath}`);
    }
  }
}
