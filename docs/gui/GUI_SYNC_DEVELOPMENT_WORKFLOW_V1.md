# DotTalk++ GUI Sync Development Workflow v1

Status: active workflow doctrine.

## Purpose

DotTalk++ now has three visible UI lanes:

- C++ wxWidgets workbench,
- Python/Tkinter workbench,
- TurboTalk/FoxTalk TUI.

This document defines how those lanes stay synchronized while they mature at
different speeds. The goal is not identical screens. The goal is one database
truth, one shared GUI/core contract vocabulary, and repeatable promotion from
prototype to production-facing behavior.

## Home In The Documentation System

GUI synchronization belongs in two places:

- `docs/gui`: GUI architecture, frontend contracts, runtime facade, and sync
  workflow.
- `docs/ui`: cross-UI principles shared by CLI, TUI, Python GUI, and C++ GUI.

The maintenance map should list GUI as a SelfDoc/maintenance subsystem because
GUI work now has durable contracts, smoke expectations, and workflow gates.
Messaging and locale remain owned by the messaging/locale lane; GUI consumes
that lane instead of growing a separate language system.

## Core Rule

The GUI lanes are parallel presentations over DotTalk++ and x64base, not
parallel database implementations.

Database behavior is owned by:

- x64base table, memo, index, lock, value, and cursor code,
- DotTalk++ command, script, shell, workspace, relation, variable, loop, and
  message/runtime code,
- shared GUI core contracts where a typed application-service boundary exists.

Frontend code owns:

- layout,
- widgets,
- menu shape,
- keyboard and mouse gestures,
- dialogs,
- status/log rendering,
- toolkit-specific event loop delivery.

## Current Lane Roles

| Lane | Current role | Long-term role |
| --- | --- | --- |
| wxWidgets C++ | Primary native windowed workbench | Packaged desktop GUI over shared runtime services |
| Python/Tkinter | Fast mirror/prototype and inspection lane | First-class scripted GUI and binding proof surface |
| TurboTalk/FoxTalk TUI | Command taxonomy and shell-bridge reference | Terminal UI where the medium is a real advantage |

The TUI is less important for rich workbench features, but it remains valuable
for keyboard behavior, command taxonomy, and shell/session lessons. wx and
Python should not copy Turbo Vision widget code. They should borrow concepts
and route database work through the same runtime contracts.

## Synchronization Model

Every GUI-facing feature should be classified before implementation:

| Class | Meaning | Required sync action |
| --- | --- | --- |
| Core contract | Shared meaning across lanes | Add/extend GUI core model or documented Python mirror first |
| Frontend rendering | Toolkit-specific display | Implement independently in each lane where useful |
| Compatibility bridge | Runtime command/script path | Prefer DotTalk++ shell/CLI behavior; do not invent semantics |
| Skeleton | Visible placeholder for planned service | Mark as pending and keep behavior harmless |
| Runtime change | x64base/DotTalk++ behavior change | Review separately before GUI code depends on it |

When one lane gains a new concept, name the concept in a shared document or
shared model before implementing it differently in another lane.

## Required Shared Concepts

These concepts must remain aligned:

- workspace,
- area,
- active area,
- current record,
- table snapshot,
- record view,
- structure,
- indexes/orders/tags,
- relations,
- command lane,
- status messages,
- task state,
- language/message locale,
- display/parse locale,
- safety/read-only/edit state.

The rendering can differ. The meaning cannot.

## Sync Checklist For Each GUI Slice

Before or during a GUI change, answer:

1. Which runtime truth owns the behavior?
2. Is there already a typed GUI core request/result/event for it?
3. Does Python need a mirror contract now, or can it remain a documented gap?
4. Does wx need native desktop behavior beyond the shared contract?
5. Does the TUI already have a command/menu/shell concept worth borrowing?
6. Are status/error strings message-keyed or hard-coded?
7. What smoke test proves the lanes stayed aligned?

## Staged Implementation Pattern

Use this pattern when a feature is too large to finish in all lanes at once:

1. Define the shared concept and ownership boundary.
2. Implement the smallest typed contract or documented compatibility bridge.
3. Make one lane visible first, usually wx for workbench UX or Python for fast
   experiments.
4. Mirror the concept in the second GUI lane before it drifts.
5. Decide whether the TUI should align, document as intentionally deferred, or
   remain command-only.
6. Add a smoke proof that exercises the shared contract, not only the toolkit.
7. Promote the contract into the maintained docs and keep the skeleton wording
   honest until native runtime service work catches up.

## Parallel Implementation Pattern

Use parallel implementation only when the shared contract is already clear.

Examples:

- language menu behavior after message keys exist,
- record view rendering after `TableSnapshot` and cursor movement exist,
- workspace tabs after `WorkspaceModel` exists,
- command catalog menus after command category data exists.

Avoid parallel implementation when the runtime behavior is still unclear. In
that case, implement one lane as a visible probe, document it as a probe, and
promote the shared contract after the behavior is understood.

## Cursor And State Rule

Cursor movement is a sync-sensitive feature.

Keyboard navigation, mouse row selection, command-line movement, record view
navigation, and relation/browser traversal must converge on the same runtime
cursor state. A frontend may cache selection for display, but after movement it
must refresh from the shared session/runtime snapshot.

No frontend should keep a private database cursor that can disagree with
DotTalk++ or x64base.

## Messaging And Language Rule

GUI text must use the DotTalk++ message/locale direction, not a parallel
language system.

Current implementation state:

- GUI message seeds live in `dottalkpp/data/messaging/gui_messages.csv`.
- C++ consumes generated text through `include/gui/core/generated_gui_messages.hpp`
  and `src/gui/core/localization.cpp`.
- Python consumes the generated mirror under `tools/gui_preview`.
- wx and Tk already use stable GUI text keys for much of the chrome/status
  surface.

Current limitation:

- GUI message seeds are not yet fully backed by the same physical runtime DBF
  catalog used by the broader messaging/locale lane.

Policy:

- Keep stable GUI message keys.
- Keep fallback English text for transitional rendering and debugging.
- Do not create a second unrelated translation catalog.
- Promote GUI message rows into the full messaging/locale catalog when the
  runtime catalog path is ready for GUI consumers.

## Workflow Integration

GUI work should participate in the normal development cycle:

1. Plan or name the shared contract.
2. Implement in the lane that best exposes the issue.
3. Mirror or defer explicitly in the other GUI lane.
4. Check the TUI for reusable command/menu/session concepts.
5. Run focused smoke tests.
6. Update `docs/gui` or `docs/ui` when the contract changes.
7. Record durable gaps as skeletons, not hidden assumptions.

This keeps chat decisions from evaporating and prevents wx, Python, and TUI
from becoming three unrelated applications.

## Near-Term GUI Sync Backlog

Highest-value sync targets:

- cursor/key navigation across browse and record view,
- workspace open/load/close parity,
- index/order/tag visibility and activation,
- relation graph/list visibility,
- command shell bridge and alias behavior,
- message/locale source promotion,
- dynamic record view parity,
- startup/shutdown/init script policy,
- read-only/edit safety boundary.

## Acceptance Checks

A GUI sync pass should prove:

- wx builds,
- Python GUI backend or mirror smoke passes,
- a changed shared concept is documented,
- no new database behavior was implemented only in widget code,
- message-facing strings use stable keys where practical,
- active area and cursor state stay stable across mouse, keyboard, and command
  movement,
- workspace/index/relation state remains visible after command/script actions.
