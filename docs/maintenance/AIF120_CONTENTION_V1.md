---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-068
  recorded_at_utc: 2026-08-20T05:00:00Z
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
    baseline_commit: 7569837ae
  authorization:
    requested_by: maintainer (member.derald), standing in-session -- "keep dogfooding
      the engine"; R59 section 5 named both cases.
  report:
    path: docs/maintenance/AIF120_CONTENTION_V1.md
    kind: ruling
---

# AIF-120 -- R60: two typed frontends contend, and the rollback path finally executes

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R59 closed with two gaps, both needing a second process: contention between typed
frontends, and the typed provider's rollback path, which had never run.

## 1. Both, in one sequence

Process A holds **only `students`** -- deliberately the *second* alias in the
provider's sorted order, so a contender acquires `enroll` first and must give it back.

```
CONTENDER owner=vm:22457:1787174988052
  before : students=LOCKED enroll=free
  resolve: enroll                          <- acquired
  resolve: students                        <- attempted
  provider: lock students: lock exists     <- refused by the ENGINE
  resolve: enroll                          <- rolled back
  handler ran      : no -- refused
  completion state : refused (domain busy)
  after  : students=LOCKED enroll=free

  C0  enroll acquired then released (resolved 2x)  : yes
  ROLLBACK: enroll released after the partial acquisition : yes
```

**R47's FLOCK semantics reach a typed frontend.** The handler does not run and the
completion is delivered as `refused` -- the application is told, rather than blocked
or silently starved.

**R48.4's argument executes.** It claimed a surviving partial acquisition is worse
than no locking, because `xbase::locks` will never call a live owner's lock stale.
The sequence above is that argument as behaviour: `enroll` taken, `students` refused,
`enroll` returned, and A's lock untouched throughout.

## 2. C0, and why the first two attempts proved nothing

**The rollback check is worthless without a witness that the acquisition happened.**
"`enroll` is free at the end" is equally satisfied by "`enroll` was never locked".
R52 learned this and this ruling had to learn it twice more.

- **Attempt 1** passed, and I nearly shipped it. It had no C0 at all.
- **Attempt 2** sampled `enroll` from a 2 ms timer. It reported `NO -- vacuous`, and
  it was right for the wrong reason: the holder's 3 s hold had expired against a 3 s
  sleep, so the contender arrived after release, **the handler RAN, and there was no
  contention to observe.** A green-looking run that tested nothing.
- **Attempt 3** sampled at 1 ms and still failed, because the acquire-fail-release
  window is microseconds. No sampler can see it.

The witness that works is inside the sequence rather than beside it: the **resolver**
is test code, and the provider must resolve an alias to act on it. `enroll` resolved
**twice** -- once to acquire, once to release -- is the rollback, observed.

Fifth flaky harness in this run. The pattern by now is specific: **a harness for an
asynchronous property fails in the same shapes the property does**, so its failures
are indistinguishable from findings until something inside the sequence testifies.

## 3. Evidence tier

**runtime-proven**, two processes, against `libxbase.a` from the current tree, wx
3.2.4, under `xvfb`. The holder holds 12 s against a 4 s delay so the contender
cannot arrive late -- the defect that produced attempt 2.

## 4. Still open, and one of them is now large

- **The mutation model is prior art this lane has not used.** The maintainer pointed
  at `cmd_commit.cpp`, `cmd_rollback.cpp`, `table_buffer.cpp`, `cmd_replace.cpp` and
  `cmd_calcwrite.cpp` while this was being written. x64base already has **buffered
  mutation with a write-ahead journal**: `TABLE ON` buffers with **no locks taken**,
  `COMMIT` fsyncs a redo log and a `C` marker before applying, `ROLLBACK` discards,
  and a crash replays. R21.1's "the lock spans the whole handler" is this lane's
  answer to a question the house answers with transactions. **That is R61**, and it
  is the sixth prior-art find.
- **`COMMIT` locks one record at a time** (`cmd_commit.cpp`: `if !try_lock_record:
  mark fail; continue`), so a commit is atomic against a *crash* and not against a
  concurrent *reader*, and a contended record is **skipped** -- a partial apply. The
  maintainer's own uncertainty -- *"table locking i think, but should be record
  locking only, i am not sure"* -- is a real open question and R61's subject.
- **Record granularity remains unsafe for writing handlers** (R57.2), untouched here.
- **The Tk backend still has no engine path** (R55.3).
- **R55.2 remains the owner's.**

## 5. Good Neighbor note

- **What changed.** New file only: `gui/uidef/wx_contend_registry.cpp`, with its
  build and two-process run line in the header comment. **No shipped code changed.**
- **Whose area.** AIF-120's own. The engine was linked against and read, never
  modified. Both tables are copies.
- **What authorization.** Maintainer (member.derald), standing in-session: "keep
  dogfooding the engine".
- **How to verify or undo.** Verify: the run line in the header; the contender must
  report `handler ran : no -- refused`, `C0 ... : yes`, and `ROLLBACK ... : yes`. If
  C0 says vacuous, the holder released too early -- lengthen the hold rather than
  believing the result. Undo: the file is a test.

## 6. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/wx_contend_registry.cpp
git add docs/maintenance/AIF120_CONTENTION_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R60 -- two typed frontends contend and the rollback path executes; the witness had to come from inside the sequence"
```
