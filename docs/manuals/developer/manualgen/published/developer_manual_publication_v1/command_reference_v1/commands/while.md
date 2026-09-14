<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# WHILE

- Catalog/topic: `DOT` / `WHILE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Buffer and execute a WHILE...ENDWHILE loop from the current record while a boolean expression remains true.

## Status

- implemented=yes; supported=yes

## Syntax

- WHILE &lt;expr&gt;
- WHILE USAGE
- WHILE &lt;bool-expr&gt; [QUIET]
- ENDWHILE
- ENDWHILE USAGE
- WHILE GPA &gt;= 3.0
- TUPLE LNAME,FNAME,GPA

## Usage

- WHILE USAGE
- WHILE &lt;bool-expr&gt; [QUIET]
- ENDWHILE
- ENDWHILE USAGE

## Example

- WHILE GPA &gt;= 3.0
- TUPLE LNAME,FNAME,GPA
- ENDWHILE

## Note

- WHILE USAGE and ENDWHILE USAGE do not start or execute a loop.
- WHILE starts buffering; the shell must route body lines to WHILE_BUFFER.
- ENDWHILE executes buffered body lines through the canonical loop executor.
- Execution starts at the current record and advances one record per iteration.
- Buffered body command effects are owned by those commands.

## Related

- IF
- UNTIL
- SCAN

## Provenance

- Topic key: `DOT|WHILE`
- Included HELP rows: `25`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
