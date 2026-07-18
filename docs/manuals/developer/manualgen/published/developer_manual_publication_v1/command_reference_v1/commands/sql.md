<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQL

- Catalog/topic: `DOT` / `SQL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Execute an SQL statement using the configured SQL engine.

- Evaluate SQL-like COUNT/FOR predicates over the current DBF work area.

## Status

- implemented=yes; supported=yes

## Syntax

- SQL &lt;statement&gt;

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

## Provenance

- Topic key: `DOT|SQL`
- Included HELP rows: `15`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
