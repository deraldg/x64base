<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# REBUILD

- Catalog/topic: `DOT` / `REBUILD`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Rebuild a CNX container for the current table, using the active CNX or a supplied CNX name/path and clearing TABLE stale state on success.

## Status

- implemented=yes; supported=yes

## Syntax

- REBUILD [USAGE|ALL|&lt;target&gt;]

## Usage

- REBUILD USAGE
- REBUILD
- REBUILD &lt;name-or-path.cnx&gt;

## Note

- REBUILD with no arguments uses the current CNX or defaults to &lt;table&gt;.cnx.
- REBUILD requires an open table except for REBUILD USAGE.
- REBUILD prompts to COMMIT dirty TABLE buffers before rebuilding.
- REBUILD refuses to continue if the table remains dirty after COMMIT.
- REBUILD opens the CNX tag directory once for reporting.
- The CNX backend rebuilds all tags in the container in one rebuild call.
- On success, TABLE STALE is cleared for the current area when table buffering is enabled.

## Related

- REINDEX
- CNX
- COMMIT
- TABLE

## Provenance

- Topic key: `DOT|REBUILD`
- Included HELP rows: `18`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
