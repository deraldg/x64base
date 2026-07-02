# Diagram Metadata v2 Message Enrichment Boundary v1

Status: active boundary note
Scope: when `MSG_ID` and `MSG_SYMBOL` may be promoted into diagram metadata v2 rows

## Purpose

This note records the current hard boundary for message enrichment in the diagram metadata lane.

The message lane is real.

But real does not mean fully seeded.

The correct rule today is:

- promote message identity only when a concrete `SYSMSG` / `SYSTEM_MESSAGES` row is proven
- keep message identity candidate-only when the symbol is inferred from HELP/status text patterns rather than a proven current message row

## What is proven now

### 1. The schema is real

The compact metadata schema defines `SYSMSG -> SYSTEM_MESSAGES` with fields including:

- `MSG_ID`
- `SYMBOL`
- `ENUM_NAME`
- `SEVERITY`
- `FACILITY`
- `SHORT_TXT`
- `IMPL_STAT`
- `VIS_TIER`
- `OWNER`
- `SRC_AUTH`
- `SRC_FILE`

Schema proof:

- [SYSTEM_METADATA_SCHEMA_v4_safe10_FIXED.dts](/D:/code/ccode/dottalkpp/data/scripts/SYSTEM_METADATA_SCHEMA_v4_safe10_FIXED.dts)

### 2. The workspace lane is real

The metadata workspaces already carry `SYSMSG.dbf` as a real lane surface.

Examples:

- `metadata.dtschema`
- `metadata_rel.dtschema`
- `MYHELP.dtschema`

This means message identity is not hypothetical architecture. It has a real runtime/storage lane.

### 3. The current seed proof is sparse

The strongest directly readable seeded proof in the current metadata seed material is:

- `MESSAGE_ID=MSG_METADATA_SEED_OK`
- `SYMBOL=METADATA_SEED_OK`

Seed proof:

- [SYSTEM_METADATA_SEED_v2.dts](/D:/code/ccode/dottalkpp/data/scripts/SYSTEM_METADATA_SEED_v2.dts)

The seed itself explicitly says:

- this is a seed message row only
- it is not yet a runtime message enum

That is an important boundary.

## What is not proven enough yet

The command-facing diagram sample uses:

- `MSG_SYMBOL=COMMAND_STATUS`

That symbol is visible in harvested HELP artifacts as the `NAME` for reflected status rows.

But that does not yet prove a current promoted `SYSMSG` row with:

- `MSG_ID`
- `SYMBOL=COMMAND_STATUS`
- stable runtime ownership and seeded metadata proof

Result:

- `COMMAND_STATUS` remains a message-shape candidate
- it must not be overstated as full current metadata truth

## Crosswalk caution

The lane must preserve the distinction between:

- `SYSMSG` as the current compact metadata feeder
- `SYSTEM_MESSAGES` as a legacy or alternate long-form schema name

Those names should be crosswalked carefully, not collapsed casually.

This boundary matters especially when manual prose, HELP artifacts, message catalog work, and metadata seeds all refer to the message family differently.

## Promotion rule

Use this rule during future enrichment:

1. If a symbol is only visible through HELP status/error/warning naming, stage it as a candidate.
2. If a symbol is backed by a concrete seeded or harvested `SYSMSG` row, it may carry `MSG_SYMBOL`.
3. If both symbol and stable row identity are present, it may also carry `MSG_ID`.
4. If the only direct proof is sparse seed material, preserve the row but describe it as seed proof, not complete runtime catalog proof.

## Current status

Current state is:

- message schema: proven
- message workspace/storage lane: proven
- message seed existence: proven
- broad typed runtime catalog population: not yet proven
- `COMMAND_STATUS` as current concrete `SYSMSG` truth: not yet proven

## Practical bottom line

For diagram metadata v2 today:

- `METADATA_SEED_OK` is a better example of current seeded message identity than `COMMAND_STATUS`
- `COMMAND_STATUS` is still valid as a command/help crosswalk candidate
- `MSG_ID` should remain blank on candidate-only rows
- message enrichment should stay selective until the `SYSMSG` lane is denser and better harvested
