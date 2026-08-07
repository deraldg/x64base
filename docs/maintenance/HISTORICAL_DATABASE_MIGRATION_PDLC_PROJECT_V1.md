# Historical Database Migration Laboratory -- PDLC Project v1

Status: **active seed / design lane**  
Project: `project.labtalk.historical_database_migration`  
Owning lifecycle: LabTalk SDLC + PLDC  
Upstream runtime authority: `project.x64base.runtime`  
Publication consumer: `project.x64base.website`

## Purpose

Build a proof-aware teaching package that carries one business dataset through
the historical database and interchange chain:

```text
COBOL fixed-length records -> xBase/DBF -> CODASYL relationships ->
JSON -> CSV -> spreadsheet inspection -> SQLite/SQL -> x64base comparison
```

The package uses existing runtime starters and sample data to teach how business
meaning, field layouts, relationships, validation, and provenance change as a
dataset moves through successive technologies.

This is an educational migration project, not a claim that x64base implements
every historical storage engine or that the JUMPS/CODASYL cases reproduce the
original production systems.

## Scope

### In scope

- JUMPS-inspired fixed-record and batch-processing reconstruction.
- COBOL fixed-length export/build/run/test learning path.
- DBF/xBase and MCC workspace midpoint.
- CODASYL owner/member and navigational relationship demonstration.
- JSON, CSV, and spreadsheet projections with loss/provenance notes.
- SQLite adapter, `SQLITE`, `BIBLETALK`, and `ERP` teaching surfaces.
- Same-machine x64base-versus-SQLite benchmark comparisons on equivalent data
  and workloads.
- Cascade Precision ERP sample database and rebuildable SQL artifacts.
- Case, lesson, dataset, proof, and website publication records.
- GnuCOBOL acknowledgement before public promotion.

### Out of scope

- Recreating an original JUMPS or CODASYL production database.
- Adding a physical CODASYL storage engine.
- Turning Cascade ERP into a production ERP product.
- Changing SQLite, COBOL, DBF, or ERP runtime behavior in this project seed.
- Publishing private source documents, large local decks, or unreviewed personal
  history as verified fact.

## Current surfaces and truth states

| Surface | Current state | Role in this project |
|---|---|---|
| `COBOL` command | `real` / runtime-supported | Fixed-length export and GnuCOBOL learning starter |
| `CODASYL` command | `real` / teaching adapter | Owner/member and navigational traversal |
| `MCC` command/workspace | `real` / starter demo | DBF/xBase midpoint and relationships |
| `SQLITE` command | `real` / runtime-supported | Generic external SQLite bridge |
| `BIBLETALK` | `real` / educational wrapper | SQLite teaching endpoint |
| `ERP` | `dev` / educational wrapper | Cascade domain-specific endpoint |
| `CASE` | `dev` / catalog surface | Historical narrative and case routing |
| Cascade Precision ERP package | `real` local artifact | SQLite schema, seed, dump, queries, CSV data |
| JUMPS case | `plugged_stubbed` / review candidate | Historical reconstruction; fact review required |
| COBOL historical case | `plugged_stubbed` / source review required | Historical foundation and fixed-record context |
| CODASYL/ALCOA case | `plugged_stubbed` / source review required | Network database context |
| Website section | `planned` | Public catalog and learner-facing migration path |

## PDLC six-step project cycle

### 1. Analyze

Inventory the dataset candidate, semantic fields, case evidence, runtime
starters, dependencies, audiences, and truth states. The exit gate is a stable
claim classification: runtime, local artifact, historical source memory,
reconstruction, planned, or unknown.

### 2. Design

Define the migration chain, canonical semantic ledger, JUMPS-inspired domain,
CODASYL owner/member model, dataset manifest, fixture policy, and
case/lesson/proof/publication crosswalk. Every transformation must state its
input, output, loss boundary, and validation observation.

### 3. Code / assemble

Initially assemble existing capabilities: `COBOL EXPORT STUDENTS`, MCC
workspaces, the `CODASYL` teaching adapter, SQLite adapter/`SQLITE`, BibleTalk,
Cascade ERP, and CSV/JSON/spreadsheet projections. Runtime changes belong to
the owning DotTalk++ project and require their own mutation contract.

### 4. Test and debug

Prove fixed record widths, COBOL build/run, DBF import, CODASYL traversal,
JSON/CSV round trips, spreadsheet loss, SQLite schema/query behavior,
SQLite<->DBF conversions, Cascade seed/dump consistency, and semantic-ledger
reconciliation. Classify differences as intentional representation changes,
conversion defects, source uncertainty, or unresolved review items.

The benchmark sublane must compare like-for-like workloads on the same machine:
the same logical dataset, equivalent predicates/aggregations, documented cold
and warm runs, identical output checks, and recorded build/runtime versions.
Benchmark results describe a workload and configuration; they do not establish
that x64base or SQLite is universally faster.

### 5. Document

Maintain this charter, the lane manifest, case pages, dataset catalog entries,
migration-format teaching page, command-to-lab crosswalk, GnuCOBOL
acknowledgement, proof index, limitations page, and website publication
proposal.

### 6. Maintain

Re-check paths after runtime/data changes, refresh checksums and manifests,
preserve the semantic ledger, keep website copy downstream from proof truth,
re-review dependency credits, update CASE/lesson states, and record superseded
projections rather than silently replacing them.

## Initial milestones

| Milestone | Deliverable | Initial state |
|---|---|---|
| M0 | Project/lane registration and charter | Registered by this change |
| M1 | Dataset and command crosswalk | Design lane |
| M2 | COBOL fixed-record slice | Existing starter; proof refresh needed |
| M3 | MCC/xBase midpoint | Existing starter; proof selection needed |
| M4 | CODASYL relationship slice | Existing adapter; case review needed |
| M5 | SQLite/Bible/Cascade endpoint | Existing surfaces; integration proof needed |
| M6 | JSON/CSV/spreadsheet projections | Planned teaching package |
| M7 | Same-machine x64base <-> SQLite benchmark slice | Planned proof lane |
| M8 | Website catalog and learner pages | Publication lane |

## Authority and promotion rules

```text
runtime/source evidence -> LabTalk case/dataset/proof records
                         -> PDLC/PLDC package review
                         -> website/manual publication
```

The public site must not upgrade a historical case, simulated migration, or
development ERP wrapper to `real` merely because a command or page exists.

## Key source pointers

- `src/edu/edu_cobol.cpp`
- `src/cli/cmd_codasyl.cpp`
- `src/cli/cmd_sqlite.cpp`
- `src/edu/edu_bibletalk.cpp`
- `src/edu/edu_erp.cpp`
- `include/sqlite/sqlite_adapter.hpp`
- `src/sqlite/sqlite_adapter.cpp`
- `dottalkpp/data/cascade_precision_erp/`
- `docs/cases/CASE_HIST_020_JUMPS_73C_ARMY_SYSTEM.md`
- `docs/cases/CASE_HIST_030_UNISYS_CODASYL_ALCOA.md`
- `labtalk/registries/projects.yaml`
- `D:\dev\x64base-site\content\docs\labtalk\database-evolution.mdx`
