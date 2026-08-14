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

// The stamp is an ornament, so readReleaseNumber() swallows its own errors and
// the component renders nothing when the fetch fails. Both are right in
// isolation and together they were a blind spot: a missing artifact in
// production looked EXACTLY like a working one with nothing to say -- no error,
// no gap in the footer, no console line. The only way to tell was to go look,
// and nobody goes and looks at an ornament.
//
// So the publish checks it, in two places. Before the push, deterministically,
// on the bytes about to ship. After the push, over the network, against what
// GitHub Pages actually serves. The first can block; the second cannot (the
// commit is already out) but it can be loud, and it retries because Pages
// propagation is not instant.
function assertReleaseArtifactShippable() {
  const file = path.join(outDir, "artifacts", "site-release.json");
  if (!fs.existsSync(file)) {
    throw new Error(`Release artifact missing from the build: ${file}`);
  }
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (err) {
    throw new Error(`Release artifact is not valid JSON: ${err.message}`);
  }
  if (!Number.isInteger(parsed.release_number) || parsed.release_number < 1) {
    // null means readReleaseNumber() hit its catch; 0 means the public/ dev seed
    // survived, i.e. writeReleaseMetadata never ran. Both ship a footer that
    // says "dev" or nothing on the live site.
    throw new Error(
      `Release artifact has no usable release_number (got ${JSON.stringify(parsed.release_number)}). ` +
      "null = the gh-pages log could not be counted; 0 = the dev seed was published instead of real metadata.",
    );
  }
  return parsed.release_number;
}

async function verifyLiveReleaseArtifact(expected) {
  const url = `https://${domain}/artifacts/site-release.json`;
  const delaysMs = [3000, 6000, 12000, 24000, 30000];
  for (let attempt = 0; attempt <= delaysMs.length; attempt += 1) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (res.ok) {
        const live = await res.json();
        if (live.release_number === expected) {
          console.log(`Verified live release artifact: ${url} -> release ${expected}`);
          return true;
        }
        console.log(
          `  live release_number is ${live.release_number}, expecting ${expected} (Pages may still be propagating)`,
        );
      } else {
        console.log(`  ${url} -> HTTP ${res.status}`);
      }
    } catch (err) {
      console.log(`  ${url} -> ${err.message}`);
    }
    if (attempt < delaysMs.length) {
      await new Promise((r) => setTimeout(r, delaysMs[attempt]));
    }
  }
  console.error("");
  console.error(`WARNING: could not confirm ${url} serves release ${expected}.`);
  console.error("The push already happened -- this does NOT mean the publish failed.");
  console.error("It means the footer's release stamp may be blank on the live site,");
  console.error("and a blank stamp looks identical to a working one. Check by hand:");
  console.error(`  curl -s ${url}`);
  return false;
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
const releaseNumber = assertReleaseArtifactShippable();

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

console.log("");
console.log(`Confirming the live release artifact (release ${releaseNumber})...`);
await verifyLiveReleaseArtifact(releaseNumber);
