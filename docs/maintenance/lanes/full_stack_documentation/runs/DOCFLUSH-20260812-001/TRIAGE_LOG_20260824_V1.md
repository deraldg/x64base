# Flush v5 -- triage log, pass of 2026-08-24/25

    Run    : COWORK-20260824-001 (member.ai.claude.cowork), for member.derald
    Rule   : steward instruction, 2026-08-25 -- "do the best triage you can to
             keep going ... each time we run the pass we harden the system so
             record your steps, don't let a couple of files stop you on a
             development run."
    Status : **review-needed.** Nothing here was committed, promoted, or
             published. Every item is read-only unless it says otherwise.

The point of this file is that the NEXT pass starts from what this one learned,
and that a blocked item costs one line instead of a session.

---

## 1. What was blocking, and what it cost after triage

| blocker | old cost | triaged to | new cost |
|---|---|---|---|
| Gate 4 store not reproducible from HEAD (`cmdhelp.cpp` uncommitted, another session's) | stop the gate | record the binding: `runtime-proven against worktree c39d966c+dirty`, re-bind later | one line, no re-run if the blob is unchanged |
| assertion 6 topic floor fails on a correct repair | stop the gate | build the replacement instead of waiting for the ruling | tool exists, ruling can land whenever |
| finding 2 (edref titles) "needs a direct HELP_TOPIC read" | carried three passes | read the DBF | **settled, 29/29, in one command** |
| `FN_COVERAGE` "still unverified by a run" | carried three passes | it is a metacollect check, not a dotscript verb -- read the output the steward already produced | **settled, see s4** |
| website matrix gate | steward asked to regroup | left paused, correctly | unchanged |

**Two of the five had already been answerable for three passes.** Both were
carried as "blocked" when they were merely un-attempted. That is the failure
mode this log exists to break.

## 2. What each step hardened

    STEP                                       LEFT BEHIND
    read HELP_TOPIC.TITLE directly             finding 2 settled, MEASURED
    diffed topic SETS instead of counts        assertion 6's replacement
    cross-read HELP_LINE against HELP_TOPIC    AIF-126
    walked six backup stores                   proof AIF-126 is frozen, not drift
    read metacompare.csv                       FILE warn closed, 2 aliases named
    wrote tools/coordination/help_store_check.py  all of the above, one command,
                                               no engine, no build, runs anywhere

The last row is the one that matters. Everything above it was a hand
measurement tonight; from now on it is `help_store_check.py`.

## 3. AIF-126 -- the finding this pass produced

`SHARED_MSG` is 2,637 HELP_LINE rows with a **blank `TOPICKEY`**, every one.
With `MINER:SOURCE`'s 120 that is **2,757 unreachable lines, 9.4% of the
store**, frozen at exactly 139 headers across six stores since 2026-08-05.

The store has been printing `SHARED_MSG [lines=2637, topics=0]` in every
capture this lane has taken. Three of my own records quote the table it sits in.

Full record: `help_refresh/AIF126_FINDING_SHARED_MSG_HAS_NO_KEY.md`.

## 4. `FN_COVERAGE` -- closed, and my owed item was wrong

I had this on the owed list as "add `FN_COVERAGE` to the capture script."
**`FN_COVERAGE` is not a dotscript verb.** It is a metacollect check. Adding it
to `fullstack_post_refresh_runtime_v1.dts` would have produced a line that does
nothing and a green tick for a test that never ran -- a fourth unsound
assertion, of the same family as the three already withdrawn.

The output existed. `tmp/metacompare.csv`, written 2026-08-24 22:21 by the
steward's own metacollect run, 192 issues:

    WARN  METADATA_ONLY  command    187
    WARN  SOURCE_ONLY    command      3
    WARN  METADATA_ONLY  function     2

**`FILE` is not among them. The 75/74 warn is gone.** The `dt_meta` link repair
(`d99f4ed9c`) and the `FN_FILE` row (`b9d267df8`) both took.

The two remaining function warns are `STRCAT` and `TRIM`, and neither is a
coverage gap:

    function_catalog.cpp:355  CONCAT, alias { "STRCAT" }
    function_catalog.cpp:160  RTRIM,  alias { "TRIM" }

Both functions exist and work. `SYSFUNC.dbf` carries the aliases as rows of
their own; the source extractor emits canonical names only, so the comparator
sees a metadata row with no source. **An alias/canonical mismatch reported as
missing coverage.** Ruling owed: emit aliases, or teach the comparator that an
alias satisfies the row. Not urgent, and it should stop being counted as a
coverage defect either way.

The 187 `METADATA_ONLY` command warns are the same shape at a larger scale --
`command_catalog.cpp` is not the whole registry -- and are consistent with the
AIF-125 drift measurement (candidate 228 vs live 212, zero live-only rows).
Not triaged further this pass. **Named, not silently dropped.**

## 5. Gate 4, capture v2 -- where it landed

Assertions 2 (status half), 3, 4, 5a, 7, 8 PASS. 1 and 5b were withdrawn
2026-08-21. 6 fails its literal floor and the floor is unsound.

Two results worth carrying forward:

- **`HELP APPGUI` resolves.** Finding 10a closed. `859ef4548` put APPGUI and
  its GUI alias in dotref.
- **The topic count fell 530 -> 526 because a fix landed.** Five expression
  functions (`FILE UDATE UDATETIME UNOW UTIME`) stopped being invented as
  commands when the concurrent session made `is_expression_function_name()`
  delegate to `function_catalog`. The floor scored that repair as a regression.

Full record: `help_refresh/GATE4_REVALIDATION_V2_20260824.md`.

## 6. The freshness instrument existed all along

    dottalk++ v0.6 (2026-08-24, c39d966c dirty)  (Aug 24 2026 17:05:41)

Commit AND dirty flag, in the banner, in every transcript this lane has ever
captured. Assertion 1 was withdrawn on 2026-08-21 for lacking exactly this, and
the replacement chosen then (`DOTHELP` renders SMTP) is a content test standing
in for a provenance test. **Proposed assertion 1', for the steward:** the banner
names a commit, and it is not `dirty`. It is the only assertion in the set that
can catch the 2026-08-12 failure -- a store built by the wrong exe -- and it
costs one `grep`.

Note this pass would have FAILED assertion 1'. That is the correct answer and it
is why the assertion is worth having.

## 7. Carried to the next pass

1. Steward ruling: assertion 1' (banner, not dirty) and assertion 6' (topic-set
   diff, not a count floor). Both instruments are built; only the ruling is
   owed.
2. Re-bind Gate 4 when the concurrent session commits `src/cli/cmdhelp.cpp`.
3. AIF-126: read `helpdata_export_dbf.cpp` and name the writer that leaves
   `TOPICKEY` blank. Then rule on the 139 headers.
4. `CMDHELPCHK` should fail on a blank `TOPICKEY`, and `topics=0` in a
   `CMDHELP SOURCE` bucket should be an error line, not a number.
5. Alias/canonical ruling for `STRCAT` and `TRIM` (s4).
6. The 187 `METADATA_ONLY` command warns (s4).
7. The website matrix closing gate. **Still paused at steward request.**

## 8. Rule this pass adds

**An item is "blocked" only when someone has tried it and been stopped.** Two of
tonight's five had never been attempted. Before carrying a blocker forward,
write down the one command that would settle it. If that command can be written,
the item is not blocked -- it is queued, and it goes in this pass.

---

## Good Neighbor note

    WHAT CHANGED   : four new files, all documentation or tooling --
                     TRIAGE_LOG_20260824_V1.md (this file),
                     help_refresh/GATE4_REVALIDATION_V2_20260824.md,
                     help_refresh/AIF126_FINDING_SHARED_MSG_HAS_NO_KEY.md,
                     coordination/aif/AIF-126.claim,
                     tools/coordination/help_store_check.py.
                     No source, no data, no store, no rebuild, no git mutation.
    WHOSE AREA     : lane full_stack_documentation, owner member.derald.
                     src/cli/cmdhelp.cpp, src/cli/expr/function_catalog.cpp and
                     dottalkpp/data/help/* were READ ONLY -- two of them belong
                     to a CONCURRENT session and nothing was written to either.
    AUTHORIZATION  : the standing "Full-Stack SelfDoc push v5" request plus the
                     steward's 2026-08-25 instruction to triage and keep going.
                     AIF-126 allocated by tools/coordination/next_aif.py.
    VERIFY OR UNDO : $py12 tools\coordination\help_store_check.py --against
                       dottalkpp\data\help.bak-20260821-101225
                     reproduces sections 3 and 5 from the tables in one command.
                     Undo is deleting the five files named above.
