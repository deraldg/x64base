<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# VALIDATE

- Catalog/topic: `DOT` / `VALIDATE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Route validation subcommands such as VALIDATE UNIQUE to their handlers.

## Status

- implemented=yes; supported=yes

## Syntax

- VALIDATE USAGE
- VALIDATE UNIQUE USAGE
- VALIDATE UNIQUE FIELD &lt;name&gt; [IGNORE DELETED] [REPAIR] [REPORT TO &lt;path&gt;]
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

## Related

- RULE
- WHERE

## Provenance

- Topic key: `DOT|VALIDATE`
- Included HELP rows: `20`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
