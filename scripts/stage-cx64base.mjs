import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const outDir = path.join(root, "out");
const mirrorDir = process.env.X64BASE_SITE_MIRROR
  ? path.resolve(process.env.X64BASE_SITE_MIRROR)
  : "C:\\x64base\\dottalk-webui\\public-site";
const mirrorRoot = "C:\\x64base\\dottalk-webui";

function assertInside(child, parent) {
  const rel = path.relative(parent, child);
  if (rel.startsWith("..") || path.isAbsolute(rel)) {
    throw new Error(`Unsafe path: ${child} is not inside ${parent}`);
  }
}

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

function refreshMirror() {
  if (!fs.existsSync(path.join(root, "package.json"))) {
    throw new Error(`Run this from the site root: ${root}`);
  }
  if (!fs.existsSync(path.join(outDir, "index.html"))) {
    throw new Error("Expected ./out/index.html. Run npm run build first.");
  }

  const resolvedRoot = fs.existsSync(mirrorRoot)
    ? fs.realpathSync.native(mirrorRoot)
    : mirrorRoot;
  const resolvedMirror = fs.existsSync(mirrorDir)
    ? fs.realpathSync.native(mirrorDir)
    : mirrorDir;

  assertInside(resolvedMirror, resolvedRoot);

  fs.mkdirSync(mirrorRoot, { recursive: true });
  fs.rmSync(mirrorDir, { recursive: true, force: true });
  fs.mkdirSync(mirrorDir, { recursive: true });
  copyDir(outDir, mirrorDir);

  fs.writeFileSync(
    path.join(mirrorDir, "MIRROR_SOURCE.txt"),
    [
      "x64base.com local mirror",
      `source: ${root}`,
      `build: ${outDir}`,
      `target: ${mirrorDir}`,
      `staged_at_utc: ${new Date().toISOString()}`,
      "",
    ].join("\n"),
    "utf8",
  );
}

refreshMirror();
console.log(`Staged static site mirror to ${mirrorDir}`);
