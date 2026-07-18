<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SHOWINI

- Catalog/topic: `DOT` / `SHOWINI`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Display DotTalk++ initialization/configuration files and resolved startup settings.

- Display a table-specific .ini file, either derived from the current table or from an explicit file/path.

## Status

- implemented=yes; supported=yes

## Syntax

- SHOWINI [USAGE|SYSTEM|USER|ALL]

## Usage

- SHOWINI
- SHOWINI USAGE
- SHOWINI &lt;table-or-ini&gt;
- SHOWINI PATH &lt;ini-file&gt;

## Example

- SHOWINI
- SHOWINI students
- SHOWINI students.ini

## Note

- SHOWINI with no arguments derives the .ini path from the current table.
- SHOWINI USAGE prints usage before open-table checks or file reads.
- SHOWINI reads .ini files and prints parsed sections/keys; it does not write files.

## Provenance

- Topic key: `DOT|SHOWINI`
- Included HELP rows: `14`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
