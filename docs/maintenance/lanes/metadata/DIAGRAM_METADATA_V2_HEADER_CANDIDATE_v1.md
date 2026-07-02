# Diagram Metadata v2 Header Candidate v1

Status: active candidate header plan
Scope: staged `DIAGENTITY`, `DIAGREL`, and `DIAGART` v2 headers for normalized joins into source evidence, HELP, metadata, and manual attachment lanes

## Purpose

This document proposes the minimal v2 staged headers needed to move the diagram metadata lane from topic/label joins toward explicit normalized joins.

The goal is not a redesign.

The goal is:

- keep current v1 meaning
- preserve current staging workflow
- add only the keys needed for clean joins

## Design rule

v2 should keep three layers of meaning separate:

1. display meaning
2. evidence meaning
3. attachment meaning

That means:

- display labels stay human-friendly
- source/metadata joins use explicit key columns
- manual/help attachment uses explicit attachment keys

## `DIAGENTITY` v2 candidate

### v1 header

```text
ENTITYID,RUNID,ETYPE,ENAME,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,SRC,MANUAL,NOTES
```

### v2 candidate header

```text
ENTITYID,RUNID,ETYPE,ENAME,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,SRC,MANUAL,
SRC_TABLE,SRC_KEY,SRC_VALUE,CAN_NAME,CMDKEY,MSG_ID,MSG_SYMBOL,MEDIA_ID,ANCHOR_ID,NOTES
```

### Why each new column exists

- `SRC_TABLE`
  identifies the feeder table family such as `SRCFILE`, `SRCUSAGE`, `SYSCMD`, `SYSMSG`, `HELP_ARTIFACTS`, `MANMEDIA`, or `MANANCHOR`
- `SRC_KEY`
  identifies the key column name such as `FILEID`, `COMMAND`, `CAN_NAME`, `CMDKEY`, `MSG_ID`, `SYMBOL`, `MEDIA_ID`, or `ANCHOR_ID`
- `SRC_VALUE`
  stores the concrete row key value used in the staged join
- `CAN_NAME`
  carries canonical command identity without overloading `ENAME`
- `CMDKEY`
  carries HELP-side command/topic identity
- `MSG_ID`
  carries compact message identity when available
- `MSG_SYMBOL`
  carries message symbol identity when `MSG_ID` is absent or sparse
- `MEDIA_ID`
  carries explicit manual-media attachment identity
- `ANCHOR_ID`
  carries explicit manual-anchor identity

### Recommended usage

- source-table entities use `SRC_TABLE`, `SRC_KEY`, and `SRC_VALUE`
- command entities also fill `CAN_NAME`
- HELP-facing entities also fill `CMDKEY`
- message entities fill `MSG_ID` and/or `MSG_SYMBOL`
- manual-facing entities fill `MEDIA_ID` and/or `ANCHOR_ID`

## `DIAGREL` v2 candidate

### v1 header

```text
RELID,RUNID,FROMID,TOID,RELNAME,JOINON,STYLE,STATUS,EVIDCLS,REVSTAT,SRC,NOTES
```

### v2 candidate header

```text
RELID,RUNID,FROMID,TOID,RELNAME,JOINON,STYLE,STATUS,EVIDCLS,REVSTAT,SRC,
JOIN_TABLE,JOIN_FIELD,FROM_SRC_VALUE,TO_SRC_VALUE,PROOF_LEVEL,NOTES
```

### Why each new column exists

- `JOIN_TABLE`
  identifies the real table or table family carrying the join proof
- `JOIN_FIELD`
  makes the actual join field explicit instead of relying only on `JOINON`
- `FROM_SRC_VALUE`
  stores the normalized source-side key value when relation proof is row-specific
- `TO_SRC_VALUE`
  stores the normalized target-side key value when relation proof is row-specific
- `PROOF_LEVEL`
  separates relation confidence from visual style

### Recommended usage

- preserve `JOINON` for compact display and continuity
- use `JOIN_TABLE` and `JOIN_FIELD` for the real physical join statement
- use `PROOF_LEVEL` for values such as `RUNTIME_PROVEN`, `REPORT_PROVEN`, `DESIGN_ONLY`, `DEFERRED_BY_DATA`

## `DIAGART` v2 candidate

### v1 header

```text
ARTID,RUNID,ARTTYPE,ARTNAME,PATH,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,MANUAL,NOTES
```

### v2 candidate header

```text
ARTID,RUNID,ARTTYPE,ARTNAME,PATH,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,MANUAL,
RELATIVE_P,CMDKEY,MSG_ID,MSG_SYMBOL,MEDIA_ID,ANCHOR_ID,NOTES
```

### Why each new column exists

- `RELATIVE_P`
  carries the normalized manual/media relative path field name directly
- `CMDKEY`
  supports HELP/manual artifact attachment by command/topic identity
- `MSG_ID`
  supports message/diagnostic artifact attachment where appropriate
- `MSG_SYMBOL`
  supports message artifact crosswalks in sparse seed situations
- `MEDIA_ID`
  supports clean join to `MANMEDIA`
- `ANCHOR_ID`
  supports clean join to `MANANCHOR`

## Minimal migration map

### `DIAGENTITY`

| v1 column | v2 treatment |
|---|---|
| `ENTITYID` | unchanged |
| `RUNID` | unchanged |
| `ETYPE` | unchanged |
| `ENAME` | unchanged |
| `TOPICID` | unchanged |
| `OWNER` | unchanged |
| `STATUS` | unchanged |
| `EVIDCLS` | unchanged |
| `REVSTAT` | unchanged |
| `SRC` | unchanged |
| `MANUAL` | unchanged |
| `NOTES` | unchanged |
| new join fields | append only |

### `DIAGREL`

| v1 column | v2 treatment |
|---|---|
| `RELID` | unchanged |
| `RUNID` | unchanged |
| `FROMID` | unchanged |
| `TOID` | unchanged |
| `RELNAME` | unchanged |
| `JOINON` | retained for compact continuity |
| `STYLE` | unchanged |
| `STATUS` | unchanged |
| `EVIDCLS` | unchanged |
| `REVSTAT` | unchanged |
| `SRC` | unchanged |
| `NOTES` | unchanged |
| new join fields | append only |

### `DIAGART`

| v1 column | v2 treatment |
|---|---|
| `ARTID` | unchanged |
| `RUNID` | unchanged |
| `ARTTYPE` | unchanged |
| `ARTNAME` | unchanged |
| `PATH` | unchanged |
| `TOPICID` | unchanged |
| `OWNER` | unchanged |
| `STATUS` | unchanged |
| `EVIDCLS` | unchanged |
| `REVSTAT` | unchanged |
| `MANUAL` | unchanged |
| `NOTES` | unchanged |
| new attachment fields | append only |

## Expected join patterns after v2

### Source-comment evidence

- `DIAGENTITY.SRC_TABLE=SRCFILE`, `SRC_KEY=FILEID`, `SRC_VALUE=<fileid>`
- `DIAGENTITY.SRC_TABLE=SRCUSAGE`, `SRC_KEY=USAGEID`, `SRC_VALUE=<usageid>`
- `DIAGREL.JOIN_TABLE=SRCFILE`, `JOIN_FIELD=FILEID`
- `DIAGREL.JOIN_TABLE=SRCUSAGE`, `JOIN_FIELD=COMMAND`

### HELP artifacts

- `DIAGENTITY.CMDKEY -> HELP_ARTIFACTS.CMDKEY`
- `DIAGART.CMDKEY -> HELP_ARTIFACTS.CMDKEY`

### Metadata commands

- `DIAGENTITY.CAN_NAME -> SYSCMD.CAN_NAME`

### Metadata messages

- `DIAGENTITY.MSG_ID -> SYSMSG.MSG_ID`
- `DIAGENTITY.MSG_SYMBOL -> SYSMSG.SYMBOL`
- `DIAGART.MSG_ID -> SYSMSG.MSG_ID`
- `DIAGART.MSG_SYMBOL -> SYSMSG.SYMBOL`

### Manual attachment

- `DIAGART.MEDIA_ID -> MANMEDIA.MEDIA_ID`
- `DIAGART.ANCHOR_ID -> MANANCHOR.ANCHOR_ID`
- `DIAGART.RELATIVE_P -> MANMEDIA.RELATIVE_P`

## What should not be added yet

Do not expand v2 into a general-purpose modeling language.

Hold off on:

- free-form polymorphic foreign-key systems
- multiple source-key columns per row
- embedded JSON
- graph-only synthetic IDs that replace real feeder keys
- layout/render columns that belong in draw.io or Mermaid consumers

## Candidate CSV header templates

### `DIAGENTITY_IMPORT_v2.header.csv`

```text
ENTITYID,RUNID,ETYPE,ENAME,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,SRC,MANUAL,SRC_TABLE,SRC_KEY,SRC_VALUE,CAN_NAME,CMDKEY,MSG_ID,MSG_SYMBOL,MEDIA_ID,ANCHOR_ID,NOTES
```

### `DIAGREL_IMPORT_v2.header.csv`

```text
RELID,RUNID,FROMID,TOID,RELNAME,JOINON,STYLE,STATUS,EVIDCLS,REVSTAT,SRC,JOIN_TABLE,JOIN_FIELD,FROM_SRC_VALUE,TO_SRC_VALUE,PROOF_LEVEL,NOTES
```

### `DIAGART_IMPORT_v2.header.csv`

```text
ARTID,RUNID,ARTTYPE,ARTNAME,PATH,TOPICID,OWNER,STATUS,EVIDCLS,REVSTAT,MANUAL,RELATIVE_P,CMDKEY,MSG_ID,MSG_SYMBOL,MEDIA_ID,ANCHOR_ID,NOTES
```

## Recommended next step

The next correct step is:

1. stage v2 header-only templates
2. map a few current v1 rows into v2 by hand
3. prove one row each for:
   - source evidence
   - HELP artifact
   - metadata command
   - metadata message
   - manual media/anchor attachment

Only after that should the lane consider a broader v1-to-v2 restaging pass.
