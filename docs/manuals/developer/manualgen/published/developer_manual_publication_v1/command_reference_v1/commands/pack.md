<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# PACK

- Catalog/topic: `DOT` / `PACK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Permanently remove deleted records from the current table.

- Physically remove deleted records by rewriting the current DBF; x64 memo tables rebuild both DBF and DTX sidecar with remapped memo ids.

## Status

- implemented=yes; supported=yes

## Syntax

- PACK

## Usage

- PACK USAGE
- PACK

## Example

- PACK

## Note

- PACK USAGE prints usage before open-table checks.
- PACK rewrites the current DBF with only non-deleted records and closes the table on success.
- PACK supports x64 M(8) memo tables by rebuilding DBF and DTX together.
- Legacy memo tables are refused.
- Index containers must be rebuilt/rebound after PACK.

## Provenance

- Topic key: `DOT|PACK`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
