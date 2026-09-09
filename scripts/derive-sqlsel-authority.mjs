/**
 * Re-derive public/artifacts/sqlsel-conformance-v1.json FROM THE ENGINE TREE.
 *
 *   node scripts/derive-sqlsel-authority.mjs --engine <path-to-engine-tree>
 *   node scripts/derive-sqlsel-authority.mjs --engine <path> --check
 *
 * Second application of the pattern in derive-primary-key-authority.mjs; see
 * scripts/lib/engine-facts.mjs for why the shared readers live in one place.
 *
 * WHAT IT FOUND ON ITS FIRST RUN, which is the argument for the pattern:
 * sqlsel-and-sql-conformance.mdx claimed "fourteen specifications" with "four
 * ... in the default suite" (measured: twelve SQLSEL_* specs, SIX in the
 * default suite) and "Four commands begin with SQL" (measured: SIX -- SQLHELP
 * and SQLERASE were missing from the page's own table). None of that was
 * catchable by any existing gate, because no gate could see the engine.
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

const TOOL = "derive-sqlsel-authority";
const args = process.argv.slice(2);
const OUT = path.join(process.cwd(), "public", "artifacts", "sqlsel-conformance-v1.json");

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

const registry = read("src", "cli", "cmd_regression.cpp");
const flags = suiteFlags(registry);

/* --- SQLsel specs ----------------------------------------------------- */
const sqlselSpecs = Object.keys(flags).filter((n) => n.startsWith("SQLSEL_")).sort();
const inSuite = sqlselSpecs.filter((n) => flags[n] === true);
const explicit = sqlselSpecs.filter((n) => flags[n] !== true);

/* --- which SPECS are graded against the SQLite oracle ------------------ *
 * The oracle is not a library the validator links: the .dts drives the SQLITE
 * bridge in the SAME RUN and writes labelled blocks, and
 * validate_sqlsel_oracle_rows() compares our block to SQLite's row for row.
 *
 * Count SPECS, not call sites. An earlier cut of this file counted call sites
 * of the helper and got 13, which is the right number by luck: it is a
 * different measurement that happens to coincide today, and it would stop
 * coinciding the moment one validator called the helper twice. So walk the
 * real chain instead -- spec -> RegressionValidator -> validator function ->
 * does that function body call the helper.                                  */
const enumToFn = Object.fromEntries(
  [...registry.matchAll(
    /case\s+RegressionValidator::(\w+):\s*\n\s*return\s+(validate_\w+)\(/g
  )].map((m) => [m[1], m[2]])
);
const fnDefs = [...registry.matchAll(/^bool\s+(validate_\w+)\s*\(/gm)];
const fnUsesOracle = {};
for (let i = 0; i < fnDefs.length; i += 1) {
  const from = fnDefs[i].index;
  const to = i + 1 < fnDefs.length ? fnDefs[i + 1].index : registry.length;
  fnUsesOracle[fnDefs[i][1]] = registry
    .slice(from, to)
    .includes("validate_sqlsel_oracle_rows(transcript,");
}
const specEntries = [...registry.matchAll(/^\s*\{\s*$\s*^\s*"([A-Z0-9_]+)",\s*$/gm)];
const specValidator = {};
for (let i = 0; i < specEntries.length; i += 1) {
  const from = specEntries[i].index;
  const to = i + 1 < specEntries.length ? specEntries[i + 1].index : registry.length;
  const v = registry.slice(from, to).match(/RegressionValidator::(\w+)/);
  if (v) specValidator[specEntries[i][1]] = v[1];
}
const oracleSpecs = Object.keys(specValidator)
  .filter((n) => fnUsesOracle[enumToFn[specValidator[n]]])
  .sort();
const oracleInSuite = oracleSpecs.filter((n) => flags[n] === true);

/* --- commands whose name begins with SQL ------------------------------- */
const commands = [
  ...new Set(
    [...read("src", "cli", "shell_commands.cpp").matchAll(/registry\(\)\.add\("(SQL[A-Z]*)"/g)].map(
      (m) => m[1]
    )
  )
].sort();

/* --- SET MODE routing -------------------------------------------------- *
 * MEASURE THE SPELLING THAT DOES THE WORK, NOT THE ONE THE PAGE HAPPENED TO
 * NAME. The page claimed routing was unwired on the evidence that
 * `sqlsel::session_mode()` is read only by the prompt -- which is TRUE and
 * proves nothing, because dispatch reads the wrapper `sqlsel::sql_mode()`
 * instead. Grepping for a symbol that does not exist returns empty, and an
 * empty result is not evidence of absence. So count the wrapper's call sites
 * in the files that actually dispatch, and read the alias list out of the
 * router rather than describing it.                                        */
const ROUTER_FILES = [
  "src/cli/shell_api.cpp",
  "src/cli/sqlsel_statement.cpp",
  "src/cli/set_relations.cpp"
];
const sqlModeCallSites = ROUTER_FILES.map((f) => ({
  file: f,
  sites: (read(...f.split("/")).match(/sqlsel::sql_mode\s*\(|(?<!::)\bsql_mode\s*\(\)/g) ?? []).length
})).filter((x) => x.sites > 0);

const router = read("src", "cli", "shell_api.cpp");
const aliasBlock = router.match(
  /if\s*\(sqlsel::sql_mode\(\)\)[\s\S]*?routed_command\s*=\s*"SQLSEL";/
);
const aliasedVerbs = aliasBlock
  ? [...new Set([...aliasBlock[0].matchAll(/U\s*==\s*"([A-Z]+)"/g)].map((m) => m[1]))]
      .filter((v) => !["REL", "RELATIONS", "REL_LIST", "REL_REFRESH", "SET"].includes(v))
      .sort()
  : [];

/* --- the conformance map ----------------------------------------------- *
 * Brace-matched rather than regexed: the entries contain braces and commas
 * inside string literals and inside long comments, and a naive split gets a
 * different answer than the compiler does.                                 */
function catalogEntries(src) {
  const anchor = src.indexOf("static const std::vector<Item> items = {");
  let i = src.indexOf("{", anchor + "static const std::vector<Item> items =".length);
  let depth = 0;
  let cur = null;
  const out = [];
  while (i < src.length) {
    const c = src[i];
    if (c === '"') {
      let j = i + 1;
      while (j < src.length) {
        if (src[j] === "\\") { j += 2; continue; }
        if (src[j] === '"') break;
        j += 1;
      }
      i = j + 1;
      continue;
    }
    if (c === "/" && src[i + 1] === "/") {
      const nl = src.indexOf("\n", i);
      i = nl < 0 ? src.length : nl;
      continue;
    }
    if (c === "{") {
      depth += 1;
      if (depth === 2) cur = i;
    } else if (c === "}") {
      if (depth === 2 && cur !== null) { out.push(src.slice(cur, i + 1)); cur = null; }
      depth -= 1;
      if (depth === 0) break;
    }
    i += 1;
  }
  return out;
}

function topLevelFields(entry) {
  const s = entry.slice(1, -1);
  const parts = [];
  let i = 0, start = 0, depth = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === '"') {
      let j = i + 1;
      while (j < s.length) {
        if (s[j] === "\\") { j += 2; continue; }
        if (s[j] === '"') break;
        j += 1;
      }
      i = j + 1;
      continue;
    }
    if (c === "/" && s[i + 1] === "/") {
      const nl = s.indexOf("\n", i);
      i = nl < 0 ? s.length : nl;
      continue;
    }
    if ("({[".includes(c)) depth += 1;
    else if (")}]".includes(c)) depth -= 1;
    else if (c === "," && depth === 0) { parts.push(s.slice(start, i)); start = i + 1; }
    i += 1;
  }
  parts.push(s.slice(start));
  return parts;
}

const litText = (s) =>
  [...s.matchAll(/"((?:[^"\\]|\\.)*)"/g)].map((m) => m[1]).join("");

const entries = catalogEntries(read("include", "sql_ref.hpp"));
let mapped = 0;
for (const e of entries) {
  const f = topLevelFields(e);
  if (f.length >= 6 && litText(f.slice(5).join(",")).trim()) mapped += 1;
}

/* --- the artifact ------------------------------------------------------ */
const engineProv = provenance(engine);
const authority = {
  schema: "x64base.sqlsel-conformance.v1",
  note:
    "GENERATED by scripts/derive-sqlsel-authority.mjs from the engine tree. " +
    "Do not hand-edit: re-derive instead, or the next run reverts you and the " +
    "site quietly disagrees with the engine.",
  derived_on: new Date().toISOString().slice(0, 10),
  engine: engineProv,
  verb: "SQLSEL",
  supported_since: "2026-07-29",
  specs: {
    sqlsel_total: sqlselSpecs.length,
    in_default_suite: inSuite.length,
    explicit_run: explicit.length,
    oracle_graded: oracleSpecs.length,
    oracle_in_default_suite: oracleInSuite.length,
    oracle_explicit_run: oracleSpecs.length - oracleInSuite.length,
    oracle_graded_names: oracleSpecs,
    default_suite_names: inSuite,
    explicit_run_names: explicit
  },
  sql_prefixed_commands: {
    count: commands.length,
    names: commands,
    source: "src/cli/shell_commands.cpp"
  },
  sql_mode: {
    switch_command: "SET MODE [TO] NATIVE|SQL|OTHER",
    routing_predicate: "sqlsel::sql_mode()",
    dispatch_call_sites: sqlModeCallSites.reduce((a, b) => a + b.sites, 0),
    dispatch_files: sqlModeCallSites,
    aliased_to_sqlsel: aliasedVerbs,
    aliased_count: aliasedVerbs.length,
    proven_by: "SQLMODE_SMOKE",
    proven_by_in_default_suite: flags.SQLMODE_SMOKE === true
  },
  conformance_map: {
    header: "include/sql_ref.hpp",
    entries: entries.length,
    with_x64_mapping: mapped,
    not_yet_mapped: entries.length - mapped
  },
  registry: {
    total_specs: registryTotal(registry),
    in_default_suite: Object.values(flags).filter(Boolean).length
  }
};

const rendered = JSON.stringify(authority, null, 2) + "\n";

if (args.includes("--print")) {
  process.stdout.write(rendered);
  process.exit(0);
}

if (CHECK_ONLY) {
  process.exit(checkAgainstDisk(OUT, rendered, engineProv, "sqlsel authority"));
}

writeArtifact(OUT, rendered);
console.log(
  `sqlsel authority written: ${authority.specs.sqlsel_total} SQLSEL specs ` +
    `(${authority.specs.in_default_suite} default / ${authority.specs.explicit_run} explicit), ` +
    `${authority.specs.oracle_graded} oracle-graded, ` +
    `${authority.sql_prefixed_commands.count} SQL-prefixed commands, ` +
    `${authority.sql_mode.aliased_count} verbs aliased in SQL mode, ` +
    `conformance map ${authority.conformance_map.with_x64_mapping}/${authority.conformance_map.entries} mapped, ` +
    `engine ${engineProv.commit_short}.`
);
