<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SCHEMAS

- Catalog/topic: `DOT` / `SCHEMAS`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Deprecated compatibility shim for WORKSPACE.<br><br>        Current mapping:<br>            SCHEMAS             -&gt; WORKSPACE<br>            SCHEMAS OPEN &lt;arg&gt;  -&gt; WORKSPACE OPEN &lt;arg&gt;<br>            SCHEMAS CLOSE

- Manage live work-area/session state
- Deprecated compatibility shim that routes old SCHEMAS commands to WORKSPACE.
- Deprecated compatibility shim for WORKSPACE.
- Current mapping:
- SCHEMAS             -&gt; WORKSPACE
- SCHEMAS OPEN &lt;arg&gt;  -&gt; WORKSPACE OPEN &lt;arg&gt;
- SCHEMAS CLOSE       -&gt; WORKSPACE CLOSE
- Notes:
- Use WORKSPACE for live work-area/session operations.
- Use DDL for schema/definition operations.
- SCHEMAS remains only so older DotScript files continue to run.

## Status

- implemented=yes; supported=yes

## Syntax

- WORKSPACE
- WORKSPACE OPEN DBF
- WORKSPACE OPEN &lt;dir&gt;
- WORKSPACE ADD &lt;file.dbf&gt;
- WORKSPACE CLOSE
- WORKSPACE SAVE &lt;name&gt;
- WORKSPACE LOAD &lt;name&gt;
- SCHEMAS [OPEN &lt;DBF|dir&gt;|CLOSE]

## Usage

- SCHEMAS
- SCHEMAS USAGE
- SCHEMAS OPEN &lt;arg&gt;
- SCHEMAS CLOSE

## Example

- WORKSPACE
- WORKSPACE CLOSE
- WORKSPACE OPEN DBF
- WORKSPACE ADD students
- WORKSPACE SAVE mcc
- WORKSPACE LOAD mcc.dtschemas

## Note

- WORKSPACE owns live areas, aliases, orders, and relation/session layout
- WORKSPACE OPEN replaces area membership; WORKSPACE ADD preserves existing areas
- DDL owns schema/definition work
- SCHEMAS remains a compatibility shim for older scripts
- SCHEMAS with no arguments still routes to WORKSPACE list behavior.
- SCHEMAS OPEN &lt;arg&gt; routes to WORKSPACE OPEN &lt;arg&gt;.
- SCHEMAS CLOSE routes to WORKSPACE CLOSE.
- SCHEMAS USAGE prints compatibility guidance and does not route to WORKSPACE.
- WORKSPACE owns live area/session behavior; DDL owns schema/definition work.

## Provenance

- Topic key: `DOT|SCHEMAS`
- Included HELP rows: `39`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
