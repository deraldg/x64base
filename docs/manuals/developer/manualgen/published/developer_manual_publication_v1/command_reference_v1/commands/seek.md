<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SEEK

- Catalog/topic: `DOT` / `SEEK`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Seek through the active order or by scanning a requested field.

- Seek an exact value using the active index/order
- Seek a value through the active order/tag or by scanning a specified field.

## Status

- implemented=yes; supported=yes

## Syntax

- SEEK &lt;expr&gt;
- SEEK &lt;expr&gt; IN &lt;alias&gt;
- SEEK &lt;value&gt; [IN &lt;field&gt;] | SEEK &lt;field&gt; = &lt;value&gt;

## Usage

- SEEK USAGE
- SEEK &lt;value&gt; IN &lt;field&gt; [TRACE ON|OFF]
- SEEK &lt;field&gt; = &lt;value&gt; [TRACE ON|OFF]
- SEEK &lt;field&gt; &lt;value&gt; [TRACE ON|OFF]
- SEEK &lt;value&gt;
- SEEK TRACE ON
- SEEK TRACE OFF

## Example

- SEEK "SMITH"
- SEEK 1001
- SEEK DTOS(DATE())

## Note

- Requires an active table and normally an active order/index
- Successful SEEK intentionally moves the current record pointer
- Command wording should stay at the CDX/tag/order level; LMDB is a backend detail
- SEEK USAGE works without an open table.
- Bare SEEK with no open table preserves existing behavior and prints (empty).
- SEEK &lt;value&gt; uses the active order/tag when one is set.
- SET NEAR affects near-match reporting policy.
- SEEK may temporarily move the cursor while searching and leaves the cursor on a found/near match.

## Warning

- Do not document direct LMDB path parsing as public SEEK behavior

## Provenance

- Topic key: `DOT|SEEK`
- Included HELP rows: `26`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
