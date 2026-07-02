# DotTalk++ TUI Alignment Plan v1

Status: planning alignment note.

## Purpose

The Turbo Vision/TUI lane should remain a first-class UI surface and should
share the same core UI principles as the Python and C++ GUI lanes.

The TUI does not need to mimic desktop windows. It should express the same
runtime concepts in a terminal-native form.

## Shared Concepts To Preserve

- Visible work areas and current area.
- Read-only table snapshot before editing.
- Command input lane.
- Output/log/status lane.
- Explicit task/progress state where terminal rendering allows it.
- Structured service calls instead of direct widget access to runtime internals.

## TUI-Specific Advantages

- Keyboard-first operation.
- Terminal/SSH-friendly workflows.
- Classic xBase text UI feel.
- Lower deployment friction than native desktop GUI.
- Good fit for browse/edit workflows that do not need rich graphics.

## TUI-Specific Constraints

- Limited screen geometry.
- Terminal color and mouse behavior vary.
- Modal dialogs and concurrent progress need careful keyboard ergonomics.
- Dense tabular data may need paging rather than large scrollable grids.

## Alignment Work

When TUI work resumes, prefer these changes:

- expose the same area list/current-area model as the wx Areas panel,
- map table snapshots into TUI browse panes,
- keep command compatibility visible,
- use the same status/error vocabulary as GUI core,
- avoid direct runtime mutation from TUI widgets without a service call boundary.
