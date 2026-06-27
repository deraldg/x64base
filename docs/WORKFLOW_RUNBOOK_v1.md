# WORKFLOW_RUNBOOK_v1

Status: DRAFT  
Project root: `D:\code\ccode`

## Purpose

This runbook turns the family workflow doctrine into operator steps.

It is the execution companion to:

- `docs/HELP_METADATA_SELFDOC_WORKFLOW_v1.md`
- `selfdoc/SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0.md`
- `selfdoc/tool_manifest.yaml`
- `selfdoc/pipeline_manifest.yaml`

This runbook focuses on the current practical lane:

```text
source/runtime
  -> HELP
  -> metadata collection and reviewed promotion
  -> SelfDoc provenance
  -> manual/diagram promotion
```

## Operating doctrine

Use these rules during execution:

1. Runtime proves.
2. Source defines.
3. HELP explains.
4. Metadata organizes.
5. CMDHELPCHK validates.
6. SelfDoc preserves provenance.
7. Manuals and diagrams are promoted attached views.

## Safety modes

There are only two normal execution modes in this family.

### 1. Report-only mode

Allowed:

- build
- runtime smoke
- HELP inspection
- `metacollect` report/candidate export
- SelfDoc manifest/policy updates
- manual and diagram drafting

Not allowed:

- live metadata mutation unless separately reviewed

### 2. Reviewed mutation mode

Allowed only after explicit review:

- metadata DBF replacement/import
- HELP DBF rebuild
- index rebuild for promoted tables

## Runtime roots and launch model

### Development/runtime root

Primary dev/runtime root:

- `D:\code\ccode\dottalkpp`

Primary launcher:

- [datarun.ps1](D:/code/ccode/datarun.ps1)

Current `datarun.ps1` behavior:

- copies `build\src\Release\dottalkpp.exe` to `dottalkpp\bin\dottalkpp.exe`
- runs from `dottalkpp\data`
- app root becomes `D:\code\ccode\dottalkpp`

### Basic build

From `D:\code\ccode`:

```powershell
cmake --build D:\code\ccode\build --config Release --target dottalkpp
```

### Basic runtime launch

Interactive:

```powershell
.\datarun.ps1
```

Non-interactive example:

```powershell
.\datarun.ps1 -CommandLines @(
  'DO x64',
  'QUIT'
)
```

## Lane entry scripts

Current lane bootstrap scripts under `dottalkpp\data`:

- [x64.dts](D:/code/ccode/dottalkpp/data/x64.dts)
- [cmdhelp.dts](D:/code/ccode/dottalkpp/data/cmdhelp.dts)
- [metadata.dts](D:/code/ccode/dottalkpp/data/metadata.dts)
- [manuals.dts](D:/code/ccode/dottalkpp/data/manuals.dts)

Current meanings:

- `DO x64`
  - sets `DBF`, `INDEXES`, and `LMDB` to the x64 lane
- `DO cmdhelp`
  - points DBF/INDEXES/LMDB to the HELP lane
  - opens help DBFs with `WORKSPACE OPEN DBF CDX`
- `DO metadata`
  - points DBF/INDEXES/LMDB to the metadata lane
- `DO manuals`
  - points DBF/INDEXES/LMDB to the manuals lane
  - opens manual DBFs with `WORKSPACE OPEN DBF CDX`

## Standard operator sequences

### Sequence A: Build and prove runtime

Use when:

- source changed
- command behavior changed
- help wording changed and must be runtime-checked

Steps:

1. Build the runtime.
2. Run `.\datarun.ps1`.
3. Smoke the affected command/function.
4. Record whether runtime proof is green.

Minimum commands:

```text
DO x64
<target command smoke>
QUIT
```

Acceptance:

- build succeeds
- runtime starts cleanly
- affected command/function behavior matches expectation

### Sequence B: Inspect HELP lane

Use when:

- reviewing help tables
- checking current command/topic surfaces
- validating that HELP DBFs open

Interactive sequence:

```text
DO cmdhelp
WORKSPACE
DBAREAS
```

Acceptance:

- HELP tables open
- command/topic/section/line/artifact families are visible

## HELP rebuild rules

### Current `CMDHELP` surface

Current supported command forms include:

- `CMDHELP`
- `CMDHELP USAGE`
- `CMDHELP BUILD`
- `CMDHELP BUILD V2`
- `CMDHELP BUILD LEGACY`
- `CMDHELP LEGACY`

Current source contract states:

- `CMDHELP BUILD` writes the current HELP DATA DBFs
- `CMDHELP BUILD V2` is a compatibility alias for `CMDHELP BUILD`
- `CMDHELP BUILD LEGACY` drives the old `commands.dbf` / `cmd_args.dbf` path

### Build order rule

Current documented operator rule:

1. If `dotref.hpp` changed, run `CMDHELP BUILD LEGACY` first.
2. Then run `CMDHELP BUILD`.
3. If source/help contracts changed but `dotref.hpp` did not, run `CMDHELP BUILD`
   without the legacy scan first.

This rule is documented in prior manualgen evidence and is treated here as the
current build-order policy.

### HELP rebuild sequence

Use when:

- command contracts changed
- source header help changed
- `dotref.hpp` changed
- command surface/help drift must be repaired

Interactive sequence:

```text
DO cmdhelp
CMDHELP BUILD LEGACY   <only when dotref.hpp changed>
CMDHELP BUILD
```

Post-check:

```text
DO cmdhelp
WORKSPACE
```

Acceptance:

- HELP build completes
- HELP tables reopen
- current help surface reflects expected commands/topics

## CMDHELPCHK position

`CMDHELPCHK` is a validator lane, not a build lane.

Use it:

- after HELP and command catalog changes
- when checking consistency/drift

Do not use it as:

- runtime proof
- source ownership replacement
- metadata authority

Run it after:

- runtime proof is acceptable
- HELP rebuild is complete

## Metadata collection sequence

### Current collector

Current read-only collector:

- `build\Release\metacollect.exe`

Current documented outputs:

- `metacollect_facts.csv`
- `metacollect_compare.csv`
- `dottalkpp\data\scripts\metadata\SYSFUNC_IMPORT_v1.csv`
- `dottalkpp\data\scripts\metadata\SYSARGS_IMPORT_v1.csv`

### Report-only metadata collection

Use when:

- source contracts changed
- function/argument catalogs changed
- candidate metadata exports need refresh

From `D:\code\ccode`:

```powershell
.\build\Release\metacollect.exe D:\code\ccode > metacollect_facts.csv
.\build\Release\metacollect.exe D:\code\ccode --compare --compare-out metacollect_compare.csv > $null
.\build\Release\metacollect.exe D:\code\ccode --sysfunc-import-out dottalkpp\data\scripts\metadata\SYSFUNC_IMPORT_v1.csv > $null
.\build\Release\metacollect.exe D:\code\ccode --sysargs-import-out dottalkpp\data\scripts\metadata\SYSARGS_IMPORT_v1.csv > $null
```

Optional diagnostic export:

```powershell
.\build\Release\metacollect.exe D:\code\ccode --include-dev-commands --sysargs-include-keywords --sysargs-import-out dottalkpp\data\scripts\metadata\SYSARGS_IMPORT_v1_full.csv > $null
```

Acceptance:

- collector runs without mutating DBFs
- candidate CSVs refresh
- facts/compare reports are produced

## Metadata promotion sequence

### Current promotion state

Current status by artifact:

- `SYSCMD`
  - reviewed runnable DotScript exists
- `SYSFUNC`
  - proposal text exists
  - not yet documented here as reviewed runnable promotion
- `SYSARGS`
  - proposal text exists
  - not yet documented here as reviewed runnable promotion

Current reviewed scripts:

- [SYSCMD_NATIVE_CREATE_IMPORT_v1.RUN_METADATA_REVIEWED.dts](D:/code/ccode/dottalkpp/data/scripts/metadata/SYSCMD_NATIVE_CREATE_IMPORT_v1.RUN_METADATA_REVIEWED.dts)
- [SYSCMD_READBACK_v1.dts](D:/code/ccode/dottalkpp/data/scripts/metadata/SYSCMD_READBACK_v1.dts)

Current proposal-only artifacts:

- [SYSFUNC_NATIVE_CREATE_IMPORT_v1.proposal.txt](D:/code/ccode/dottalkpp/data/scripts/metadata/SYSFUNC_NATIVE_CREATE_IMPORT_v1.proposal.txt)
- [SYSARGS_NATIVE_CREATE_IMPORT_v1.proposal.txt](D:/code/ccode/dottalkpp/data/scripts/metadata/SYSARGS_NATIVE_CREATE_IMPORT_v1.proposal.txt)

### Reviewed metadata mutation sequence

Use only after explicit review.

Interactive sequence:

```text
DO metadata
DO scripts\metadata\SYSCMD_NATIVE_CREATE_IMPORT_v1.RUN_METADATA_REVIEWED
DO scripts\metadata\SYSCMD_READBACK_v1
```

Acceptance:

- metadata lane paths are correct
- target table is created/imported as reviewed
- readback succeeds

### Important current limitation

Do not imply `SYSFUNC` and `SYSARGS` are live reviewed mutation lanes yet unless
their reviewed runnable import scripts are added and accepted.

At the moment, they are part of:

- report-only collection
- proposal review

not fully documented reviewed mutation in this runbook.

## SelfDoc update sequence

Use when:

- adding a helper tool
- changing pipeline steps
- changing lane doctrine

Current canonical files:

- `selfdoc/tool_manifest.yaml`
- `selfdoc/pipeline_manifest.yaml`
- `selfdoc/SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0.md`

Operator steps:

1. Update policy doc if the boundary changes.
2. Update tool manifest if tool identity/outputs change.
3. Update pipeline manifest if execution steps change.
4. Keep helper tools classified as report-only unless mutation is explicitly
   intended and reviewed.

Acceptance:

- helper tool role is documented
- inputs/outputs are declared
- non-authority boundaries are explicit

## Manual promotion sequence

Use when:

- help and metadata evidence are good enough to assemble prose
- SelfDoc provenance exists

Manual lane principle:

- manual assembly may read HELP, metadata, CMDHELPCHK, source, and SelfDoc
- manual assembly does not replace their authorities

Operator sequence:

1. Confirm source/runtime evidence.
2. Confirm HELP evidence.
3. Confirm metadata evidence.
4. Confirm SelfDoc provenance.
5. Draft or promote manual sections.

Acceptance:

- manual claims are traceable
- no manual text silently replaces runtime/source truth

## Diagram promotion sequence

Use when:

- entities, flows, and joins are stable enough to visualize

Preferred sources:

- reviewed metadata rows
- reviewed help/manual crosswalks
- reviewed SelfDoc provenance

Preferred outputs:

- Mermaid
- Draw.io

Rule:

- diagrams should attach to manuals or system docs
- diagrams should not become the only authority

Acceptance:

- node/entity names use stable canonical IDs
- localized labels can be layered later

## Language and region checkpoints

Even when only English is seeded, check these seams during workflow changes:

- stable canonical IDs remain locale-neutral
- metadata rows can carry `DEF_LOCALE` and `REGION_ID`
- HELP/manual promotion can support localized variants later
- message-routing changes do not hard-code shell output unnecessarily

Current default seam examples:

- `DEF_LOCALE = en-US`
- `REGION_ID = GLOBAL`

## Artifact homes

Current important homes:

- runtime/help data:
  - `dottalkpp\data\help`
- metadata data:
  - `dottalkpp\data\metadata`
- metadata candidate CSVs:
  - `dottalkpp\data\scripts\metadata`
- SelfDoc manifests/policies:
  - `selfdoc\`
- family workflow docs:
  - `docs\`
- manuals:
  - `docs\manuals\developer\manualgen\`

## Daily operator checklist

Use this order:

1. Build the runtime.
2. Prove runtime behavior for changed commands/functions.
3. Rebuild HELP if source/help contracts changed.
4. Run `CMDHELPCHK` when consistency validation is needed.
5. Refresh metadata candidates with `metacollect`.
6. Promote metadata only through reviewed mutation steps.
7. Update SelfDoc if tool/pipeline boundaries changed.
8. Promote manuals/diagrams only from reviewed evidence.

## Summary

This runbook keeps the lanes in the right order:

```text
prove in runtime
  -> explain in HELP
  -> organize in metadata
  -> preserve provenance in SelfDoc
  -> promote into manuals and diagrams
```

Current key boundary:

- `metacollect` is read-only collection/proposal support
- `SYSCMD` currently has a reviewed runnable metadata import path
- `SYSFUNC` and `SYSARGS` currently remain proposal-driven until their reviewed
  import scripts are promoted
