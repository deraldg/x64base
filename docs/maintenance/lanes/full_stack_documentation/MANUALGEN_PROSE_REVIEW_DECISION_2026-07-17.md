# Manualgen Prose Review Decision — 2026-07-17

Decision: approved for non-published selective merge candidate.

## Reviewed batch

- Prose review run: `MANRUN-20260718T012220Z-6CF3FC93`
- Manifest: `docs/manuals/developer/manualgen/generated/manualgen_prose_review_batches/MANRUN-20260718T012220Z-6CF3FC93/manual_prose_review_batch_manifest.json`
- Human assessment: the three candidates look good; their intentionally scant
  scope is acceptable for this first gate.

## Hash reconciliation

The first selective-merge preflight detected byte-hash drift in all three
reviewed files after newline normalization and failed closed. Normalized UTF-8
text comparison reports all three files equal to the originally reviewed
content. Manualgen regenerated the same prose as passing run
`MANRUN-20260718T020630Z-9367A5BA`.

The hash-reconciled manifest used for mechanical merge is:

`docs/manuals/developer/manualgen/generated/manualgen_prose_review_batches/MANRUN-20260718T020630Z-9367A5BA/manual_prose_review_batch_manifest.json`

This reconciliation changes byte lineage only; it does not expand the approved
prose or its scope.

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
