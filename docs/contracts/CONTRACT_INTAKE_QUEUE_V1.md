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
