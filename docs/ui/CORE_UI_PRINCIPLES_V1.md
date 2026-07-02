# DotTalk++ Core UI Principles v1

Status: active architecture principle.

## Purpose

DotTalk++ should have multiple user interfaces that feel related because they
are built on the same runtime and interaction principles. The CLI, Turbo Vision
TUI, Python GUI, and C++ GUI may differ in presentation, but they should not
invent incompatible concepts for work areas, commands, table snapshots, status,
errors, or task progress.

Related lane documents:

- `UI_LANE_TRADEOFFS_V1.md`
- `TUI_ALIGNMENT_PLAN_V1.md`
- `GUI_THREADING_RAII_CONTRACT_V1.md`
- `../gui/UNIFIED_GUI_CORE_V1.md`
- `../gui/OPEN_ARCH_GUI_PLAN_V1.md`
- `../gui/GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md`
- `../gui/WINDOWED_APP_CONTRACT_V1.md`
- `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `../database/DATABASE_SAFETY_CONTRACT_V1.md`

## Shared Mental Model

Every UI should expose the same core concepts where appropriate:

| Concept | Meaning |
| --- | --- |
| Work area | An opened table or workspace slot with identity, path, alias/name, order/filter state, and current record |
| Current area | The selected area that commands and browse actions target by default |
| Snapshot | Immutable read model for table grids, lists, or browse panes |
| Command lane | DotTalk/Fox-style command input and script compatibility |
| Service lane | Typed UI actions such as open table, refresh, seek, filter, import, export, validate |
| Output lane | Logs, warnings, command output, diagnostics, and transcript-style text |
| Task lane | Queued/running/completed/cancelled/failed work with progress and messages |
| Value context | Encoding, dialect, locale, parse rules, display rules, and collation/index identity |
| Safety context | Read-only/edit mode, locks, dirty state, validation, recovery, and mutation boundaries |

The UI should make these concepts visible using the idioms of each surface:

- CLI: prompts, command output, status commands.
- TUI: panes, menus, keyboard navigation, compact status bars.
- Python GUI: fast scripting-friendly windows and inspectors.
- C++ GUI: native desktop windows, menus, grids, dialogs, and packaged workflows.

## Shared Contract Rules

- Runtime state belongs behind service/session APIs, not directly in widgets.
- UI adapters translate user gestures into requests and translate structured
  results back into display updates.
- Work area identity must be explicit. Opening a second table should not
  silently destroy the first unless the user explicitly closes/replaces it.
- Work area lifecycle should be symmetrical: open, list, select, refresh, close.
- Commands should target the current area unless they explicitly name an area.
- Long operations should produce task events and must not block the visible UI.
- Threading policy should be shared, but event-loop delivery should branch per UI toolkit.
- Errors should be structured first and rendered as text second.
- Console text is useful, but it should not be the primary data contract for new UI features.
- Read-only workflows come before editing workflows unless write safety is
  explicit and tested.
- UI language, display locale, parse locale, table encoding, and collation are
  separate concepts.
- Indexes are valid only under the value/collation identity used to build them.
- Database safety state should be visible before a UI enables mutation.

## Shared Layout Pattern

Where the surface allows it, each UI should converge on this layout model:

```text
Area/workspace selector
  Current area, open areas, aliases, relation/workspace state

Primary data view
  Browse grid, record view, schema view, result set, report preview

Command/action input
  DotTalk command line, action buttons, menus, shortcuts

Output/status
  Logs, transcript, warnings, task progress, current position
```

TUI and GUI should differ in rendering, not in conceptual ownership.

## Branching Principle

Branch only where the UI medium has a real advantage.

Do not fork business behavior because a toolkit makes it convenient. Fork
presentation, navigation, packaging, automation hooks, and inspection workflows
where the UI surface is naturally stronger.

## Minimum Shared Smoke

Each first-class UI lane should prove:

- open one table,
- open a second table without losing the first,
- switch current area,
- close an area without corrupting the remaining active area,
- refresh a read-only snapshot,
- run a command through the compatibility lane,
- show structured status/error output,
- keep the UI responsive while work is queued.

## GUI Sync Workflow

The windowed GUI lanes now have an explicit synchronization workflow in
`../gui/GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md`.

Use that document when a feature exists in one UI lane and needs to be mirrored,
deferred, or promoted into the shared core contract. This is especially
important for wx, Python/Tkinter, and TurboTalk/FoxTalk changes that affect
workspace state, cursor movement, indexes, relations, command behavior,
language/message text, or record view behavior.
