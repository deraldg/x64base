<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# BUILDLMDB

- Catalog/topic: `DOT` / `BUILDLMDB`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Build or rebuild the LMDB backing store for a CDX container using one LMDB environment per table container and named databases for tags.

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
- BUILDLMDB CLEAN MAPSIZE &lt;size&gt; YES
- BUILDLMDB CLEAN ARCHIVE YES
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
- BUILDLMDB CLEAN ARCHIVE YES

## Argument

- NOPROMPT
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Note

- BUILDLMDB requires an open table except for usage/help requests.
- The public CDX container resolves under INDEXES and the LMDB backend environment resolves under LMDB.
- If an existing LMDB environment would be destructively rebuilt, explicit YES, AUTO, NOPROMPT, QUIET, or SILENT is required.
- CLEAN and FORCE DISCARD the superseded environment before rebuild. It is a
- DERIVED artifact, regenerated here from the .cdx container and the table;
- the container is ~3 KB against a multi-hundred-megabyte environment, so retaining the environment protects nothing the sources do not.
- ARCHIVE (or KEEP) opts in to retaining it under backups/ instead. This was the silent default until 2026-07-27 (AIF-065) and is how a 73 GB LMDB tree accumulated one rebuild at a time.
- ARCHIVE IS NOT A SAFETY FEATURE. BUILDLMDB reads the container and writes the environment (see risk block); it never modifies the declaration, so a size change puts nothing irrecoverable at risk. ARCHIVE exists only for a deliberate before/after comparison of index CONTENT. The commands that DO restructure the container -- CDX CREATE and CDX ADDTAG -- archive nothing today, which is where a ~3 KB snapshot would actually earn its place.
- Archive the thing that CHANGES, at the command that changes it; size is not a reason to keep a copy, irrecoverability is.
- BUILDLMDB releases active index/order state before destructive rebuild.
- BUILDLMDB rebuilds tag databases from current table data.

## Related

- CDX
- LMDB
- SET ORDER
- INDEX
- REINDEX

## Provenance

- Topic key: `DOT|BUILDLMDB`
- Included HELP rows: `67`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
