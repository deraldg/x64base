<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# GO

- Catalog/topic: `DOT` / `GO`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Execute a DotTalk++ command line (dispatch to command handlers).

- Move to a record or navigation endpoint
- Refresh the current record, move to table/order endpoints, move to an absolute record number, or skip relative to the current record.

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
- GO &lt;commandLine&gt;

## Usage

- GO
- GO USAGE
- GO TOP
- GO BOTTOM
- GO FIRST
- GO LAST
- GO TO &lt;recno&gt;
- GO RECORD &lt;recno&gt;
- GO &lt;recno&gt;
- GO +&lt;n&gt;
- GO -&lt;n&gt;

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
- GO with no arguments refreshes/re-reads the current record through the navigation layer.
- GO TOP/BOTTOM/FIRST/LAST move to logical endpoints.
- GO &lt;recno&gt;, GO TO &lt;recno&gt;, and GO RECORD &lt;recno&gt; navigate absolutely.
- GO +/-&lt;n&gt; delegates to relative skip.
- GO USAGE prints usage before navigation.

## Warning

- IN &lt;alias&gt; is not supported yet

## Provenance

- Topic key: `DOT|GO`
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
