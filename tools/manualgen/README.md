# Manualgen Python 3.12 Engine

This directory contains the Python 3.12 manual regeneration engine and candidate-review commands for the DotTalk++ / x64base Developer Manual.

MDO-222 created the bootstrap and structured logging contract.
MDO-223 adds read/report-only `inventory` and `validate` commands.

## Commands

```powershell
$py12 = 'C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe'
& $py12 .\tools\manualgen\manualgen.py version
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested inventory
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested validate
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested export-manifest
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-dry-run
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested parity-review
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-reference-candidate
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-curation-candidate
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-disposition-candidate
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-structural-reconciliation
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-section-delta-candidates
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-prose-review-batch
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-selective-merge-candidate
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer --publication-workspace developer_manual_publication_v1_media_section_v1 --harvest-workspace docs\manuals\developer\manualgen\harvested build-controlled-acceptance-plan --candidate-run MANRUN-20260718T031554Z-F1F59445 --pointer-audit docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260716-001\manualgen_phase\post_help_refresh_20260717\publication_ascent_preflight_v1\pointer_evidence_reconciliation_20260718T025559Z\after_audit\manual_documentation_pointer_audit_v1.json --context-decision docs\maintenance\lanes\full_stack_documentation\MANUALGEN_SELECTIVE_MERGE_EOF_RECONCILIATION_2026-07-18.md
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer apply-controlled-acceptance --plan-run MANRUN-20260718T031714Z-1A3F1333 --authorization-record docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260716-001\manualgen_phase\post_help_refresh_20260717\publication_ascent_preflight_v1\CANONICAL_APPLY_AUTHORIZATION_2026-07-18.md
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-command-reference-candidate --reference-run MANRUN-20260717T222026Z-28C704E0 --disposition-run MANRUN-20260717T230554Z-DB3F2DC8
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-command-reference-review-book --candidate-run MANRUN-20260718T034751Z-B7DC1EEB
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer build-publication-structure-candidate
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog status
& $py12 .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog counts
```

Python 3.12 is mandatory for repository Python work. Do not fall back to a
shell-resolved 3.11 or 3.13 interpreter when dependencies are missing; report
or repair the 3.12 environment instead. The repository root `.python-version`
records this selection. On the current maintainer workstation the verified
interpreter is:

```powershell
C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe
```

## Assembly workspace selection

Use `--publication-workspace <workspace-id-or-path>` for every evidence-bearing
run. Despite the historical option name, this selects the workspace used for
inventory and dry-run assembly; it does not claim publication authority or
promote that workspace.

The option accepts a discovered workspace id, a repo-relative path, or an
absolute path. An explicit value that does not identify a discovered workspace
fails closed. Omitting the option retains the historical selection order for
backward compatibility, but validation marks that implicit selection for
review.

## HELP/META harvest selection

Evidence-bearing runs must also pass `--harvest-workspace <directory>`. The
directory may be repo-relative or absolute and must contain the six `HELP_*`
and eight `META_*` CSV contracts. Manualgen inventories every required file,
records its row count, header, and SHA-256, and embeds that inventory in dry-run
and exported manifests. It does not copy the files into the canonical
`harvested/` directory and does not promote their data.

Omitting the option reads the legacy `harvested/` directory for compatibility,
but validation marks the selection for review. A missing explicit directory or
missing required CSV fails closed.

`build-reference-candidate` creates a human-view Markdown projection, a
row-level HELP-line lineage CSV, a command-to-topic resolution ledger, and a hash-bearing manifest beneath
`generated/manualgen_reference_candidates/<run-id>/`. It renders all selected
topics and HELP lines mechanically. The output is a review candidate, not an
accepted manual section or publication.

Blank-key global messages and unscoped source facts remain classified
non-topic evidence. FOX compact legacy SET command keys resolve only when the
corresponding spaced physical topic exists; every such resolution is recorded
and the harvested CSVs are never rewritten.

`build-curation-candidate` partitions every topic and HELP line into stable
review shelves. It writes one topic ledger, one line ledger, shelf-specific
human packets, and a coverage manifest. Developer/internal material is excluded
from public-manual inclusion by default; system messages and source facts stay
in separate appendices. The command does not edit existing manual sections.

`build-disposition-candidate` applies the explicit 49-topic policy, validates
all canonical alias targets and evidence-bearing inclusions, and emits the
approved topic ledger plus five candidate-only section-factory packets. Alias,
source-fact, diagnostic, and deferred rows remain in the disposition ledger and
do not silently become manual sections.

`build-structural-reconciliation` consumes the latest disposition candidate,
records the 24-section primary body and both controlled 25-section overlays,
and maps every approved topic to an existing section or a candidate-only
partial-HELP appendix. It emits baseline, topic, and section-delta ledgers plus
a human proposal and hash manifest. It does not replace a section, promote an
overlay, or change the primary reader pointer.
The explicit 13-topic structural review policy records source/HELP/DOTREF-backed
targets and rationales; invalid targets, missing policy topics, and residual
review fallbacks fail the reconciliation closed.

`build-section-delta-candidates` copies all 462 approved topic blocks intact
from the disposition packets and regroups them into hash-bound, per-target
additive delta packets. It fails on missing, duplicate, unused, or unmapped
topic blocks and does not edit any existing section or appendix.

`build-prose-review-batch` opens the human prose gate with the three smallest
packets: Runtime Evidence, Command Surface, and the candidate Partial HELP
appendix. It validates the eight selected topic identities and packet hashes,
checks every proposed anchor against the current primary section hash, and
emits three candidate-only prose fragments plus a disposition ledger and batch
manifest. It does not merge those fragments into the manual.

`build-selective-merge-candidate` requires the durable human-review decision
for a passing prose batch. It inserts the reviewed fragments after complete
named subsections in copied section sources, creates a separate candidate
Partial HELP appendix, and produces a full contextual reader plus unified
diffs. Every canonical input is checked by hash before and after generation;
all outputs remain beneath `generated/`.

`build-controlled-acceptance-plan` requires an exact selective-merge run, a
green pointer-audit JSON, and the durable canonical-preflight context decision.
It independently reconstructs the two sections, Partial HELP appendix, and
reader without the candidate banner; emits eight allow-listed future mutation
rows plus planned evidence previews; and has no apply option. Canonical files,
accepted records, reader pointers, and publication authority remain unchanged.

`apply-controlled-acceptance` requires an exact passing plan run and an
authorization record bound to both the plan-manifest and mutation-ledger
hashes. It is Python 3.12-only, verifies every before/candidate hash, creates a
byte-preserved backup and staged-after set, applies only the eight allow-listed
targets with atomic replacements, verifies every after hash, and emits a
standalone guarded rollback command. It never changes the reader pointer,
MAN* catalogs, HELP/META, source staging, or website surfaces.

`build-command-reference-candidate` reads the accepted reader without changing
it, resolves its 164 command-reference links against an exact passing HELP
topic-reference run and review-disposition run, and emits one candidate page
per link plus page, row-lineage, and link-context ledgers. Public page bodies
exclude source-fact rows and workstation drive paths. The command records the
different section-source and combined-reader relative-link requirements but
does not project pages into publication, rewrite links, or claim authority.

`build-command-reference-review-book` validates every page hash in one passing
command-reference candidate, then emits a human index with all 164 page links
and a single combined Markdown review book. It does not modify the source
candidate, accepted reader, pointer, or website. A current-reader hash drift is
recorded in the review-book manifest but does not rewrite accepted evidence.

`build-publication-structure-candidate` reads the exact accepted-reader bytes,
proposes the eleven missing END markers, and emits a 14-row status-disposition
ledger. Its preview preserves every historical status in an HTML comment and
shows `REVIEWED_FOR_PUBLICATION` as a proposed replacement. It does not edit the
accepted reader; each status row must be confirmed or held before acceptance.

`build-gate4-acceptance-plan` binds one passing 164-page command-reference run,
one passing publication-structure run, and the exact all-row status approval.
It stages all proposed publication files beneath `generated/`, including the
164 pages, their human index, the balanced reader with reader-relative links,
the 14 persistent section-status updates, and refreshed acceptance records.
Every create or replacement has a before hash and staged hash in the mutation
ledger. The standalone Navigation status and appendix review states remain
outside the 14-row approval. This command has no canonical apply path; an apply
authorization must name the resulting plan-manifest and mutation-ledger hashes.

`apply-gate4-acceptance` requires that exact plan run plus a durable JSON
authorization bound to both package hashes and all 183 targets. It rechecks
every before and staged hash, backs up the 17 existing targets, materializes a
complete staged-after manifest, applies command pages before the reader and
acceptance records, and verifies every final hash. Any partial failure triggers
automatic rollback. The retained backup also includes a guarded Python 3.12
rollback command. Apply-time finalization changes only the three acceptance
records named by the authorization; reader pointer, HELP/META, product source,
and website remain outside the allow-list.

`build-gate5-source-gap-candidate` consumes the 19-row standalone-section link
gap ledger left by Gate 4, the seven-occurrence held-status ledger, and the
same hash-bound HELP/disposition evidence used by the accepted command
reference. It fails unless all 19 source links still match the ledgers and
resolve to approved HELP topics. The output includes 19 candidate pages,
lineage, an index, a combined review book, four logical status decisions, and a
report-only `PROMOTE.manifest` delta. It does not change the accepted manual,
`C:\x64base`, or the website.

`build-gate5-development-plan` requires the exact passing Gate 5 candidate and
a durable disposition record bound to its manifest, page ledger, status
ledger, and `PROMOTE.manifest` delta hashes. It stages 25 proposed development
targets beneath `generated/`: 19 supplemental pages, a repaired accepted index
with 183 links, the Navigation status with its historical value retained,
three synchronized acceptance records, and the 20-entry allow-list delta. The
accepted reader remains byte-identical and the three appendix review states
remain held. The command has no apply path and does not write `C:\x64base`.

`apply-gate5-development-plan` requires a durable authorization bound to the
exact plan-manifest and mutation-ledger hashes, all 25 targets, and the three
acceptance-record finalizations. It rechecks every before/staged hash, preserves
all six existing targets, applies 19 pages before the index and evidence
records, and verifies every final hash. The retained rollback refuses to run if
any applied target has subsequently drifted. The accepted reader, reader
pointer, HELP/META, product source, appendices, `C:\x64base`, Git, and website
remain outside the apply allow-list.

The promoted test suite keeps parsing coverage independent of generated run
directories. Candidate disposition packets remain development evidence and
are deliberately absent from the public projection; their 462-topic
integration assertion runs when that evidence is present and is reported as
an explicit skip when it is not. A temporary two-topic packet exercises the
same parser in every projection.

## Boundary

These commands write reports and structured logs only. They do not rebuild publication, alter media files, create x64base tables, create C++ files, or mutate HELP/META/CMDHELPCHK/source/runtime data.
