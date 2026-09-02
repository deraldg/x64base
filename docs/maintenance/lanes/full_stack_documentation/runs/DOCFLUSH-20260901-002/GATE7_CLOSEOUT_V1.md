---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260902-COWORK-015
  recorded_at_utc: 2026-09-02T00:30:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: COWORK-20260826-002
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 45f699a23
  authorization:
    requested_by: maintainer (member.derald), in-session, "start over and do it right
      all the way through the fullstack this time, not skipping steps", then
      "you have step by step instructions on what to do". Phase 4 and the E2
      reflection run were executed by the maintainer directly on the host.
    scope: >
      Gate 7 closeout for DOCFLUSH-20260901-002 (v8). Records Gates 0 through 6,
      the entry-condition state, and one new finding. Publication was not entered
      and is not claimed.
  report:
    path: docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260901-002/GATE7_CLOSEOUT_V1.md
    kind: gate-record
---

# DOCFLUSH-20260901-002 (v8) -- Gate 7 closeout

    run        : DOCFLUSH-20260901-002 (v8)
    lane       : full_stack_documentation
    owner      : member.derald
    steward    : member.ai.claude.cowork
    branch     : development
    baseline   : 45f699a23  (2026-09-01)
    prior      : v7 = DOCFLUSH-20260901-001. v6 = DOCFLUSH-20260825-001.
    motto      : normalize -- smooth -- improve

    STATUS     : CLOSED at Gate 7.
    PUBLICATION: NOT ENTERED. Phase 8 is a separate lane.

## What v8 was, in one line

The first run since 2026-07-16 to carry the pipeline end to end -- and it found
that the reflection surface certifying the whole thing keeps a fourth,
unchecked copy of the SET ladder.

## Gates

    Gate 0    run envelope         GATE0_RUN_ENVELOPE_V1.md
    Gate 0.5  contract coverage    GATE0_5_CONTRACT_STATE_V1.md
    Gate 1    reference drift      GATE1_REFERENCE_DISPOSITION_V1.md
    Gate 2    pre-refresh runtime  AUTHORED, NOT CAPTURED -- see the gap below
    Gate 3    refresh package      help_refresh/
    Gate 4    HELP refresh         GATE4_5_6_REFRESH_AND_CANDIDATES_V1.md  (owner-run)
    Gate 5    metadata candidates  same record
    Gate 6    manual candidate     same record
    Gate 7    this file

## Entry conditions at close -- measured at this baseline, none inherited

    E1  dev run closed at Gate 7    THIS FILE. v8 closes.
    E2  CMDHELPCHK reflection       PASS. Owner-run on the host against the new
                                    store. "OK no structural issues found."
    E3  contracts 100 percent       PASS. census 1080/1080, uncovered 0.
    E4  refcheck + normcheck        PASS. Both arms, re-run at 45f699a23.
    E5  harvest after the build     PASS. 14/14 after re-export; 9/14 before.
    E6  command-catalog.mdx         HOLD. Site branch unruled. Not attempted.
    E7  backup + rollback named     **UNCONFIRMED.** See below.
    E8  per-mutation authorization  Phase 4 authorized and run by the owner
                                    directly. Gates 5 and 6 produced candidates
                                    only; nothing was imported or accepted.

**Seven of eight hold. E6 is a deliberate hold. E7 is the one open row**, and it
is open in the honest direction: the Phase 4 transcript shows
`CMDHELP BUILD LEGACY` and `CMDHELP BUILD . <src>` but no backup step before
them. If no dated `help.bak-*` was taken for this refresh, the rollback path has
no named target. That is worth settling now rather than discovering at the next
rebuild. (Related, carried from v7: twelve backup directories already exist,
~617 MB, and nothing rotates them.)

## THE FINDING: a fourth copy of the SET ladder, and nothing checks it

E2 passed, and reading its output produced this.

`CMDHELPCHK`'s Subcommand Inventory prints 23 SET subcommands. They come from
`collect_set_subcommands()` in `src/cli/reference_collection.cpp` -- **a
hand-maintained literal list of `add(...)` calls.**

`stack_audit_v1.py` check G (`SUBCMD_COV`) exists precisely to compare
representations of this surface, and its docstring names **three**:

    1. the LADDER      if (opt == "X") arms in src/cli/cmd_set.cpp
                       -- "the only one that actually dispatches anything"
    2. the USAGE TEXT  MessageId::SetUsageText
    3. the TABLE       dottalkpp/data/metadata/SYSSUBCMD.dbf

`collect_set_subcommands()` is a **fourth**, and check G does not read it.

Measured at 45f699a23:

    ladder arms (dispatching)  36
    reflection SET rows        23

    In the ladder, absent from the reflection list:
      CONSOLE, DEVDIAG, ERRORSTOP, INDEXTXN, LANGUAGE, LOCALE, MESSAGE,
      NEAR, UNIQUE
      (plus HELP and USAGE, meta arms; SETCASE and SETNEAR, alias spellings
       check G already folds; and TABLE, which the reflection carries as
       "TABLE BUFFER" -- naming variance, not absence)

    In the reflection list, absent from the ladder:
      none

**Verified at the CALL SITES, not the declarations**, because a declaration
proves nothing:

    src/cli/cmd_set.cpp:1670   if (opt == "NEAR" || opt == "SETNEAR")  -> cmd_SETNEAR   (1672)
    src/cli/cmd_set.cpp:1848   if (opt == "UNIQUE")                    -> cmd_SET_UNIQUE (1850)

Both dispatch. Both are published by CMDHELP as `implemented=yes supported=yes`
(`SET NEAR` id 197, `SET UNIQUE` id 396). Neither appears in the reflection
surface that certifies the catalog. **And Structural Checks reports OK** -- the
AIF-118 shape this house already has a name for: a check returning the same
answer for "absent" and "fine."

Two of the nine, `LANGUAGE` and `LOCALE`, are the same pair
`DOTREF_COV/SUBCOMMAND_ONLY` describes as *"the gap that orphaned the SET
LANGUAGE / SET LOCALE locale topics"* -- the same defect arriving from a fourth
direction, which is corroboration rather than a second finding.

### Why this is the lane's own subject matter

Three columns of that report are compile-time constants, not measurements. Every
row is written by one lambda that hardcodes:

    sc.authority   = "command_catalog";
    sc.status      = "partial";
    sc.source_file = "cmd_set.cpp";

So `AUTHORITY: command_catalog` reads as a fact discovered about each
subcommand and is a string literal written once. `SET RELATION`'s real handler is
`cmd_SET_RELATION`, not `cmd_set.cpp`'s -- the column says otherwise for all 23.

This is the same defect as the 64-name literal list in
`is_expression_function_name()` that this session replaced with a delegation to
the function catalog: a hand-kept second copy of something the engine already
knows. It strengthens the case for that change and it is the same fix shape --
derive the list, do not retype it.

**Not fixed here.** It is a source change to a reflection surface, found at the
end of a run, and by the owner's standing ruling that is a decision made when a
mission closes and can be back-verified -- which is now. Two shapes:

  (a) derive `collect_set_subcommands()` from the ladder, the way `cmdhelp.cpp`
      now asks the function catalog. Removes the copy rather than monitoring it.
  (b) extend check G to read the reflection list as a fourth representation.
      Cheaper, and it makes the copy permanent by watching it.

(a) is the lane's thesis -- *"moves one more stored fact to a measured one"*.
(b) is what this lane spent v7 arguing against building for `CONTRACT_COV`.

## What v8 produced

- **Phase 0.5 cleared with content, not backfill.** The last uncovered file got
  an authored `@dottalk.file` banner (`owns:` naming the `__fldtmp`/`__fldbak`
  convention, `lane: AIF-133` read from the introducing commit). 1023/1079
  banners carry zero authored fields; a 1080th empty one would have raised a
  number that measures nothing.
- **Phase 1's default input was two months stale.** The crosswalk defaults to
  `DOCFLUSH-20260716-001`'s `_v1` inventory while the inventory step now emits
  `_v2`. Bound to today's: REVIEW 139 -> 84, ALIGNED 168 -> 215. **55 review rows
  were an artifact of the default.** The disposition recommender then took 84 to
  14 needing a human, and those 14 are the already-open rulings arriving from the
  catalog side.
- **The half-run store is closed.** LEGACY was 63h45m ahead of the store; both
  halves now share a three-minute window. Topics 473 -> 666, line rows
  10846 -> 29700.
- **E5 caught and cleared.** The pre-check found the stale harvest carried MORE
  `HELP_HELP_TOPIC` rows than the source (670 vs 666), so a growth-only heuristic
  would have missed it.
- **Gates 5 and 6 produced candidates only**, `boundary_fail_rows=0`, with the
  one manualgen FAIL being `PYTHON_312` -- the interpreter self-check, not a
  content finding.

## What v8 got wrong

1. **"Phases 1-6 never ran" as a criticism of v7.** Stated twice. Corrected by
   the owner: those gates are scoped to what the RUN changed, v7 changed no
   source of its own, so not running them was correct. Scoring a run against a
   checklist instead of against its own scope.
2. **"Phase 4 will collect it into SRCFILE."** Wrong, and corrected in the Gate
   0.5 record after the rebuild left `SRCFILE_DRIFT/UNCOLLECTED` at 60.
   `SRCFILE.dbf` is under `data/comments/` and is written by the comments
   reharvest; `CMDHELP BUILD` writes `data/help/` and never touches it. Two
   tables both derived from source, both called "collected", one rebuilt in front
   of me.
3. **"The website's measures were derived from the stale canonical harvest."**
   Wrong -- an inference presented as a measurement, in the Phase 8 entry check,
   and corrected there. The 2026-08-26 store also read 670 topics, so matching
   numbers established nothing. The measured finding is different and larger:
   `documentation-progress-v1.json` has no generator anywhere in the producer
   tree, and its values carry three separate vintages at once.
   **All three of these have one shape** -- reading a coincidence of numbers as a
   causal link between two artifacts, without checking what writes either. That
   is the failure `CLAUDE.md` names in its corollary, hit three times in one run.

## The gap this run leaves

**Phase 2 was authored and never captured.** The `.dts` is in place with 26
targeted topics derived from the contracts that changed since the store was
built, plus the five dead multiword keys. The owner ran Phase 4 directly, so no
pre-refresh transcript exists and the before/after comparison cannot be made for
this run. The aggregate counts survive; the per-topic arm does not. Recorded
rather than glossed: this run cannot say which of the 26 were stale and which
were already current.

## Owed, and to whom

    E7        confirm a dated HELP backup exists for the 2026-09-01 17:03 build,
              or record that this refresh has no rollback target.
    owner     the SET-ladder fourth copy: derive (a) or check (b).
    owner     AIF-134's five-key ruling. Phase 1's review queue reaches the same
              three ERROR rows independently.
    owner     V6_HINTS sec 4 -- FILE / UDATE / UDATETIME / UTIME / UNOW. All five
              appear in this run's Function Inventory. `cmdhelp.cpp` was changed
              on 2026-09-01 to delegate `is_expression_function_name()` to the
              function catalog -- candidate (b) of three, shipped without the
              ruling, and now in the exe. Needs the ruling retroactively or a
              revert.
    AIF-129   pick one exemption spelling; `layer: helper` and
              `status: implementation-helper` remain disjoint with zero overlap.
    v9        SYSCMD reports 212 (table) / 203 (CSV mirror) / 218 (metacollect
              candidate). One number, three artifacts, none agreeing.
    v9        the crosswalk default: point it at the current inventory, or give
              the inventory step a `--run-id` so it stops writing into July.
    codex     `current_fullstack_doc_push.yaml` -- still says FAILED where v6's
              closeout says POSTPONED. Carried from v7, not edited here.

## Boundary held

No metadata import. No manualgen acceptance. No website write. No DBF, CDX or
LMDB mutation by this run. One source file changed --
`include/dottalk/scratch_sidecar.hpp`, a documentation banner, named in the Gate
0.5 record. Phase 4's HELP mutation was performed by the owner on the host, not
by this session.

Every commit from this run names explicit paths and stages neither `src/` nor
`include/` as a directory: the tree carries other sessions' in-flight work.
