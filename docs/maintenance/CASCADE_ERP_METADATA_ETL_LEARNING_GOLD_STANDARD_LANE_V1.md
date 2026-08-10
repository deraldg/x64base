# Cascade ERP Metadata, ETL, Migration, and Learning Gold Standard Lane V1

    status      : chartered; M0 authority audit active
    lane        : AIF-105
    parent      : project.labtalk.historical_database_migration
    owner       : member.derald
    steward     : member.ai.codex.local
    coworker    : member.ai.chatgpt
    run         : CODEX-20260810-ERP-RELATIONS-001
    created_utc : 2026-08-10T14:52:56Z

## Assignment

The maintainer assigned `member.ai.codex.local` as steward and implementation
lead responsible for carrying this lane to its gold-standard gates. ChatGPT Pro
is recorded through the existing project identity `member.ai.chatgpt` as
coworker and design contributor.

The owner remains `member.derald`. Stewardship is responsibility for analysis,
implementation, proof, documentation, and handoff. It is not ownership,
commit authority, promotion authority, or publication authority.

## Origin and correction

The external Cascade bundle report is a draft and design input. It is not an
accepted implementation, proof record, or publication artifact. Its useful
architecture is adopted for review; its claims must pass local authority,
source, runtime, and evidence gates.

The first audit found a load-bearing terminology error. The canonical local
SQLite carrier currently measures:

```text
user tables                  34
analytical views              9
loaded sample records       330
foreign-key constraints      58
foreign-key field edges      58
cross-module FK edges        26
foreign_key_check rows        0
self-references                2
```

The manifest's 26 figure is explicitly the cross-module subset. It must not be
labeled as the total foreign-key constraint count. Any generator, runtime
command, lesson, graph, or proof that conflates these quantities fails the
lane.

## Objective

Make Cascade Precision Mfg ERP the authoritative dogfood substrate for a
coherent path:

```text
canonical SQLite carrier
  -> read-only metadata inventory
  -> exact relation and graph model
  -> complete dual-carrier logical schema contract
  -> explicit x64base table mirrors and materialized view snapshots
  -> bidirectional ETL and ELT instruction
  -> reconciliation and proof
  -> LabTalk lessons and cases
  -> reviewed publication candidates
```

The graph is generated from database metadata. It never becomes an independent
schema authority.

## Gold-standard architecture ruling -- GIGO gate

The target is not two mutable masters and it is not one carrier copied into a
second carrier by value inference. The target is one reviewed, versioned
logical contract with two generated and independently verified carrier
projections.

Bootstrap and steady-state authority are deliberately different:

1. The sealed SQLite package is the admitted origin for Cascade V1. Its carrier,
   manifest, schema, seed, CSV, and checksum ledger must reconcile before any
   schema is promoted.
2. A neutral `cascade_schema_v1` contract is extracted as a candidate, reviewed
   field by field, and accepted with the exact source carrier hash.
3. After acceptance, that versioned logical contract becomes the schema design
   authority. SQLite and x64base are generated projections of it; neither
   carrier silently becomes a second design master.
4. The sealed SQLite instance remains the V1 data/provenance authority. A later
   schema revision requires an explicit migration and a new contract version.

The canonical logical contract must carry stable object and field identities,
logical and physical names, semantic domains, widths and scales, nullability,
defaults, primary and unique keys, checks, all foreign-key constraints and
actions, generated expressions, indexes, view definitions, module ownership,
and carrier support states. Support states are explicit: `native`, `soft`,
`materialized`, or `unsupported`.

The x64base projection is complete only when every semantic feature is either
implemented and proven or explicitly represented in the capability/enforcement
matrix. A sidecar is complete metadata, not native enforcement. A materialized
view snapshot is not a live x64base view.

Parity has four independent gates:

1. Structural parity: exact objects, fields, order, types, widths, scales,
   nullability, keys, constraints, relationships, generated expressions,
   indexes, and view definitions.
2. Data parity: canonical per-row values and identities, explicit NULL bitmaps,
   rejects, row digests, aggregate invariants, and view-result digests.
3. Behavioral parity: only operations that both carriers claim to support,
   including mutation, constraint behavior, transactions, restart, indexing,
   and query observations. Unsupported differences are labeled, not hidden.
4. Reproducibility parity: a clean checkout can rebuild into an empty temporary
   root, produce deterministic artifacts, and verify the same contract and
   carrier digests without relying on ambient files or cwd discovery.

Case studies are executable acceptance products over those gates. Their
metadata, lifecycle, visibility, provenance, dataset version, schema-contract
version, and proof links belong in one validated `cases.yaml`. Runtime, portal,
and website artifacts are compiled audience-specific projections; they do not
scan arbitrary Markdown files or maintain independent case authorities.

The portal is an observer and proof operator, not an authority. It may display
PASS only after a captured runner has exited successfully and its receipt,
required assertions, carrier hashes, and freshness checks have passed. Starting
a background process is `launched`, never `passed`.

## Gate 0 -- durability before feature depth

The current working tree cannot yet reproduce the teaching surface from HEAD:

- 15 of the 16 registry case documents are present locally but untracked; only
  `ENG-060` is present in HEAD.
- The secondary 22-file case tree and the shared `launch-common.ps1` used by
  `datarun.ps1` are also untracked.
- The complete Cascade source package -- schema, seed, dump, manifest, checksum
  ledger, queries, README, and 34 table CSVs -- is present locally but untracked.
  The SQLite carrier is intentionally local and ignored; a clean checkout must
  reconstruct it and prove the accepted carrier hash from admitted inputs.
- The AIF-105 claim, charter, generator, schemas, proof transcripts, and mirror
  artifacts are working-tree-only.
- Historical migration material and the AI-roles taxonomy both use `AIF-058`.
  AIF-105 must remain the sole Cascade lane identifier while that older ticket
  collision is reconciled separately.

No later milestone may be called durable until an exact-path review admits the
intended files, a fresh checkout contains every required authority, and the
clean-checkout gates pass. Untracked evidence can inform review, but it cannot
upgrade repository truth.

Housekeeping decisions and admission boundaries are recorded in
`docs/maintenance/CASCADE_ERP_GATE0_HOUSEKEEPING_V1.md`.

## Authority chain

1. The identified local SQLite carrier and its package checksums identify the
   source instance.
2. SQLite schema and pragma results define the observed table, column, index,
   view, trigger, and foreign-key metadata.
3. DotTalk++ source defines the `ERP` command behavior.
4. Runtime regressions and preserved transcripts establish observed behavior.
5. LabTalk registries organize concepts, datasets, commands, proofs, cases, and
   lessons.
6. The PDLC/SDLC review gate decides readiness.
7. Staging and public sites receive only reviewed promoted views.

Historical ZIPs and external bundles are design/provenance evidence. They do
not outrank the identified operational carrier.

## Scope

- Read-only canonical metadata generator and deterministic artifacts.
- Exact distinction among FK constraints, FK field edges, intra-module edges,
  cross-module edges, and self-references.
- Table and module graphs, bounded neighborhoods, hubs, cycles, and dependency
  stages with honest treatment of cycles.
- Candidate runtime surfaces:
  - `ERP PROFILE`
  - `ERP RELATIONS [table]`
  - `ERP GRAPH [TEXT|MERMAID|DOT|CSV] [table]`
- Correction of `ERP CHECK` so measured metadata replaces hard-coded claims.
- Reuse and strengthening of the existing Cascade Items crosswalk.
- Complete schema parity across all 34 SQLite tables and all 9 analytical views:
  native SQLite objects on one side; explicit x64base DBFs plus complete
  relational sidecars on the other.
- Deterministic rebuild and parity proof that rejects value-inferred type drift.
- ETL/ELT learning sequence across real ERP processes.
- Candidate ETL control schemas validated against the selected active schema
  contract and then exercised through normal DotTalk++ paths.
- Governed plan and proofs for migration into native x64base mechanisms.
- Durable proof, lesson, case, closeout, and handoff records.

## Non-goals

- Recreating or redesigning the Cascade ERP from memory.
- Treating a generated graph as schema authority.
- Claiming that all 34 tables have migrated before they have.
- Mutating the canonical SQLite carrier during metadata generation.
- Editing HELP DBFs, generated catalogs, staging, or publication outputs without
  their separate gates.
- Calling a successful build runtime proof.

## Roles and working agreement

### Steward and implementation lead: member.ai.codex.local

- Own the working plan and gate order.
- Ground every draft assertion against local authority.
- Implement the narrow accepted slices in `D:\code\ccode`.
- Preserve unrelated dirty work and use exact-path scope.
- Build, run, assert data, and preserve evidence before upgrading truth state.
- Reconcile source usage, tests, metadata impact, lessons, and handoff.
- Report dev, staging, validation, and publication as separate states.

### Coworker (Class A) and coauthor of record: member.ai.claude.cowork (owner-assigned 2026-08-10)

- Authored the system-bundle organization (layout ruling execution), the
  `.dtschema` + relation-graph generator and its projections, the three
  environment/build scripts, and the path migrations across tools, tests,
  the ecology preflight, and the `ERP CASCADE` candidate list.
- Adjudicates host datarun transcripts for its slices; verifies before
  asserting; hands mutating git to the owner.
- Respects the steward's lane leadership: re-baseline notes are left for
  member.ai.codex.local, whose uncommitted work is preserved untouched, and
  runtime `ERP GRAPH`/`PROFILE` M2 scope remains the steward's.

### Coworker and design contributor: member.ai.chatgpt

- Supply design alternatives, lesson structure, review findings, and candidate
  artifacts through attributable intake.
- Review terminology, learner flow, graph presentation, ETL controls, and
  migration plans.
- Mark proposals and unexecuted validations honestly.
- Do not declare local integration, runtime proof, promotion, or publication
  without evidence returned from the responsible local gate.

### Owner: member.derald

- Retains final rulings, commit authority, promotion authority, and publication
  authority.

## Milestones and gates

| Milestone | Outcome | Exit gate |
| --- | --- | --- |
| M0 | Authority and draft audit | Carrier identity, hashes, 34/9/330/58/26/0 taxonomy, existing surfaces, and draft gaps recorded. |
| M1 | Metadata generator | Read-only open, deterministic JSON/CSV/Markdown/Mermaid/DOT, constraint-versus-edge tests, canonical run, checksum manifest. |
| M2 | Runtime metadata commands | Source contract aligned; `PROFILE`, `RELATIONS`, and bounded `GRAPH` implemented; DEVELOPMENT build and self-asserting regression green. |
| M3 | Dual-carrier schema mirror | All 34 tables have explicit x64base schemas; all 9 views have labeled materialized snapshots; fields, counts, identifiers, and sidecar relational semantics reconcile without AUTODBF type drift. |
| M4 | Multi-table ETL labs | Vendor/Items, procure-to-pay, plan-to-produce, order-to-cash, and close-to-report labs use graph-proven edges. |
| M5 | ETL control metadata | Candidate schemas validate and are exercised through DDL/open/mutate/index/relation/export and recovery paths. |
| M6 | Native migration slice | One bounded multi-module transfer proves identity, counts, rejects, lineage, restart behavior, and process-view reconciliation. |
| M7 | Full migration program | All approved tables migrate under dependency/cycle policy with per-table and end-to-end evidence. |
| M8 | LabTalk and publication ascent | Registries, lessons, cases, proofs, SelfDoc/manual candidates, and publication review align without overstating maturity. |

Milestones advance independently only where their dependencies and evidence
permit. M8 cannot promote a capability beyond the strongest source/runtime
proof beneath it.

## Gold-standard acceptance rules

1. Every count names its exact population and derivation.
2. Every canonical run records carrier path, SHA-256, SQLite version, generator
   or binary identity, working directory, and timestamp.
3. Metadata generation is read-only and proves that the carrier hash is
   unchanged before and after.
4. Regressions fail when a command is absent, output is truncated unexpectedly,
   an expected edge is missing, or a script does not execute.
5. Synthetic tests cover simple, composite, self-referencing, cyclic, and
   disconnected schemas even when Cascade does not exercise each shape.
6. Load order reports strongly connected components or deferred constraints;
   it never prints a false linear order through a cycle.
7. ETL proof asserts values and identities, not only row counts and schemas.
8. Candidate schemas remain candidate until exercised by current runtime paths.
9. Local work is never called promoted, published, or public.
10. The chat is not the record; accepted evidence is durable and attributable.
11. SQLite-declared TEXT identifiers remain character fields in x64base even
    when every current value looks numeric; NULL-only numeric fields remain
    numeric. Value inference cannot define the mirror schema.
12. A complete logical mirror includes tables, columns, keys, defaults, checks,
    indexes, relationships, and view SQL. Features DBF cannot enforce natively
    remain explicit sidecar semantics and must not be mislabeled as native.
13. SQLite views become labeled materialized teaching snapshots in x64base;
    they are never described as live x64base views.

## Current working state

- `AIF-105` is atomically claimed by `member.ai.codex.local`.
- The external report is classified as a draft requiring intake and verification.
- A local `ERP RELATIONS` source/test candidate exists but has not completed its
  correct DEVELOPMENT build and runtime proof. It is not accepted M2 evidence.
- The deterministic dual-schema generator currently emits and validates 34
  explicit x64base table schema candidates plus 9 labeled materialized view
  snapshot candidates. A current runtime run created and imported all 43
  objects and reconciled importer-reported row counts. This is structural-build
  evidence, not complete schema, value, constraint, index, relation, view, or
  round-trip parity.
- Character widths are still derived from current maximum values and REAL-like
  columns share a blanket numeric scale. Those are candidate mappings, not an
  accepted semantic schema.
- Current DDL receipts mark indexes as metadata-only and do not build physical
  relations. Relationship sidecars also require a reviewed logical-to-physical
  identity map before they can drive a native relation loader.
- The current mirror runner counts build/import markers but does not assert all
  emitted field definitions, readback counts, values, NULL identities, view
  digests, or round trips. Its PASS state must be read as structural-build pass
  until the parity oracle is strengthened.
- `ERP PROFILE` and `ERP GRAPH` are not implemented in the tracked baseline.
- No external bundle deliverable has been admitted into this repository.
- No staging, commit, push, promotion, or publication is claimed.

## Layout ruling 2026-08-10 (owner) -- system bundle

Recorded by member.ai.claude.cowork executing an explicit owner instruction; the
lane steward (member.ai.codex.local, offline to 2026-08-16) must RE-BASELINE on
this before resuming.

- All Cascade artifacts now live under `dottalkpp/data/systems/cascade_erp/`
  (`sqlite/` sealed package moved intact with its checksum ledger, `dbf/` 43
  mirrors, `meta/` 172 sidecar JSONs split out of the DBF dir, `indexes/`,
  `lmdb/`, `schema/`, `scripts/`). Bundle README documents the layout. All
  moved files were untracked, so git history is unaffected.
- Path constants updated: `tools/cascade_erp/generate_dual_schema_contract.py`
  (SYSTEM_ROOT), `run_dual_schema_mirror.ps1` (mirror/physical roots), and
  `src/edu/edu_erp.cpp` (bundle carrier path prepended to the ERP CASCADE
  candidate list; old paths retained as fallbacks). NOTE: `edu_erp.cpp` also
  carries the steward's uncommitted AIF-105 diff; the commit decision (fuse
  with dual attribution vs wait) is the owner's.
- New generated projection: `schema/CASCADE_ERP.dtschema` + executable
  `scripts/cascade_erp_build_indexes.dts`, emitted by
  `tools/cascade_erp/generate_dtschema.py` from the meta sidecars (34 tables,
  9 views, 103 tags of which 6 composite/partial, 58 relations; meta aggregate
  sha256 recorded in the file). Consistent with rule 12: sidecars stay
  authority; the .dtschema is a generated projection. Composite indexes are
  declared in full but built as leading-column tags, labeled partial
  (single-name `CDX ADDTAG`).
- Graph generated from metadata per this lane's own doctrine ("the graph is
  generated from database metadata; it never becomes an independent schema
  authority"): `schema/CASCADE_ERP.graph.mmd` (58 FK edges, meta hash stamped)
  + `schema/CASCADE_ERP.graph.html` local viewer. This is the GENERATOR-side
  graph only; the runtime `ERP GRAPH` command remains unimplemented M2 scope,
  and when it lands its output can be diffed against this file as a parity
  check.
- Environment scripts authored: `scripts/cascade_erp.dts` (DBF side; 7-area
  module-spine working set) and `scripts/cascade_sql.dts` (SQLite side; ERP
  CASCADE/CHECK/RELATIONS + SQLSEL demo queries). All runtime claims in them
  are UNPROVEN until a host datarun; the build-index script additionally
  requires the rebuilt engine for the new carrier path.
- Legacy `dbf/cascade_dbf/` and `dbf/cascade_og/` untouched; RETIRE candidates
  under the widow-and-orphan support rule, pending owner + steward approval.

## Immediate next gate

Complete Gate 0 as an exact-path source-control and clean-checkout inventory.
Then complete M0 by admitting the sealed source package, correcting the AIF-058
collision reference, and classifying every current generated artifact and proof.
Only after those gates may the neutral schema contract, parity oracle, compiled
case catalog, runtime commands, or deeper portal UI be accepted for promotion.
