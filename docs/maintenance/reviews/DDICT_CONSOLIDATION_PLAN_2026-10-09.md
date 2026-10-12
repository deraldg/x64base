# DDICT bounded curation and consolidation plan

Date: 2026-10-09 (America/Los_Angeles)
Owner: member.derald
Status: navigation implemented; inventory measured; physical consolidation planned only
Scope: D:/code/ccode; no search or change under D:/dev

The first consolidation is navigational: one maintained DDICT entry point links
current source, consumers, catalog authority, tooling, and historical evidence.
The second is classification: a bounded inventory identifies exact files without
treating repeated directory names as permission to merge or delete them.

## Implementation follow-up

The authorized shared-view source implementation and native long-name dogfood
proof are recorded in [the implementation closeout](DDICT_CATALOG_VIEW_IMPLEMENTATION_2026-10-09.md).
Physical consolidation remains planned only; the catalog data findings require
a separate repair scope. The sections below retain the curation baseline.

## Completed organization

- Updated [docs/datadict/README.md](../../datadict/README.md) to describe current
  storage roots, command behavior, consumers, and historical boundaries.
- Updated [tools/datadict/README.md](../../../tools/datadict/README.md) to distinguish
  the new bounded inventory from old orchestration and apply-stage scripts.
- Added a DDICT route to [the Portal search map](../../../labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md).
- Recorded the [catalog authority assessment](DDICT_CATALOG_AUTHORITY_2026-10-09.md).
- Added the report-only [inventory tool](../../../tools/datadict/review/curation_inventory.py)
  and its [measured output](DDICT_CURATION_INVENTORY_2026-10-09.json).

Existing historical documents retain their wording and dates. The previous
[crosswalk](DDICT_CROSSWALK_2026-10-09.md) remains the initial assessment; this
follow-up adds live-row, field, member-set, and historical-hash evidence.
The owner clarified that xbase.com was a typo for x64base.com.

## Role and retention manifest

The JSON inventory is the per-file manifest for its explicit files and named
direct-child scopes. Each row records role, owner qualification, tracking state,
bytes, SHA-256, disposition, and replacement. Tool option declarations are
extracted without execution and do not certify safety. The following directory
roles guide future classification; they do not claim that unenumerated children
were inspected.

| Scope | Producer and consumers | Disposition |
| --- | --- | --- |
| `src/cli/cmd_ddict.cpp`, `src/datadict/`, `include/datadict/` | Maintained source authors; consumed by CMake, CLI, GUI, and selected metadata tooling | Keep as implementation authority |
| `tools/datadict/` | Engineering source; operator/evidence pipeline consumers | Keep current paths; classify individual runners before use. Historical repair generators are not today's repair instructions. |
| `docs/datadict/specs`, `contracts`, `definitions`, `schemas` | DD-series authors/generators; later proof and design references | Preserve historical lineage. Link current applicability from the landing page. No bulk relocation. |
| `docs/datadict/policy` | Recorded layout/promotion decisions | Preserve; distinct role from plural `policies` |
| `docs/datadict/policies` | Baseline and evidence-tool rules | Preserve executable/tool references; do not merge with `policy` by name similarity |
| `docs/datadict/packages`, `drafts`, `fragments` | Original deliveries and candidate patches | Preserve as historical inputs; not alternate source homes |
| `docs/datadict/reports`, `manifests`, `runlog` | Generators and runtime captures; proof/closeout consumers | Keep immutable evidence. Ignored outputs are not automatically durable Git records. Essential historical manifests are embedded in the new measured inventory. |
| `docs/datadict/baselines`, `review_queue`, `reviews` | Acceptance and disposition work | Preserve until the exact baseline/consumer graph is reviewed |
| `docs/datadict/backups`, `candidates` | Staging/promotion tools | Preserve until reconstruction and rollback are demonstrated |
| `dottalkpp/scripts/datadict` and `dottalkpp/data/scripts/ddict_help.dts` | Runtime-facing templates and scripts | Keep separate from engineering generators; do not treat a template as executed proof |
| `dottalkpp/data/datadict` | Catalog producers; current CLI/GUI/workspace consumers | Preserve both table families; no row rewriting |
| `build` object files and pasted temporary examples | Compiler/scratch products | Outside this bounded manifest and cleanup plan |

The report tool deliberately does not traverse packages, backups, LMDB trees,
build trees, or every historical report. It does not run the old repository-wide
orchestrator. Individual historical tool stewardship remains unverified rather
than assigned from a filename.

## Exact nested-copy candidate set

The inventory's `consolidation_candidates` array names every proposed source,
retained counterpart, archive destination, source/retained hash, and prerequisite.
All 25 enumerated direct DBF/DBT/DTX files in the nested directory match the
corresponding parent files at measurement time: eleven DBFs, seven DBTs, seven
DTXs. These bytes were compared, not inferred from filenames or timestamps.

Source directory: `dottalkpp/data/datadict/datadict/`

Retained directory: `dottalkpp/data/datadict/`

Proposed archive directory: `docs/datadict/backups/curation_20261009/nested_catalog/`

This is an exact file plan, not a recursive directory move. It excludes any
other file, subdirectory, index, LMDB environment, build product, and historical
backup. Neither memo extension is declared disposable; both are retained in the
candidate recovery set. No bytes have been moved or removed.

## Before executing that file plan

1. Read the exact candidate array and approve its scope after refreshing hashes.
2. Check live consumers and named resolver/workspace/promotion references for
   dependence on the nested paths. Prove canonical selection from supported
   working directories and preserve a fallback-only deployment case.
3. Resolve sidecar/index dependencies and demonstrate equivalent CLI/GUI results
   in an isolated copy with the nested candidates absent. Hash equality alone
   does not prove path independence.
4. Create an isolated recovery copy, record all member hashes, and demonstrate
   restoration to the exact original paths. The proposed backup root is ignored
   by Git, so a commit is not its rollback proof.
5. Only after those checks, archive the exact files using a path-contained
   operation. Recheck consumers and report any unclassified residue; do not
   remove the enclosing directory by a broad recursive cleanup.

These are unresolved execution gates, not findings that the files are unsafe.
This pass implements the requested organization and supplies the concrete plan;
it does not reinterpret "proceed" as permission to destroy data or backups.

## Source follow-up sequence

The original review's TAGS reporting defect, reader error/empty ambiguity,
memo handling, and omitted OBJECTS annotation remain recorded. A filename-only
catalog cutover would not resolve them. A bounded implementation can first fix
the misleading TAGS condition and align usage, then introduce a shared typed
read result and normalized catalog view with isolated failure/empty/memo/schema
tests. Its exact source preflight, HELP impact, and behavior proof should be
reviewed against the catalog assessment before a migration is designed.

## Validation and handoff

Mode: maintenance. Change class: C0 documentation plus an experimental
report-only inspection tool. Owning lifecycle: DotTalk++ maintenance; no engine
build target or product/index profile change. Source preflight consulted the
contract shelf, lifecycle, registry, source-mutation and engineering seeds,
DD095/DD096 policy, and relevant reader/command contracts. No registered
DDICT-specific central contract was found by the scoped registry search; the
historical subsystem contracts and source remain applicable evidence.

Validation covers parsed catalog members and schemas, hashes, exact scope,
output-path rejection, ASCII prose, navigation targets, and protected-input
stability. It does not establish a fresh DDICT runtime or complete refresh.
No engine source, build files, catalog data, HELP, indexes, or old generated
reports were changed. No commit, push, or website publication was performed.
All results are local and require a scoped commit to travel with the repository.
