<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DRAWIO

- Catalog/topic: `DOT` / `DRAWIO`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Generate or manage Draw.io-oriented diagram artifacts for documentation and teaching workflows.

- Launch diagrams.net, or list/open draw.io files from configured diagram paths.

## Status

- implemented=yes; supported=yes

## Syntax

- DRAWIO [USAGE|&lt;args...&gt;]

## Usage

- DRAWIO USAGE
- DRAWIO
- DRAWIO PATHS
- DRAWIO LIST
- DRAWIO LIST SYSTEM
- DRAWIO LIST USER
- DRAWIO LIST ALL
- DRAWIO OPEN
- DRAWIO OPEN &lt;url-or-path&gt;
- DRAWIO OPEN SYSTEM &lt;n|filename&gt;
- DRAWIO OPEN USER &lt;n|filename&gt;
- DRAWIO OPEN ALL &lt;n|filename&gt;

## Note

- DRAWIO with no arguments launches the default diagrams.net URL.
- DRAWIO OPEN with no target also launches the default diagrams.net URL.
- DRAWIO LIST defaults to SYSTEM.
- SYSTEM diagrams come from SETPATH SYSTEM_DIAGRAMS / DIAGRAMS.
- USER diagrams come from SETPATH USER_DIAGRAMS.
- DRAWIO does not mutate table data or workspace state.

## Provenance

- Topic key: `DOT|DRAWIO`
- Included HELP rows: `22`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
