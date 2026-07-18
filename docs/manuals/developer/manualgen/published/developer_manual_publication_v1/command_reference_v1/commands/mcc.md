<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# MCC

- Catalog/topic: `DOT` / `MCC`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Load the MCC v32 demo workspace by running DotScript x32 and WORKSPACE LOAD mcc.dtschemas.

- Load the MCC v32 demo workspace as a one-command starter demo.

## Status

- implemented=yes; supported=yes

## Syntax

- MCC

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

## Provenance

- Topic key: `DOT|MCC`
- Included HELP rows: `14`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
