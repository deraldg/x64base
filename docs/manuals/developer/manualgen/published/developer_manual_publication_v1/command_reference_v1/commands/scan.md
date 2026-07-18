<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SCAN

- Catalog/topic: `DOT` / `SCAN`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Iterate records using a SCAN block (record loop).

- Buffer and execute a SCAN...ENDSCAN record loop over the current logical rowset.

## Status

- implemented=yes; supported=yes

## Syntax

- SCAN [ALL|DELETED] [FOR &lt;pred&gt;] [WHILE &lt;pred&gt;] [NEXT &lt;n&gt;|REST]

## Usage

- SCAN
- SCAN USAGE
- SCAN FOR &lt;expr&gt;
- ENDSCAN
- ENDSCAN USAGE

## Note

- SCAN with no arguments starts buffering a scan block on the current area.
- SCAN FOR &lt;expr&gt; adds a predicate to the scan loop.
- ENDSCAN executes buffered body lines through the canonical command executor.
- Deleted records and active SET FILTER visibility are honored by the scan gate.
- Active order traversal uses shared order_iterator when available, with physical fallback.
- ENDSCAN restores the user's cursor best-effort after execution.

## Provenance

- Topic key: `DOT|SCAN`
- Included HELP rows: `15`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
