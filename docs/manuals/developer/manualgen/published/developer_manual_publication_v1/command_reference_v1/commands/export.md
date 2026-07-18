<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# EXPORT

- Catalog/topic: `DOT` / `EXPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Export to CSV.

- Export the current DBF rowset, or an already-open named work area, to a delimited file.

## Status

- implemented=yes; supported=yes

## Syntax

- EXPORT &lt;csv&gt;

## Usage

- EXPORT USAGE
- EXPORT [TO] &lt;file&gt; [CSV|PIPE]
- EXPORT &lt;open-area-token&gt; TO &lt;file&gt; [CSV|PIPE]

## Note

- EXPORT [TO] &lt;file&gt; writes the current table to the named file.
- EXPORT &lt;open-area-token&gt; TO &lt;file&gt; writes an already-open work area without changing
- the user's selected area intentionally.
- Named tokens may be an area number, #area, alias/name, logical name, DBF basename/stem,
- filename, or full path, if those values resolve uniquely to an open area.
- Named EXPORT does not auto-open tables from disk.
- CSV is the default format; PIPE uses a pipe delimiter.
- A missing extension is added automatically (.csv for CSV, .txt for PIPE).
- EXPORT writes a header row.
- EXPORT honors the active SET FILTER for the exported area.
- EXPORT reads records in physical table order.
- EXPORT may report file/write errors and still emit a summary when appropriate.

## Provenance

- Topic key: `DOT|EXPORT`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
