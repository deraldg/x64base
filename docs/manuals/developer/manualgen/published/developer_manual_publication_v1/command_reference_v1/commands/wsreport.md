<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# WSREPORT

- Catalog/topic: `DOT` / `WSREPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Workspace report / diagnostics.

- Print a workspace/status report covering open areas, LMDB/order summary, and table-buffer state.

## Status

- implemented=yes; supported=yes

## Syntax

- WSREPORT

## Usage

- WSREPORT
- WSREPORT USAGE
- WSREPORT ALL

## Note

- WSREPORT with no arguments reports the current workspace and current area.
- WSREPORT ALL includes all open work areas in the area/index summary.
- WSREPORT USAGE prints usage and does not inspect areas.
- WSREPORT is read-only.

## Provenance

- Topic key: `DOT|WSREPORT`
- Included HELP rows: `11`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
