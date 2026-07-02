/**
 * scripts/build-apache-static.mjs
 *
 * Builds the static export (`out/`) and drops a ready-to-use `.htaccess` into it.
 *
 * Usage:
 *   node scripts/build-apache-static.mjs
 */
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function run(cmd) {
  execSync(cmd, { stdio: "inherit" });
}

run("npm run build");

const outDir = path.join(process.cwd(), "out");
const htaccessSrc = path.join(process.cwd(), "apache", ".htaccess");
const htaccessDst = path.join(outDir, ".htaccess");

if (!fs.existsSync(outDir)) {
  throw new Error("Expected ./out to exist after build. Did the build fail?");
}

fs.copyFileSync(htaccessSrc, htaccessDst);
console.log("✅ Static site ready in ./out (with .htaccess)");
