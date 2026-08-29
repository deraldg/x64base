# DotTalk++ GUI Threading and Event Model v1

Status: shared policy with per-frontend adapters started.

## Purpose

The windowed GUI must remain responsive while DotTalk++ opens files, scans tables, runs DotScript, rebuilds indexes, imports data, and generates reports. The design uses one UI thread plus worker threads, with explicit immutable events between them.

## Core Rule

Only the GUI thread may touch widgets.

Worker threads may use runtime services, produce immutable results, and post events back to the GUI adapter. They must not call wxWidgets controls, dialogs, grids, or frame methods directly.

Share threading policy; branch event delivery. The task lifecycle, event names,
area identity, cancellation/progress/status model, and runtime ownership rules
should be common across UI lanes. The final handoff into each UI loop remains
frontend-specific:

| UI lane | Delivery adapter |
| --- | --- |
| C++ wxWidgets | `wxQueueEvent` into the wx event loop |
| Python/Tkinter | `queue.Queue` drained by `after(...)` |
| Turbo Vision TUI | poll/drain from the TUI event loop tick |
| CLI | synchronous command execution or explicit task monitor output |

## Thread Roles

| Thread | Owns | Allowed work |
| --- | --- | --- |
| UI thread | wx application, frames, menus, dialogs, grids | Paint UI, handle user events, dispatch service requests, apply completed results |
| Worker thread | Runtime task execution | Open/read tables, run scripts, build snapshots, import/export, metadata scans |
| Optional scheduler thread | Task queue | Dispatch queued work, coalesce progress, manage cancellation |

## Event Contract

Events should be value types that can cross threads safely. The initial code contract lives in:

- `include/gui/core/events.hpp`
- `include/gui/core/async_session.hpp`
- `src/gui/core/async_session.cpp`

`AsyncSession` owns one runtime `Session` on a worker thread and serializes submitted work. This keeps the first implementation conservative while preserving the later option to add multiple read-only workers after the xbase/index concurrency rules are proven. Python mirrors the same semantics in `tools/gui_preview/dottalk_gui_async.py` while using Python's queue/thread primitives and Tkinter's `after(...)` delivery.

```cpp
enum class GuiEventKind {
    task_started,
    progress,
    log_line,
    table_snapshot_ready,
    command_finished,
    error,
    task_cancelled
};

struct GuiEvent {
    GuiEventKind kind;
    TaskId task_id;
    std::string label_code;
    std::string label;
    std::vector<StatusMessage> messages;
};
```

Large payloads, such as table snapshots, should move through `std::shared_ptr<const T>` or an equivalent immutable owner.

`label_code` is the stable localization key. `label` is transitional fallback
text. Frontends should render through the GUI message resolver described in
`GUI_LOCALIZATION_MESSAGE_CONTRACT_V1.md`.

## Task Lifecycle

```text
queued
  -> running
  -> completed
  -> failed
  -> cancelled
```

Cancellation is cooperative. A worker checks a token:

- before opening a file,
- between record batches,
- between DotScript commands where possible,
- before publishing large results,
- before starting expensive secondary work.

## Event Flow

```text
User clicks Open
  UI thread creates OpenTableRequest
  UI thread enqueues task
  Worker opens table
  Worker posts TaskStarted
  Worker posts Progress
  Worker builds TableSnapshot
  Worker posts TableSnapshotReady
  UI thread applies snapshot to grid
```

## Progress Strategy

Progress must be structured and optional.

For known-size work:

- `fraction = completed / total`
- label describes the current phase.

For unknown-size work:

- no fraction,
- periodic `LogLine` or phase changes.

Avoid updating the UI for every row. Batch progress updates by count or time.

Recommended initial batching:

- table scans: every 500 records or 100 ms,
- import/export: every 1000 records or 100 ms,
- DotScript: after each command,
- index rebuild: per phase plus periodic count.

## Runtime Locking Policy

Runtime state must have clear ownership.

Initial rule:

- One `RuntimeSession` is owned by one GUI document/workspace.
- Only one mutating task may run per session at a time.
- Multiple read-only snapshot tasks are allowed only after `DbArea` and index access are proven safe for concurrent reads.

Conservative first version:

- serialize all tasks per session,
- allow the UI to queue tasks,
- allow cancellation before a queued task starts.

## Output Handling

Text output remains useful but should not be the primary GUI data path.

Use structured events for:

- task completion,
- table snapshots,
- errors,
- progress,
- validation results.

Use log lines for:

- command compatibility output,
- diagnostics,
- transcript view,
- developer details.

Existing `OutputRouter` and `ScopedShellTranscript` can help bridge command compatibility, but they should not leak into GUI widgets directly.

## Failure Handling

Workers must catch exceptions at the task boundary and convert them into structured errors.

The UI should receive:

- short message for status bar/dialog,
- detailed message for log panel,
- task ID,
- optional source path or command text,
- retry/cancel affordance if appropriate.

## Testing Plan

Phase 2 tests should not require a real GUI toolkit.

Test the GUI core with:

- fake event sink,
- fake cancellation token,
- empty command,
- missing table path,
- queued task cancellation,
- simple table snapshot once runtime open is wired.

The first toolkit-free smoke is `dottalk_gui_core_async_smoke`. It verifies that
`AsyncSession` publishes command, progress, snapshot warning, and pending
cancel events without linking wxWidgets or creating a native window.

Phase 3 wx tests can stay smoke-level:

- app object starts,
- main frame creates,
- fake event updates log panel,
- fake table snapshot populates grid model.

Python GUI tests should stay headless where possible:

- backend area lifecycle smoke,
- async event lifecycle smoke,
- import/syntax checks without opening a Tk window.
