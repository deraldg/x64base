---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-059
  recorded_at_utc: 2026-08-19T22:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: bf54022d0
  authorization:
    requested_by: maintainer (member.derald), standing in-session -- R50 section 7's
      top open item, run in WSL under the agreed split (PowerShell for doc work,
      WSL for testing and dev).
  report:
    path: docs/maintenance/AIF120_LOCK_RECLAIM_V1.md
    kind: ruling
  cross_lane_finding:
    lane: AIF-116
    kind: source_evidenced
    summary: >
      is_pid_alive's Windows branch treats access-denied as process-not-found, so a
      live owner belonging to another user can be declared stale. The POSIX branch
      handles the equivalent case (EPERM) correctly.
---

# AIF-120 -- R51: crash reclaim holds, and the Windows liveness branch does not ask the same question as the POSIX one

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R50 section 7 led with: *"Crash reclaim is untested... whether the liveness check
reclaims it is exactly the path AIF-116 broke."* It does, correctly, in both
directions. Reading the source to explain *why* found something else.

## 1. Both directions, runtime-proven

The two requirements pull against each other, and either alone can be satisfied by a
broken implementation -- a check that always reclaims passes the second, a check that
never reclaims passes the first. So they are tested in this order:

```
=== 1. LIVE owner must NOT be reclaimed (the AIF-116 direction) ===
    holder pid 18716 is alive
    . LOCK: failed (lock exists).
    . Table: LOCKED (owner Grimwood:18716:1787170076682)

=== 2. DEAD owner MUST be reclaimed -- holder killed with SIGKILL ===
    holder pid 18716 killed. Sidecar still present: yes
    confirmed: pid 18716 is gone
    . LOCK: table locked.
    . Table: LOCKED (owner Grimwood:18742:1787170079766)

  LIVE owner's lock was NOT taken (AIF-116)      : True
  DEAD owner's lock WAS reclaimed                : True
```

`SIGKILL` between `LOCK` and `UNLOCK` -- no release, no shutdown hook, no chance to
clean up. This is what a crashed frontend leaves behind, and the next one recovers
from it. Evidence tier: **runtime-proven**.

## 2. The on-disk format, and a redundancy worth naming

```
DotTalk++ lock
owner=Grimwood:18716:1787170076682
pid=18716
ms=1787170076682
```

The pid appears **twice** -- inside `owner=` and again as `pid=` -- and so does the
acquisition timestamp. Ownership is compared using `owner=`; liveness is decided
using `pid=`. Two copies of one number, written by one code path and consumed by
two, is precisely the shape AIF-116 had: what was written and what was parsed
diverged. Nothing today makes them disagree, and nothing today would notice if they
did.

## 3. The fail-closed design is right, and worth stating so it is not "simplified" later

```cpp
// AIF-116: fail CLOSED. Only an owner whose pid was parsed cleanly may be
// declared stale. An unreadable or malformed owner is presumed ALIVE.
if (meta.pid_valid && !is_pid_alive(meta.pid)) { ... }
```

`pid_valid` is a separate flag rather than `pid == 0` because -- as the source itself
notes -- `is_pid_alive(0)` is false, so a sentinel would make an *unreadable* owner
look *dead*. That distinction is the whole remedy, and it is the kind of thing a
later reader deletes as redundant.

## 4. Finding for AIF-116: the two liveness branches do not ask the same question

```cpp
#ifdef _WIN32
    HANDLE h = ::OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (!h) return false;                       // <-- access-denied == not-found
#else
    const int rc = ::kill(pid, 0);
    if (rc == 0) return true;
    if (errno == EPERM) return true;            // exists, but no permission
    return false;
#endif
```

The POSIX branch distinguishes **"exists but I may not signal it"** from **"does not
exist."** The Windows branch does not. `OpenProcess` returns NULL both when the
process is gone (`ERROR_INVALID_PARAMETER`) and when it exists but the caller lacks
rights to query it (`ERROR_ACCESS_DENIED`) -- another user's process, or one at a
higher integrity level. Both are read as dead, and a dead owner's lock is
force-removed.

**Consequence:** on Windows, in a genuinely multi-user deployment, process B can
declare process A's live lock stale and take it. That is AIF-116's failure mode --
a live lock seen as free -- reached by a different route. `USE ... AGAIN`'s own notes
say record locking arbitrates "per the multi-user model", so multi-user is a
supported condition, not an exotic one.

**The shape of the fix is already in the file**, four lines below: discriminate the
error, as POSIX does.

```cpp
if (!h) return ::GetLastError() == ERROR_ACCESS_DENIED;
```

**This lane has not made that change and must not.** `xbase::locks` is AIF-116's
area. This is reported for relay, source-evidenced only: it is untestable from here,
needing Windows execution and two accounts, and this sandbox has neither. Same-user
same-session callers are unaffected, which is why every test to date passes.

## 5. Still open

- **pid reuse makes a lock immortal.** Liveness is pid-only; `ms=` is written and
  never read back. A dead owner whose pid is recycled by any unrelated live process
  looks permanently alive, and the lock is never reclaimed. The failure direction is
  **availability, not correctness** -- the table wedges until `force_unlock_table`,
  it does not lose exclusion -- which is the safe way round, and `ms=` is already
  sitting in the file if this ever needs fixing. Not tested: pid reuse cannot be
  scheduled on demand.
- **Record-granularity reclaim is untested.** R48's bare `LOCK` / `UNLOCK` pair has
  still never run against the binary, in this ruling or R50.
- **One area, not a domain.** Unchanged from R50.7: the all-or-nothing acquisition
  across a relation set, and its rollback, are proven only against a recording sink.
- **Nothing reclaims on the frontend's behalf.** The runtime refuses a busy domain
  (R47) and the engine reclaims dead owners, but a UIDEF frontend that is refused has
  no way to ask *why* -- "held by a live peer" and "held by a corpse the engine has
  not yet noticed" are the same refusal. Whether the DSL should expose that is the
  owner's.

## 6. Good Neighbor note

- **What changed.** New file `tools/uidef/lock_reclaim_wsl.sh`. **No code changed in
  this ruling** -- it is a measurement plus one cross-lane finding.
- **Whose area.** `src/xbase/xbase_locks.cpp` is AIF-116's and **was read, not
  touched.** Section 4 is a report for the maintainer to relay, with a suggested fix
  this lane has deliberately not applied. The harness copies its table to a scratch
  directory, so no `.lock` sidecar is created anywhere in the repository.
- **What authorization.** Maintainer (member.derald), standing in-session, under the
  agreed split: PowerShell for doc work, WSL for testing and dev.
- **How to verify or undo.** Verify: `bash tools/uidef/lock_reclaim_wsl.sh` from the
  repo root in WSL after `./wslbuild.sh`; both verdict lines must read True. Undo:
  the file is a test and deleting it changes no behaviour.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/lock_reclaim_wsl.sh
git add docs/maintenance/AIF120_LOCK_RECLAIM_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R51 -- crash reclaim proven both ways; reported to AIF-116 that the Windows liveness branch reads access-denied as dead"
```
