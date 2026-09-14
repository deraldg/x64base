<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ROLLBACK

- Catalog/topic: `DOT` / `ROLLBACK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Discard buffered/uncommitted table changes for the current area or all areas.

## Status

- implemented=yes; supported=yes

## Syntax

- ROLLBACK [USAGE|HELP|?]

## Usage

- ROLLBACK USAGE
- ROLLBACK
- ROLLBACK ALL

## Example

- ROLLBACK
- ROLLBACK ALL

## Note

- ROLLBACK USAGE returns before modifying buffer state.
- ROLLBACK without arguments clears buffered state for the current area.
- ROLLBACK ALL clears buffered state across all areas.
- ROLLBACK best-effort notes a ROLLBACK marker in the durable journal for the area.

## Related

- COMMIT
- TABLE BUFFER

## Provenance

- Topic key: `DOT|ROLLBACK`
- Included HELP rows: `15`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
