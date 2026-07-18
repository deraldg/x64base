<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# UPDATE

- Catalog/topic: `DOT` / `UPDATE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Update data rows (scripting/SQL helper; see command usage).

- Update records in the current DBF work area using SQL-like SET/WHERE syntax.

## Status

- implemented=yes; supported=yes

## Syntax

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

## Provenance

- Topic key: `DOT|UPDATE`
- Included HELP rows: `11`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
