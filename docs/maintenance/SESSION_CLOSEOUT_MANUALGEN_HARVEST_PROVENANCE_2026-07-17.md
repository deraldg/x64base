---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260717-005
  recorded_at_utc: 2026-07-17T22:02:45Z
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  authorization:
    requested_by: maintainer
    scope: continue the full-stack documentation vertical flush after the authorized HELP refresh without publishing the manual
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_MANUALGEN_HARVEST_PROVENANCE_2026-07-17.md
    kind: session_closeout
---

# Session Closeout — Manualgen harvest provenance

Date: 2026-07-17.  
Owning lifecycle: DotTalk++ SDLC.  
SDLC lane: documentation assembly and evidence provenance.  
Truth state: tool- and report-proven.  
Publication state: candidate only.

## One-line summary

Manualgen now binds every evidence-bearing run to an explicit, hashed 14-file
HELP/META snapshot, carries all 462 approved topics through structural and
per-section packets, and has opened the prose gate with three anchored
smallest-packet candidates plus a full non-published selective-merge reader;
accepted manual sections and publication remain untouched.

## Changed

- Added `--harvest-workspace` with fail-closed explicit directory selection.
- Added inventory, validation, report, manifest, and dry-run provenance for six
  HELP and eight META CSV contracts.
- Added a reusable harvest comparator and regression tests.
- Added `build-reference-candidate`, producing candidate Markdown, 12,784-row
  lineage, a command-resolution ledger, and a hash-bearing transform manifest.
- Extended parity classification so harvest-provenance comments are correctly
  treated as generated metadata rather than manual content.
- Added the lane contract
  `MANUALGEN_HELP_META_HARVEST_INPUT_CONTRACT_V1.md`.
- Added `build-curation-candidate` and
  `MANUALGEN_TOPIC_CURATION_CONTRACT_V1.md`, producing nine review packets plus
  complete topic and line ledgers.
- Added `build-disposition-candidate` and
  `MANUALGEN_REVIEW_DISPOSITION_CONTRACT_V1.md`, closing all 49 review rows and
  producing five approved section-factory packets.
- Added `build-structural-reconciliation` and
  `MANUALGEN_STRUCTURAL_RECONCILIATION_CONTRACT_V1.md`, mapping all 462 approved
  topics across the governed manual topology without authorizing replacement.
- Added `build-section-delta-candidates` and
  `MANUALGEN_SECTION_DELTA_DRAFT_CONTRACT_V1.md`, copying all approved topic
  blocks into 22 hash-bound additive target packets.
- Added `build-prose-review-batch` and
  `MANUALGEN_PROSE_REVIEW_BATCH_CONTRACT_V1.md`, classifying and drafting the
  eight topics in the three smallest packets against explicit section anchors.
- Recorded human prose approval and added `build-selective-merge-candidate`
  plus `MANUALGEN_SELECTIVE_MERGE_CANDIDATE_CONTRACT_V1.md`, producing copied
  merged sections, a candidate appendix, a contextual reader, and exact diffs.
- Added the append-only documentation-flush progress log and CSV ledger so
  future gate state is recorded during work as well as at closeout.

## Verified

- Candidate harvest: 14/14 required files, 14/14 readable headers.
- Manualgen validation: 0 FAIL, 0 REVIEW, 0 boundary FAIL.
- Harvest delta: seven compatible content changes, seven unchanged files,
  zero header changes, zero missing files.
- Row total: 21,979 canonical-May rows to 33,859 post-refresh rows.
- Core deltas: HELP commands +46, arguments +442, lines +4,690, artifacts
  +3,191, physical topics +157, and `META_SYSCMD` +163.
- Harvest-bound dry run: 25 sections, 14 attached evidence files, authority
  claimed 0.
- Section source hashes: 25/25 unchanged from the immediately preceding dry
  run.
- Human-view parity: no substantive interior differences; the known 118-line
  MDO-261/MDO-270 trailing overlay remains a separate review.
- Reference candidate: 631 topics, 12,784/12,784 HELP lines, 449 commands,
  2,506 arguments, and 203 SYSCMD rows; 0 duplicate topic keys.
- Reconciled candidate SHA-256:
  `3D36626E0623CF85C826DFDBDF578A78A3ED377EA05B5E27B5B06A500FFF7BE5`.
- All 2,656 blank-key rows are classified: 2,611 global shared-message lines,
  45 unscoped source-message facts, and zero unclassified rows.
- All eight FOX compact SET commands resolve to existing spaced topic rows via
  an explicit command-resolution ledger; unresolved command/topic rows are 0.
- Curation candidate: 631/631 topics and 12,784/12,784 lines across nine
  packets, with zero duplicate or unclassified rows.
- Public inclusion candidates: 238 DOT topics, 172 FOX topics, and 29 education
  concepts. Explicit review queue: 22 DOT, four FOX, and 23 supplemental
  topics. Five developer/internal topics remain excluded by default.
- Review disposition: 49/49 rows; 20 runtime inclusions, three partial HELP
  inclusions, nine alias merges, six source-fact routes, two developer routes,
  and nine deferrals.
- Section factory: five candidate packets containing 462 unique approved
  topics; missing/extra policy and invalid evidence/target counts are zero.
- Structural reconciliation: primary body 24, media revision 25, controlled
  runtime body 25, and governed union 26; 462/462 topics mapped with zero
  duplicates or missing targets.
- Existing placement evidence: 284 topics occur in section command lists and
  52 also occur in the three review appendices.
- Structural review: 13/13 explicit evidence-backed placements, including
  `EXITS` as read-only extension-manifest document control and
  `EXPORTFUNCTIONS` with the Functions/Expression Helpers surface; remaining
  review and unplaced counts are zero.
- Additive delta packets: 22 targets and 462/462 intact topic blocks; missing,
  duplicate, unused, and unmapped counts are zero.
- Smallest-packet prose review: 8/8 topics and three candidate files; four
  additive prose topics, one canary cross-reference, and three appendix-only
  topics; packet-hash, identity, duplicate, and anchor findings are zero.
- Selective merge candidate: two copied sections, one candidate appendix, one
  full reader, and three diffs. Section additions are 33 and 22 lines;
  deletions, hash failures, extraction failures, anchor failures, and canonical
  hash changes are zero.
- The first selective-merge attempt `MANRUN-20260718T020511Z-ADA1E01D` failed
  closed on three newline-only prose-file hash changes. Normalized text matched
  3/3; the reconciled prose run and final merge run pass without weakening the
  hash gate.
- Post-change manualgen validation run `MANRUN-20260718T020942Z-CB9E6290`:
  14/14 harvest files, 0 FAIL, 0 REVIEW, and 0 boundary failures.
- Manualgen tests: 28 pass; existing full-stack tests: 11 pass; focused
  harvest/parity tests: 4 pass; comments tests: 6 pass; SelfDoc tests: 19 pass.
- AI report audit: 12 enforced, 12 valid, 9 grandfathered, 0 findings.

## Boundary

The canonical `harvested/` directory was not replaced. No accepted pointer,
published manual, HELP/META runtime table, website, git stage, commit, push, or
external publication was changed.

The new contract records which evidence a run selected. The mechanical
reference candidate is a review product, not an accepted section set, and it
does not claim that the current 25-section prose consumes changed rows.

The curation packets are also candidate-only. Shelf inclusion means eligible
for review, not accepted prose or publication authority.

Disposition and section-factory packets retain the same boundary. An approved
candidate topic has sufficient evidence for comparison, not authority to
replace an existing section.

Structural reconciliation retains that boundary. It proposes merges and one
candidate partial-HELP appendix, records every existing section/appendix
placement, and authorizes zero wholesale replacements.

The 22 additive packets are reorganized evidence, not accepted prose. They do
not edit or supersede their target sections.

The three prose-review files are anchored editorial candidates, not merged
sections. `GENERIC` remains canary-level and the partial HELP topics remain
segregated; no support claim is promoted by drafting them.

The selective-merge package applies those files only to copies beneath
`generated/`. Its full reader is contextual review evidence, not a replacement
for the primary reader or an accepted appendix set.

## Provenance pointers

- `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/manualgen_phase/post_help_refresh_20260717/harvest_delta_v1/HELP_META_HARVEST_DELTA_V1.md`
- `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/manualgen_phase/post_help_refresh_20260717/manual_parity_harvest_bound_v1/MANUALGEN_PARITY_DELTA_CLASSIFICATION_V1.md`
- `docs/manuals/developer/manualgen/generated/manualgen_build_dry_runs/MANRUN-20260717T215917Z-176027B5/build_dry_run_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_reference_candidates/MANRUN-20260717T222026Z-28C704E0/help_topic_reference_candidate.md`
- `docs/manuals/developer/manualgen/generated/manualgen_reference_candidates/MANRUN-20260717T222026Z-28C704E0/help_topic_reference_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_reference_candidates/MANRUN-20260717T222026Z-28C704E0/help_topic_command_resolution.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_curation_candidates/MANRUN-20260717T225704Z-573F2F89/manual_curation_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_curation_candidates/MANRUN-20260717T225704Z-573F2F89/manual_topic_curation_ledger.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_curation_candidates/MANRUN-20260717T225704Z-573F2F89/manual_line_curation_ledger.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_disposition_candidates/MANRUN-20260717T230554Z-DB3F2DC8/manual_disposition_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_disposition_candidates/MANRUN-20260717T230554Z-DB3F2DC8/manual_review_topic_disposition_ledger.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_disposition_candidates/MANRUN-20260717T230554Z-DB3F2DC8/manual_section_factory_approved_topics.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_structural_reconciliations/MANRUN-20260717T233746Z-BD33A215/manual_structural_reconciliation_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_structural_reconciliations/MANRUN-20260717T233746Z-BD33A215/manual_structural_delta_proposal.md`
- `docs/manuals/developer/manualgen/generated/manualgen_structural_reconciliations/MANRUN-20260717T233746Z-BD33A215/manual_topic_structural_mapping.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_structural_reconciliations/MANRUN-20260717T233746Z-BD33A215/manual_structural_review_disposition_ledger.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_section_delta_candidates/MANRUN-20260717T234222Z-ECBB99AD/manual_section_delta_candidate_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_section_delta_candidates/MANRUN-20260717T234222Z-ECBB99AD/manual_section_delta_packet_ledger.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_prose_review_batches/MANRUN-20260718T012220Z-6CF3FC93/manual_prose_review_batch_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_prose_review_batches/MANRUN-20260718T012220Z-6CF3FC93/manual_prose_review_ledger.csv`
- `docs/manuals/developer/manualgen/generated/manualgen_prose_review_batches/MANRUN-20260718T020630Z-9367A5BA/manual_prose_review_batch_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_selective_merge_candidates/MANRUN-20260718T020658Z-BFE7F605/MANUAL_SELECTIVE_MERGE_CONTEXT_REVIEW.md`
- `docs/manuals/developer/manualgen/generated/manualgen_selective_merge_candidates/MANRUN-20260718T020658Z-BFE7F605/manual_selective_merge_candidate_manifest.json`
- `docs/manuals/developer/manualgen/generated/manualgen_selective_merge_candidates/MANRUN-20260718T020658Z-BFE7F605/developer_manual_selective_merge_candidate.md`
- `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/DOCUMENTATION_FLUSH_PROGRESS_LOG_V1.md`
- `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/documentation_flush_progress_ledger_v1.csv`
- `docs/maintenance/lanes/metadata/missions/METACOLLECT-238-20260717-001/README.md`

## Next gate

Review the full selective-merge reader and the three diffs. The next decision
is whether to open a canonical section/appendix acceptance preflight; no such
mutation is authorized yet. Canonical-harvest replacement, accepted pointers,
and publication remain separate gates. The 238-finding metadata mission also
remains separate.
