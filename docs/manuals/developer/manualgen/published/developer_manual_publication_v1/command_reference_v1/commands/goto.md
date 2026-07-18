<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# GOTO

- Catalog/topic: `DOT` / `GOTO`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Move the current work area to a specific record or boundary position.

- Move to a record or navigation endpoint
- Move the current work-area cursor to an absolute record number, first record, or last record through the shared navigation layer.

## Status

- implemented=yes; supported=yes

## Syntax

- GO
- GO TOP
- GO BOTTOM
- GO FIRST
- GO LAST
- GO [TO] &lt;recno&gt;
- GO RECORD &lt;recno&gt;
- GO +&lt;n&gt;
- GO -&lt;n&gt;
- GOTO &lt;recno&gt;|TOP|BOTTOM

## Usage

- GOTO USAGE
- GOTO &lt;recno&gt;
- GOTO FIRST
- GOTO LAST

## Example

- GO
- GO TOP
- GO TO 10
- GO RECORD 25
- GO +5
- GO -1

## Note

- GO with no arguments refreshes or reports the current record context
- TOP and FIRST are synonyms
- BOTTOM and LAST are synonyms
- Relative movement uses the current work-area cursor
- GOTO requires a target argument except for GOTO USAGE.
- GOTO FIRST and GOTO LAST use endpoint navigation.
- GOTO &lt;recno&gt; uses absolute record navigation.
- GOTO mutates cursor position but does not mutate table data.

## Warning

- IN &lt;alias&gt; is not supported yet

## Provenance

- Topic key: `DOT|GOTO`
- Included HELP rows: `33`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
