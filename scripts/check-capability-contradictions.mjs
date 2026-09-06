// Tier 2 of the freshness discipline: does any page CONTRADICT the engine?
//
// The existing contracts in site-freshness-contracts.json compare exact values
// -- a page says 245 keys, the authority says 245 keys. That is precise and it
// is blind to the failure that actually shipped: on 2026-09-05 five pages said
// x64base had no JOIN and no NULL, phrased five different ways, and every
// number on every page was correct. Nothing disagreed with a figure. The pages
// disagreed with the ENGINE.
//
// So this sweep reads a GENERATED authority -- engine-capabilities-v1.json,
// emitted by ccode's tools/reports/engine_capabilities.py from kRegressionSpecs
// -- and looks for a negation sitting next to a capability the engine ships.
//
// IT IS ADVISORY BY DESIGN AND LOUD BY DESIGN. It never blocks a publish: this
// is a prose heuristic and a false positive must not stop a release. But an
// advisory nobody reads decays, and coordination/OPEN_ITEMS.md measures that
// decay at 33% compliance for ungated obligations against 83-94% for gated
// ones -- so it always prints a count, and the count rides out in the publish
// output where staleness is about to become public.
//
// TWO SEVERITIES, because the registry makes the distinction and pretending it
// does not would be its own dishonesty:
//   flag   -- default-suite. Re-proven on every REGRESSION ALL. A page denying
//             this is simply wrong.
//   review -- explicit-run. Proven, but pending mutation proof, review and
//             soak. A page denying this MIGHT be describing the soak honestly.
//
// Legitimate negatives are real and common ("SQLsel DML refuses to store a
// NULL" is TRUE and must stay sayable), so they are exempted BY NAME in
// capability-contradiction-exemptions.json, each with a reason. An exemption
// without a reason is rejected: muting a check silently is how a check dies.

import fs from "node:fs";
import path from "node:path";

const AUTHORITY = "scripts/engine-capabilities-v1.json";
const EXEMPTIONS = "scripts/capability-contradiction-exemptions.json";
const CONTENT = "content";

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (entry.name.endsWith(".mdx")) out.push(full);
  }
  return out;
}

// A table CELL is a unit and so is a sentence: the 2026-09-05 misses were
// mostly cells, where a sentence split on ". " would have swallowed the whole
// row and drowned the signal in eight competitor columns.
function units(text) {
  const out = [];
  for (const rawLine of text.split(/\r?\n/)) {
    for (const cell of rawLine.split("|")) {
      for (const piece of cell.split(/(?<=[.;:])\s+/)) {
        const trimmed = piece.trim();
        if (trimmed) out.push(trimmed);
      }
    }
  }
  return out;
}

const wordRe = (w) =>
  new RegExp(`(?<![a-z0-9_])${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?![a-z0-9_])`, "i");

// SQL SYNTAX IS NOT A DENIAL. "NOT EXISTS", "NOT IN", "NOT NULL" and "[NOT]"
// are the language, not a claim that something is missing, and left unmasked
// they made `subqueries` and `stored null` fire on the pages that document
// them CORRECTLY. Masked before any negation is looked for.
const SQL_SYNTAX = /\b(?:\[not\]|not\s+(?:exists|in|null)|is\s+null|not\s+between|not\s+like)\b/gi;

// A denial has to GOVERN the capability, not merely share a sentence with it.
// Two windows, both tight: words that deny in front of the thing they deny,
// and words that deny after it.
const BEFORE_WINDOW = 46;
const AFTER_WINDOW = 44;

const DENY_BEFORE = [
  "no", "without", "lacks", "lacking", "unsupported", "unimplemented",
  "missing", "absent", "neither"
];
// MATURITY LANGUAGE IS NOT A DENIAL, by owner ruling 2026-09-06: "the website
// is alpha about beta/alpha components of our system, it is ok to say planned,
// or almost done, or in dev." So "planned", "chartered", "in dev", "almost
// done", "roadmap" and "future" are deliberately ABSENT from both lists. This
// sweep polices ONE thing -- a page asserting that something DOES NOT EXIST
// when the engine re-proves it every run. Saying a shipped thing is immature,
// unsoaked, or still moving is honest and must stay sayable.
//
// The severity split carries the rest of the nuance: an explicit-run capability
// is proven but unsoaked, so a page hedging it gets "review", not "flag".
const DENY_AFTER = [
  "is not", "are not", "not yet", "not implemented", "not supported",
  "not available", "not shipped", "not present", "cannot", "can't",
  "does not exist"
];

// "no other", "no longer", "no second" and friends are NOT denials of the
// capability -- they are ordinary English that happens to start with `no`.
// This list was derived by running the sweep against the tree and reading
// every false positive, not guessed.
const NOT_A_DENIAL_AFTER_NO = /^\s*(?:other|second|third|one|longer|matter|doubt|such\s+thing)\b/i;

const denyBeforeRes = DENY_BEFORE.map((w) => ({ text: w, re: wordRe(w) }));
const denyAfterRes = DENY_AFTER.map((w) => ({ text: w, re: new RegExp(w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i") }));

function denialFor(unit, tokenRe) {
  const masked = unit.replace(SQL_SYNTAX, (m) => "\u0000".repeat(m.length));
  const hit = masked.match(tokenRe);
  if (!hit || hit.index === undefined) return null;
  const start = hit.index;
  const end = start + hit[0].length;
  let before = masked.slice(Math.max(0, start - BEFORE_WINDOW), start);
  // A DENIAL DOES NOT CROSS A CLAUSE BOUNDARY. "reads no relation state at all
  // -- two join surfaces answering two questions" denies RELATION STATE, and
  // without this cut the `no` reached across the dash and landed on `join`.
  // The house clause separator is ` -- `; an em dash and a semicolon count too.
  const boundary = before.lastIndexOf(" -- ");
  const boundary2 = Math.max(before.lastIndexOf(";"), before.lastIndexOf("\u2014"));
  const cut = Math.max(boundary >= 0 ? boundary + 4 : -1, boundary2 + 1);
  if (cut > 0) before = before.slice(cut);
  const after = masked.slice(end, end + AFTER_WINDOW);

  for (const d of denyBeforeRes) {
    const m = before.match(d.re);
    if (!m || m.index === undefined) continue;
    if (d.text === "no" && NOT_A_DENIAL_AFTER_NO.test(before.slice(m.index + 2))) continue;
    return d.text;
  }
  for (const d of denyAfterRes) {
    if (d.re.test(after)) return d.text;
  }
  return null;
}

export function sweep(root) {
  const authorityPath = path.join(root, AUTHORITY);
  if (!fs.existsSync(authorityPath)) {
    return {
      skipped: true,
      reason:
        `${AUTHORITY} is absent -- regenerate it from ccode with ` +
        `tools/reports/engine_capabilities.py --out <site>/${AUTHORITY}`,
      findings: []
    };
  }
  const authority = readJson(authorityPath);
  if (authority.schema_version !== 1) {
    throw new Error(
      `${AUTHORITY}: unsupported schema_version ${authority.schema_version}; this checker knows 1`
    );
  }

  let exemptions = [];
  const exemptionsPath = path.join(root, EXEMPTIONS);
  if (fs.existsSync(exemptionsPath)) {
    exemptions = readJson(exemptionsPath).exemptions ?? [];
    for (const ex of exemptions) {
      if (!ex.reason || !String(ex.reason).trim()) {
        throw new Error(
          `${EXEMPTIONS}: ${ex.file ?? "?"} / ${ex.capability ?? "?"} has no reason. ` +
            "Every exemption states why the negative is TRUE; a silent mute is how a check dies."
        );
      }
    }
  }

  const caps = authority.capabilities.map((c) => ({
    ...c,
    tokenRes: c.tokens.map((t) => ({ text: t, re: wordRe(t) }))
  }));

  const findings = [];
  for (const file of walk(path.join(root, CONTENT)).sort()) {
    const rel = path.relative(root, file).split(path.sep).join("/");
    const text = fs.readFileSync(file, "utf8");
    const lines = text.split(/\r?\n/);
    for (const cap of caps) {
      if (exemptions.some((e) => e.file === rel && (e.capability === cap.id || e.capability === "*"))) continue;
      const seen = new Set();
      for (const unit of units(text)) {
        for (const token of cap.tokenRes) {
          const negation = denialFor(unit, token.re);
          if (!negation) continue;
          const key = `${cap.id}|${unit}`;
          if (seen.has(key)) break;
          seen.add(key);
          const lineNo = lines.findIndex((l) => l.includes(unit.slice(0, 60))) + 1;
          findings.push({
            file: rel,
            line: lineNo > 0 ? lineNo : null,
            capability: cap.id,
            state: cap.state,
            severity: cap.severity,
            token: token.text,
            negation,
            excerpt: unit.length > 160 ? `${unit.slice(0, 157)}...` : unit
          });
          break;
        }
      }
    }
  }
  return { skipped: false, authority, exemptions, findings };
}

export function report(result) {
  if (result.skipped) {
    console.log(`Capability sweep SKIPPED: ${result.reason}`);
    return;
  }
  const flags = result.findings.filter((f) => f.severity === "flag");
  const reviews = result.findings.filter((f) => f.severity === "review");
  for (const f of [...flags, ...reviews]) {
    const where = f.line ? `${f.file}:${f.line}` : f.file;
    console.log(
      `  [${f.severity}] ${where} -- ${f.capability} (${f.state}) ` +
        `"${f.negation}" near "${f.token}"`
    );
    console.log(`      ${f.excerpt}`);
  }
  console.log(
    `Capability sweep (advisory, never blocks): ${flags.length} flag, ` +
      `${reviews.length} review, over ${result.authority.capabilities.length} ` +
      `capabilities and ${result.exemptions.length} stated exemption(s).`
  );
  if (flags.length) {
    console.log(
      "  A 'flag' is a page denying something REGRESSION ALL re-proves every run. " +
        "Fix the page, or state the exemption with a reason."
    );
  }
}

// A check that has never been shown to fire has never been tested. This plants
// a contradiction the engine's own authority refutes, in a page that is really
// on disk, and fails if the sweep shrugs at it -- the same discipline
// check-site-freshness applies to its exact-value contracts.
export function selfTest(root) {
  const authority = readJson(path.join(root, AUTHORITY));
  const flagged = authority.capabilities.find((c) => c.severity === "flag");
  if (!flagged) throw new Error("capability self-test: no default-suite capability to test with");

  const probe = `x64base has no ${flagged.tokens[0]} yet.`;
  const caps = [{ ...flagged, tokenRes: flagged.tokens.map((t) => ({ text: t, re: wordRe(t) })) }];
  const hit = units(probe).some((u) => caps[0].tokenRes.some((t) => denialFor(u, t.re)));
  if (!hit) {
    throw new Error(
      `capability self-test: the sweep did NOT flag "${probe}", which the ` +
        `authority says is proven by ${flagged.specs.join(", ")}. The matcher is inert.`
    );
  }

  // The mirror: an AFFIRMATIVE sentence about the same capability must stay quiet,
  // or the sweep is just a token grep wearing a costume.
  const clean = `x64base ships ${flagged.tokens[0]}, proven by ${flagged.specs[0]}.`;
  const noise = units(clean).some((u) => caps[0].tokenRes.some((t) => denialFor(u, t.re)));
  if (noise) {
    throw new Error(
      `capability self-test: the sweep flagged the AFFIRMATIVE sentence "${clean}". ` +
        "A checker that fires on praise will be muted within a week."
    );
  }

  console.log(
    `Capability sweep self-test passed: a planted denial of ${flagged.id} was caught, ` +
      "and an affirmative sentence about it was not."
  );
}
