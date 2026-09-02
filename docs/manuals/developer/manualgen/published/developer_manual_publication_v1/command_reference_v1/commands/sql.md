<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQL

- Catalog/topic: `DOT` / `SQL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Evaluate SQL-like COUNT/FOR predicates over the current DBF work area.

## Status

- implemented=yes; supported=yes

## Syntax

- SQL USAGE
- SQL [COUNT] [ALL|DELETED] [FOR &lt;expr&gt; | &lt;expr&gt;] [VERBOSE]
- SQL COUNT
- SQL COUNT ALL
- SQL COUNT DELETED
- SQL COUNT FOR GPA &gt;= 3.0
- SQL LNAME = "SMITH"
- SQL VERBOSE COUNT FOR GPA &gt;= 3.0
- SQLSEL  -- SELECT statements: SQLSEL SELECT &lt;cols&gt; FROM &lt;table&gt; ...
- SQLITE  -- the SQLite bridge, for an actual SQLite database

## Usage

- SQL USAGE
- SQL [COUNT] [ALL|DELETED] [FOR &lt;expr&gt; | &lt;expr&gt;] [VERBOSE]

## Example

- SQL COUNT
- SQL COUNT ALL
- SQL COUNT DELETED
- SQL COUNT FOR GPA &gt;= 3.0
- SQL LNAME = "SMITH"
- SQL VERBOSE COUNT FOR GPA &gt;= 3.0

## Note

- SQL USAGE prints usage before open-table checks.
- SQL reads records and may temporarily move the cursor.
- SQL does not mutate table data.
- COUNT reports the number only. A bare predicate scan lists its matches.
- VERBOSE prints every record with its true/false verdict, plus scan diagnostics.
- SQL DOES NOT EXECUTE SQL STATEMENTS. The name is historical: this command scans the CURRENT area with a predicate and reports matches or a count.
- Family boundary, stated here because the three names invite confusion:
- SQL     -- predicate scan/count over the current area (this command)
- SQLSEL  -- SQLsel, the SELECT statement surface over a named open table
- SQLITE  -- the SQLite bridge, for talking to an actual SQLite database
- SQLSEL also accepts this same predicate-scan form for compatibility, so
- `SQL COUNT FOR &lt;expr&gt;` and `SQLSEL COUNT FOR &lt;expr&gt;` are equivalent.

## Related

- SQLSEL
- WHERE
- WHERECACHE

## Provenance

- Topic key: `DOT|SQL`
- Included HELP rows: `38`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
