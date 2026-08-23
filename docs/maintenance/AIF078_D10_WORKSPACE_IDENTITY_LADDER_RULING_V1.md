---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260823-COWORK-116
  recorded_at_utc: 2026-08-23T14:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: GUI API
    run_id: COWORK-20260823-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: fd41c5d87
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-23. Opened with
      "we have conflicts by me and different agents at this juncture, which tells
      me this is a crux -- what is the platinum standard", then ruled "i want a
      ws_id" (D10.1) and "it is the same lane" (D10.3). Authorises NO code.
  review:
    supersedes: D9 sec 9b's persistence half. See sec 6.
    accepted_by: maintainer (member.derald), in-session 2026-08-23 -- "accept".
      Covers D10.2, D10.4 and D10.5; D10.1 and D10.3 were already his.
  report:
    path: docs/maintenance/AIF078_D10_WORKSPACE_IDENTITY_LADDER_RULING_V1.md
    kind: ruling
---

# AIF-078 -- D10: one identity ladder, three rungs, and a workspace is born durable

Status: **ruling, ACCEPTED 2026-08-23.** D10.1 and D10.3 are the STEWARD's,
given in-session. D10.2, D10.4 and D10.5 were the author's recommendations and
were **accepted by the steward in-session the same day -- "accept"** -- which
is what moves this document out of review-needed. One branch remains open
inside D10.5 and is marked there; it blocks nothing.
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260823-001`.
Date: 2026-08-23. Baseline `fd41c5d87`.

**This document authorises no build.** It fixes what identifies a workspace, so
that I1.2, `WORKSPACE DESTROY` and the GUI redesign are each cut once.
Depends on **D8** (lane seam) and amends **D9** (relation key).

## 1. Why this ruling exists

The steward's own diagnosis opened it: *"we have conflicts by me and different
agents at this juncture, which tells me this is a crux."*

He is right, and the cause is not that anyone reasoned badly. **This tree
contains two independent identity systems for the same noun, each internally
consistent, neither citing the other.** Every agent that read one authority and
not the other produced a confident, well-argued, incompatible answer. This
author produced two of them, in opposite directions, eleven hours apart.

**System A -- shipped, exercised by three registered specs, stated in three
separate source files:**

- `include/xbase/workspace_membership.hpp`, header contract:
  *"The workspace CATALOG (WORKSPACES.dbf, catalog v2) is the persistence
  authority: WS_ID allocates identity, WS_NAME is the key, and a saved
  posture's AREA lines are the child list AT REST."*
- Same file, at `join()`: *"A HANDLE is a KEY -- the runtime twin of the
  catalog's WS_ID auto-id -- and keys have no base to speak of; handle 0 stays
  reserved for 'no such workspace / no parent'."*
- `include/xbase.hpp`: *"identity is the catalog's WS_ID -- an N(10) column."*
- And it is enforced, not merely asserted: `open_catalog()` registers `WS_ID`
  through `unique_reg::set_unique_field` / `set_primary_field` as the catalog's
  PRIMARY UNIQUE field.

**System B -- declared, never built:** `dottalk::reference::WorkspaceIdentity`,
`WorkspacePath`, `DataAddress`, from the reference/PDLC lane. Its own header
admits the gap: *"searched-and-absent: no runtime workspace registry, no
containment invariant, no cycle guard, no depth cap."*

`WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` sec 2 chose System B. D9 sec 9a
chose System B. D9 sec 9b chose half of System A and got the other half wrong.
**The disagreement was a symptom. The defect is that both systems exist.**

## 2. The platinum standard

Every mature system that has solved this converges on the same shape -- POSIX
(`fd` vs inode), Win32 (`HANDLE` vs object name), Git (packfile offset vs SHA
vs ref), Oracle (`ROWID` vs primary key), and VFP itself (work area number vs
alias vs table path). It is **three rungs, not two.** The fight only happens in
a system that has the rungs but never wrote down which rung answers which
question -- which is exactly this tree's position.

| rung | this tree's token | scope | reused | the ONLY question it answers |
|---|---|---|---|---|
| **durable** | `WS_ID` chain root, `WS_NAME` the human key, `PREV_ID` lineage | sessions, processes, machines | never | *which workspace is this, forever* |
| **session** | `_ws_handle` (uint64, monotonic, never reused, 0 = none) | one process | never within a session | *are these the same workspace, in O(1), right now* |
| **positional** | `_engine_slot`, `_ws_local_slot`, posture `AREA <n>` | one container | immediately | *where is it sitting* |

Five rules govern them. **These are the standard, and they are the point of
this document:**

> **R1 -- Derivation runs downward only.** durable -> session -> positional,
> each step a NAMED lookup that can fail. Never upward. A position never names
> a workspace; a handle is never persisted. The tree already half-obeys this:
> `declare()`'s own comment says it exists for *"what a catalog restore will
> need when WS_ID is the authority"* -- that IS the durable-to-session
> conversion, already written and waiting for a caller.
>
> **R2 -- A rung is real only if it has a PRODUCER, a COMPARATOR, and a
> PERSISTER.** This is the test that ends the argument, because it is measured
> rather than argued.
>
> **R3 -- Conversion sites are few, named, and fail in the return value.**
> Already house practice, and already reasoned about: the membership header
> explains why its miss sentinel is -1 and not 0.
>
> **R4 -- The rung is chosen by the QUESTION, never by the caller's
> convenience.** Every defect in this family is a caller reaching for whichever
> token was nearest.
>
> **R5 -- One tree, one ladder.** A second identity system for the same noun is
> a DEFECT, not a lane. This is the rule that was missing, and its absence is
> what produced the conflict.

## 3. R2 applied -- the measurement that settles System A vs System B

Measured 2026-08-23 at `fd41c5d87`:

| candidate | producer | comparator | persister | verdict |
|---|---|---|---|---|
| `WS_ID` / `WS_NAME` | yes (`save_to_memo`, max+1 under FLOCK) | yes (PRIMARY UNIQUE) | yes (WORKSPACES.dbf) | **a rung** |
| `_ws_handle` | yes (`create()`, `DbArea::open()`) | yes | **no, and correctly so** | **a rung** (session only) |
| `WorkspaceIdentity` | **no** | yes (`operator==`) | **no** | **not a rung** |

`grep -rn "WorkspaceIdentity" include src` returns **17 lines in three files**:
its own declaration, its own definition, and one test. **Zero under `src/cli`,
`src/xbase` or `src/gui`.** Two of its three fields -- `profile_path`,
`session_id` -- are written nowhere in the tree at all.

It is not wrong. It is **unbuilt** -- an AIF-079 instance, a mechanism with
zero call sites. Keying anything on it today would require inventing two values
at the moment of use, which is not identity; it is fabrication wearing a
struct.

## 4. The defect the steward's instinct found

He said *"i want a ws_id."* Reading the source to answer him surfaced this:

```
N("WS_ID", 10);    // unique auto-id
C("WS_NAME", 32);  // THE key: the human handle you load by
N("PREV_ID", 10);  // lineage: WS_ID of the row this save superseded (0 = first)
...
const std::uint64_t newId = maxId + 1;     // allocated on EVERY save
```
(`src/cli/cmd_workspace.cpp` `ensure_catalog()` and `save_to_memo()`.)

**`WS_ID` identifies a SAVE, not a workspace.** One workspace named `MCC` saved
five times is five rows, five `WS_ID`s, chained by `PREV_ID`, four
`SUPERSEDED`. The field that identifies the workspace across time is the
32-char human name, by the owner's own catalog-v2 ruling: *"single-key identity
(WS_NAME is the human handle -- NO composite keys)."*

So a field named `WS_ID` does not identify a WS. That dissonance is what the
steward's instinct located, and it is a real defect, not a preference.

## 5. The rulings

> **D10.1 (STEWARD).** *"i want a ws_id."* **A workspace is born durable.**
> `WORKSPACE NEW` allocates the workspace's durable identity at creation. A
> workspace does not have to be saved before it can be referred to from
> outside the process.
>
> **D10.2 (author's recommendation, under D10.1).** The mechanism is a **BIRTH
> ROW**, not a redefinition and not a new column. `WORKSPACE NEW` appends a
> catalog row under the existing `WsLock` FLOCK -- `WS_ID = max+1`, `WS_NAME`,
> `PREV_ID = 0`, no payload. The first save then supersedes it exactly as saves
> already supersede each other.
>
> **A workspace's durable identity is the ROOT of its `PREV_ID` chain.** Walk
> back to 0 and you have its birth id.
>
> This is Git's model and the catalog is already three-quarters of the way
> there: the chain root is identity, each save is a commit with a parent,
> `SUPERSEDED` marks which is live. It costs no schema change, no catalog v3,
> and destroys none of the existing rows -- and it makes the name `WS_ID`
> TRUE, because the first id in a chain really does identify a workspace.
>
> Rejected, and recorded so they are choices rather than omissions:
> redefining `WS_ID` to per-workspace guts `PREV_ID`'s stated meaning and
> spends the best part of the catalog; a new `WS_UID` column needs catalog v3,
> and with no ALTER-add-field in this tree the upgrade path is the pre-v2
> guard's own remedy -- *"Remove WORKSPACES.\* ... and re-save"* -- which throws
> away every existing row for no benefit (b) does not already give.
>
> **D10.3 (STEWARD).** *"it is the same lane."* **`WORKSPACE DESTROY` is cut
> with the birth row, not after it.** A workspace born durable must be able to
> die durable, or birth rows accumulate with nothing able to retire them.
> `workspace::destroy()` is defined in `workspace_membership.hpp` and has
> **ZERO callers** -- a second AIF-079 instance, and this is where it gets its
> call site. DESTROY retires the birth row and releases the handle; the handle
> is never reused, which the header already guarantees and explains.
>
> **D10.4 (amends D9.1, and supersedes D9 sec 9b's persistence half).**
> The steward's *"yes we key both ends"* is untouched for the fourth time.
> Both ends of a relation edge carry a workspace. The SPELLING is now settled
> by the ladder rather than by argument:
>
> - **Runtime, in-process:** the interned `std::uint64_t` handle. O(1), no
>   allocation, no fabricated fields, and the only workspace identity any
>   runtime writer in this tree produces.
> - **Persisted or crossing a process boundary:** the **chain-root `WS_ID`**,
>   with `WS_NAME` carried alongside as the human key.
>
> **9b said persist the NAME. That was wrong** and R2 is what catches it: 9b
> reached for `Entry::name` because `name` was the field it could see, and
> `Entry` is the SESSION rung. Persisting a bare name re-creates NAME_AMBIG's
> problem one level up -- two workspaces called `MCC` in two catalogs -- which
> is the exact failure that lane exists to prevent.
>
> **D10.5 (author, and no longer a crux).** `WorkspaceIdentity` is the
> reference lane's ADDRESS type, not the workspace ladder. Under R1 it sits
> DOWNSTREAM: its workspace field is populated FROM the ladder at one named
> conversion site, or the struct is repointed onto `WS_ID`. Under R5, what may
> NOT happen is the two systems continuing to coexist as peers.
>
> **ACCEPTED 2026-08-23, with one branch left open.** "Downstream, not a peer"
> is settled. WHICH of the two -- populate from the ladder, or repoint onto
> `WS_ID` -- is deliberately deferred to the moment the conversion site is
> written, because that is when the cost of each becomes visible rather than
> estimated. It blocks nothing: no consumer exists to be broken either way,
> which is the whole finding of sec 3.

## 6. What this makes false the day it lands

Recorded here so it is corrected in the same commit rather than rotting:

- **`WORKSPACE_SCOPE`'s registered summary** claims it *"leaves two
  runtime-only workspaces declared (they hold no areas and do not survive a
  restart)."* Under D10.1 those workspaces write catalog rows. The summary and
  the spec's mutation disclosure both change.
- **`WSMULTI` and `USE_ARGS`** likewise mint workspaces per run. With DESTROY
  in the same lane (D10.3) their teardown gains a destroy step; without it they
  would multiply rows.
- **The catalog census report** in `cmd_workspace.cpp` rests on *"nothing the
  system writes puts a non-memo row in this table."* A payload-less birth row
  is a second kind, and that comment -- which is itself a correction of an
  earlier wrong claim -- needs its third revision.
- **D9 sec 9b's persistence half** is superseded by D10.4. 9b's runtime half
  and its measurement stand.

## 7. What would falsify D10

- A runtime writer of `WorkspaceIdentity` outside `data_address.cpp` and the
  PDLC test -- then R2's verdict in sec 3 is wrong and System B is a rung.
- A producer landing for `profile_path` or `session_id` -- then the struct has
  content and D10.5's direction may invert.
- A measured collision in `max+1`-under-FLOCK allocation -- the birth row
  reserves its id BY WRITING under the lock, the same proven `bbs_store`
  next_id pattern the save path already uses; if that pattern is unsound the
  save path is unsound too and this is the smaller half of the problem.
- A steward ruling that `WS_NAME` alone is sufficient durable identity. It is
  his catalog and his single-key ruling; D10.4 adds the surrogate BESIDE the
  name, and does not remove the name.

## 8. Evidence tier

MEASURED for sec 3 and sec 4 (greps and source reads at `fd41c5d87`, commands
in sec 9). REASONED for sec 2 (the three-rung convergence is prior art from
outside this tree, offered as precedent, not as proof about this code).
RULED for D10.1 and D10.3. RECOMMENDED for D10.2, D10.4, D10.5.

## 8a. I1.2 LANDED 2026-08-23, and the one exclusion D9 required in writing

The relation store is now partitioned by workspace handle, per D10.4's runtime
half. `relations_store()` keeps its exact signature and resolves the current
workspace internally, so all 29 call sites are unchanged and exactly ONE place
decides which partition a name lookup means. Proven by `RELSCOPE2`
(RS_G0-G2, RS_T1, RS_T2).

**D9 sec 4 item 1 is superseded in the landing as it was in 9a.** The composite
`RelKey{ws, name}` was never built: the partition IS the map, so no hash
function was written and same-named parents in two workspaces cannot collide
because the key never leaves its workspace.

**The exclusion, stated as sec 4 item 5 required.** `merge_relation`
(`src/gui/core/session.cpp`) is **EXPLICITLY OUT OF I1.2**, not brought into
agreement. Its identity predicate compares lowered parent and child names with
no workspace term, and its key check treats an EMPTY key as compatible with
anything -- the AIF-118 shape, absent read as fine. Both remain true today.

The reason this is an exclusion rather than an oversight: `merge_relation` is
the GUI's own model-merge path and does not read the CLI store this lane just
partitioned, so the two cannot disagree about a relation they never share.
**What it WILL do, the moment the GUI consumes the partitioned store, is
recreate the two-resolver defect I1.3a closed, one layer up** -- exactly as sec
4 item 5 predicted. That makes it a prerequisite of the GUI redesign's S-series,
not of I1.2, and it is recorded here so the redesign meets it as a known debt
rather than as a discovery.

Also landed with I1.2, from sec 4 item 4: `set_current_handle()` now REJECTS 0
at the API. It was policed only at one call site before; harmless against a flat
map, load-bearing against a partitioned one, because a stray 0 would drop a
whole workspace's relations into the reserved "no such workspace" bucket.

Recorded, not fixed: `current_parent_override()` in `set_relations.cpp` is still
ONE global rather than per workspace. It is the REL parent shorthand and not the
graph, so no arm of `RELSCOPE2` depends on it -- but it is the next
workspace-blind piece of relation state and should not be found by surprise.

## 9. Good Neighbor note

- **What changed.** This document. No code, no build, no test, no schema.
- **Whose area.** AIF-078's. It amends D9.1 (same lane, same author). It
  reaches into the reference/PDLC lane at D10.5 -- that lane's owner wins on
  `WorkspaceIdentity`'s internals; D10.5 rules only that it is downstream of
  the ladder, not that it is wrong.
- **What authorization.** The steward, in-session 2026-08-23: *"what is the
  platinum standard"*, then *"i want a ws_id"* (D10.1), then *"it is the same
  lane"* (D10.3). Authorises NO code.
- **How to verify, and this is the whole of the argument.**
  - `grep -rn "WorkspaceIdentity" include src --include=*.hpp --include=*.cpp`
    -- expect 17 lines in three files, none under `src/cli`, `src/xbase`,
    `src/gui`.
  - `grep -n 'N("WS_ID"\|C("WS_NAME"\|N("PREV_ID"\|newId = maxId' src/cli/cmd_workspace.cpp`
    -- expect the four lines quoted in sec 4.
  - `grep -n "inline bool destroy" include/xbase/workspace_membership.hpp`
    -- expect ONE line, the definition. Then
    `grep -rn "workspace::destroy" src include` -- expect ZERO. Both halves are
    needed and the second alone is not the proof: callers spell these
    `xbase::workspace::create(...)` (see `cmd_workspace.cpp`, `cmd_use.cpp`),
    while the definition is a bare `inline bool destroy` inside
    `namespace xbase::workspace`, so a qualified-name grep finds neither the
    definition nor a caller and returns 0 either way. Checked 2026-08-23: a
    bare `grep -rn "destroy(" src --include=*.cpp` returns only Turbo Vision
    dialog teardown and two statics in `evaluate.cpp`, none of them this one.
  - `sed -n '14,32p;258,270p' include/xbase/workspace_membership.hpp` -- the
    two System A quotes in sec 1.
  - `grep -n "searched-and-absent" include/reference/data_address.hpp` -- the
    System B admission.
- **How to undo.** Delete this file. No code depends on it. D9 sec 9b's
  persistence half would revert to standing, and the crux would reopen.
