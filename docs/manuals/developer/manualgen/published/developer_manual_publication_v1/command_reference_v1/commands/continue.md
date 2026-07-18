<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CONTINUE

- Catalog/topic: `DOT` / `CONTINUE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Continue a running loop/scan block (scripting control flow).

- Continue a previous LOCATE search, or continue with an explicit FOR predicate, following active order when present.

## Status

- implemented=yes; supported=yes

## Syntax

- CONTINUE

## Usage

- CONTINUE
- CONTINUE USAGE
- CONTINUE FOR &lt;expr&gt;

## Note

- CONTINUE with no arguments reuses the active LOCATE/CONTINUE predicate.
- CONTINUE FOR &lt;expr&gt; searches forward from the current record using the supplied predicate.
- CONTINUE follows active order when one is present; otherwise it scans physical order.
- CONTINUE requires an open table except for CONTINUE USAGE.
- CONTINUE mutates cursor/search state but does not mutate table data.

## Provenance

- Topic key: `DOT|CONTINUE`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
