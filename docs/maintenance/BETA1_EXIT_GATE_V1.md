# BETA-1 Exit Gate — falsifiable checklist (v1)

Status: **draft, active** — the "all must be true" list for declaring the x64base engine
**BETA-1**. Paired with the evidence lane `BETA1_STABILIZATION_REGRESSION_LANE_V1.md`
(AIF-041), which is the engine that fills these boxes.

Rule (project doctrine): **status is earned, not asserted.** BETA-1 is declared only when
every REQUIRED row below is met and cites its proof artifact. "Runtime proves." A box is
`MET` only with a durable artifact — a passing test transcript, a CI run, a report — not a
recollection.

Status legend: `MET` · `PARTIAL` · `NOT-YET` · `BLOCKED` · `N/A`.

## A. Build & runtime integrity

| # | Condition (falsifiable) | Proof artifact | Status |
| --- | --- | --- | --- |
| A1 | Clean full build **and test** on **both** CI matrices (MSVC Release + Ubuntu/GCC) on the beta commit | GitHub Actions run (green) for that SHA | PARTIAL — confirm Actions on `7f7b7c75` + later |
| A2 | A full-stack restart from the beta binary **exposes every shipped feature** (no feature hidden by a stale running instance) | restart transcript showing arrays/VAR/errorstop live | NOT-YET |
| A3 | No new compiler warnings introduced on the beta surface under `/W4 /permissive-` and `-Wall -Wextra -Wpedantic` | build logs | PARTIAL |

## B. Regression proof (AIF-041 spine)

| # | Condition (falsifiable) | Proof artifact | Status |
| --- | --- | --- | --- |
| B1 | **Every feature shipped this cycle has a REGRESSION-registered, self-bootstrapping test that passes:** arrays (`{}`/`$name`/`$a[n]`/nested/out-of-range), VAR memvars, `stop_on_error`, field codecs (I/B/Y/T/X + VFP interop), RECNO64 boundary (>2^31 + uint64), WAL/COMMIT durability + crash-recovery replay, DTV foundation smoke | `REGRESSION LIST` + per-feature teed pass transcripts | NOT-YET — **this is AIF-041 M1** |
| B2 | **Full** curated REGRESSION suite green — or each red triaged as (a) real regression → fixed, or (b) intended evolution → test updated with recorded reason | suite status matrix (AIF-041 M2) | NOT-YET |
| B3 | Data-integrity proofs hold end-to-end: RECNO64 sparse-file read-back, VFP round-trip both directions, COMMIT crash-recovery replay | existing proof transcripts folded into the suite | PARTIAL (proofs exist; not yet suite-registered) |

## C. Documentation & contract integrity

| # | Condition (falsifiable) | Proof artifact | Status |
| --- | --- | --- | --- |
| C1 | `CMDHELPCHK` clean — registry ↔ `@dottalk.usage` contracts ↔ HELP DATA ↔ DOTREF reconcile with no unresolved mismatch | `CMDHELPCHK` report | NOT-YET (needs reharvest + run) |
| C2 | `@dottalk.usage` contracts match behavior for the behavior-changed surface, confirmed via COMMENTS reharvest | reharvest + `CMDHELPCHK` diff clean | PARTIAL (contracts fixed this cycle; reharvest pending) |
| C3 | Public docs / website claim **no** capability beyond its proven status (PLANNED/PARTIAL/SUPPORTED honest); ACID stated as partial/beta-1 | site reality audit | PARTIAL |
| C4 | `dotref`/`foxref` maintainability decision recorded (hand-header vs generated) | decision record (AIF-041 M4) | NOT-YET |

## D. Scope decisions recorded (recorded ≠ implemented)

| # | Condition (falsifiable) | Proof artifact | Status |
| --- | --- | --- | --- |
| D1 | BETA-1 language-support scope decided + manual locale-readiness assessed | decision record (AIF-041 M5) | NOT-YET |
| D2 | Tuple/DTV **runtime** explicitly **scoped OUT** of BETA-1 (foundation only; TupleCell contract NOT frozen) — so "beta" cannot imply tuples ship | decision note (tuple_pdlc) | PARTIAL (stated on agent-sync + decision docs) |
| D3 | Code-refactor register produced; each item done or explicitly deferred-past-beta | refactor register (AIF-041 M3) | NOT-YET |

## E. Review & promotion

| # | Condition (falsifiable) | Proof artifact | Status |
| --- | --- | --- | --- |
| E1 | Peer-review pass complete (human + cross-AI); findings triaged into this gate | review findings doc (AIF-041 M6) | NOT-YET |
| E2 | Clean promotion to `C:\x64base` + GitHub push; `git ls-files` completeness verified (no GLOB-untracked source) | staging build green + push SHA | PARTIAL (arrays/DTV done `7f7b7c75`; contract edits + tests pending) |
| E3 | The BETA-1 declaration itself cites the proof artifacts above and is recorded as a closeout | BETA-1 closeout + audit envelope | NOT-YET |

## Explicitly OUT of scope for BETA-1 (so the label is honest)

- **Tuple / DTV runtime** — foundation lib only; the canonical wire, comparison, adapters,
  and TupleCell/TupleRow contracts are post-beta.
- **Code blocks (`{|…|}`), maps** and other future DotScript composites.
- **Array `A*` functions** unless M1b-3 lands + proves them before the gate closes;
  otherwise arrays ship at the literal/subscript/memvar level and the function surface is
  post-beta.
- **Full ACID** — durability/atomicity are partial (ACID beta-1).
- **Full localization** — target set by D1.

## How this gate is worked

The gate is filled by **AIF-041** milestones: M1→B1, M2→B2, M3→D3, M4→C4, M5→D1, M6→E1;
A/B via CI + restart + the suite; C1/C2 via the COMMENTS→CMDHELP→CMDHELPCHK pipeline. When
every REQUIRED row is `MET` with its artifact, BETA-1 is declared in a closeout (E3).

## Provenance

Lane: `docs/maintenance/BETA1_STABILIZATION_REGRESSION_LANE_V1.md` (AIF-041). Parent
project: `project.x64base.runtime`.
