<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# FOXHELP

- Catalog/topic: `DOT` / `FOXHELP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

List or search command help topics.<br><br>        Examples:<br>            FOXHELP<br>            FOXHELP WORKSPACE<br>            FOXHELP REL<br><br>        Notes:<br>            Uses the help catalogs and any HELP DBFs.

- List or search the static FoxPro-style command catalog.
- List or search command help topics.
- Examples:
- FOXHELP
- FOXHELP WORKSPACE
- FOXHELP REL
- Notes:
- Uses the help catalogs and any HELP DBFs.

## Status

- implemented=yes; supported=yes

## Syntax

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

## Provenance

- Topic key: `DOT|FOXHELP`
- Included HELP rows: `22`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
