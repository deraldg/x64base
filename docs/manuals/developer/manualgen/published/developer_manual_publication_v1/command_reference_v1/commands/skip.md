<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SKIP

- Catalog/topic: `DOT` / `SKIP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Move relative to the current record in the active work area.

- Move the current work-area cursor forward or backward
- Move the current work-area cursor forward or backward using filter-aware navigation selection.

## Status

- implemented=yes; supported=yes

## Syntax

- SKIP
- SKIP &lt;n&gt;
- SKIP +&lt;n&gt;
- SKIP -&lt;n&gt;
- SKIP [&lt;n&gt;]

## Usage

- SKIP
- SKIP USAGE
- SKIP &lt;n&gt;

## Example

- SKIP
- SKIP 5
- SKIP -1

## Note

- Default movement is one record forward
- Uses active logical order when one is active
- SKIP with no arguments moves forward one logical record.
- SKIP &lt;n&gt; moves forward when n is positive and backward when n is negative.
- SKIP 0 rereads the current record.
- SKIP requires an open table except for SKIP USAGE.
- Navigation uses the shared filter-aware selector.
- SKIP mutates cursor position but does not mutate table data.

## Provenance

- Topic key: `DOT|SKIP`
- Included HELP rows: `23`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
