<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CDX

- Catalog/topic: `DOT` / `CDX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Manage CDX index container metadata: create containers, inspect header/tag directories, add tags, and drop tags.

## Status

- implemented=yes; supported=yes

## Syntax

- CDX [INFO|TAGS|CREATE|ADDTAG|DROPTAG] [&lt;path.cdx&gt;]

## Usage

- CDX USAGE
- CDX INFO [&lt;path.cdx&gt;]
- CDX TAGS [&lt;path.cdx&gt;]
- CDX CREATE [&lt;path.cdx&gt;]
- CDX ADDTAG &lt;name&gt; [&lt;path.cdx&gt;]
- CDX DROPTAG &lt;name&gt; [&lt;path.cdx&gt;]

## Note

- CDX with no arguments shows usage and does not default to INFO.
- If no path is supplied, CDX first uses the active CDX path from order state when available.
- Otherwise CDX derives &lt;current_dbf_basename&gt;.cdx through the INDEXES path slot.
- CREATE refuses to overwrite an existing file.
- INFO and TAGS are read-only inspection operations and require an existing file.
- ADDTAG and DROPTAG mutate the CDX container tag directory and require an existing file.
- ADDTAG requires an OPEN TABLE and refuses a &lt;name&gt; that does not resolve to one of its fields, through the same standard resolver REPLACE uses (xfg::resolve_field_index_std):
- a CDX tag IS a field name, and BUILDLMDB builds each tag FROM the field of that name.
- Before 2026-08-29 any string was accepted here and the miss was swallowed at BUILD time without a message, leaving a container carrying a tag nothing would ever fill.
- DROPTAG is deliberately NOT field-checked: removing a tag whose field is gone is exactly when you need it, so requiring the field to exist would fence off the repair.
- CDX manages container header/tag metadata; backend tag build data persistence is owned elsewhere.
- INFO's per-tag root_off/recs fields are written by the NATIVE rebuild only (2026-09-22):
- BUILDLMDB -- the x64 default flow -- reads tag NAMES and never writes the directory back, so those fields read 0 on an LMDB-backed container while the env holds the live keys.
- INFO appends a pathless note saying so when the env exists; LMDB INFO has the live counts.

## Related

- CNX
- INDEX
- SET CDX
- SET ORDER
- REINDEX

## Provenance

- Topic key: `DOT|CDX`
- Included HELP rows: `34`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
