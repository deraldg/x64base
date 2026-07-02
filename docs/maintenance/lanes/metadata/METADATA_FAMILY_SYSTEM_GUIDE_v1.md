# Metadata Family System Guide v1

Status: active operator and maintainer guide
Scope: live `SYS*` metadata tables, metadata workspaces, schema/seed/validate scripts, `CATALOGCANARY`, catalog reader seams, `metacollect`, and the current relationship between metadata, HELP, and `CMDHELPCHK`

## Purpose

This guide explains the DotTalk++ metadata family from beginning to end:

- what the live metadata system is
- where the tables and scripts live
- how the runtime metadata lane differs from the newer collector/proposal lane
- how to open, inspect, seed, validate, and browse metadata safely
- how metadata relates to HELP, `CMDHELP`, `CMDHELPCHK`, manuals, and future localization work
- how metadata is intended to promote upward into top-level diagram/render consumers such as Mermaid and draw.io

This is the practical starting document for metadata continuity.

Companion diagram-promotion doctrine:

- [DIAGRAM_METADATA_PROMOTION_GUIDE_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_PROMOTION_GUIDE_v1.md)

## Core model

The current metadata family is split into two major lanes.

### Lane 1: Live runtime metadata catalog

This is the actual persisted metadata authority currently used by the repo runtime.

Its core assets are:

- `SYSARGS`
- `SYSCMD`
- `SYSENTVAR`
- `SYSFLDDIC`
- `SYSFUNC`
- `SYSHELP`
- `SYSMSG`
- `SYSSUBCMD`

These tables live under:

- `D:\code\ccode\dottalkpp\data\metadata`

This lane is opened through DotScript path selectors and metadata workspaces.

### Lane 2: Metadata collection / proposal lane

This is the newer read-only collector family built around `metacollect`.

Its purpose is to scan source/catalog evidence and emit normalized metadata facts for future comparison and evolution.

Its core source files are:

- [metacollect.cpp](/D:/code/ccode/src/meta/metacollect.cpp:1)
- [metacollect.hpp](/D:/code/ccode/include/dt/meta/metacollect.hpp:1)
- [metacollect_main.cpp](/D:/code/ccode/src/tools/metacollect_main.cpp:1)

Current truth:

- `metacollect` is not the live metadata storage authority
- `metacollect` is read-only
- `metacollect` is still partial/skeletal

This distinction is the main continuity rule for the metadata family.

## What metadata is intended to describe

The metadata system is broader than HELP.

The schema and surrounding doctrine show that the family is intended to model:

- commands
- subcommands
- entry variants
- aliases
- re-expressions
- functions
- messages
- help text ownership
- argument shapes
- field dictionary facts

This means metadata is a system catalog layer, not merely a help table set.

It is also intended to trickle upward into higher documentation/render layers, especially:

- Mermaid diagrams
- draw.io diagrams
- self-documentation and manual-generation layers that need structured architectural facts

## Physical layout

### Runtime path selectors

The runtime entry script is:

- [metadata.dts](/D:/code/ccode/dottalkpp/data/metadata.dts:1)

Current behavior:

- `metadata.dts` points to `data\metadata`, `indexes\metadata`, and `lmdb\metadata`
- x64 is now the default runtime, so there is no separate `metadata_x64.dts` bootstrap

### Runtime workspaces

The live metadata workspaces are:

- [metadata.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/metadata.dtschema:1)
- [metadata_rel.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/metadata_rel.dtschema:1)
- [metadata_noindex.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/metadata_noindex.dtschema:1)
- [metadata.erz](/D:/code/ccode/dottalkpp/data/workspaces/metadata.erz:1)

Important distinction:

- `metadata.dtschema` is the older lighter workspace
- `metadata_rel.dtschema` is the fuller CDX/LMDB relational workspace
- `metadata.erz` is an Ersatz browser preset rooted at `SYSCMD`

### Live DBF storage

The live DBFs are in:

- `D:\code\ccode\dottalkpp\data\metadata`

The observed tables are:

- `SYSARGS.dbf`
- `SYSCMD.dbf`
- `SYSENTVAR.dbf`
- `SYSFLDDIC.dbf`
- `SYSFUNC.dbf`
- `SYSHELP.dbf`
- `SYSMSG.dbf`
- `SYSSUBCMD.dbf`

### Live index and LMDB storage

The active index/LMDB roots are split by selected metadata lane:

- `D:\code\ccode\dottalkpp\data\indexes\metadata`
- `D:\code\ccode\dottalkpp\data\lmdb\metadata`
- `D:\code\ccode\dottalkpp\data\indexes\x64\metadata`
- `D:\code\ccode\dottalkpp\data\lmdb\x64\metadata`

### Schema / seed / validate packages

The original schema package is still present as DotScript:

- [SYSTEM_METADATA_SCHEMA_v1.dts](/D:/code/ccode/dottalkpp/data/meta/SYSTEM_METADATA_SCHEMA_v1.dts:1)

The active bundled seed/validate package documents itself here:

- [README_SYSTEM_METADATA_v4_safe10_FIXED.txt](/D:/code/ccode/dottalkpp/data/README_SYSTEM_METADATA_v4_safe10_FIXED.txt:1)

Key scripts:

- [SYSTEM_METADATA_SEED_v4_safe10_FIXED.dts](/D:/code/ccode/dottalkpp/data/scripts/SYSTEM_METADATA_SEED_v4_safe10_FIXED.dts:1)
- [SYSTEM_METADATA_VALIDATE_v4_safe10_FIXED.dts](/D:/code/ccode/dottalkpp/data/scripts/SYSTEM_METADATA_VALIDATE_v4_safe10_FIXED.dts:1)

## Runtime surfaces

### DotScript selectors

There is not currently a primary built-in `METADATA` shell command in the same sense as `HELP` or `CMDHELP`.

The real entry surface is:

- `DO METADATA`

Those are DotScript path selectors, not a compiled command family.

### Workspace surface

The metadata lane is normally opened through:

- `WORKSPACE LOAD metadata`
- `WORKSPACE LOAD metadata_rel`
- `WORKSPACE OPEN DBF`

depending on which metadata lane is active.

### `CATALOGCANARY`

The main developer consumer surface already wired to metadata is:

- [cmd_catalogcanary.cpp](/D:/code/ccode/src/cli/cmd_catalogcanary.cpp:1)

Its current doctrine is important:

- it does not open `SYSCMD` directly
- it expects DotTalk++ to have already opened `SYSCMD`
- it is an area-first consumer

Expected setup shown by the command itself:

```text
DO METADATA
WORKSPACE OPEN DBF
SELECT SYSCMD
CATALOGCANARY
```

### Catalog reader adapter

The metadata catalog reader seam is defined in:

- [catalog_reader_adapter.hpp](/D:/code/ccode/include/cli/catalog_reader_adapter.hpp:1)

Current doctrine:

- DotTalk++ proves and opens the tables
- the adapter reads an already-open `SYSCMD` area
- the adapter must not directly open DBFs
- the adapter must not compete with `USE` or `WORKSPACE`

This is a clean boundary and should be preserved.

## The live `SYS*` table family

### `SYSCMD`

Primary command catalog table.

Observed role:

- canonical command identity
- display identity
- command kind
- visibility and status
- owner
- handler
- reachability

This is the root table for the current metadata browser and canary flows.

### `SYSSUBCMD`

Subcommand and routed-surface catalog.

Observed relational role:

- child of `SYSCMD`
- stores qualified routed entries such as subcommand surfaces

### `SYSENTVAR`

Entry-variant catalog.

Observed role:

- aliases
- shortcuts
- re-expressions
- canonical help ownership mapping

### `SYSFUNC`

Function catalog table.

Observed role:

- scalar/function-like surfaces
- argument ranges
- function categories

Historical note:

- earlier evidence snapshots showed this table under-seeded or empty

### `SYSHELP`

Metadata-owned help text catalog.

Observed role:

- text ownership
- generated versus curated text distinction
- help fragments tied to metadata owners

This is one of the most important bridges between metadata and HELP-family work.

### `SYSMSG`

Message catalog table.

Observed role:

- system/user-facing messages
- severity/facility identity
- metadata ownership of messages

This table is where metadata and the newer messaging/language work eventually meet.

### `SYSARGS`

Argument-shape catalog.

Observed role:

- owner/argument relationships
- value shape
- required/repeatable semantics

### `SYSFLDDIC`

Field-dictionary facts.

Observed role:

- logical field naming
- field semantics
- reusable dictionary-style knowledge

This is a strong overlap point with `DDICT`, but it is not the same system.

## Current workspace relations

The most complete live relation workspace is:

- [metadata_rel.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/metadata_rel.dtschema:1)

Current declared relations:

1. `SYSCMD` -> `SYSSUBCMD` on canonical name to parent
2. `SYSSUBCMD` -> `SYSENTVAR` on qualified name to help owner

This means the current relational model is command-rooted and only partially expanded.

It is enough for:

- command/subcommand browsing
- variant browsing
- catalog consumer canaries

It is not yet a full metadata graph.

## Beginning-to-end runtime workflow

### Phase A: Select the metadata lane

For the shared metadata lane:

```text
DO METADATA
```

For the shared DBF plus x64 index/LMDB lane:

```text
DO METADATA
```

### Phase B: Open the workspace

For the light workspace:

```text
WORKSPACE LOAD metadata
```

For the relational workspace:

```text
WORKSPACE LOAD metadata_rel
```

For the no-relation workspace:

```text
WORKSPACE LOAD metadata_noindex
```

### Phase C: Inspect open areas

```text
WORKSPACE
DBAREAS
SELECT SYSCMD
AREA
```

### Phase D: Prove the catalog consumer boundary

```text
SELECT SYSCMD
CATALOGCANARY
```

This proves:

- the metadata workspace opened correctly
- `SYSCMD` contains readable rows
- the area-first reader boundary is intact

### Phase E: Browse relationally

The Ersatz preset already exists:

```text
ERSATZ LOAD
ERSATZ
```

using:

- [metadata.erz](/D:/code/ccode/dottalkpp/data/workspaces/metadata.erz:1)

Current preset:

- setup = `metadata`
- workspace = `metadata_rel.dtschema`
- root = `SYSCMD`

## Schema / seed / validate workflow

### Schema creation

The explicit create script is:

- [SYSTEM_METADATA_SCHEMA_v1.dts](/D:/code/ccode/dottalkpp/data/meta/SYSTEM_METADATA_SCHEMA_v1.dts:1)

Its own contract says:

- it does not set DBF / INDEXES / LMDB paths
- the environment must already be selected
- it creates x64 metadata tables

Expected sequence:

```text
DO METADATA
DO SYSTEM_METADATA_SCHEMA_v1
```

### Seeding

The stronger documented seed package is the safe10 fixed bundle:

- [SYSTEM_METADATA_SEED_v4_safe10_FIXED.dts](/D:/code/ccode/dottalkpp/data/scripts/SYSTEM_METADATA_SEED_v4_safe10_FIXED.dts:1)

Its goals are:

- safe <= 10 character field tokens
- real memo content in `SYSHELP` and notes
- real indexed readback paths

Expected sequence:

```text
DO METADATA
DO SYSTEM_METADATA_SEED_v4_safe10_FIXED
```

### Validation

The paired validation script is:

- [SYSTEM_METADATA_VALIDATE_v4_safe10_FIXED.dts](/D:/code/ccode/dottalkpp/data/scripts/SYSTEM_METADATA_VALIDATE_v4_safe10_FIXED.dts:1)

Expected sequence:

```text
DO METADATA
DO SYSTEM_METADATA_VALIDATE_v4_safe10_FIXED
```

Current validation behavior includes:

- `USE SYSCMD`
- indexed order checks
- `LIST`
- `DISPLAY`
- memo readback on help/dictionary tables

## Relationship to HELP

Metadata and HELP are related, but they are not the same system.

Current rule:

- HELP is a rendered surface
- metadata is the broader catalog/evidence authority candidate

Older doctrine captured this correctly in:

- [metadata_cmdhelpchk_boundary_doctrine_v1.md](/D:/code/ccode/dottalkpp/docs/generated/reports/metadata_cmdhelpchk_boundary_doctrine_v1.md:1)

That doctrine states:

- `CMDHELPCHK` is not the metadata system
- HELP is not the authority
- metadata is broader than HELP

Practically, that means:

- a HELP surface can be green while metadata is thin
- metadata can exist while HELP coverage is incomplete
- metadata should eventually feed or validate HELP, not be replaced by HELP

## Relationship to `CMDHELPCHK`

`CMDHELPCHK` is a validator/orchestrator lane, not metadata storage.

The correct model is:

1. metadata facts exist
2. runtime reachability is proven
3. HELP and other rendered surfaces are compared
4. `CMDHELPCHK` reports alignment or drift

That keeps storage, proof, and reporting separate.

## Relationship to manuals and selfdoc

Metadata is also an input to self-documentation and manual-generation work.

Older evidence already grouped:

- HELP DBFs
- META DBFs
- `CMDHELPCHK` reflection reports

as the primary mined evidence layer for manuals.

Reference:

- [selfdoc-help-meta-evidence-inventory-v0.1.md](/D:/code/ccode/docs/evidence/developer_manual/selfdoc-help-meta-evidence-inventory-v0.1.md:1)

That means metadata belongs below manualgen, not inside it.

## Relationship to diagram generation

Metadata is not only for command/help inspection. It is also intended to feed top-level diagram/render consumers.

Current intended upward flow is:

1. metadata captures structured system facts
2. validation/checkpoint lanes compare those facts against runtime and help surfaces
3. documentation and diagram lanes consume approved facts
4. top-level rendered outputs are produced for humans

Important target consumers include:

- Mermaid
- draw.io

This matches the existing repo direction around metadata-to-diagram tooling, including files such as:

- `D:\code\ccode\tools\diagram\generate_drawio_from_meta.py`
- `D:\code\ccode\tools\diagram\diagram_seed_contracts_v0.meta`

Practical rule:

- metadata should hold structured architectural facts
- diagram/render layers should consume those facts
- diagram files themselves should not become the primary authority when metadata can hold the normalized truth first

That is the same pattern used elsewhere:

- metadata/storage first
- generated/rendered consumer second
- validation/checkpoint between them

## Relationship to messaging and language

Metadata already has a message-facing table:

- `SYSMSG`

This matters because your larger direction is not only help coverage, but language-aware runtime selection.

Current practical implication:

- metadata can carry message identity and ownership
- the messaging system can carry localized/runtime-selected message text
- HELP can render curated or generated user-facing text

That makes metadata a classification layer, not the final multilingual rendering layer.

## The `metacollect` lane

### What it is

`metacollect` is a read-only collector that scans source/catalog evidence and emits normalized `MetaFact` rows.

Its main options already show this shape:

- `include_source_catalogs`
- `include_runtime_proof`
- `include_metadata_tables`

### What it is not

It is not currently:

- the live `SYS*` storage writer
- the main runtime metadata loader
- the primary consumer behind `HELP`

### Current value

It is still useful as:

- a source-scan collector
- an architecture staging lane
- a future comparison input for metadata-first validation

## Continuity rules

### Rule 1: Distinguish live catalog from collector proposals

Do not treat `metacollect` output as if it had already replaced the `SYS*` DBFs.

### Rule 2: Open tables through DotTalk++

The current doctrine for consumers such as `CATALOGCANARY` is correct:

- DotTalk++ opens/proves the tables
- consumers read already-open areas

Do not reintroduce direct DBF opening inside metadata readers unless that boundary is deliberately changed.

### Rule 3: Do not confuse metadata authority with rendered help

HELP output is not metadata truth by itself.

### Rule 4: Keep storage, proof, and validation separate

- storage: `SYS*` tables
- proof: runtime open/read/browse/canary
- validation: `CMDHELPCHK` and future metacheck lanes

### Rule 5: Preserve x64 workspace continuity

`metadata_rel.dtschema` and `metadata.erz` are real working assets. They should be maintained as operator-facing runtime tools, not treated as disposable experiments.

## Common failure classes

### `DO METADATA` works, but `CATALOGCANARY` fails

Check:

- current selected area
- whether `SYSCMD` is actually open
- whether the open area has the expected `SYSCMD` fields

### Workspace opens, but relations are thin

Check:

- whether you loaded `metadata.dtschema` or `metadata_rel.dtschema`
- whether index/LMDB roots match the selected metadata lane

### Seed data looks incomplete

Check:

- whether the seed package was only partially applied
- whether you are looking at old seed facts rather than regenerated data
- whether the missing concept is only present in `metacollect` proposals, not the live DBFs

### HELP disagrees with metadata

Check:

- whether the disagreement is in storage, help rendering, or checkpoint logic
- do not patch HELP blindly before classifying the layer boundary

## Canonical smoke sequences

### Live metadata lane smoke

```text
DO METADATA
WORKSPACE LOAD metadata
WORKSPACE
SELECT SYSCMD
AREA
```

### X64 relational smoke

```text
DO METADATA
WORKSPACE LOAD metadata_rel
WORKSPACE
SELECT SYSCMD
CATALOGCANARY
```

### Ersatz smoke

```text
DO METADATA
ERSATZ LOAD
ERSATZ
ERSATZ STATUS
ERSATZ GRID
```

### Schema/seed/validate sequence

```text
DO METADATA
DO SYSTEM_METADATA_SCHEMA_v1
DO SYSTEM_METADATA_SEED_v4_safe10_FIXED
DO SYSTEM_METADATA_VALIDATE_v4_safe10_FIXED
```

## What is solid today

- runtime metadata DBF lane under `data\metadata`
- DotScript lane selectors
- metadata workspaces
- x64 relational workspace
- Ersatz preset
- area-first metadata consumer doctrine
- `CATALOGCANARY` as a live developer proof surface

## What is still incomplete

- a single normalized metadata-first doctrine lane
- stronger seeding breadth, especially for functions and broader catalog coverage
- full integration between live metadata storage and `metacollect`
- clearer ownership boundaries between metadata, HELP generation, and validation
- cleaner removal or archiving of older one-off metadata proposal clutter

## Practical bottom line

If you are working in metadata, think in this order:

1. select the metadata lane
2. open the metadata workspace
3. inspect `SYSCMD` and related `SYS*` tables directly
4. prove consumers through already-open-area boundaries
5. keep HELP and `CMDHELPCHK` as consumers/checkers, not as metadata owners
6. treat Mermaid, draw.io, and manual/selfdoc layers as top-level consumers of normalized metadata
7. treat `metacollect` as the future collector/comparison lane, not the current live authority

That reflects how the repo actually works now and gives us a clean base for future metadata-first normalization.
