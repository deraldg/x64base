<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LMDB_UTIL

- Catalog/topic: `DOT` / `LMDB_UTIL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Developer/diagnostic LMDB utility surface for low-level backend inspection and maintenance workflows.

- Deprecated disabled LMDB utility command that points users to the per-area LMDB command.

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

## Provenance

- Topic key: `DOT|LMDB_UTIL`
- Included HELP rows: `10`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
