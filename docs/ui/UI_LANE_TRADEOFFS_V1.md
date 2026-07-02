# DotTalk++ UI Lane Tradeoffs v1

Status: active architecture note.

## Summary

All UI lanes should share the same core model, but each exists because it has a
different strength. This document records where branching is useful and where it
would create unnecessary fragmentation.

## Shared Foundation

| Foundation | Applies To |
| --- | --- |
| Work areas and current area | CLI, TUI, Python GUI, C++ GUI |
| Structured table snapshots | TUI, Python GUI, C++ GUI, tests |
| Command compatibility lane | CLI, TUI, Python GUI, C++ GUI |
| Typed service lane | TUI, Python GUI, C++ GUI, automation |
| Task/progress events | TUI where possible, Python GUI, C++ GUI |
| Read-only-before-editing safety | All UI lanes |

## CLI

Advantages:

- fastest command entry,
- best for scripts, automation, regression runs, and remote terminals,
- simplest deployment and debugging surface,
- preserves FoxPro/DotTalk command muscle memory.

Disadvantages:

- weak spatial browsing,
- limited discoverability,
- hard to represent multiple simultaneous panes,
- long-running work can feel opaque without structured progress.

Best use:

- scripts, tests, batch work, expert command workflows, automation.

## Turbo Vision TUI

Advantages:

- works in terminal environments,
- supports keyboard-centric browsing and panels,
- can feel close to classic xBase tools,
- lighter than a desktop GUI while more visual than CLI.

Disadvantages:

- terminal rendering constraints,
- mouse/platform behavior can vary,
- dense layouts can become hard to inspect,
- fewer native desktop affordances.

Best use:

- terminal-first browsing, classic text UI workflows, low-dependency local tools.

## Python GUI

Advantages:

- fastest iteration for new UI workflows,
- easy scripting and inspection,
- good bridge to `pydottalk`,
- useful for internal tools, prototypes, data diagnostics, and workflow experiments.

Disadvantages:

- packaging can be less native,
- performance depends on binding/fallback choices,
- Tkinter visuals are functional rather than richly native,
- runtime dependency management differs from the C++ app.

Best use:

- exploratory GUI tools, operational utilities, rapid workflow validation, scripting-heavy users.

## C++ wxWidgets GUI

Advantages:

- native compiled desktop app,
- good Windows/POSIX/macOS portability,
- direct C++ runtime integration,
- conventional menus, dialogs, grids, status bars, and packaging path.

Disadvantages:

- slower iteration than Python,
- native toolkit dependency must be installed and packaged,
- threading rules must be enforced carefully,
- more compile/build friction.

Best use:

- primary desktop application, packaged user-facing workflows, native platform integration.

## Branching Guidance

| Feature | Preferred First Lane | Reason |
| --- | --- | --- |
| Runtime command compatibility | CLI | Existing command shell is canonical |
| Read-only table area model | C++ GUI core | Shared typed contract for GUI/TUI adapters |
| Visual workflow experiments | Python GUI | Faster iteration |
| Packaged desktop browse/edit | C++ wx GUI | Native app shape |
| Terminal browse/edit | TUI | Keyboard and terminal-friendly |
| Automation and regression | CLI/Python | Scriptability |

Features can graduate between lanes once the contract is stable.
