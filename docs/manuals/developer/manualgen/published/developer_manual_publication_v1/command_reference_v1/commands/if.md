<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# IF

- Catalog/topic: `DOT` / `IF`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Begin a conditional DotScript block; execute the following block when the logical expression is true.

- Start an IF/ELSE/ENDIF conditional block using the shell's shared boolean expression evaluator and control-flow stack.

## Status

- implemented=yes; supported=yes

## Syntax

- IF &lt;logical_expr&gt;

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

## Provenance

- Topic key: `DOT|IF`
- Included HELP rows: `20`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
