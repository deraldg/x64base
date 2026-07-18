<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TUPLE

- Catalog/topic: `DOT` / `TUPLE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Build one tuple row from fields across work areas.<br><br>        Examples:<br>            TUPLE *                    (all fields from current area)<br>            TUPLE LNAME,FNAME          (selected fields from

- Build and print a tuple row from the canonical tuple builder using a tuple field specification and optional output flags.
- Build one tuple row from fields across work areas.
- Examples:
- TUPLE *                    (all fields from current area)
- TUPLE LNAME,FNAME          (selected fields from current area)
- TUPLE #11.*                (all fields from area 11)
- TUPLE #9.*,#11.LNAME       (mix of areas)
- Notes:
- #n prefixes a work area slot; "*" means all fields for that area.
- Output fields are separated by ASCII Unit Separator (0x1F).

## Status

- implemented=yes; supported=yes

## Syntax

- TUPLE &lt;spec&gt;

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

## Provenance

- Topic key: `DOT|TUPLE`
- Included HELP rows: `39`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
