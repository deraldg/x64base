# Diagram Metadata v2 Proof Sample v1

Status: active proof sample
Scope: hand-mapped v1-to-v2 proof rows for source evidence, HELP artifacts, metadata command identity, message candidate identity, and manual media/anchor attachment

## Purpose

This packet proves the next step after the v2 header plan.

It does not attempt a full v1-to-v2 restaging pass.

It proves that the v2 headers can carry:

- source-comment join keys
- HELP artifact join keys
- metadata command join keys
- message candidate keys
- manual media and anchor keys

using a very small hand-mapped set.

## Files in this proof packet

- [DIAGENTITY_IMPORT_v2.proof_sample.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGENTITY_IMPORT_v2.proof_sample.csv)
- [DIAGREL_IMPORT_v2.proof_sample.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGREL_IMPORT_v2.proof_sample.csv)
- [DIAGART_IMPORT_v2.proof_sample.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGART_IMPORT_v2.proof_sample.csv)

## What is proven

### 1. Source evidence carry-forward

The proof packet preserves the current `FILEID` and `COMMAND` relation doctrine.

It shows:

- table-level `SRCFILE` and `SRCUSAGE` entities
- a preserved `SRCFILE -> SRCUSAGE` relation using `JOIN_TABLE=SRCFILE` and `JOIN_FIELD=FILEID`

This proves the v2 header can carry the existing source-evidence join family without changing the meaning of the current staged rows.

### 2. HELP artifact crosswalk

The packet uses the harvested HELP row for:

- `COMMAND=ABOUT`
- `CMDKEY=DOT|ABOUT`
- `OWNER=COMMAND:ABOUT`
- `NAME=COMMAND_STATUS`

This proves the v2 packet can carry:

- `CMDKEY`
- `CAN_NAME`
- HELP-side ownership

without relying only on prose or topic labels.

### 3. Metadata command identity

The packet includes a command entity for `ABOUT` crosswalked as:

- `SRC_TABLE=SYSCMD`
- `SRC_KEY=CAN_NAME`
- `SRC_VALUE=ABOUT`
- `CAN_NAME=ABOUT`

This proves the v2 packet can carry the compact `SYSCMD` command identity path directly.

### 4. Manual media and anchor attachment

The packet includes a manual media/anchor pair from the accepted manual manifests:

- `MEDIA_ID=MEDIA-STORY-001`
- `ANCHOR_ID=media-storyboard-cobol-connected-computers`
- `RELATIVE_P=docs\media\ChatGPT Image May 26, 2026, 11_23_18 AM (1).png`

This proves the v2 packet can attach diagrams to the manual lane with:

- `MEDIA_ID`
- `ANCHOR_ID`
- `RELATIVE_P`

instead of relying on filename-only matching.

## What is still only a candidate

### Message identity

The packet includes a message candidate row for `COMMAND_STATUS`.

This row is intentionally not claimed as runtime-proven `SYSMSG` truth.

It exists to prove that the v2 header can carry:

- `SRC_TABLE=SYSMSG`
- `SRC_KEY=SYMBOL`
- `SRC_VALUE=COMMAND_STATUS`
- `MSG_SYMBOL=COMMAND_STATUS`

while still marking the row as review-needed and sparse.

That is the correct treatment right now because:

- the HELP artifact harvest shows `COMMAND_STATUS`
- the compact/future `SYSMSG` lane is still sparse
- we should not over-claim a live message-catalog proof where we only have a crosswalk candidate

## Practical bottom line

This proof packet shows that the v2 headers are sufficient for the next lane.

They can already carry one row each for:

- source evidence
- HELP artifact
- metadata command identity
- message candidate identity
- manual media and anchor attachment

That means the next serious step is no longer header design.

It is a controlled v1-to-v2 restaging pass with explicit join keys preserved.
