<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LOCATE

- Catalog/topic: `DOT` / `LOCATE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Position on the first record matching a predicate or simple field comparison.

- Locate the first record matching a predicate, using simple CDX fast-path when possible and selector-backed scanning otherwise.

## Status

- implemented=yes; supported=yes

## Syntax

- LOCATE FOR &lt;expr&gt; | LOCATE &lt;field&gt; &lt;op&gt; &lt;value&gt;

## Usage

- LOCATE USAGE
- LOCATE FOR &lt;expr&gt;
- LOCATE &lt;field&gt; &lt;op&gt; &lt;value&gt;

## Example

- LOCATE FOR LNAME = Smith
- LOCATE LNAME = Smith
- LOCATE FOR BALANCE &gt; 100

## Note

- LOCATE requires an open table except for LOCATE USAGE.
- LOCATE with no predicate shows usage.
- LOCATE clears previous LOCATE and CONTINUE bridge state before searching.
- Simple predicates on the active CDX tag may use the CDX fast path.
- Complex predicates are evaluated through the selector and expression path.
- LOCATE positions on the first matching record.
- LOCATE updates locate state and CONTINUE bridge state after a match.
- LOCATE is read-only for table data but mutates cursor/search state.

## Provenance

- Topic key: `DOT|LOCATE`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
