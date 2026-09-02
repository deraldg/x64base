<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# UPDATE

- Catalog/topic: `DOT` / `UPDATE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Update records in the current DBF work area using SQL-like SET/WHERE syntax.

## Status

- implemented=yes; supported=yes

## Syntax

- UPDATE USAGE
- UPDATE SET &lt;field&gt;=&lt;value&gt;[, ...] [WHERE &lt;expr&gt;]
- UPDATE &lt;statement&gt;

## Usage

- UPDATE USAGE
- UPDATE SET &lt;field&gt;=&lt;value&gt;[, ...] [WHERE &lt;expr&gt;]

## Example

- UPDATE SET GPA=3.5 WHERE SID = 1001
- UPDATE SET MAJOR="CSCI" WHERE MAJOR = "CS"

## Note

- UPDATE USAGE prints usage before open-table checks.
- UPDATE without WHERE may update all visible records depending on implementation.
- Use WHERE intentionally.

## Related

- SQL
- INSERT
- SQLERASE

## Provenance

- Topic key: `DOT|UPDATE`
- Included HELP rows: `16`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
