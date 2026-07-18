<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IMAGE

- Catalog/topic: `DOT` / `IMAGE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect image file metadata or open a supported image file in the operating-system viewer.

- Inspect image file metadata or open a supported image file in the operating system viewer.

## Status

- implemented=yes; supported=yes

## Syntax

- IMAGE [USAGE|INFO &lt;file&gt;|&lt;file&gt;]

## Usage

- IMAGE USAGE
- IMAGE &lt;file&gt;
- IMAGE INFO &lt;file&gt;

## Note

- IMAGE with no arguments prints usage.
- IMAGE USAGE prints usage and does not open a viewer.
- IMAGE INFO &lt;file&gt; prints file extension, size, and recognized-image status.
- IMAGE &lt;file&gt; opens the OS viewer on Windows.
- Non-Windows viewer launch is currently not implemented.
- IMAGE does not mutate table data.

## Provenance

- Topic key: `DOT|IMAGE`
- Included HELP rows: `13`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
