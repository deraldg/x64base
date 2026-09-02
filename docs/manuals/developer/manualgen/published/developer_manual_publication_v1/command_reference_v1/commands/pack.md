<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# PACK

- Catalog/topic: `DOT` / `PACK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Physically remove deleted records by rewriting the current DBF; x64 memo tables rebuild both DBF and DTX sidecar with remapped memo ids.

## Status

- implemented=yes; supported=yes

## Syntax

- PACK USAGE
- PACK

## Usage

- PACK USAGE
- PACK

## Argument

- NONE
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Example

- PACK

## Note

- PACK USAGE prints usage before open-table checks.
- PACK rewrites the current DBF with only non-deleted records and closes the table on success.
- PACK supports x64 M(8) memo tables by rebuilding DBF and DTX together.
- Legacy memo tables are refused.
- Index containers must be rebuilt/rebound after PACK.

## Related

- TURBOPACK
- ZAP
- RECALL

## Provenance

- Topic key: `DOT|PACK`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
