<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# WORKSPACE

- Catalog/topic: `DOT` / `WORKSPACE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Canonical live work-area/session command.<br><br>        Usage:<br>            WORKSPACE<br>                List current open work areas.<br><br>            WORKSPACE CLOSE<br>                Close all work areas and clea

- Manage live work-area/session state
- Report and manage live work-area/session layout.
- Canonical live work-area/session command.
- Usage:
- WORKSPACE
- List current open work areas.
- WORKSPACE CLOSE
- Close all work areas and clear relation state.
- WORKSPACE OPEN DBF
- Scan the configured DBF path slot and open tables into areas 0..N.
- WORKSPACE OPEN &lt;dir&gt;
- Scan a specific directory and open DBFs into areas 0..N.
- WORKSPACE SAVE &lt;name&gt;
- Save a workspace layout where supported.
- WORKSPACE LOAD &lt;name&gt;
- Restore a saved workspace layout where supported.
- Notes:
- WORKSPACE owns live areas, aliases, index/tag bindings, and relation/session layout.
- DDL owns schema/definition work.
- WSREPORT owns verbose diagnostics.

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
- WORKSPACE [OPEN &lt;DBF|dir&gt;|CLOSE|SAVE &lt;name&gt;|LOAD &lt;name&gt;]

## Usage

- WORKSPACE
- WORKSPACE USAGE
- WORKSPACE ALL
- WORKSPACE OPEN DBF
- WORKSPACE OPEN &lt;dir&gt;
- WORKSPACE OPEN &lt;file.dbf&gt;
- WORKSPACE ADD &lt;file.dbf&gt;
- WORKSPACE ADD &lt;target&gt; CNX [FALLBACK] [TABLE]
- WORKSPACE ADD &lt;target&gt; INX|IDX [FALLBACK] [TABLE]
- WORKSPACE ADD &lt;target&gt; CDX [FALLBACK] [TABLE]
- WORKSPACE OPEN &lt;target&gt; CNX [FALLBACK] [recursive] [TABLE]
- WORKSPACE OPEN &lt;target&gt; INX|IDX [FALLBACK] [recursive] [TABLE]
- WORKSPACE OPEN &lt;target&gt; CDX [FALLBACK] [recursive] [TABLE]
- WORKSPACE CLOSE
- WORKSPACE CLOSE &lt;n&gt; [m ...]
- WORKSPACE CLOSE &lt;name|file|stem|alias&gt;[,...]
- WORKSPACE SAVE &lt;file&gt;
- WORKSPACE LOAD &lt;file&gt;
- WORKSPACE TUPLES [LIMIT &lt;n&gt;] [OFFSET &lt;n&gt;] [AREA &lt;n&gt;]

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

## Provenance

- Topic key: `DOT|WORKSPACE`
- Included HELP rows: `58`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
