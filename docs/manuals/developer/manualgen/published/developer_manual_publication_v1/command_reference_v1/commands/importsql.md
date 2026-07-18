<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IMPORTSQL

- Catalog/topic: `DOT` / `IMPORTSQL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Import or bridge SQL data into DotTalk++ through the SQL import helper surface.

- Preview, validate, infer schema, create/import table data from delimited files.

## Status

- implemented=yes; supported=yes

## Syntax

- IMPORTSQL [USAGE|&lt;args...&gt;]

## Usage

- IMPORTSQL USAGE
- IMPORTSQL PREVIEW &lt;file&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL VALIDATE &lt;file&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL SCHEMA &lt;file&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL CREATE &lt;file&gt; TO &lt;table&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL FILE &lt;file&gt; TO &lt;table&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL MAP &lt;subcommand&gt; &lt;mapfile&gt;

## Example

- IMPORTSQL PREVIEW data\students.psv
- IMPORTSQL VALIDATE data\students.csv DELIM COMMA
- IMPORTSQL CREATE data\students.psv TO students
- IMPORTSQL FILE data\students.psv TO students

## Note

- IMPORTSQL USAGE returns before file/table work.
- IMPORTSQL PREVIEW/VALIDATE/SCHEMA read input files.
- IMPORTSQL CREATE/FILE may create tables and import records.

## Provenance

- Topic key: `DOT|IMPORTSQL`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
