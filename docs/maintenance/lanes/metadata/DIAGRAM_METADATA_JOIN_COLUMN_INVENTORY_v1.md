# Diagram Metadata Join Column Inventory v1

Status: active join inventory
Scope: staged `DIAG*` CSV headers versus current `SRC*`, `HELP_ARTIFACTS`, `SYSCMD`, `SYSMSG`, `MANMEDIA`, and `MANANCHOR` columns

## Purpose

This document turns the diagram metadata doctrine into a concrete join-column inventory.

It answers four practical questions:

1. what columns the staged `DIAG*` files actually have today
2. what columns the current feeder systems actually expose today
3. which joins are physically strong right now
4. which joins still need one more normalization pass before live promotion

## Current staged diagram headers

### `DIAGENTITY_IMPORT_v1.csv`

Current header:

```text
ENTITYID,RUNID,ETYPE,ENAME,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,SRC,MANUAL,NOTES
```

### `DIAGREL_IMPORT_v1.csv`

Current header:

```text
RELID,RUNID,FROMID,TOID,RELNAME,JOINON,STYLE,STATUS,EVIDCLS,REVSTAT,SRC,NOTES
```

### `DIAGART_IMPORT_v1.csv`

Current header:

```text
ARTID,RUNID,ARTTYPE,ARTNAME,PATH,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,MANUAL,NOTES
```

## Current feeder columns

### Comments/source evidence

Source-comment schema proof:

- [SOURCE_COMMENT_SCHEMA_CREATE.dts](/D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_SCHEMA_CREATE.dts:1)

Current strong source tables and columns:

`SRCFILE`

```text
FILEID, RELPATH, ROOT, EXT, HASH, HAS_HDR, HDR_LINES, FIRST_HDR,
LAST_HDR, FIRST_CODE, DET_KIND, DET_OWNER, DET_CMD, STATUS, UPDATED
```

`SRCUSAGE`

```text
USAGEID, BLOCKID, FILEID, OWNER, COMMAND, CATEGORY, STATUS, NOARGS,
EFFECT, MUTATES, USGACC, SUMMARY, USAGE, EXAMPLES, NOTES, RELATED
```

`SRCCLASS`

```text
CLASSID, FILEID, BLOCKID, COMMAND, NORMCMD, CMDKEY, STATUS, RULEID,
POLICY, REASON, ACTION
```

Immediate conclusion:

- `FILEID` and `COMMAND` are the strongest real source join keys today

### HELP artifact lane

Current harvested HELP artifact header:

- [HELP_HELP_ARTIFACTS.csv](/D:/code/ccode/docs/manuals/developer/manualgen/harvested/HELP_HELP_ARTIFACTS.csv:1)

```text
ID, CATALOG, COMMAND, CMDKEY, OWNER, KIND, SOURCE, CONFID,
SEVERITY, NAME, ORD, TEXT, DETAIL, EVIDENCE
```

Immediate conclusion:

- `CMDKEY`, `COMMAND`, `OWNER`, `KIND`, and `NAME` are the best HELP-side attachment and crosswalk columns today

### Metadata command lane

Compact current `SYSCMD` create/import package evidence:

- [metacheck_v2_syscmd_native_create_import_package_v1.ps1](/D:/code/ccode/dottalkpp/docs/tools/metacheck_v2_syscmd_native_create_import_package_v1.ps1:1)

```text
CMD_ID, CAN_NAME, TYPE, VIS, HANDLER, ACTIVE
```

Immediate conclusion:

- `CAN_NAME` is the strongest current command identity join column
- `CMD_ID` is the strongest stable metadata-side identifier when present

### Metadata message lane

Current manualgen evidence for the compact/future `SYSMSG` feeder:

- [messages_errors_and_diagnostics.md](/D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_273_pre_promotion_active_publication_backup_20260527_125906/sections/sections/messages_errors_and_diagnostics.md:1)

```text
MSG_ID, SYMBOL, ENUM_NAME, SEVERITY, FACILITY, SHORT_TXT, IMPL_STAT,
VIS_TIER, OWNER, SRC_AUTH, SRC_FILE, PUB_SURF, USED_RUN, ACTIVE,
VER_AT, SUG_ACT, NOTES
```

Immediate conclusion:

- `SYMBOL` is the best current message-identity join target
- `MSG_ID` is the preferred stable metadata-side identifier when present
- `SYSMSG` is still a feeder lane and may be sparse

### Manual attachment lane

Current MAN* create proof:

- [MDO_248_MAN_SCHEMA_EXECUTE_v1.dts](/D:/code/ccode/docs/manuals/developer/manualgen/generated/x64base_man_catalog_execution_v1/dts/MDO_248_MAN_SCHEMA_EXECUTE_v1.dts:1)

`MANMEDIA`

```text
MEDIA_ID, FILE_NAME, RELATIVE_P, SHA256, LENGTH_BYT
```

`MANANCHOR`

```text
ANCHOR_ID, MEDIA_ID, MEDIA_FILE, ACTIVE_COM, ACTIVE_C01
```

Immediate conclusion:

- `MEDIA_ID` is the strongest manual-media join key
- `ANCHOR_ID` is the strongest manual-anchor join key
- `MEDIA_FILE` and `FILE_NAME` are useful cross-check columns but should not replace `MEDIA_ID`

## Join inventory

## 1. Source-comment joins

| Diagram row kind | Current DIAG column | Target table | Target column | Strength | Notes |
|---|---|---|---|---|---|
| source entity | `ENAME=SRCFILE` style row label | `SRCFILE` | logical table name only | weak | current staged row only names the table, not the specific file row |
| source usage entity | `ENAME=SRCUSAGE` style row label | `SRCUSAGE` | logical table name only | weak | current staged row names the table family, not a usage row |
| source relation | `JOINON=FILEID` | `SRCFILE` / child `SRC*` table | `FILEID` | strong | this is the strongest proven relation pattern today |
| command relation | `JOINON=COMMAND` | `SRCUSAGE` / `SRCCLASS` | `COMMAND` | strong | already proven in current comments relation scripts |

Current assessment:

- `DIAGREL.JOINON` already captures the correct normalized join concept for the comments lane
- `DIAGENTITY` does not yet carry enough row-level keys to point at a specific `SRCFILE.FILEID` or `SRCUSAGE.USAGEID`

## 2. HELP artifact joins

| Diagram row kind | Current DIAG column | Target table | Target column | Strength | Notes |
|---|---|---|---|---|---|
| help-topic entity | `TOPICID` | `HELP_ARTIFACTS` | `OWNER` or `CMDKEY` crosswalk | medium | workable for logical/topic joins, not yet a strict physical FK |
| help artifact row | `TOPICID` + `OWNER` | `HELP_ARTIFACTS` | `OWNER`, `COMMAND`, `CMDKEY`, `KIND`, `NAME` | medium | enough for staged crosswalks |
| generated help artifact | `ARTNAME` / `PATH` | `HELP_ARTIFACTS` | `NAME` or `DETAIL` | weak | path/file joins should stay secondary to command/topic joins |

Current assessment:

- the HELP side is already semantically rich
- the staged `DIAGART` and `DIAGENTITY` rows can logically attach to HELP now
- a stricter normalized join needs `CMDKEY` or a dedicated help-owner field in `DIAG*`

## 3. Metadata command joins

| Diagram row kind | Current DIAG column | Target table | Target column | Strength | Notes |
|---|---|---|---|---|---|
| command architecture entity | `ENAME` | `SYSCMD` | `CAN_NAME` | medium | workable if `ENAME` is the canonical command token |
| command topic/entity | `TOPICID` | `SYSCMD` | future crosswalk via canonical command | weak | topic IDs are not yet a direct `SYSCMD` key |
| command artifact | `OWNER` | `SYSCMD` | future crosswalk | weak | `OWNER` is too broad without a command-name field |

Current assessment:

- `SYSCMD.CAN_NAME` is ready
- the staged `DIAGENTITY` format should add an explicit canonical command column before claiming a normalized metadata join

## 4. Metadata message joins

| Diagram row kind | Current DIAG column | Target table | Target column | Strength | Notes |
|---|---|---|---|---|---|
| message/diagnostic entity | `ENAME` or `TOPICID` | `SYSMSG` | `SYMBOL` | weak | possible only by naming convention today |
| message artifact | `OWNER` / `NOTES` | `SYSMSG` | `OWNER`, `SYMBOL` | weak | not stable enough for a real join |

Current assessment:

- `SYSMSG` should remain visible in the inventory now
- but the staged `DIAG*` headers are not yet strong enough for a clean message-level physical join

## 5. Manual attachment joins

| Diagram row kind | Current DIAG column | Target table | Target column | Strength | Notes |
|---|---|---|---|---|---|
| emitted artifact | `PATH` | `MANMEDIA` | `RELATIVE_P` | medium | useful current bridge if relative paths are normalized |
| emitted artifact | future explicit media key | `MANMEDIA` | `MEDIA_ID` | strong | preferred final design |
| publication anchor | future explicit anchor key | `MANANCHOR` | `ANCHOR_ID` | strong | preferred final design |
| media-to-anchor chain | `PATH` plus file name | `MANMEDIA` + `MANANCHOR` | `FILE_NAME` / `MEDIA_FILE` | medium | workable for cross-check, not preferred as the primary key path |

Current assessment:

- `DIAGART.PATH -> MANMEDIA.RELATIVE_P` is the best current manual-side bridge
- the final normalized model should use `MEDIA_ID` and `ANCHOR_ID`, not filename matching

## What works right now without column changes

These joins are strong enough today for staged/report work:

- `DIAGREL.JOINON=FILEID` against the `SRCFILE` relation family
- `DIAGREL.JOINON=COMMAND` against the `SRCUSAGE`/`SRCCLASS` relation family
- `DIAGART.PATH -> MANMEDIA.RELATIVE_P` as a manual artifact bridge
- `DIAGENTITY.TOPICID` and `DIAGART.TOPICID` as logical HELP/manual topic anchors
- `DIAGENTITY.ENAME -> SYSCMD.CAN_NAME` when the entity is clearly a canonical command token

## What is not normalized enough yet

The current staged headers are not yet sufficient for clean row-level joins in these areas:

- specific source row joins to `SRCFILE.FILEID`, `SRCUSAGE.USAGEID`, or `SRCCLASS.CLASSID`
- strict HELP artifact joins by `CMDKEY`
- strict metadata joins by `CMD_ID`
- strict message joins by `MSG_ID` or `SYMBOL`
- strict manual joins by `MEDIA_ID` and `ANCHOR_ID`

## Minimal column expansion recommended

The staged files do not need a redesign. They need a small normalization pass.

### Recommended additions to `DIAGENTITY`

- `SRC_TABLE`
- `SRC_KEY`
- `SRC_VALUE`
- `CAN_NAME`
- `MSG_SYMBOL`
- `CMDKEY`
- `MEDIA_ID`
- `ANCHOR_ID`

### Recommended additions to `DIAGREL`

- `JOIN_TABLE`
- `JOIN_FIELD`
- `FROM_SRC_VALUE`
- `TO_SRC_VALUE`
- `PROOF_LEVEL`

### Recommended additions to `DIAGART`

- `MEDIA_ID`
- `ANCHOR_ID`
- `CMDKEY`
- `RELATIVE_P`

These additions preserve the current staged rows while making future live joins explicit.

## Recommended join policy

Use this priority order.

### Source/comment diagrams

1. prefer `FILEID`
2. then `COMMAND`
3. then logical table/topic names only if no row key exists

### HELP diagrams

1. prefer `CMDKEY`
2. then `OWNER`
3. then `COMMAND`
4. use `NAME` only as a secondary cross-check

### Metadata command diagrams

1. prefer `CMD_ID`
2. then `CAN_NAME`

### Metadata message diagrams

1. prefer `MSG_ID`
2. then `SYMBOL`

### Manual/publication diagrams

1. prefer `MEDIA_ID`
2. then `ANCHOR_ID`
3. use `RELATIVE_P` / `FILE_NAME` only as a bridge or cross-check

## Practical bottom line

The staged `DIAG*` files are already good enough to support:

- report-only relation diagrams
- HELP/manual topic alignment
- comments-lane relation diagrams
- draw.io and Mermaid generation from staged facts

They are not yet strong enough for a fully normalized live promotion because the current rows mostly carry:

- labels
- topic names
- owner names
- relation names

and not enough explicit row keys.

So the next correct move is not to rebuild the diagram lane. It is to add a small set of explicit join-key columns so the lane can marry cleanly to:

- `SRCFILE` and `SRCUSAGE`
- `HELP_ARTIFACTS`
- `SYSCMD` and `SYSMSG`
- `MANMEDIA` and `MANANCHOR`

without relying on filename or prose matching.
