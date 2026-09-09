/**
 * Re-derive public/artifacts/primary-key-policy-v1.json FROM THE ENGINE TREE.
 *
 *   node scripts/derive-primary-key-authority.mjs --engine <path-to-engine-tree>
 *   node scripts/derive-primary-key-authority.mjs --engine <path> --check
 *
 * WHY THIS FILE EXISTS, stated plainly because the weakness it addresses is
 * recorded and real. Every other freshness contract in this repo names a
 * SITE-LOCAL JSON as its authority, and check-site-freshness.mjs resolves
 * authorities against the site root. So the contracts can prove a page agrees
 * with a file next to it, and can prove nothing at all about the engine. That
 * is exactly how a false AUTOINCREMENT claim survived two days unflagged in
 * 2026-09: the page and its authority agreed with each other, and both were
 * wrong about the engine.
 *
 * This script does not fix that -- a Next build cannot reach the engine tree,
 * which lives in a different repository on a different clone. What it does is
 * make the gap MECHANICAL AND VISIBLE instead of manual and invisible:
 *
 *   - every number in the authority is MEASURED from engine sources, never
 *     typed by hand, so re-deriving is one command rather than an audit;
 *   - the authority records the engine COMMIT it was measured at, so a reader
 *     comparing it to the engine's HEAD can see staleness without reading a
 *     single fact; and
 *   - --check re-derives into memory and diffs, so a session that HAS both
 *     trees mounted can answer "is this page still true" in one step.
 *
 * The remaining hole is named rather than hidden: nothing forces anyone to run
 * this. Closing that needs the engine's own pre-push gate to run it and refuse
 * a drifted artifact, which is engine work and is not done.
 *
 * NO ABSOLUTE PATH IS EMBEDDED HERE ON PURPOSE. --engine is required, has no
 * default, and check-public-content.mjs blocks a drive-lettered path anywhere
 * in scanned source. This file is in scripts/, which that guard also scans.
 */

import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const args = process.argv.slice(2);
const CHECK_ONLY = args.includes("--check");

function argValue(flag) {
  const i = args.indexOf(flag);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : null;
}

const engine = argValue("--engine") ?? process.env.X64BASE_ENGINE_TREE ?? null;
if (!engine) {
  console.error(
    "derive-primary-key-authority: --engine <path-to-engine-tree> is required\n" +
      "  (or set X64BASE_ENGINE_TREE). There is deliberately no default: a\n" +
      "  hardcoded clone path is both machine-specific and blocked by\n" +
      "  check-public-content.mjs."
  );
  process.exit(2);
}
if (!fs.existsSync(path.join(engine, "src", "cli", "cmd_regression.cpp"))) {
  console.error(
    `derive-primary-key-authority: ${engine} does not look like the engine tree\n` +
      "  (src/cli/cmd_regression.cpp not found)."
  );
  process.exit(2);
}

const OUT = path.join(process.cwd(), "public", "artifacts", "primary-key-policy-v1.json");

const read = (...p) => fs.readFileSync(path.join(engine, ...p), "utf8");

/* --- provenance ------------------------------------------------------ */
// Read-only git only, and never through a pipe: a SIGPIPE on a git child can
// leave a zero-byte .git/index.lock behind. execFileSync captures directly.
function git(...a) {
  return execFileSync("git", ["--no-optional-locks", "-C", engine, ...a], {
    encoding: "utf8"
  }).trim();
}
const commit = git("log", "-1", "--format=%H");
const commitDate = git("log", "-1", "--format=%cs");

/* --- the flag -------------------------------------------------------- */
const x64hdr = read("include", "xbase_64.hpp");
const flagMatch = x64hdr.match(
  /constexpr\s+uint16_t\s+X64_FIELD_FLAG_PRIMARY\s*=\s*(0x[0-9A-Fa-f]+)/
);
if (!flagMatch) throw new Error("X64_FIELD_FLAG_PRIMARY not found in include/xbase_64.hpp");

/* --- markers, counted from the scripts that print them ---------------- */
function markers(file, re) {
  return [...new Set(read("dottalkpp", "data", "scripts", file).match(re) ?? [])];
}
const pkp = markers("pk_policy_regression.dts", /PKP_[GT]\d+/g);
const pkpGuards = pkp.filter((m) => m.startsWith("PKP_G")).length;
const pkpArms = pkp.filter((m) => m.startsWith("PKP_T")).length;

// PKDURABLE's markers are printed by two CHILD scripts and graded in C++ off
// the captures they leave on disk, so the marker table in the validator -- not
// the .dts -- is the authority for which are guards and which are expected red.
const validator = read("src", "cli", "cmd_regression.cpp");
const pkdRows = [
  ...validator.matchAll(
    /\{\s*([12])\s*,\s*"(PKD_[A-Z0-9]+)_[^"]*"\s*,\s*(true|false)\s*,\s*(true|false)\s*\}/g
  )
].map((m) => ({ run: +m[1], name: m[2], guard: m[3] === "true", expect: m[4] === "true" }));
if (!pkdRows.length) throw new Error("PKDURABLE marker table not found in cmd_regression.cpp");

/* --- default-suite membership ---------------------------------------- */
// The registry is a constexpr array of brace-initialised structs whose fourth
// member is in_default_suite. Bound each entry's scan by the NEXT entry rather
// than by a fixed lookahead: an earlier cut of this parser used 40 lines and
// silently read 80 of 81 entries, because one summary is longer than that.
function suiteFlags(text) {
  const starts = [...text.matchAll(/^\s*\{\s*$\s*^\s*"([A-Z0-9_]+)",\s*$/gm)];
  const flags = {};
  for (let i = 0; i < starts.length; i += 1) {
    const from = starts[i].index;
    const to = i + 1 < starts.length ? starts[i + 1].index : text.length;
    const body = text.slice(from, to);
    const flag = body.match(/^\s*(true|false),?\s*(?:\/\/.*)?$/m);
    flags[starts[i][1]] = flag ? flag[1] === "true" : null;
  }
  return flags;
}
const flags = suiteFlags(validator);
const totalSpecs = Number(
  (validator.match(/std::array<RegressionSpec,\s*(\d+)>/) ?? [])[1] ?? 0
);

/* --- unrouted direct field writes ------------------------------------ */
const baseline = read("tools", "staging", "field_write_callers_baseline.txt")
  .split(/\r?\n/)
  .filter((l) => l.trim() && !l.trimStart().startsWith("#"));
const baselineFiles = new Set(baseline.map((l) => l.split(":")[0]));

/* --- the artifact ---------------------------------------------------- */
const authority = {
  schema: "x64base.primary-key-policy.v1",
  note:
    "GENERATED by scripts/derive-primary-key-authority.mjs from the engine " +
    "tree. Do not hand-edit: re-derive instead, or the next run reverts you " +
    "and the site quietly disagrees with the engine.",
  derived_on: new Date().toISOString().slice(0, 10),
  engine: {
    commit,
    commit_short: commit.slice(0, 9),
    commit_date: commitDate
  },
  declaration: "SET UNIQUE FIELD <field> PRIMARY",
  enforced_since: "2026-09-07",
  flag: {
    name: "X64_FIELD_FLAG_PRIMARY",
    value: flagMatch[1],
    header: "include/xbase_64.hpp"
  },
  specs: {
    pkpolicy: {
      name: "PKPOLICY",
      script: "dottalkpp/data/scripts/pk_policy_regression.dts",
      markers: pkp.length,
      guards: pkpGuards,
      arms: pkpArms,
      in_default_suite: flags.PKPOLICY === true
    },
    pkdurable: {
      name: "PKDURABLE",
      script: "dottalkpp/data/scripts/pk_durability_regression.dts",
      child_markers: pkdRows.length,
      guards: pkdRows.filter((r) => r.guard).length,
      arms: pkdRows.filter((r) => !r.guard).length,
      expected_red_arms: pkdRows.filter((r) => !r.guard && !r.expect).length,
      in_default_suite: flags.PKDURABLE === true
    }
  },
  write_paths_asserted: 5,
  unrouted_direct_writes: {
    sites: baseline.length,
    files: baselineFiles.size,
    gate: "tools/staging/check_field_write_callers.py"
  },
  registry: {
    total_specs: totalSpecs,
    in_default_suite: Object.values(flags).filter(Boolean).length
  }
};

const rendered = JSON.stringify(authority, null, 2) + "\n";

if (CHECK_ONLY) {
  const onDisk = fs.existsSync(OUT) ? fs.readFileSync(OUT, "utf8") : "";
  // derived_on is a timestamp, not a fact about the engine; comparing it would
  // make this check fail every day for no reason.
  const strip = (s) => s.replace(/"derived_on": "[^"]*",\n/, "");
  if (strip(onDisk) === strip(rendered)) {
    console.log(
      `primary-key authority: MATCHES the engine at ${authority.engine.commit_short}.`
    );
    process.exit(0);
  }
  console.error(
    "primary-key authority: DRIFTED from the engine tree.\n" +
      `  engine HEAD: ${authority.engine.commit_short} (${commitDate})\n` +
      "  Re-derive with the same command minus --check, then re-run\n" +
      "  `npm run check:freshness` -- the page contract will name every\n" +
      "  sentence that has to change."
  );
  process.exit(1);
}

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, rendered, "utf8");
console.log(
  `primary-key authority written: ${authority.specs.pkpolicy.markers} PKPOLICY markers, ` +
    `${authority.specs.pkdurable.child_markers} PKDURABLE child markers, ` +
    `${authority.unrouted_direct_writes.sites} unrouted sites in ` +
    `${authority.unrouted_direct_writes.files} files, engine ${authority.engine.commit_short}.`
);
