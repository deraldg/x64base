# AI Portal C++ Reach and GitHub Main Drift — 2026-07-12 v1

Status: correction implemented and staging proof passed
Owning lifecycle: DotTalk++ SDLC plus LabTalk SDLC
SDLC lane: review
Truth state: development source inspected
Proof state: static source and Git comparison
Risk class: source/help wording; read-only command behavior
Source path: `D:\code\ccode`
Staging path: `C:\x64base`
Public target: `github.com/deraldg/x64base` branch `main`
Next gate: review explicit Git scope, commit, push, and merge through main CI

## Finding

The working AI Portal has not become a native C++ portal or autonomous agent
runtime.

Current implementation:

- Python/Tk portal: `labtalk/portal/labtalk_portal.py`
- YAML registries: `labtalk/registries/*.yaml`
- durable seeds and handoff contracts: `labtalk/ai_portal`
- root fast start: `AI_PORTAL.md`

C++ has a read-only `MAINT AI` onboarding and visibility surface in
`src/cli/cmd_maint.cpp`, with curated DOTREF/HELP wording. Development C++ still
claimed the LabTalk portal link was not started. That is documentation drift.

No `AI_PORTAL`, `PORTAL`, or `LABTALK` native command is registered in the
central command registry.

## Drift against freshly fetched GitHub main

For current C/C++ files under `src`, `include`, and `bindings`:

| State | Count |
| --- | ---: |
| Development files inspected | 980 |
| Exact matches with `origin/main` | 888 |
| Shared paths with different content | 81 |
| Development-only paths | 11 |
| Main-only paths | 5 |

Central command registrations:

- development: 223
- main: 218
- added in development: `ARCTICTALK`, `CONCAT`, `EXITS`, `HANUKKAH`,
  `REGRESSION`, `STRCAT`
- removed in development: `TURBOTALK`

Application C++ paths under `src/app` and `include/app` match main. The
development-only application drift is the LabTalk `apps.yaml` registry, not a
new native AI application.

The staging branch is four commits and 92 files ahead of main, primarily the
LabTalk portal, campus/SDLC documents, diagrams, launchers, and proof material.
The newer AI Portal seed set remains uncommitted in staging.

## Source mutation contract preflight

Source target:

- `src/cli/cmd_maint.cpp`
- `include/dotref.hpp`
- `src/help/helpdata_messages.cpp`

Owning subsystem: DotTalk++ CLI maintenance command, HELP/DOTREF, message
catalog; downstream LabTalk AI Portal.

Contracts read:

- `docs/contracts/README.md`
- `docs/contracts/CONTRACT_REGISTRY_V1.md`
- `docs/contracts/CONTRACT_LIFECYCLE_V1.md`
- `docs/contracts/WEBSITE_SELFDOC_PUBLICATION_CONTRACT_V1.md`
- `docs/database/DATABASE_SAFETY_CONTRACT_V1.md`
- `docs/gui/OPEN_ARCH_GUI_PLAN_V1.md`
- `docs/gui/UNIFIED_GUI_CORE_V1.md`
- `docs/gui/GUI_THREADING_EVENT_MODEL_V1.md`
- `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`
- `docs/gui/WINDOWED_APP_CONTRACT_V1.md`
- `docs/gui/WX_FRONTEND_PLAN_V1.md`
- `docs/gui/PYTHON_FRONTEND_PLAN_V1.md`
- `src/cli/cmd_maint.cpp` `@dottalk.usage v1` block
- affected command usage blocks inspected in the source promotion set

Contract evidence states: active design/source contracts; `MAINT` usage is
source-defined and experimental/read-only.

Constraints that apply:

- development source remains authority;
- `MAINT AI` remains read-only;
- portal prose must not claim native runtime or autonomous AI behavior;
- publication must not outrun source and proof;
- HELP/DOTREF/message wording must agree;
- no GUI, database, threading, storage, or mutation semantics may change.

Proposed behavioral effect: replace stale onboarding output with correct paths
to the Alpha Python/registry AI Portal, SDLC seed, and source-contract gate.
The command continues to print information only.

Required source/test/HELP/metadata updates:

- update the three listed source/HELP files coherently;
- run `labtalk/ai_portal/probes/maint_ai_portal_readback_v1.dts`;
- inspect the generated/import message catalog seed as a residual drift item.

Proof plan:

1. compile staging `dottalkpp`;
2. run portal unit tests;
3. run the MAINT AI DotScript readback probe;
4. require begin/end markers, current portal paths, Alpha boundary, and no
   unknown-command output;
5. verify promoted hashes and staged Git scope.

Known contract drift or uncertainty: the historical
`SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv` row for `MAINT_USAGE_TEXT` already predates
the present compiled MAINT AI usage wording. It should not be silently treated
as the current message authority; classify or regenerate it through the
messaging lane rather than hand-editing an old import snapshot.

## Staging proof result

- selected current source-like paths: 2,950 shared, 2,950 exact matches
- `dottalkpp` Release build: passed after CMake glob regeneration
- portal output-acceptance unit tests: 7 passed
- compiled LMDB smoke test: 1 passed
- DotScript startup readiness: accepted, process return code 0
- MAINT AI Portal readback: accepted, process return code 0
- portal truth audit: 13 sections, 180 items, 32 runnable, 49 proof-like,
  5 known unrelated missing paths, 0 duplicate IDs

The staged runtime-layout executable was refreshed from the successful build
for proof only. It is ignored by Git and is not part of the source publication
set.
