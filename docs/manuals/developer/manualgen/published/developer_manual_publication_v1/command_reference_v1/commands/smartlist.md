<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SMARTLIST

- Catalog/topic: `DOT` / `SMARTLIST`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

LIST-style output with SQL-grade filtering (order-aware).<br><br>        Examples:<br>            SMARTLIST 20 FOR gpa &gt;= 3.5<br>            SMARTLIST ALL FOR lname LIKE "SMI%"<br><br>        Notes:<br>            Evaluat

- Order-aware list output with predicate support
- Filter-aware, order-aware table listing with optional projections, tuple output, debug tracing, deleted-record modes, and predicate filtering.
- LIST-style output with SQL-grade filtering (order-aware).
- Examples:
- SMARTLIST 20 FOR gpa &gt;= 3.5
- SMARTLIST ALL FOR lname LIKE "SMI%"
- Notes:
- Evaluates filters using the expression/predicate pipeline.

## Status

- implemented=yes; supported=yes

## Syntax

- SMARTLIST
- SMARTLIST &lt;n&gt;
- SMARTLIST ALL
- SMARTLIST DELETED
- SMARTLIST FOR &lt;expr&gt;
- SMARTLIST DEBUG
- SMARTLIST [ALL|DELETED|&lt;n&gt;] [DEBUG] [FOR &lt;expr&gt;]

## Usage

- SMARTLIST
- SMARTLIST USAGE
- SMARTLIST &lt;fields&gt;
- SMARTLIST ALL
- SMARTLIST &lt;limit&gt;
- SMARTLIST NEXT &lt;n&gt;
- SMARTLIST FIRST &lt;n&gt;
- SMARTLIST DELETED
- SMARTLIST DEBUG
- SMARTLIST TUPLES
- SMARTLIST FOR &lt;pred&gt;

## Example

- SMARTLIST
- SMARTLIST 20
- SMARTLIST ALL FOR GPA &gt;= 3.5
- SMARTLIST FOR LNAME LIKE "SMI%"

## Note

- Preferred listing command for user-facing ordered output
- Respects active order and active filter where available
- Uses expression/predicate services rather than ad-hoc string matching
- SMARTLIST requires an open table except for SMARTLIST USAGE.
- SMARTLIST with no arguments preserves existing behavior and prints usage before continuing with default listing.
- Field projections are comma-separated.
- ALL removes the output limit.
- NEXT and FIRST limit scan scope.
- DELETED selects deleted records.
- TUPLES emits tuple bridge output.
- DEBUG emits order/filter diagnostics.
- FOR applies predicate filtering.
- SMARTLIST restores the original cursor best-effort after listing.
- SMARTLIST is read-only for table data.

## Provenance

- Topic key: `DOT|SMARTLIST`
- Included HELP rows: `45`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
