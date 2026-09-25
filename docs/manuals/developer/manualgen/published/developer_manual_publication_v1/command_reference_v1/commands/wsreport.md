<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# WSREPORT

- Catalog/topic: `DOT` / `WSREPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Print a session status report: open workspaces and their areas, the order/LMDB summary, table-buffer state, and per-area index detail.

## Status

- implemented=yes; supported=yes

## Syntax

- WSREPORT
- WSREPORT USAGE
- WSREPORT ALL

## Usage

- WSREPORT
- WSREPORT USAGE
- WSREPORT ALL

## Argument

- NOTHING
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Note

- WSREPORT with no arguments reports the whole desk and the current area.
- WSREPORT ALL includes every open work area in the area/index summary.
- WSREPORT USAGE prints usage and inspects nothing.
- WSREPORT is read-only. It reports an invariant violation; it repairs none.
- The WORKSPACES section names workspaces. Until 2026-09-11 a section headed
- `Workspace` showed only work-area slots and never called the workspace table, so it read identically whether every area sat in DEFAULT or was spread across five named workspaces. That block is now `Work Areas`, which is what it always was.

## Related

- AREA
- STATUS
- WORKSPACE
- THE WORKSPACE LEVEL IS NOT COMPUTED HERE, and that is the change.
- `cli::workdesk::observe()` walks the workspace table and the engine's areas
- and returns the join; `cli::workdesk::render()` prints it. This file routes
- output and owns the three blocks that are genuinely its own. Before that
- split, three places each built the same workspace/area pairing privately --
- cmd_workspace.cpp inline, this file (badly, by omitting it), and
- cli::AmbiguityHit, whose ws_handles/engine_slots pair IS this join under
- another name. A fourth private walk is the thing to avoid, not a fourth
- report.

## Provenance

- Topic key: `DOT|WSREPORT`
- Included HELP rows: `34`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
