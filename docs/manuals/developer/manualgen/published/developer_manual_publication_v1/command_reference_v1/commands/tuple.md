<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TUPLE

- Catalog/topic: `DOT` / `TUPLE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Build and print a tuple row from the canonical tuple builder using a tuple field specification and optional output flags.

## Status

- implemented=yes; supported=yes

## Syntax

- TUPLE
- TUPLE USAGE
- TUPLE &lt;spec&gt;
- TUPLE &lt;spec&gt; --HEADER
- TUPLE &lt;spec&gt; --AREA-PREFIX
- TUPLE &lt;spec&gt; --NO-ECHO
- TUPLE &lt;spec&gt; --STRICT
- TUPLE &lt;spec&gt; --HEADER-ONLY
- TUPLE &lt;spec&gt; --VALUES-ONLY
- TUPLE &lt;spec&gt; DEBUG
- TUPLE &lt;spec&gt; --DEBUG
- TUPLE &lt;spec&gt; --NULL &lt;token&gt;
- TUPLE LNAME,FNAME
- TUPLE * --HEADER
- TUPLE * --VALUES-ONLY

## Usage

- TUPLE
- TUPLE USAGE
- TUPLE &lt;spec&gt;
- TUPLE &lt;spec&gt; --HEADER
- TUPLE &lt;spec&gt; --AREA-PREFIX
- TUPLE &lt;spec&gt; --NO-ECHO
- TUPLE &lt;spec&gt; --STRICT
- TUPLE &lt;spec&gt; --HEADER-ONLY
- TUPLE &lt;spec&gt; --VALUES-ONLY
- TUPLE &lt;spec&gt; DEBUG
- TUPLE &lt;spec&gt; --DEBUG
- TUPLE &lt;spec&gt; --NULL &lt;token&gt;

## Example

- TUPLE
- TUPLE LNAME,FNAME
- TUPLE STUDENTS.LNAME,STUDENTS.FNAME
- TUPLE * --HEADER
- TUPLE * --VALUES-ONLY

## Note

- TUPLE with no arguments uses the default star spec.
- TUPLE delegates tuple truth to tuple_builder.
- TUPLE can print formatted output, raw unit-separated values, or both.
- --HEADER prints a header row before values.
- --AREA-PREFIX prefixes header columns with area context.
- --NO-ECHO preserves legacy raw-only scripting behavior.
- --VALUES-ONLY prints raw unit-separated values only.
- DEBUG and --DEBUG print the raw unit-separated row before formatted output.
- --STRICT asks the tuple builder to reject loose field matches.
- TUPLE is read-only for table data.

## Related

- SMARTLIST
- TUPVALIDATE
- TUPTALK
- ERSATZ

## Provenance

- Topic key: `DOT|TUPLE`
- Included HELP rows: `57`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
