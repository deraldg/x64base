<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# STRUCT

- Catalog/topic: `DOT` / `STRUCT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Report DBF field structure and index/container information for the current area or all open areas.

- Minimal translation unit reserved for future STRUCT helper code.

## Status

- implemented=yes; supported=yes

## Syntax

- STRUCT
- STRUCT USAGE
- STRUCT INDEX
- STRUCT FIELDS
- STRUCT ALL
- STRUCT ALL INDEX
- STRUCT ALL VERBOSE
- STRUCT command behavior and usage are owned by the actual STRUCT command implementation.

## Usage

- STRUCT
- STRUCT USAGE
- STRUCT INDEX
- STRUCT FIELDS
- STRUCT ALL
- STRUCT ALL INDEX
- STRUCT ALL VERBOSE
- This file intentionally does not export cmd_STRUCT().
- STRUCT command behavior and usage are owned by the actual STRUCT command implementation.

## Argument

- NOTE
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Example

- STRUCT

## Note

- Shows field-level structure for the current area
- Non-mutating inspection command
- STRUCT with no arguments reports field and index information for the current area.
- STRUCT INDEX is explicit index-info mode; index info is included by default.
- STRUCT FIELDS suppresses index info and reports fields only.
- STRUCT ALL reports all open areas.
- STRUCT ALL VERBOSE includes verbose CNX tag information where available.
- STRUCT is read-only; it reports structure/index metadata and does not mutate table data.
- Keeping this file minimal avoids duplicate cmd_STRUCT definitions.
- Future shared STRUCT helpers may live here without adding command dispatch.

## Related

- AREA
- DBAREA
- FIELDS
- STATUS
- WORKSPACE

## Provenance

- Topic key: `DOT|STRUCT`
- Included HELP rows: `40`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
