<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TUPLEDELTA

- Catalog/topic: `DOT` / `TUPLEDELTA`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Tuple diagnostic helper surface for comparing projected tuple output or tuple-state deltas.

- Compare two named tuple streams and report insert, delete, and update deltas. The loader remains a skeleton until tuple stream storage is finalized.

## Status

- implemented=yes; supported=yes

## Syntax

- TUPLEDELTA [USAGE|&lt;args...&gt;]

## Usage

- TUPLEDELTA USAGE
- TUPLEDELTA &lt;baseline-stream&gt; &lt;current-stream&gt;

## Note

- TUPLEDELTA requires two stream names except for TUPLEDELTA USAGE.
- Tuple stream loading is not implemented in this skeleton.
- REC_ID or PRIMARY UNIQUE is intended to be the identity key.
- Field-level diffing is intentionally stubbed for now.
- TUPLEDELTA is diagnostic and does not mutate table or index data.

## Provenance

- Topic key: `DOT|TUPLEDELTA`
- Included HELP rows: `11`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
