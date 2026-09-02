<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# RULE

- Catalog/topic: `DOT` / `RULE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect rule catalog paths, bindings, and field constraints for the current work area.

## Status

- implemented=yes; supported=yes

## Syntax

- RULE
- RULE USAGE
- RULE STATUS
- RULE SHOW &lt;field|ALL&gt;
- RULE LIST
- RULE PATHS
- RULE [USAGE|&lt;args...&gt;]
- RULE SHOW GPA
- RULE SHOW ALL

## Usage

- RULE
- RULE USAGE
- RULE STATUS
- RULE SHOW &lt;field|ALL&gt;
- RULE LIST
- RULE PATHS

## Example

- RULE
- RULE STATUS
- RULE SHOW GPA
- RULE SHOW ALL
- RULE LIST
- RULE PATHS

## Note

- RULE with no arguments reports rule status.
- RULE USAGE prints usage and does not require an open table.
- RULE is diagnostic/read-only; it does not create, edit, or bind rules.

## Related

- VALIDATE
- WHERE

## Provenance

- Topic key: `DOT|RULE`
- Included HELP rows: `29`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
