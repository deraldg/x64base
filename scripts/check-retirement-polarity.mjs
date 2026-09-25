#!/usr/bin/env node
// check-retirement-polarity.mjs
//
// THE OTHER POLARITY. `check-capability-contradictions.mjs` sweeps for a SHIPPED
// capability described as planned or missing. Its authority is a list of what
// ships, so a page asserting a REMOVED surface has nothing to match against and
// the sweep runs green over it. Measured 2026-09-15: the getting-started FAQ
// described the `SQL` verb as a working COUNT command for eleven days after the
// owner retired it, while both tiers of the freshness check were green the whole
// time. The sweep that found it was a person asking.
//
// This reads a register of retirements and flags a page that states a retired
// form as though it still works.
//
// THE HARD PART IS NOT DETECTION, IT IS THE EXCUSE. A page explaining a
// retirement necessarily contains the retired grammar -- that is what makes the
// explanation useful. So a match is only a finding when NO retirement marker
// appears near it. The window is deliberately generous; a false negative here
// costs one missed sentence, a false positive costs the check's credibility and
// then the check.
//
// Advisory by design, like its sibling. It reports and exits 0 unless --strict.

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const CONTENT = join(ROOT, 'content');
const WINDOW = 6;                  // lines either side that may carry the excuse
const strict = process.argv.includes('--strict');
const argRoot = (() => {
  const i = process.argv.indexOf('--content');
  return i > -1 ? process.argv[i + 1] : CONTENT;
})();

const reg = JSON.parse(readFileSync(join(HERE, 'engine-retirements-v1.json'), 'utf8'));
let exempt = { exemptions: [] };
try {
  exempt = JSON.parse(readFileSync(join(HERE, 'retirement-polarity-exemptions.json'), 'utf8'));
} catch { /* an absent exemptions file means none, not a failure */ }

for (const e of exempt.exemptions) {
  if (!e.reason || !e.reason.trim()) {
    console.error(`retirement sweep: exemption for ${e.file} has no reason. Refused.`);
    process.exit(2);
  }
}
const isExempt = (file, id) =>
  exempt.exemptions.some(e => e.file === file && (e.retirement === '*' || e.retirement === id));

const markers = reg.excuse_markers.map(m => m.toLowerCase());
const excused = (lines, at) => {
  const lo = Math.max(0, at - WINDOW), hi = Math.min(lines.length, at + WINDOW + 1);
  const near = lines.slice(lo, hi).join('\n').toLowerCase();
  return markers.some(m => near.includes(m));
};

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (name.endsWith('.mdx') || name.endsWith('.md')) out.push(p);
  }
  return out;
}

// --selftest replays the sentences that motivated each register row. The first
// draft of this file passed over its own founding example -- the FAQ line ends
// "the name is historical", and `historical` was in the excuse list -- so the
// stale sentence talked its way out using the checker's own vocabulary. That is
// why the fixtures live in the register beside the patterns they exercise.
if (process.argv.includes('--selftest')) {
  let bad = 0;
  for (const r of reg.retirements) {
    const hits = line => r.patterns.some(p => new RegExp(p, 'i').test(line));
    for (const line of (r.must_flag || [])) {
      const ok = hits(line) && !excused([line], 0);
      if (!ok) { bad++; console.log(`  FAIL ${r.id}: should FLAG but did not:\n       ${line}`); }
    }
    for (const line of (r.must_pass || [])) {
      const ok = !hits(line) || excused([line], 0);
      if (!ok) { bad++; console.log(`  FAIL ${r.id}: should PASS but was flagged:\n       ${line}`); }
    }
  }
  const n = reg.retirements.reduce((a, r) =>
    a + (r.must_flag || []).length + (r.must_pass || []).length, 0);
  console.log(bad
    ? `Retirement sweep SELFTEST: ${bad} of ${n} fixture(s) FAILED.`
    : `Retirement sweep SELFTEST: ${n}/${n} fixtures pass.`);
  process.exit(bad ? 1 : 0);
}

const findings = [];
for (const path of walk(argRoot)) {
  const rel = relative(ROOT, path).split('\\').join('/');
  const lines = readFileSync(path, 'utf8').split('\n');
  for (const r of reg.retirements) {
    if (isExempt(rel, r.id)) continue;
    for (const pat of r.patterns) {
      const re = new RegExp(pat, 'i');
      lines.forEach((line, i) => {
        if (!re.test(line)) return;
        if (excused(lines, i)) return;
        findings.push({
          file: rel, line: i + 1, id: r.id, retired_on: r.retired_on,
          replaced_by: r.replaced_by, severity: r.severity,
          text: line.trim().slice(0, 150),
        });
      });
    }
  }
}

const files = new Set(findings.map(f => f.file));
console.log(
  `Retirement polarity sweep: ${findings.length} assertion(s) over ` +
  `${reg.retirements.length} retirement(s) and ${exempt.exemptions.length} stated exemption(s).`);
if (findings.length === 0) {
  console.log('  Nothing on the site states a retired surface as live.');
} else {
  for (const f of findings) {
    console.log(`  ${f.file}:${f.line}  [${f.id}, retired ${f.retired_on}]`);
    console.log(`     ${f.text}`);
    console.log(`     -> ${f.replaced_by}`);
  }
  console.log(`  ${files.size} file(s). Each line states a form the engine no longer has,`);
  console.log('  with no nearby word saying so. Fix the sentence, or add an exemption WITH A REASON.');
}
process.exit(strict && findings.length ? 1 : 0);
