# DOTHELP Comments/Help Proof Report v1

Status: report-only maintenance proof artifact
Target: `DOTHELP`
Workflow: `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

## Purpose

Instantiate the comments/help/router proof workflow on `DOTHELP` and record the current observed layer status.

This revision adds direct live comments-lane proof for `DOTHELP` and closes the command's current native help/router continuity in the repo runtime.

## Target

- Target: `DOTHELP`
- Canonical command name: `DOTHELP`
- Owner: `DOT|DOTHELP`
- Primary source file: `src/cli/cmd_dothelp.cpp`

## Phase 1: Source evidence

Observed evidence:

- `cmd_dothelp.cpp` exists at [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:1)
- `@dottalk.usage v1` is present at [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:1)
- owner, command, summary, usage, notes, and related surfaces are present at [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:2), [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:3), [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:10), [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:13), [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:19), [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:30)

Status:

- Source evidence: green

## Phase 2: Comments evidence

Observed evidence:

- the comments evidence workflow and workspace are established in:
  - [COMMENTS_PIPELINE_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/lanes/comments/COMMENTS_PIPELINE_MANIFEST_v1.md:13)
  - [comments.dtschema](D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- staged source-comment imports contain `DOTHELP` after targeted upsert from [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:1)
- live repo-runtime comments reload completed through the canonical [SOURCE_COMMENT_RESET_RELOAD.dts](D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)
- live runtime readback now proves:
  - `SRCFILE.DET_CMD = "DOTHELP"` at file row:
    - `912 | src/cli/cmd_dothelp.cpp | src | cpp | "" | T | 34 | 1 | 34 | 36 | USAGE_CONTRACT | DOT|DOTHELP | DOTHELP | ACTIVE | 20260625`
  - `SRCUSAGE.COMMAND = "DOTHELP"` at usage row:
    - `430 | 0 | 912 | DOT|DOTHELP | DOTHELP | "" | ACTIVE | "" | "" | "" | "" | "" | "" | "" | "" | ""`
- the reusable staging maint tool used for this pass is [upsert_source_comment_contract.py](D:/code/ccode/tools/comments/upsert_source_comment_contract.py:1)

Status:

- Comments evidence: green

Interpretation:

- `DOTHELP` source evidence is matched by direct `SRCFILE` / `SRCUSAGE` row-level proof in the live repo runtime.

## Phase 3: HELP DATA build

Observed evidence:

- the help pipeline notes place `DOTHELP` in the current HELP/CMDHELP/DOTREF split investigation in [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md:14)
- `DOTHELP` is itself a native help/router surface and does not rely on HELP DBF rows for the compiled DOTREF entry it prints

Status:

- HELP DATA build: not the primary continuity gate for this command

## Phase 4: CMDHELP proof

Observed evidence:

- `DOTHELP` is related to `CMDHELP` at [cmd_dothelp.cpp](D:/code/ccode/src/cli/cmd_dothelp.cpp:33)
- the current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1) records a green `CMDHELP DOTHELP` rendering pass after the SET-family canonicalization repair
- that same closeout confirms the public artifact surface emits the canonical `DOT|DOTHELP` identity without stale compact SET-family duplicates

Status:

- CMDHELP: green in current parent same-pass closeout

## Phase 5: DOTREF/router source

Observed evidence:

- canonical live header is `include/dotref.hpp`
- `DOTHELP` is present in the canonical DOTREF header at [dotref.hpp](D:/code/ccode/include/dotref.hpp:628)

Status:

- DOTREF source/catalog: green

## Phase 6: DOTHELP / HELP /DOT runtime proof

Observed evidence:

- fresh runtime smoke on 2026-06-26 proves:
  - `DOTHELP DOTHELP`: green
  - `HELP /DOT DOTHELP`: green
- both commands rendered the canonical native entry:
  - syntax: `DOTHELP [<term>]`
  - summary: `Show project-native DotTalk++ reference entries from the DOTREF catalog.`

Status:

- DOTHELP / HELP /DOT: green in current runtime smoke

## Phase 7: CMDHELPCHK checkpoint

Observed evidence:

- the current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1) records:
  - `Structural Checks`
  - `OK no structural issues found`
  - compact SET-family command keys = `0`
  - compact SET-family artifact rows = `0`
  - SET-family alias/variant rows = `0`

Status:

- CMDHELPCHK: green in current parent help-family checkpoint

## Continuity findings

Current truth:

- source evidence is green
- comments evidence is green
- canonical DOTREF source is green
- current runtime smoke says both `DOTHELP DOTHELP` and `HELP /DOT DOTHELP` work
- current parent help-family checkpoint also proves the `CMDHELP DOTHELP` artifact surface is green after the SET-family repair

Main continuity repair in this pass:

- `DOTHELP` now has direct live comments-lane row proof, not just source/header proof

## Layer summary

- Source evidence: green
- Comments evidence: green
- HELP DATA build: not the primary continuity gate for this command
- CMDHELP: green in current parent same-pass closeout
- DOTREF source/catalog: green
- DOTHELP / HELP /DOT: green in current runtime smoke
- CMDHELPCHK: green in current parent help-family checkpoint

## First red layer

- none observed in the current proof chain for `DOTHELP`

## Last green checkpoint

- current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1), plus live runtime smoke proving both `DOTHELP DOTHELP` and `HELP /DOT DOTHELP` render the canonical DOTREF entry

## Recommended next gate

1. keep using `DOTHELP` as a canonical proof surface for compiled DOTREF visibility
2. if `DOTHELP` regresses again, compare the runtime router behavior against the current direct comments-lane row evidence before touching HELP DBFs
3. continue the same workflow on adjacent help-family commands so source, comments, and runtime proof stay aligned
