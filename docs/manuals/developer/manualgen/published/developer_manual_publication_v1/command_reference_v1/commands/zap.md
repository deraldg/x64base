<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ZAP

- Catalog/topic: `DOT` / `ZAP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Remove all records from the current non-memo DBF while preserving structure.

## Status

- implemented=yes; supported=yes

## Syntax

- ZAP USAGE
- ZAP

## Usage

- ZAP USAGE
- ZAP

## Argument

- NONE
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Example

- ZAP

## Note

- ZAP USAGE prints usage before open-table checks.
- ZAP rewrites the current DBF with zero records and closes the table on success.
- ZAP currently refuses memo tables.
- Index containers must be rebuilt/rebound afterward.

## Related

- ERASE
- PACK
- RECALL

## Provenance

- Topic key: `DOT|ZAP`
- Included HELP rows: `17`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
