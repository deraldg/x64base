<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# INIT

- Catalog/topic: `DOT` / `INIT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Initialize runtime paths, cleanup stale locks, and run system/user init scripts from the executable directory.

## Status

- implemented=yes; supported=yes

## Syntax

- INIT
- INIT USAGE
- INIT [USAGE]

## Usage

- INIT
- INIT USAGE

## Note

- INIT with no arguments initializes default paths when needed and reports path slots.
- INIT cleans stale DBF locks best-effort.
- INIT runs dottalkpp.ini and init.ini from the executable directory when present.
- INIT USAGE prints usage and does not initialize paths, cleanup locks, or run scripts.
- Script commands run through the shell command executor and may have their own side effects.

## Related

- SHUTDOWN
- SETPATH
- DOTSCRIPT

## Provenance

- Topic key: `DOT|INIT`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
