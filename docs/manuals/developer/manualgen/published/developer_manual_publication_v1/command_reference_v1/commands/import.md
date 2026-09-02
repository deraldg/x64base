<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IMPORT

- Catalog/topic: `DOT` / `IMPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Import records from a CSV file into the current open table by matching CSV headers to field names case-insensitively.

## Status

- implemented=yes; supported=yes

## Syntax

- IMPORT USAGE
- IMPORT &lt;csvfile&gt;
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

## Related

- EXPORT
- APPEND
- APPEND_BLANK
- DDL

## Provenance

- Topic key: `DOT|IMPORT`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
