<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# INDEX

- Catalog/topic: `DOT` / `INDEX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Build an INX index file from the current table using a field key, tag/file name, optional direction, and optional INX format.

## Status

- implemented=yes; supported=yes

## Syntax

- INDEX USAGE
- INDEX ON &lt;field&gt; TAG &lt;name&gt;
- INDEX ON &lt;field&gt; TAG &lt;name&gt; ASC
- INDEX ON &lt;field&gt; TAG &lt;name&gt; DESC
- INDEX ON &lt;field&gt; TAG &lt;name&gt; 1INX
- INDEX ON &lt;field&gt; TAG &lt;name&gt; 2INX
- INDEX ON &lt;field&gt; TAG &lt;name&gt; ASC 1INX
- INDEX ON &lt;field&gt; TAG &lt;name&gt; DESC 2INX
- INDEX [ON &lt;field&gt; TAG &lt;name&gt; | STATUS | LIST]

## Usage

- INDEX USAGE
- INDEX ON &lt;field&gt; TAG &lt;name&gt;
- INDEX ON &lt;field&gt; TAG &lt;name&gt; ASC
- INDEX ON &lt;field&gt; TAG &lt;name&gt; DESC
- INDEX ON &lt;field&gt; TAG &lt;name&gt; 1INX
- INDEX ON &lt;field&gt; TAG &lt;name&gt; 2INX
- INDEX ON &lt;field&gt; TAG &lt;name&gt; ASC 1INX
- INDEX ON &lt;field&gt; TAG &lt;name&gt; DESC 2INX

## Example

- INDEX ON LNAME TAG students
- INDEX ON LNAME TAG students DESC
- INDEX ON LNAME TAG students ASC 1INX
- INDEX ON LNAME TAG students DESC 2INX

## Note

- INDEX requires an open table except for INDEX USAGE, INDEX HELP, and INDEX question-mark.
- Deleted records are excluded.
- Default direction is ASC.
- Default output format is 2INX, matching REINDEX.
- Optional direction and format tokens may appear in either order.
- Field-number tokens are also accepted by the parser, but omitted from mineable usage rows because hash syntax is a source-comment marker.
- 2INX uses fixed-length keys, uppercases character fields, and writes a pos-by-recno table.
- TAG must name an INX file target; non-.inx extensions are refused.
- INDEX writes an index file through the INDEXES path resolver and does not mutate table records.

## Related

- REINDEX
- SET INDEX
- SET ORDER
- CDX
- CNX

## Provenance

- Topic key: `DOT|INDEX`
- Included HELP rows: `38`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
