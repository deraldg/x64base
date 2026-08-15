---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-004
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  git:
    branch: development
    baseline_commit: 5e4c86b84
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session, "do it"
    scope: >
      Lane charter only. Drafted from the source-level findings in
      AIPR-20260815-COWORK-002. No source mutation. AIF-113 claimed host-side by
      the owner via session_coordinator.py claim-aif; not self-assigned.
  lane: AIF-113
  report:
    path: docs/maintenance/LOCK_RELEASE_AND_RECOVERY_LANE_V1.md
    kind: lane_charter
  primary_topics:
    - "xbase_locks"
    - "release_held"
    - "force_unlock"
    - "I5"
    - "lock recovery"
---

# Lock Release and Recovery -- Three Dead Functions and a Command That Never Releases (Lane V1)

**Status:** not started -- charter only. **Lane:** AIF-113
(claimed 2026-08-15, run COWORK-20260815-001, lane `lock-release-recovery`).
**Owning project:** `project.x64base.runtime`. **Evidence class:** `source-defined`
(every claim below is a file:line read on 2026-08-15 at `5e4c86b84`).
**Split from:** AIF-112, which demoted this out of its Phase-1 gate. See
`AIF112_SOURCE_REUSE_AUDIT_AND_I5_SCOPING_V1.md`.

> **PRIORITY CHANGED 2026-08-15, after this charter was written.** This lane was
> chartered as housekeeping: three dead functions, nobody calls them, no user is
> currently harmed. **That is no longer true.** AIF-116 found, on a live
> two-process run, that `xbase_locks` cannot distinguish a live lock owner from a
> dead one, and its fix cannot ship without the recovery path this lane owns.
> **AIF-113 is now a blocking dependency of AIF-116, not a neighbour of it.**
> See the section "Runtime leg supplied" below, and
> `LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md` section 10.

## The problem, measured

`WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` invariant I5 asserted three things.
All three are true, at the line numbers it gave:

- `release_held` -- declared `include/xbase_locks.hpp:59`, defined
  `src/xbase/xbase_locks.cpp:407`, and **called from nowhere**. Two occurrences
  in the entire tree.
- `current_owner()` is a process singleton:
  `static Owner g_owner{ make_owner_string() };`. Owner string is `host:pid:ms`.
- The stale reaper fires only on a dead pid --
  `if (!is_pid_alive(meta.pid))` at `:244`, same test at `:315` and `:321`.

I5 then said a leaked lock is clearable by "nothing but `FORCE UNLOCK`."
**That is where it is too optimistic.** Measured:

- `force_unlock_table` (`xbase_locks.cpp:386`) and `force_unlock_record`
  (`:393`) exist and are **called by nothing**. Their only other occurrences are
  the declarations at `xbase_locks.hpp:55-56`.
- `cmd_unlock.cpp` handles `ALL` and `TABLE` (`:114`) and routes both to the
  owner-aware `unlock_table`, which refuses a non-matching owner. There is no
  `FORCE` verb on the command surface.

So the designed recovery path is **three functions, none reachable**. A leaked
live-pid lock owned by another process is clearable by no exposed command.
Recovery today means killing the owning process or removing the sidecar by hand.

## What is actually exposed, and what is not

Every lock acquisition outside `xbase_locks.cpp` falls into one of two classes.
This distinction is why the lane is narrow rather than alarming.

**Class A -- transient, released in the same operation. NOT at risk.**

| Site | Shape |
|---|---|
| `src/bbs/bbs_store.cpp:95,99` | RAII `TableLock`, destructor unlocks |
| `src/cli/cmd_workspace.cpp:2112,2117` | RAII `WsLock`, destructor unlocks |
| `src/cli/append_support.cpp` | four paired acquire/release sites |
| `cmd_calcwrite`, `cmd_commit`, `cmd_delete`, `cmd_recall`, `cmd_replace`, `cmd_replace_multi` | paired around a single write |

The two RAII sites are additionally exception-safe. The paired ones are not: an
early return or throw between acquire and release leaks. That is a real but
narrow hardening item, listed under Design below.

**Class B -- held across operations. THE ENTIRE EXPOSURE.**

`src/cli/cmd_lock.cpp:161, 175, 199` -- owner-aware acquires.
`grep -n unlock src/cli/cmd_lock.cpp` returns nothing. The `LOCK` command never
releases, by design, because holding is what it is for. `UNLOCK` is the only
release path.

The failure: a user issues `LOCK`, then closes the area without `UNLOCK`. The
sidecar survives with a live pid. Nothing in-process releases it, the reaper will
not fire, and no exposed command can clear it.

## Why this was not caught earlier

`WsLock`'s destructor calls `unlock_table` **explicitly** rather than relying on
area close. So the two most-exercised lock users route around the defect without
depending on a fix, and the defect never shows up in their proofs. It only bites
the user-facing command, which has no automated proof exercising a
hold-then-close sequence.

## Design (options, not decisions)

1. **Wire `release_held` into area close.** The obvious fix, and the one I5
   proposes: `close_area_if_open` (`cmd_workspace.cpp:1283` per I5) calls
   `release_held` for the closing area. Priced surface per I5: 43 lock call
   sites across 13 files.
2. **Expose a FORCE verb.** `force_unlock_table` / `force_unlock_record` already
   exist. `UNLOCK FORCE` / `UNLOCK FORCE <recno>` would make them reachable.
   Should be permission-gated -- `cmd_net.cpp` is the model (Critical,
   requires_approval, owner exempt, AI denied).
3. **Give the owner token a workspace suffix**, per I5, so intra-process
   isolation is real rather than assumed.
4. **Harden the Class A paired sites to RAII**, so an exception cannot leak what
   a destructor would have released.

Options 1 and 2 are independent and both worth having: 1 prevents the leak, 2
recovers from one that already exists (including leaks predating the fix).

## What this does NOT solve

- It does not change AIF-112. That lane's ledger is Class A and never holds a
  lock across operations. Confirmed and recorded; do not re-couple them.
- It does not address the *absence of proof* around the `LOCK` command. A
  regression exercising hold-then-close-then-contend is a separate acceptance
  item and arguably should land first, since it is what would have caught this.
- It does not touch `autoq_next` (load-only auto-id, `xbase_64.hpp:52`), which
  `cmd_workspace.cpp:2345` names as its own chartered engine lane.

## Acceptance

- [ ] A regression that acquires via `LOCK`, closes the area without exiting,
      and asserts the lock is gone.
- [ ] A regression that leaks a lock deliberately and recovers it through an
      exposed command, with no manual file removal.
- [ ] `release_held` has at least one call site, or is deleted with a recorded
      reason. Same for `force_unlock_table` / `force_unlock_record`.
- [ ] Cross-process contention still refused correctly after the change --
      `dottalk_bbsd` and the CLI on one data root is the natural harness.
- [ ] The Class A paired sites either converted to RAII or recorded as accepted
      risk with reasons.

## Runtime leg supplied 2026-08-15 -- and it inverted this lane's priority

The closing note below asked for the I5 runtime probe to be routed here when run.
**It was run**, on 2026-08-15, at banner `fb7106e0 dirty`, as AIF-112 Phase-1
Step 4. It supplied the runtime leg this charter was missing and it found
something this charter did not predict.

**What the probe found.** Two processes, same table. A took `LOCK TABLE`. B read
A's lock correctly and was then **granted the same lock**. Root cause in
AIF-116: the owner's pid is written to the sidecar through an un-imbued stream,
so under a grouping locale it lands as `pid=16,984`; `std::stoul` reads it back
as `16`; `is_pid_alive(16)` is false; the stale branch runs `force_remove` and
the lock is stolen. Every live lock looks stale, on every acquisition.

**Three consequences for this lane, in order of importance.**

1. **The stale reaper described above at `:244`/`:315`/`:321` is not merely
   correct-but-narrow, as this charter assumed. It is firing constantly, on
   locks whose owners are alive.** The charter's reading of I5 -- that recovery
   only matters for genuinely leaked locks -- described intended behaviour, not
   observed behaviour.

2. **The two defects are currently masking each other, and that makes this lane
   blocking.** Leaked Class B locks are being silently cleaned up *by* the broken
   stale detection. Fix AIF-116's parse alone and orphans stop being reclaimable
   at all -- and because `force_unlock_table` and `force_unlock_record` are
   unreachable, there is no exposed command to clear one. A single abandoned
   `LOCK TABLE` would wedge that table for every process on the machine. **The
   enforcement fix and the recovery path have to land together.** Of the design
   options below, option 2 (expose a permission-gated FORCE verb) is therefore no
   longer optional, and option 1 (wire `release_held` into area close) is what
   stops the leak being created in the first place.

3. **The release-side survey widened.** Confirmed by source read on the same day:
   `CLOSE`, `CLEAR`, `USE`/`OPEN`, `DbArea::close()` (`dbarea.cpp:59`),
   `~DbArea()` (`:57`) and process exit **all** leave the sidecar in place. The
   explicit `UNLOCK` verb is the only release path in the system. This confirms
   the charter's Class A / Class B split rather than revising it, and it answers
   the maintainer's question during the run -- entering a new work area does not
   clear another session's lock, and nothing else does either.

**Also observed, filed in AIF-116 as E2:** `UNLOCK` on a record that is not
locked reports success. A release verb that cannot distinguish "released it" from
"there was nothing to release" leaves the operator unable to detect that a lock
they believed they held was already gone -- which is precisely the state AIF-116
produces. Minor alone; it belongs to this lane's surface.

**Acceptance implication.** The acceptance criteria below were written for a
source-defined lane. At least one now needs a runtime leg: a two-process test
that a leaked Class B lock is recoverable through an exposed command, which is
the same harness AIF-116 owes for refusal-under-contention. Build it once, use it
for both.

## Ties

- **AIF-116** (`LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md`)
  -- **blocking relationship, this lane is the blocker.** Same file, same
  subsystem; that lane is acquisition, this one is release. Its fix is unsafe to
  ship without this lane's recovery path.
- **AIF-031** -- the defect class behind AIF-116, and the sweep that missed
  `xbase_locks.cpp`. Relevant here because it is the reason to prefer a gate over
  remembered discipline when this lane's fix lands.
- **AIF-112** -- demoted this out of its Phase-1 gate on the Class A/B evidence.
- **AIF-059** (Hot Potato) -- advisory commit lock; same family of "who holds
  what, and how does it get released."
- `WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` invariant I5 -- the origin.
- `proof.agency.model` declared gaps -- "git agency serialized by convention not
  mechanism" is the same shape of problem one layer up.

## Note on the source of this charter

Written by a scribe with read-only source access, from static analysis. **No
runtime probe was executed** at charter time. The optional I5 probe in AIF-112's
amended exercise outline would supply the runtime leg and should be routed here
when run.

**Closed 2026-08-15: it was run, and it is routed here.** See "Runtime leg
supplied" above. The static analysis held up on every point it made -- the three
dead functions, the Class A / Class B split, the absent FORCE verb -- and was
wrong only in its estimate of urgency, which static analysis could not have
reached. Worth recording as a method note: **a source-defined charter can be
completely correct and still mis-rank itself.** The line that needed a runtime
leg was not any factual claim in this document; it was the word "housekeeping."
