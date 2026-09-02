<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SHUTDOWN

- Catalog/topic: `DOT` / `SHUTDOWN`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Run the optional shutdown.ini script from the executable directory.

## Status

- implemented=yes; supported=yes

## Syntax

- SHUTDOWN
- SHUTDOWN USAGE

## Usage

- SHUTDOWN
- SHUTDOWN USAGE

## Note

- SHUTDOWN with no arguments looks for shutdown.ini beside the executable and executes it when present.
- SHUTDOWN USAGE prints usage and does not execute shutdown.ini.
- Each non-empty shutdown.ini line is executed through the shell command executor.
- UTF-8 BOM and trailing carriage returns are handled.
- SHUTDOWN may indirectly mutate data, session state, or files depending on script contents.

## Related

- INIT
- TEST
- DOTSCRIPT

## Provenance

- Topic key: `DOT|SHUTDOWN`
- Included HELP rows: `15`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
