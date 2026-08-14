import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const outDir = path.join(root, "out");
const deployDir = path.join(root, ".gh-pages-deploy");
const domain = "x64base.com";
const repo = "deraldg/x64base";
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const packageJsonPath = path.join(root, "package.json");

function run(command, args, options = {}) {
  console.log(`$ ${[command, ...args].join(" ")}`);
  return execFileSync(command, args, {
    stdio: "inherit",
    cwd: options.cwd ?? root,
    env: { ...process.env, ...(options.env ?? {}) },
    shell: process.platform === "win32" && command.endsWith(".cmd"),
  });
}

function output(command, args, options = {}) {
  return execFileSync(command, args, {
    cwd: options.cwd ?? root,
    shell: process.platform === "win32" && command.endsWith(".cmd"),
    encoding: "utf8",
  }).trim();
}

function readPackageVersion() {
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
  return packageJson.version ?? "0.0.0";
}

function assertInside(child, parent) {
  const rel = path.relative(parent, child);
  if (rel.startsWith("..") || path.isAbsolute(rel)) {
    throw new Error(`Unsafe path: ${child} is not inside ${parent}`);
  }
}

function ensureDeployRepo() {
  if (!fs.existsSync(path.join(root, "package.json"))) {
    throw new Error(`Run this from the site root: ${root}`);
  }
  if (!fs.existsSync(path.join(deployDir, ".git"))) {
    throw new Error(`Missing GitHub Pages worktree: ${deployDir}`);
  }
  const branch = output("git", ["branch", "--show-current"], { cwd: deployDir });
  if (branch !== "gh-pages") {
    throw new Error(`Expected ${deployDir} to be on gh-pages, found ${branch}`);
  }
  const remote = output("git", ["remote", "get-url", "origin"], { cwd: deployDir });
  if (!remote.includes("github.com/deraldg/x64base")) {
    throw new Error(`Unexpected gh-pages origin: ${remote}`);
  }
}

function removeDeployContents() {
  const resolvedDeploy = fs.realpathSync(deployDir);
  for (const entry of fs.readdirSync(deployDir, { withFileTypes: true })) {
    if (entry.name === ".git") continue;
    const target = path.join(deployDir, entry.name);
    assertInside(fs.realpathSync.native(target), resolvedDeploy);
    fs.rmSync(target, { recursive: true, force: true });
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

function ensureMarkers() {
  fs.writeFileSync(path.join(deployDir, "CNAME"), `${domain}\n`, "utf8");
  fs.writeFileSync(path.join(deployDir, ".nojekyll"), "\n", "utf8");
}

// How many times this site has been published, counted from the deploy branch's
// own history rather than stored in a file that could drift. Owner direction
// 2026-08-13, choosing this over a visitor counter: it is a number the site can
// honestly know about itself, it needs no third party, and it keeps the site
// free of tracking. Every publish commit is titled "Publish x64base site <stamp>",
// so counting them IS the release number; this run is the next one.
function readReleaseNumber() {
  try {
    const log = output("git", ["log", "--oneline", "--grep", "^Publish x64base site"],
                       { cwd: deployDir });
    const prior = log ? log.split("\n").filter(Boolean).length : 0;
    return prior + 1;
  } catch {
    return null; // never block a publish over an ornament
  }
}

function writeReleaseMetadata({ sourceCommit, sourceBranch, packageVersion }) {
  const artifactDir = path.join(outDir, "artifacts");
  fs.mkdirSync(artifactDir, { recursive: true });
  fs.writeFileSync(
    path.join(artifactDir, "site-release.json"),
    `${JSON.stringify(
      {
        site: "x64base.com",
        package_version: packageVersion,
        release_number: readReleaseNumber(),
        source_branch: sourceBranch,
        source_commit: sourceCommit,
        published_at_utc: new Date().toISOString(),
        publish_mode: "github-pages",
        source_root: "website source tree",
        deploy_branch: "gh-pages",
        deploy_repo: repo,
      },
      null,
      2,
    )}\n`,
    "utf8",
  );
}

function assertLocalOnlyReportsAbsent() {
  const reportsDir = path.join(outDir, "reports");
  if (fs.existsSync(reportsDir)) {
    throw new Error(
      `Refusing to publish local-only reports found at ${reportsDir}`,
    );
  }
}

function commitAndPush() {
  run("git", ["add", "-A"], { cwd: deployDir });
  const status = output("git", ["status", "--short"], { cwd: deployDir });
  if (!status) {
    console.log("No deploy changes to commit.");
    return output("git", ["rev-parse", "HEAD"], { cwd: deployDir });
  }

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  run("git", ["commit", "-m", `Publish x64base site ${stamp}`], { cwd: deployDir });
  run("git", ["push", "origin", "gh-pages"], { cwd: deployDir });
  return output("git", ["rev-parse", "HEAD"], { cwd: deployDir });
}

ensureDeployRepo();

const sourceStatus = output("git", ["status", "--short"]);
if (sourceStatus) {
  throw new Error(
    "Refusing to publish from a dirty source worktree. Commit or stash source changes in the website source tree first.",
  );
}

const sourceCommit = output("git", ["rev-parse", "HEAD"]);
const sourceBranch = output("git", ["branch", "--show-current"]);
const packageVersion = readPackageVersion();

run("git", ["fetch", "origin", "gh-pages"], { cwd: deployDir });
run("git", ["pull", "--rebase", "origin", "gh-pages"], { cwd: deployDir });
run(npmCommand, ["run", "build"], {
  env: { NEXT_PUBLIC_SITE_VERSION: sourceCommit.slice(0, 12) },
});

if (!fs.existsSync(outDir)) {
  throw new Error("Expected ./out after build.");
}
assertLocalOnlyReportsAbsent();

writeReleaseMetadata({ sourceCommit, sourceBranch, packageVersion });

removeDeployContents();
copyDir(outDir, deployDir);
ensureMarkers();

const commit = commitAndPush();

console.log(`Published ${commit} to ${repo}:gh-pages`);
console.log(`Live URL: https://${domain}/`);
console.log(`Source commit: ${sourceCommit}`);
console.log(`Source branch: ${sourceBranch}`);
console.log("Release metadata: /artifacts/site-release.json");
console.log("Verify Pages settings with: gh api repos/deraldg/x64base/pages");
