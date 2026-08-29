# DotTalk++ GUI Localization Message Contract v1

Status: active skeleton.

## Purpose

Windowed GUI frontends must use the same language and region principles as the
CLI, TUI, metadata, HELP, and documentation lanes. GUI text is not allowed to
become an isolated pile of hard-coded English strings.

This contract applies to:

- C++ wxWidgets GUI,
- Python GUI preview,
- future windowed GUI frontends,
- future TUI alignment where the same event/status model is used.

Related contracts:

- `../LANGUAGE_AND_REGION_SEAMS_v1.md`
- `UNIFIED_GUI_CORE_V1.md`
- `WINDOWED_APP_CONTRACT_V1.md`
- `GUI_THREADING_EVENT_MODEL_V1.md`
- `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`

## Core Rule

GUI identity is canonical. GUI wording is localized.

Stable values:

- event kind,
- task state,
- task label code,
- status message code,
- area ID,
- command ID,
- field name,
- table path,
- database value identity.

Localized values:

- menu labels,
- toolbar labels,
- tab labels,
- task progress text,
- status bar text,
- log severity labels,
- dialog text,
- explanatory error/warning text.

## Locale Context

Every GUI lane should be able to carry this context:

| Field | Meaning | Default |
| --- | --- | --- |
| `message_locale` | UI chrome, messages, warnings, status text | `en-US` |
| `display_locale` | Formatting for dates, numbers, currency, and value presentation | `en-US` |
| `parse_locale` | Locale used when interpreting user-entered localized values | `en-US` |
| `region_id` | Region policy selector for future catalog/profile lookup | `GLOBAL` |

These fields intentionally mirror the language/region seam doctrine without
requiring full multilingual coverage on day one.

## Message Resolution

GUI renderers must prefer stable keys over fallback text.

Resolution order:

1. look up `label_code` or `StatusMessage.code` in the active GUI message
   catalog,
2. fall back to the English text carried by the event/result,
3. include the stable code in logs and diagnostic surfaces where useful.

C++ implementation:

- `dottalkpp/data/messaging/gui_messages.csv`
- `tools/gui/generate_gui_messages.py`
- `include/gui/core/localization.hpp`
- `include/gui/core/generated_gui_messages.hpp`
- `src/gui/core/localization.cpp`

Python mirror:

- `tools/gui_preview/generated_gui_text.py`
- `tools/gui_preview/dottalk_gui_text.py`
- `tools/gui_preview/gui_contract.py`

Seeded message locales:

- `en-US`
- `es`
- `fr`
- `de`
- `it`

## Task Progress Contract

Task progress must carry both:

- `label_code`: stable message key,
- `label`: fallback text.

The fallback is for debug, tests, and transitional rendering. Windowed
frontends should render through the message resolver.

Examples:

| Label code | Fallback |
| --- | --- |
| `gui.task.queued` | `Queued` |
| `gui.task.opening_table` | `Opening table` |
| `gui.task.snapshot_ready` | `Table snapshot ready` |

## Status Message Contract

`StatusMessage` remains the durable result/status shape:

| Field | Role |
| --- | --- |
| `severity` | `info`, `warning`, or `error` |
| `code` | stable status/message key |
| `text` | fallback text |
| `detail` | diagnostic detail, path, or exception text |

GUI logs should preserve the code. Status bars and dialogs may show only the
localized text when space is limited.

## Data Locale Boundary

Message localization must not rewrite data.

Database values remain canonical/raw at the core boundary. Formatting and
parsing belong to the display/parse locale layer described by
`../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`.

Examples:

- a DBF date value is not translated in storage,
- a numeric field keeps its canonical value,
- collation/search rules are explicit database/index contracts,
- field names and table aliases remain stable identifiers unless a separate
  display-label layer is added.

## Current Skeleton

Current source-defined pieces:

- C++ `LocaleContext`,
- C++ GUI text resolver,
- shared GUI message CSV seed under `dottalkpp/data/messaging`,
- generated C++ GUI message adapter,
- C++ startup locale resolution through `DOTTALK_GUI_LOCALE`, `DOTTALK_LOCALE`,
  `LANG`, and wx `--locale`,
- C++ task/event `label_code`,
- C++ status rendering helper,
- Python `LocaleContext`,
- Python GUI text resolver,
- generated Python GUI message adapter,
- Python startup locale resolution through the same environment variables and
  `--locale`,
- Italian (`it`, including `it_IT` environment-style normalization) seeded and
  smoke-tested across the C++ and Python GUI lanes,
- Python task/event `label_code`,
- wx and Tk adapters consuming the resolver for key chrome/status text.

Current limitations:

- GUI catalogs are generated from a CSV seed, not full production localization
  assets.
- GUI status-code coverage is seeded for current open/select/close/command and
  snapshot messages.
- CLI `MessageId` and GUI text keys are not yet backed by one physical catalog.
- SET LANGUAGE / SET LOCALE is not yet wired into a persisted GUI session
  settings file.

## Promotion Path

1. Keep GUI label/status codes stable.
2. Move the GUI CSV seed into the full shared message catalog or locale spine
   when that runtime catalog path is ready for GUI consumers.
3. Expose GUI locale selection from startup/session settings.
4. Add value display/parse locale rules before edit/write workflows mature.
5. Add screenshot/runtime proofs for at least one non-English GUI locale.
