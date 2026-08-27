# R130 -- A POSTURE RECORDS A KEY, NOT AN ADDRESS

    Number  : R130, allocated 2026-08-27 with `tools\coordination\next_r.py`
              (NEXT FREE R130; highest taken was R129). Recorded in
              `docs/ai-friendly/R_RULING_REGISTER_V1.md` before being cited.
    Ruled   : 2026-08-27 by member.derald.
              "regarding LOAD, no problem, we don't save slots, we
               allocated them as they are available, do we need a slot
               provider??"
              And on the brute close: "now we use workspace close as
               the brute solution -- everybody has database fun until
               they shutdown their app and all of the workspaces close
               at one time."
    Lane    : AIF-078 (multi-workspace). Completes R128, whose title
              says LOAD is additive while only the GUI's was.
    Status  : review-needed. The author does not self-approve.
    Basis   : source read 2026-08-27, lines cited. NOTHING HERE WAS RUN.
              No claim in this document is runtime-proven.

## 1. WHAT WAS RULED

**A posture's `AREA <n>` is a KEY, not an engine address.** On load, slots are
allocated as they are available; the recorded number identifies the entry
inside the posture and nothing else.

**And no new slot provider is needed.** The owner asked; the answer is that one
already exists and every other opener in the tree already uses it.

**THIS IS THE ITEM R129 PARKED BY NAME.** R129's NOT RULED list carries "the
CLI `LOAD` half of R128 (`schema_close_all()` at `:2405`)". That is this
document. The function has since been renamed `workspace_close_all()`
(commit `f60d2d70d`, owner: *"schema_close_all is a bad name"*), so a reader
following R129's citation is looking for a name that no longer exists -- said
here rather than left to be discovered.

## 2. WHY LOAD CLOSED EVERYTHING, AND WHY THAT WAS NOT THE DEFECT

**MEASURED.** `workspace_load_from_stream()` replays recorded slots:

    AREA 0 dbf=... index=...        ->  open_into_area(0, ...)
    AREA 1 dbf=... index=...        ->  open_into_area(1, ...)

`open_into_area(n, ...)` puts the table at engine slot `n` EXACTLY. So the
loader can only work if slot `n` is free, which is what
`workspace_close_all()` at `cmd_workspace.cpp:2405` guaranteed.

**THE CLOSE WAS NOT THE DEFECT. IT WAS THE ONLY GUARANTEE AVAILABLE TO A
LOADER THAT REPLAYS ADDRESSES.** The owner drew the distinction that makes
this readable: closing every workspace at once is CORRECT at shutdown --
"everybody has database fun until they shutdown their app and all of the
workspaces close at one time" -- and `workspace_close_all()` exists for
exactly that. The defect was LOAD borrowing shutdown's hammer as a
precondition.

**This is why LOAD is different from OPEN.** R128 made OPEN additive by
DELETING its close, because OPEN allocates. Deleting LOAD's close alone would
be worse than the defect: the loader would open into whatever occupies the
recorded slots, which is precisely where another workspace's areas live. The
same shape R128 recorded for `schema_open_directory`'s slot loop, one verb
over.

## 3. THE PROVIDER ALREADY EXISTS

**MEASURED.** `cli::find_free_area_for_current_workspace(bool& broke_contiguity)`
(`workarea_util.hpp:155`, defined `workarea_util.cpp:223`). It is
workspace-scoped, grows a workspace contiguously, and REPORTS when it cannot.

Its callers today:

    cmd_use.cpp:765         USE ... IN FREE
    cmd_workspace.cpp:1223  R128's additive OPEN

**LOAD is the only opener in the tree that does not use it.** Built at AIF-078
stage 1, hardened under R128, and already guarded: `USE_ARGS`'s `U_T4` arm
exists to catch it going workspace-blind again -- "if U_T4 ever reads 1 again,
IN FREE has gone back to workspace-blind."

**So the answer to the owner's question is no.** Nothing new is built. LOAD
stops replaying addresses and asks the allocator every other opener asks.

## 4. THE LOAD-BEARING HALF: THE KEY-TO-SLOT MAP

**The recorded numbers are not decoration. Three payload lines reference
them**, and all three are v3 session state:

    CURSOR <area> <recno>    cmd_workspace.cpp:2528  -> get_area_0based(n)
    CURRENT <area>           cmd_workspace.cpp:2539  -> applied at :2569
                                                        via select_engine_area(n)

**So the loader must carry a map from recorded key to allocated slot, built
during the AREA loop and consulted by the CURSOR and CURRENT handlers.**

**IF THE MAP IS OMITTED, THE DEFECT IS WORSE THAN THE ONE BEING FIXED.** With
LOAD allocating past an occupied range, a bare `CURSOR 8` reaches engine slot
8 -- which now belongs to whichever workspace was already there -- and MOVES
ITS CURSOR. That is AIF-137's shape as a WRITE rather than a read, on a user's
data, driven by a saved file. AIF-137 was found by an instrument; this would
have no instrument at all.

**The map is therefore not an implementation detail of this ruling. It is the
ruling's other half**, and the spec's discriminating arm exists to catch its
absence (sec 6).

## 5. WHAT THIS DISSOLVES

**R129 sec 6.2 needed a SLOT ARM before LOAD could be made additive, and now it
does not.** 6.2 as ruled governs NAME resolution; LOAD addresses by slot, and
R121's precedent (ADDRESSING IS ABSOLUTE, TRAVERSAL IS FILTERED) argues
`SELECT <n>` should reach slot `n` across any workspace. That left LOAD with no
refusal to catch a bad remap.

**Under this ruling LOAD never addresses a slot it did not just allocate**, so
it cannot reach a foreign workspace's cursor at all. The hazard stops existing
rather than needing a guard. **6.2's slot arm is still an open question for
`SELECT` itself; it is simply no longer a prerequisite for LOAD.**

## 6. WHAT IS BACKWARD COMPATIBLE, AND WHAT IS NOT

**NO FORMAT VERSION BUMP IS NEEDED, and that was not obvious.** A posture's
`AREA` numbers only have to be INTERNALLY CONSISTENT, not zero-based. Whatever
a save wrote, a load treats as keys -- so a posture saved from a workspace
holding engine slots 13..25 loads correctly, its numbers being labels.

**NOT CLAIMED: that an OLD loader reads a NEW posture identically.** Nothing
about the FILE changes under this ruling, so the question does not arise --
but it would arise the moment anyone proposed renumbering saves, and that is
named here so nobody does it thinking it is free.

## 7. WHAT IS NOT RULED

- **What LOAD does when the workspace already holds areas.** R128 ruled that a
  second OPEN of the same directory RE-ENTERS and adds only what is not there.
  Whether LOAD is re-entrant in the same sense, or always allocates fresh for
  every posture entry, is a separate question and is not answered here.
- **Whether `WORKSPACE LOAD <name> AS <ws>` should exist.** Under this ruling
  a plain LOAD is already additive, so a named destination is a convenience
  rather than a mechanism.
- **The allocator's contiguity report.** `find_free_area_for_current_workspace`
  sets `broke_contiguity`; what LOAD does with it -- announce, or ignore --
  is not ruled. USE announces.
- **R129 sec 6.2's slot arm**, per sec 5. Still open for `SELECT`.

## 8. HOW IT WILL BE PROVEN

**Spec first, watched to fail, then the fix** -- the order R128 and AIF-137
both used, and the order that caught a false green in each.

Three arms, and one of them is honest about being green today for the wrong
reason:

- **T1 -- the other workspace survived the LOAD.** Two workspaces populated,
  LOAD a posture into one, read a sentinel from the OTHER. **RED today**,
  because `workspace_close_all()` closed it.
- **T2 -- the loaded workspace's cursor was restored.** **GREEN TODAY FOR THE
  WRONG REASON** and stated as such: with the slot space emptied first, the
  recorded number and the allocated slot coincide by accident. It does not
  discriminate against today's build; it discriminates against a NEW
  implementation whose map is wrong.
- **T3 -- the other workspace's cursor was NOT moved.** **RED today** (that
  workspace is closed) **and RED under a missing map** (its cursor is driven by
  a stale `CURSOR <n>`). This is the arm sec 4 exists for.

## 9. THE GO WAS GIVEN; THE ORDER IS SPEC FIRST

`src/cli/**` is engine and wants an explicit go. **It was given on 2026-08-27**
-- *"yes and start addressing these corrections in code"* -- so implementation
follows in the same session.

**AT THE MOMENT THIS DOCUMENT WAS STAMPED, NOTHING HAD BEEN IMPLEMENTED AND
NOTHING HAD BEEN RUN.** Every line above is source read at HEAD `f60d2d70d`.
The spec goes in first and is watched to fail (sec 8); the implementation and
its runtime evidence land in the session closeout, not here. **Do not read a
later green back into this document** -- if the arms move, the closeout says
so and this record stays as written.

**GOOD NEIGHBOR**

- **What changed:** nothing in the tree at the time of writing; this is a
  ruling document. The implementation it authorizes is recorded separately.
- **Whose area:** AIF-078. Would touch `workspace_load_from_stream()` and the
  CURSOR/CURRENT handlers in `src/cli/cmd_workspace.cpp`, and nothing else --
  the allocator already exists and is not modified.
- **What authorization:** the owner ruled it on 2026-08-27 and asked for the
  code to follow.
- **How to verify or undo:** delete this file; nothing else exists yet.
