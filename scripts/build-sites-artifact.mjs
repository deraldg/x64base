import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { buildSitesDist } from "./build-sites-dist.mjs";

const root = process.cwd();
const stagingRoot = path.join(root, ".sites-artifact");
const distDir = path.join(stagingRoot, "dist");
const archivePath = path.join(root, "x64base-sites-artifact.tar.gz");

fs.rmSync(stagingRoot, { recursive: true, force: true });
fs.rmSync(archivePath, { force: true });
buildSitesDist({ root, distDir });

execFileSync("tar", ["-C", stagingRoot, "-czf", archivePath, "dist"], {
  stdio: "inherit",
});

console.log(archivePath);
