<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LMDB_UTIL

- Catalog/topic: `DOT` / `LMDB_UTIL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Deprecated disabled LMDB utility command that points users to the per-area LMDB command.

## Status

- implemented=yes; supported=yes

## Syntax

- LMDB_UTIL [USAGE|&lt;args...&gt;]

## Usage

- LMDB_UTIL
- LMDB_UTIL USAGE

## Note

- LMDB_UTIL is deprecated and disabled.
- LMDB_UTIL intentionally does not open LMDB environments or transactions.
- Use LMDB INFO, LMDB OPEN, LMDB USE, LMDB SEEK, LMDB DUMP, LMDB SCAN, and LMDB CLOSE instead.
- This avoids cross-area contamination and reader-slot conflicts.

## Related

- LMDB
- LMDBDUMP
- CDX

## Provenance

- Topic key: `DOT|LMDB_UTIL`
- Included HELP rows: `13`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
