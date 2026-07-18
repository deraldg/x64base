<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# FIND

- Catalog/topic: `DOT` / `FIND`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Find text or values using the active order when possible, with scan fallback when needed.

- Seek an exact value using the active index/order
- Find text in the current table, delegating to SEEK when the active order can satisfy the request and otherwise scanning the selected field.

## Status

- implemented=yes; supported=yes

## Syntax

- SEEK &lt;expr&gt;
- SEEK &lt;expr&gt; IN &lt;alias&gt;
- FIND &lt;text&gt; [IN &lt;field&gt;]

## Usage

- FIND USAGE
- FIND &lt;text&gt;
- FIND &lt;field&gt; &lt;text&gt;
- FIND &lt;text&gt; IN &lt;field&gt;

## Example

- SEEK "SMITH"
- SEEK 1001
- SEEK DTOS(DATE())

## Note

- Requires an active table and normally an active order/index
- Successful SEEK intentionally moves the current record pointer
- Command wording should stay at the CDX/tag/order level; LMDB is a backend detail
- FIND requires an open table except for FIND USAGE.
- FIND with one text argument delegates to SEEK when an order is active.
- FIND with a field delegates to SEEK only when that field is the active tag.
- Otherwise FIND scans the requested field using ordered or physical traversal.
- FIND honors active SET FILTER visibility.
- FIND positions on the found record when successful.
- FIND restores the prior cursor when not found.

## Warning

- Do not document direct LMDB path parsing as public SEEK behavior

## Provenance

- Topic key: `DOT|FIND`
- Included HELP rows: `25`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
