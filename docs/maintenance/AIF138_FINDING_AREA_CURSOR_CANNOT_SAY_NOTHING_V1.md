# AIF-138 -- THE AREA CURSOR CANNOT SAY "NOTHING SELECTED", AND SLOT 0 MEANS THREE THINGS

    AIF     : AIF-138, claimed 2026-08-27T11:33:46Z with
              `session_coordinator.py claim-aif` (atomic O_EXCL, no
              number passed -- the allocator chose). Claim file
              verified present after the tool reported success.
    Found   : 2026-08-27. Surfaced by the owner during R129 sec 6.1a,
              in two words, after the author had answered the question
              wrongly twice.
    Lane    : engine. NOT a multi-workspace defect -- AIF-078 made it
              REACHABLE, it did not cause it. Predates that work.
    Status  : review-needed. The author does not self-approve.
    Evidence: MEASURED in source, lines cited. Partly corroborated by
              the 2026-08-27 transcript recorded in AIF-137 sec 2.
              The no-engine arm (sec 2.3) is NOT runtime-proven.
    Severity: ON THE PATH, not latent. R129 sec 6.1 was RULED on
              2026-08-27: the owner made the empty workspace legal and
              called it the place you start from when building one up.
              "Nothing selected" is now a position a user is INVITED
              to occupy, and the engine has no value for it. This is
              the work that ruling depends on.

## 1. THE FINDING IN ONE SENTENCE

**`Engine::_current` has no value meaning "nothing selected", so absence is
spelled `0` -- which is also a real work area, also the startup position, and
also what the accessor returns when there is no engine at all.**

## 2. SLOT 0 MEANS THREE THINGS

### 2.1 A real, addressable work area

Area 0 is an ordinary slot. In the 2026-08-27 multi-workspace run it is where
`WSX64`'s BUILDING opened, and it is what the R112 ambiguity ledger reported
choosing: `resolved to area 0`. RUNTIME-OBSERVED; the transcript is in
`AIF137_FINDING_RELATION_PARENT_IS_WORKSPACE_BLIND_V1.md` sec 2.

### 2.2 The startup position, by decision

`src/cli/shell.cpp:528`:

    XBaseEngine eng;
    eng.selectArea(0);

A fresh session is PARKED on slot 0 deliberately. So "the cursor is on 0" does
not distinguish "the user selected area 0" from "nothing has happened yet".

### 2.3 No engine at all

`src/cli/workareas.hpp:120`:

    std::size_t current_slot() const {
        rebind_if_needed();
        auto* eng = shell_engine();
        if (!eng) return 0;
        return static_cast<std::size_t>(eng->currentArea());
    }

**A missing engine and a cursor legitimately on slot 0 return the same
number.** MEASURED. This is the AIF-118 shape -- a guard returning the same
answer for absent and for fine -- and it is in the accessor that
`infer_parent_from_workarea()` (`set_relations.cpp:159`) calls, which is the
entry to the AIF-137 path.

NOT RUNTIME-PROVEN: no session was run without an engine. The line is read,
not exercised.

## 3. WHY THIS IS R6 AND NOT A STYLE COMPLAINT

R6: **absent must not be representable among present.**

`Engine::_current` is a plain `int` (`include/xbase.hpp:623`) and
`selectArea()` (`:615`) accepts only `0 <= idx < MAX_AREA` before assigning.
Every value it can hold is the address of a present thing. "Nothing selected"
is absent. It therefore has no representation, and the codebase spells it with
a present value.

The consequence is not hypothetical: it is why sec 2.3 can exist at all. A
function with no way to say "I have nothing" returns the lowest legal address
instead.

## 4. WHAT MAKES IT REACHABLE NOW

**R129 sec 6.1 was RULED on 2026-08-27.** An EMPTY workspace is a legal
position: `WORKSPACE NEW x` then `WORKSPACE SWITCH x` succeeds, with no
current table and the next OPEN joining it.

Two arguments were given and the owner's is the load-bearing one. The external
reviewer argued from the invariant -- **I1 forbids a NULL workspace, not an
EMPTY one.** The owner argued from use: *"there will be times we want to open
and add to it. You have to have a place to start."*

**That second reason is why this defect is not latent.** An empty workspace is
not a tolerated edge case to be survived; it is the **intended starting
state** for building a workspace up. The position is now on the ordinary path,
and the engine cannot express it.

An empty workspace has no lowest member, so there is nothing for the area
cursor to point at -- which is precisely the state the engine cannot express.
Before multi-workspace this state was rare and unnamed; R129 sec 6.1 makes it
ordinary and gives it a verb.

## 5. WHAT WAS TRIED AND REJECTED, RECORDED SO IT IS NOT RETRIED

**"Point `_current` at a closed slot the workspace will fill."** Rejected.
Parking the cursor at a closed slot means parking it at SOME slot, and which
slot depends on what OTHER workspaces happen to hold -- the cursor becomes a
function of unrelated state. Slot 0 collides with all three meanings in sec 2;
any higher free slot is arbitrary and unstable across sessions.

**"`wsHandle() == 0` on the current area is a sufficient signal."** Rejected,
and this one is worth the words because it was written into R129 before it was
caught. `DbArea::close()` sets `_ws_handle = 0` (`dbarea.cpp:123`), so a
closed area reads 0 -- but **so does an OPEN area whose membership stamp was
MISSED**, which is a registration defect `reconcile_unregistered_areas()`
(`cmd_workspace.cpp:1578`) exists to name and which `compute_save_scope`
already counts as `skipped_unregistered` (`:1963`). An invariant stated over
`wsHandle()` alone accepts the defect as a legal position. **That is the
AIF-118 shape inside an invariant written to prevent it.**

## 6. THE SHAPE OF A FIX, NOT RULED

A declared no-current value, and every reader of `currentArea()` becoming a
two-case read. The cost is real -- `selectArea()` rejects negatives today, and
the reader count is not measured here -- but the cost is the price of the
defect and is owed whether or not workspaces exist.

**NOT MEASURED and needed before any fix is scoped:** how many callers read
`currentArea()` / `current_slot()`, and how many would need the second case
rather than a safe default. **NOT RULED:** whether the no-current value is a
negative sentinel, an `optional`, or a separate `hasCurrent()` predicate.
Sec 2.3 wants its own answer either way -- "no engine" is a different absence
from "no current area", and collapsing them is how this got here.

## 7. WHAT THIS DOES NOT CLAIM

- **Not claimed: that any user has hit it.** The transcript in AIF-137 shows
  slot 0 behaving as a normal area, not as a confusion. Nothing observed a
  no-engine return.
- **Not claimed: that it caused AIF-137.** AIF-137's cause is separate --
  lowering a held `DbArea*` to a name and searching the process. This defect
  sits in the accessor on that path and would make a related failure harder to
  see, which is a different statement.
- **Not claimed: that `selectArea(0)` at startup is wrong.** Parking a fresh
  session somewhere is reasonable. The defect is that the parking spot and
  "nowhere" are the same value.

## 8. NO CODE WAS WRITTEN

`src/cli/**` and `src/xbase/**` are engine and want an explicit go. Nothing
was changed and nothing was built.

**GOOD NEIGHBOR**

- **What changed:** nothing in the tree except this document and the claim
  file the allocator wrote.
- **Whose area:** engine. `include/xbase.hpp`, `src/cli/workareas.hpp`,
  `src/cli/shell.cpp`, and every reader of `currentArea()`.
- **What authorization:** the owner authorized the AIF claim on 2026-08-27.
  No fix is authorized and none is designed.
- **How to verify:** read the three lines in sec 2. No build required.
- **How to undo:** delete this file and release the number with
  `session_coordinator.py release-aif`.
