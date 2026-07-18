<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLERASE

- Catalog/topic: `DOT` / `SQLERASE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

SQL helper surface for erase/drop/delete-style SQL maintenance workflows where enabled.

- Mark records deleted using SQL-like ERASE FROM &lt;table&gt; WHERE &lt;expr&gt; syntax.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLERASE [USAGE|&lt;args...&gt;]

## Usage

- SQLERASE USAGE
- SQLERASE FROM &lt;table&gt; WHERE &lt;expr&gt;

## Example

- SQLERASE FROM STUDENTS WHERE SID = 1001
- SQLERASE FROM STUDENTS WHERE GPA &lt; 1.0

## Note

- SQLERASE USAGE prints usage before open-table checks.
- WHERE is required to reduce accidental destructive operations.
- SQLERASE mutates table data by marking matching records deleted.

## Provenance

- Topic key: `DOT|SQLERASE`
- Included HELP rows: `11`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
