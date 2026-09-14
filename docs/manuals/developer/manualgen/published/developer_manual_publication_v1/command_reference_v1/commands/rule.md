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

- RULE [USAGE|&lt;args...&gt;]
- RULE
- RULE USAGE
- RULE STATUS
- RULE SHOW &lt;field|ALL&gt;
- RULE LIST
- RULE PATHS
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
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
