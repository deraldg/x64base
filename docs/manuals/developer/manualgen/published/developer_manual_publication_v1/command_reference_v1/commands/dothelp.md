<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DOTHELP

- Catalog/topic: `DOT` / `DOTHELP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Show project-native DotTalk++ reference entries from the DOTREF catalog.

## Status

- implemented=yes; supported=yes

## Syntax

- DOTHELP [&lt;term&gt;]

## Usage

- DOTHELP
- DOTHELP USAGE
- DOTHELP &lt;term&gt;
- HELP /DOT &lt;term&gt;

## Note

- DOTHELP with no arguments lists project-native commands and subsystems.
- DOTHELP &lt;term&gt; prints a matching dotref entry or search matches.
- DOTHELP USAGE prints usage only.
- HELP /DOT &lt;term&gt; is the related HELP-surface access path.
- DOTHELP is read-only.

## Provenance

- Topic key: `DOT|DOTHELP`
- Included HELP rows: `12`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
