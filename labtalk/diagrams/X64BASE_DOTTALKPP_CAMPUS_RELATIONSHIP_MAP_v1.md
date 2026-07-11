# x64base / DotTalk++ / Laboratory Campus Relationship Map v1

Status: curated source-derived architecture diagram

Canonical Mermaid source:

- `x64base_dottalkpp_campus_relationship_map_v1.mmd`

## Purpose

This map describes authority and consumption relationships across the database
engine, command/runtime identity, scripting layer, evidence and documentation
system, and Laboratory Campus. It is a system-context architecture map, not an
entity-relationship model: the boxes are subsystems and governed processes, not
database entities with record cardinality.

## Corrections Applied

- Laboratory Campus consumes and organizes DotTalk++ evidence; it does not fully
  encapsulate or own runtime truth.
- DotTalk++ is the command/runtime/manual identity over x64base engine services.
  The source remains in the broader x64base tree until a curated split is justified.
- x64base supports classic/MS-DOS, Visual FoxPro, and x64 DBF-family work rather
  than only `DBF_64`.
- SelfDoc is report-only by default and preserves provenance. MDO and manualgen
  own later review and packaging stages.
- The curriculum is an evolving crosswalk and set of initial lab paths. A fixed
  seven-module syllabus is not yet a canonical, reviewed claim.
- Open Index API and Open GUI API are development lanes, not completed universal
  API guarantees.
- The student/custom index lane has real but deliberately limited surfaces:
  `SIX` is registered with create/build/info operations, `SCX` is the current
  compound student family, and `REINDEX CUSTOM` opts into both. `SNX` remains a
  reserved/container-groundwork lane with no registered educational shell
  command. A general user-supplied index adapter contract is planned, not complete.

## Source Basis

- `labtalk/README.md`
- `labtalk/LABTALK_CAMPUS_ARCHITECTURE_v0.md`
- `labtalk/LABTALK_EDUCATION_MAP_v0.md`
- `docs/governance/REPO_BOUNDARIES_RUNTIME_GUI_LABTALK_v1.md`
- `docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`
- `docs/HELP_METADATA_SELFDOC_WORKFLOW_v1.md`
- `selfdoc/tool_manifest.yaml`
- `tools/manualgen/README.md`
- current `src`, `include`, HELP, proof, and registry surfaces

## Reading Rule

Solid arrows show current authority, execution, consumption, evidence, or
promotion relationships. Status labels inside each node prevent the diagram from
presenting alpha, partial, experimental, or reserved work as finished product.
