---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-055
  recorded_at_utc: 2026-08-19T19:10:00Z
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
    baseline_commit: f8880f4db
  authorization:
    requested_by: maintainer (member.derald), in-session, "are you use x64base
      locking" then "dogfood", and an explicit ruling on contention semantics --
      "Refuse, like FLOCK()".
  report:
    path: docs/maintenance/AIF120_LOCK_SEMANTICS_V1.md
    kind: ruling
---

# AIF-120 -- R47: the runtime was not using x64base's locks, and the deadlock was mine

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

## 0. Correction 31, and it is the largest in this run

I built `LockDomains` on `threading.RLock` and `std::mutex`, proved things about it
across R21, R26, R37, R38 and R41, and never asked whether x64base had locking.

It does, and it always did:

| | |
|---|---|
| `include/xbase_locks.hpp`, `src/xbase/xbase_locks.cpp` | owner-aware table and record locks, `Owner` = `host:pid:nonce` |
| `src/cli/cmd_lock.cpp`, `src/cli/cmd_unlock.cpp` | the language surface: `LOCK TABLE`, `LOCK <n>`, `LOCK STATUS`, `LOCK WHO <n>`, `UNLOCK` |
| `tools/regression/lock_mutual_exclusion_regression.ps1` | a standing cross-process regression |
| `docs/maintenance/LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md` | AIF-116: a grouping locale wrote `pid=16,984`, `std::stoul` read `16`, every process saw every other process's lock as stale. Fixed at `fe42666e`. |

This is the same failure as the locale one, found the same way -- by the maintainer
asking. The lane's runtime has been a **simulation of locking running beside the
engine's own locks**, and `locked_test.py` says so in its own header without either
of us noticing: *"The runtime decides what each one locks."* It decided, and it
locked nothing.

## 1. The deadlock I found this morning does not exist in x64base

Before the maintainer's question I reproduced a textbook AB-BA hang in four seconds
-- two workers, each holding one domain and synchronously wanting the other -- and
added a `SecondDomain` guard that refused the second acquisition.

`xbase::locks::try_lock_table` is a **single non-blocking attempt**:

```cpp
bool try_lock_table(DbArea& a, const Owner& me, std::string* err) {
    const std::string lp = table_lock_path(a);
    if (!create_or_validate_owned(lp, me, err)) return false;   // no retry, no wait
    book()[&a].table = true;
    return true;
}
```

No path waits, so no circular wait can form. **The deadlock was a property of my
reimplementation, not of the system.** R26.3's argument was right about the engine
and I proved it wrong about a model the engine does not use.

The `SecondDomain` guard has been **deleted, not kept**. Try-semantics dissolve the
case rather than defend against it, and a guard that can never fire is a claim that
the thing it guards against is possible.

## 2. Owner ruling: refuse, like FLOCK()

Asked what a handler should do when its domain is busy, the owner ruled: **refuse**.

`FLOCK()` returns `.F.`; it does not queue. Everything this lane recorded about
contention before today described a blocking lock the engine does not have.

### R47.1 -- `LockDomains` is non-blocking and re-entrant by depth

`threading.Lock` taken with `blocking=False`; `std::mutex::try_lock`. Re-entry by the
*same* thread on the *same* domain is allowed above the lock by a per-thread depth
count, because a handler calling a handler on its own data is not contention and
R21.1 already says the lock spans the whole handler. A busy domain refuses, and the
completion is delivered with `state = 'refused'` so the application is told rather
than silently starved.

### R47.2 -- the data lock goes through the house's own verbs

`LockProvider` acquires a domain by issuing, for every area in it:

```
SELECT <alias>
LOCK TABLE
```

all-or-nothing, releasing what it took on partial failure, and `SELECT <alias>` +
`UNLOCK` to release. Aliases are taken in sorted order -- defence in depth, not the
reason it is safe; the reason is that `try_lock_table` never waits.

Left unset, the runtime gives **in-process exclusion only**. That is the honest
default for a generated frontend with no engine attached, and it is now labelled as
such instead of being mistaken for a data lock.

### R47.3 -- both layers are necessary, and neither is sufficient

`Owner` is one token per process (`host:pid:nonce`). Two UIDEF handlers in the same
frontend share it, so the engine lock alone gives cross-process exclusion and **no
intra-process exclusion at all** -- R21.1 would not hold inside a single app. The
in-process latch alone protects nothing from another process. The runtime takes the
latch first (cheap, fails fast), then the engine lock, and releases in reverse.

## 3. Runtime-proven, and identical on both targets

```
                      Python (threading)                 wx C++ (std::thread)
AB-BA                 blocked=0  completions=2           blocked=0, both complete
one domain            enter / complete refused /         slow enter / complete refused /
                      leave / complete completed         slow leave / complete completed
unrelated domains     overlapped=True (A in B in         unchanged
                      B out A out)
same-domain re-entry  inner ran, refusals=0              inner ran, refusals=0
```

`gui/uidef/lock_semantics_test.py` exits 0. The wx build exits 0 on both modes.

## 4. What this changes in already-shipped rulings

- **R38 and R41 recorded queueing.** Their timelines showed the second handler on a
  shared domain running *after* the first. It is now refused and never runs.
  `adopt_test.py`'s R21.1 assertion ("two worker handlers on one lock domain
  OVERLAPPED: False") still passes -- but for a different reason, and the reason is
  the interesting part. Both rulings need their section 3 evidence re-read against
  this one.
- **R26's conclusion survives, and is not hollow.** Measured over 20 trials:

  ```
  area     workers started=40  refused-for-busy=0     -> 60/60 wrong
  domain   workers started=40  refused-for-busy=20    ->  0/60 wrong
  ```

  The area reading lets both handlers through and corrupts every time; the domain
  reading refuses exactly one per trial. The safety now comes from **refusal**, not
  from serialization. That distinction matters to an application author: with a
  queue, both units of work eventually happen. Under `FLOCK()` semantics **the
  second one does not happen**, and the app must decide what to do about it.
- **R21.1 needs a sentence.** It says work is serialized at handler granularity.
  Under R47 it is *excluded* at handler granularity. Serialized implies eventual.

## 5. Still open

- **The provider is source-evidenced, not runtime-proven.** This sandbox cannot
  build dottalk++, so `LockProvider` has never issued a real `LOCK TABLE`. The
  in-process half is runtime-proven on both targets; the engine half is code that
  matches a header. **It should not be described as proven until it runs against the
  binary**, which needs the maintainer's tree.
- **`SET REPROCESS` has no UIDEF field.** The owner ruled for plain refusal, and real
  VFP lets a program ask for N retries or a timeout. A document cannot express that
  today. If it should, it is a schema change and therefore the owner's.
- **The runtime only ever takes TABLE locks.** `xbase::locks` has record locks and
  the contract's `BINDING` names a field, not a table. Locking a whole table to edit
  one row is correct and coarse.
- **AIF-116's defect class.** The owner string is written through a stream whose
  imbuement matters. R33 gave this lane a codepage; nothing has checked that a
  frontend running under a grouping locale does not re-enter that bug from the other
  side.
- **No cross-process test exists for the frontend.** `lock_mutual_exclusion_regression.ps1`
  tests the engine. Nothing runs two generated frontends against one table.

## 6. Good Neighbor note

- **What changed.** `gui/uidef/uidef_runtime.py` and `gui/uidef/uidef_rt.h`:
  non-blocking domain acquisition, per-thread re-entry depth, refusal delivered as a
  completion state, and a `LockProvider` seam that issues the house's own
  `SELECT`/`LOCK TABLE`/`UNLOCK`. The `SecondDomain` guard added earlier the same day
  was removed. New: `gui/uidef/lock_semantics_test.py`,
  `gui/uidef/wx_lock_registry.cpp`.
- **Whose area.** `xbase::locks` is AIF-116's and the engine's; **nothing in
  `src/` or `include/` was touched.** This lane changed only how its own runtime
  asks. The provider seam is a call site, not a modification.
- **What authorization.** Maintainer (member.derald), in-session: "are you use
  x64base locking", "dogfood", and the explicit contention ruling "Refuse, like
  FLOCK()".
- **How to verify or undo.** Verify: `python3 gui/uidef/lock_semantics_test.py`
  (exit 0, four cases), and for wx build `scopes.cpp` against
  `gui/uidef/wx_lock_registry.cpp` and run with `abba` and `contend`. Undo: the
  change is confined to `LockDomains`/`Hold` and the two dispatch branches;
  restoring `threading.RLock` + `with lock` restores queueing, and with it the
  deadlock in section 1.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/uidef_runtime.py
git add gui/uidef/uidef_rt.h
git add gui/uidef/lock_semantics_test.py
git add gui/uidef/wx_lock_registry.cpp
git add docs/maintenance/AIF120_LOCK_SEMANTICS_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R47 -- the runtime dogfoods xbase::locks; FLOCK() refuses rather than queues, and the deadlock was in my reimplementation"
```
