<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LMDB

- Catalog/topic: `DOT` / `LMDB`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect and control the per-area LMDB backed CDX index backend through the current DbArea IndexManager.

- Per-area LMDB/CDX backend inspection and control command.
- Command-owned @dottalk.usage v1 summary.

## Status

- implemented=yes; supported=yes

## Syntax

- LMDB USAGE
- LMDB INFO
- LMDB OPEN &lt;container.cdx&gt;
- LMDB OPEN &lt;envdir.cdx.d&gt;
- LMDB OPEN &lt;stem&gt;
- LMDB USE &lt;tag&gt;
- LMDB SEEK &lt;key&gt;
- LMDB DUMP
- LMDB DUMP &lt;max&gt;
- LMDB SCAN &lt;low&gt; &lt;high&gt;
- LMDB CLOSE
- LMDB command (per-area):
- LMDB DUMP [&lt;max&gt;]
- LMDB [USAGE|INFO|OPEN|USE|SEEK|DUMP|SCAN|CLOSE] ...

## Usage

- LMDB USAGE
- LMDB INFO
- LMDB OPEN &lt;container.cdx&gt;
- LMDB OPEN &lt;envdir.cdx.d&gt;
- LMDB OPEN &lt;stem&gt;
- LMDB USE &lt;tag&gt;
- LMDB SEEK &lt;key&gt;
- LMDB DUMP
- LMDB DUMP &lt;max&gt;
- LMDB SCAN &lt;low&gt; &lt;high&gt;
- LMDB CLOSE
- Per-area LMDB/CDX backend inspection and control command.
- LMDB command (per-area):
- LMDB DUMP [&lt;max&gt;]

## Note

- LMDB is a thin wrapper over the current area IndexManager and CDX backend.
- LMDB does not use LMDB_UTIL or any shared global LMDB environment.
- Bare stems are resolved through the INDEXES path slot.
- OPEN attaches the CDX container and updates legacy order state.
- USE selects an active tag and updates legacy active-tag state.
- SEEK searches the selected tag and reports the matching record number.
- DUMP and SCAN inspect the selected tag.
- CLOSE closes the current area index manager and clears order state.
- LMDB mutates index/order session state but not table records.
- LMDB is a thin wrapper over the current area IndexManager/CDX backend.
- Runtime status and error output is intentionally separate from this usage contract.

## Related

- CDX
- CNX
- SET INDEX
- SET ORDER
- LMDBDUMP
- LMDB_UTIL

## Provenance

- Topic key: `DOT|LMDB`
- Included HELP rows: `50`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
