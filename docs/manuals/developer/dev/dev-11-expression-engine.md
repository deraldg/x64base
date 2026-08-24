# DEV-11 Expression Engine

```yaml
page_id: DEV-11
title: Expression Engine
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Correct evidence rule for functions

SYSFUNC is the future semantic feeder for function metadata. Until it is populated, temporary evidence lanes must be labeled, crosswalked, and designed for later SYSFUNC reconciliation.

## Current temporary evidence lanes

- CMDHELPCHK Function Inventory
- HELP FUNCTION `<name>`
- HELP FUNCTIONS
- function catalog source
- xexpr/function registry source
- runtime expression smokes

## Future preferred META lane

- `META.SYSFUNC`

## Function crosswalk statuses

`PENDING_SYSFUNC_SEED`, `READY_FOR_SYSFUNC_PROMOTION`, `BLOCKED_BY_ARG_CONFLICT`, `BLOCKED_BY_HANDLER_UNKNOWN`, `BLOCKED_BY_RUNTIME_CANARY`, `PROMOTED_TO_SYSFUNC`.
