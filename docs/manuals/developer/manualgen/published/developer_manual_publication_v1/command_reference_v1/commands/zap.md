<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ZAP

- Catalog/topic: `DOT` / `ZAP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Delete all records from the current table.

- Remove all records from the current non-memo DBF while preserving structure.

## Status

- implemented=yes; supported=yes

## Syntax

- ZAP

## Usage

- ZAP USAGE
- ZAP

## Example

- ZAP

## Note

- ZAP USAGE prints usage before open-table checks.
- ZAP rewrites the current DBF with zero records and closes the table on success.
- ZAP currently refuses memo tables.
- Index containers must be rebuilt/rebound afterward.

## Provenance

- Topic key: `DOT|ZAP`
- Included HELP rows: `11`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
