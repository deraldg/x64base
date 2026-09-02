<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CANARY

- Catalog/topic: `DOT` / `CANARY`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Dev canary for the metadata catalog reader adapter. Reads the current already-open SYSCMD area and reports adapter row/distribution counts. Invoked as CANARY (registered in shell_commands.cpp); cmd_CATALOGCANARY is the handler, not the command name.

## Status

- implemented=yes; supported=yes

## Syntax

- CANARY
- CANARY USAGE
- CANARY [USAGE]

## Usage

- CANARY
- CANARY USAGE

## Note

- CATALOGCANARY does not open SYSCMD.dbf.
- CATALOGCANARY does not call USE or WORKSPACE OPEN.
- CATALOGCANARY expects DotTalk++ to have already prepared the area:
- DO METADATA
- WORKSPACE OPEN DBF
- SELECT SYSCMD
- It calls load_commands_from_area(current_area).
- Registration is intentionally left to the house shell command registry.

## Related

- METADATA
- WORKSPACE
- USE
- FIELDS
- LIST
- CMDHELPCHK

## Provenance

- Topic key: `DOT|CANARY`
- Included HELP rows: `23`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
