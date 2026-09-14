<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# APPEND

- Catalog/topic: `DOT` / `APPEND`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Append one or more blank records to the current table, using smart append paths that maintain keys and active indexes, or raw append paths when requested.

## Status

- implemented=yes; supported=yes

## Syntax

- APPEND

## Usage

- APPEND USAGE
- APPEND
- APPEND &lt;count&gt;
- APPEND MANY &lt;count&gt;
- APPEND RAW
- APPEND RAW MANY &lt;count&gt;

## Note

- APPEND with no arguments appends one blank record through the shared smart append path.
- APPEND &lt;count&gt; is shorthand for APPEND MANY &lt;count&gt;.
- APPEND MANY &lt;count&gt; performs smart batch append under one lock.
- APPEND RAW appends one record without inline index update.
- APPEND RAW MANY &lt;count&gt; performs raw batch append under one lock.
- Count values must be positive integers.
- APPEND is a table-data mutation command; do not classify it as read-only.

## Related

- APPEND_BLANK
- REPLACE
- MULTIREP
- TABLE
- COMMIT

## Provenance

- Topic key: `DOT|APPEND`
- Included HELP rows: `22`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
