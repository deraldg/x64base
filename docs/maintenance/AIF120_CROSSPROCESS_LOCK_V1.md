---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-058
  recorded_at_utc: 2026-08-19T21:15:00Z
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
    baseline_commit: 8969de78e
  authorization:
    requested_by: maintainer (member.derald), in-session -- "remember we have wsl as
      an option too", then built the binary and ran the harness.
  report:
    path: docs/maintenance/AIF120_CROSSPROCESS_LOCK_V1.md
    kind: ruling
---

# AIF-120 -- R50: the engine finally heard it, and the release verb was wrong

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R47, R48 and R49 each closed with the same admission, in the same words: both
providers are proven to **say** the right thing and the engine has never **heard**
it. The maintainer's "remember we have wsl as an option too" is what closed it. The
first thing the engine said back was that the release verb was wrong.

## 1. R47's ruling holds against the shipped binary

```
=== B issues the frontend's acquire sequence while A holds ===
    . LOCK: failed (lock exists).
    . Table: LOCKED (owner Grimwood:8084:1787166819756)
```

Refused, immediately, not queued. **FLOCK semantics, runtime-proven.** Every
concurrency claim in this lane from R21 to R49 rested on a model until this line.

## 2. Correction 33: the release verb, wrong in three shipped rulings

`UNLOCK` with no arguments unlocks the current **record**. `UNLOCK TABLE` releases
the table lock. `src/cli/cmd_unlock.cpp` says exactly that in its usage block:
*"UNLOCK with no arguments unlocks the current record."*

R47.2 shipped `SELECT <alias>` + `UNLOCK` as the release sequence. R48 and R49
carried it into both runtimes. The default granularity is `table`. So the shipped
default acquired a table lock and **never released it**:

```
    . LOCK: table locked.
    . UNLOCK: record 1 unlocked.
    . Table: LOCKED (owner Grimwood:5383:1787165951581)     <-- still held
```

R48.4 argued, at length and one ruling before shipping this, that a lock held by a
process which does not believe it holds one is worse than no locking, because
`xbase::locks` will never call a live owner's lock stale. The same sentence condemns
this.

**How it got in.** I read `cmd_lock.cpp`'s usage block to learn `LOCK TABLE`, and
then assumed the release side was symmetric instead of reading `cmd_unlock.cpp`'s.
The engine documents both, adjacently, in the same format. This is not a subtle
defect and no amount of testing what the runtime *says* would have found it -- both
provider suites asserted the string `UNLOCK` and passed, because they were checking
the runtime against my belief rather than against the engine.

### Ruling R50.1: the release verb pairs with the acquire verb

| granularity | acquire | release |
|---|---|---|
| `table` (default) | `LOCK TABLE` | `UNLOCK TABLE` |
| `record` | `LOCK` | `UNLOCK` |

Both runtimes, both test suites, and the rollback path on partial acquisition.

## 3. Ruling R50.2: a proof must exclude the incidental mechanism

The first harness had three steps: A holds, B is refused, A exits, B succeeds. Every
one passed. **It proved nothing about release**, because B's success in step 3 is
equally explained by A's process exiting -- and `release_held` runs at shutdown.

Step 4 is the one that means something. A acquires, releases, and **stays alive**
with its stdin held open on a fifo, while B attempts the same acquire:

```
    --- B, with A still running ---
    . LOCK: table locked.
    . Table: LOCKED (owner Grimwood:8138:1787166828836)
    --- A, which never exited during B's attempt ---
    . UNLOCK: table unlocked.
    . Table: unlocked
```

B's success now has exactly one explanation. **The general form: when a test asserts
that mechanism X released a resource, the test must keep every other release path
shut for the duration.** Process exit, scope destruction and garbage collection are
all willing to make a broken teardown look correct.

## 4. Correction 34: the harness nearly measured a binary nobody ships

The first version chose its binary by taking the first hit from a fixed list. That
list contained `build/wsl-core-vcpkg/src/dottalkpp` (2026-08-10, predating AIF-116's
fix at `fe42666e`) and `dottalkpp/bin-wsl/dottalkpp` (2026-07-30), and did **not**
contain `dottalkpp/bin-wsl-lean/`, which is where `./wslbuild.sh` actually stages.
Run as shipped, it would have selected the July binary, run cleanly, and produced a
confident table about a build nobody ships.

It now prints every candidate with its timestamp, takes the newest, and refuses any
binary older than `src/xbase/xbase_locks.cpp`. **A fallback that picks quietly is a
fallback that picks wrong.**

## 5. A note owed to AIF-116

The owner strings in this run are `Grimwood:8084:1787166819756` -- pid and a 13-digit
nonce, both **ungrouped**. Under the locale-grouping defect they would read
`8,084` and `1,787,166,819,756`, and `std::stoul` would parse the pid as `8`.

That is an independent confirmation of `fe42666e` from outside AIF-116's own lane,
obtained for free by printing the owner string in a test about something else. It is
offered to that lane as corroboration, not as a claim on their area.

## 6. Evidence tier

**runtime-proven**, against `dottalkpp/bin-wsl-lean/dottalkpp` built from the current
tree on Ubuntu 24.04, two live processes, real `.lock` sidecars. This is the first
`runtime-proven` claim in the lane that involves the engine rather than a model of it.

## 7. Still open

- **Crash reclaim is untested.** Step 4's B acquired and exited without releasing,
  leaving `STUDENTS.dbf.lock` behind. Whether the liveness check reclaims it is
  exactly the path AIF-116 broke, and this run does not exercise it. A frontend that
  dies holding a domain is not a hypothetical -- R21.4 exists because containers go
  away.
- **Only `table` granularity was exercised.** R48's bare `LOCK` / `UNLOCK` pair has
  not been run against the binary.
- **One area, not a domain.** The harness locks `STUDENTS` alone. R26's whole point
  is the transitive closure, and the all-or-nothing acquisition across two related
  areas -- including rollback when the second refuses -- has been proven only against
  a recording sink.
- **`--version` is not a supported option** (`Error: unknown option: --version`). Minor,
  but the harness asks for it and the banner it wanted is printed at startup instead.
- **`SET REPROCESS` and per-handler granularity still have no fields.** Owner's,
  unchanged from R47 and R48.

## 8. Good Neighbor note

- **What changed.** `tools/staging/check_cited_paths.py` and
  `tools/uidef/cite_check.py` gained `.sh` and `.ps1` to their extension list --
  this ruling cites a `.sh` harness and the check silently ignored it, which is
  the blind spot R42 and R43 exist to close.
  `tools/uidef/uidef_runtime.py` and `tools/uidef/uidef_rt.h`: the
  release verb pairs with the acquire verb. `tools/uidef/lock_provider_test.py` and
  `tools/uidef/wx_provider_registry.cpp` assert the pairing. New:
  `tools/uidef/lock_crossproc_wsl.sh`.
- **Whose area.** AIF-120's own. Nothing in `src/` or `include/` was touched. The
  harness copies its table to a scratch directory, so no `.lock` sidecar is created
  anywhere in the repository. The AIF-116 corroboration in section 5 is offered to
  that lane, not filed against it.
- **What authorization.** Maintainer (member.derald), in-session: "remember we have
  wsl as an option too", followed by building the binary and running the harness.
- **How to verify or undo.** Verify: `./wslbuild.sh` then
  `bash tools/uidef/lock_crossproc_wsl.sh` from the repo root in WSL; step 2 must
  show `LOCK: failed (lock exists)`, and step 4 must show B acquiring while A is
  still running. Undo: reverting `unverb` to the literal `UNLOCK` in both runtimes
  restores the leak in section 2, which no in-process test detects.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/uidef_runtime.py
git add tools/uidef/uidef_rt.h
git add tools/uidef/lock_provider_test.py
git add tools/uidef/wx_provider_registry.cpp
git add tools/uidef/lock_crossproc_wsl.sh
git add tools/staging/check_cited_paths.py
git add tools/uidef/cite_check.py
git add docs/maintenance/AIF120_CROSSPROCESS_LOCK_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R50 -- cross-process locking proven against the real binary; the release verb was unlocking the record, not the table"
```
