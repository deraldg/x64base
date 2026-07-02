# SelfDoc Apps Index v1

This index names the mutable-document and SelfDoc subsystem apps currently recognized by the maintenance architecture.

## comments

Purpose: preserve source comments and `@dottalk.usage v1` contracts as queryable evidence.

Current runtime data position:

- `dottalkpp/data/comments`
- `dottalkpp/data/workspaces/comments.dtschema`

Current builder relationship:

- evidence-preservation layer
- `CMDHELP BUILD` still mines source/contracts directly instead of reading the `SRC*` DBFs back as its primary feed

Tables:

- SRCFILE
- SRCBLOCK
- SRCLINE
- SRCUSAGE
- SRCCLASS
- SRCDISP
- SRCALIAS
- MEMO_LINES

## help

Purpose: transform registry, source contracts, DOTREF/FOXREF, curated docs, and source-mined facts into HELP DATA and runtime help surfaces.

Primary runtime/builder surface:

- CMDHELP
- CMDHELP BUILD
- CMDHELP LEGACY
- HELP
- HELP /DOT
- DOTHELP

## manualgen

Purpose: produce and catalog the developer manual and related manual artifacts.

Runtime inspector:

- MANUAL

Catalog family:

- MAN*

## datadict

Purpose: inspect and govern the Data Dictionary catalog and x64base bridge.

Runtime inspector:

- DDICT

Catalog family:

- DD*
- DATA_DICTIONARY_*

## messaging

Purpose: replace scattered output text with catalog-backed, typed, language-aware messages.

Known runtime setting:

- SET LANGUAGE
- SET LOCALE

Candidate catalog family:

- MSGDEF
- MSGTEXT
- MSGARG
- MSGUSE
- MSGLANG
- MSGRUN
- MSGGATE
- MSGREVIEW

## gui

Purpose: keep C++ wxWidgets, Python/Tkinter, and TurboTalk/FoxTalk UI lanes
aligned over one DotTalk++ / x64base runtime truth.

Current architecture documents:

- `docs/gui/OPEN_ARCH_GUI_PLAN_V1.md`
- `docs/gui/UNIFIED_GUI_CORE_V1.md`
- `docs/gui/GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md`
- `docs/gui/GUI_LOCALIZATION_MESSAGE_CONTRACT_V1.md`
- `docs/ui/CORE_UI_PRINCIPLES_V1.md`
- `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`

Current source lanes:

- `src/gui/core`
- `src/gui/wx`
- `tools/gui_preview`
- `src/tv`

Runtime surfaces:

- `dottalk_wx_next`
- Python/Tkinter preview launcher
- TurboTalk/FoxTalk TUI

## blackbox

Purpose: teach the data-in, process, information-out model for SelfDoc systems.

Current command/source file:

- `src/cli/cmd_bbox.cpp`
- command surface: BBOX

## maintenance

Purpose: govern SDLC procedures, cookbooks, scripts, proof gates, backups, rollback, and smoke tests.

Current command/source file:

- `src/cli/cmd_maint.cpp`
- command surface: MAINT

Current document grouping note:

- `docs/maintenance/DOCUMENT_INFORMATION_CLASSES_FOR_AI_MAINTENANCE_V1.md`

Shared native code root:

- `src/maintenance`

External script station:

- `dottalkpp/scripts/maintenance`
