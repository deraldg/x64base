<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# RECALL

- Catalog/topic: `DOT` / `RECALL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Unmark the current deleted record when supported by the current table state.

- Clear deleted flags on the current record or selected deleted records.

## Status

- implemented=yes; supported=yes

## Syntax

- RECALL

## Usage

- RECALL USAGE
- RECALL
- RECALL ALL
- RECALL REST
- RECALL NEXT &lt;n&gt;
- RECALL FOR &lt;expr&gt;
- UNDELETE

## Example

- RECALL
- RECALL ALL
- RECALL REST
- RECALL NEXT 10
- RECALL FOR LNAME = "SMITH"

## Note

- RECALL USAGE prints usage before open-table checks.
- RECALL with no arguments recalls the current record.
- RECALL target selection is deleted-only.
- RECALL rebuilds index entries for recalled records best-effort.
- UNDELETE is the registered compatibility alias of RECALL.

## Alias

- UNDELETE

## Provenance

- Topic key: `DOT|RECALL`
- Included HELP rows: `22`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
