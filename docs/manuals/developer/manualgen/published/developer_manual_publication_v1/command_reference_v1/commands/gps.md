<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# GPS

- Catalog/topic: `DOT` / `GPS`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Report current session/navigation position and work-area orientation diagnostics.

- Report current work-area position, including area slot, table label, physical record number, and computed logical row.

## Status

- implemented=yes; supported=yes

## Syntax

- GPS

## Usage

- GPS
- GPS USAGE

## Note

- GPS with no arguments reports cursor position.
- GPS with no open table reports the current area and no-table state.
- GPS computes logical row by iterating visible ordered records.
- GPS is read-only for table data but may temporarily move the cursor while computing logical row.

## Provenance

- Topic key: `DOT|GPS`
- Included HELP rows: `10`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
