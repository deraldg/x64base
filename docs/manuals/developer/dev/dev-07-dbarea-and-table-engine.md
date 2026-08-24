# DEV-07 DbArea and Table Engine

```yaml
page_id: DEV-07
title: DbArea and Table Engine
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Core ownership

DbArea owns table runtime state: open table state, records, cursor state, mutation behavior, table flavor behavior, and work-area identity.

DbArea does not own memo payload lifecycle, LMDB physical backend implementation, HELP/META cataloging, browser rendering, TUI display policy, or manual generation.

## Record-number width (RECNO64, development 2026-07)

DbArea's authoritative cursor state is 64-bit (`_crn64`, `_rec_count64`, exposed via `recno64()`/`recCount64()`). The record-number widening lane is progressively moving the remaining runtime paths off 32-bit: positioning (`gotoRec64`), the navigation commands (`GO`/`GOTO`/`SKIP`/`RECNO`/`TOP`/`BOTTOM`/`FIRST`/`LAST`/`NEXT`/`PRIOR`), the record-lock API, the table-buffer change key, and the active CDX/LMDB index record numbers are widened and regression-checked (CURSOR, INDEX_X64). The classic `recno()`/`recLength()`/`cpr()` accessors still saturate at `INT_MAX`. This is development-only and not promoted, and addressing past `2^31` is not yet measured. Path-by-path status is on the website [64-Bit Capacity Math](https://x64base.com/docs/engine/x64-capacity-math) page.

## Current evidence lanes

- `include/xbase.hpp`
- `src/xbase`
- table command handlers in `src/cli`
- HELP command/topic/artifact rows
- runtime table/work-area smokes

## Future/maturing META feeders

- `SYSFLDDIC`: field dictionary and logical field roles
- `SYSCMD`: table command identity and handlers
- `SYSARGS`: command argument metadata
- `SYSMSG`: table/mutation/navigation messages and errors
- `SYSHELP`: table concept help

## Crosswalk target

`table-command-crosswalk-v0.csv`
