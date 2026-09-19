# AIF-120 Workbench: native catalog inspection

Status: first slice implemented and locally tested; review-needed, uncommitted.
Owner authorization: 2026-09-17, "I want a workbench that reflects that ...
I am giving you the job - begin".
Run: CODEX-20260917-UIDEF-WORKBENCH.
Report/run registry identity: AIPR-20260917-001.
Baseline: development, 6123842098f8e4d9cc3f8010865709cce899730f.

## Scope calibration

```text
id: AIF-120 / AIPR-20260917-001
title: Generated native Workbench catalog inspection
area: gui/uidef
owning_lifecycle: DotTalk++ SDLC and frontend PDLC
sdlc_lane: review
operating_mode: production
change_class: C2
build_target: frontend
product_profile: not_applicable
index_profile: NONE
scope_reason: native generated frontend, isolated from the CLI assembly
affected_authorities: UIDEF generation, standalone CMake, catalog read model
truth_state: dev
proof_state: locally observed; registry promotion awaits versioned artifacts
risk_class: bounded read-only frontend; readers use owned copies
source_path: gui/uidef
website_path: not_applicable
minimum_gate_set: native build, reader fixtures, actual catalog, UI and shutdown
optional_educational_gates: none
deferred_gates_and_residual_risk: live session, hydration, editing and nested memo expansion
next_gate: owner review of first slice; single-session live workspace service
owner: member.derald
status: review-needed
```

## Source mutation preflight

- Targets: gui/uidef/CMakeLists.txt; new author_workbench.py,
  workbench_catalog.hpp/.cpp, wx_workbench.cpp, workbench_catalog_test.cpp,
  and build_workbench.py under gui/uidef. The native visual check found that
  uidef_wx.py's data-frame branch discarded the existing Weight/Fill/Span
  properties. The scope includes honoring those declared properties there;
  no vocabulary change, engine change, or sample retirement.
  Delivery also includes verify_workbench.py, WORKBENCH.md and the gui/README
  entry point, plus session-owned evidence and registry fragments.
- Subsystem: generated native frontend and toolkit-neutral read model.
- Contracts read: docs/contracts README, registry and lifecycle;
  docs/ui/CORE_UI_PRINCIPLES_V1.md and GUI_THREADING_RAII_CONTRACT_V1.md;
  docs/gui OPEN_ARCH_GUI_PLAN, UNIFIED_GUI_CORE, GUI_THREADING_EVENT_MODEL,
  GUI_LOCALIZATION_MESSAGE_CONTRACT, WINDOWED_APP_CONTRACT,
  WORKSPACE_GRAPH_CONTRACT and WX_FRONTEND_PLAN;
  docs/database DATABASE_SAFETY_CONTRACT and VALUE_LOCALE_COLLATION_CONTRACT;
  AIF120_DESIGN_TABLE_CONTRACT_V1.md and AIF120_HOST_CONTRACT_V1.md.
- Evidence states: shared GUI contracts are design/skeleton boundaries;
  UIDEF has historical Linux runtime proof. Native Windows proof is required
  here, not inferred from it.
- Constraints: DBF-authored layout; existing dispatch host seam; serialized
  reads off the UI thread; immutable results; RAII shutdown; no database edits.
  The original wx/C++ and Python samples remain independent.
- Behavioral effect: inspect saved catalog records, parent identity and saved
  versions; inspect MINIDB members and RAM versus disk sidecar byte totals
  using the engine scanner. Saved catalog records are not live workspaces.
- Data access: copy the selected catalog family into private temporary storage
  before using existing engine readers, whose open APIs are write-capable.
  No parser or memo format is reimplemented by widgets.
- Source/test/docs: separate executable and focused native reader/lifecycle
  checks, documented build and launch. No CLI syntax, HELP, or live metadata
  changes in this slice.
- Proof: MSVC configure/build; native tests against disposable data; unchanged
  live catalog hashes around read-only inspection; actual generated window
  startup and teardown. No full CLI regression needed unless engine code changes.
- Known drift: WORKSPACE_GRAPH_CONTRACT describes OPEN/LOAD as replacement;
  current runtime is additive. This slice invokes neither. The wx frontend plan
  predates the owner's sample/product distinction. UIDEF captions have no
  implemented portable message-reference syntax; host-rendered wording will use
  stable keys with the shared locale resolver and English fallbacks.

## Development sequence

1. Native build and saved-catalog/MINIDB inspection.
2. One in-process engine session, live workspace/area tree, and command service.
3. Guarded hydration and safe workspace close, with isolated runtime proofs.
4. Explicit edit, dirty state, commit/revert, and writeback preview.

Only the first item is the current implementation slice. The remaining items
describe subsequent work, not capabilities of the first executable.

## Result and evidence

- Built `arctictalk_workbench.exe`, `uidef_catalog_test.exe` and the existing
  `uidef_wx_demo.exe` with MSVC 19.44 and wxWidgets 3.3.1 on Windows.
- The baseline standalone build failed first on Windows min/max macros, then
  on two missing closure units: sqlsel/mode.cpp and cli/group_log.cpp. Restoring
  the root Windows definitions and naming these existing units fixed the build.
- Native fixture checks cover durable parent versus version history, retained
  versus deleted rows, MINIDB parsing and RAM/disk totals, truncated payloads,
  cycle termination, byte preservation, cancellation and missing/invalid input.
- The actual catalog yielded 134 retained / 148 deleted records, seven readable
  MINIDB images and zero payload errors. These are measured 2026-09-17 facts,
  not invariants.
- Native UI verification exercised filtering, history and a selected MINIDB;
  its read-only member grid contained 24 files. Close during read requested
  cancellation and joined the worker before window teardown.
- Both actual catalog files retained their SHA-256 hashes. The verifier records
  them and the built executable hash in the transcript.
- The first screenshot exposed the dropped Weight/Fill properties: a grid stayed
  at its small default size. The corrected generated grid measured 774 x 538.
  All 20 existing author_cases fixtures, in four dispatch/stream combinations,
  generated byte-identical output to the baseline after this fix (80 checks).
- Screenshot capture initially failed in the sandbox, and a hidden desktop
  subsequently returned a black image despite a successful blit. The verifier
  now rejects black captures. The final screenshot was visually inspected.

Evidence (local, uncommitted):

- [native transcript](evidence/AIF120_workbench_20260917.txt)
- [native window](evidence/AIF120_workbench_20260917.png)
- [operator guide](../../gui/uidef/WORKBENCH.md)

Contracts are preserved: DBF-authored layout, unchanged vocabulary, source-owned
MINIDB interpretation, worker-only reads, immutable UI snapshots and explicit
read-only state. The generator fix implements already-declared layout intent.
No CLI HELP, command metadata, website, publication staging or sample program
changed. No commit, staging or push was performed. The broader Workbench is
still in development; this report does not close AIF-120.

Known gaps: no live engine session/commands, no hydration, no edit/writeback,
no nested DTX payload expansion, no splitter lifecycle change, and new UI text
uses English fallbacks where the shared catalog has no translation. Linux/macOS
builds were not run. Catalog snapshot copying does not promise atomicity with a
concurrent writer. The pre-existing workspace-contract drift noted above remains.

RE: AIF-120 steward -- owner commissioned this generated Workbench slice on
2026-09-17. Changes are confined to the generated frontend, standalone build,
docs and session-owned evidence/registry fragments. Verify with
`gui/uidef/verify_workbench.py`; undo only the named new files and exact CMake,
generator and README hunks. Preserve the pre-existing peer-review handoff and
all other dirty work.
