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

- REPLACE &lt;field&gt; WITH &lt;value&gt;

## Usage

- REPLACE USAGE
- REPLACE &lt;field_index&gt; WITH &lt;value&gt;
- REPLACE &lt;field_name&gt; WITH &lt;value&gt;
- REPLACE &lt;field_index|field_name&gt; WITH NULL
- REPLACE &lt;field_index|field_name&gt; WITH .NULL.

## Argument

- NOTES
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.
- NOTE

## Example

- REPLACE LNAME WITH "Smith"
- REPLACE 3 WITH TODAY
- REPLACE NOTES WITH "updated memo text"
- REPLACE VNAME WITH NULL

## Note

- REPLACE requires an open table and a current record.
- REPLACE resolves fields by standard field index/name rules.
- RHS values pass through the expression/RHS evaluator and legacy string/date function handling.
- X64 memo text is converted into stored object-id text before DBF storage.
- Field values are validated and normalized before storage.
- WITH NULL (or .NULL.) sets the field's null bit and clears its value. It is intercepted before the value pipeline, so a null is never evaluated, normalized or width-validated into the string "NULL".
- WITH NULL is REFUSED on a field whose descriptor carries no null flag: there is no bit to record the answer in, and nothing is written.
- WITH NULL is REFUSED while TABLE buffering is ON. The buffer stores one value string per field and cannot represent NULL; buffering one would commit a blank, which reads back as not-null. COMMIT or ROLLBACK first.
- Only VFP-flavour tables carrying a `_NullFlags` column can hold a null at all;
- on every other table every field answers not-nullable and WITH NULL refuses.
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
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
