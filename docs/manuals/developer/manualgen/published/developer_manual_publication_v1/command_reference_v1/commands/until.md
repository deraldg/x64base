<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# UNTIL

- Catalog/topic: `DOT` / `UNTIL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Buffer and execute an UNTIL...ENDUNTIL loop from the current record until a boolean expression becomes true.

## Status

- implemented=yes; supported=yes

## Syntax

- UNTIL USAGE
- UNTIL &lt;bool-expr&gt; [QUIET]
- ENDUNTIL
- ENDUNTIL USAGE
- UNTIL &lt;expr&gt;
- UNTIL EOF()
- TUPLE LNAME,FNAME,GPA

## Usage

- UNTIL USAGE
- UNTIL &lt;bool-expr&gt; [QUIET]
- ENDUNTIL
- ENDUNTIL USAGE

## Example

- UNTIL EOF()
- TUPLE LNAME,FNAME,GPA
- ENDUNTIL

## Note

- UNTIL USAGE and ENDUNTIL USAGE do not start or execute a loop.
- UNTIL starts buffering; the shell must route body lines to UNTIL_BUFFER.
- ENDUNTIL executes buffered body lines through the canonical loop executor.
- Execution starts at the current record and advances one record per iteration.
- Buffered body command effects are owned by those commands.

## Related

- IF
- WHILE
- SCAN

## Provenance

- Topic key: `DOT|UNTIL`
- Included HELP rows: `25`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
