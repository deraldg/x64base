<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# NORMALIZE

- Catalog/topic: `DOT` / `NORMALIZE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Normalize/clean an input expression or text (developer utility).

- - This command does not touch the current work area.
- Mined from a command-local *_usage/*_help output block. Promote to DOTREF/FOXREF or CommandDoc when curated.

## Status

- implemented=yes; supported=yes

## Syntax

- NORMALIZE &lt;expr&gt;
- NORMALIZE USAGE
- NORMALIZE &lt;C|N|D|L&gt; &lt;len&gt; [dec_if_N] &lt;value...&gt;
- NORMALIZE C 20 "  Hello  "
- NORMALIZE N 10 0 1,234
- NORMALIZE N 10 2 1234.50
- NORMALIZE D 8 11/05/2025
- NORMALIZE L 1 yes

## Provenance

- Topic key: `DOT|NORMALIZE`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
