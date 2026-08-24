# DEV-18 Known Red Paths

```yaml
page_id: DEV-18
title: Known Red Paths
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Runtime canaries

| ID | Status | Summary |
|---|---|---|
| CAN-001 | OPEN | SET ORDER/CNX tag availability and reporting consistency. |
| CAN-002 | OPEN | x64 ERSATZ load reports failure while browser state appears usable. |
| CAN-003 | OPEN | WORKSPACE OPEN DBF memo backend auto-attach gap. |
| CAN-004 | OPEN | MIN/MAX scalar function versus aggregate command ambiguity. |
| CAN-005 | OPEN | AGGS scaffold/debug command exposure. |
| CAN-006 | DEFERRED | ERSATZ GRID snapshot branch deferred. |
| CAN-007 | DEFERRED | BLOCKID-level SelfDoc joins deferred; FILEID is reliable. |

## HELP/META evidence canaries

| ID | Status | Summary |
|---|---|---|
| HM-CAN-001 | OPEN | HELP broad / META narrow asymmetry. |
| HM-CAN-002 | OPEN | SYSFUNC empty. |
| HM-CAN-003 | REVIEW | SYSSUBCMD seed hygiene. |
| HM-CAN-004 | REVIEW | SYSENTVAR seed hygiene. |
| HM-CAN-005 | REVIEW | SYSHELP narrow seed. |
| HM-CAN-006 | OPEN | AGGS public/internal classification conflict. |
| HM-CAN-007 | REVIEW | SOURCE_MINER inferred rows require review. |

## Publication/manual canaries

| ID | Status | Summary |
|---|---|---|
| PUB-CAN-001 | OPEN | Combined developer manual can drift from per-section chapter files if mirrored updates are not pushed upward after verified edits. |
