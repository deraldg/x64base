# DotTalk++ Unified GUI Core v1

Status: active skeleton.

## Purpose

The open architecture GUI work should build on one unified core contract. C++ wx,
Python/Tkinter, future TUI adapters, and tests should share the same concepts and
event names even when their event-loop delivery mechanisms differ.

The GUI program is allowed to mature top-down while the database runtime remains
bottom-up and authoritative. In practice, this means wx and Python can present
the workbench shell early, but any database behavior must come from one of three
places: the shared GUI core, the DotTalk++ CLI/script bridge, or an explicit
skeleton marked as pending runtime service work.

This core also needs to carry database truth without becoming a GUI toolkit. In
particular, it should expose value, locale, collation, index, and safety status
from the database contracts:

- `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `../database/DATABASE_SAFETY_CONTRACT_V1.md`
- `WINDOWED_APP_CONTRACT_V1.md`

## C++ Core Shape

| File | Role |
| --- | --- |
| `include/gui/core/model.hpp` | Toolkit-neutral value model: areas, tasks, status, commands, snapshots |
| `include/gui/core/events.hpp` | Toolkit-neutral event payloads |
| `include/gui/core/localization.hpp` | Toolkit-neutral GUI locale context and message resolver |
| `include/gui/core/session.hpp` | Runtime facade over xbase/memo/xindex |
| `include/gui/core/async_session.hpp` | Serialized worker/task facade |
| `src/gui/core/localization.cpp` | Seed GUI message catalog and rendering helpers |
| `src/gui/core/session.cpp` | Runtime-backed area and snapshot implementation |
| `src/gui/core/async_session.cpp` | Shared C++ task queue and event publication |

Toolkits must depend on these contracts rather than owning runtime state.

## Python Mirror

| File | Role |
| --- | --- |
| `tools/gui_preview/gui_contract.py` | Python mirror of shared task/event/lifecycle names |
| `tools/gui_preview/dottalk_gui_text.py` | Python mirror of GUI locale context and text resolution |
| `tools/gui_preview/dottalk_gui_backend.py` | Python area/session backend with pydottalk-first fallback |
| `tools/gui_preview/dottalk_gui_async.py` | Python async/session layer mirroring C++ task events |
| `tools/gui_preview/dottalk_gui_preview.py` | Tkinter adapter and renderer |

Python remains a first-class UI lane, but its contract names must stay aligned
with the C++ model.

## Shared Contract

Task states:

- `queued`
- `running`
- `completed`
- `cancelled`
- `failed`

Event kinds:

- `task_progress`
- `open_table_finished`
- `area_selected`
- `area_closed`
- `areas_listed`
- `table_snapshot_ready`
- `command_finished`
- `log_line`

Area lifecycle:

- open
- list
- select
- refresh
- close

Database context that should become shared, not per-toolkit:

- table dialect,
- table encoding/code page,
- display locale,
- input parse locale,
- collation profile,
- index validity state,
- read-only/edit mode,
- safety warnings with stable status codes.

Message context that should stay shared:

- `message_locale`,
- `display_locale`,
- `parse_locale`,
- `region_id`,
- stable task `label_code`,
- stable `StatusMessage.code`,
- fallback text for transitional/debug rendering.

See `GUI_LOCALIZATION_MESSAGE_CONTRACT_V1.md`.

## Adapter Boundary

Each frontend owns only final delivery and rendering:

- wxWidgets posts `GuiEvent` through `wxQueueEvent`.
- Tkinter drains Python `GuiEvent` objects from `queue.Queue` with `after(...)`.
- TUI should drain the same logical events from its event loop tick.
- CLI can remain synchronous or expose a task monitor.

No frontend should reach directly into `xbase::DbArea` unless it is implementing
the unified core/facade itself.

## Orthogonal Frontend Rule

The frontends are orthogonal presentations, not independent database products.

- wx owns native desktop interaction, menus, grids, dialogs, packaging, and OS
  integration.
- Python owns fast iteration, scripted inspection, and binding experiments.
- TUI owns keyboard-heavy terminal workflows.
- CLI owns canonical command/script behavior and exact transcripts.

When one lane gains a concept, the concept should be named in the shared core
contract before another lane reimplements it. The rendering can differ; the
meaning should not.
