<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DELETE

- Catalog/topic: `DOT` / `DELETE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Mark the current record or selected records deleted, honoring filters and applying index delete snapshots in direct-write mode.

## Status

- implemented=yes; supported=yes

## Syntax

- DELETE USAGE
- DELETE
- DELETE ALL
- DELETE REST
- DELETE NEXT &lt;n&gt;
- DELETE FOR &lt;field&gt; &lt;op&gt; &lt;value&gt;

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

## Related

- RECALL
- PACK
- TABLE
- COMMIT
- COUNT
- SET FILTER

## Provenance

- Topic key: `DOT|DELETE`
- Included HELP rows: `29`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
