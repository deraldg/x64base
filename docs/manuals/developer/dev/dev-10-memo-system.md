# DEV-10 Memo System

```yaml
page_id: DEV-10
title: Memo System
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Current truth

```text
normal USE memo path is proven
workspace/bulk-open memo attach path is canary
MemoManager owns payload lifecycle
DbArea owns record/table context
metadata alignment should mature through SYSFLDDIC, SYSMSG, SYSCMD, SYSARGS, and SYSHELP
```

## Proven path

`USE memo_x64` attaches the memo backend, supports memo REPLACE, and preserves close/reopen readback.

## Canary path

`WORKSPACE OPEN DBF` opens `MEMO_X64.dbf` without memo backend attachment in the observed red path.

## Crosswalk target

`memo-system-crosswalk-v0.csv`
