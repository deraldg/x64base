<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TURBOPACK

- Catalog/topic: `DOT` / `TURBOPACK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Fast byte-oriented compaction for plain non-memo, non-x64 DBF tables.

## Status

- implemented=yes; supported=yes

## Syntax

- TURBOPACK USAGE
- TURBOPACK

## Usage

- TURBOPACK USAGE
- TURBOPACK

## Example

- TURBOPACK

## Note

- TURBOPACK USAGE prints usage before open-table checks.
- TURBOPACK is a fast path for plain DBF tables only.
- Memo tables and x64 tables are refused; use PACK instead.
- TURBOPACK closes the table on success.
- Index containers must be rebuilt/rebound after TURBOPACK.

## Related

- PACK
- ZAP
- RECALL

## Provenance

- Topic key: `DOT|TURBOPACK`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
