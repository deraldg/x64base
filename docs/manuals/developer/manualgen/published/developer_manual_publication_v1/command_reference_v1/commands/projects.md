<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# PROJECTS

- Catalog/topic: `DOT` / `PROJECTS`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect or manage DotTalk++ project/workflow entries and project-oriented local state.

- List, create, inspect, tree, or delete project skeleton directories under the configured PROJECTS slot.

## Status

- implemented=yes; supported=yes

## Syntax

- PROJECTS [USAGE|LIST|OPEN &lt;name&gt;|STATUS]

## Usage

- PROJECTS
- PROJECTS USAGE
- PROJECTS LIST
- PROJECTS CREATE &lt;name&gt; [DATA|FEATURE|HYBRID]
- PROJECTS INFO &lt;name&gt;
- PROJECTS TREE &lt;name&gt;
- PROJECTS DELETE &lt;name&gt; [CONFIRM]

## Example

- PROJECTS
- PROJECTS CREATE demo DATA
- PROJECTS INFO demo
- PROJECTS TREE demo
- PROJECTS DELETE demo
- PROJECTS DELETE demo CONFIRM

## Note

- PROJECTS with no arguments lists known projects.
- CREATE writes project skeleton folders and a manifest.
- DELETE is dry-run unless CONFIRM is supplied.
- PROJECTS USAGE prints usage and does not create/delete files.

## Provenance

- Topic key: `DOT|PROJECTS`
- Included HELP rows: `21`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
