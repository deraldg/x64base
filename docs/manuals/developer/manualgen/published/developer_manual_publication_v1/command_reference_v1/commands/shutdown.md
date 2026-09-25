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
- Included HELP rows: `14`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
