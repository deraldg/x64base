<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# GPS

- Catalog/topic: `DOT` / `GPS`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Report current work-area position, including area slot, table label, physical record number, computed logical row, and the workspace that OWNS the area beside the session's CURRENT workspace.

## Status

- implemented=yes; supported=yes

## Syntax

- GPS
- GPS USAGE

## Usage

- GPS
- GPS USAGE

## Note

- GPS with no arguments reports cursor position.
- GPS with no open table reports the current area and no-table state.
- GPS computes logical row by streaming the active order and counting visible records up to the physical record the cursor is on.
- GPS is an instrument. It restores the cursor and the record buffer it moved, so the position it reports is the position that survives the call.
- GPS reports WHY there is no logical row when there is none. It never prints a row number that was not derived.
- GPS rejects arguments it does not recognize rather than treating an unrecognized argument as a request for a position report.
- GPS reports BOTH the owning and the current workspace, always, including when they agree -- "they agree" and "this build does not check" must not look alike (the R112 ledger's rule). An area owned by nothing reads
- "(none)", which is a real state rather than an error.

## Related

- GOTO
- SKIP
- AREA
- STATUS

## Provenance

- Topic key: `DOT|GPS`
- Included HELP rows: `25`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
