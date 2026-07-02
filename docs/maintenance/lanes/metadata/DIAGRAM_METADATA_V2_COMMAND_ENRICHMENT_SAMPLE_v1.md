# Diagram Metadata v2 Command Enrichment Sample v1

Status: active command-facing sample
Scope: repeatable command/help/message enrichment pattern beyond the single-row `ABOUT` proof

## Purpose

This packet extends the earlier one-row proof into a small repeatable command-facing sample.

It keeps the full structural selfdoc/design candidates unchanged.

Instead, it adds separate rows that are genuinely:

- command identities
- HELP artifact identities
- message candidates

That is the preferred enrichment pattern for the metadata lane.

## Files in this packet

- [DIAGENTITY_IMPORT_v2.command_enrichment_sample.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGENTITY_IMPORT_v2.command_enrichment_sample.csv)
- [DIAGREL_IMPORT_v2.command_enrichment_sample.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGREL_IMPORT_v2.command_enrichment_sample.csv)
- [DIAGART_IMPORT_v2.command_enrichment_sample.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGART_IMPORT_v2.command_enrichment_sample.csv)

## Commands chosen

This sample uses three commands:

- `ABOUT`
- `AREA`
- `ASCEND`

They were chosen because each already has harvested HELP artifact identity:

- `DOT|ABOUT`
- `DOT|AREA`
- `DOT|ASCEND`

and each has a reflected status artifact using the same `COMMAND_STATUS` name pattern.

## What this packet proves

### 1. Separate command rows are better than mutating structural rows

The packet does not try to force command identity into old structural rows such as:

- `SRCFILE`
- `SRCUSAGE`
- draft pages
- gates

Instead it creates new `COMMAND` rows backed by:

- `SRC_TABLE=SYSCMD`
- `SRC_KEY=CAN_NAME`
- `SRC_VALUE=<command>`

This is the correct normalization direction.

### 2. HELP enrichment is repeatable

The earlier proof packet showed `ABOUT`.

This packet shows the same pattern cleanly for:

- `ABOUT`
- `AREA`
- `ASCEND`

using:

- `SRC_TABLE=HELP_ARTIFACTS`
- `SRC_KEY=CMDKEY`
- `SRC_VALUE=DOT|...`

and relation rows that meet on `CMDKEY`.

### 3. Shared status-message candidates can be modeled without over-claiming runtime proof

The harvested HELP artifacts reuse the `NAME=COMMAND_STATUS` pattern for reflected command status rows.

This packet models that with one shared `MESSAGE` candidate entity:

- `SRC_TABLE=SYSMSG`
- `SRC_KEY=SYMBOL`
- `SRC_VALUE=COMMAND_STATUS`
- `MSG_SYMBOL=COMMAND_STATUS`

The relation rows are marked `CANDIDATE_ONLY`.

That is deliberate.

The sample proves message-shape compatibility without falsely claiming a fully proven live `SYSMSG` catalog row.

## What this packet does not claim

It does not claim:

- that every command in HELP should be promoted immediately
- that `SYSMSG` proof is complete
- that all HELP artifacts should become diagram entities

It only proves a stable pattern for the command-facing subset.

## How this fits the lane

This packet sits between:

- the single-row proof packet
- the full structural selfdoc/design candidate set

Its job is to show how a later broader command-enrichment pass should be staged:

1. add real command rows
2. add real HELP artifact rows
3. add message candidates carefully
4. keep structural rows unchanged unless they truly represent those identities

## Practical bottom line

We now have three distinct levels:

1. structural v2 candidates for the full staged lane
2. proof-sample rows for cross-family feasibility
3. a command-facing enrichment sample that demonstrates repeatable HELP/command/message staging

That is enough to move the lane forward without mixing row kinds or inventing keys.
