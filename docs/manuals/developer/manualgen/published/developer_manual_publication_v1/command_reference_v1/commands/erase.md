<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ERASE

- Catalog/topic: `DOT` / `ERASE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Erase a file or supported target through the DotTalk++ shell surface.

- Physically delete a DBF table file plus known same-stem sidecars across DBF, INDEXES, and LMDB roots.

## Status

- implemented=yes; supported=yes

## Syntax

- ERASE &lt;target&gt;

## Usage

- ERASE USAGE
- ERASE &lt;table&gt; [CONFIRM]
- ERASE TABLE &lt;table&gt; [CONFIRM]

## Example

- ERASE TABLE clients
- ERASE TABLE clients CONFIRM
- ERASE students.dbf CONFIRM

## Note

- ERASE USAGE prints usage and does not inspect or delete files.
- Without CONFIRM, ERASE performs a dry-run and lists files that would be deleted.
- CONFIRM physically deletes the DBF, matching index containers/files, and matching LMDB backend directory when present.

## Provenance

- Topic key: `DOT|ERASE`
- Included HELP rows: `13`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
