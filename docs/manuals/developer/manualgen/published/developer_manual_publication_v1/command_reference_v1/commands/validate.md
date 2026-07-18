<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# VALIDATE

- Catalog/topic: `DOT` / `VALIDATE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Schema/sidecar validation command.

- Route validation subcommands such as VALIDATE UNIQUE to their handlers.

## Status

- implemented=yes; supported=yes

## Syntax

- VALIDATE &lt;path&gt;

## Usage

- VALIDATE USAGE
- VALIDATE UNIQUE USAGE
- VALIDATE UNIQUE FIELD &lt;name&gt; [IGNORE DELETED] [REPAIR] [REPORT TO &lt;path&gt;]

## Example

- VALIDATE UNIQUE FIELD SID
- VALIDATE UNIQUE FIELD EMAIL IGNORE DELETED
- VALIDATE UNIQUE FIELD SID REPAIR
- VALIDATE UNIQUE FIELD SID REPORT TO tmp\sid_dupes.txt

## Note

- VALIDATE with no arguments prints usage.
- VALIDATE USAGE prints usage and does not scan or repair records.
- VALIDATE UNIQUE is delegated to the UNIQUE validator.
- REPAIR may mutate field values; use it intentionally.

## Provenance

- Topic key: `DOT|VALIDATE`
- Included HELP rows: `15`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
