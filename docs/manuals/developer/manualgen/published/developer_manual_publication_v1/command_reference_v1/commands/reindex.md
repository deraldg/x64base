<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# REINDEX

- Catalog/topic: `DOT` / `REINDEX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Rebuild index files for the current table (or all open tables).

- Canonical rebuild dispatcher for INX, CNX, CDX/LMDB, and student index families, choosing a default family by table flavor when no family is given.

## Status

- implemented=yes; supported=yes

## Syntax

- REINDEX [ALL]

## Usage

- REINDEX USAGE
- REINDEX
- REINDEX INX
- REINDEX INX &lt;tagfile&gt;
- REINDEX CNX
- REINDEX CNX &lt;name-or-path.cnx&gt;
- REINDEX CDX
- REINDEX CDX YES
- REINDEX CDX AUTO
- REINDEX CDX NOPROMPT
- REINDEX CDX CLEAN
- REINDEX CDX FORCE
- REINDEX CDX QUIET
- REINDEX SIX
- REINDEX SIX &lt;tagfile&gt;
- REINDEX SCX
- REINDEX SCX &lt;tagfile&gt;
- REINDEX ALL
- REINDEX CUSTOM
- REINDEX &lt;tagfile&gt;

## Note

- REINDEX with no arguments chooses the default family by open table flavor.
- v64-like tables default to CDX through BUILDLMDB.
- v32-like tables default to INX.
- With no table open, the fallback default is CDX.
- REINDEX INX rebuilds a legacy single-tag INX file.
- REINDEX CNX delegates to REBUILD.
- REINDEX CDX delegates to BUILDLMDB.
- REINDEX ALL excludes SIX and SCX by design.
- REINDEX CUSTOM runs SIX and SCX student families.
- REINDEX &lt;tagfile&gt; is treated as REINDEX INX &lt;tagfile&gt; for compatibility.
- Dirty TABLE buffers may prompt for COMMIT before supported rebuild paths.

## Provenance

- Topic key: `DOT|REINDEX`
- Included HELP rows: `35`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
