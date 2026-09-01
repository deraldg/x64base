# DOCFLUSH-20260901-001 -- E8, the mutation inventory

    run       : DOCFLUSH-20260901-001 (v7)
    baseline  : 2d26612b9  (2026-09-01)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    posture   : REPORT-ONLY. Nothing below has been done or is authorized by
                this document. This is the list to authorize FROM.

v6 recorded E8 as **NOT SOUGHT**. The cookbook requires "owner authorization for
each distinct mutation", and a mutation nobody enumerated cannot be authorized
one at a time -- it gets a blanket yes, which is how a run mutates something it
did not intend to. This file exists so the yes can be per-item.

Nothing here is a recommendation. Several of these should probably NOT happen in
v7 at all; that is noted per row.

---

## M1 -- HELP DATA rebuild  (`CMDHELP BUILD LEGACY`, then `CMDHELP BUILD . <src>`)

    writes    : dottalkpp/data/help/  -- 10 .dbf tables plus memo sidecars,
                54 MB total on disk (measured, not the .dbf sum)
                COMMANDS, CMD_ARGS, HELP_ARTIFACTS, HELP_LINE, HELP_SECTION,
                HELP_TOPIC + 4 *_LOCALE tables
    reversible: YES, from a backup taken first -- see M2
    host only : YES. Requires the engine.
    blocked by: the DotTalkBBSD daemon holds the store. It must be stopped with
                an ELEVATED `Get-Process dottalk_bbsd | Stop-Process -Force`;
                `Stop-ScheduledTask` alone returns success and leaves it running
                (CLAUDE.md, measured 2026-08-21).
    order     : LEGACY FIRST. foxref feeds the legacy builder, and a dotref
                change requires it.

**Is it needed in v7?** Only if source contracts changed. **v7 has changed no
source of its own**, so if it closes without a source edit, **M1 is not needed and
should not be run.** E2 (CMDHELPCHK) can be proven against the existing store.

**CORRECTION, and it is a hazard rather than a detail.** The first draft of this
row said "at this baseline v7 has changed NO source", full stop. That was true of
v7 and false of the TREE. Measured: `src/cli/record_view.cpp` and
`src/memo/x64_memo_store.cpp` are modified and uncommitted, and neither is v7's
-- both last committed `3706da78c` (2026-07-25) and untouched by this run. Three
sessions show `status: active` in `coordination/active_sessions/`.

So: **v7 must not stage src/ or include/ at all**, and any commit it makes must
name explicit paths. A `git add src` here would fuse another session's in-flight
work, which is precisely what the never-`git add -A` rule exists to prevent. A
"the tree is clean" reading of a status filtered to one's own files is the same
error in a smaller frame.

## M2 -- HELP store backup  (prerequisite for M1, not a mutation of record)

    writes    : dottalkpp/data/help.bak-<stamp>/   (a new directory)
    reversible: n/a -- it only creates
    note      : v6's `help.bak-20260825-180609` exists and does NOT cover a build
                v7 performs. **TWELVE backup directories already exist** and
                nothing rotates them; at 54 MB each that is a standing disk cost
                nobody owns. If v7 runs M1, take a fresh one and name the rollback
                in the Gate 3 record -- and note the rotation gap for v8.

## M3 -- metadata candidates  (`metacollect`)

    writes    : candidate CSVs only, gitignored, SHA-bound in the Gate 5 record
    reversible: YES -- they are candidates; nothing is imported
    build     : requires -DDOTTALK_BUILD_METACOLLECT=ON
    NOT this  : importing candidates into live metadata is a SEPARATE gate and a
                separate authorization. v7 does not request it.

## M4 -- manualgen candidate  (`manualgen.py` build-* chain)

    writes    : docs/manuals/developer/manualgen/generated/<run-id>/...
    reversible: YES -- candidate workspaces are additive
    NOT this  : `apply-controlled-acceptance` mutates the ACCEPTED manual and its
                pointer. That needs its own authorization bound to a plan-manifest
                hash and a mutation-ledger hash, and v7 does not request it.

## M5 -- website command catalog regeneration  (`command_catalog_sync.py emit`)

    writes    : D:\dev\x64base-site\content\docs\dottalk\command-catalog.mdx
    tree      : THE SITE REPO, not this one
    reversible: YES, by git in that repo
    **HOLD.** The site tree is on `codex/lean-sites-publish`, 198 commits ahead of
    site `main`, 1 unpushed, 2 untracked files. A generated page written into that
    branch lands in a tree whose relationship to `main` is unsettled. E6 was
    scoped out of v6; v7 should keep it out until the branch question is ruled.

## M6 -- source edits implied by Gate 0.5

    M6a  include/dottalk/scratch_sidecar.hpp -- add the missing @dottalk.file
         banner. ONE header. Closes the E3 arithmetic.
         CAVEAT: 94.8% of banners are empty backfill, so adding a 1080th empty
         banner raises a number that does not measure knowledge. Worth doing for
         consistency; not worth reporting as progress.
    M6b  TRANSACTION -- either a dotref entry or a deliberate absence. See
         V8_HINTS D1: the generator angle probably makes this moot.
    M6c  AIF-134's five dead multiword keys -- ROUTER or DELETE. Owner ruling
         still open. NOT v7 work unless separately instructed.

## M7 -- run records  (what v7 has actually written)

    writes    : docs/maintenance/lanes/full_stack_documentation/runs/
                DOCFLUSH-20260901-001/{GATE0_RUN_ENVELOPE, GATE0_5_CONTRACT_STATE,
                V8_HINTS, this file}
                + the cookbook Phase 0.5 edit (D3, owner-approved)
                + the AIF-134 charter correction
    reversible: YES, by git
    status    : DONE. These are documentation, they are what a run IS, and they
                are the only mutations v7 has performed.

---

## The shape of the request, if v7 proceeds

v7 has changed no source and no data OF ITS OWN (see the M1 correction: the tree
carries two modified source files belonging to another session). Everything above
except M7 is optional for this run. The honest position:

**v7 can close at Gate 7 having mutated nothing but its own records**, with E4
re-proven, E3 measured and understood, the contract-authority finding recorded,
D2 and D3 resolved, and V8_HINTS left for the next crossing. That is a complete,
useful pass and it is what the lane means by "drives the next span".

**What v7 CANNOT do from the sandbox**, and must not claim: E2 (CMDHELPCHK
reflection) requires the engine on the host. No sandbox result may be recorded as
E2 PASS.

**The one thing worth asking for**, if anything: M6a, the single missing banner,
because it is one line, closes an arithmetic gap, and carries no downstream
rebuild -- `@dottalk.file` is mined from source text, not compiled in.
