<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# FOXSTANDARD

- Catalog/topic: `DOT` / `FOXSTANDARD`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Render static historical FoxPro-standard reference topics.

## Status

- implemented=yes; supported=yes

## Syntax

- FOXSTANDARD [USAGE|HELP|&lt;topic&gt;]

## Usage

- FOXSTANDARD USAGE
- FOXSTANDARD &lt;command&gt;
- FOXSTANDARD ALL
- FOXSTANDARD TOPICS
- FOXSTANDARD LIST

## Note

- FOXSTANDARD with no arguments shows usage.
- FOXSTANDARD ALL, TOPICS, and LIST render the available topic list.
- FOXSTANDARD &lt;command&gt; renders the static reference for that command.
- FOXSTANDARD is separate from the live HELP and command catalogs.

## Related

- FOXHELP
- HELP
- CMDHELP

## Provenance

- Topic key: `DOT|FOXSTANDARD`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
