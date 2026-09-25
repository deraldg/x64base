<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IMPORTSQL

- Catalog/topic: `DOT` / `IMPORTSQL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Preview, validate, infer schema, create/import table data from delimited files.

## Status

- implemented=yes; supported=yes

## Syntax

- IMPORTSQL [USAGE|&lt;args...&gt;]
- IMPORTSQL USAGE
- IMPORTSQL PREVIEW &lt;file&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL VALIDATE &lt;file&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL SCHEMA &lt;file&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL CREATE &lt;file&gt; TO &lt;table&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL FILE &lt;file&gt; TO &lt;table&gt; [DELIM PIPE|TAB|COMMA]
- IMPORTSQL MAP &lt;subcommand&gt; &lt;mapfile&gt;
- IMPORTSQL PREVIEW data\students.psv
- IMPORTSQL VALIDATE data\students.csv DELIM COMMA
- IMPORTSQL CREATE data\students.psv TO students
- IMPORTSQL FILE data\students.psv TO students
- EXPORTSQL USAGE
- EXPORTSQL PREVIEW &lt;table&gt;
- EXPORTSQL FILE &lt;table&gt; TO &lt;file&gt;
- EXPORTSQL PREVIEW students
- EXPORTSQL FILE students TO tmp\students.sql

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

- IMPORTSQL FILE TAKES THE TABLE FENCE ONCE, BEFORE THE FIRST ROW (OI-043, 2026-09-19), and refuses with "IMPORTSQL: table locked (&lt;reason&gt;)" when another process holds the target. It did not until that date: measured against a planted foreign lock it reported "IMPORT: OK / Rows imported: 1" while APPEND BLANK, SQLSEL INSERT and REPLACE were all refused by name.
- The target may be the table this session already has open -- current_area_matches_target() exists for exactly that -- so the table it grows can be the one another engine is holding.
- IMPORTSQL FILE ENFORCES PRIMARY-KEY POLICY (AIF-156, 2026-09-23, owner ruling: identity is house-owned, meaning is data). On a table whose key is declared PRIMARY: an import whose positional columns would land on the key column is REFUSED BEFORE THE FIRST ROW ("IMPORT: REFUSED", naming the key and instructing demotion to a data column); every row's columns are asked of xbase::cli::gateFieldWrites() BEFORE the append;
- and rows imported past the key come out MINTED by the same generator
- APPEND uses, never blank. A source key with embedded meaning (a VIN) is imported as an ordinary data column, never as the house key.
- PKPOLICY arms PKP_G8/G9/T9/T10 are the runtime proof.
- IMPORTSQL USAGE returns before file/table work.
- IMPORTSQL PREVIEW/VALIDATE/SCHEMA read input files.
- IMPORTSQL CREATE/FILE may create tables and import records.
- IMPORTSQL FILE refuses to feed a declared PRIMARY key and mints it instead (2026-09-23; see the enforcement note above).

## Related

- USE
- COPY
- SQL

## Provenance

- Topic key: `DOT|IMPORTSQL`
- Included HELP rows: `57`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
