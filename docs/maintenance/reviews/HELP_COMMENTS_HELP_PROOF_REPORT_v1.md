# HELP Comments/Help Proof Report v1

Status: report-only maintenance proof artifact
Target: `HELP`
Workflow: `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

## Purpose

Instantiate the comments/help/router proof workflow on the top-level `HELP` command and record the current observed layer status.

This revision closes the parent `HELP` surface with direct comments-lane proof and current runtime smoke.

## Target

- Target: `HELP`
- Canonical command name: `HELP`
- Owner: `DOT|HELP`
- Primary source file: `src/cli/cmd_help.cpp`

## Phase 1: Source evidence

Observed evidence:

- `cmd_help.cpp` exists at [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:3)
- `@dottalk.usage v1` is present at [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:4)
- owner, command, summary, usage, notes, and related surfaces are present at [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:5), [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:6), [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:13), [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:17), [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:32), [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:44)

Status:

- Source evidence: green

## Phase 2: Comments evidence

Observed evidence:

- the comments evidence workflow and workspace are established in:
  - [COMMENTS_PIPELINE_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/lanes/comments/COMMENTS_PIPELINE_MANIFEST_v1.md:13)
  - [comments.dtschema](D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- staged source-comment imports contain `HELP` after targeted upsert from [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:3)
- live repo-runtime comments reload completed through the canonical [SOURCE_COMMENT_RESET_RELOAD.dts](D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)
- live runtime readback proves:
  - `SRCFILE.RELPATH = "src/cli/cmd_help.cpp"` at file row:
    - `914 | src/cli/cmd_help.cpp | src | cpp | "" | T | 50 | 1 | 50 | 51 | USAGE_CONTRACT | DOT|HELP | HELP | ACTIVE | 20260625`
  - `SRCUSAGE.COMMAND = "HELP"` at usage rows pointing at `FILEID = 914`
- live `SRCFILE` count checks show:
  - `COUNT FOR UPPER(RELPATH) == "SRC/CLI/CMD_HELP.CPP"` => `1`
  - `COUNT FOR UPPER(DET_CMD) == "HELP"` => `1`
- live `SRCFILE` row count is now `909` after the CSV-aware `IMPORT` repair

Status:

- Comments evidence: green

Interpretation:

- `HELP` has direct live `SRCFILE` and `SRCUSAGE` proof.
- the earlier comments-lane inconsistency was repaired by making `IMPORT` CSV-record aware, so the full staged `SRCFILE` set now materializes in the live repo runtime

## Phase 3: HELP DATA build

Observed evidence:

- `HELP` is itself the top-level router over multiple help surfaces at [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:13)
- no fresh standalone `CMDHELP BUILD` pass was required to prove current `HELP` routing behavior in this report

Status:

- HELP DATA build: not the primary continuity gate for this command

## Phase 4: CMDHELP proof

Observed evidence:

- `HELP` is directly related to `CMDHELP` and `CMDHELPCHK` at [cmd_help.cpp](D:/code/ccode/src/cli/cmd_help.cpp:45)
- the current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1) records a green help-family `CMDHELPCHK` proof pass after the SET-family canonicalization repair
- current implementation treats `CMDHELP HELP` as the self-usage surface for `CMDHELP`, so `HELP` continuity is proven through the parent help-family checkpoint rather than a separate `CMDHELP HELP` behavior change in this report

Status:

- CMDHELP: green at parent-surface continuity level; `CMDHELP HELP` remains a documented self-usage special case

## Phase 5: DOTREF / FOXREF router source

Observed evidence:

- `HELP` is present in the public native catalog at [dotref.hpp](D:/code/ccode/include/dotref.hpp:383)
- `HELP` is also present in the Fox-facing catalog at [foxref.hpp](D:/code/ccode/include/foxref.hpp:574)

Status:

- DOTREF source/catalog: green
- FOXREF parallel entry: green

## Phase 6: HELP runtime proof

Observed evidence:

- fresh runtime smoke on 2026-06-26 proves:
  - `HELP`: green
  - `HELP HELP`: green
  - `HELP /DOT HELP`: green
  - `HELP /FOX REL`: green
- `HELP` with no arguments printed the top-level router summary:
  - `Show command, function, predicate, SQL, and system help topics`
- `HELP HELP` rendered the canonical public entry:
  - syntax: `HELP [<topic>] [/FOX] [/PRED]`
  - summary: `General help entry point (supports /FOX and /PRED views).`
- `HELP /FOX REL` rendered the Fox-style `REL` help surface correctly

Status:

- HELP runtime surfaces: green in current runtime smoke

## Phase 7: CMDHELPCHK checkpoint

Observed evidence:

- the current curated parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1) records:
  - `Structural Checks`
  - `OK no structural issues found`
  - repaired artifact gate with compact SET-family command keys = `0`, compact SET-family artifact rows = `0`, and alias/variant rows = `0`

Status:

- CMDHELPCHK: green in current parent help-family checkpoint

## Continuity findings

Current truth:

- source evidence is green
- comments evidence is green
- native and Fox-facing catalog entries are both present
- current runtime smoke says the top-level `HELP` router is green
- the current curated parent help-family checkpoint is also green after the SET-family artifact canonicalization repair

## Layer summary

- Source evidence: green
- Comments evidence: green
- HELP DATA build: not the primary continuity gate for this command
- CMDHELP: green at parent-surface continuity level; `CMDHELP HELP` remains a documented self-usage special case
- DOTREF source/catalog: green
- FOXREF parallel entry: green
- HELP runtime surfaces: green in current runtime smoke
- CMDHELPCHK: green in current parent help-family checkpoint

## First red layer

- none observed in the current proof chain for `HELP`

## Last green checkpoint

- current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1), plus direct runtime proof that `HELP`, `HELP HELP`, `HELP /DOT HELP`, and `HELP /FOX REL` all work

## Recommended next gate

1. if the `HELP` router regresses again, compare native and Fox-facing catalog entries before touching HELP DATA
2. keep using live `SRCFILE` plus live `SRCUSAGE` proof after reset/reload as the baseline comments-lane standard
3. keep the CSV-aware `IMPORT` path in mind whenever staged metadata CSVs appear truncated again
4. preserve the current `CMDHELP HELP` self-usage rule unless a deliberate help-surface behavior change is authorized
