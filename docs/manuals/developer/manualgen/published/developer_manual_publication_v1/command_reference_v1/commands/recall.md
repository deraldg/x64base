<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# RECALL

- Catalog/topic: `DOT` / `RECALL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Clear deleted flags on the current record or selected deleted records.

## Status

- implemented=yes; supported=yes

## Syntax

- RECALL USAGE
- RECALL
- RECALL ALL
- RECALL REST
- RECALL NEXT &lt;n&gt;
- RECALL FOR &lt;expr&gt;
- UNDELETE

## Usage

- RECALL USAGE
- RECALL
- RECALL ALL
- RECALL REST
- RECALL NEXT &lt;n&gt;
- RECALL FOR &lt;expr&gt;
- UNDELETE

## Argument

- NOT_DELETED
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

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

## Related

- ERASE
- PACK
- ZAP

## Provenance

- Topic key: `DOT|RECALL`
- Included HELP rows: `33`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
