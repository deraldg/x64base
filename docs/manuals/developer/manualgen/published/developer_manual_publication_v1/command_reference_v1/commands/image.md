<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IMAGE

- Catalog/topic: `DOT` / `IMAGE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect image file metadata or open a supported image file in the operating system viewer.

## Status

- implemented=yes; supported=yes

## Syntax

- IMAGE USAGE
- IMAGE DEFAULT
- IMAGE &lt;file&gt;
- IMAGE INFO DEFAULT
- IMAGE INFO &lt;file&gt;
- IMAGE [USAGE|INFO &lt;file&gt;|&lt;file&gt;]

## Usage

- IMAGE USAGE
- IMAGE DEFAULT
- IMAGE &lt;file&gt;
- IMAGE INFO DEFAULT
- IMAGE INFO &lt;file&gt;

## Note

- IMAGE with no arguments prints usage.
- IMAGE USAGE prints usage and does not open a viewer.
- IMAGE DEFAULT opens "arctic fox.png" beside the running executable.
- IMAGE INFO DEFAULT reports metadata for the default image.
- IMAGE INFO &lt;file&gt; prints file extension, size, and recognized-image status.
- IMAGE &lt;file&gt; opens the OS viewer on Windows.
- Non-Windows viewer launch is currently not implemented.
- IMAGE does not mutate table data.

## Related

- WEB
- BANG

## Provenance

- Topic key: `DOT|IMAGE`
- Included HELP rows: `24`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
