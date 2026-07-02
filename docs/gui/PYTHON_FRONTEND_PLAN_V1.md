# DotTalk++ Python GUI Frontend Plan v1

Status: first-class frontend lane started.

## Purpose

The DotTalk++ GUI architecture should stay open-ended. A Python desktop GUI is a
valid first-class frontend alongside the compiled C++ wxWidgets frontend.

The Python lane must mirror the same windowed and database contracts as the C++
lane:

- `WINDOWED_APP_CONTRACT_V1.md`
- `WORKSPACE_GRAPH_CONTRACT_V1.md`
- `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `../database/DATABASE_SAFETY_CONTRACT_V1.md`

Python is useful for:

- fast iteration on layout and workflows,
- operational tools that favor scripting and inspection,
- embedding DotTalk++ table access through `pydottalk`,
- proving GUI workflows before hardening them in C++.

## Product Shape

The current Python GUI lives at:

- `tools/gui_preview/dottalk_gui_preview.py`

This should evolve from preview harness into a maintained Python frontend lane.
The current implementation opens a real desktop window using Tkinter, loads DBF
tables on a worker thread, and displays a table grid, log panel, and status bar.
It also exposes a read-only Workspace Graph tab that summarizes the current
areas while the graph load/save service remains pending.

## Runtime Boundary

Preferred backend order:

1. `pydottalk` binding over the C++ runtime.
2. Pure-Python read-only DBF preview fallback for visibility and bootstrap.

The fallback is intentionally read-only and narrow. It keeps the GUI visible when
the binding is not built, but product behavior should migrate toward `pydottalk`
or another structured runtime service API.

## Relationship To C++ GUI

The Python GUI and C++ wxWidgets GUI are peers, not replacements for each other.
Both should follow the shared principles in `docs/ui/CORE_UI_PRINCIPLES_V1.md`
and branch only where their UI medium has a real advantage.

| Frontend | Strength |
| --- | --- |
| Python/Tkinter | fast iteration, scripting, lightweight distribution for internal tools |
| C++/wxWidgets | native compiled desktop app, direct C++ integration, production packaging |

Both should consume structured runtime contracts. Neither should scrape console
text as its primary data path.

Workspace files follow the same rule. Python widgets must not become an ad hoc
`.dtschema`, `.dtschemas`, or `.erz` parser. The Python lane may prototype graph
inspection, but durable load/save behavior belongs behind a shared workspace
graph service.

Both should also keep UI language, display locale, parse locale, table encoding,
collation, and database safety state as explicit concepts rather than toolkit
local details.

Both should render task labels and status text through stable GUI message keys.
Python mirrors the C++ resolver in `tools/gui_preview/dottalk_gui_text.py`.

## Near-Term Work

- Keep the Python GUI read-only until runtime write safety is explicit.
- Keep `dottalk_gui_backend.py` as the table/session backend module so Tkinter
  widgets do not own table access logic.
- Keep `test_gui_backend.py` as the headless backend smoke.
- Keep Python area session behavior aligned with GUI core: open, select, close,
  and preserve remaining areas when one area closes.
- Add optional `pydottalk` discovery through `PYDOTTALK_BIN` and known build dirs.
- Keep the visible layout aligned with the C++ wx skeleton.
- Keep the bootstrap Workspace load/save menu aligned with the wx lane while
  full graph load/save remains service-backed future work.
- Keep the read-only Workspace Graph tab aligned with the wx lane and fed from
  session/area state, not widget-owned database state.
- Prototype locale, encoding, collation, and safety inspectors quickly in
  Python, then promote stable concepts back into the shared GUI/core contracts.
