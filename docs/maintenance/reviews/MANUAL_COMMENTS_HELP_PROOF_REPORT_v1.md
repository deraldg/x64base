# MANUAL Comments/Help Proof Report v1

Status: report-only maintenance proof artifact
Target: `MANUAL`
Workflow: `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

## Purpose

Instantiate the comments/help/router proof workflow on `MANUAL` and record the current observed layer status.

This revision adds direct live comments-lane proof for `MANUAL` so the command now matches the same continuity standard already used for `BBOX`, `MAINT`, and `DDICT`.

## Target

- Target: `MANUAL`
- Canonical command name: `MANUAL`
- Owner: `DOT|MANUAL`
- Primary source file: `src/cli/cmd_manual.cpp`

## Phase 1: Source evidence

Observed evidence:

- `cmd_manual.cpp` exists at [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:1)
- `@dottalk.usage v1` is present at [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:1)
- owner, command, summary, usage, and notes are present at [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:2), [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:3), [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:10), [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:13), [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:24)

Status:

- Source evidence: green

## Phase 2: Comments evidence

Observed evidence:

- the comments evidence workflow and workspace are established in:
  - [COMMENTS_PIPELINE_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/lanes/comments/COMMENTS_PIPELINE_MANIFEST_v1.md:13)
  - [comments.dtschema](D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- staged source-comment imports now contain `MANUAL` after targeted upsert from [cmd_manual.cpp](D:/code/ccode/src/cli/cmd_manual.cpp:1)
- live repo-runtime comments reload completed through the canonical [SOURCE_COMMENT_RESET_RELOAD.dts](D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)
- live runtime readback now proves:
  - `SRCFILE.DET_CMD = "MANUAL"` at file row:
    - `911 | src/cli/cmd_manual.cpp | src | cpp | "" | T | 41 | 1 | 41 | 43 | USAGE_CONTRACT | DOT|MANUAL | MANUAL | ACTIVE | 20260625`
  - `SRCUSAGE.COMMAND = "MANUAL"` at usage row:
    - `429 | 0 | 911 | DOT|MANUAL | MANUAL | "" | ACTIVE | "" | "" | "" | "" | "" | "" | "" | "" | ""`
- the reusable staging maint tool used for this pass is [upsert_source_comment_contract.py](D:/code/ccode/tools/comments/upsert_source_comment_contract.py:1)

Status:

- Comments evidence: green

Interpretation:

- `MANUAL` source evidence is matched by direct `SRCFILE` / `SRCUSAGE` row-level proof in the live repo runtime.

## Phase 3: HELP DATA build

Observed evidence:

- the help pipeline notes place `MANUAL` in the current HELP/CMDHELP split investigation in [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md:24)
- prior manual runtime smoke and closeout artifacts remain green in:
  - [mdo_290_manual_native_runtime_smoke_manifest_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_290_manual_native_runtime_smoke_manifest_v1.csv:2)
  - [mdo_291_manual_runtime_smoke_closeout_summary_v1.md](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_291_manual_runtime_smoke_closeout_summary_v1.md:15)
- fresh same-pass closeout on 2026-06-26 is recorded in [DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md:1)
- that closeout records:
  - `CMDHELPCHK ARTIFACTS . 5`
  - `compact DOT SET-family artifact rows: 0`
  - current release HELP DATA visibility for `CMDHELP MANUAL`

Status:

- HELP DATA build: green in current same-pass closeout

## Phase 4: CMDHELP proof

Observed evidence:

- the help pipeline notes record `CMDHELP MANUAL works` in [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md:30)
- reviewed candidate help rows exist for `DOT|MANUAL` in [mdo_294_help_cmdhelpchk_candidate_review_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_294_help_cmdhelpchk_candidate_review_v1.csv:2)
- fresh same-pass closeout on 2026-06-26 records `CMDHELP MANUAL` rendering `DOT|MANUAL` with the canonical summary/syntax surface in [DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md:1)

Status:

- CMDHELP: green in current same-pass closeout

## Phase 5: DOTREF/router source

Observed evidence:

- canonical live header is `include/dotref.hpp`
- `MANUAL` is present in the canonical DOTREF header at [dotref.hpp](D:/code/ccode/include/dotref.hpp:428)
- usage and notes are present in the canonical DOTREF entry at [dotref.hpp](D:/code/ccode/include/dotref.hpp:431), [dotref.hpp](D:/code/ccode/include/dotref.hpp:442)

Status:

- DOTREF source/catalog: green

## Phase 6: DOTHELP / HELP /DOT runtime proof

Observed evidence:

- fresh runtime smoke on 2026-06-26 is recorded in [HELP_DOT_ROUTER_SMOKE_DDICT_MANUAL_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_DOT_ROUTER_SMOKE_DDICT_MANUAL_20260626_v1.md:1)
- `DOTHELP MANUAL` rendered the canonical DOTREF entry in the current repo runtime
- `HELP /DOT MANUAL` rendered the canonical DOTREF entry in the current repo runtime
- the help pipeline notes now preserve the older red state as historical only in [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md:17)

Status:

- DOTHELP / HELP /DOT: green in current runtime smoke

## Phase 7: CMDHELPCHK checkpoint

Observed evidence:

- fresh same-pass closeout on 2026-06-26 is recorded in [DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md:1)
- `CMDHELPCHK` noargs ended with:
  - `Structural Checks`
  - `OK no structural issues found`
- `CMDHELPCHK ARTIFACTS . 5` reported:
  - `compact DOT SET-family command keys : 0`
  - `compact DOT SET-family artifact rows: 0`
  - `SET-family alias/variant rows       : 0`

Status:

- CMDHELPCHK: green in current same-pass closeout

## Continuity findings

Current truth:

- source evidence is green
- comments evidence is green
- current same-pass `CMDHELP MANUAL` proof is green
- canonical DOTREF source is green
- current runtime smoke says both `DOTHELP MANUAL` and `HELP /DOT MANUAL` work
- current same-pass curated checkpoint proof is green

Main continuity repair in this pass:

- `MANUAL` no longer relies on source-only evidence in the comments lane
- the command now has the same live `SRCFILE` / `SRCUSAGE` row proof standard as the other maintenance/help proof targets

## Layer summary

- Source evidence: green
- Comments evidence: green
- HELP DATA build: green in current same-pass closeout
- CMDHELP: green in current same-pass closeout
- DOTREF source/catalog: green
- DOTHELP / HELP /DOT: green in current runtime smoke
- CMDHELPCHK: green in current same-pass closeout

## First red layer

- none observed in the current proof chain for `MANUAL`

## Last green checkpoint

- same-pass closeout on 2026-06-26 at [DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md:1), with direct proof across `CMDHELPCHK`, HELP DATA artifacts, `CMDHELP MANUAL`, and the native/runtime router surfaces

## Recommended next gate

1. keep the historical router-red note only as prior-investigation context, not as current defect status
2. if `MANUAL` regresses again, compare first against the 2026-06-26 same-pass closeout artifact
3. reconcile stale planning notes that still describe `MANUAL` as pending checkpoint work
