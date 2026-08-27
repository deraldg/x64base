# AIF-139 -- R112's MIGRATION GATE IS A COUNTER NOTHING CAN READ

    AIF     : AIF-139, claimed 2026-08-27 with
              `session_coordinator.py claim-aif` (atomic O_EXCL, no
              number passed). Claim file verified present.
    Found   : 2026-08-27 by member.ai.claude.cowork, in two halves --
              the first by reading the instrument while designing an
              arm for AIF-137, the second by RUNNING that arm and
              watching the ledger fire where it was documented as
              unreachable.
    Lane    : AIF-120 (name resolution) / R112. Adjacent to AIF-137,
              which used the same instrument and is a different defect.
    Status  : review-needed. The author does not self-approve.
    Evidence: sec 2 MEASURED in source, lines cited. sec 3
              RUNTIME-PROVEN 2026-08-27 and names what it ran against.

## 1. THE FINDING IN TWO SENTENCES

**R112 sec 6a admits first-wins-plus-warning ONLY as an instrumented migration
phase "whose counter has to reach a measured zero" -- and nothing in the tree
can read that counter.** The one spec that calls itself the tripwire for it
asserts nothing, and a comment claims the counter is assertable when no reader
exists.

## 2. THE GATE, AND WHY NOTHING CAN PASS IT

**The rule** (`src/cli/workarea_util.hpp:41-52`):

    R112 sec 6a ruled that first-wins-plus-warning is admissible only as an
    INSTRUMENTED migration phase whose counter has to reach a measured zero
    -- so this records, and does not merely print.

The recording half is real. `record_ambiguity()` (`workarea_util.cpp:102`)
latches one entry per (name, site) and carries `ws_handles` beside
`engine_slots`. `WORKSPACE REGISTRY` prints it (`cmd_workspace.cpp:4740-4757`)
even at zero, deliberately, so that "no collision occurred" and "nothing is
instrumented" cannot look alike.

**MEASURED: `ambiguity_count()` has exactly three consumers in the tree** --
`workarea_util.cpp` which defines it, `workarea_util.hpp` which declares it,
and `cmd_workspace.cpp` which PRINTS it. **There is no DTS-visible reader.**
No `.dts` spec can assert the count, so the gate's own condition is not
expressible in the language the suite is written in.

### 2.1 The spec that calls itself the tripwire asserts nothing

`dottalkpp/data/scripts/rel_name_ambiguity_regression.dts`:

    * MUST print `name ambiguity : 0 resolution(s)`. ... this line is the
    * tripwire for [AIF-078 stage 4].
    FORMULA "NAME-AMBIGUITY-LEDGER-BEGIN"
    WORKSPACE REGISTRY
    FORMULA "NAME-AMBIGUITY-LEDGER-END"

`WORKSPACE REGISTRY` between two markers, for a human to read. **"MUST print"
with nothing checking is a non-assertion wearing assertion clothes** -- the
FIELDMGR_APPEND doctrine's failure mode, in the arm that exists to catch it.

### 2.2 And a comment says the opposite

`cmd_workspace.cpp:4736` states the count is

    a FIELD of the registry, assertable by a spec

It is not. **That sentence is what convinced the author of this finding, in
writing, before he checked** -- it was repeated to the owner as fact and had to
be retracted. A false affirmation is worse than silence: a reader who checks
finds the claim and stops.

### 2.3 The consequence, and it is not hypothetical

**The tripwire fired on 2026-08-27 and no spec in the suite would have caught
it.** AIF-137 -- a relation refresh resolving its parent into another
workspace -- was found by a person typing four commands and reading console
output. The ledger had been armed by R128 for one day. Had nobody looked, the
count would have kept rising with nothing reporting it.

## 3. THE SECOND HALF: THE LEDGER IS NOT STRUCTURALLY ZERO, AND HAS NOT BEEN

**RUNTIME-PROVEN 2026-08-27**, in the fixture phase of
`relation_parent_workspace_crossing.dts`, on the binary reporting
`v0.6 (2026-08-27, 5d09988b)`:

    NAME: 'RPCP' is open in 2 areas (ws 1 area 0, ws 1 area 2); resolved to
          area 0 [REL refresh parent].

**`ws 1` twice.** Both areas in DEFAULT. No second workspace existed yet.

**Cause: `CREATE` opens a second same-named table with NO auto-rename.** `USE`
renames a duplicate stem to `<stem>2` and announces it (`cmd_use.cpp:944-972`),
which is the mechanism the "structurally zero" claim rests on. `CREATE` does
not.

**So this claim, recorded in `cmd_regression.cpp:465`, is FALSE:**

    the ambiguity ledger is STRUCTURALLY ZERO -- not untested, unreachable --
    until two workspaces can be open at once and cross-workspace names may
    repeat

It has been reachable inside ONE workspace, by `CREATE`, since long before
R128. R112 sec 6a predicted the zero would "record zero for the wrong reason";
the instrument built under that ruling then recorded zero for a THIRD reason
nobody had named -- not prevention, and not unreachability, but **a path that
was reachable and simply never walked while anybody was reading.**

## 4. THE COUNTER IS ALSO A FLOOR

**MEASURED.** `cmd_select.cpp` resolves `SELECT <name>` by scanning work areas
and calling `eng->selectArea()` at `:200`. It does NOT call
`find_open_area_by_name_ci()`, so it records nothing.

Observed 2026-08-27: `SELECT students` crossed a workspace boundary -- area 8
in workspace 2 while the current handle was 3 -- and the ledger entry that
appeared was tagged `REL refresh parent`, not a select site. **It existed only
because the refresh that followed happened to resolve the same name.** On a
name the refresh did not touch, the crossing would have been silent.

**A counter blind to one of its own crossing paths cannot retire anything, and
its zero would mean "not instrumented" while looking like "clean".**

## 5. WHAT AIF-137'S FIX CHANGED HERE, AND WHAT IT DID NOT

AIF-137 scoped eleven relation-path resolutions to the current workspace
(`6d05e181d`). **The cross-workspace hits stopped being recorded, because they
stopped happening** -- that is the fix working, not the instrument being
silenced.

**The in-workspace hits still print, deliberately.** The scoped resolver still
calls `record_ambiguity()` when more than one candidate survives the workspace
filter, which is exactly the `CREATE` case in sec 3. **That residue is what
R112 sec 6a's measured zero is actually about**, and it is now the only thing
the ledger counts on the relation path.

**None of that makes the counter readable.** Sections 2 and 4 stand unchanged.

## 6. WHAT IS NOT RULED

- **What the target actually is.** The external reviewer's Q4 answer
  (`ANSWERS_TO_CLAUDE_2026-08-27.md`, member.derald + xAI Grok): *"Duplicate
  names across workspaces stay legal. Count UNSCOPED SUCCESSES down to zero.
  Instrument SELECT before anyone treats the R112 number as a measurement."*
  That reframes the counter from "ambiguous resolutions" to "resolutions that
  succeeded without a scope", which is a different number and needs a ruling.
- **Whether the reader is a DTS function, a catalog field, or a marker-visible
  predicate.** `RECNO()` and `FOUND()` already render EMPTY in a `?` marker
  (USE_AGAIN), so a naive function would repeat that trap.
- **Whether `CREATE` should auto-rename like `USE` does.** Making it match
  would drive the in-workspace residue to zero by prevention rather than by
  measurement -- which is what R112 sec 6a warned about, and might be right
  anyway. Not this finding's call.

## 7. WHAT THIS DOES NOT CLAIM

- **Not claimed: that the ledger is wrong.** Everything it records is correct.
  It cannot be READ by a spec, which is a different failure.
- **Not claimed: that anyone was misled in production.** The one measured
  consequence is AIF-137 going unnoticed for a day.
- **Not claimed: that AIF-137's fix depends on this.** It does not. They share
  an instrument and are separate defects.

## 8. NO CODE WAS WRITTEN

Nothing was changed for this finding. `cmd_workspace.cpp:4736`'s false
sentence and `cmd_regression.cpp:465`'s false claim are both still in the tree,
named here and not corrected, because correcting a comment inside a commit that
does not otherwise touch its file is how a change set stops being reviewable.

**GOOD NEIGHBOR**

- **What changed:** this document and the AIF-139 claim file.
- **Whose area:** AIF-120 / R112. A fix would touch `src/cli/workarea_util.*`,
  `src/cli/cmd_select.cpp`, `src/cli/cmd_workspace.cpp` and the DTS evaluator.
- **What authorization:** the owner authorized the claim on 2026-08-27. No fix
  is authorized and none is designed.
- **How to verify:** grep `ambiguity_count` -- three consumers, none in a
  spec. For sec 3, run `relation_parent_workspace_crossing.dts` and read the
  fixture phase; the two `ws 1` lines print on every run.
- **How to undo:** delete this file and release AIF-139.
