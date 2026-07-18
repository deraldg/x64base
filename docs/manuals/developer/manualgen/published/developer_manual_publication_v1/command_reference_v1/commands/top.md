<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TOP

- Catalog/topic: `DOT` / `TOP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Move to the first record in the current table/order.

- Move the current work-area cursor to the first logical record
- Move the current work-area cursor to the first visible/logical record using the shared filter-aware navigation selector.

## Status

- implemented=yes; supported=yes

## Syntax

- TOP

## Usage

- TOP
- TOP USAGE

## Example

- TOP

## Note

- Uses the active order when an order is active
- Equivalent user intent to GO TOP / GO FIRST
- TOP with no arguments moves to the first visible record.
- TOP requires an open table except for TOP USAGE.
- TOP mutates cursor position but does not mutate table data.
- TALK ON prints the resulting record number.

## Provenance

- Topic key: `DOT|TOP`
- Included HELP rows: `14`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
