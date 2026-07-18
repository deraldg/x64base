<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# BOTTOM

- Catalog/topic: `DOT` / `BOTTOM`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Move to the last record in the current table/order.

- Move the current work-area cursor to the last logical record
- Move the current work-area cursor to the last visible/logical record.

## Status

- implemented=yes; supported=yes

## Syntax

- BOTTOM
- BOTTOM USAGE

## Usage

- BOTTOM
- BOTTOM USAGE

## Example

- BOTTOM

## Note

- Uses the active order when an order is active
- Equivalent user intent to GO BOTTOM / GO LAST
- BOTTOM with no arguments moves to the last visible/logical record.
- BOTTOM requires an open table except for BOTTOM USAGE.
- BOTTOM uses the AutoByFilter last-record navigation selector.
- BOTTOM mutates cursor position but does not mutate table data.
- TALK ON prints the resulting record number when movement succeeds.
- risk:
- mutates_cursor: yes
- mutates_table_data: no
- requires_open_table: yes except usage

## Related

- TOP
- BOTTOM
- FIRST
- LAST
- NEXT
- PRIOR
- SKIP
- GOTO
- GPS

## Provenance

- Topic key: `DOT|BOTTOM`
- Included HELP rows: `29`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
