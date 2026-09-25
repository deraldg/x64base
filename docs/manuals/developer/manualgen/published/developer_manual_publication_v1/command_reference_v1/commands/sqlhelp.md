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
- SQLHELP SQLSEL
- SQLHELP LIST-CATEGORIES
- SQLHELP &lt;category&gt;
- SQLHELP &lt;term&gt;

## Example

- SQLHELP
- SQLHELP SQLSEL
- SQLHELP INDEXING
- SQLHELP CREATE-INDEX
- SQLHELP LIST-CATEGORIES

## Note

- SQLHELP with no arguments displays the grouped SQL reference.
- SQLHELP USAGE prints command usage without searching the catalog.
- SQLHELP is read-only and does not execute SQL.
- THE CATALOG IS A PORTABLE SQLite/MSSQL REFERENCE AND RUNS NOTHING HERE.
- This engine's own SELECT is SQLSEL. SQLHELP SQLSEL DELEGATES to sqlsel::print_statement_usage() -- the ONE runtime description of the statement grammar -- rather than keeping a second copy. Three authorities for one command's help is how the text drifts from the code, which AIF-074 caught twice in one day.

## Related

- SQL
- SQLSEL
- SQLITE
- SHOW
- PSHELL

## Provenance

- Topic key: `DOT|SQLHELP`
- Included HELP rows: `29`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
