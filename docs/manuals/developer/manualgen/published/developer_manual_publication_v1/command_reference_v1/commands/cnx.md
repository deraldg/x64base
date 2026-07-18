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
- risk:
- reads_index_file: INFO TAGS WALK TRACE ADDTAG DROPTAG
- creates_index_file: CREATE
- overwrites_index_file: no, CREATE refuses existing target
- mutates_index_metadata: ADDTAG DROPTAG
- mutates_table_data: no
- diagnostic_tree_walk: WALK TRACE
- default_path_uses_order_state: yes
- default_path_uses_indexes_slot: yes

## Related

- CDX
- INDEX
- SET CNX
- SET ORDER

## Provenance

- Topic key: `DOT|CNX`
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
