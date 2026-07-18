<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# BUILDLMDB

- Catalog/topic: `DOT` / `BUILDLMDB`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Build or rebuild the LMDB backing store for the current CDX container; may mutate LMDB/index files but not table records.

- Build or rebuild the LMDB backing store for a CDX container using one LMDB environment per table container and named databases for tags.

## Status

- implemented=yes; supported=yes

## Syntax

- BUILDLMDB USAGE
- BUILDLMDB
- BUILDLMDB YES
- BUILDLMDB AUTO
- BUILDLMDB NOPROMPT
- BUILDLMDB CLEAN YES
- BUILDLMDB FORCE YES
- BUILDLMDB QUIET
- BUILDLMDB SILENT
- BUILDLMDB TINY
- BUILDLMDB SMALL
- BUILDLMDB MEDIUM
- BUILDLMDB LARGE
- BUILDLMDB XL
- BUILDLMDB HUGE
- BUILDLMDB MAPSIZE &lt;size&gt; YES
- BUILDLMDB [HELP|?] [MAPSIZE &lt;n[K|M|G]&gt;|SIZE &lt;n[K|M|G]&gt;|TINY|SMALL|MEDIUM|LARGE|XL|HUGE] [YES|AUTO|NOPROMPT] [CLEAN|FORCE] [QUIET]

## Usage

- BUILDLMDB USAGE
- BUILDLMDB
- BUILDLMDB YES
- BUILDLMDB AUTO
- BUILDLMDB NOPROMPT
- BUILDLMDB CLEAN YES
- BUILDLMDB FORCE YES
- BUILDLMDB QUIET
- BUILDLMDB SILENT
- BUILDLMDB TINY
- BUILDLMDB SMALL
- BUILDLMDB MEDIUM
- BUILDLMDB LARGE
- BUILDLMDB XL
- BUILDLMDB HUGE
- BUILDLMDB MAPSIZE &lt;size&gt; YES
- BUILDLMDB CLEAN MAPSIZE &lt;size&gt; YES

## Argument

- NOPROMPT
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Note

- BUILDLMDB requires an open table except for usage/help requests.
- The public CDX container resolves under INDEXES and the LMDB backend environment resolves under LMDB.
- If an existing LMDB environment would be destructively rebuilt, explicit YES, AUTO, NOPROMPT, QUIET, or SILENT is required.
- CLEAN and FORCE archive the existing environment before rebuild.
- BUILDLMDB releases active index/order state before destructive rebuild.
- BUILDLMDB rebuilds tag databases from current table data.

## Provenance

- Topic key: `DOT|BUILDLMDB`
- Included HELP rows: `45`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
