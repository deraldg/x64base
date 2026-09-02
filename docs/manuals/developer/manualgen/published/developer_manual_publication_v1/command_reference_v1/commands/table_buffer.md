<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TABLE_BUFFER

- Catalog/topic: `DOT` / `TABLE_BUFFER`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect or change per-area table-buffer state.

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

## Related

- COMMIT, ROLLBACK, TABLE

## Provenance

- Topic key: `DOT|TABLE_BUFFER`
- Included HELP rows: `10`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
