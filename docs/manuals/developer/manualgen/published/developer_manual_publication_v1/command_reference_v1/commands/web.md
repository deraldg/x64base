<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# WEB

- Catalog/topic: `DOT` / `WEB`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Open, fetch, or inspect web URLs using the default handler or WinHTTP.

## Status

- implemented=yes; supported=yes

## Syntax

- WEB USAGE
- WEB DEFAULT
- WEB RETRO
- WEB OPEN &lt;url|DEFAULT|RETRO&gt;
- WEB LAUNCH &lt;url|DEFAULT|RETRO&gt;
- WEB GET &lt;url|DEFAULT|RETRO&gt;
- WEB HEAD &lt;url|DEFAULT|RETRO&gt;
- WEB FETCH &lt;url|DEFAULT|RETRO&gt; TO &lt;file&gt;
- WEB [USAGE|&lt;args...&gt;]
- WEB OPEN https://example.com
- WEB OPEN DEFAULT
- WEB HEAD https://example.com
- WEB GET https://example.com
- WEB FETCH https://example.com/data.csv TO tmp\data.csv

## Usage

- WEB USAGE
- WEB DEFAULT
- WEB RETRO
- WEB OPEN &lt;url|DEFAULT|RETRO&gt;
- WEB LAUNCH &lt;url|DEFAULT|RETRO&gt;
- WEB GET &lt;url|DEFAULT|RETRO&gt;
- WEB HEAD &lt;url|DEFAULT|RETRO&gt;
- WEB FETCH &lt;url|DEFAULT|RETRO&gt; TO &lt;file&gt;

## Example

- WEB DEFAULT
- WEB RETRO
- WEB OPEN https://example.com
- WEB OPEN DEFAULT
- WEB HEAD https://example.com
- WEB GET https://example.com
- WEB FETCH https://example.com/data.csv TO tmp\data.csv

## Note

- WEB USAGE prints usage and does not launch a browser, make a network request, or write files.
- WEB DEFAULT opens x64base.com.
- WEB RETRO opens the Flying Toasters page.
- DEFAULT and RETRO are accepted anywhere a URL operand is accepted.
- WEB OPEN/LAUNCH use the OS default URL handler.
- WEB GET/HEAD use HTTP request support where implemented.
- WEB FETCH writes the response body to the requested file.

## Related

- SFTP
- PSHELL

## Provenance

- Topic key: `DOT|WEB`
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
