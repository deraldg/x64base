<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CONCAT

- Catalog/topic: `DOT` / `CONCAT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Concatenate one or more expressions into a single string and print the result.

## Status

- implemented=yes; supported=yes

## Syntax

- CONCAT &lt;expr1&gt;[, &lt;expr2&gt; ...]
- STRCAT &lt;expr1&gt;[, &lt;expr2&gt; ...]
- CONCAT(&lt;expr1&gt;, &lt;expr2&gt;, ...)
- CONCAT USAGE
- CONCAT(&lt;c1&gt;[, &lt;c2&gt; ...]) | CONCAT &lt;args...&gt;
- CONCAT "hello", " ", "world"
- CONCAT FNAME, " ", LNAME
- STRCAT("A", "B", "C")

## Usage

- CONCAT USAGE
- CONCAT &lt;expr1&gt;[, &lt;expr2&gt; ...]
- STRCAT &lt;expr1&gt;[, &lt;expr2&gt; ...]

## Example

- CONCAT "hello", " ", "world"
- CONCAT FNAME, " ", LNAME
- STRCAT("A", "B", "C")

## Note

- CONCAT is the shell command surface over the same string-function family used by CALC
- When a table is open, bare identifiers can resolve as fields; otherwise they remain literal text
- STRCAT is an alias of CONCAT
- CONCAT accepts between 1 and 32 arguments.
- Bare identifiers resolve through the expression engine:
- fields read from the current table when open; otherwise they remain plain text.
- Parenthesized call form is also accepted for command-line convenience.

## Alias

- STRCAT

## Related

- CALC
- REPLACE
- MULTIREP

## Provenance

- Topic key: `DOT|CONCAT`
- Included HELP rows: `29`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
