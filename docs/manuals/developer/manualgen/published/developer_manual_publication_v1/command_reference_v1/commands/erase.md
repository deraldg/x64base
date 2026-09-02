<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ERASE

- Catalog/topic: `DOT` / `ERASE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Physically delete a DBF table file plus known same-stem sidecars across DBF, INDEXES, and LMDB roots.

## Status

- implemented=yes; supported=yes

## Syntax

- ERASE USAGE
- ERASE &lt;table&gt; [CONFIRM]
- ERASE TABLE &lt;table&gt; [CONFIRM]
- ERASE DIR &lt;path&gt; [CONFIRM]
- ERASE [&lt;table&gt;|TABLE &lt;table&gt;|DIR &lt;path&gt;] [CONFIRM]

## Usage

- ERASE USAGE
- ERASE &lt;table&gt; [CONFIRM]
- ERASE TABLE &lt;table&gt; [CONFIRM]
- ERASE DIR &lt;path&gt; [CONFIRM]

## Example

- ERASE TABLE clients
- ERASE TABLE clients CONFIRM
- ERASE students.dbf CONFIRM
- ERASE DIR DBF\wbregress CONFIRM

## Note

- ERASE USAGE prints usage and does not inspect or delete files.
- Without CONFIRM, ERASE performs a dry-run and lists files that would be deleted.
- CONFIRM physically deletes the DBF, matching index containers/files, and matching LMDB backend directory when present.
- ERASE DIR deletes the named directory and everything under it; cwd-relative or absolute path, no SETPATH resolution, no sidecar sweep. Dry-run without CONFIRM.

## Related

- ZAP
- PACK
- COPY

## Provenance

- Topic key: `DOT|ERASE`
- Included HELP rows: `44`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
