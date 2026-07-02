# DotTalk++ GUI Runtime Facade Plan v1

Status: planning.

## Purpose

The windowed GUI needs a stable application-service boundary between toolkit code and the existing runtime. This facade should let wxWidgets, Python/Tkinter, future Qt/FLTK frontends, tests, and automation drive DotTalk++ without depending on CLI globals, console capture, or toolkit-specific types.

The facade is not a new database engine. It is a narrow orchestration layer over the existing runtime.

The facade is also where GUI-visible database truth should be normalized:
encoding, dialect, locale, collation, safety status, index validity, and
read/write mode should cross this boundary as structured data.

## Facade Goals

- Open and close workspaces/tables.
- Expose read-only table snapshots for grids.
- Run commands and DotScript with structured results.
- Report progress, logs, warnings, errors, and cancellation.
- Keep raw mutable `DbArea` ownership inside the runtime/session.
- Avoid GUI toolkit types in public service contracts.
- Support both compiled C++ frontends and Python frontends through structured bindings.
- Carry value/locale/collation and safety context from the database contracts:
  - `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
  - `../database/DATABASE_SAFETY_CONTRACT_V1.md`

## Proposed Service Shape

```cpp
namespace dottalk::gui {

class RuntimeSession {
public:
    OpenTableResult open_table(OpenTableRequest request);
    OpenTableResult add_table(OpenTableRequest request);
    OpenWorkspaceResult open_workspace(OpenWorkspaceRequest request);
    CloseTableResult close_table(TableHandle table);
    TableSnapshot snapshot_table(TableSnapshotRequest request);
    CommandResult run_command(CommandRequest request);
    ScriptResult run_script(ScriptRequest request);
    WorkspaceSnapshot snapshot_workspace();
};

}
```

The existing `dottalk::gui::Session` skeleton in `include/gui/core/session.hpp` is the first placeholder for this boundary. It should evolve toward this service surface.

## Handles, Not Raw Pointers

GUI code should never hold raw `xbase::DbArea*`.

Use stable handles:

```cpp
struct TableHandle {
    std::uint64_t id;
};

struct WorkspaceHandle {
    std::uint64_t id;
};
```

The session owns any map from handles to runtime objects. A future implementation can map handles to:

- engine work area slots,
- standalone temporary `DbArea` instances,
- read-only snapshot caches,
- or backend-specific table adapters.

## Table Snapshot Contract

The GUI grid should consume immutable snapshots:

```cpp
struct TableSnapshot {
    TableHandle table;
    std::vector<TableColumn> columns;
    std::vector<TableRow> rows;
    std::uint64_t first_record;
    std::uint64_t total_records;
    bool truncated;
    std::vector<StatusMessage> messages;
};
```

Initial implementation can use the existing table/browse helpers:

- `include/browser/browser_snapshot.hpp`
- `include/browser/browser_builders.hpp`
- `src/browser/browser_builders.cpp`
- `src/cli/table_object.cpp`

The GUI should not render console output from `render_browser_snapshot_console`. It should use or adapt the structured snapshot data before formatting.

Current runtime note: `DbArea::open` opens the DBF using the existing runtime mode, not a separate OS-level read-only mode. The GUI facade must avoid mutations in its first implementation, but a true read-only open option should be added to the runtime before the windowed GUI is treated as safe for inspecting production data.

## Command Execution Contract

Command execution should be split into two lanes.

### Lane A: Native Service Calls

Prefer direct service calls for GUI workflows:

- open table,
- add table to current workspace,
- open/load workspace graph,
- browse table,
- seek/search,
- run import/export,
- validate,
- rebuild index,
- inspect metadata.

These can produce typed results without text parsing.

### Lane B: Compatibility Command Runner

Keep a command runner for users who type DotTalk++ commands. This is useful, but it should be treated as a compatibility lane until the command shell is made service-native.

Current implementation note: the first compatibility runner is process-based.
The command window accepts `cli <command>`, writes a short temporary `.dts`
script, and runs `dottalkpp --script <script>` when a CLI executable is
discoverable. This intentionally borrows the real DotTalk++ command surface
without linking GUI widgets to CLI globals. The runner discovers the executable
from `DOTTALKPP_GUI_CLI`, then `DOTTALKPP_EXE`, then common local build paths.
When an active GUI table is selected, the temporary script seeds the CLI session
with `USE <active-table> NOINDEX` before table-dependent commands.

Known risks:

- many commands depend on `shell_engine()`,
- many commands write through `OutputRouter`,
- DotScript uses transcript and stream-oriented output paths,
- command cancellation is not uniformly available.
- process-based execution has separate runtime session state from the GUI.

Useful existing surfaces:

- `src/cli/shell.cpp` owns the primary shell engine lifecycle.
- `src/cli/shell_commands.cpp` registers command handlers.
- `src/cli/output_router.cpp` centralizes much command output.
- `src/cli/shell_transcript.cpp` can capture command output, but it should not become the primary GUI data contract.

## Runtime Session Ownership

The GUI session should own or borrow runtime state explicitly.

Phase 2 should choose one of these options:

| Option | Description | Tradeoff |
| --- | --- | --- |
| Standalone GUI engine | GUI session creates its own `XBaseEngine` and work areas | Cleaner isolation, may require extracting shell setup |
| Shell-engine adapter | GUI session wraps the current `shell_engine()` model | Faster integration, more global-state risk |
| Hybrid | Direct services own tables; command compatibility temporarily uses shell globals | Pragmatic bridge, requires clear lifetime rules |

Recommended first implementation: hybrid. Use direct services for table snapshots and a limited command runner for typed command input.

Runtime naming rule: additive table opening and replacement workspace opening
must remain separate operations. CLI `WORKSPACE ADD <file.dbf>` preserves
existing areas; CLI `WORKSPACE OPEN ...` is replacement-style and resets area
membership before opening.

## Error Model

All facade calls should return structured status:

```cpp
struct StatusMessage {
    Severity severity;
    std::string code;
    std::string text;
    std::string detail;
};
```

The current skeleton has `severity` and `text`. Later phases should add stable `code` values so UI actions can branch without parsing English text.

Database-facing status codes should include locale/value and safety cases such
as unknown encoding, guessed encoding, stale index, incompatible collation,
locked table, invalid memo pointer, corrupt header, read-only mode, and unsafe
mutation request.

## Migration Sequence

1. Expand `include/gui/core/session.hpp` with handles, request IDs, and stable status codes.
2. Add a read-only `open_table` implementation using `xbase::DbArea` behind the session.
3. Add `snapshot_table` by translating `DbArea` fields and rows into `TableSnapshot`.
4. Add a basic command runner that captures output only for compatibility commands.
5. Promote high-value CLI commands into typed service methods.
6. Evaluate an in-process shell adapter only after shell engine lifetime,
   `OutputRouter` capture, cancellation, and mutation safety are explicitly
   owned by the GUI facade.
7. Add cancellation checks to long-running service paths.

## Acceptance Criteria For Phase 2

- `dottalk_gui_core` builds without wxWidgets.
- Opening a DBF through the facade produces a `TableHandle`.
- Opening multiple DBFs keeps multiple GUI areas alive.
- The facade supports list/select/close lifecycle operations for GUI areas.
- A read-only snapshot returns columns, rows, and total record count.
- Empty, invalid, locked, and missing-file cases return structured errors.
- No GUI toolkit headers appear in runtime/service headers.
- CLI behavior remains unchanged when GUI options are disabled.
