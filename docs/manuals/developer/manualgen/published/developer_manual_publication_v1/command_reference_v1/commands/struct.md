<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# STRUCT

- Catalog/topic: `DOT` / `STRUCT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Display table structure.

- Display the structure of the current table
- Report DBF field structure and index/container information for the current area or all open areas.
- Minimal translation unit reserved for future STRUCT helper code.

## Status

- implemented=yes; supported=yes

## Syntax

- STRUCT

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

## Provenance

- Topic key: `DOT|STRUCT`
- Included HELP rows: `26`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
