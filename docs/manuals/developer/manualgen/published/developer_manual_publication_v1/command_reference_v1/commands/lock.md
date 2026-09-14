<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LOCK

- Catalog/topic: `DOT` / `LOCK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Acquire record or table locks for the current table and inspect lock status or lock ownership.

## Status

- implemented=yes; supported=yes

## Syntax

- LOCK [RECORD|TABLE|&lt;recno&gt;...]

## Usage

- LOCK USAGE
- LOCK
- LOCK &lt;n&gt;
- LOCK ALL
- LOCK TABLE
- LOCK STATUS
- LOCK WHO &lt;n&gt;

## Note

- LOCK requires an open table except for LOCK USAGE.
- LOCK with no arguments locks the current record.
- LOCK &lt;n&gt; locks record n.
- LOCK ALL and LOCK TABLE lock the entire table.
- LOCK STATUS reports table and current-record lock state.
- LOCK WHO &lt;n&gt; reports the owner of record n when a lock is recorded.
- LOCK mutates lock state but does not mutate table data.

## Related

- UNLOCK
- DELETE
- COMMIT

## Provenance

- Topic key: `DOT|LOCK`
- Included HELP rows: `21`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
