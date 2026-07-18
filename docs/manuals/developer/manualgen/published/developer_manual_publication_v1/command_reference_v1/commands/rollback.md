<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ROLLBACK

- Catalog/topic: `DOT` / `ROLLBACK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Discard staged TABLE/buffered changes without committing them; operational behavior depends on the current buffering state.

- Discard buffered/uncommitted table changes for the current area or all areas.

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

## Provenance

- Topic key: `DOT|ROLLBACK`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
