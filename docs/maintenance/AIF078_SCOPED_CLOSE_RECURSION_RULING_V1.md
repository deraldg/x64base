# AIF-078 Stage 3 -- Scoped Close and SET RECURSION

- **AIPR:** AIPR-20260822-COWORK-110
- **Lane:** application-ui-dsl
- **Author:** member.ai.claude.cowork (ALPHA)
- **Status:** review-needed
- **Date:** 2026-08-22
- **Depends on:** AIF-078 stage 1 (`_ws_handle`/`_engine_slot`/`_ws_local_slot`),
  stage 2 (`include/xbase/workspace_membership.hpp`, verified 2026-08-22 on
  build `8384734f`: 14 areas opened -> 14 members -> 0 after close)

## The defect this closes

`schema_close_all()` in `src/cli/cmd_workspace.cpp` read:

```cpp
for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0)
```

That is a sweep of the whole engine wearing the name of a workspace operation.
It was correct only because exactly one workspace has ever existed. The owner
named it directly on 2026-08-22:

> "close_all needs to be SCOPED to a specific workspace instead of 0-max_areas.
> workspaces have to know the group of areas that belong to them."

Stage 2 built that group. This is its first consumer.

There is a second, independent reason, and it is not decoration. `MAX_AREA` is
512 for testing and the owner has stated the real ceiling is not 512 -- "can
you imagine how long it would take to give you a dotscript results of a 10
trillion max_area pass." A close that is `O(MAX_AREA)` does not survive that
sentence. A close that is `O(members)` does not care what `MAX_AREA` is.

## What changed, observably

| Form | Before | After |
|---|---|---|
| `WORKSPACE CLOSE` | every area, 0..MAX_AREA | the **current workspace** only, plus nested ones per `SET RECURSION` |
| `WORKSPACE CLOSE ALL` | closed nothing (no table named "all"), printed "No matching open areas" | every workspace, everywhere -- the old bare-CLOSE contract, now explicit |
| `WORKSPACE NEW <name> [UNDER <parent>]` | -- | declare a runtime workspace |
| `WORKSPACE SWITCH <name-or-handle>` | -- | areas opened next join that workspace |
| `WORKSPACE REGISTRY` | handle/name/members | adds `parent`, `depth`, and the recursion state |
| `SET RECURSION [ON\|OFF]` | -- | whether an operation descends into nested workspaces |

**With one workspace open, bare CLOSE is byte-identical to the old sweep.**
That is why the eight default regressions do not move: every script in the
suite runs entirely inside DEFAULT.

## SET RECURSION -- what the flag does and does not do

Owner ruling 2026-08-22:

> "we need a SET RECURSION ON | OFF / even with OFF we still alow multiple
> workspaces , just paralell."

So the flag does **not** gate whether nesting may exist. It gates whether an
operation **descends**. OFF leaves nested workspaces open and **says so**;
their areas stay live and reachable.

## Both guards announce

The recursion guard is a visited set plus a depth cap
(`kMaxWorkspaceDepth = 32`), and a structural `would_cycle()` check that
refuses a cyclic parent at declaration time -- the cheapest moment, before
anything is built on the bad edge.

Every one of them **prints when it fires**. This is the direct lesson of the
relation depth cap (`set_relations.cpp`, hardcoded 24, twice, returning
SILENTLY): a traversal that stops early and says nothing is indistinguishable
from one that finished, and a caller cannot tell a complete answer from a
truncated one.

## The reconcile pass, and why the sweep did not simply vanish

Membership is stamped by `DbArea::open()`. If an area is open and belongs to no
workspace, the stamp was missed, and a member-list close would walk past it and
leave a live file handle behind **while reporting success**. The old sweep
caught that by brute force.

So the sweep survives as `reconcile_unregistered_areas()`, which runs **only on
a full close**, and which **prints** each orphan rather than quietly absorbing
it. An orphan is a defect in the registration path, and this is the line that
would name it. A scoped close does not pay that cost and says so.

## Known limitation, stated rather than hidden

The relation graph is process-global -- `relations_api` has no notion of which
workspace a relation belongs to. A scoped close therefore still clears **all**
relations, because leaving a relation pointing into an area this close just
emptied is the dangling-parent shape, and that is worse than an over-eager
clear.

The over-reach is **printed** when it can actually bite (another workspace
still holds areas). **Making the relation graph workspace-scoped is the named
prerequisite before two workspaces can hold relations at the same time.**

`normalize_selected_area_after_workspace_change(0)` likewise still prefers area
0, which after a scoped close may belong to another workspace. Same bucket.

## Why `WORKSPACE NEW` is in stage 3 and not stage 4

The recursive branch has exactly one way to be exercised: a workspace with a
child. Without a way to make one, stage 3 would ship a recursion guard, a depth
cap and a post-order walk that **nothing can reach** -- the AIF-079 shape this
lane has now catalogued four times (`wasStale()` with 7 overrides and 0
callers, `cursor_hook::notify()` with 0 callers, the silent relation depth cap,
and the whole `src/workspace/` namespace).

A mechanism with zero call sites is not "ready for stage 4." It is unproven
code wearing a plan as an alibi.

`WORKSPACE NEW` is runtime-only: no catalog row is written. `WORKSPACES.dbf`
remains the persistence authority, and a declared workspace surviving a restart
is stage 5.

## Verification -- RUNTIME-PROVEN 2026-08-22, build 10:45:57, FIRST TRY

`REGRESSION RUN WORKSPACE_SCOPE` (explicit-run, `workspace_scope_regression.dts`).
All seven markers green: `WS_G0`/`WS_G1`/`WS_G2`/`WS_G3` fixture guards,
`WS_T1`, `WS_T2`, `WS_T3`, `WS_T4`.

`REGRESSION ALL` green on all 8 defaults on the same build. They did not move,
which is the prediction this change had to satisfy: every script in the suite
runs entirely inside DEFAULT, where bare `CLOSE` is byte-identical to the old
sweep.

The two `WORKSPACE REGISTRY` blocks are the direct evidence the walk descended:

```
before:  handle 1 DEFAULT  parent 0  depth 0  members 1
         handle 2 WSPARENT parent 0  depth 0  members 1
         handle 3 WSCHILD  parent 2  depth 1  members 1

after:   handle 1 DEFAULT  parent 0  depth 0  members 1   <-- untouched
         handle 2 WSPARENT members 0
         handle 3 WSCHILD  members 0
```

with `WORKSPACE: 2 workspace(s) closed.` and `2 area(s) closed`.

The OFF arm measured what the flag is for:
`SET RECURSION is OFF; 1 nested workspace(s) under WSPARENT were left open.`
followed by `1 area(s) closed` and `WS_T2` green.

**No guard fired.** No cycle line, no depth-cap line, and no
`area N belongs to NO workspace`. The reconcile ran on every full close and
found nothing, so membership and reality agree -- stage 2's registration claim
is now re-measured on every `CLOSE ALL` rather than asserted once.

The relation over-reach printed where predicted, with correct counts: `1 area(s)`
in the ON arm (DEFAULT) and `2 area(s)` in the OFF arm (DEFAULT plus the child
deliberately left open).

Cosmetic defect found in the run, not fixed: `WORKSPACE: N workspace(s) closed.`
prints BEFORE the relations line and the area count, so the summary leads the
detail it summarises. No behavioural consequence; fix when this file is next open.

**WS_T1 is the discriminator.** Under the old sweep it goes red: closing a
nested workspace took DEFAULT's areas with it. Delete the scoping and exactly
one line reds.

**WS_T2 is the only place `SET RECURSION` is load-bearing** -- same script,
same shape, one flag flipped, and the nested workspace's table is still
readable.

**WS_T4** proves `CLOSE ALL` reached the filesystem and not merely the
bookkeeping, by reopening and reading.

**Not asserted, deliberately:** that a recursively-closed workspace is *empty*.
USE_AGAIN established over three cuts that no marker in this language can
assert an area is empty -- the marker evaluator binds a null area unless the
area is OPEN (`rhs_eval.cpp:969`), which is the very thing under assertion, and
an errored marker prints nothing rather than going red. The recursive close is
proven by contrast plus the member counts in the two `WORKSPACE REGISTRY`
blocks, read from the transcript (external measurement, the IDXDIFF precedent).

The membership header additionally carries a standalone self-check that was run
before this shipped -- nesting, depth, cycle refusal, lowest-free-slot reuse,
and the destroy guards -- compiled and executed under g++ -std=c++20.

## Good Neighbor

- **What changed:** `src/cli/cmd_workspace.cpp` (scoped close, reconcile,
  NEW/SWITCH, REGISTRY fields, usage), `include/xbase/workspace_membership.hpp`
  (parent link, recursion flag, create/destroy/cycle guard),
  `src/cli/cmd_set.cpp` (`SET RECURSION`), `src/cli/reference_collection.cpp`
  (reflection row), `src/cli/cmd_regression.cpp` (registration, array size
  46 -> 47), new `dottalkpp/data/scripts/workspace_scope_regression.dts`.
- **Whose area:** this lane's own. `src/xbase/` was not touched in this stage.
- **What authorization:** owner ruling 2026-08-22 ("close_all needs to be
  SCOPED...", "we need a SET RECURSION ON | OFF...", "I agree to all semantics,
  begin building"), and "build it" for this stage.
- **How to verify:** `cmake --build build --config Release`, then
  `REGRESSION ALL` (8 defaults must stay green -- they run entirely inside
  DEFAULT and must not move) followed by `REGRESSION RUN WORKSPACE_SCOPE`.
- **How to undo:** revert the commit. Bare `WORKSPACE CLOSE` returns to the
  full sweep; `CLOSE ALL`, `NEW`, `SWITCH` and `SET RECURSION` disappear.
  Nothing on disk is written by any of it -- workspaces declared with NEW are
  session state and no catalog row is created.

## Open, carried forward

1. Relation graph is not workspace-scoped (blocks two workspaces holding
   relations simultaneously).
2. `normalize_selected_area_after_workspace_change` is not workspace-aware.
3. Catalog persistence for declared workspaces (stage 5).
4. `WORKSPACE NEW` on a name that already exists prints and returns; reruns
   within one process are tolerable but not idempotent.

---

## Addendum -- local slots rebased to 0 (owner ruling 2026-08-22)

**Status:** review-needed. Same AIPR, same stage, same files; recorded here
rather than in a separate document because it changes a field this ruling
introduced and would be unreadable apart from it.

### The observation

The owner noticed the asymmetry before it set:

> "i noticed workspace handles are 1 based and areas are 0 based ... i always
> kind of thought of '0' as a 'default' for when 1 table was in use, not a
> requirement just a 'default' not a rule, just opining before things get baked
> in"

There were in fact THREE numbering planes in one process, not two:

| plane | base | kind |
|---|---|---|
| engine slot | 0 | position |
| workspace-local slot | 1 | position |
| workspace handle | 1, with 0 = "none" | key |

### The ruling

> "we advertise all over the place that x64base is not a clone but an
> 'evolution'. so 0 based costs us nothing to maintain forward in workspaces
> too"

Local slots are now **0-based**, matching the engine.

The 1-based spelling was inherited habit, not design: dBase and FoxPro number
work areas from 1 and FoxPro spends `SELECT 0` on "the lowest unused work area."
Neither is a contract this project owes anyone -- and note DotTalk++ had already
diverged, since `SELECT 0` here selects area 0 rather than allocating a free
one. Keeping the inherited base bought one thing: a second counting origin
inside one process, and an off-by-one for every reader to carry.

### Why it was free, and the AIF-079 instance it exposed

`DbArea::wsLocalSlot()` had **zero readers** -- written in `dbf_file.cpp`,
cleared in `dbarea.cpp`, read nowhere; `WORKSPACE REGISTRY` derived its display
number from the member vector's index, never from the field. That is the
AIF-079 shape (a mechanism with no call sites) and it is **mine**, introduced in
stage 1 five days ago, found while answering a question about numbering rather
than a question about dead code. Fifth instance in this lane's census, first one
authored here.

### What did NOT change, and why

**The handle stays a key.** It is the runtime twin of the catalog's `WS_ID`
auto-id allocator, and a key has no position to be based on. Handle `0` remains
reserved for "no such workspace / no parent," which is what lets
`find_by_name_ci`, `parent_of` and `resolve_workspace_token` report failure
through the return value with no second channel.

The concrete cost of 0-basing it would have been observable: `WORKSPACE
REGISTRY` prints `parent 0` to mean **root**. With DEFAULT at handle 0 that line
stops distinguishing "has no parent" from "child of DEFAULT" -- information lost
at exactly the place the tree is read.

### The line that had to move with it

`dbf_file.cpp` guarded the join result with `if (local > 0)`. Correct while
slots were 1-based; under 0-basing that spelling silently drops **every
workspace's first area**. Now `>= 0`.

`join()`'s failure return survived untouched precisely because it is `-1` and
not `0`. Had the original author reached for zero as the error value, the first
valid slot and "no such workspace" would now be the same number. That is luck
rather than foresight, and it is written down here so the next person treats it
as a constraint.

### Verification

The standalone header self-check was extended and re-run under `g++ -std=c++20`:
first member is slot 0, lowest-free reuse returns 0, idempotent re-join returns
0, and `join()` on an unknown handle returns `-1` and is asserted **distinct
from 0** -- the assertion this rebase could have broken and did not.

`WORKSPACE REGISTRY` output changes: member lines now read `local 0  engine slot
N`. `WORKSPACE_SCOPE` asserts no local-slot numbers (no marker in this language
reads REGISTRY output -- the IDXDIFF external-measurement precedent), so it
stays green on its own terms; the numbering is covered by the self-check.
