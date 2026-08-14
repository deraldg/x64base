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

## Scoring pass 2026-08-13 (member.ai.claude.cowork, coworker; owner review needed)

Occasioned by an owner question -- whether x64base is beta 2, DotTalk++ beta 1, LabTalk
alpha 0 -- and by the observation that the build has read `v0.6` for months. This gate
already answers the first part, so it was scored rather than a new scheme invented. The
rule at the head of this document is why: status is earned, not asserted.

**Result: BETA-1 is NOT met.** Two structural rows are red, six cannot be scored without
runs, and no row moved to MET in this pass.

| # | Scored | Evidence, measured this session |
| --- | --- | --- |
| A1 | **NOT-YET** (was PARTIAL) | Both matrices EXIST -- `.github/workflows/ci.yml` runs `ubuntu-latest` and `windows-latest`. The row demands green on the beta commit, and the tree carries a metacollect build broken by the `FILE()` slot-resolution change. A red build in the tree forecloses A1 regardless of CI configuration. |
| A3 | PARTIAL (unchanged) | No two-compiler warning log produced this session. |
| C1 | **NOT-YET** (confirmed) | `FN_COVERAGE` still warns on `FILE` in every prepush-gate run today. `SYSFUNC_IMPORT_v1.csv` was regenerated on disk (70 -> 75 rows) but STILL carries no `FILE` row, so committing it would not clear this. |
| C2 | PARTIAL (unchanged) | No COMMENTS reharvest this session. |
| C3 | improved, not scored | Website claims tightened: alpha -> beta references corrected, the ECO map relabelled to what it is, the challenge page given rules and a judge. Row needs a site reality audit against the proof registry, which was not run. |
| E2 | **MET** (was PARTIAL) -- see the correction below | Clause 1: promotion completed and verified -- staging cold-clone build green (`pro-md`, libsodium/lmdb/nlohmann-json/sqlite3 resolved), `main` at `1de39e1e3`, projection DRIFT 0 across 798 files. Clause 2: at `908db87eb`, 1,058 engine sources scanned, **0 untracked**, and **0 uncommitted** in `src/`+`include/`+`tests/`. |
| B1 B2 B3 A2 | **UNSCORED** | Each needs a transcript from an executing binary (regression suite, restart, data-integrity proofs). None was run. Left unscored deliberately rather than inferred -- this gate accepts a durable artifact, not a recollection. |
| C4 D1 D2 D3 E1 E3 | NOT-YET (unchanged) | Decision records and the peer-review pass; no work this session. |

Shortest path to a defensible declaration, in dependency order: land or revert the 27
uncommitted source/test changes; track or delete `src/agile/edu_agile.cpp`; fix the
metacollect build; let CI turn A1 green. That clears the two structural rows and reduces
the remainder to the B block, which is a regression RUN rather than a judgement call.

**Correction, same session, a few hours later.** The first three of those four were done
before this document was committed, so the E2 row above was rewritten rather than left to
be read as current -- a scored gate whose scores are already stale is worse than an
unscored one, because it reads as measurement. What changed:

- `908db87eb` landed the 27 changes as one slice (file-contract headers across tests and
  tools, `cmd_order` layer corrected, `check_cpp_ascii` extended) and tracked
  `src/agile/edu_agile.cpp` + `agile.hpp`, removing five misfiled or duplicated files
  (`shell_api.cpp` at root was a 2,100-byte truncated copy of the 13,080-byte
  `src/cli/shell_api.cpp`; three `.dts`/`.ps1` under `src/cli/` were misfiled scripts).
- The metacollect build was unbroken by adding `src/common/path_resolver.cpp` and
  `src/common/path_state.cpp` to the `dt_meta` closure. It was never a signature break:
  `fn_string.cpp` and `function_catalog.cpp` compile into TWO closures, the engine linked
  the definitions and `dt_meta` did not, so only `metacollect` failed while every other
  target stayed green. `metacollect.exe` now links.

A1 is therefore UNBLOCKED but still NOT-YET: the row wants a clean build **and test** on
BOTH matrices on the beta commit, and what exists is one matrix, locally, with no test
run. It is now answerable by a CI run rather than by any further repair.

Recorded because the version string and the maturity model have been drifting apart: the
build prints `v0.6`, `projects.yaml` says `active_beta` for `project.x64base.runtime`, and
this gate says not yet. Three records of one fact with nothing comparing them -- which is
the same defect the gate itself was written to prevent.

## How this gate is worked

The gate is filled by **AIF-041** milestones: M1→B1, M2→B2, M3→D3, M4→C4, M5→D1, M6→E1;
A/B via CI + restart + the suite; C1/C2 via the COMMENTS→CMDHELP→CMDHELPCHK pipeline. When
every REQUIRED row is `MET` with its artifact, BETA-1 is declared in a closeout (E3).

## Provenance

Lane: `docs/maintenance/BETA1_STABILIZATION_REGRESSION_LANE_V1.md` (AIF-041). Parent
project: `project.x64base.runtime`.
