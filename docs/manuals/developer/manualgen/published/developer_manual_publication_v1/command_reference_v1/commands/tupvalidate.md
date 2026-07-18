<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TUPVALIDATE

- Catalog/topic: `DOT` / `TUPVALIDATE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Tuple validation helper surface for checking tuple projection, relation-walk, or logical-row consistency.

- Validate tuple graph rows for the current table using the tuple graph cursor and relation-aware tuple validation layer.

## Status

- implemented=yes; supported=yes

## Syntax

- TUPVALIDATE [USAGE|&lt;args...&gt;]

## Usage

- TUPVALIDATE
- TUPVALIDATE USAGE
- TUPVALIDATE *
- TUPVALIDATE &lt;tuple-spec&gt;
- TUPVALIDATE * FOR &lt;expr&gt;
- TUPVALIDATE * FOR &lt;expr&gt; MAX &lt;n&gt;
- TUPVALIDATE * FOR &lt;expr&gt; TRACE

## Example

- TUPVALIDATE LNAME,FNAME
- TUPVALIDATE STUDENTS.*,MAJORS.* FOR MAJORS.NAME = CS

## Note

- TUPVALIDATE with no arguments validates the default star tuple spec.
- TUPVALIDATE USAGE prints usage and does not require an open table.
- The tuple graph cursor uses active ordering and relation context.
- Validation checks tuple cells against their source work areas when available.
- Cursor restoration is reported after validation.
- TUPVALIDATE is read-only for table data but moves cursors during validation.

## Provenance

- Topic key: `DOT|TUPVALIDATE`
- Included HELP rows: `19`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
