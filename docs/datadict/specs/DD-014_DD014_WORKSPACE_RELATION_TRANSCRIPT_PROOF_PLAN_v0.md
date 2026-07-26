# DD-014 Workspace / Relation / Tuple Transcript Proof Plan v0

## Status

Report-only planning package. No DotTalk++ runtime was launched. No repo files were changed. No tables, indexes, memo stores, HELP DATA, CMDHELPCHK artifacts, metadata catalogs, DBFs, CDXs, LMDB stores, relation files, or workspace files were mutated by this package.

## Purpose

DD-013 mapped the C++ source surfaces for workspace, relation, and tuple infrastructure. DD-014 defines the guarded evidence plan for turning those source contracts into runtime-proof candidates.

The core question is:

> Can a controlled DotTalk++ runtime transcript prove open work areas, relation definitions, relation persistence, and tuple graph behavior without mutating table data or protected system artifacts?

DD-014 answers with a staged plan, not an execution.

## Inputs

- Corrected C++ repo archive: `ccode_homegrown_20260527-055727.zip`
- Prior source map package: `dd013_workspace_relation_tuple_source_map_v0`
- DD-013 usage surfaces: 28 rows
- DD-013 registry surfaces: 22 rows
- DD-013 state structures: 25 rows

## Package outputs

- `dd014_proof_phases_v0.csv`
- `dd014_transcript_command_plan_v0.csv`
- `dd014_transcript_evidence_fields_v0.csv`
- `dd014_workspace_relation_transcript_proof_v0.schema.json`
- `dd014_sample_transcript_manifest_not_executed_v0.json`
- `dd014_workspace_relation_proof_template.dts`
- `dd014_capture_wrapper.ps1.template`
- `dd014_mutation_boundary_matrix_v0.csv`
- `dd014_catalog_promotion_map_v0.csv`
- `dd014_local_run_checklist_v0.csv`
- `dd014_summary_counts_v0.csv`
- `DD014_NEXT_ACTIONS_v0.md`
- `DD014_AUTOLOG_v0.md`

## Proof phases

| Phase | Name | Boundary |
|---|---|---|
| DD014A | Transcript harness preflight | no runtime |
| DD014B | Read-only surface proof | usage/report commands only |
| DD014C | Scratch workspace session proof | workarea/relation/session mutation only; no table-data mutation |
| DD014D | Tuple graph proof | read/cursor-motion proof only |
| DD014E | Manifest promotion review | offline review; no automatic promotion |

## Core command evidence plan

DD-014 focuses on these command families:

- `WORKSPACE`, `AREA`, `DBAREAS`, `STATUS`
- `RELATIONS`, `SET RELATIONS`, `SET RELATION`
- `TUPLE`, `TUPVALIDATE`

Excluded from default DD-014 execution:

- `TUPEXPORT`, because it writes/truncates filesystem output.
- `BROWSE`, `BROWSER`, `BROWSETUI`, and interactive `ERSATZ` edit paths, because browser/edit behavior needs a separate guard.
- HELP/META/CMDHELPCHK mutation paths.

## Catalog targets

DD-014 reserves transcript promotion paths for:

- `DD_TRANSCRIPT_RUN`
- `DD_TRANSCRIPT_COMMAND`
- `DD_WORKSPACE_SNAPSHOT`
- `DD_WORKAREA`
- `DD_REL`
- `DD_REL_FIELD`
- `DD_REL_FILE`
- `DD_REL_VERIFY`
- `DD_TUPLE_SPEC`
- `DD_TUPLE_COLUMN`
- `DD_TUPLE_VERIFY`
- `DD_RUNTIME_PROOF`

## Trust rule

A source usage block proves the command contract exists. A registry row proves the command surface is registered. A runtime transcript proves observed behavior only for the specific build, data root, command sequence, and output captured. DD-014 keeps those evidence kinds separate.

## Result

DD-014 creates the plan and templates needed for a later local proof run, but it does not claim runtime proof yet.
