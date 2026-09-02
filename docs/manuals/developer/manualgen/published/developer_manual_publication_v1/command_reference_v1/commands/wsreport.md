<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# WSREPORT

- Catalog/topic: `DOT` / `WSREPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Print a workspace/status report covering open areas, LMDB/order summary, and table-buffer state.

## Status

- implemented=yes; supported=yes

## Syntax

- WSREPORT
- WSREPORT USAGE
- WSREPORT ALL

## Usage

- WSREPORT
- WSREPORT USAGE
- WSREPORT ALL

## Note

- WSREPORT with no arguments reports the current workspace and current area.
- WSREPORT ALL includes all open work areas in the area/index summary.
- WSREPORT USAGE prints usage and does not inspect areas.
- WSREPORT is read-only.

## Related

- AREA
- STATUS
- WORKSPACE

## Provenance

- Topic key: `DOT|WSREPORT`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
