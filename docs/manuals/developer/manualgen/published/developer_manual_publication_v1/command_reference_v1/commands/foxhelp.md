<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# FOXHELP

- Catalog/topic: `DOT` / `FOXHELP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

List or search the static FoxPro-style command catalog.

## Status

- implemented=yes; supported=yes

## Syntax

- FOXHELP
- FOXHELP USAGE
- FOXHELP &lt;name&gt;
- FOXHELP &lt;search&gt;
- FH &lt;name&gt;
- FH &lt;search&gt;
- FOXHELP [&lt;term&gt;]

## Usage

- FOXHELP
- FOXHELP USAGE
- FOXHELP &lt;name&gt;
- FOXHELP &lt;search&gt;
- FH
- FH &lt;name&gt;
- FH &lt;search&gt;

## Note

- FOXHELP with no arguments lists the FoxPro-style command subset.
- FOXHELP &lt;name&gt; prints an exact catalog item when found.
- FOXHELP &lt;search&gt; searches the catalog and prints matching items.
- FH is a short alias for FOXHELP.
- FOXHELP is a read-only help/report command.

## Related

- HELP
- CMDHELP
- FOXSTANDARD

## Provenance

- Topic key: `DOT|FOXHELP`
- Included HELP rows: `31`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
