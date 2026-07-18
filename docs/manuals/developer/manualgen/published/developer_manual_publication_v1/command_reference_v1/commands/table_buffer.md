<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TABLE_BUFFER

- Catalog/topic: `DOT` / `TABLE_BUFFER`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Developer/diagnostic helper surface for inspecting or testing TABLE buffering and stale-field behavior.

- Inspect or change per-area table-buffer state.

## Status

- implemented=yes; supported=yes

## Syntax

- TABLE_BUFFER [USAGE|&lt;args...&gt;]

## Usage

- TABLE_BUFFER
- TABLE_BUFFER USAGE
- TABLE_BUFFER STATUS [ALL]
- TABLE_BUFFER BUFFER ON|OFF|DIRTY|CLEAN|STALE|FRESH|STATUS|DUMP|TESTADD|RESET

## Note

- No arguments reports current buffer state. State-changing subcommands mutate session buffer metadata.

## Provenance

- Topic key: `DOT|TABLE_BUFFER`
- Included HELP rows: `9`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
