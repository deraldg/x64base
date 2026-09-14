<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLHELP

- Catalog/topic: `DOT` / `SQLHELP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Display or search the SQL helper/reference catalog.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLHELP [USAGE|&lt;topic&gt;]

## Usage

- SQLHELP
- SQLHELP USAGE
- SQLHELP LIST-CATEGORIES
- SQLHELP &lt;category&gt;
- SQLHELP &lt;term&gt;

## Example

- SQLHELP
- SQLHELP INDEXING
- SQLHELP CREATE-INDEX
- SQLHELP LIST-CATEGORIES

## Note

- SQLHELP with no arguments displays the grouped SQL reference.
- SQLHELP USAGE prints command usage without searching the catalog.
- SQLHELP is read-only and does not execute SQL.

## Related

- SQL
- SHOW
- PSHELL

## Provenance

- Topic key: `DOT|SQLHELP`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
