<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LOCK

- Catalog/topic: `DOT` / `LOCK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Lock the current record (or table) for editing.

- Acquire record or table locks for the current table and inspect lock status or lock ownership.

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

## Provenance

- Topic key: `DOT|LOCK`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
