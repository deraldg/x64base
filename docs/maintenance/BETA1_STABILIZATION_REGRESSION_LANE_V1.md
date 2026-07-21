# BETA-1 Stabilization & Regression Validation — lane (v1)

Status: **active (dev)** — stabilization gate, not a feature lane.
Owning lifecycle: DotTalk++ SDLC · engine hardening toward BETA-1.
Parent project: `project.x64base.runtime` (AIF-040).
Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-041).

## What this lane is

The disciplined path from "it compiles and the milestones are green" to "the engine is
BETA-1 worthy." Two intertwined jobs:

1. **Reliable regression coverage for all of this cycle's new work** — arrays, `$name`
   memory variables, `stop_on_error`, the DTV foundation, field codecs, RECNO64, and WAL
   durability. A feature is not BETA-ready until a REGRESSION-registered test proves it.
2. **A full validation pass through the existing regression suite.** Let the recently
   changed subsystems settle, run every curated REGRESSION entrypoint, and update tests
   **as we go** to track intended drift and evolution — never silently: each test change
   records which test, and why it changed (real regression fixed vs intended evolution).

Governing principle (project authority chain): **runtime proves.** The suite is the
proof that the engine is stable; a green build is not a green engine.

## Milestones

- **M1 — Regression coverage for the new work.** A REGRESSION-registered, self-
  bootstrapping test for each feature shipped this cycle:
  - **DotScript arrays** — `{…}` literals, `$name` memvars, one-based `$a[n]`, nested /
    chained subscripts, out-of-range rejection; reference-sharing vs `ACLONE` once the
    `A*` functions land (M1b-3).
  - **VAR memory variables** — store/read `$name`, scalar *and* array, case-insensitive
    names, scope (LOCAL shadow / PUBLIC persist).
  - **stop_on_error / errorstop** — OFF continues past an error, ERROR aborts
    (self-contained proof `errorstop/stop_on_error_regression.dts` exists — register +
    re-verify).
  - **field codecs** (`I/B/Y/T/X`) — encode/decode boundaries + VFP interop (M5 gate
    exists — fold in).
  - **RECNO64** — boundary past 2^31 and full `uint64` (tests exist — fold in).
  - **WAL / COMMIT durability** — write-ahead journal + COMMIT marker + crash-recovery
    replay (ACID beta-1).
  - **DTV foundation** — `dottalkpp_pdlc_foundation_smoke` ctest (exists).

  **Finding (2026-07-21, from starting M1):** `$name` / `$a[n]` resolve in the
  *expression* path (`?`/`CALC`/`FORMULA` → the `rhs_eval` ValueParser) but **not** the
  *predicate* path (`IF`/`WHILE`/`UNTIL`/`SCAN FOR` → `shell_eval_bool_expr` →
  `where_boolean_eval` → the compiled WHERE engine). **Decision (maintainer):** fix by
  **centralizing on the house expression system** — one evaluator both paths delegate to,
  so `$name` resolves once — *not* a substitution shim (which would add a third path). This
  is the `expression_runtime` convergence (project `x64base.dotscript`), the same
  "one canonical" principle as DTV. It is build-required and high blast radius (every
  predicate consumer), so it lands **against the regression net, not blind**: author the
  WHERE/IF baseline + arrays/VAR + a predicate-parity target test first (the parity test
  is RED until the convergence lands, then GREEN), then converge and prove no WHERE
  regression.

  **Registered this pass (2026-07-21).** `REGRESSION` now carries the cycle's
  DotScript-level proofs; the C++ proofs stay in `ctest` (their correct runner —
  `dottalkpp_pdlc_foundation_smoke`, `dottalkpp_recno64_boundary_test`,
  `dottalkpp_recno64_sparse_e2e_test`, `dottalkpp_field_codec_test`), not duplicated
  into `kRegressionSpecs`. New `REGRESSION` entries (proven green, 2026-07-21 build):
  `DOTSCRIPT_EXPR` (default — VAR/`$name`/arrays, green; self-bootstrap `STOP_ON_ERROR
  OFF` confirmed firing before BEGIN), `LEXING` (default — AIF-037 comment vocabulary,
  read-only, green); and explicit-run only: `DOTSCRIPT_PARITY` (the RED-until-convergence
  parity target), `CALC` (AIF-031 output routing, all 9 ValueKind cases green; leaves ECHO
  ON), `ERRORSTOP` (AIF-036, correct Phase-2 abort at line 27; leaves STOP_ON_ERROR ON).

  **Finding (2026-07-21, from proving the widened net):** the legacy
  `commit_rollback_test.dts` is **not regression-grade** — it assumes an already-open
  `students` table and does **not** self-bootstrap, so run standalone (after the default
  suite closed all areas) it selected a non-existent area and silently no-op'd
  (`no file open`; `ROLLBACK: discarded 0 change(s)`). It was therefore **pulled** from
  `kRegressionSpecs`. This is the concrete case that proves the environment-bootstrap
  rule is a gate, not a nicety.

  **Replacement authored (2026-07-21):** `pinocchio\wal_commit_rollback_regression.dts`,
  registered as `WAL_COMMIT_ROLLBACK` (explicit-run — it mutates the filesystem). Derived
  from the self-bootstrapping `wal_phaseA_proof.dts` but self-asserting: it `CREATE X64`s
  a throwaway `WALREGR` table, proves W1 (COMMIT applies a buffered+logged REPLACE) and W2
  (ROLLBACK discards one) via `.T.` markers, then ERASEs the table — never touching the
  shared `students` fixture. Awaiting the build + `REGRESSION RUN WAL_COMMIT_ROLLBACK`
  proof (expect W0/W1/W2 all `.T.`). The full `wal_phaseA_proof.dts` stays off the curated
  surface (self-labeled CANDIDATE/REVIEW_BEFORE_EXECUTION); this regression is the
  minimal, self-contained slice of it.

  **Doctrine — environment bootstrap (recorded 2026-07-21).** Every regression test
  **sets its own environment**; the ambient default is `STOP_ON_ERROR OFF` and legacy
  scripts preserve it. Corollaries enforced here: (1) a test that depends on a setting
  states it at its own top (e.g. `DOTSCRIPT_EXPR` sets `STOP_ON_ERROR OFF` because R8
  deliberately errors, and `SET ECHO OFF` for a clean judged region); (2) a test that
  leaves the ambient dirty (ERRORSTOP → policy ON, CALC → ECHO ON) stays **out of the
  default suite** so it cannot contaminate the ordered run — it remains explicitly
  runnable. `REGRESSION ALL` therefore preserves the clean ambient end to end.

- **M2 — Full regression sweep + settle.** Run all curated REGRESSION entrypoints;
  produce a suite status matrix (pass / fail / skipped); triage every failure as either
  (a) a real regression → fix, or (b) intended evolution → update the test and record the
  reason. Test-maintenance is documented (mirrors AIF-024), so drift compensation is
  auditable, not silent.

- **M3 — Complete code-refactor analysis** *(item 1).* A report-first assessment of the
  engine for refactor opportunities before BETA-1: duplication a review would flag
  (AIF-037 / Rule of Three), separation-of-concerns, dead / experimental code, and a
  prioritized tech-debt register (do-before-BETA vs defer). No blind refactors — analysis
  and a register first.

- **M4 — `dotref` / `foxref` maintainability decision** *(item 2).* `dotref.hpp` is ~248
  entries / 1000+ lines and hand-maintained, and this cycle proved it drifts (the VAR
  entry). Decide the maintenance model: keep the curated header, or **generate** it from
  the command registry + `SRC*` usage contracts (the COMMENTS pipeline already harvests
  the same fields). Weigh single-source-of-truth (contracts) vs a curated catalog, drift
  risk, and build-time vs generated. Output: a decision record (+ migration sketch if
  generating).

- **M5 — Language-support scope decision (manual-level)** *(item 3).* Decide how far to
  take localization for BETA-1, at least to the manual. Confirm whether the manual is
  **spined to be language-friendly** — i.e., whether the manual assembler + the
  messaging / locale spine (SYSTEM_MESSAGES, `locale_spine_catalog`, en-US + de/es/fr/it)
  support a localizable manual, or the manual is English-only for BETA-1. **See:
  messaging** (`docs/.../Messaging & Localization`; `src/help/locale_spine_catalog.*`).
  Output: a scoped BETA-1 language target + whether the manual spine needs work to be
  locale-ready.

- **M6 — Peer review** *(item 4).* A pre-BETA peer-review pass — human and/or cross-AI
  (ChatGPT / Codex) — over the engine surface, the usage contracts, and the regression
  suite, delivered as reviewable packages per the Outside-AI Delivery Rule. Output:
  review findings triaged into the BETA-1 gate.

## Relationship to BETA-1

This lane is the **evidence engine for the BETA-1 readiness gate.** Its exit condition is
the regression suite green (every red triaged and resolved or documented as intended
evolution), the refactor register cleared-or-deferred, and the `dotref`/`foxref`,
language-scope, and peer-review decisions recorded. It pairs with the separate BETA-1
exit-conditions checklist (the falsifiable "all must be true" list).

## Doctrine hooks

- **REGRESSION** owns the curated, self-bootstrapping test entrypoints (`runtime proves`).
- **Test-maintenance discipline:** every drift/evolution edit to a test records which
  test and why — settling the suite is documented, not silent (AIF-024).
- **Refactor analysis** under AIF-037 (representative by design / Rule of Three).
- **Contract validation** via `CMDHELPCHK` + the COMMENTS pipeline feeds M2 and M4 (the
  usage-contract sweep this cycle is the first input).

## Non-goals / honesty

Not a rewrite, and not a date promise — BETA-1 ships when the suite is green and the
decisions are recorded, not on a calendar. Dev-only until proven + promoted.

## Provenance

- Parent project: `project.x64base.runtime`.
- Related lanes: arrays (AIF-038), DTV/tuple (`docs/maintenance/tuple_pdlc/`), errorstop
  (AIF-036), field codecs (AIF-030), WAL durability (AIF-017/023).
- Inputs already in-tree: `REGRESSION` curated entrypoints; `dottalkpp_pdlc_foundation_smoke`;
  `errorstop/stop_on_error_regression.dts`; RECNO64 boundary tests; VFP interop gate;
  the usage-contract crosswalk (`CMDHELPCHK` + `SRCUSAGE`).
