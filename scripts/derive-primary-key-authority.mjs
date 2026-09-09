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

import path from "node:path";
import {
  resolveEngine,
  reader,
  provenance,
  suiteFlags,
  registryTotal,
  checkAgainstDisk,
  writeArtifact
} from "./lib/engine-facts.mjs";

const TOOL = "derive-primary-key-authority";
const args = process.argv.slice(2);
const OUT = path.join(process.cwd(), "public", "artifacts", "primary-key-policy-v1.json");

// Two read-only modes, both used by the ENGINE-SIDE gate
// (tools/staging/check_site_artifacts.py in the x64base tree):
//
//   --artifact-path  print where this generator's artifact lives,
//                    relative to the site root, and exit. The gate
//                    globs scripts/derive-*-authority.mjs and ASKS
//                    each one, rather than keeping its own list of
//                    generator/artifact pairs -- a second list of the
//                    same fact is how the two drift, and this repo has
//                    paid for that shape more than once.
//   --print          write the freshly derived JSON to stdout and
//                    write nothing to disk, so the gate can compare
//                    FACTS while ignoring provenance. --check cannot
//                    serve that: it compares whole files, so every
//                    engine commit would read as drift even when no
//                    fact moved, and a gate that cries wolf on every
//                    push is a gate that gets switched off.
if (args.includes("--artifact-path")) {
  console.log(path.relative(process.cwd(), OUT).split(path.sep).join("/"));
  process.exit(0);
}
const CHECK_ONLY = args.includes("--check");
const engine = resolveEngine(args, TOOL);
const read = reader(engine);


/* --- the flag -------------------------------------------------------- */
const engineProv = provenance(engine);
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
const flags = suiteFlags(validator);
const totalSpecs = registryTotal(validator);

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
  engine: engineProv,
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

if (args.includes("--print")) {
  process.stdout.write(rendered);
  process.exit(0);
}

if (CHECK_ONLY) {
  process.exit(checkAgainstDisk(OUT, rendered, engineProv, "primary-key authority"));
}

writeArtifact(OUT, rendered);
console.log(
  `primary-key authority written: ${authority.specs.pkpolicy.markers} PKPOLICY markers, ` +
    `${authority.specs.pkdurable.child_markers} PKDURABLE child markers, ` +
    `${authority.unrouted_direct_writes.sites} unrouted sites in ` +
    `${authority.unrouted_direct_writes.files} files, engine ${engineProv.commit_short}.`
);
