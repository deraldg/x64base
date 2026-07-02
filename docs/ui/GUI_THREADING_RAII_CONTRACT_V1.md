# DotTalk++ GUI Threading and RAII Contract v1

Status: active architecture principle.

## Purpose

Windowed GUI work must stay responsive without forking database behavior away
from DotTalk++ and x64base. This contract defines the threading boundary for
the C++ wxWidgets GUI, the Python GUI lane, and any future windowed surface.

The rule is conservative by design: UI toolkits own their event loops, while
DotTalk++ workspace/session state remains serialized unless the underlying
runtime has an explicit thread-safe contract.

## Source Boundary

The active source repository for this lane is:

```text
D:\code\ccode
```

GUI lane work may change GUI core, wx, Python preview, and UI documentation.
Changes to DotTalk++ or x64base database/runtime behavior require an explicit
review note first, including the reason, expected surface area, and test plan.

## Thread Ownership

| Lane | Ownership |
| --- | --- |
| GUI main thread | Owns all widgets, menus, windows, dialogs, grids, and visual updates |
| Workspace executor | Runs serialized DotTalk++ GUI session commands and command bridge calls |
| Snapshot workers | May build immutable read models when safe; must not mutate workspace state |
| Event sink | Delivers immutable results back to the GUI main thread |

No worker thread may directly touch wxWidgets controls, Tkinter widgets, or TUI
screen objects. Workers produce values; UI threads render values.

## Serialization Rule

One workspace/session has one mutation lane.

Commands that may affect area selection, current record, order state, filters,
relations, variables, loops, locks, dirty state, or shell/session state must be
serialized through the workspace executor.

This includes:

- `USE`, `SELECT`, `AREA`, `DBAREA`
- `GOTO`, `SKIP`, `TOP`, `BOTTOM`
- `SET INDEX`, `SET ORDER`, `ASCEND`, `DESCEND`
- `REL`, `WORKSPACE`, `DOTSCRIPT`
- loops, variables, scans, locks, triggers, and polling hooks

Read-only GUI snapshots may be concurrent only after they are based on a stable
copy or an explicitly guarded runtime read.

## RAII Requirements

C++ GUI/threading code must prefer RAII guards and owned lifetimes:

- `std::unique_ptr` for private implementation ownership.
- `std::lock_guard` or `std::unique_lock` for mutex scopes.
- Worker threads joined or stopped from destructors.
- Queued work cancelled or drained in a predictable shutdown path.
- No raw owning pointers for thread, session, lock, or runtime resources.
- No manual lock/unlock pairs when a standard guard can express the scope.
- No detached worker thread that can outlive its session or event sink.

The current `AsyncSession` shape follows this direction: the implementation owns
the worker thread, guards the queue with a mutex, signals shutdown in the
destructor, wakes the worker, and joins before the session is destroyed.

## Event Contract

Worker results must be immutable or treated as immutable after publication.

Preferred event payloads:

- `WorkspaceModel`
- `TableSnapshot`
- `CommandResult`
- `ListAreasResult`
- `StatusMessage`
- task progress records

The UI may cache these values for display, but it must not treat them as direct
handles to mutable x64base runtime state.

## Toolkit Rules

### wxWidgets

- All `wxWindow`, `wxGrid`, `wxMenu`, `wxDialog`, and status bar updates happen
  on the wx main thread.
- Background work posts events with copied/shared immutable payloads.
- The app must tolerate command completion order through task ids and explicit
  active area ids.

### Python Tk

- Tk widgets are updated only on the Tk main loop.
- Worker output returns through a queue and `after()` polling or equivalent
  main-loop callback.
- Python preview must follow the same workspace/session model as the C++ GUI.

### TUI

- The TUI may stay single-event-loop unless a specific operation needs a worker.
- If workers are added, terminal rendering remains owned by the TUI event loop.
- TUI concepts should align with `WorkspaceModel`, snapshots, command results,
  and status messages.

## Anti-Patterns

Avoid these unless a later contract explicitly allows them:

- thread per window,
- direct widget access from workers,
- parallel mutable commands against the same workspace,
- GUI-specific database cursor state separate from x64base/DotTalk++ state,
- detached command bridge processes for ordinary persistent-session commands,
- long-running UI-thread command execution,
- parsing console text as the only contract for new native GUI features.

Console parsing is acceptable as a compatibility bridge while the shared runtime
API is being extracted. It should be replaced by typed runtime APIs where the
core already exposes stable state.

## Acceptance Checks

A GUI threading change should prove:

- the app remains responsive during a command,
- closing the app joins/stops workers cleanly,
- no widget is touched from a worker thread,
- queued work does not outlive the session,
- active area and record cursor remain stable after command completion,
- relation/index/workspace state still reflects DotTalk++ runtime output,
- tests or smoke runs cover the changed lane.
