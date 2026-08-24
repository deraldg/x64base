# DEV-14 HELP, Metadata, and CMDHELPCHK

```yaml
page_id: DEV-14
title: HELP, Metadata, and CMDHELPCHK
status: DRAFT
last_verified: 2026-07-08
```

## Center of gravity

HELP and META are not side documentation. They are mined SelfDoc evidence stores
used by the documentation family.

The important correction is that this family is no longer just:

```text
source -> CMDHELP -> manual
```

It is now understood as a layered producer stack:

- source and curated reference headers define the candidate truth inventory
- HELP DATA and legacy HELP lanes explain and preserve command surfaces
- CMDHELPCHK validates reflected structure and catalog drift
- `dt_meta.lib` and `metacollect.exe` harvest read-only metadata facts outside
  the shell runtime
- `manualgen.py` assembles inventory, validation, manifests, and publication
  workspaces from the same evidence spine

That distinction matters because manuals and website pages must derive from the
same reviewed evidence set without pretending that one tool does every job.

## Core doctrine

Use this doctrine consistently:

- runtime proves behavior
- source defines implementation and subsystem ownership
- HELP explains command behavior, vocabulary, examples, and concepts
- metadata organizes identities, arguments, ownership, and relationships
- CMDHELPCHK validates structural alignment and catches drift
- SelfDoc preserves provenance and evidence lineage
- manualgen assembles reviewable publication artifacts

Safe wording:

- HELP/META/CMDHELPCHK-first is assembly order
- it is not authority order
- source is not demoted to a sidecar
- runtime proof is still required for behavior claims

Verified HELP DATA rebuild on 2026-07-07 used:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Observed current HELP DATA evidence from that verified run:
- line rows: `10846`
- topics: `473`

Observed legacy compatibility evidence from that verified run:
- `commands.dbf` rows written: `447`
- `cmd_args.dbf` rows written: `2294`

Observed META evidence:
- META.SYSCMD: 40 records
- META.SYSSUBCMD: 12 records
- META.SYSENTVAR: 12 records
- META.SYSFUNC: 0 records in the observed seed
- META.SYSHELP: 8 records

Observed release-build documentation toolchain outside `dottalkpp`:

- `dt_meta.lib`
- `metacollect.exe`

Observed manual assembly toolchain:

- `tools/manualgen/manualgen.py`

## HELP tables

`CMD_ARGS`, `COMMANDS`, `HELP_ARTIFACTS`, `HELP_LINE`, `HELP_SECTION`, `HELP_TOPIC`.

## META tables

`SYSARGS`, `SYSCMD`, `SYSENTVAR`, `SYSFLDDIC`, `SYSFUNC`, `SYSHELP`, `SYSMSG`, `SYSSUBCMD`.

## CMDHELPCHK role

CMDHELPCHK validates reflected command/function metadata and HELP artifact paths.

Observed result from the verified 2026-07-07 run:

```text
Structural Checks
=================
OK no structural issues found
```

## Practical rebuild rule

Current practical order is:

1. `CMDHELP BUILD LEGACY` when `dotref.hpp` changed
2. `CMDHELP BUILD . d:\code\ccode\src` for the richer current HELP DATA pass
3. `CMDHELPCHK` to validate reflected structure

The explicit source-root build is important because it harvested:

- `REGISTRY`
- `DOTREF`
- `FOXREF`
- `EDREF`
- `SHARED_MSG`
- `SOURCE_MINER`
- `USAGE_CONTRACT`

## Producer roles

### HELP lane

HELP is the strongest explanatory feeder.

It explains:

- command vocabulary
- usage shapes
- examples
- operator concepts
- artifact lineage now stored in HELP DATA

HELP can be broad and richly populated without proving runtime behavior.

### Metadata lane

Metadata organizes the system semantically.

It is the right lane for:

- command identity
- argument identity
- message identity
- environment variables
- feeder relationships
- future diagram and website attachment points

Sparse metadata is not the same as failed metadata. Sparse tables are future
feeders until seeded and verified.

### CMDHELPCHK lane

CMDHELPCHK is a validator, not a behavior proof engine.

It is responsible for:

- structural reflection checks
- HELP/catalog drift checks
- artifact validation
- manual assembly gates where reflected structure matters

### External metadata lane

The release build proves there are documentation producers outside the shell:

- `dt_meta.lib` supplies read-only extraction support
- `metacollect.exe` is the standalone developer entrypoint for metadata/source
  extraction, compare reports, and seed-export CSV generation

These belong in the documentation family and must not be hidden behind a
runtime-only mental model.

### Manualgen lane

`manualgen.py` assembles inventories, validation reports, manifests, dry-run
artifacts, and publication workspaces.

Its role is assembly, not authority replacement.

## Mutation boundaries

These lanes must stay role-clean:

- HELP build mutates HELP DATA and legacy HELP compatibility lanes only when
  explicitly invoked
- CMDHELPCHK is report-only
- `dt_meta.lib` and `metacollect.exe` are read-only/report-only by contract
- `manualgen.py` writes reports and manual artifacts, not runtime HELP/META
  production data

This boundary keeps publication work from silently mutating runtime truth.

## Crosswalk artifacts

Current working crosswalks:

```text
docs/manuals/developer/manualgen/reports/help_meta_toolchain_crosswalk_v1.csv
docs/manuals/developer/manualgen/reports/help-topic-to-manual-section-map-v1.csv
docs/manuals/developer/manualgen/reports/manualgen-evidence-harvest-checklist-v1.md
```

Use them in this order:

1. toolchain crosswalk to identify producer roles
2. topic-to-section map to place families into manual chapters
3. evidence harvest checklist to repeat the rebuild/validation sequence

## Central rule

HELP is broad and richly populated. META is semantic and seeded but narrower.
CMDHELPCHK validates reflected structure. Source verifies. Runtime proves.
