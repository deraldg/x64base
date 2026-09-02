<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ELSE

- Catalog/topic: `DOT` / `ELSE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Empty translation-unit shim for ELSE command ownership.

## Status

- implemented=yes; supported=yes

## Syntax

- ELSE usage is owned by the IF/ELSE/ENDIF command implementation.
- ELSE

## Usage

- ELSE usage is owned by the IF/ELSE/ENDIF command implementation.
- This file intentionally exports no command handler.

## Note

- This file exists only because ELSE has a cmd_*.cpp translation unit in the build tree. Do not add a second ELSE implementation here.

## Provenance

- Topic key: `DOT|ELSE`
- Included HELP rows: `9`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
