<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# AREA

- Catalog/topic: `DOT` / `AREA`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Report the current DotTalk++ work-area state.

- Report the current work-area slot and table context
- Report the current work-area slot and current area file/session state.

## Status

- implemented=yes; supported=yes

## Syntax

- AREA
- AREA USAGE

## Usage

- AREA
- AREA USAGE

## Example

- AREA

## Note

- This is a non-mutating inspection command
- Use SELECT to change the current work area
- AREA with no arguments reports the current work-area number, open file,
- record count, current record, DBF flavor, runtime kind, logical name,
- absolute path, and active order/index line.
- AREA is read-only; it reports current area state and does not mutate table data.

## Related

- DBAREA
- DBAREAS
- STATUS
- STRUCT
- WORKSPACE

## Provenance

- Topic key: `DOT|AREA`
- Included HELP rows: `20`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
