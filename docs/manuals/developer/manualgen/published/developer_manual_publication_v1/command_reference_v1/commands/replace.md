<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# REPLACE

- Catalog/topic: `DOT` / `REPLACE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Replace one field in the current record by field name or field index, preserving RHS expression evaluation, type validation, memo conversion, and table-buffer semantics.

## Status

- implemented=yes; supported=yes

## Syntax

- REPLACE USAGE
- REPLACE &lt;field_index&gt; WITH &lt;value&gt;
- REPLACE &lt;field_name&gt; WITH &lt;value&gt;
- REPLACE &lt;field&gt; WITH &lt;value&gt;

## Usage

- REPLACE USAGE
- REPLACE &lt;field_index&gt; WITH &lt;value&gt;
- REPLACE &lt;field_name&gt; WITH &lt;value&gt;

## Argument

- NOTES
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.
- NOTE

## Example

- REPLACE LNAME WITH "Smith"
- REPLACE 3 WITH TODAY
- REPLACE NOTES WITH "updated memo text"

## Note

- REPLACE requires an open table and a current record.
- REPLACE resolves fields by standard field index/name rules.
- RHS values pass through the expression/RHS evaluator and legacy string/date function handling.
- X64 memo text is converted into stored object-id text before DBF storage.
- Field values are validated and normalized before storage.
- When TABLE buffering is ON, REPLACE records a buffered field change and marks the field stale/dirty.
- When TABLE buffering is OFF, REPLACE writes immediately through DbArea storage.
- COMMIT owns durable application of buffered table changes.
- REPLACE is a table-data mutation command; do not classify it as read-only.

## Related

- REPLACE_MULTI
- TABLE
- COMMIT
- ROLLBACK
- STRUCT
- FIELDS

## Provenance

- Topic key: `DOT|REPLACE`
- Included HELP rows: `31`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
