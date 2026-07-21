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

  **Convergence implemented + PROVEN (2026-07-21, dev).** Grounded by a
  full recon of both eval paths: the two are separate engines (display = the `rhs_eval`
  ValueParser over `session_vars()`; predicate = the compiled WHERE engine), and the `$`
  sigil is *stripped* in `sql_to_dottalk_where` before the WHERE compiler ever sees it, so
  the WHERE grammar has no `$`/`[`/`{` at all. Rather than teach three tokenizers to carry
  the sigil and then duplicate the resolver (which would fork it), the fix centralizes on
  the one existing house resolver: at the single predicate entry point
  `shell_eval_bool_expr` (`src/cli/shell_bool_eval_adapter.cpp`), a predicate that
  references DotScript state (`$name`, `$a[n]`, `{...}` — detected by `$`+ident or `{`) is
  delegated to `dottalk::expr::eval_rhs_avalue` (the same array-aware, `session_vars()`-backed
  evaluator the display path uses), ahead of both the injected AST evaluator and the WHERE
  engine. Field-only predicates never enter the branch (behavior unchanged); a memvar
  predicate the house evaluator can't handle falls through to the old path rather than
  erroring — **no regression surface**. Scope: covers `IF`/`WHILE`/`UNTIL` (which route
  through `shell_eval_bool_expr`); `SCAN FOR`/`LIST FOR` compile-once-run-per-record paths
  are a documented follow-up. **Proven on the 2026-07-21 MSVC build:** `DOTSCRIPT_PARITY`
  flipped **red→green** (both `PARITY_predicate_memvar` and `PARITY_predicate_array_subscript`
  now `PASS`); `DOTSCRIPT_EXPR` stayed green; `NONDESTRUCTIVE` (field predicates: `LIST FOR`,
  `SEEK`, aggregate `FOR`/`WHERE`) and the full `CURSOR` family regression (physical +
  CNX/FNAME ordered traversal, SEEK, boundaries) stayed green — no WHERE/field-predicate
  regression, and the change compiled clean first try. Follow-ups: (1) `SCAN FOR`/`LIST FOR`
  compile-once-per-record predicates; (2) `DOTSCRIPT_PARITY` is now GREEN and side-effect-free,
  so it can be promoted into the default suite (and its summary updated from "RED until…").

  **Finding (2026-07-21, from reconning the scan path) — `$` is overloaded, and the
  predicate surface is forked into THREE evaluators.** (a) In the scan/filter grammar
  (`predx::eval_expr`, `FOR LAST_NAME $ "MIT"`), **`$` is the xBase substring-containment
  operator**, not a memvar sigil. The convergence detector was therefore hardened: `$` is
  treated as a memvar sigil only when it *starts an operand* (at the start, or the previous
  non-space char is not an operand terminator), so `a$b` containment stays on the WHERE
  path. (b) The predicate surface actually has **three** evaluators — the house `rhs_eval`
  ValueParser (display + now `IF`/`WHILE`), `where_eval` (`compile_where_expr_cached` /
  `run_program`, used by `WHERE`/`SQL`/browser), and `predx::eval_expr`
  (`predicate_eval.hpp`, used by `LIST`/`COUNT`/`SCAN FOR` + `SET FILTER`). This fork is
  itself an **AIF-037 / M3 refactor-analysis input** (representative-by-design: one
  predicate evaluator, not three). **Scan-path convergence plan (deferred to a netted
  milestone, not a blind patch):** extract the memvar/array delegation into one shared
  bridge helper (`looks_like_dotscript_expr` + `avalue_truthy` + `eval_rhs_avalue` call),
  reuse it in `shell_eval_bool_expr` (Rule of Three), and inject it at `predx::eval_expr`'s
  per-record seam — authored **against a new `SCAN FOR`/`LIST FOR` memvar parity test that
  is RED first**, exactly as `DOTSCRIPT_PARITY` was for `IF`. The `$`-overload means the
  detector, not just the injection, is the load-bearing part on the scan side.

  **Scan convergence — shared bridge built, predx wired, empirical build pending
  (2026-07-21, dev).** The memvar/array delegation is now one shared header
  `include/cli/expr/dotscript_predicate_bridge.hpp` (`looks_like_dotscript_predicate` — the
  hardened operand-leading `$` detector — + `avalue_truthy` + `try_eval_dotscript_predicate`).
  `shell_bool_eval_adapter.cpp` (IF/WHILE) was refactored onto it (Rule of Three; the local
  copies removed), and `predx::eval_expr` (`predicate_eval.cpp`) was wired onto it at its
  per-record seam. Authored + registered the RED `SCAN_PARITY` net (`LOCATE`/`COUNT FOR`
  with a `$threshold`). **Honest open item:** the recon showed the predicate surface is
  forked across **five** evaluators — the house `rhs_eval` ValueParser, `where_eval`,
  `predx::eval_expr`, `predicates::eval_expr` (→ `dottalk::expr::eval_bool`), and the unwired
  `dt/predicate/predicate_engine`. Source alone doesn't reveal which one `LOCATE`/`COUNT`
  actually reach, so **`REGRESSION RUN SCAN_PARITY` after the build is the determinant**: if
  it flips green, `predx` was the path; if it stays red, the scan commands use
  `predicates::eval_expr`/`eval_bool` and that seam gets the same bridge next (cheap — one
  call). The bridge patch is harmless either way (field-only/containment predicates never
  match it). This five-way fork is the sharpest **AIF-037 / M3** input yet: *one* predicate
  evaluator, not five. Regression guard: rebuild must keep `DOTSCRIPT_PARITY` +
  `DOTSCRIPT_EXPR` green (the IF/WHILE refactor onto the bridge must not change behavior).

  **Refined (2026-07-21, maintainer correction + deeper recon).** (1) `BOOLEAN` →
  `edu_BOOLEAN` uses the `dt/predicate/predicate_engine` **student/teaching** evaluator
  (self-labeled "not wired to the expression engine yet") — NOT a production predicate
  path, so it drops out of the unify count. The real **production** predicate evaluators
  are four: house `rhs_eval` ValueParser, `where_eval`, `predx::eval_expr`, and
  `dottalk::expr::eval_bool`. (2) The **main** scan/filter seam is
  `dottalk::expr::eval_bool` (`value_eval.cpp`), used by `cmd_scan`, `scan_selector`
  (→ `COUNT`/`LIST FOR`), `cmd_sort`, and `predicates::eval_expr` — **not** `predx`, which
  is a narrow side path. `eval_bool`'s `compile_where → make_record_view` route strips `$`
  and never consults `session_vars()`, so it was wired onto the shared bridge too. The
  scan convergence now delegates at both `eval_bool` (main) and `predx::eval_expr` (side).
  Header placement verified: `include/cli/expr/dotscript_predicate_bridge.hpp` sits with
  `rhs_eval.hpp`/`api.hpp`/`value_eval.hpp` under the `include/` root that
  `target_include_directories(dottalkpp PUBLIC .../include)` puts on the path. With
  `eval_bool` wired, `REGRESSION RUN SCAN_PARITY` after the build should flip red→green.

  **PROVEN (2026-07-21 build).** `SCAN_PARITY` flipped red→green: `LOCATE FOR VAL > $threshold`
  located VAL=20 (`SCAN_locate_predicate_memvar:PASS`) and `COUNT FOR VAL > $threshold`
  returned 2. `DOTSCRIPT_PARITY` + `DOTSCRIPT_EXPR` stayed green (the IF/WHILE refactor onto
  the shared bridge is behavior-preserving), and `NONDESTRUCTIVE` stayed green (field /
  containment predicates unchanged), on a clean compile. **`$name`/`$a[n]` now resolve
  everywhere a predicate is evaluated — display (`?`/`CALC`), control flow
  (`IF`/`WHILE`/`UNTIL`), and scan/filter (`LOCATE`/`COUNT`/`SCAN`/`LIST FOR` + `SET
  FILTER`) — through the ONE shared bridge (`dotscript_predicate_bridge.hpp`), reused by
  `shell_eval_bool_expr`, `predx::eval_expr`, and `dottalk::expr::eval_bool`.** The
  DotScript memvar/array expression-path convergence (AIF-041) is complete: the marquee
  language capability *and* an AIF-037 consolidation (one bridge, not four forked copies)
  in one change. Remaining tidy-ups (non-blocking): promote `DOTSCRIPT_PARITY`/`SCAN_PARITY`
  to the default suite now that both are green; the deeper four-evaluator unification stays
  an M3 refactor target.

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
