<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ASCEND

- Catalog/topic: `DOT` / `ASCEND`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Set ascending sort direction for the active order/tag.

- Set the active order/tag direction to ascending for the current work area.

## Status

- implemented=yes; supported=yes

## Syntax

- ASCEND
- ASCEND USAGE

## Usage

- ASCEND
- ASCEND USAGE

## Note

- ASCEND requires an active order except for ASCEND USAGE.
- ASCEND with no arguments mutates order direction to ascending.
- ASCEND does not mutate table records or rebuild indexes.
- risk:
- mutates_order_state: yes
- mutates_table_data: no
- requires_active_order: yes except usage

## Related

- DESCEND
- SET ORDER
- ORDER
- include "xbase.hpp"

## Provenance

- Topic key: `DOT|ASCEND`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
