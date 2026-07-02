# MAINT Comments/Help Proof Report v1

Status: report-only maintenance proof artifact
Target: `MAINT`
Workflow: `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

## Purpose

Instantiate the comments/help/router proof workflow on `MAINT` and record the current observed layer status.

This revision records the live comments-lane green proof for `MAINT`, including the staged source-comment upsert and canonical comments-lane reload used to produce it.

## Target

- Target: `MAINT`
- Canonical command name: `MAINT`
- Owner: `DOT|MAINT`
- Primary source file: `src/cli/cmd_maint.cpp`

## Phase 1: Source evidence

Observed evidence:

- `cmd_maint.cpp` exists at [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:1)
- `@dottalk.usage v1` is present at [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:5)
- owner, command, summary, usage, and note rows are present at [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:6), [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:7), [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:11), [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:13), [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:20)

Status:

- Source evidence: green

## Phase 2: Comments evidence

Observed evidence:

- The comments evidence workflow and workspace are established in:
  - [COMMENTS_PIPELINE_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/lanes/comments/COMMENTS_PIPELINE_MANIFEST_v1.md:13)
  - [comments.dtschema](D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- staged source-comment imports now contain `MAINT` after targeted upsert from [cmd_maint.cpp](D:/code/ccode/src/cli/cmd_maint.cpp:1)
- live repo-runtime comments reload completed through the canonical [SOURCE_COMMENT_RESET_RELOAD.dts](D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)
- live runtime readback now proves:
  - `SRCFILE.DET_CMD = "MAINT"` at file row:
    - `909 | src/cli/cmd_maint.cpp | src | cpp | "" | T | 27 | 1 | 27 | 29 | USAGE_CONTRACT | DOT|MAINT | MAINT | ACTIVE | 20260625`
  - `SRCUSAGE.COMMAND = "MAINT"` at usage row:
    - `424 | 0 | 909 | DOT|MAINT | MAINT | "" | ACTIVE | "" | "" | "" | "" | "" | "" | "" | "" | ""`
- the reusable staging maint tool used for this pass is [upsert_source_comment_contract.py](D:/code/ccode/tools/comments/upsert_source_comment_contract.py:1)

Status:

- Comments evidence: green

Interpretation:

- `MAINT` source evidence is matched by direct `SRCFILE` / `SRCUSAGE` row-level proof in the live repo runtime.

## Phase 3: HELP DATA build

Observed evidence:

- `MDO-330` records MAINT `CMDHELP BUILD` / smoke closeout in [mdo_330_maint_cmdhelp_build_smoke_closeout_summary_v1.md](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_330_maint_cmdhelp_build_smoke_closeout_summary_v1.md:1)
- `mdo_330_maint_cmdhelp_validation_v1.csv` records `MDO-329 CMDHELP build/smoke plan green` and operator `CMDHELP MAINT` acceptance in [mdo_330_maint_cmdhelp_validation_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_330_maint_cmdhelp_validation_v1.csv:1)

Status:

- HELP DATA build: green when operator-accepted

## Phase 4: CMDHELP proof

Observed evidence:

- `mdo_330_maint_help_path_closeout_v1.csv` records `cmdhelp_path` green-when-operator-accepted in [mdo_330_maint_help_path_closeout_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_330_maint_help_path_closeout_v1.csv:1)
- `mdo_330_maint_cmdhelp_validation_v1.csv` records `operator MAINT CMDHELP smoke accepted` in [mdo_330_maint_cmdhelp_validation_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_330_maint_cmdhelp_validation_v1.csv:1)

Status:

- CMDHELP: green when operator-accepted

## Phase 5: DOTREF/router source

Observed evidence:

- Canonical live header is `include/dotref.hpp`
- `MAINT` is present in the canonical DOTREF header at [dotref.hpp](D:/code/ccode/include/dotref.hpp:469)
- usage and notes are present in the canonical DOTREF entry at [dotref.hpp](D:/code/ccode/include/dotref.hpp:472), [dotref.hpp](D:/code/ccode/include/dotref.hpp:481)
- `mdo_330_maint_cmdhelp_build_smoke_closeout_summary_v1.md` states canonical DOTREF remains `include/dotref.hpp` in [mdo_330_maint_cmdhelp_build_smoke_closeout_summary_v1.md](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_330_maint_cmdhelp_build_smoke_closeout_summary_v1.md:5)

Status:

- DOTREF source/catalog: green

## Phase 6: DOTHELP / HELP /DOT runtime proof

Observed evidence:

- `mdo_330_maint_help_path_closeout_v1.csv` records `dotref_path` green-when-operator-accepted and explicitly says `DOTHELP MAINT / HELP /DOT MAINT` prove the path in [mdo_330_maint_help_path_closeout_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_330_maint_help_path_closeout_v1.csv:1)
- `mdo_333_maint_cmdhelpchk_report_only_smoke_closeout_summary_v1.csv` records:
  - `dothelp_maint_visible = 1`
  - `help_dot_maint_visible = 1`
  in [mdo_333_maint_cmdhelpchk_report_only_smoke_closeout_summary_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_333_maint_cmdhelpchk_report_only_smoke_closeout_summary_v1.csv:1)

Status:

- DOTHELP / HELP /DOT: green when operator-accepted

## Phase 7: CMDHELPCHK checkpoint

Observed evidence:

- `mdo_333_maint_cmdhelpchk_report_only_smoke_closeout_summary_v1.csv` records:
  - `cmdhelpchk_report_only_smoke_closed = 1`
  - `maint_cmdhelp_visible = 1`
  - `dothelp_maint_visible = 1`
  - `help_dot_maint_visible = 1`
  in [mdo_333_maint_cmdhelpchk_report_only_smoke_closeout_summary_v1.csv](D:/code/ccode/docs/manuals/developer/manualgen/reports/mdo_333_maint_cmdhelpchk_report_only_smoke_closeout_summary_v1.csv:1)

Status:

- CMDHELPCHK: green when operator-accepted

## Continuity findings

Current truth:

- source evidence is green
- comments evidence is green
- HELP DATA / CMDHELP proof is green
- canonical DOTREF source is green
- DOTHELP / HELP /DOT proof is green
- CMDHELPCHK proof is green

Main continuity drift:

- `MAINT` was already green in upper help/router layers before the comments lane had explicit row-level proof
- the earlier gap was stale comments-lane staging, not a defect in the `MAINT` source contract

## Layer summary

- Source evidence: green
- Comments evidence: green
- HELP DATA build: green when operator-accepted
- CMDHELP: green when operator-accepted
- DOTREF source/catalog: green
- DOTHELP / HELP /DOT: green when operator-accepted
- CMDHELPCHK: green when operator-accepted

## First red layer

- none observed in the current proof chain for `MAINT`

## Last green checkpoint

- `MDO-333` report-only CMDHELPCHK closeout, with direct comments-lane proof now added in this report

## Recommended next gate

1. carry the same comments-lane upsert/reload proof to `MANUAL`
2. extend the source-comment harvester/upsert path to support block-comment contract headers, then run the workflow on `DDICT`
3. keep using this same workflow for continuity-first help/router proof
