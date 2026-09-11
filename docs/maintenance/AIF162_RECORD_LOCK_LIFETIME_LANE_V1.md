---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260911-COWORK-205
  recorded_at_utc: 2026-09-11T01:15:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260910-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 1c0669ead
  authorization:
    requested_by: owner (member.derald), in-session 2026-09-11. Asked about the
      two-pass BEFORE-trigger question, was told the veto fires before the
      record locks are taken, and answered with the model this lane exists for --
      "i don't see the problem, create the tuple, if successful, start recording
      table buffer changes, locking records and releasing them at commit or
      rollback" -- then authorized a lane for it and ran AIFgen.
    scope: |
      Lane charter for AIF-162 (record-lock-lifetime). DESIGN AND MEASUREMENT
      ONLY. No source change is authorized by this document.
      Write access exercised for this report:
        docs/maintenance/AIF162_RECORD_LOCK_LIFETIME_LANE_V1.md
        docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md (one row)
      NOT authorized here: any edit to src/xbase/xbase_locks.cpp,
      src/cli/cmd_commit.cpp or src/cli/table_state.cpp; any amendment to the
      AIF-160 charter's decision 6.3; any work on AIF-113.
  report:
    path: docs/maintenance/AIF162_RECORD_LOCK_LIFETIME_LANE_V1.md
    kind: lane-charter
---

# AIF-162 -- a record lock should live as long as the change does

    lane      : AIF-162 (record-lock-lifetime)
    claim     : coordination/aif/AIF-162.claim
    run       : AIFGEN-20260910-190858
    intake    : docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md
    owner     : member.derald
    steward   : member.ai.claude.cowork
    status    : CHARTERED. NOTHING IS BUILT. BLOCKED ON AIF-113 -- see section 5,
                which is the section to read if only one is read.
    opened    : 2026-09-11
    baseline  : 1c0669ead

## 1. The model

Owner, 2026-09-11:

> *"create the tuple, if successful, start recording table buffer changes,
> locking records and releasing them at commit or rollback."*

**Acquire the record lock when the change is STAGED. Hold it. Release it at
COMMIT or ROLLBACK.** Ordinary two-phase locking, and also what the xBase
lineage means by record locking: you lock the row you are editing, not the row
you are flushing.

## 2. What ships today, measured 2026-09-11

**Locks are taken at APPLY, per record, and released in the same loop.**
`apply_one_recno` (`src/cli/cmd_commit.cpp`) calls
`xbase::locks::try_lock_record(A, rn, ...)`, writes, then
`xbase::locks::unlock_record(A, rn)` before it returns. The lock's whole life is
one record's write.

**A record lock is a FILE.** `record_lock_path` (`src/xbase/xbase_locks.cpp:107`)
is `<dbf path> + ".lock." + <recno>` -- a sibling of the .dbf, one per locked
record, created `CREATE_NEW`/`O_EXCL` and removed on unlock.

**The BEFORE-trigger veto runs with NO record locks held.** The comment at the
fire site says the phase fires "after the locks are held", and the only lock
held there is an `InsertTableLockGuard`, taken *only when the transaction
contains an insert*. So a trigger answers about records that nothing is holding,
and the lock is taken later, inside apply.

**THERE IS THEREFORE ALREADY A VETO-TO-LOCK GAP, PER AREA, TODAY.** It is narrow
-- microseconds inside one loop -- and nothing has been reported against it. It
is named here because this lane is what closes it, and because the AIF-160
charter's section 8 reasoning assumed the locks were held.

## 3. What it costs -- and the reframing that matters

**THE FILE OPERATION COUNT DOES NOT CHANGE.** Today: one create and one delete
per record, inside apply. Under this model: one create at stage, one delete at
commit or rollback. **Same two operations per record. What changes is LIFETIME,
not volume** -- which is the opposite of the first objection anyone reaches for.

What does change:

| cost | measure |
|---|---|
| **hold duration** | user-scale. A record is locked from the edit to the COMMIT -- minutes in an interactive session, unbounded if a user walks away mid-transaction. **This is the real trade.** |
| **peak lock count** | `kMaxChanges` is 10,000 (build vectors), so one area's transaction can hold ten thousand `.lock.<recno>` files |
| **directory occupancy** | those files are SIBLINGS OF THE .dbf. `WORKSPACE OPEN <dir>` scans directories for tables, and `ERASE` sweeps same-stem sidecars -- neither was written with ten thousand lock siblings in mind. **An open question, not a blocker: see section 7.** |
| **deadlock** | possible in principle the moment locks span user time, and **ANSWERED ALREADY** -- see section 4 |

## 4. Deadlock is answered by a decision already taken

Holding locks across user time makes deadlock possible: two sessions staging
records in different orders.

**AIF-160 decision 6.3 kills it: REFUSE IMMEDIATELY.** If the lock is not free at
stage time, refuse the stage. No waiting means no cycle. And it is not a new
posture -- `src/cli/sqlsel_statement.cpp:3344` already refuses a table carrying
buffered changes from outside the transaction, in the very function that would
learn to stage many.

**A deterministic acquisition order is NOT required under this model**, which is
the opposite of what the AIF-160 charter says -- see section 6.

## 5. THE BLOCKING DEPENDENCY, AND ITS OWN PREDICTION HAS COME TRUE

**AIF-113 (`lock-release-recovery`, chartered 2026-08-15) owns the release path
this model needs, and it is still dead code.**

Its subject: nothing releases a lock except an explicit `UNLOCK`. Not `CLOSE`,
not `CLEAR`, not `USE`/`OPEN`, not `DbArea::close()`, not `~DbArea()`, **not
process exit**.

**Verified against the tree at `1c0669ead`, four weeks after that charter:**

```
release_held        -> ONE occurrence in the tree: its own declaration,
                       include/xbase_locks.hpp:122. No callers.
force_unlock_table  -> zero callers anywhere.
force_unlock_record -> zero callers anywhere.
```

**AND AIF-113 PREDICTED THE STATE THE TREE IS NOW IN.** Its row records that
AIF-113 and AIF-116 masked each other: leaked locks were being cleaned up *by*
AIF-116's broken stale detection -- the parse that read `pid=16,984` as `16`,
decided the owner was dead, and force-removed a live lock. It states that
repairing that parse alone leaves orphans **permanently unreclaimable, with no
exposed command to clear them**, and that one abandoned `LOCK TABLE` would wedge
that table for every process on the machine.

**AIF-116 is FIXED, at `fe42666e`. AIF-113 is not. That state is live.**

**IT IS SURVIVABLE TODAY FOR EXACTLY ONE REASON: LOCKS BARELY LIVE.** The orphan
window is the microseconds inside `apply_one_recno`, plus a user who types
`LOCK` and never `UNLOCK`.

**THIS LANE REMOVES THAT MITIGATION.** A session that stages five hundred edits
and crashes leaves five hundred permanently wedged lock files and nothing in the
product can clear them.

**So AIF-162 CANNOT SHIP BEFORE AIF-113.** Not "should coordinate with": the
release path this design calls for IS the dead function AIF-113 owns. AIF-113's
design option 1 is *`release_held` wired into area close*; this lane needs the
same function wired into commit and rollback. One mechanism, adjacent call
sites.

## 6. What this dissolves in AIF-160

**Decision 6.3's "deterministic acquisition order is still required" becomes
void.** It was written assuming a group commit must grab N areas' locks at commit
time. Under this model there is no acquisition phase at commit -- the locks were
taken incrementally as the user worked, and there is nothing left to order. The
refuse-immediately half of 6.3 survives and moves to stage time.

**Decision 6.5 (two-pass BEFORE triggers) becomes trivially right rather than
arguably right.** The veto pass asks about a set nothing else can touch, so the
answer cannot go stale between the asking and the writing. The cost argument
(one sweep and zero durable writes, against N-1 wasted fsyncs) still holds and
is now the lesser reason.

**AND THE NAME "TWO-PASS" SHOULD BE CORRECTED WHEREVER IT APPEARS:** it means two
passes over the AREAS, one veto and one prepare. **Each trigger is asked exactly
once.** Read as "triggers fire twice" it describes a cost that is not being
proposed and would be a fair reason to reject it.

**This lane is also the WRITE HALF OF ISOLATION**, which
`claude/STATUS_WHERE_A_TRANSACTION_STANDS_20260911.md` calls the largest
untouched leg with no lane behind it. That statement is superseded by this
document for writers; readers are untouched and remain uncovered.

## 7. Open, and not decided here

1. **WHICH VERBS STAGE.** The model says "start recording table buffer changes",
   so the lock is taken where a `ChangeEntry` is added. But `MULTIREP` direct-
   writes unconditionally (AIF-151, unbuilt) and bare `INSERT`/`UPDATE`
   (`src/cli/cmd_sql_insert.cpp`, `src/cli/cmd_sql_update.cpp`) write directly
   and stage nothing. **A transaction is only as isolated as the narrowest path
   into it** -- the same shape AIF-160 records for atomicity.
2. **TEN THOUSAND SIBLINGS.** Lock files sit beside the .dbf.
   `WORKSPACE OPEN <dir>` scans directories for tables and `ERASE` sweeps
   same-stem sidecars. Whether either copes with ten thousand `.lock.<recno>`
   files is **unmeasured**, and a lock subdirectory is an obvious alternative
   that changes `record_lock_path` and therefore AIF-150's proven publication
   protocol. Not chosen here.
3. **RELEASE ON THE FAILURE PATHS.** Commit and rollback are the stated release
   points. Partial commit, a trigger veto, a failed durable sync and a process
   crash each need a named answer, and three of the four are the AIF-113
   recovery path rather than this lane's.
4. **IDENTITY PRESSURE.** A lock that lives across user time makes "whose lock is
   this" a user-facing question rather than a diagnostic one. AIF-144 records
   five authorities answering "who am I" and a lock system that asks none of
   them. This lane does not fix that and should not mint a sixth.

## 8. Sequence

1. **AIF-113 lands.** Prerequisite, not this lane's work.
2. **Rule section 7 item 1** -- which verbs stage, and what the direct-write
   paths do meanwhile.
3. **Measure section 7 item 2** before choosing the lock path shape.
4. Acquire at stage, refuse immediately on contention.
5. Release at commit and rollback, with the failure paths named.
6. An arm. Two processes are the only honest instrument, and
   `src/tests/test_lock_protocol.cpp:371` is the harness shape -- whether it is
   wired to a build target is still unverified (AIF-160 section 7).

## 9. NOT CLAIMED

- **Nothing is built, measured at runtime, or authorized.**
- **NOT claimed that hold duration is acceptable.** Section 3 names it as the
  real trade and does not measure it. A shared-table workload and a single-user
  student session have opposite answers.
- **NOT a complete audit of the lock call sites.** AIF-113's row counts 43
  across 13 files; this charter read `apply_one_recno`, `try_lock_record`,
  `record_lock_path` and the three dead release functions, and no more.
- **NOT claimed that `src/xbase/lock_cleanup.cpp` is irrelevant.** It contains
  no `release_held` and no `unlock`, which is why it is not the release path;
  what it IS for was not read.
- **NOT claimed that readers gain anything.** This is write isolation. A
  concurrent reader can still observe a partial commit.
