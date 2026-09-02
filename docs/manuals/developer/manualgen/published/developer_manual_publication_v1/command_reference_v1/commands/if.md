<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IF

- Catalog/topic: `DOT` / `IF`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Start an IF/ELSE/ENDIF conditional block using the shell's shared boolean expression evaluator and control-flow stack.

## Status

- implemented=yes; supported=yes

## Syntax

- IF USAGE
- IF &lt;bool-expr&gt;
- ELSE
- ELSE USAGE
- ENDIF
- ENDIF USAGE
- IF &lt;logical_expr&gt;
- IF GPA &gt;= 3.0
- ECHO HONORS
- ECHO REGULAR

## Usage

- IF USAGE
- IF &lt;bool-expr&gt;
- ELSE
- ELSE USAGE
- ENDIF
- ENDIF USAGE

## Example

- IF GPA &gt;= 3.0
- ECHO HONORS
- ELSE
- ECHO REGULAR
- ENDIF

## Note

- IF USAGE prints usage and does not modify the IF stack.
- IF evaluates only when the outer IF stack allows execution.
- ELSE flips the active branch for the current IF frame.
- ENDIF exits the current IF frame.
- Effects of commands inside the active branch are owned by those commands.

## Related

- WHILE
- UNTIL
- SCAN

## Provenance

- Topic key: `DOT|IF`
- Included HELP rows: `32`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
