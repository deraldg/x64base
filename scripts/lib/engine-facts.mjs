/**
 * Shared reading of the ENGINE tree for site authority generators.
 *
 * WHY THIS FILE EXISTS. The first generator
 * (derive-primary-key-authority.mjs) carried its own copies of engine-tree
 * resolution, read-only git provenance, and the regression-registry parser.
 * The second generator needed all three. Copying them would have created
 * exactly the failure this whole mechanism exists to prevent -- two lists of
 * the same fact drifting apart -- and it would have drifted in the WORST
 * direction, because the registry parser here has a bug already paid for once:
 * a fixed-window scan silently read 80 of 81 entries in
 * check_soak_evidence.py on 2026-09-08. A second hand-copy of that parser is a
 * second chance to reintroduce it.
 *
 * So the parsers live here once. If a fact is read from the engine by more
 * than one generator, it belongs in this file.
 */

import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

/**
 * Resolve and sanity-check the engine tree. NO DEFAULT ON PURPOSE: a
 * drive-lettered clone path is machine-specific AND blocked by
 * check-public-content.mjs, which scans scripts/.
 */
export function resolveEngine(args, toolName) {
  const i = args.indexOf("--engine");
  const engine =
    (i >= 0 && i + 1 < args.length ? args[i + 1] : null) ??
    process.env.X64BASE_ENGINE_TREE ??
    null;
  if (!engine) {
    console.error(
      `${toolName}: --engine <path-to-engine-tree> is required\n` +
        "  (or set X64BASE_ENGINE_TREE). There is deliberately no default: a\n" +
        "  hardcoded clone path is both machine-specific and blocked by\n" +
        "  check-public-content.mjs."
    );
    process.exit(2);
  }
  if (!fs.existsSync(path.join(engine, "src", "cli", "cmd_regression.cpp"))) {
    console.error(
      `${toolName}: ${engine} does not look like the engine tree\n` +
        "  (src/cli/cmd_regression.cpp not found)."
    );
    process.exit(2);
  }
  return engine;
}

export function reader(engine) {
  return (...p) => fs.readFileSync(path.join(engine, ...p), "utf8");
}

/**
 * Read-only git, and never through a pipe: a SIGPIPE on a git child can leave
 * a zero-byte .git/index.lock behind. execFileSync captures directly.
 */
export function provenance(engine) {
  const git = (...a) =>
    execFileSync("git", ["--no-optional-locks", "-C", engine, ...a], {
      encoding: "utf8"
    }).trim();
  const commit = git("log", "-1", "--format=%H");
  return {
    commit,
    commit_short: commit.slice(0, 9),
    commit_date: git("log", "-1", "--format=%cs")
  };
}

/**
 * The regression registry: spec name -> in_default_suite.
 *
 * Each entry's scan is bounded BY THE NEXT ENTRY rather than by a fixed
 * lookahead. See the file header: a 40-line window silently lost an entry
 * whose summary is longer than the window.
 */
export function suiteFlags(registrySource) {
  const starts = [
    ...registrySource.matchAll(/^\s*\{\s*$\s*^\s*"([A-Z0-9_]+)",\s*$/gm)
  ];
  const flags = {};
  for (let i = 0; i < starts.length; i += 1) {
    const from = starts[i].index;
    const to = i + 1 < starts.length ? starts[i + 1].index : registrySource.length;
    const body = registrySource.slice(from, to);
    const flag = body.match(/^\s*(true|false),?\s*(?:\/\/.*)?$/m);
    flags[starts[i][1]] = flag ? flag[1] === "true" : null;
  }
  return flags;
}

export function registryTotal(registrySource) {
  return Number(
    (registrySource.match(/std::array<RegressionSpec,\s*(\d+)>/) ?? [])[1] ?? 0
  );
}

/**
 * Compare a freshly derived artifact against what is on disk, ignoring
 * derived_on -- that is a timestamp, not a fact about the engine, and
 * comparing it would fail every day for no reason.
 */
export function checkAgainstDisk(outPath, rendered, engineProv, label) {
  const onDisk = fs.existsSync(outPath) ? fs.readFileSync(outPath, "utf8") : "";
  const strip = (s) => s.replace(/"derived_on": "[^"]*",\n/, "");
  if (strip(onDisk) === strip(rendered)) {
    console.log(`${label}: MATCHES the engine at ${engineProv.commit_short}.`);
    return 0;
  }
  console.error(
    `${label}: DRIFTED from the engine tree.\n` +
      `  engine HEAD: ${engineProv.commit_short} (${engineProv.commit_date})\n` +
      "  Re-derive with the same command minus --check, then re-run\n" +
      "  `npm run check:freshness` -- the page contract will name every\n" +
      "  sentence that has to change."
  );
  return 1;
}

export function writeArtifact(outPath, rendered) {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, rendered, "utf8");
}
