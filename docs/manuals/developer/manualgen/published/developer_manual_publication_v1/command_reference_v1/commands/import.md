<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IMPORT

- Catalog/topic: `DOT` / `IMPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Import from CSV.

- Import records from a CSV file into the current open table by matching CSV headers to field names case-insensitively.

## Status

- implemented=yes; supported=yes

## Syntax

- IMPORT &lt;csv&gt;

## Usage

- IMPORT USAGE
- IMPORT &lt;csvfile&gt;

## Note

- IMPORT requires an open table except for IMPORT USAGE.
- IMPORT appends .csv to the file name when the extension is omitted.
- The first CSV row is interpreted as headers.
- Headers are mapped to current table fields case-insensitively.
- Each data row appends a blank record, sets mapped fields, and writes the record.
- Unmapped CSV columns are ignored.
- IMPORT mutates table data by appending records.

## Provenance

- Topic key: `DOT|IMPORT`
- Included HELP rows: `13`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
