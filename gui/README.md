# gui/ -- the UI description layer

    status      : active
    project     : project.x64base.gui
    originating : AIF-120 (application-ui-dsl)
    owner       : member.derald   steward: member.ai.claude.cowork
    created_utc : 2026-08-20T02:00:00Z

## What this is

**UIDEF is a language, and this is where it lives.** A UIDEF document is a DBF
"design table" -- sixteen fields, three record kinds -- that describes a user
interface without naming a toolkit. Four backends read the same document and
produce four different frontends: Tk, HTML, character-cell, and wx C++.

The charter is narrow and worth restating: *give the existing GUI a language.*
The engine was already built. Nothing here re-derives engine behavior; it
describes an interface and calls the house's own surface to fill it.

## Why it is a top-level directory and not `tools/`

Two reasons, both from house doctrine rather than preference.

**It is a project, not a tool.** `AI_PORTAL.md`, *Projects, Lanes and Promotion*
(AIF-040): a lane is promoted when it "spawns sub-lanes, gains an independent
lifecycle, or becomes a program others build under." UIDEF has four backends, an
importer, a manifest gate, a lock provider, a runtime binding and its own fixture
corpus. `tools/` is where a program's helpers live; this is a program.

**The registry already places non-C++ products at the root.**
`labtalk/registries/projects.yaml` roots `project.pycrud` at `ccode/pycrud`,
`project.dottalk_webui` at `ccode/dottalk-webui`, and `project.sqlite_gui`
(`kind: gui_project`) at `ccode/sqlite-gui`. A non-C++ product living beside
`src/` and `include/` is the established pattern, not a new one. "ccode implies
C++" is already not how this tree is organized.

## What is here

    gui/
      README.md          this file
      uidef/             the language: readers, backends, importers, gates,
                         fixtures, and the C++ the wx backend needs

`uidef/` is deliberately FLAT. Its 33 Python modules import each other by bare
name off a single `sys.path.insert`; foldering them into `backends/`, `import/`
and `author/` would break every one of those imports for a cosmetic gain. If that
restructuring is ever wanted it is its own unit with its own proof, not a rider
on a move.

## What is NOT here, and why

`src/gui/core`, `src/gui/wx` and `include/gui/core` are the **shipped C++ GUI
application** (targets `dottalk_wx`, `dottalk_wx_next`). They stay where the build
expects them. `src/CMakeLists.txt` already excludes that subtree from globbing --
`"${CMAKE_CURRENT_SOURCE_DIR}/gui"   # GUI isolated, not globbed` -- so the build
has its own view of GUI isolation and this directory does not disturb it.

**The two are different things wearing one word.** `src/gui` is an application.
`gui/uidef` is a language that generates applications. They are related the way a
compiler is related to a program.

> **Known cost, recorded rather than hidden:** `gui/` and `src/gui/` now both
> exist. Any sentence saying "the gui directory" is ambiguous until one of them
> moves. Consolidating `src/gui` under here is a legitimate later unit and would
> touch `src/CMakeLists.txt` lines 117, 450 and 454; it was deliberately NOT
> bundled with this move, because a directory move and a build-graph change fail
> in different ways and should not fail together.

Also elsewhere on purpose:

- `tools/gui/generate_gui_messages.py` -- generates `include/gui/core/generated_gui_messages.hpp`. It is a build-time code generator for the C++ app, so it stays with the tools that serve the build.
- `tools/gui_preview/` -- a Python mirror of `src/gui/core` used to preview the shipped app. It belongs to that app, not to UIDEF.
- `bindings/pydottalk` -- the Python binding to the engine. A different product with its own charter; UIDEF does not depend on it.
- `docs/maintenance/AIF120_*.md` -- the rulings stay in the lane ledger with every other lane's rulings. Moving them would break the ledger's index, which is the only index they have.

## Start here

| To | Read |
| --- | --- |
| understand the format | `docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md` |
| see every ruling | `docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md` (the only index) |
| generate a frontend | `uidef/uidef_tk.py`, `uidef_html.py`, `uidef_text.py`, `uidef_wx.py` |
| check a document | `uidef/manifest.py` |
| bind a grid to live records | `uidef/uidef_wx.py --stream`, and `docs/maintenance/AIF120_GRID_STREAM_BINDING_V1.md` |

## Evidence state

The wx backend is the only one proven `runtime-proven` against the engine: R70
built a generated window, linked 44 house translation units, and filled a grid
from `DbTupleStream` off the shipped x64 tables. Tk, HTML and character-cell are
`runtime-proven` as renderers and have no data binding yet.
