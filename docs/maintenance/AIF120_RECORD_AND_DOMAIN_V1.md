---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-060
  recorded_at_utc: 2026-08-19T22:45:00Z
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
    baseline_commit: 9852b0a59
  authorization:
    requested_by: maintainer (member.derald), standing in-session -- the three lock
      claims R48, R50 and R51 left proven only against a recording sink.
  report:
    path: docs/maintenance/AIF120_RECORD_AND_DOMAIN_V1.md
    kind: ruling
  cross_lane_finding:
    lane: AIF-116
    kind: runtime_observed
    summary: >
      try_lock_table succeeds while another process holds a record lock on the same
      table. Both processes then believe they hold the row exclusively. VFP's FLOCK()
      refuses in this situation.
---

# AIF-120 -- R52: record granularity is real, the rollback works, and a table lock does not exclude a record lock

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Three claims had been asserted against a recording sink and never against the
engine: R48's record granularity, R48.4's rollback argument, and the domain itself
("one area, not a domain", R50.7 and R51.5). Two hold. The third run found a defect
that makes R48.3's advice wrong.

## 1. Record granularity is real -- runtime-proven

```
  holder has record 1. Another process asks for record 1:
      . LOCK: failed (lock exists).
      . Table: unlocked
      Record 1: LOCKED (owner Grimwood:21080:1787170784963)
  ...and for record 5:
      . LOCK: record 5 locked.
      Record 5: LOCKED (owner Grimwood:21100:1787170786983)
```

Both halves are needed. The refusal alone is equally satisfied by a table lock
wearing a record lock's name; only granting record 5 while record 1 is held shows
the granularity is genuine.

## 2. R52.1 -- a held RECORD does not block a TABLE lock

```
      . LOCK: table locked.
      . Table:  LOCKED (owner Grimwood:21109:1787170787044)
      Record 1: LOCKED (owner Grimwood:21080:1787170784963)
```

One process holds the whole table. Another holds record 1. **Both believe they have
exclusive access to that row.** `try_lock_table` consults the table sidecar and never
the record sidecars.

VFP's `FLOCK()` fails when another user holds any record in the file. That is not a
stylistic difference: the whole point of a file lock is that it subsumes the record
locks beneath it.

### What it costs this lane

R48.3 ruled that `table` stays the default because it is **the conservative
choice** -- a handler that scans an area needs all of it. That reasoning silently
assumed coarser subsumes finer. It does not. A UIDEF handler scanning under a table
lock can be reading rows another process is actively editing under a record lock,
which is the corruption class R26 exists to prevent, arriving through the door R48
recommended.

**R48.3 is corrected, not withdrawn.** `table` remains the default, because it is
still strictly better than `record` for a scanning handler and no combination
available to a frontend closes the hole -- taking both verbs would still cover one
record. What changes is the claim attached to it: `table` is conservative **against
other table lockers**, and that is all. The limitation is now recorded in
`uidef_runtime.py` at the line where the granularity is chosen, not only here.

**The engine defect is reported, not fixed.** `xbase::locks` is AIF-116's area.
This lane observed it and stops there.

## 3. R48.4's rollback argument, finally run

```
  P2 (still running) attempted both areas and rolled back:
      . LOCK: table locked.          <- ENROLL taken
      . LOCK: failed (lock exists).  <- STUDENTS refused
      . UNLOCK: table unlocked.      <- ENROLL released
      . Table: unlocked
  a third process now asks for ENROLL, while P2 is STILL ALIVE:
      . LOCK: table locked.

  C0 P2 actually held the first area               : True
  C  rollback released the first area              : True
```

`C0` exists because `C` is meaningless without it: if P2 never took ENROLL there was
nothing to roll back, and P3's success would prove only that ENROLL was free all
along. **A test whose subject may not have happened needs a witness that it did.**

P2 is alive when P3 acquires, so process exit cannot explain the release (R50.2).

## 4. Correction 35, and the design gap it uncovered

The first run reported `C: False`. That was my harness. `USE` opens into the
**current work area**, so issuing it twice replaced ENROLL with STUDENTS in area 0.
The rollback's `SELECT ENROLL` then had nothing to select, `UNLOCK TABLE` released
the current area -- STUDENTS, which P2 never held -- and ENROLL stayed locked.

The mistake surfaced something worth more than the mistake:

> **The provider emits `SELECT <alias>`, which presumes every alias in the domain is
> already open in a work area of its own. Nothing in the runtime, and nothing in the
> contract, says who issues the `USE`.**

R47.2 defined the acquire sequence, R48 gave it granularity, R49 moved it into both
runtimes, and all three shipped that precondition unstated. The document's `SOURCE`
names `Alias` and `Table` for exactly this purpose (R36), so the information is
present; what is missing is the ruling that says the frontend opens each area before
the first handler fires, and what happens when a `Table` does not resolve. Gate 11
already flagged the second half -- fix 2 of its five: *"Define BINDING's syntax, and
require refusal when SOURCE.Table does not resolve."*

**This is the next unit** and it is a contract question, not a runtime one.

## 5. Also observed: a release you do not hold reports success

`UNLOCK TABLE` against a table this process does not hold printed `UNLOCK: table
unlocked.` `remove_if_owned` returns true when the sidecar does not exist. Benign in
itself, but it means **the provider cannot detect a failed release** -- every
`unlock` looks identical whether it did anything or not. R47's provider ignores the
return value, which is now a decision rather than an oversight.

## 6. Evidence tier

**runtime-proven** for sections 1, 2 and 3, against
`dottalkpp/bin-wsl-lean/dottalkpp` built from the current tree, three live processes,
real sidecars.

## 7. Still open

- **The `USE` precondition.** Section 4. Next unit.
- **Table-vs-record in the other direction is untested.** This run took a table lock
  while a record was held. Whether a record lock succeeds while another process holds
  the table has not been run, and it is the same defect's mirror.
- **pid reuse**, unchanged from R51.5.
- **Gate 11's five contract fixes**, untouched since R28.
- **`SET REPROCESS` and per-handler granularity have no fields.** Owner's.

## 8. Good Neighbor note

- **What changed.** `tools/uidef/uidef_runtime.py`: a comment at the granularity
  choice recording that `table` is conservative only against other table lockers.
  New: `tools/uidef/lock_record_domain_wsl.sh`.
- **Whose area.** AIF-120's own. `src/xbase/xbase_locks.cpp` was **read, not
  touched**; section 2 is reported to AIF-116 for relay. The harness copies both
  tables to a scratch directory, so no `.lock` sidecar is created in the repository.
- **What authorization.** Maintainer (member.derald), standing in-session, under the
  agreed split: PowerShell for doc work, WSL for testing and dev.
- **How to verify or undo.** Verify: `bash tools/uidef/lock_record_domain_wsl.sh`
  from the repo root in WSL; A1, A2, C0 and C must be True and B False until the
  engine changes. Undo: the code change is a comment; the harness is a test.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/uidef_runtime.py
git add tools/uidef/lock_record_domain_wsl.sh
git add docs/maintenance/AIF120_RECORD_AND_DOMAIN_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R52 -- record granularity and the rollback proven; a table lock does not exclude a record lock, so R48.3's conservative default was not"
```
