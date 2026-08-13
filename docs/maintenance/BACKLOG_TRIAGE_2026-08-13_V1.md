# Working-tree backlog triage, 2026-08-13

    Steward   : member.ai.claude.cowork
    Owner     : member.derald
    Measured  : 2026-08-13, working tree at 5283c6d49 (pushed)
    Status    : triage only. NOTHING here is staged. Several slices belong to
                sessions other than this one and are not mine to commit.

---

## 0. Method, and two corrections it forced

Measured with read-only git (`--no-optional-locks`), no index touched.

**83 tracked files modified.** Not 1,676 -- that first figure was stderr
line-ending warnings flooding the pipe, not content. Worth recording because
`git diff --name-only | wc -l` without `2>/dev/null` will mislead anyone who
repeats it here.

Two claims this triage made and then had to withdraw, both from testing one
thing and concluding about a class:

1. *"Not em-dash work."* Tested by counting `U+2014` only. The real pattern is a
   broader NON-ASCII sweep -- U+00B7 middle dot (8), U+2014 em-dash (4),
   U+2026 ellipsis (2), U+2192 arrow (1), U+2717 ballot-X (1). The
   owner's hypothesis was right in kind; the sweep is just small (10 removed
   lines of 1,099) and confined to tooling.
2. *"Gates are the highest risk of the set."* False. All four tooling diffs are
   character substitution with **zero behaviour change**. They are the SAFEST
   slice here, not the most dangerous.

Both mistakes have the shape this session has been documenting all day. Recorded
rather than smoothed over.

---

## 1. Shape of the 83

    5,132 added / 1,099 removed lines.

Roughly 3,500 of the added lines are REGENERATED ARTIFACTS, not authored work:
`portal_truth_audit_latest.json` alone is +2,796, `AI_PORTAL_REPORT.html` +433,
`ai_runs.yaml` +198, `portal.yaml` +104. Ten more files are binary HELP-store
tables. So the backlog is much smaller than 83 files suggests: it is a handful
of real lanes wearing a lot of generated output.

---

## 2. Proposed slices, ordered by how safely they can go out

### S0. This session's refinement (mine, ready)

    src/cli/cmd_workspace.cpp
    docs/maintenance/RAM_MINIDB_MEMO_WORKSPACE_OPERATIONS_V1.md
    docs/ai-friendly/PSEUDO_CHAT_BOARD.md

The `appendBlank()` claim refined from "nothing else writes it" to "nothing the
SYSTEM writes puts a non-memo row here" (17 files call `appendBlank`; only
`cmd_workspace.cpp` names the catalog, but 16 generic writers exist and the
catalog is an ordinary table). Plus the challenge post to the hosted coworker.
Compile clean, ASCII clean.

### S1. ASCII sweep reaches the tooling (SAFEST -- zero behaviour)

    tools/staging/prepush_gate.py
    tools/coordination/session_coordinator.py
    tools/coordination/aif_collision_gate.py
    labtalk/ai_portal/audit_trail.py

Ten lines, all character substitution in docstrings and console output. Partly
closes the AIF-088 shape for `.py`, which `check_house_style.py` never covered
(`CHECKED_SUFFIXES = (".md",)`, and it inspects ADDED lines only).

### S2. Source-tree litter deletions (safe, verified as deletions)

    shell_api.cpp                                        (repo ROOT)
    src/cli/build_help.ps1
    src/cli/vfp.dts
    src/cli/export_current_syntax_smoke.dts
    src/cli/cursor_family_regression_001_cdx_sandbox.dts

479 lines removed, confirmed `delete mode` via `--summary`. Scripts and a stray
`.cpp` living in the source tree.

Reference sweep RAN (scoped to `src include tools docs`, excluding build trees):
**no references** to `vfp.dts`, `export_current_syntax_smoke.dts`,
`cursor_family_regression_001_cdx_sandbox.dts`, or `build_help.ps1`.

`shell_api.cpp` swept separately, because a `.cpp` at the repo root was the one
most likely to be named in a build file. Result: **two files of that name are
tracked** --

    shell_api.cpp           (repo ROOT)   <- the deletion
    src/cli/shell_api.cpp   13,080 B      <- the real one, untouched

The root copy is a stray duplicate, and no `CMakeLists.txt` / `.cmake` /
`.vcxproj` / `.ps1` names `shell_api` outside the build trees (the build globs
sources rather than listing them). The deletion removes a duplicate, not the
translation unit. **S2 is fully verified.**

### S3. `@dottalk.file` contract headers on tests (mechanical)

    16 files, each exactly +9 -0, identical block:
    tests/{dewey_benchmark, sqlite_adapter, tv_probe, xbase_probe,
           xbase_64_probe, xbase_vfp_probe, test_expr, test_sql_where,
           test_where_cache_only, test_lmdb_backend.cpp/.hpp,
           test_dot_talk_m365_integration(.e2e), identity/*3}
    tools/app_paxon.hpp  (+9 -0, same shape)

Zero behaviour. **One thing to check first:** v6 hints section 5 records the
harvest at "205 files" against 229 contract-bearing `.cpp` tree-wide, and nobody
knows whether the miner is `src/cli`-shaped. Adding 17 contract blocks changes
that arithmetic, so land this BEFORE the v6 harvest-scope measurement or the
baseline moves under it.

### S4. `USE_AGAIN` lane (another session's -- needs its author)

    src/cli/cmd_use.cpp        +258 -10
    src/cli/cmd_regression.cpp  +61 -1   (spec 46, "USE_AGAIN")

Owner-directed 2026-08-12 ("add use again", then "fix the use command"). The
spec's own text says the marker count is deliberately unstated because it
changed. Looks complete; I have not run it and it is not my lane.

### S5. `ERP RELATIONS` / AIF-105 (another session's)

    src/edu/edu_erp.cpp  +112 -13   (adds ERP RELATIONS, stamps lane AIF-105)

Also unattributed-to-me and unrun.

### S6. Small source edits, unclassified

    src/cli/expr/glue_xbase.cpp   +26 -0
    src/help/helpdata_messages.cpp +4 -4
    src/cli/cmd_order.cpp          +2 -2

Not inspected in detail. Cheap to classify; I did not.

### S7. Generated portal / report output (needs a policy answer, not a review)

    labtalk/reports/portal/portal_truth_audit_latest.json   +2796 -298
    labtalk/reports/portal/portal_truth_audit_latest.md       +99 -55
    docs/reports/{AI_PORTAL_REPORT,index,BBS_BOARDS_REPORT,
                  BBS_ACCESS_REPORT,AIF_RULINGS_REPORT}.html
    labtalk/registries/{portal.yaml, ai_runs.yaml}
    labtalk/portal/{README.md, tests/test_runtime_paths.py}

These are tool output. The question is not "is the diff correct" but "does
generated output get committed, and at what cadence" -- a standing policy
question, and reviewing 2,796 lines of regenerated JSON by eye is not the
answer to it.

### S8. HELP store binaries (needs a ruling)

    dottalkpp/data/help/{HELP_TOPIC,HELP_SECTION,HELP_LINE,HELP_ARTIFACTS,
                         COMMANDS,CMD_ARGS}.dbf + 3 .dbt
    dottalkpp/data/indexes/x32/STUDENTS.cnx

The v5 `CMDHELP BUILD` output. `prepush_gate` warns on data fixtures and blocks
build trees, so this needs a deliberate decision: is the built HELP store an
artifact of record that ships with the flush, or a build product that should
never be committed? v6 hints section 2 is the related open item -- the store
carries NO provenance rows, so a committed store cannot say which binary or
commit produced it.

### S9. Lane documents (11 in docs/maintenance, plus labtalk + docs/ai-friendly)

Four session closeouts, `GATE_GOVERNANCE_LANE_V1`, `PREPUSH_GATE_REFERENCE_V1`,
`AI_SYSTEMS_*`, `DEVELOPMENT_ACCELERATION_ANALYSIS_LANE_V1`, the flush cookbook,
`ENTITY_LIFECYCLE_AND_THE_BRIDGE_V1` (+139), a July whitepaper (+95),
`PROMOTION_PROCESS/CHECKLIST`, contract registry entries. Per-lane; each wants
its own author or an owner sweep.

---

## 3. Separate finding: task 20 is genuinely still open

`dottalkpp/data/scripts/metadata/SYSFUNC_IMPORT_v1.csv` has 5 added rows --
`PADC`, `PADL`, `PADR`, `PROPER`, `STUFF` -- all tagged "runtime builtin spec
without curated FunctionDoc row."

**`FILE` is not among them.** So the partial regeneration did not close the
`FN_COVERAGE` warn, and task 20 is open on its merits rather than accidentally
satisfied. Worth knowing before anyone reads the CSV's mtime as evidence.

---

## 4. What I recommend, and what I will not do

Ready now, mine or mechanical: **S0, S1, S3** (S3 after the harvest-baseline
note above). **S2 after** its reference sweep actually runs.

Not mine to stage: S4, S5, S9. The house rule is explicit that a slice must not
fuse several sessions' half-done work, and three of these are exactly that.

Needs a ruling before anyone can act: **S7** (generated-output policy) and
**S8** (built HELP store).

Unfinished in this triage, stated rather than implied: the S2 reference sweep,
and the S6 classification.
