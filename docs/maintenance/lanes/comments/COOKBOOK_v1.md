# comments Blackbox cookbook v1

## Data in
source comments and @dottalk.usage blocks

## Blackbox process
scan, harvest, classify, import, validate

## Information out
SRCFILE/SRCBLOCK/SRCLINE/SRCUSAGE/SRCCLASS/SRCDISP/SRCALIAS/MEMO_LINES and comments.dtschema

## Current runtime boundary
- The comments workspace is the preserved evidence layer.
- Current `CMDHELP BUILD` still mines source files and `@dottalk.usage v1` contracts directly.
- Current HELP DATA rebuilds do not yet consume `SRC*` DBFs as the primary live feed.

## Controls
- Start report-only unless a separate apply gate is explicitly authorized.
- Name inputs, outputs, backups, rollback, smoke tests, and next gate before mutation.
- Runtime scripts remain under dottalkpp/data/scripts; maintenance scripts live here.
- Source code remains outside this lane unless a separate source-mutation package is authorized.

## Next planned step
comments-to-HELP crosswalk audit
