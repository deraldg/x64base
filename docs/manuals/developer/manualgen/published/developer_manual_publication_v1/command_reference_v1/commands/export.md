<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# EXPORT

- Catalog/topic: `DOT` / `EXPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Export the current DBF rowset, or an already-open named work area, to a delimited file.

## Status

- implemented=yes; supported=yes

## Syntax

- EXPORT USAGE
- EXPORT [TO] &lt;file&gt; [CSV|PIPE|SDF]
- EXPORT &lt;open-area-token&gt; TO &lt;file&gt; [CSV|PIPE|SDF]

## Usage

- EXPORT USAGE
- EXPORT [TO] &lt;file&gt; [CSV|PIPE|SDF]
- EXPORT &lt;open-area-token&gt; TO &lt;file&gt; [CSV|PIPE|SDF]

## Note

- EXPORT [TO] &lt;file&gt; writes the current table to the named file.
- EXPORT &lt;open-area-token&gt; TO &lt;file&gt; writes an already-open work area without changing the user's selected area intentionally.
- Named tokens may be an area number, #area, alias/name, logical name, DBF basename/stem, filename, or full path, if those values resolve uniquely to an open area.
- Named EXPORT does not auto-open tables from disk.
- CSV is the default format; PIPE uses a pipe delimiter; SDF writes fixed-width rows.
- A missing extension is added automatically (.csv for CSV, .txt for PIPE, .sdf for SDF).
- EXPORT writes a header row for CSV and PIPE; SDF writes data records only.
- EXPORT honors the active SET FILTER for the exported area.
- EXPORT reads records in physical table order.
- EXPORT may report file/write errors and still emit a summary when appropriate.
- Named tokens may be an area number,
- area, alias/name, logical name, DBF basename/stem,

## Related

- DUMP
- LIST
- COPY TO
- DDL
- WORKSPACE
- WSREPORT

## Provenance

- Topic key: `DOT|EXPORT`
- Included HELP rows: `29`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
