# HELP_METADATA_SELFDOC_WORKFLOW_v1

Status: DRAFT
Project root: `D:\code\ccode`

## Purpose

This document defines the current canonical workflow for the DotTalk++ / x64base
help, metadata, SelfDoc, manual, and diagram family.

It answers:

- what each lane owns
- what each lane may read
- what each lane may write
- how evidence is promoted from source/runtime into user-facing documentation
- where language and region support must exist even when only English is seeded

This document is policy and workflow guidance. It is not a replacement for
runtime commands, DBF schemas, or manifest files.

## Core doctrine

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
Manuals and diagrams are promoted views, not authority.
External tools may assist, but they are not authority by default.
```

## Family overview

The family currently has six major lanes:

1. Source/runtime lane
2. Help lane
3. Metadata lane
4. SelfDoc lane
5. Manual promotion lane
6. Diagram promotion lane

The intended flow is:

```text
source headers/comments/contracts/runtime registration
  -> HELP extraction / explanation surfaces
  -> metadata collection / normalization / candidate export
  -> reviewed live metadata promotion
  -> SelfDoc provenance and inventory
  -> manuals and diagrams as promoted, attached views
```

## Lane authorities

### 1. Source/runtime lane

Primary inputs:

- `src/`
- `include/`
- runtime command registration
- function registration
- source comments and file headers

Authority:

- command existence
- function existence
- actual runtime behavior
- source comment truth
- usage-contract truth when implemented in code

Non-authority:

- not the user-facing help publication layer
- not the metadata organization layer
- not the manual layout layer

Key rule:

If runtime and docs disagree, runtime behavior wins until docs are repaired.

### 2. Help lane

Primary surfaces:

- runtime `HELP`
- `cmdhelp`
- help DBF families under `dottalkpp/data/help`
- command/topic/section/line/artifact collections

Authority:

- user-facing explanation surface
- command help wording
- organized topic presentation

Non-authority:

- does not prove command existence by itself
- does not replace source/runtime truth
- does not replace live metadata

Key rule:

HELP explains what runtime and source define; it does not invent reality.

### 3. Metadata lane

Primary surfaces:

- metadata DBFs under `dottalkpp/data/metadata`
- candidate CSVs under `dottalkpp/data/scripts/metadata`
- reviewed import scripts and proposals

Authority:

- organized machine-readable catalogs
- normalized identifiers
- cross-lane join points
- future promotion inputs for manuals and diagrams

Non-authority:

- not proof of command existence by itself
- not a substitute for HELP
- not a substitute for runtime validation

Key rule:

Metadata is the organizing layer, not the proving layer.

### 4. SelfDoc lane

Primary surfaces:

- `selfdoc/tool_manifest*.yaml`
- `selfdoc/pipeline_manifest*.yaml`
- SelfDoc policy documents
- reviewed workflow/provenance packets

Authority:

- provenance
- tool inventory
- pipeline inventory
- lane boundary documentation
- evidence preservation

Non-authority:

- does not replace live metadata
- does not replace HELP
- does not mutate DBFs by default

Key rule:

SelfDoc records how work is done and what helper tools exist; it is not the
schema or runtime authority.

### 5. Manual promotion lane

Primary surfaces:

- `docs/manuals/developer/manualgen/...`
- generated draft sections
- review packets and work orders

Authority:

- curated long-form explanation
- promoted prose views
- attached cross-lane narrative

Non-authority:

- does not override runtime truth
- does not replace HELP or metadata
- should not duplicate facts that can be attached from metadata/diagrams

Key rule:

Manuals are promoted narrative views assembled from reviewed evidence.

### 6. Diagram promotion lane

Primary surfaces:

- Mermaid
- Draw.io
- future system/data-flow/entity-relationship diagrams

Authority:

- promoted structural views
- attached explanatory visuals

Non-authority:

- not the data authority
- not the runtime authority
- not a substitute for metadata tables

Key rule:

Diagrams should be attached to manuals and documentation, not embedded as the
only source of truth.

## End-to-end workflow

### Stage A: Define and prove in source/runtime

Inputs:

- command implementations
- function implementations
- source header comments
- runtime registration
- usage contracts

Expected outputs:

- executable behavior
- source comments
- callable command/function surfaces

Gate:

- build green
- runtime command/function actually exists

### Stage B: Explain in HELP

Inputs:

- source/runtime truth
- command help code
- help tables and command-argument tables

Expected outputs:

- `HELP`
- `cmdhelp`
- topic/section/line/artifact surfaces

Gate:

- command help aligns with runtime
- topic tables can be loaded
- help rebuild and review steps complete

### Stage C: Collect and normalize in metadata

Inputs:

- source contracts
- runtime catalogs
- existing metadata DBFs
- help-derived evidence when appropriate

Expected outputs:

- normalized candidate CSVs
- compare/facts reports
- reviewed import proposals

Gate:

- collection is read-only
- candidate output is repeatable
- promotion is still separate from collection

### Stage D: Review and promote into live metadata

Inputs:

- candidate CSVs
- reviewed proposal text
- human decision

Expected outputs:

- live metadata DBF rows
- CDX/LMDB rebuild where needed

Gate:

- reviewed authorization exists
- schema shape is verified
- import/rebuild path is explicit

### Stage E: Preserve provenance in SelfDoc

Inputs:

- tool identities
- pipeline steps
- reports
- policy boundaries

Expected outputs:

- tool manifest entries
- pipeline manifest entries
- workflow policies
- review packets

Gate:

- helper tool boundaries are documented
- authority and non-authority are explicit

### Stage F: Promote into manuals and diagrams

Inputs:

- reviewed help
- reviewed metadata
- reviewed SelfDoc provenance

Expected outputs:

- manual sections
- attached system diagrams
- attached data-flow and entity-relationship views

Gate:

- promoted view is traceable to reviewed evidence
- diagrams attach to manuals instead of becoming standalone truth

## Current position of `metacollect`

`metacollect` belongs in Stage C.

It is currently:

- a read-only collector
- a comparison/report tool
- a canonical candidate CSV emitter for metadata seeding

It is currently not:

- a live DBF writer
- a HELP rebuild tool
- a `CMDHELPCHK` replacement
- a manual publisher

Current documented artifacts include:

- `metacollect_facts.csv`
- `metacollect_compare.csv`
- `dottalkpp/data/scripts/metadata/SYSFUNC_IMPORT_v1.csv`
- `dottalkpp/data/scripts/metadata/SYSARGS_IMPORT_v1.csv`

Current documented policy references:

- `selfdoc/SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0.md`
- `selfdoc/tool_manifest.yaml`
- `selfdoc/pipeline_manifest.yaml`

## Current position of live metadata

Live metadata is the reviewed organized lane used for later promotion upward.

Its intended use includes:

- command catalogs
- function catalogs
- argument catalogs
- future diagram inputs
- future manual attachment inputs

Its intended non-use includes:

- proving runtime truth without source/runtime support
- silently replacing help wording

## Language and region seams

Language and region support must exist across the whole family, even if English
is the only currently seeded content in many lanes.

### Required cross-family concepts

- `DEF_LOCALE`
- `REGION_ID`
- stable canonical identifiers independent of localized display text

### Where locale must matter now

1. Messaging/output lane
   - user-facing shell output should migrate away from hard-coded `cout`
   - command messages should resolve through message-aware routing where possible

2. Metadata lane
   - metadata rows should carry locale/region seams now, even if seeded with
     `en-US` and `GLOBAL`

3. Help/manual lane
   - help topics, sections, lines, and manuals should be promotable to localized
     variants later

4. Diagram lane
   - diagram nodes should prefer canonical IDs and attach localized labels later

### Where locale does not need to dominate

- source comments may remain English-only when they are intrinsic to source
  maintenance and code collection

Key rule:

Canonical IDs stay stable; display language is layered on top.

## Promotion gates by lane boundary

### Source/runtime -> HELP

Required:

- real command/function exists
- help wording matches current syntax/behavior

### HELP -> metadata

Required:

- help evidence is harvested or mapped explicitly
- metadata row purpose is clear
- duplication is avoided where metadata can reference rather than copy

### Source/runtime -> metadata via `metacollect`

Required:

- read-only scan only
- candidate output labeled as candidate/evidence
- human review before import

### Metadata -> SelfDoc

Required:

- provenance preserved
- source of candidate/import/report is explicit
- helper tool boundary documented

### Metadata/SelfDoc -> manuals

Required:

- promoted prose is review-backed
- manual sections cite the correct evidence lane

### Metadata/SelfDoc -> diagrams

Required:

- entities/flows come from reviewed metadata
- diagrams remain attached promoted views

## Practical operating rules

1. Do not let external helpers become silent authorities.
2. Do not let manuals duplicate facts that metadata or diagrams can attach on
   demand.
3. Do not let metadata pretend to prove runtime behavior.
4. Do not let HELP drift from actual command/function syntax.
5. Do not force language retrofits later when schema seams can be installed now.

## Recommended next documents

This workflow document is the family-level map. The next useful supporting
documents are:

1. `docs/WORKFLOW_RUNBOOK_v1.md`
2. `docs/LANGUAGE_AND_REGION_SEAMS_v1.md`
3. `docs/HELP_LANE_POLICY_v1.md`
4. `docs/METADATA_LANE_POLICY_v1.md`
5. `docs/MANUAL_DIAGRAM_PROMOTION_POLICY_v1.md`

## Summary

The current intended family is:

```text
source/runtime truth
  -> HELP explanation
  -> metadata organization and candidate collection
  -> reviewed live metadata
  -> SelfDoc provenance
  -> manuals and diagrams as promoted attached views
```

`metacollect` now has a documented place in that chain.

The next job is not to redefine the family again, but to add the operator
runbook and the language/region policy so execution and localization stay
aligned with this workflow.
