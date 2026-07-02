import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const outDir = path.join(root, "out");
const stagingRoot = path.join(root, ".sites-artifact");
const distDir = path.join(stagingRoot, "dist");
const serverDir = path.join(distDir, "server");
const publicDir = path.join(serverDir, "public");
const openAiDir = path.join(distDir, ".openai");
const archivePath = path.join(root, "x64base-sites-artifact.tar.gz");

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

if (!fs.existsSync(outDir)) {
  throw new Error("Expected ./out to exist. Run npm run build first.");
}

fs.rmSync(stagingRoot, { recursive: true, force: true });
fs.rmSync(archivePath, { force: true });
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

execFileSync("tar", ["-C", stagingRoot, "-czf", archivePath, "dist"], {
  stdio: "inherit",
});

console.log(archivePath);
