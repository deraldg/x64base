<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ERSATZ

- Catalog/topic: `DOT` / `ERSATZ`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Launch or drive the Ersatz relational browser/demo surface for workspace and relation-graph inspection.

- Relational browser and tuple-stream helper for current workspace/session, with navigation, tree/grid rendering, workspace handoff, and delta baselines.

## Status

- implemented=yes; supported=yes

## Syntax

- ERSATZ [USAGE|&lt;args...&gt;]

## Usage

- ERSATZ
- ERSATZ USAGE
- ERSATZ SHOW
- ERSATZ REFRESH
- ERSATZ TREE
- ERSATZ GRID
- ERSATZ STATUS
- ERSATZ ORDER
- ERSATZ TOP
- ERSATZ BOTTOM
- ERSATZ NEXT
- ERSATZ NEXT &lt;n&gt;
- ERSATZ PREV
- ERSATZ PREV &lt;n&gt;
- ERSATZ SKIP &lt;n&gt;
- ERSATZ ROOT
- ERSATZ ROOT &lt;alias&gt;
- ERSATZ LIMIT &lt;n&gt;
- ERSATZ PATH &lt;alias&gt;
- ERSATZ CLEARPATH
- ERSATZ BACK
- ERSATZ OPEN &lt;workspace&gt;
- ERSATZ LOAD &lt;name&gt;
- ERSATZ SAVE &lt;name&gt;
- ERSATZ WLOAD &lt;name&gt;
- ERSATZ DELTA MARK &lt;name&gt;
- ERSATZ DELTA SHOW &lt;name&gt;
- ERSATZ DELTA CLEAR &lt;name&gt;
- ERSATZ DELTA CLEAR ALL
- ERSATZ DELTA STATUS
- ERSATZ RESET

## Note

- ERSATZ with no arguments renders the current relational browser snapshot.
- SHOW, REFRESH, TREE, and GRID render the current browser session.
- TOP, BOTTOM, NEXT, PREV, and SKIP navigate the root cursor and render.
- ROOT, LIMIT, PATH, CLEARPATH, and BACK mutate browser session settings.
- OPEN hands off to WORKSPACE.
- LOAD, SAVE, and WLOAD read or write workspace files.
- DELTA commands manage in-memory tuple-stream baselines.
- RESET clears ERSATZ browser session state.
- ERSATZ is not table-data mutation by itself, but it can mutate cursor/session/workspace state.

## Provenance

- Topic key: `DOT|ERSATZ`
- Included HELP rows: `44`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
