<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CDX

- Catalog/topic: `DOT` / `CDX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect or manage CDX container metadata and tag directories. ramfs/VDISK-aware: under a mounted VDISK the container resolves from RAM (a native CDX-V64), so CREATE/ADDTAG/DROPTAG operate on the in-RAM container with no file on disk (AIF-043).

## Status

- implemented=yes; supported=yes

## Syntax

- CDX USAGE
- CDX INFO [&lt;path.cdx&gt;]
- CDX TAGS [&lt;path.cdx&gt;]
- CDX CREATE [&lt;path.cdx&gt;]
- CDX ADDTAG &lt;name&gt; [&lt;path.cdx&gt;]
- CDX DROPTAG &lt;name&gt; [&lt;path.cdx&gt;]
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

## Related

- CNX
- INDEX
- SET CDX
- SET ORDER
- REINDEX

## Provenance

- Topic key: `DOT|CDX`
- Included HELP rows: `35`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
