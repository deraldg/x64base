# CMDHELP Comments/Help Proof Report v1

Status: report-only maintenance proof artifact
Target: `CMDHELP`
Workflow: `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

## Purpose

Instantiate the comments/help/router proof workflow on the `CMDHELP` build/report parent surface and record the current observed layer status.

This revision normalizes the source contract for `cmdhelp.cpp`, captures current runtime smoke, and records a real comments-lane continuity defect instead of masking it.

## Target

- Target: `CMDHELP`
- Canonical command name: `CMDHELP`
- Owner: `DOT|CMDHELP`
- Primary source file: `src/cli/cmdhelp.cpp`

## Phase 1: Source evidence

Observed evidence:

- `cmdhelp.cpp` exists at [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:1)
- this pass converted the file from doctrine-only header comments to a formal `@dottalk.usage v1` contract at [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:1)
- owner, command, summary, usage, notes, risk, and related surfaces are now present at [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:2), [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:3), [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:10), [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:13), [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:21), [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:31), [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:36)

Status:

- Source evidence: green

## Phase 2: Comments evidence

Observed evidence:

- staged source-comment imports contain `CMDHELP` after targeted upsert from [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:1)
- staged `SRCFILE_IMPORT.csv` contains:
  - `913 | src/cli/cmdhelp.cpp | src | cpp | ... | DOT|CMDHELP | CMDHELP | ACTIVE | 20260625`
- staged `SRCUSAGE_IMPORT.csv` contains `DOT|CMDHELP | CMDHELP` rows pointing at `FILEID = 913`
- live repo-runtime comments reload completed through the canonical [SOURCE_COMMENT_RESET_RELOAD.dts](D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)
- live runtime readback proves:
  - `SRCFILE.RELPATH = "src/cli/cmdhelp.cpp"` at file row:
    - `913 | src/cli/cmdhelp.cpp | src | cpp | "" | T | 40 | 1 | 40 | 41 | USAGE_CONTRACT | DOT|CMDHELP | CMDHELP | ACTIVE | 20260625`
  - `SRCUSAGE.COMMAND = "CMDHELP"` exists:
    - two live `SRCUSAGE` rows point at `FILEID = 913`
- live `SRCFILE` count checks show:
  - `COUNT FOR UPPER(RELPATH) == "SRC/CLI/CMDHELP.CPP"` => `1`
  - `COUNT FOR UPPER(DET_CMD) == "CMDHELP"` => `1`
- live `SRCFILE` row count is now `909` after the CSV-aware `IMPORT` repair

Status:

- Comments evidence: green

Interpretation:

- the earlier defect was not in `CMDHELP` harvesting
- it was in the line-oriented `IMPORT` path used by the comments reset/reload script
- once `IMPORT` became CSV-record aware, `CMDHELP` materialized cleanly in live `SRCFILE`

## Phase 3: HELP DATA build

Observed evidence:

- `CMDHELP` is the current HELP DATA build/report surface by design at [cmdhelp.cpp](D:/code/ccode/src/cli/cmdhelp.cpp:10)
- the current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1) records a same-pass `CMDHELPCHK` green result after repairing the compact SET-family artifact duplication defect
- that parent closeout is sufficient current build/report continuity for `CMDHELP` because the repaired artifact gate is part of the HELP DATA reporting path owned by `CMDHELP`

Status:

- HELP DATA build: green at current parent same-pass closeout level

## Phase 4: CMDHELP runtime proof

Observed evidence:

- fresh runtime smoke on 2026-06-26 proves:
  - `CMDHELP`: green
  - `CMDHELP USAGE`: green
- `CMDHELP` noargs reported current HELP DATA successfully, including:
  - directory: `D:\code\ccode\dottalkpp\data\help`
  - line rows: `8251`
  - topics: `481`
  - source counts including `USAGE_CONTRACT = 4,532`
- `CMDHELP USAGE` printed the current public syntax set including:
  - `CMDHELP`
  - `CMDHELP USAGE`
  - `CMDHELP BUILD`
  - `CMDHELP BUILD . <source-root>`
  - `CMDHELP <topic>`
  - `CMDHELP BUILD LEGACY`
  - `CMDHELP LEGACY`

Status:

- CMDHELP runtime surfaces: green in current runtime smoke

## Phase 5: DOTREF / FOXREF router source

Observed evidence:

- `CMDHELP` is present in the native public catalog at [dotref.hpp](D:/code/ccode/include/dotref.hpp:397)
- `CMDHELP` is also present in the Fox-facing catalog at [foxref.hpp](D:/code/ccode/include/foxref.hpp:588)

Status:

- DOTREF source/catalog: green
- FOXREF parallel entry: green

## Phase 6: CMDHELPCHK checkpoint

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
- runtime `CMDHELP` and `CMDHELP USAGE` surfaces are green
- staged comment imports are green
- live comments evidence is green
- current parent help-family checkpoint is green after the compact SET-family artifact repair

Main continuity repair in this pass:

- `cmdhelp.cpp` now participates in the same formal source-contract workflow as the rest of the help family
- the CSV-aware `IMPORT` repair now allows the full staged `SRCFILE` set to load, including `CMDHELP`

## Layer summary

- Source evidence: green
- Comments evidence: green
- HELP DATA build: green at current parent same-pass closeout level
- CMDHELP runtime surfaces: green in current runtime smoke
- DOTREF source/catalog: green
- FOXREF parallel entry: green
- CMDHELPCHK: green in current parent help-family checkpoint

## First red layer

- none observed in the current proof chain for `CMDHELP`

## Last green checkpoint

- current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1), plus live comments reset/reload on 2026-06-26 importing all `909` `SRCFILE` rows and runtime smoke proving `CMDHELP` and `CMDHELP USAGE` work

## Recommended next gate

1. keep `cmdhelp.cpp` on the formal source-contract path
2. preserve the CSV-aware `IMPORT` behavior because the comments lane depends on it
3. if staged/live row counts diverge again, inspect the import boundary before blaming command-specific harvesting
4. preserve the current `CMDHELP HELP` self-usage rule unless a deliberate help-surface behavior change is authorized
