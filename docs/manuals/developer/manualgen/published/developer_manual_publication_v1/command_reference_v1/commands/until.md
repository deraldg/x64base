<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# UNTIL

- Catalog/topic: `DOT` / `UNTIL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Begin an UNTIL block (scripting).

- Buffer and execute an UNTIL...ENDUNTIL loop from the current record until a boolean expression becomes true.

## Status

- implemented=yes; supported=yes

## Syntax

- UNTIL &lt;expr&gt;

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

## Provenance

- Topic key: `DOT|UNTIL`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
