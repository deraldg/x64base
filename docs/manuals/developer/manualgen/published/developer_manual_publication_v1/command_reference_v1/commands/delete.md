<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DELETE

- Catalog/topic: `DOT` / `DELETE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Mark the current record deleted using current table semantics.

- Mark the current record or selected records deleted, honoring filters and applying index delete snapshots in direct-write mode.

## Status

- implemented=yes; supported=yes

## Syntax

- DELETE

## Usage

- DELETE USAGE
- DELETE
- DELETE ALL
- DELETE REST
- DELETE NEXT &lt;n&gt;
- DELETE FOR &lt;field&gt; &lt;op&gt; &lt;value&gt;

## Note

- DELETE with no arguments deletes the current record.
- DELETE requires an open table except for DELETE USAGE.
- DELETE honors active SET FILTER in ALL, REST, NEXT, and FOR scans.
- DELETE snapshots target recnos before mutating to avoid active-index traversal mutation.
- Direct-write mode captures index keys before delete and applies index delete snapshots after delete.
- Buffered table mode leaves rebuild or final application to COMMIT.
- DELETE marks fields stale best-effort and refreshes current navigation best-effort.
- If index snapshot or apply fails, data delete may still succeed and a rebuild warning is emitted.

## Provenance

- Topic key: `DOT|DELETE`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
