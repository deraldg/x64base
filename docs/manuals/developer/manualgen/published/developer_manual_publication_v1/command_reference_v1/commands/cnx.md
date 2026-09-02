<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CNX

- Catalog/topic: `DOT` / `CNX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Index container command (CNX multi-tag support).

## Status

- implemented=yes; supported=yes

## Syntax

- CNX USAGE
- CNX INFO [&lt;path.cnx&gt;]
- CNX TAGS [&lt;path.cnx&gt;]
- CNX CREATE [&lt;path.cnx&gt;]
- CNX ADDTAG &lt;name&gt; [&lt;path.cnx&gt;]
- CNX DROPTAG &lt;name&gt; [&lt;path.cnx&gt;]
- CNX WALK &lt;tag&gt; [&lt;path.cnx&gt;]
- CNX TRACE &lt;tag&gt; [&lt;path.cnx&gt;]
- CNX &lt;name&gt;

## Usage

- CNX USAGE
- CNX INFO [&lt;path.cnx&gt;]
- CNX TAGS [&lt;path.cnx&gt;]
- CNX CREATE [&lt;path.cnx&gt;]
- CNX ADDTAG &lt;name&gt; [&lt;path.cnx&gt;]
- CNX DROPTAG &lt;name&gt; [&lt;path.cnx&gt;]
- CNX WALK &lt;tag&gt; [&lt;path.cnx&gt;]
- CNX TRACE &lt;tag&gt; [&lt;path.cnx&gt;]

## Argument

- NODE
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Note

- CNX with no arguments shows usage.
- If no path is supplied, CNX first uses the active CNX path from order state when available.
- Otherwise CNX derives &lt;current_dbf_basename&gt;.cnx through the INDEXES path slot.
- CREATE refuses to overwrite an existing file.
- INFO, TAGS, WALK, and TRACE are read-only inspection/diagnostic operations and require an existing file.
- WALK/TRACE use root_page_off from the CNX tag directory and follow plausible child offsets with loop/depth protection.
- ADDTAG and DROPTAG mutate the CNX container tag directory and require an existing file.
- ADDTAG requires an OPEN TABLE and refuses a &lt;name&gt; that does not resolve to one of its fields, through the same standard resolver REPLACE uses (xfg::resolve_field_index_std).
- A CNX tag IS a field name. Catching it here matters MORE than on the CDX side: REBUILD rebuilds the whole container in one call and then prints OK for every tag in the directory, reporting ok = tags.size(), so a dead tag is not merely unmentioned -- it is reported OK and counted (cmd_rebuild.cpp:285-315). REINDEX CNX delegates to REBUILD.
- DROPTAG is deliberately NOT field-checked: removing a tag whose field is gone is exactly when you need it, so requiring the field to exist would fence off the repair.

## Related

- CDX
- INDEX
- SET CNX
- SET ORDER
- REINDEX

## Provenance

- Topic key: `DOT|CNX`
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
