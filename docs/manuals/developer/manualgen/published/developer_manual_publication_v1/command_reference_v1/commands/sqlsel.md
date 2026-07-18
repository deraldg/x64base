<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLSEL

- Catalog/topic: `DOT` / `SQLSEL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Execute an SQL SELECT and display results.

- Evaluate SQL-like selection predicates over the current DBF work area.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLSEL &lt;expr&gt;

## Usage

- SQLSEL USAGE
- SQLSEL [COUNT] [ALL|DELETED] [FOR &lt;expr&gt; | &lt;expr&gt;]

## Example

- SQLSEL COUNT
- SQLSEL COUNT ALL
- SQLSEL COUNT FOR GPA &gt;= 3.0
- SQLSEL LNAME = "SMITH"

## Note

- SQLSEL USAGE prints usage before open-table checks.
- SQLSEL reads records and may temporarily move the cursor.
- SQLSEL does not mutate table data.

## Provenance

- Topic key: `DOT|SQLSEL`
- Included HELP rows: `13`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
