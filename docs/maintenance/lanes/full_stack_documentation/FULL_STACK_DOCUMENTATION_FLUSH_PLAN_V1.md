# Full Stack Documentation Flush Plan v1

Status: active; HELP refresh validated; reader ledger and overlay candidate complete; promotion review pending  
Created: 2026-07-16  
Initial scope: `include/*ref.hpp` through `CMDHELP`, `CMDHELPCHK`, SelfDoc,
manualgen, and reviewed publication pointers

## Outcome

Produce a traceable documentation refresh in which every promoted manual or
publication claim can be followed back to current source/runtime evidence, and
every generated-data mutation is isolated behind a reviewed gate.

The first run improves both the data and the pipeline, but it does so in two
separate passes:

1. prove and document the current pipeline;
2. authorize and execute narrowly scoped refreshes based on the observed drift.

## Scope

### In scope

- `include/dotref.hpp`, `include/foxref.hpp`, and `include/edref.hpp`;
- command registration and `@dottalk.usage v1` blocks;
- comments/source-evidence harvesting boundaries;
- current and legacy `CMDHELP` build paths;
- HELP DATA tables and reader surfaces;
- `CMDHELPCHK` validation;
- report-only metadata candidate refresh when inputs changed;
- SelfDoc pipeline and provenance records;
- manualgen inventory, validation, exported manifests, dry-run candidate, and parity review;
- accepted/canonical/reader pointer review;
- a reviewed handoff to website/publication lanes when warranted.

### Out of scope until separately authorized

- broad source cleanup or reference-header rewriting;
- blind HELP DBF, CDX, or LMDB replacement;
- live metadata import;
- accepted `MAN*` catalog replacement;
- automatic manual publication replacement;
- website edits or public push;
- branch changes, broad staging, or cleanup of the dirty development tree.

## Pipeline Model

| Stage | Owner | Primary inputs | Output or proof | Default mode |
| --- | --- | --- | --- | --- |
| 0. Baseline | full-stack lane | git state, current pointers, prior reports | run record and drift inventory | report-only |
| 1. Source truth | runtime/source | registrations, implementations, usage contracts | source inventory and targeted runtime proof | report-only unless repair approved |
| 2. Reference catalogs | HELP/router | `dotref.hpp`, `foxref.hpp`, `edref.hpp` | compiled catalog inventory and router smoke | report-only unless repair approved |
| 3. Comments evidence | comments/SelfDoc | source headers and contracts | provenance tables/reports | report-only; reload is gated |
| 4. Legacy HELP | HELP | curated reference catalogs | `commands.dbf`, `cmd_args.dbf` | reviewed mutation |
| 5. Current HELP DATA | HELP | registry, refs, usage contracts, source miner | HELP topic/section/line/artifact family | reviewed mutation |
| 6. Validation | CMDHELPCHK | source, reflection, HELP artifacts | checkpoint report and runtime transcript | report-only |
| 7. Metadata | metadata | source/help evidence | facts, compare reports, candidate CSVs | report-only; import is gated |
| 8. Provenance | SelfDoc | commands, inputs, hashes, outputs | pipeline/tool/run evidence | report-only documentation |
| 9. Manual candidate | manualgen | reviewed evidence and current publication | inventory, validate, dry-run, parity reports | candidate-only |
| 10. Promotion | manual/publication owner | reviewed candidate and manifest | accepted artifacts and active pointers | reviewed mutation |
| 11. Public projection | website/publication owner | reviewed promoted docs | staged/public snapshot | separate authorization |

## Known Pipeline Facts to Preserve

1. `CMDHELP BUILD` writes current HELP DATA DBFs.
2. `CMDHELP BUILD V2` is a compatibility alias for the current build.
3. `CMDHELP BUILD LEGACY` drives the old `commands.dbf` / `cmd_args.dbf` path.
4. Current operator doctrine says that a `dotref.hpp` change requires legacy
   build first, followed by the current build.
5. `CMDHELP` visibility does not prove `DOTHELP`, `FOXHELP`, or `HELP /DOT`
   router visibility; those surfaces require separate smoke proof.
6. `CMDHELPCHK` validates alignment but does not replace source or runtime proof.
7. `metacollect` is a read-only candidate/report tool; it is not a live metadata writer.
8. The Python manualgen engine writes reports, logs, manifests, and dry-run
   candidates; it does not itself authorize publication replacement.
9. The canonical manual manifest, current-state manifest, current-publication
   manifest, and active-reader pointer must agree before a manual is called current.

## Execution Plan

### Phase 0: Create the run envelope

- Assign `DOCFLUSH-YYYYMMDD-NNN`.
- Copy the flush-record template into a dated run record.
- Capture branch, HEAD, concise status for in-scope paths, and existing pointer values.
- Record the exact executable and Python interpreter intended for proof.
- Hash the in-scope `*ref.hpp` inputs and active manual pointers.

Gate 0 acceptance:

- no generated catalog has been changed;
- inputs, authorities, protected systems, and rollback expectations are named;
- unrelated dirty work is explicitly excluded.

### Phase 1: Inventory and classify source/reference drift

- Inventory `dotref`, `foxref`, and `edref` item identities and duplicates.
- Compare reference identities with command registration and usage-contract identities.
- Classify differences as source defect, curated-reference gap, deliberate alias,
  developer-only surface, stale HELP, or unresolved.
- Do not edit a header merely to make counts match.

Gate 1 acceptance:

- each proposed edit names the owning authority and evidence;
- alias and developer-only differences are not mislabeled as defects;
- source changes, if needed, receive their own contract preflight and approval.

### Phase 2: Capture the pre-refresh runtime baseline

Use the currently intended binary and record, at minimum:

```text
CMDHELP
CMDHELP USAGE
CMDHELPCHK
DOTHELP
FOXHELP
HELP
MANUAL STATUS
MANUAL COUNTS
```

Add targeted topic checks for every proposed change.

Gate 2 acceptance:

- transcript names the binary path, timestamp, data root, and exit state;
- failures are assigned to a layer instead of repaired opportunistically.

### Phase 3: Prepare a reviewed HELP refresh package

Before executing either build, record:

- why a build is required;
- which input changed;
- HELP/legacy files expected to change;
- pre-build hashes or a backup manifest;
- rollback procedure;
- post-build checks.

Current conditional order:

```text
if include/dotref.hpp changed:
    CMDHELP BUILD LEGACY
    CMDHELP BUILD . D:\code\ccode\src
else if current HELP inputs changed:
    CMDHELP BUILD . D:\code\ccode\src
```

Do not infer that every `*ref.hpp` change requires the legacy build. The
documented trigger is currently `dotref.hpp`; changes to `foxref.hpp` or
`edref.hpp` must be classified against the implementation before execution.

Gate 3 acceptance:

- maintainer authorizes the named mutation package;
- backup/rollback and affected paths are concrete;
- the build is not bundled with manual publication or metadata import.

### Phase 4: Execute HELP refresh and same-pass validation

After authorization:

1. run only the approved build sequence;
2. capture changed-file and table-count deltas;
3. run `CMDHELPCHK` and targeted artifact/reflection modes;
4. smoke `CMDHELP`, `HELP`, `DOTHELP`, `FOXHELP`, and affected topics;
5. retain the transcript and boundary ledger.

Gate 4 acceptance:

- the current and legacy outputs are distinguished;
- all target reader surfaces agree or remaining drift is recorded;
- no manual or metadata promotion is implied by a green HELP build.

### Phase 5: Refresh organizing and provenance layers

- Run `metacollect` only when source/function/argument inputs changed.
- Store facts/compare outputs and candidate CSVs as candidates.
- Update SelfDoc tool/pipeline/run provenance with input/output hashes.
- Do not import candidates into live metadata without a separate reviewed gate.

Gate 5 acceptance:

- candidate and live data are visibly distinct;
- no external helper is presented as authority;
- the run record accounts for every generated report.

### Phase 6: Generate and review a manual candidate

Use the manualgen engine in this order:

```powershell
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer inventory
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer validate
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer export-manifest
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-dry-run
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer parity-review
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-reference-candidate
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-curation-candidate
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-disposition-candidate
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-structural-reconciliation
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-section-delta-candidates
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-prose-review-batch
python .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-selective-merge-candidate
```

Record the Python path and manualgen version. Treat all outputs as reports or
candidates until review explicitly promotes them. Evidence-bearing runs also
pass the explicit `--publication-workspace` and `--harvest-workspace` selected
for the run; the abbreviated examples above do not grant implicit-selection
authority.

Gate 6 acceptance:

- validation is green or exceptions are named;
- dry-run and current publication differences are reviewed by topic;
- candidate provenance reaches the HELP/source evidence used in this run;
- prose-review batches retain exact packet hashes, target hashes, topic
  dispositions, and insertion anchors;
- no active pointer changed.

### Phase 7: Review and promote narrowly

Review these states separately:

1. candidate workspace;
2. accepted/canonical manifest;
3. active primary reader artifact;
4. current publication manifest;
5. website/public projection.

Promotion requires a manifest listing exact source and destination paths,
hashes, review decision, rollback, and post-promotion validation.

Gate 7 acceptance:

- pointer values agree with the artifact actually reviewed;
- accepted catalogs and reader artifacts agree;
- website/publication work is handed to its own lane;
- the development-tree run closes before any public push is claimed.

## Workflow Improvements Required by the First Run

The first run should produce evidence for these improvements:

- one machine-readable inventory joining ref identity, source registration,
  usage contract, HELP topic, metadata identity, and manual page;
- one pre/post manifest for HELP DATA and legacy compatibility files;
- one command transcript format carrying binary, data root, locale, and exit state;
- one pointer-consistency check for canonical manifest, publication manifest,
  active reader, and manual catalog;
- one run closeout that separates development refresh, candidate generation,
  promotion, staging, commit, and push states.

These are desired outputs of the run, not permission to implement or execute
all of them during lane setup.

### Implemented comments checkpoint

`DOCFLUSH-20260716-001` now provides:

- a deterministic baseline/current comments drift inventory;
- a P1 evidence reconciliation against Git, worktree, and closeout records;
- an isolated `SRCFILE.HASH` candidate with existing `SRC*` row inventories
  preserved;
- a separate usage-contract delta instead of a lossy metadata replacement;
- a default refusal gate on header-only replacement of an existing file slice.

The missing replacement generator was restored as
`tools/comments/reharvest_source_comment_catalog.py`. It regenerates every
dependent leading-header and usage-contract row across the current C-family
scope, retains reviewed policy tables, records current whole-file hashes, and
writes a candidate-only replacement package. The candidate must remain
unloaded until its P1 review items and a full-reload/rollback manifest are
approved.

### Current phase checkpoint

The first run completed the static DOTREF/FOXREF/EDREF/registry/usage identity
join, the maintainer-executed legacy/current HELP refresh, an 18-file recovery
proof, and the post-refresh runtime transcript. Reflection remains green.
Topics increased from 473 to 481, line rows from 10,846 to 11,410, artifacts
from 6,926 to 7,264, and orphan command-key rows fell from 461 to 373. Nine
compact SET-family canonicalization errors and 18 blank artifact texts remain.

Phase 6 report/candidate work is also complete under Python 3.12.9: validation
and boundary checks are green, the dry-run contains all 25 explicitly selected
assembly-reference sections, and the five non-failing parity checks resolve to
generated assembly-header metadata plus one 118-line MDO-261/MDO-270 trailing
overlay. Manualgen now requires an explicit workspace selector for evidence-
bearing runs, classifies the supporting role, and claims no publication
authority. The MAN*
catalog reader now reports 8 tables and zero drift after a case-normalization
repair with regression coverage. The pointer-consistency audit has no broken
targets but records stale reader hash/line-count evidence, an incomplete
post-MDO-318 hash-bearing reader chain, and distinct supporting publication
workspaces. The manual authority reconciliation contract and candidate package
now make those roles explicit. A mutation ledger partitions the 247-line
post-MDO-318 reader delta, and a two-file ordered overlay candidate corrects the
MDO-261/MDO-270 Markdown defects without registering or promoting them. Phase 7
promotion review remains the active gate; no accepted catalog, publication, or
pointer was changed.

The accepted Stage C metadata checkpoint is also complete as a candidate-only
metacollect reharvest. A dedicated Release build returned 1,071 facts, 131
comparison issues, 65 SYSFUNC rows, 221 standard SYSARGS rows, and 942
diagnostic SYSARGS rows. Existing root reports, tracked seed exports, live
metadata DBFs, HELP, COMMENTS, and accepted pointers were not replaced. Review
of the command, function-authority, and usage-contract deltas is required before
any promotion.

A repository-wide metadata systems pass now identifies 24 distinct systems
behind the generic `meta` label. The resulting inventory separates source
provenance, contract discovery, runtime reflection, HELP construction,
validation, physical schema/index integrity, messaging seeds, SelfDoc/manual
aggregation, diagram projection, and AI report provenance. Only metacollect is registered in the
current SelfDoc manifests. The next workflow contract is therefore a reviewed
metadata systems registry with explicit authority, lifecycle, mutation class,
dependencies, and last-verified evidence; registry work does not itself
authorize execution or promotion.

That registry gate is now implemented. The 24-system JSON registry is governed
by `METADATA_SYSTEM_REGISTRY_CONTRACT_V1.md`, linked from both active SelfDoc
manifests, and checked by a standard-library validator plus five focused tests.
All entries keep default execution and promotion false; CMDHELP and the CDX
sidecar writer are explicitly classified as protected mutators. The remaining
work is overlap disposition, beginning with shared command identity,
source-contract probe lineage, CMDHELPCHK v2 lineage, and messaging exporters.

The shared identity gate is now established. Commands, subcommands, functions,
arguments, and entry variants have namespace-qualified logical keys and
field-level authority order in a machine-readable SelfDoc map. The validator
confirms the current 331 reference, 65 function, and 221 argument candidates
without duplicate logical keys or legacy-id collisions. The legacy argument id
format remains a projection with an explicit future collision gate; no schema
or live metadata change was made.

## Definition of Done

A full-stack documentation flush is complete only when:

- source/reference changes are reviewed and proven;
- HELP build mutations, if any, have backup and same-pass validation;
- `CMDHELPCHK` and reader surfaces have retained proof;
- metadata remains candidate-only unless separately promoted;
- SelfDoc records inputs, outputs, hashes, commands, and boundaries;
- manualgen has a reviewed candidate and parity result;
- accepted and active pointers agree after any promotion;
- unresolved drift is explicit;
- publication, commit, and push states are reported separately and truthfully.
