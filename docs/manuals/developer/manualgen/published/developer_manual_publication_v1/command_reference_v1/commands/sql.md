<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQL

- Catalog/topic: `DOT` / `SQL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Reserved verb. Reports where the scanning and statement surfaces now live.

## Status

- implemented=yes; supported=yes

## Syntax

- SQL [COUNT] [ALL|DELETED] [FOR &lt;expr&gt; | &lt;expr&gt;] [VERBOSE]

## Usage

- SQL
- SQL USAGE

## Example

- SQL
- SQL USAGE

## Note

- SQL no longer scans records and never requires an open table.
- Retired as a scanner 2026-09-04; its LIST and VERBOSE behaviour moved to
- COUNT, onto the shared selection path that honours SET FILTER and
- SET DELETED. The retired form could disagree with COUNT and did not say so.
- Family boundary, stated because the three names invite confusion:
- SQL     -- reserved (this command)
- SQLSEL  -- SQLsel, the SELECT statement surface
- SQLITE  -- the SQLite bridge, for an actual SQLite database
- Any argument is accepted and answered with the same guidance, so a script carrying an old `SQL COUNT FOR ...` line gets a correction, not silence.

## Related

- COUNT
- SQLSEL
- SQLITE

## Provenance

- Topic key: `DOT|SQL`
- Included HELP rows: `22`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
