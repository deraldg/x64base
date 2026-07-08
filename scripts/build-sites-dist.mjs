import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

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
