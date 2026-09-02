<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# MCC

- Catalog/topic: `DOT` / `MCC`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Load the MCC v32 demo workspace as a one-command starter demo.

## Status

- implemented=yes; supported=yes

## Syntax

- MCC
- MCC USAGE

## Usage

- MCC
- MCC USAGE

## Note

- MCC prepares and loads the MCC sample workspace for demonstration.
- MCC runs DotScript x32 to set the v32 DBF and INDEX paths.
- MCC then runs WORKSPACE LOAD mcc.dtschemas.
- Equivalent manual sequence is DOTSCRIPT x32, then WORKSPACE LOAD mcc.dtschemas.
- MCC is a convenience command and does not directly open tables or create relations itself.
- Table/session/relation restoration remains owned by WORKSPACE.
- Environment/path setup remains owned by DotScript.
- DO X32 is a command-surface shortcut for DotScript x32; MCC should be documented as using DotScript.

## Related

- DOTSCRIPT
- WORKSPACE
- REL
- USE

## Provenance

- Topic key: `DOT|MCC`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
