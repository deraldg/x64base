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

- IMPORT &lt;csv&gt;

## Usage

- IMPORT USAGE
- IMPORT &lt;csvfile&gt;

## Note

- IMPORT requires an open table except for IMPORT USAGE.
- IMPORT appends .csv to the file name when the extension is omitted.
- IMPORT TAKES THE TABLE FENCE ONCE, BEFORE THE FIRST ROW (OI-043, 2026-09-19), and refuses with "IMPORT: table locked (&lt;reason&gt;)" when another process holds the table. One fence for the whole file, so a refusal costs nothing rather than leaving a partial import. It did not take one until that date: measured against a planted foreign lock, it appended to the fenced table and reported success.
- The FIRST csv record is read as HEADERS and mapped to fields by name; a column that matches no field is skipped, so a feed with no header line appends rows and writes nothing.
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
- Included HELP rows: `26`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
