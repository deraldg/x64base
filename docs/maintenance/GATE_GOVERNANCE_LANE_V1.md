# Gate Governance Lane -- document, record, and maintain the build/commit/publish gates

**Status:** charter (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-09. **AIF-100** (claimed 2026-08-09, run `COWORK-20260809-001`) -- and the claim
was surfaced by the estate this lane governs: the collision gate's reconciliation advisory
("claim(s) with no intake row: AIF-100") flagged the missing row before this stamp landed.
Parent project: `project.x64base.runtime` (tooling) with a publication seam.

## Why now (owner: "they are getting to be good")

The gate estate has grown organically, one scar at a time, and it now WORKS -- two live catches
in a single hour on 2026-08-09: the hand-maintained `kRegressionSpecs` count turned a missing
bump into a compile error exactly as its comment promised, and the report-audit gate BLOCKED a
closeout for missing its own envelope (the "a report cannot approve itself" doctrine enforcing
itself mechanically). That maturity is the reason to govern them: an estate this good, grown
this organically, has no single census, no uniform record of what each gate proves, and no
standing procedure for adding one. The prior art for what happens otherwise is AIF-082's
instrument findings: four checkers wrong on first build, one passing vacuously -- a gate you
cannot enumerate is a gate you cannot re-prove.

## Scope -- the three gate surfaces

1. **Build-time gates** (compile is the gate): the `kRegressionSpecs` hand-maintained count;
   the duplicate-basename shadow guard (AIF-043); `static_assert` capacity checks (AIF-044,
   planned); MSVC/link failures used deliberately (LNK1104 on a running daemon).
2. **Commit/push gates** (the prepush chain): `repository_role_guard.py` (root/branch/refs),
   `prepush_gate.py` (staged-slice classification: binaries hard-block, data/fixture warn,
   mass-change warn) and its delegated checks -- `aif_collision_gate.py`, report-audit
   (`ai_report_audit` envelope + id uniqueness), `refcheck_v1.py` / `normcheck_v1.py` catalog
   drift, and the AIF-082 portal gates (`check_sandbox_git_guard.py --lock-only`,
   `check_house_style.py`, `check_mandatory_tracked.py`, `check_session_log_row.py`,
   `check_seed_budget.py`, `check_aif_claimed.py`). Plus the advisory-not-yet-wired:
   `check_host_python.py`.
3. **Publish gates** (site/main/manual): `check-public-content.mjs` + `check-diagrams` (site
   build chain), `stage_public.py` leak guards + `portal.yaml` sensitivity, `PROMOTE.manifest`
   allow-list + `rebuild-staging.ps1`, `docpush_preflight.py` HARD checks (source census 100%,
   catalog sync), the website-documentation-matrix closeout gate (fail-closed), and the Phase
   7->8 entry check / Phase 8 ascent gates of the flush plan.

Prior art to consume, not duplicate: `PREPUSH_GATE_REFERENCE_V1.md` (the commit-chain
reference -- becomes one chapter of the registry, not a competitor), `COST_BENEFIT_GATE_DOCTRINE_V1.md`,
`BETA1_EXIT_GATE_V1.md` (a lifecycle gate, referenced not absorbed), and AI_PORTAL's "Build It
to Prove It" rules (a checker is unproven until seen FAILING; bound every metric).

## Deliverables (milestones)

| M | Delivers | Gate |
|---|---|---|
| M0 | **Census (measure first).** Enumerate every gate on the three surfaces: name, path, surface, trigger (hook/manual/build), severity (hard/advisory), what it proves, owner lane, and whether a known-bad input has ever been seen to FAIL it. One table, one doc. | count published + each row cites file:line |
| M1 | **GATE_REGISTRY_V1** -- the maintained registry (M0 census promoted to a living doc). `PREPUSH_GATE_REFERENCE_V1` folded in as the commit chapter. Registered as a recall node (trigger: about-to-commit / about-to-publish). | registry tracked + reachable; no orphan gates |
| M2 | **Known-bad proofs.** For each HARD gate, a recorded known-bad input + the transcript of it failing (the "seen it FAIL" rule made an artifact). Gates that cannot be shown to fail get flagged as unproven, not assumed good. | every hard gate has a FAIL transcript or an unproven flag |
| M3 | **The add-a-gate procedure.** A short standing rule: a new gate ships with (a) a registry row, (b) a known-bad proof, (c) its severity + trigger declared, (d) advisory-first unless the owner rules blocking. The promote-final-tests rule is the sibling: final tests become regressions; regressions that guard policy become gates. | procedure in the registry; next new gate follows it |
| M4 | (Optional, prove the bottleneck first) **Gate-of-gates validator**: a check that the registry matches the actually-wired hooks (a registry row with no hook, or a hook with no row, is drift). Only build if M0 measures real drift. | validator sees a seeded mismatch FAIL |

## Rules this lane inherits (do not restate elsewhere)

- Measure before build (M0 before anything); a checker is unproven until seen failing (M2);
  advisory-first wiring; no perishable literals in the registry (point at the gate's own
  source for its current behavior; record only invariants + proofs).
- Asides during this lane follow the standing aside rule.

## Registration (on pickup, host-side)

`claim-aif` a fresh number (run id of the claiming session), add the intake row citing it,
stamp it here. Docs/tooling lane: authorable in-sandbox; anything touching hooks is verified by
running the real gate on the host with a known-bad input, per M2's own standard.
