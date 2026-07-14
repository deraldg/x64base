# DotTalk++ Contract Intake Queue v1

Status: active queue.

## Purpose

This queue captures contract candidates that are visible but not yet fully
registered, proven, or normalized.

Items should either graduate into `CONTRACT_REGISTRY_V1.md`, become source/test
work, or be marked rejected/superseded.

## Open Intake

| Candidate | Kind | Evidence now | Needed next |
| --- | --- | --- | --- |
| Command usage extraction as general contract model | Usage | Source-defined in `src/meta/metacollect.cpp` | Registry crosswalk from harvested commands to contract rows |
| `@dottalk.contract` header annotations | Source/provenance | Source-defined in include headers | Scanner report and policy for annotation fields |
| File format contracts for x64/v128/DBF/memo/index families | Data | Scattered source/docs | Central file-format contract index |
| Build option and dependency contracts | Build | CMake/options/docs scattered | Build contract document and registry rows |
| Destructive command safety contracts | Safety/usage | Runtime/source scattered | Command-by-command safety matrix |
| Import/export locale contracts | Data/safety | Design need identified | Contract doc or section under value/locale |
| GUI request/event/result schema | UI/runtime | Source skeleton | Schema contract and Python/C++ mirror checks |
| Python/C++ binding contract | Runtime/binding | Early pydottalk/preview behavior | Binding contract once pydottalk surface stabilizes |
| Test fixture contracts | Test/data | Fixtures exist ad hoc | Fixture manifest and purpose map |

## Runtime Findings — Observed Behavior Awaiting a Contract Decision

Surfaced by the MCC databuild session, 2026-07-14. Full transcripts and context
in `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md`. These are
runtime observations, not yet contracts: source may be correct and the docs
wrong, or vice versa. Each needs a maintainer decision before it becomes a
registered rule or a source fix (through
`SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`).

| Finding | Kind | Evidence now | Needed next |
| --- | --- | --- | --- |
| `SETLMDB PHYSICAL` is not a valid form; fails as missing container `PHYSICAL.cdx.d`. Correct form `SETLMDB 0`. | Usage/runtime | Runtime transcript 2026-07-14; also failing silently in `canaries/mcc_exhaustive_full_regression_canaries_lmdb.dts` | Decide: fix the canary, and either accept `SETLMDB 0` as the only clear form or add `PHYSICAL` as an alias in `cmd_setlmdb.cpp`. |
| `BUILDLMDB` and `SETLMDB` report different LMDB env directories for the same container (`LMDB\x64\...` vs `INDEXES\x64\...`). `SET INDEX` agrees with `BUILDLMDB`. | Runtime/data/path | Runtime transcript 2026-07-14 | Reconcile the env-path resolution in `cmd_setlmdb.cpp` against `cmd_buildlmdb.cpp`; two of three surfaces agree. |
| `SHOW TABLE` misreports the table path (drops `dbf\<lane>`), and on a VFP readback reported an `indexes\x32` container while the VFP one was attached. Behavior correct, display wrong. | Runtime/display | Runtime transcript 2026-07-14 | Fix the `SHOW TABLE` path/index display. It is exactly the kind of misreport that sends work chasing ghosts. |
| Bare `ASC` errors (`ASC expects 1 argument(s)`) and does not undo `DESC`; runner continues, leaving descending order silently active. | Usage/runtime | Runtime transcript 2026-07-14 | Decide whether bare `ASC` should reset ascending, or document `SET ORDER TO TAG` as the canonical reset. |

## Recently Seeded

| Contract | Current state |
| --- | --- |
| Value/Locale/Collation Contract | Design-intended, registered |
| Database Safety Contract | Design-intended, registered |
| Windowed Application Contract | Design-intended, registered |
| Contract Lifecycle | Active process contract |
| Contract Registry | Active registry |

## Queue Rules

- Do not leave a candidate here indefinitely without a next action.
- Prefer graduating candidates into the registry with honest low evidence over
  losing them.
- Mark rejected ideas explicitly when they were considered and declined.
- Link to reports or source when the candidate becomes stronger than design
  intent.

