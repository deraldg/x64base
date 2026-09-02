<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLERASE

- Catalog/topic: `DOT` / `SQLERASE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Mark records deleted using SQL-like ERASE FROM &lt;table&gt; WHERE &lt;expr&gt; syntax.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLERASE USAGE
- SQLERASE FROM &lt;table&gt; WHERE &lt;expr&gt;
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

## Related

- ERASE
- RECALL
- ZAP

## Provenance

- Topic key: `DOT|SQLERASE`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
