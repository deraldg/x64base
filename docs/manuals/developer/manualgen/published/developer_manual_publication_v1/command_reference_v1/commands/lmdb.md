<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LMDB

- Catalog/topic: `DOT` / `LMDB`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect or manage per-area LMDB-backed index/storage wiring where supported.

- Inspect and control the per-area LMDB backed CDX index backend through the current DbArea IndexManager.

## Status

- implemented=yes; supported=yes

## Syntax

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

## Provenance

- Topic key: `DOT|LMDB`
- Included HELP rows: `24`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
