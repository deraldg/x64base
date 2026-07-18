<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# USE

- Catalog/topic: `DOT` / `USE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Open a DBF table in the active DotTalk++ work area.

- Open a DBF table into the current work area, with duplicate-open guard, memo auto-attach, optional index auto-attach, and NOINDEX physical-order mode.

## Status

- implemented=yes; supported=yes

## Syntax

- USE &lt;table&gt; [ALIAS &lt;name&gt;] [NOINDEX]

## Usage

- USE USAGE
- USE &lt;table&gt;
- USE &lt;table.dbf&gt;
- USE &lt;path\table.dbf&gt;
- USE &lt;table&gt; NOINDEX
- USE &lt;table&gt; NOIDX

## Note

- USE requires a table name or path; no usable argument shows usage.
- Relative logical names resolve through the configured DBF path slot.
- USE prevents duplicate opens of the same DBF path across work areas.
- USE clears stale order/tag/container state and closes the current area before opening the new DBF.
- USE opens the target DBF and populates DbArea metadata.
- USE auto-attaches memo storage when memo fields are present.
- USE auto-attaches flavor-appropriate indexes when present, unless NOINDEX/NOIDX is specified.
- USE prefers the configured INDEXES slot and falls back to the DBF directory.
- NOINDEX/NOIDX opens the table in physical order and skips index auto-attach.
- USE is a session/area mutation command; it changes the current work area binding but should not mutate table records.

## Provenance

- Topic key: `DOT|USE`
- Included HELP rows: `20`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
