<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ELSE

- Catalog/topic: `DOT` / `ELSE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Begin the alternate branch of an IF block when the IF condition is false.

- Empty translation-unit shim for ELSE command ownership.

## Status

- implemented=yes; supported=yes

## Syntax

- ELSE

## Usage

- ELSE usage is owned by the IF/ELSE/ENDIF command implementation.
- This file intentionally exports no command handler.

## Note

- This file exists only because ELSE has a cmd_*.cpp translation unit in the
- build tree. Do not add a second ELSE implementation here.

## Provenance

- Topic key: `DOT|ELSE`
- Included HELP rows: `8`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
