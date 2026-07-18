<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# EXPORTSQL

- Catalog/topic: `DOT` / `EXPORTSQL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Export DotTalk++ table or workspace data through the SQL export helper surface.

- Preview SQL export output and expose the file-export command surface.

## Status

- implemented=yes; supported=yes

## Syntax

- EXPORTSQL [USAGE|&lt;args...&gt;]

## Usage

- EXPORTSQL USAGE
- EXPORTSQL PREVIEW &lt;table&gt;
- EXPORTSQL FILE &lt;table&gt; TO &lt;file&gt;

## Example

- EXPORTSQL PREVIEW students
- EXPORTSQL FILE students TO tmp\students.sql

## Note

- EXPORTSQL USAGE returns before file or table work.
- EXPORTSQL hooks are currently preview/file command surfaces.

## Provenance

- Topic key: `DOT|EXPORTSQL`
- Included HELP rows: `11`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
