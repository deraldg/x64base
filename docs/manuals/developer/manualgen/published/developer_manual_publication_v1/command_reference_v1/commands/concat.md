<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CONCAT

- Catalog/topic: `DOT` / `CONCAT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Concatenate string arguments. (Available as CALC function; also usable as a command where wired.)

- Concatenate one or more expressions into a single printed string
- Concatenate one or more expressions into a single string and print the result.

## Status

- implemented=yes; supported=yes

## Syntax

- CONCAT &lt;expr1&gt;[, &lt;expr2&gt; ...]
- STRCAT &lt;expr1&gt;[, &lt;expr2&gt; ...]
- CONCAT(&lt;expr1&gt;, &lt;expr2&gt;, ...)
- CONCAT(&lt;c1&gt;[, &lt;c2&gt; ...]) | CONCAT &lt;args...&gt;

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

## Alias

- STRCAT

## Provenance

- Topic key: `DOT|CONCAT`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
