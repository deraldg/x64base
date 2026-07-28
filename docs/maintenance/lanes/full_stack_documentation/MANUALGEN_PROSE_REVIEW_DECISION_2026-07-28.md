# Manualgen Prose Review Decision — 2026-07-28

Decision: approved for non-published selective merge candidate.

- Owner: member.derald
- Run: DOCFLUSH-20260722-001 (AIF-068)
- Supersedes: `MANUALGEN_PROSE_REVIEW_DECISION_2026-07-17.md` (previous cycle,
  8-topic baseline). This cycle re-baselines the prose review to the current
  16-topic policy after the fresh HELP/META harvest.

## Reviewed batch

- Prose review run: `MANRUN-20260728T013323Z-6C6EBB28`
- Manifest: `docs/manuals/developer/manualgen/generated/manualgen_prose_review_batches/MANRUN-20260728T013323Z-6C6EBB28/manual_prose_review_batch_manifest.json`
- Batch result: `status=PASS`, input topics 16/16, candidate files 3,
  missing 0, unexpected 0, duplicate 0, packet-hash failures 0, missing
  anchors 0.
- Human assessment: the three candidates (runtime proof launchers, command
  surface notes, partial-HELP appendix) are accurate and intentionally
  additive. The expanded scope over the previous cycle is the eight
  current-harvest review topics: `DOT|DEFCMD`, `DOT|UNDEFCMD`, `UI|RECORD`,
  `UI|RECORDVIEW` (contracted, command-surface additive) and `DOT|UDATE`,
  `DOT|UDATETIME`, `DOT|UNOW`, `DOT|UTIME` (uncontracted date helpers, kept in
  the partial-HELP appendix pending a source usage contract). All are labeled
  and none overclaims runtime support.

## Hash reconciliation

None required. The selective-merge preflight against this run's manifest
reports all three reviewed candidate files and both canonical section targets
(`runtime_evidence_source_verification_and_canary_closure`,
`command_surface_dispatch_and_entry_variants`) byte-identical to the recorded
hashes. Mechanical merge uses this same run's manifest directly.

## Authorized continuation

The three reviewed prose files may be inserted into copied section sources and
a generated, non-published combined reader for contextual review. The exact
reviewed prose, recorded anchors, upstream hashes, and partial-HELP boundary
must be preserved.

## Not authorized

This decision does not authorize edits to the canonical section sources,
acceptance of the Partial HELP appendix, rebuilding or replacing an accepted
reader, changing a pointer, publishing externally, staging, committing, or
pushing.
