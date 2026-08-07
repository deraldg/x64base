# SELFDOC_INVENTORY_PROBE_PLAN_v0

Status: PLAN_ONLY  
Date: 2026-05-14  
Subsystem: SelfDoc / inventory probe planning  
Scope: read-only probe definition before CMDHELPCHK integration

## 1. Purpose

This document defines the first safe SelfDoc inventory/probe plan.

The goal is to describe a small set of read-only and report-only probes that can later inspect source contracts, HELP artifacts, metadata catalog presence, diagram catalog presence, loose tooling, generated-output homes, and data-root cleanup candidates.

This is a planning/control artifact only.

It does not implement probes. It does not wire anything into `CMDHELPCHK`. It does not move files, write DBFs, rebuild HELP DATA, repair source contracts, parse x64base DBFs generically, or promote loose scripts automatically.

## 2. Current baseline

SelfDoc tooling bootstrap is complete.

Expected baseline paths:

```text
selfdoc\
selfdoc\probes\
selfdoc\attic\
selfdoc\tool_manifest.yaml
selfdoc\pipeline_manifest.yaml
selfdoc\probes\README.md
selfdoc\attic\README.md
```

Baseline boundaries:

```text
No existing scripts moved.
No DBFs written.
CMDHELPCHK not implemented or modified.
HELP DATA untouched.
```

This plan extends the baseline only by adding this planning file:

```text
selfdoc\SELFDOC_INVENTORY_PROBE_PLAN_v0.md
```

## 3. Probe list

Proposed first probes:

```text
source_contract_inventory_probe
help_artifacts_summary_probe
metadata_catalog_presence_probe
diagram_catalog_presence_probe
loose_tooling_inventory_probe
data_root_cleanup_plan_probe
command_help_crosswalk_probe
cmdhelpchk_v2_probe
generated_output_homes_probe
```

The first six are inventory probes. The final three are bridge/planning probes that should remain non-mutating until explicitly promoted.

## 4. Probe safety class

Allowed safety classes:

```text
READ_ONLY
REPORT_ONLY
PLAN_ONLY
PROJECTION_WRITER
PATCH_WRITER
MUTATION_TOOL
```

For this phase, every proposed probe must be one of:

```text
READ_ONLY
REPORT_ONLY
PLAN_ONLY
```

No mutation tools are allowed in this phase.

| Probe | Safety class | Phase intent |
|---|---:|---|
| `source_contract_inventory_probe` | READ_ONLY | Count and classify source usage contracts and escrow candidates |
| `help_artifacts_summary_probe` | REPORT_ONLY | Summarize HELP artifact corpus without rebuilding HELP DATA |
| `metadata_catalog_presence_probe` | READ_ONLY | Check metadata catalog file/directory presence only |
| `diagram_catalog_presence_probe` | READ_ONLY | Check diagram lane file/directory presence only |
| `loose_tooling_inventory_probe` | REPORT_ONLY | Inventory loose scripts and classify them without promotion |
| `data_root_cleanup_plan_probe` | PLAN_ONLY | Dry-run classification of direct files under `data\` |
| `command_help_crosswalk_probe` | REPORT_ONLY | Compare command/help/catalog names from existing artifacts only |
| `cmdhelpchk_v2_probe` | PLAN_ONLY | Draft future validator coverage; do not implement CMDHELPCHK |
| `generated_output_homes_probe` | READ_ONLY | Confirm generated-output home directories and intended lanes |

## 5. Inputs

Global possible inputs:

```text
src\
include\
selfdoc\
docs\generated\
docs\generated\reports
docs\generated\diagrams
docs\generated\patches
docs\generated\evidence
data\help\help_artifacts.dbf
data\dbf\x64\metadata\
data\indexes\x64\metadata\
data\lmdb\x64\metadata\
user\default\diagrams\
*.ps1
*.py
*.dts
*.md
*.yaml
*.yml
*.meta
*.dtx
```

Inputs are read-only. A probe may inspect names, timestamps, sizes, extensions, and text content where safe. It must not infer unsupported row-level meaning from x64base DBFs.

## 6. Outputs

For this phase, outputs are planned only.

Allowed future report outputs:

```text
docs\generated\reports\selfdoc_source_contract_inventory_v0.md
docs\generated\reports\selfdoc_help_artifacts_summary_v0.md
docs\generated\reports\selfdoc_metadata_catalog_presence_v0.md
docs\generated\reports\selfdoc_diagram_catalog_presence_v0.md
docs\generated\reports\selfdoc_loose_tooling_inventory_v0.md
docs\generated\reports\selfdoc_data_root_cleanup_plan_v0.md
docs\generated\reports\selfdoc_command_help_crosswalk_v0.md
docs\generated\reports\selfdoc_cmdhelpchk_v2_plan_v0.md
docs\generated\reports\selfdoc_generated_output_homes_v0.md
```

No DBF outputs are allowed in this phase.

No source patches are allowed in this phase.

No automatic script movement or cleanup outputs are allowed in this phase.

## 7. What each probe may read

### 7.1 `source_contract_inventory_probe`

May read:

```text
src\**\*.cpp
src\**\*.hpp
include\**\*.hpp
include\**\*.h
```

May search for:

```text
@dottalk.usage v1
Usage:
SYNTAX
cmdhelp
command registration names
handler names
```

May classify:

```text
has @dottalk.usage v1
missing @dottalk.usage v1
possible source contract escrow candidate
possible stale/minimal usage block
generated or non-command source
```

Must treat source contracts as escrow candidates, not repair targets.

### 7.2 `help_artifacts_summary_probe`

May read:

```text
data\help\help_artifacts.dbf
data\help\
```

May summarize if safely available:

```text
KIND
SOURCE
CONFID
SEVERITY
TOPICKEY
CMDKEY
```

May report:

```text
total artifact rows
counts by KIND
counts by SOURCE
counts by CONFID
counts by SEVERITY
orphan CMDKEY count if safely available
missing or unreadable artifact corpus
```

Important: this probe must treat `help_artifacts.dbf` as the primary HELP artifact corpus, but must not use generic unsafe DBF parsing against x64base DBFs. If safe reading is not available, it must report presence and defer row-level summary.

### 7.3 `metadata_catalog_presence_probe`

May read directory/file presence only:

```text
data\dbf\x64\metadata\SYS*
data\indexes\x64\metadata\
data\lmdb\x64\metadata\
*.dtx
*.meta
```

May report:

```text
directory exists / missing
file exists / missing
file count
extension count
candidate SYS* catalog list
metadata sidecar presence
```

Must separate file/catalog presence from row-level verification.

SYS* row-level meaning is provisional until a safe metadata-aware reader exists.

### 7.4 `diagram_catalog_presence_probe`

May read directory/file presence only:

```text
docs\generated\diagrams\
user\default\diagrams\
```

May classify apparent lanes:

```text
DRAWIO SYSTEM lane
DRAWIO USER lane
unknown diagram artifact
```

May report:

```text
directory exists / missing
file count
extension count
candidate diagram names
system-lane candidates
user-lane candidates
```

Must not regenerate diagrams.

### 7.5 `data_root_cleanup_plan_probe`

May read direct entries under:

```text
data\
```

May classify as dry-run only:

```text
expected root directory
known root slot
loose file
generated artifact candidate
manual-review candidate
do-not-touch candidate
unknown
```

Must not move, delete, rename, archive, or rewrite anything.

### 7.6 `loose_tooling_inventory_probe`

May read file names and, where safe, light text headers from:

```text
*.py
*.ps1
*.bat
*.cmd
*.sh
*.dts
docs\generated\reports\*.md
selfdoc\*.yaml
selfdoc\*.md
```

May classify:

```text
probe
candidate tool
promoted tool
retired
unknown
generated report
DotScript probe
PowerShell helper
Python helper
```

Must treat loose scripts as inventory targets, not cleanup targets.

### 7.7 `generated_output_homes_probe`

May read directory presence only:

```text
docs\generated\reports\
docs\generated\diagrams\
docs\generated\patches\
docs\generated\evidence\
```

May report:

```text
directory exists / missing
recommended lane purpose
unexpected files at lane root
```

Must not create or move generated outputs during this probe phase unless a later explicit bootstrap allows directory creation.

### 7.8 `command_help_crosswalk_probe`

May read existing generated HELP/catalog artifacts only:

```text
data\help\
selfdoc\
docs\generated\reports\
```

May compare existing reflected names, topic keys, and report names if safe.

Must not rebuild HELP DATA.

Must not call `cmdhelp build`.

### 7.9 `cmdhelpchk_v2_probe`

May read:

```text
selfdoc\SELFDOC_INVENTORY_PROBE_PLAN_v0.md
selfdoc\pipeline_manifest.yaml
selfdoc\tool_manifest.yaml
docs\generated\reports\
```

May draft a future validator coverage report.

Must not modify CMDHELPCHK.

Must not add executable validator logic.

## 8. What each probe may write

For this phase, this plan file is the only required write:

```text
selfdoc\SELFDOC_INVENTORY_PROBE_PLAN_v0.md
```

Future probe implementations may write markdown reports only under:

```text
docs\generated\reports\
```

Allowed future write type:

```text
*.md report files
```

Not allowed in this phase or probe phase:

```text
*.dbf
*.cdx
*.idx
*.lmdb
source patches
moved scripts
rewritten manifests without explicit review
```

Manifest updates should be proposed in report text before being applied.

## 9. What each probe must not touch

All probes in this phase must not mutate:

```text
src\
include\
data\help\
data\dbf\
data\indexes\
data\lmdb\
user\default\diagrams\
docs\generated\diagrams\
existing scripts
existing DBFs
CMDHELPCHK implementation
command handlers
command registry
runtime dispatch
```

Specific prohibitions:

```text
Do not move files.
Do not delete files.
Do not rename files.
Do not write DBFs.
Do not rebuild HELP DATA.
Do not run cmdhelp build.
Do not repair source contracts.
Do not use generic DBF parsing against x64base DBFs.
Do not promote loose scripts automatically.
Do not implement CMDHELPCHK.
Do not regenerate diagrams.
```

## 10. Promotion criteria from probe to tool

A probe may be considered for promotion to a tool only after all criteria are met:

1. It is read-only or report-only in practice.
2. It has a stable input list.
3. It has a stable markdown report format.
4. It has deterministic output for the same repository state.
5. It has explicit refusal behavior for unsafe inputs.
6. It does not parse x64base DBFs generically.
7. It does not require command-shell side effects.
8. It can be run from repo root.
9. It has a manifest entry proposed and reviewed.
10. It has at least one reviewed sample output.

Promotion states:

```text
probe
candidate tool
promoted tool
retired
unknown
```

No loose script should be promoted automatically based on location or filename.

## 11. Manifest update recommendations

`selfdoc\tool_manifest.yaml` should eventually describe stable tools only.

Recommended future fields:

```yaml
schema_version: 0.1
kind: selfdoc_tool_manifest
status: active
tools:
  - name: source_contract_inventory_probe
    safety_class: REPORT_ONLY
    entrypoint: selfdoc/probes/source_contract_inventory_probe.ps1
    inputs:
      - src
      - include
    outputs:
      - docs/generated/reports/selfdoc_source_contract_inventory_v0.md
    writes_dbf: false
    mutates_source: false
    modifies_cmdhelpchk: false
```

`selfdoc\pipeline_manifest.yaml` should eventually describe reviewed pipeline stages only.

Recommended future fields:

```yaml
schema_version: 0.1
kind: selfdoc_pipeline_manifest
status: draft
pipelines:
  - name: selfdoc_inventory_v0
    mode: report_only
    stages:
      - source_contract_inventory_probe
      - help_artifacts_summary_probe
      - metadata_catalog_presence_probe
      - diagram_catalog_presence_probe
      - loose_tooling_inventory_probe
      - data_root_cleanup_plan_probe
      - command_help_crosswalk_probe
      - cmdhelpchk_v2_probe
```

For this plan step, do not update manifests automatically unless a separate reviewed patch is requested.

## 12. Pipeline order recommendation

Recommended future order:

```text
1. source_contract_inventory_probe
2. help_artifacts_summary_probe
3. metadata_catalog_presence_probe
4. diagram_catalog_presence_probe
5. loose_tooling_inventory_probe
6. data_root_cleanup_plan_probe
7. command_help_crosswalk_probe
8. cmdhelpchk_v2_probe
```

Rationale:

1. Start with source contract inventory because it is text-only and low risk.
2. Summarize HELP artifacts next to compare source contracts with generated HELP facts.
3. Check metadata catalog presence before row-level semantics.
4. Check diagrams as catalog presence only.
5. Inventory loose tools before any cleanup planning.
6. Classify data-root cleanup candidates as dry-run only.
7. Crosswalk command/help names only after inventories exist.
8. Defer CMDHELPCHK v2 until the inputs, reports, and categories are stable.

`generated_output_homes_probe` may run before all report-writing probes as a preflight check, but it should not create directories without a separate explicit bootstrap request.

## 13. Acceptance criteria

This plan is complete when:

1. `selfdoc\SELFDOC_INVENTORY_PROBE_PLAN_v0.md` exists.
2. It clearly defines the read-only probes.
3. It states inputs and outputs for each probe.
4. It states what each probe must not mutate.
5. It separates file/catalog presence from row-level verification.
6. It treats `data\help\help_artifacts.dbf` as a primary HELP artifact corpus.
7. It treats SYS* row-level meaning as provisional.
8. It treats source contracts as escrow candidates, not repair targets yet.
9. It identifies loose scripts as inventory targets, not cleanup targets.
10. It does not implement CMDHELPCHK.
11. It does not write DBFs.
12. It does not rebuild HELP DATA.
13. It does not move files.
14. It does not repair source contracts.
15. It does not promote loose scripts automatically.
