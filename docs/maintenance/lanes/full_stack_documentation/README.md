# Full Stack Documentation Lane

Status: active planning, audit, and candidate-orchestration lane  
Created: 2026-07-16  
Authority root: `D:\code\ccode`

## Purpose

This lane coordinates a controlled documentation flush from source reference
inputs through HELP, validation, provenance, manual candidates, and reviewed
publication pointers.

It begins with the current `*ref.hpp` and source-contract family and follows the
data through:

```text
source/runtime and include/*ref.hpp
  -> comments and usage-contract evidence
  -> CMDHELP legacy compatibility build when required
  -> current HELP DATA build
  -> CMDHELPCHK and runtime reader proof
  -> metadata and SelfDoc evidence refresh
  -> manualgen inventory, validation, dry run, and parity review
  -> reviewed promotion and publication pointers
```

This is an orchestration lane. It does not take ownership away from the HELP,
comments, metadata, SelfDoc, manualgen, or publication lanes.

## Start Here

1. Read [FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md](D:/code/ccode/docs/maintenance/lanes/full_stack_documentation/FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md).
2. Copy [FULL_STACK_DOCUMENTATION_FLUSH_RECORD_TEMPLATE_V1.md](D:/code/ccode/docs/maintenance/lanes/full_stack_documentation/FULL_STACK_DOCUMENTATION_FLUSH_RECORD_TEMPLATE_V1.md) for the run.
3. Start the run's append-only progress log and CSV companion.
4. Complete the report-only baseline before authorizing any generated-data mutation.

The active run log is
`runs/DOCFLUSH-20260716-001/DOCUMENTATION_FLUSH_PROGRESS_LOG_V1.md`. Update it
at every material pass, failure, reconciliation, authorization, or next-gate
change. Do not wait for session closeout to reconstruct progress.

## Engine benchmark history

Engine-performance facts that surface during documentation matriculation must
retain the same provenance discipline as HELP and manual inputs. Pinocchio keeps
its initial human summary in `docs/maintenance/PINOCCHIO_STRESS_TEST_PLAN_V1.md`,
row-level results in `PINOCCHIO_HISTORICAL_ENGINE_BENCHMARKS_V1.csv`, and the
currently observed future-run machine input in
`PINOCCHIO_MACHINE_PROFILE_CURRENT_V1.json`.

Do not infer historical hardware from the current workstation. Future runs must
retain raw transcripts and the per-run `machine_profile.json`; new results append
to the historical ledger instead of replacing earlier baselines.

## Authority and Ownership

The lane follows the repository authority order:

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
Manualgen assembles reviewed views.
Publication exposes reviewed snapshots.
```

Primary owning documents:

- `docs/governance/authority_order.md`
- `docs/governance/anti_drift_best_practices.md`
- `docs/HELP_METADATA_SELFDOC_WORKFLOW_v1.md`
- `docs/WORKFLOW_RUNBOOK_v1.md`
- `docs/maintenance/lanes/help/HELP_DOCUMENT_FAMILY_SYSTEM_GUIDE_v1.md`
- `docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md`
- `tools/manualgen/README.md`

## Mutation Boundary

Planning, inventory, source inspection, HELP inspection, validation, manualgen
inventory, manualgen validation, candidate generation, and parity reports may
be performed as report-only work.

The following are separate reviewed mutation gates:

- changing source or `include/*ref.hpp`;
- reloading comments evidence tables;
- `CMDHELP BUILD LEGACY`;
- `CMDHELP BUILD` or `CMDHELP BUILD V2`;
- replacing HELP DBFs, indexes, or LMDB projections;
- importing or replacing live metadata;
- replacing accepted manual catalogs;
- moving a manual candidate into the active publication;
- changing active reader, canonical-manifest, website, or public-repository pointers.

A request to plan or inspect this lane does not authorize those mutations.

## Run Identity

Use a stable run ID in every new report and candidate manifest:

```text
DOCFLUSH-YYYYMMDD-NNN
```

The run record must name:

- authoritative input paths and hashes;
- binary used for runtime proof;
- pre-run and post-run catalog counts;
- commands actually executed;
- protected systems changed;
- candidate outputs;
- review decisions;
- active pointers changed;
- unresolved drift and the next gate.

The progress log is the during-work chronological record; the run record and
session closeouts remain the consolidated evidence and final-state records.

## Current Starting Point

The repository contains established HELP and manualgen lanes, but the current
workspace is mixed and heavily dirty. Existing status notes from 2026-06-26
report green HELP-family checkpoints, while current manualgen pointers identify
an accepted canonical manifest and primary reader artifact. Those are baseline
claims to inspect and refresh; they are not automatically accepted as proof for
a new flush.

The first full-stack run completed inventory, drift capture, a post-messaging
comment reharvest, the joined reference/source identity report, and pre/post
runtime transcripts. The maintainer executed the legacy HELP build first and
then the current source build; same-pass validation recorded nine changed HELP
files, improved catalog coverage, and retained residual drift. Manualgen then
completed inventory, validation, manifest export, dry-run assembly, section
parity, MAN* readback, and a four-surface pointer audit without promotion.

Manual authority and reader-lineage review classified the existing publication
surfaces without promoting them. The active reader and canonical manifest
resolve, but their stored reader hash and line-count evidence are stale. The
247-line post-MDO-318 delta is now partitioned across MDO-381,
MDO-382, three July 9 section/reader refreshes, and formatting, but its
authorization/result-hash chain remains incomplete. The current-publication
filename now survives only as a compatibility export. Manualgen explicitly
selects the supporting workspace as an assembly reference, emits
`publication_authority_claimed = 0`, and writes a separately named selected-
assembly manifest. The parity difference is now classified as one generated
assembly-metadata header evolution plus one 118-line MDO-261/MDO-270 overlay,
not missing section content. No accepted catalog, publication, or active
pointer has been promoted by this lane.

The current gate is human review of the three anchored smallest-packet prose
candidates. Selective merge, appendix acceptance, reader rebuild, and
publication remain separate decisions.

## Comments Evidence Tooling

The first active run established a preservation-first comments workflow:

- `tools/comments/audit_source_comment_escrow.py` inventories baseline/current
  drift without assigning authorization;
- `tools/comments/reconcile_source_comment_p1.py` cross-references P1 drift
  with Git, worktree, and closeout evidence;
- `tools/comments/build_source_comment_refresh_candidate.py` creates an
  isolated `SRCFILE.HASH` candidate while preserving all existing comment rows;
- `tools/comments/reharvest_source_comment_catalog.py` performs a complete
  current C-family leading-header and usage-contract harvest into an isolated
  replacement `SRC*` package;
- `tools/comments/upsert_source_comment_contract.py` refuses replacement of an
  existing metadata slice unless its explicitly lossy override is supplied.

The restored reharvester produces candidate data only. A candidate must pass
hash, referential-integrity, field-width, policy-table, and review-queue checks
before a separately authorized full COMMENTS reload. The header-only upsert
helper is not a substitute for this complete replacement path.

## Manual and Pointer Audit Tooling

The first active run added
`tools/fullstack_docs/audit_manual_documentation_pointers.py`. It compares the
active reader pointer, its evidence JSON, the active canonical-manifest pointer,
the current-publication manifest, the publication role index, and the MDO-350
controlled target. Missing targets are failures; stale hashes, line counts, or
intentionally split authority surfaces are review rows. The tool is report-only
and cannot promote or repair a pointer.

`tools/fullstack_docs/analyze_manualgen_parity_delta.py` classifies actual
line-level differences so repeated normalization failures are not mistaken for
multiple content losses. Its first run proved all 25 section bodies agree and
isolated the remaining overlay contract.

`tools/fullstack_docs/verify_manual_overlay_candidate.py` verifies ordered
overlay hashes, contiguous order, Markdown fences/headings, repaired paths, and
closed mutation boundaries. The current candidate passes with one portability
review because its preserved repo-local Python interpreter path is absent.

`MANUAL_AUTHORITY_RECONCILIATION_CONTRACT_V1.md` assigns distinct roles to the
primary reader, historical evidence revisions, accepted canonical manifests,
assembly references, controlled publication targets, and overlays. Historical
records are revisioned, not silently rewritten to current hashes.

`MANUALGEN_ASSEMBLY_WORKSPACE_SELECTION_CONTRACT_V1.md` makes manualgen's
assembly input explicit. Evidence-bearing runs use `--publication-workspace`;
invalid explicit values fail closed, while omitted values retain backward
compatibility but produce a validation REVIEW.

`MANUALGEN_HELP_META_HARVEST_INPUT_CONTRACT_V1.md` adds the adjacent evidence
input contract. Evidence-bearing runs use `--harvest-workspace`; all six HELP
and eight META CSVs are inventoried by path, shape, and SHA-256. The first
post-refresh run passes 14/14 with zero reviews or failures. Its comparison
finds 33,859 candidate rows versus 21,979 in the May canonical harvest, with
unchanged schemas. The selected evidence is manifest-bound but not copied or
promoted. `build-reference-candidate` now produces a complete 631-topic,
12,784-line human view plus row-level lineage. The reconciled run classifies
all 2,656 non-topic lines into global-message or source-fact appendices and
resolves all eight FOX compact SET identities to existing spaced topics through
an auditable ledger, leaving zero unclassified or unresolved rows. The
unchanged 25 section hashes keep curation into accepted manual sections as the
next explicit gate.

`MANUALGEN_TOPIC_CURATION_CONTRACT_V1.md` defines the next projection stage.
The first run produces nine shelf packets with complete 631-topic and
12,784-line ledgers. Supported DOT, FOX, and education topics are eligible
section candidates; pending/partial and supplemental topics form a 49-topic
review queue; developer/internal, system-message, and source-fact material stay
under explicit non-public or separate-appendix dispositions. No shelf is an
accepted manual section merely because it was generated.

`MANUALGEN_REVIEW_DISPOSITION_CONTRACT_V1.md` closes the 49-topic queue through
an explicit policy map validated against HELP, SYSCMD, and canonical topic
targets. The passing result yields five section-factory packets with 462 topics.
Twenty review topics enter through active runtime evidence and three through
partial physical HELP; aliases, source/developer facts, and nine no-runtime
deferrals remain outside generated section content.

`MANUALGEN_STRUCTURAL_RECONCILIATION_CONTRACT_V1.md` compares those 462 topics
with the 24-section primary body, both controlled 25-section overlays, and the
three review appendices. The passing 26-surface union map proposes additive
merges and one partial-HELP appendix only. Its follow-up evidence join closes
all 13 structural review rows, including explicit placement for `EXITS` and
`EXPORTFUNCTIONS`; remaining review and unplaced counts are zero. No
replacement or reader-pointer change is authorized.

`MANUALGEN_SECTION_DELTA_DRAFT_CONTRACT_V1.md` regroups the accepted mapping
into 22 per-target additive packets while copying all 462 disposition topic
blocks intact. Missing, duplicate, unused, and unmapped block counts are zero.
These packets are evidence for prose review, not section replacements.

`MANUALGEN_PROSE_REVIEW_BATCH_CONTRACT_V1.md` opens that prose gate with the
three smallest packets. The first run verifies all eight selected identities,
all three upstream packet hashes, and every proposed primary-section anchor,
then emits three candidate prose files. Four topics receive bounded additive
prose, `GENERIC` remains a canary cross-reference, and the three partial HELP
topics remain appendix-only. Existing sections and accepted appendices are not
edited.

`MANUALGEN_SELECTIVE_MERGE_CANDIDATE_CONTRACT_V1.md` consumes the durable human
review decision and inserts the approved prose only into copied sections and a
full generated reader candidate. The passing package contains two additive-
only section copies, one separate Partial HELP appendix, three unified diffs,
and one contextual reader. Section deletions, hash failures, anchor failures,
and canonical hash changes are zero.

The MAN* catalog CLI also has a regression test at
`tools/manualgen/tests/test_manual_catalog_cli.py` for case-normalized DBF
discovery. This prevents valid accepted tables from being double-counted as
`EXTRA_MAN_DBF` drift.

## Metacollect Reharvest Evidence

`DOCFLUSH-20260716-001/metacollect_phase/` records the isolated rebuild and
post-messaging metacollect refresh. The main build cache remains OFF; the
dedicated build enables only the report collector and writes five candidate
CSVs beneath the run envelope. Root reports, tracked seed candidates, and live
metadata DBFs remain protected by a no-replacement boundary.

The phase manifest records executable/source hashes, candidate hashes and row
counts, facts/compare/SYSFUNC/SYSARGS deltas, runtime warnings, command
transcripts, and explicit promotion state. The current gate is contract review,
not metadata loading.

The 2026-07-17 continuation now closes the command-identity contract queue.
The final reharvest is under
`DOCFLUSH-20260716-001/comments_reharvest/post_messaging_20260717_contracts_v4_final/`
and the joined identity report is under
`DOCFLUSH-20260716-001/reference_inventory_v6_contracts_final/`. One source
file may contribute multiple independently located `SRCUSAGE` rows, including
adjacent contracts separated only by another marker. The deterministic
203-row public SYSCMD candidate, row-level disposition ledger, runtime proof,
and executed rollback/readback package are under
`DOCFLUSH-20260716-001/metacollect_phase/candidate_v8_contracts_resolved/`.
All 40 former blockers are closed. The 2026-07-17 authorized promotion now has
an exact 203-row live readback with zero differences. The same proof pass found
and repaired HELP-slot assignment and compact SET identity collection in
source. The separately authorized nine-file HELP promotion now passes live at
12,784 lines, 492 topics, 449 legacy commands, and 2,506 legacy arguments.

## Metadata Systems Mining

`DOCFLUSH-20260716-001/metadata_mining_phase/` classifies 24 collection,
harvest, reflection, validation, transformation, and readback systems found by
the repository-wide `meta` pass. It separates documentation candidates from
HELP and CDX mutators and records overlaps among source-contract, command,
messaging, Data Dictionary, SelfDoc, manual, and diagram systems.

Only `metacollect` remains an operational entry in the SelfDoc tool/pipeline
subsets. The follow-on registry phase established
`selfdoc/metadata_system_registry_v1.json`, covering all 24 systems while
keeping default execution and promotion closed. Both active SelfDoc manifests
now point to that broader descriptive registry.

## Metadata System Registry

`METADATA_SYSTEM_REGISTRY_CONTRACT_V1.md` defines the cross-domain registry,
mutation classes, lifecycle classes, hash rule, and SelfDoc integration. The
standard-library validator checks all 24 entrypoints, hashes, related-system
references, protected mutators, manifest mappings, and closed authorization
gates. Five focused tests cover the passing registry and failure canaries.

Execution evidence is retained under
`DOCFLUSH-20260716-001/metadata_registry_phase/`. Registration does not execute
collectors, authorize CMDHELP or CDX mutation, or promote candidate data.

## Reference Identity Authority

`REFERENCE_IDENTITY_AUTHORITY_CONTRACT_V1.md` and
`selfdoc/reference_identity_authority_v1.json` define stable logical keys and
field-level authority for commands, subcommands, functions, arguments, and
entry variants. The contract preserves runtime/source/HELP/metadata/validator
roles and forbids last-writer-wins merging.

The current evidence check passes for 331 reference identities, 65 function
candidates, and 221 argument candidates with no duplicate logical keys or
current legacy-id collisions. Execution evidence is under
`DOCFLUSH-20260716-001/identity_contract_phase/`. No HELP build or metadata load
is part of this contract phase.

The follow-on authority crosswalk contains 593 provenance-bearing rows: 307
commands, 65 functions, and 221 arguments. Twenty-four EDREF-only topics remain
outside command identity. The CMDHELPCHK v2 canonical implementation is now
`dottalkpp/tools/help/cmdhelpchk_v2_scan.py`; the older root implementation is
preserved byte-for-byte in `tools/help/attic`, and its former path is a
compatibility launcher.

## Gate 6 Website Feed

`tools/fullstack_docs/build_website_feed_packet.py` and
`validate_website_feed_packet.py` provide the Python 3.12 report-only handoff
from the public manual commit to the maintained website repository. The builder
binds Git blobs, accepted manual counts, current website file hashes, proof
labels, public source URLs, and proposed route actions without writing the site.
The independent validator rechecks packet hashes, source blobs, route identity,
target existence, website baseline state, and zero mutation authority.

The passing `WEBSITEFEED-20260718T155242Z` packet proposes 11 Gate 7 targets:
two creates, eight updates, and one exact manual-download replacement. It finds
the existing website manual stale at 3,828 lines / 212 headings against the
public 4,118-line / 237-heading artifact, and flags two obsolete Python 3.11
validation statements for reviewed correction. Website files, build, commit,
push, deployment, and the metacollect-238 mission remain unchanged.

## Gate 7 Website Integration

Gate 7 is split into an exact plan and a bounded local apply:

- plan: `GATE7PLAN-20260718T160428Z`;
- apply/build: `GATE7APPLY-20260718T162939Z`;
- website baseline: `a69e0ec0` on `codex/lean-sites-publish`;
- transaction: two creates, eight updates, one exact manual replacement;
- build: 117 static pages, public-content guard and TypeScript PASS;
- validation: 32/32 full-stack tests, post-apply validator PASS with zero
  findings, and `git diff --check` PASS.

The website manual and generated download are byte-exact to public source Git
blob SHA-256 `09B593E9...B13B`. Package, lockfile, and hosting configuration
remain unchanged. Gate 7 deliberately leaves the 11-path website diff
uncommitted; commit, push, GitHub Pages publication, and live verification are
Gates 8 and 9.

## Gates 8-9 Public Publication

The approved Gate 7 transaction was committed as website source `43f120a4` and
published as `gh-pages` commit `0ef77ea9`. GitHub Pages build `1102357325`
reports `built` with HTTPS enforced.

Gate 9 read the public products with a unique cache-busting query:

- `/downloads/`: HTTP 200;
- `/docs/dottalk/command-reference/`: HTTP 200, previously 404;
- publication announcement: HTTP 200, previously 404;
- download manifest and release metadata: HTTP 200 and source-bound;
- Markdown manual: exact SHA-256 `09B593E9...B13B`, 4,118 lines, 237 headings.

This completes all nine gates in `DOCFLUSH-20260716-001`. The private Sites
mirror was not used because GitHub Pages is the canonical public lane. The
metacollect-238 findings remain a separate mission.

## Public Projection Test Boundary

The public staging projection includes the reusable validators and their
self-contained unit tests, but it does not publish candidate-only metacollect
tables, generated manual disposition runs, or locally retained raw benchmark
transcripts. Repository-integration tests that require those development
inputs run normally in `D:\code\ccode` and report a named skip in a clean public
projection. Hermetic parser, identity, arithmetic, and failure-canary tests
still run in both locations. This is an evidence-authority boundary, not a
substitute for a passing development test run.
