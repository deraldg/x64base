<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DRAWIO

- Catalog/topic: `DOT` / `DRAWIO`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Launch diagrams.net, or list/open draw.io files from configured diagram paths.

## Status

- implemented=yes; supported=yes

## Syntax

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
- DRAWIO [USAGE|&lt;args...&gt;]
- DRAWIO LIST [SYSTEM|USER|ALL]
- SYSTEM = SETPATH SYSTEM_DIAGRAMS / DIAGRAMS
- USER   = SETPATH USER_DIAGRAMS

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
- External viewers are launched without blocking the DotTalk++ command loop.

## Related

- HELP
- EXPORT
- SETPATH

## Provenance

- Topic key: `DOT|DRAWIO`
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
