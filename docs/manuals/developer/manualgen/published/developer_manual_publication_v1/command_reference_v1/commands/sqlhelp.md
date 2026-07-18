<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLHELP

- Catalog/topic: `DOT` / `SQLHELP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Show SQL-oriented help and guidance for DotTalk++ SQL bridge workflows.

- Display or search the SQL helper/reference catalog.

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

## Provenance

- Topic key: `DOT|SQLHELP`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
