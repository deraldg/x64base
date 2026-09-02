<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SHOWINI

- Catalog/topic: `DOT` / `SHOWINI`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Display a table-specific .ini file, either derived from the current table or from an explicit file/path.

## Status

- implemented=yes; supported=yes

## Syntax

- SHOWINI
- SHOWINI USAGE
- SHOWINI &lt;table-or-ini&gt;
- SHOWINI PATH &lt;ini-file&gt;
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

## Related

- SHOWINI
- SETPATH
- STATUS

## Provenance

- Topic key: `DOT|SHOWINI`
- Included HELP rows: `21`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
