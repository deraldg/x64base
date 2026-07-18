<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CDX

- Catalog/topic: `DOT` / `CDX`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect or manage CDX container metadata and tag directories.

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
- CDX manages container header/tag metadata; backend tag build data persistence is owned elsewhere.
- risk:
- reads_index_file: INFO TAGS ADDTAG DROPTAG
- creates_index_file: CREATE
- overwrites_index_file: no, CREATE refuses existing target
- mutates_index_metadata: ADDTAG DROPTAG
- mutates_table_data: no
- default_path_uses_order_state: yes
- default_path_uses_indexes_slot: yes

## Related

- CNX
- INDEX
- SET CDX
- SET ORDER
- REINDEX
- include "xbase.hpp"

## Provenance

- Topic key: `DOT|CDX`
- Included HELP rows: `36`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
