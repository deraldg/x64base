# Comments Pipeline Manifest v1

Status: captured maintenance manifest
Lane: comments
Runtime workspace: comments

## Purpose

The comments lane preserves source comments and `@dottalk.usage v1` contracts as evidence. It protects fragile source-level documentation so HELP, CMDHELP, manuals, data dictionary records, and future repair/regeneration tools can rely on durable facts.

## Current runtime placement

The live comments evidence tables currently sit at:

- `dottalkpp/data/comments`
- `dottalkpp/data/workspaces/comments.dtschema`

Known opened tables:

- MEMO_LINES
- SRCALIAS
- SRCBLOCK
- SRCCLASS
- SRCDISP
- SRCFILE
- SRCLINE
- SRCUSAGE

## Blackbox model

DATA IN

- source files
- header comments
- `@dottalk.usage v1` contracts
- command-local usage text

PROCESS

- scan
- harvest
- classify
- import
- validate
- compare coverage

INFORMATION OUT

- SRCFILE source inventory
- SRCBLOCK harvested blocks
- SRCLINE line evidence
- SRCUSAGE parsed usage contracts
- SRCCLASS classifier results
- SRCDISP disposition rows
- SRCALIAS alias/canonical mappings
- MEMO_LINES long text support

## Relationship to HELP

The comments lane is below HELP. It should answer whether source contracts exist and how they were classified before HELP or DOTREF is blamed for visibility problems.

Current builder boundary:

- the comments workspace is a preserved evidence layer
- current `CMDHELP BUILD` still mines source files and `@dottalk.usage v1` contracts directly
- current HELP DATA rebuilds do not yet read back from `SRCFILE`/`SRCUSAGE` as their primary feed

Key questions for a command:

- Does SRCFILE know the source file?
- Does SRCUSAGE know the command?
- Does SRCCLASS consider the block valid?
- Does SRCALIAS define aliases/canonical names?
- Does SRCDISP mark review/defer/accept?
- Which HELP DATA layer consumes it?

## Safety boundary

Default is report-only. Source edits, HELP mutation, metadata mutation, classifier policy changes, CMDHELPCHK changes, and DBF rewrites require explicit authorization.
