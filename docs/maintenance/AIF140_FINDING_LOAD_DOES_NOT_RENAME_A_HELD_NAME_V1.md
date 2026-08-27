# AIF-140 -- LOAD DOES NOT RENAME A HELD NAME, AND USE DOES

    Number  : AIF-140, claimed 2026-08-27 with `session_coordinator.py
              claim-aif` (run COWORK-20260827-001). Claim file verified
              present at `coordination/aif/AIF-140.claim` before this
              number was cited anywhere.
    Found   : 2026-08-27, by running the six explicit-run carrier specs after
              R130 landed.
    Lane    : AIF-078 (multi-workspace). CAUSED BY R130, not revealed by it.
    Status  : review-needed. The author does not self-approve.
    Basis   : RUNTIME-PROVEN -- two transcripts, this session, on the R130
              build. SOURCE-EVIDENCED for the mechanism, lines cited.
    Family  : AIF-137. Fourth instance of "a name resolved without asking
              which one".

## 1. WHAT WAS MEASURED

**`WORKSPACE_LOADSHORT`'s `L_T3` READS GREEN AND IS READING THE WRONG TABLE.**

The arm addresses by NAME -- `SELECT TEACHERS` -- and the ledger fired on the
line before it:

    NAME: 'TEACHERS' is open in 2 areas (ws 3 area 10, ws 3 area 22);
    resolved to area 10 [REL refresh parent].

Area 10 is the **x64** TEACHERS the spec opened as its healthy session. Area 22
is the **partially-restored** TEACHERS the arm exists to assert. First-wins took
area 10. The arm passed because both files descend from the same bytes, so the
field compares equal.

**`CASCADE_ENV` IS GREEN OVER A DIFFERENT ARRANGEMENT THAN IT WAS WRITTEN FOR.**
It opened two tables with `USE`, then loaded a 43-area posture, and printed:

    WORKSPACE LOAD: 43 table(s) landed at an engine slot other than the number
    recorded in the posture.

It ended with **45 areas open instead of 43**, `CASCADE_ITEMS` and
`CASCADE_SALES_ORDERS` each open twice, and the ledger fired **five times** --
`REL add child`, `REL add parent` twice, `REL refresh parent` twice. All nine
arms read `.T.`. The green is real. It is not the same green.

**SEVEN LEDGER HITS ACROSS THE SESSION, AND NO SPEC CAN READ ONE.** That is
AIF-139: `ambiguity_count()` has no DTS-visible reader, so the instrument
announces to a person and is invisible to the suite. A run nobody reads by eye
would have shown fifteen green specs and nothing else.

## 2. THE MECHANISM, AND THE ASYMMETRY IS THE POINT

**`USE` HAS A THREE-ARM ALIAS POLICY** (`cmd_use.cpp:890-928`), written under
the USE_AGAIN lane on 2026-08-12, resolved BEFORE the target area is touched:

    explicit alias, already held  ->  REFUSE, open nothing
    derived from stem, held       ->  derive_distinct_alias() + ANNOUNCE
    free                          ->  take it

Its own comment states the defect it was built to close: *"Before this arm both
instances answered to one name and find_open_area_by_name_ci() returned the
lower slot to SET RELATION and every other name-based verb, with no diagnostic:
the second instance was open but unreachable by name."*

**`WORKSPACE LOAD` HAS NONE OF IT.** `cmd_workspace.cpp:2523`:

    setLogicalNameIf(A, alias, 0);

which resolves to a bare `a.setLogicalName(s)` (`:613`). No uniqueness probe,
no refusal, no rename, no announcement.

**WHY IT COULD NOT FIRE BEFORE, AND THIS IS WHY R130 OWNS IT.** The old loader
ran `workspace_close_all()` first, so at the moment it assigned a name the
session was empty and no collision was reachable. R130 removed that close --
correctly, and for reasons that stand -- and made the collision ORDINARY.
**This defect did not pre-exist R130 in a reachable form. R130 created it.**

## 3. WHAT IS ALREADY KNOWN ABOUT THE OTHER VERBS, AND WHAT IS NOT

- **`CREATE` does not auto-rename either.** Measured 2026-08-27 during the
  AIF-137 fixture phase and recorded in the RELWSNAME registration: the ledger
  fired `ws 1 area 0, ws 1 area 2` -- both in DEFAULT -- because CREATE opens a
  second same-named table with no rename, unlike USE.
- **`WORKSPACE OPEN` is UNMEASURED on this point** and is NOT claimed here
  either way. It is additive since R128 and takes its names from file stems, so
  it is the obvious next place to look; nobody has looked.

**So the shape is not "LOAD is broken". It is that ONE verb has the policy and
the others do not** -- and the policy lives inside `cmd_use.cpp` rather than
anywhere a second caller could reach it.

## 4. WHAT THIS BREAKS THAT WAS PREVIOUSLY SOUND ADVICE

R130's closeout told spec authors that a LOAD followed by a slot address is now
order-dependent, and offered addressing by NAME as the robust alternative.
**`WORKSPACE_LOADSHORT` had ALREADY made exactly that move** -- its header at
`:89` reads *"sits at a different slot in each. The first draft of this spec
used ordinals and produced two reds that were the SPEC's fault, not the
engine's."*

**And the name form is what failed.** After an additive LOAD, neither form is
safe unassisted: ordinals move, and names collide. That is worth stating plainly
because the obvious repair -- "address by name" -- is the one that produced this
false green.

## 5. WHAT IS NOT RULED, AND IT IS A RULING RATHER THAN AN IMPLEMENTATION CHOICE

**Should LOAD REFUSE the collision, or RENAME it?** USE answers differently
depending on where the name came from, and a posture's `alias=` field has a
claim on BOTH readings:

- **REFUSE**, like USE's explicit-alias arm: the posture NAMES its tables, the
  author typed those names, and silently renaming a name someone typed defeats
  the reason they typed it. A refusal is also the only answer that cannot
  produce a working session whose names mean something other than what the
  posture says.
- **RENAME AND ANNOUNCE**, like USE's derived arm: a posture is replayed rather
  than typed, a load that refuses on one collision restores nothing, and R130's
  whole direction is that a load ADDS to a session rather than dictating it.

**Not decided here.** Recording both arguments rather than picking, because the
last two times this project picked before measuring it picked wrong and said so
afterwards (R129 secs 6.1 and 6.2, both WITHDRAWN after the transcript).

**Also not ruled:** whether the alias policy should MOVE out of `cmd_use.cpp` so
LOAD, CREATE and OPEN share one implementation. That is the shape of the
AIF-137 fix -- one primitive, one filter -- and it is the same argument, but it
is a refactor with its own blast radius and is not smuggled in here.

## 6. NO ARM COVERS THIS, AND THAT IS DELIBERATE FOR NOW

No spec asserts anything about the ambiguity ledger (AIF-139), and no marker in
this language can read console text (the IDXDIFF precedent). An arm for this
finding must therefore be a FIELD read that separates two same-named tables --
which is exactly the shape `relation_parent_workspace_crossing.dts` already
uses, with two fixtures carrying different labels. That spec is prior art for
the fixture, not for the defect.

**`L_T3` IS THE HONEST ARM TO FIX FIRST**, and it is not fixed here: it should
assert the RESTORED table specifically, which today it cannot name.

**GOOD NEIGHBOR**

- **What changed:** nothing in the tree. This is a finding document.
- **Whose area:** AIF-078, and it touches `src/cli/cmd_workspace.cpp` and
  `src/cli/cmd_use.cpp` if and when it is ruled. Neither is modified.
- **What authorization:** found while running the six explicit-run carrier
  specs the R130 closeout named as its own limit; the owner asked for the
  number to be claimed and the finding written, with no code.
- **How to verify:** run `REGRESSION RUN WORKSPACE_LOADSHORT` and read the
  transcript for `NAME: 'TEACHERS' is open in 2 areas`. The arm above it is
  green while that line is printed; that pair is the whole finding.
- **How to undo:** delete this file.
