# FOXHELP Comments/Help Proof Report v1

Status: report-only maintenance proof artifact
Target: `FOXHELP`
Workflow: `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

## Purpose

Instantiate the comments/help/router proof workflow on `FOXHELP` and record the current observed layer status.

This revision adds direct live comments-lane proof for `FOXHELP` and records the current dual-catalog continuity fact: the command is sourced in `foxref.hpp`, while an equivalent public entry is also present in `dotref.hpp`.

## Target

- Target: `FOXHELP`
- Canonical command name: `FOXHELP`
- Owner: `DOT|FOXHELP`
- Primary source file: `src/cli/cmd_foxhelp.cpp`

## Phase 1: Source evidence

Observed evidence:

- `cmd_foxhelp.cpp` exists at [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:1)
- `@dottalk.usage v1` is present at [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:2)
- owner, command, summary, usage, notes, and related surfaces are present at [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:3), [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:4), [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:11), [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:14), [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:23), [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:35)

Status:

- Source evidence: green

## Phase 2: Comments evidence

Observed evidence:

- the comments evidence workflow and workspace are established in:
  - [COMMENTS_PIPELINE_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/lanes/comments/COMMENTS_PIPELINE_MANIFEST_v1.md:13)
  - [comments.dtschema](D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- staged source-comment imports contain `FOXHELP` after targeted upsert from [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:1)
- live repo-runtime comments reload completed through the canonical [SOURCE_COMMENT_RESET_RELOAD.dts](D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts:1)
- live runtime readback now proves:
  - `SRCFILE.DET_CMD = "FOXHELP"` at file row:
    - `104 | src/cli/cmd_foxhelp.cpp | src | cpp | "" | T | 40 | 1 | 40 | 41 | USAGE_CONTRACT | DOT|FOXHELP | FOXHELP | ACTIVE | 20260521`
  - `SRCUSAGE.COMMAND = "FOXHELP"` at usage row:
    - `112 | 0 | 104 | DOT|FOXHELP | FOXHELP | "" | ACTIVE | "" | "" | "" | "" | "" | "" | "" | "" | ""`
- the reusable staging maint tool used for this pass is [upsert_source_comment_contract.py](D:/code/ccode/tools/comments/upsert_source_comment_contract.py:1)

Status:

- Comments evidence: green

Interpretation:

- `FOXHELP` source evidence is matched by direct `SRCFILE` / `SRCUSAGE` row-level proof in the live repo runtime.

## Phase 3: HELP DATA build

Observed evidence:

- `FOXHELP` notes explicitly say it uses the static catalog and any HELP DBFs at [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:24)
- runtime smoke shows `FOXHELP` works as a read-only catalog/report surface even without proving a fresh HELP DBF regeneration in this pass

Status:

- HELP DATA build: partially evidenced, not freshly re-proved in this pass

## Phase 4: CMDHELP proof

Observed evidence:

- `FOXHELP` is adjacent to `CMDHELP` in both source metadata and catalog definitions at [cmd_foxhelp.cpp](D:/code/ccode/src/cli/cmd_foxhelp.cpp:37), [foxref.hpp](D:/code/ccode/include/foxref.hpp:588), [dotref.hpp](D:/code/ccode/include/dotref.hpp:397)
- the current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1) records a green `CMDHELP FOXHELP` rendering pass after the SET-family canonicalization repair
- that same closeout confirms the public artifact surface now emits the canonical `DOT|FOXHELP` and `FOX|FOXHELP` pairing without stale compact SET-family duplicates

Status:

- CMDHELP: green in current parent same-pass closeout

## Phase 5: FOXREF / DOTREF router source

Observed evidence:

- canonical Fox-style header is `include/foxref.hpp`
- `FOXHELP` is present in `foxref.hpp` at [foxref.hpp](D:/code/ccode/include/foxref.hpp:577)
- an equivalent public `FOXHELP` entry is also present in `dotref.hpp` at [dotref.hpp](D:/code/ccode/include/dotref.hpp:386)

Status:

- FOXREF source/catalog: green
- DOTREF parallel entry: green

Interpretation:

- current runtime behavior is consistent with `FOXHELP` being a real command with Fox-style catalog backing and an exposed native help-family entry in DOTREF
- this is a continuity fact, not a defect, until evidence shows the two catalogs drift apart

## Phase 6: DOTHELP / HELP /DOT / FOXHELP runtime proof

Observed evidence:

- fresh runtime smoke on 2026-06-26 proves:
  - `DOTHELP FOXHELP`: green
  - `HELP /DOT FOXHELP`: green
  - `FOXHELP`: green
  - `FOXHELP APPEND`: green
  - `FH REL`: green
- `DOTHELP FOXHELP` and `HELP /DOT FOXHELP` rendered the canonical public entry:
  - syntax: `FOXHELP [<term>]`
  - summary: `List or search command help topics.`
- `FOXHELP` with no arguments listed the FoxPro-style command subset and ended with:
  - `Tip: FOXHELP <NAME> for details, e.g. FOXHELP INDEX`

Status:

- DOTHELP / HELP /DOT / FOXHELP runtime surfaces: green in current runtime smoke

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
- `foxref.hpp` source is green
- `dotref.hpp` also exposes a public `FOXHELP` entry
- current runtime smoke says `DOTHELP FOXHELP`, `HELP /DOT FOXHELP`, `FOXHELP`, `FOXHELP APPEND`, and `FH REL` all work
- current parent help-family checkpoint also proves the `CMDHELP FOXHELP` artifact surface is green after the SET-family repair

Main continuity repair in this pass:

- `FOXHELP` now has direct live comments-lane row proof and a current recorded runtime smoke set

Main continuity watchpoint:

- `FOXHELP` is represented in both `foxref.hpp` and `dotref.hpp`, so future edits should keep summary/examples aligned across both catalogs

## Layer summary

- Source evidence: green
- Comments evidence: green
- HELP DATA build: partially evidenced, not freshly re-proved in this pass
- CMDHELP: green in current parent same-pass closeout
- FOXREF source/catalog: green
- DOTREF parallel entry: green
- DOTHELP / HELP /DOT / FOXHELP runtime surfaces: green in current runtime smoke
- CMDHELPCHK: green in current parent help-family checkpoint

## First red layer

- none observed in the current proof chain for `FOXHELP`

## Last green checkpoint

- current parent closeout at [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md:1), plus live runtime smoke proving `DOTHELP FOXHELP`, `HELP /DOT FOXHELP`, `FOXHELP`, `FOXHELP APPEND`, and `FH REL` all work

## Recommended next gate

1. treat `foxref.hpp` as the Fox-facing source of truth, but keep the parallel `dotref.hpp` public entry synchronized
2. if `FOXHELP` regresses again, compare the two catalog entries before assuming a HELP DBF or command-dispatch defect
3. continue the same proof workflow on adjacent help-family commands so comments, compiled catalogs, and runtime surfaces stay aligned
