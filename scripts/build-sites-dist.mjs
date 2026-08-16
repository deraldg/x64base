import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { LOCAL_ONLY_DIRS } from "./strip-local-only-output.mjs";

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

export function buildSitesDist({
  root = process.cwd(),
  distDir = path.join(root, "dist"),
} = {}) {
  const outDir = path.join(root, "out");
  const serverDir = path.join(distDir, "server");
  const publicDir = path.join(serverDir, "public");
  const openAiDir = path.join(distDir, ".openai");

  if (!fs.existsSync(outDir)) {
    throw new Error("Expected ./out to exist. Run next build first.");
  }
  // Reads LOCAL_ONLY_DIRS rather than naming "reports" itself. This check was
  // a second hand-kept list, and it had already drifted: "retro" joined the
  // local-only set on 2026-08-15 and this guard never learned about it, so a
  // dist artifact would have carried it while the other two layers believed it
  // was covered. A guard that names its own subset silently narrows over time.
  for (const name of LOCAL_ONLY_DIRS) {
    if (fs.existsSync(path.join(outDir, name))) {
      throw new Error(
        `Refusing to package local-only content: out/${name}. ` +
        "Run strip-local-only-output first (the publish does this for you).",
      );
    }
  }

  fs.rmSync(distDir, { recursive: true, force: true });
  fs.mkdirSync(serverDir, { recursive: true });
  copyDir(outDir, publicDir);

  fs.writeFileSync(
    path.join(serverDir, "index.js"),
    `export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  }
};
`,
  );

  fs.mkdirSync(openAiDir, { recursive: true });
  fs.copyFileSync(
    path.join(root, ".openai", "hosting.json"),
    path.join(openAiDir, "hosting.json"),
  );

  return distDir;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(buildSitesDist());
}
