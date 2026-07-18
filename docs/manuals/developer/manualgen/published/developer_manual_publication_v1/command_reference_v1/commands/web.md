<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# WEB

- Catalog/topic: `DOT` / `WEB`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Web-oriented helper command surface for local documentation, preview, or integration workflows where enabled.

- Open, fetch, or inspect web URLs using the default handler or WinHTTP.

## Status

- implemented=yes; supported=yes

## Syntax

- WEB [USAGE|&lt;args...&gt;]

## Usage

- WEB USAGE
- WEB OPEN &lt;url&gt;
- WEB LAUNCH &lt;url&gt;
- WEB GET &lt;url&gt;
- WEB HEAD &lt;url&gt;
- WEB FETCH &lt;url&gt; TO &lt;file&gt;

## Note

- WEB USAGE prints usage and does not launch a browser, make a network request, or write files.
- WEB OPEN/LAUNCH use the OS default URL handler.
- WEB GET/HEAD use HTTP request support where implemented.
- WEB FETCH writes the response body to the requested file.

## Provenance

- Topic key: `DOT|WEB`
- Included HELP rows: `14`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
