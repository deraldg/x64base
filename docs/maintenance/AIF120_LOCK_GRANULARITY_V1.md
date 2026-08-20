---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-056
  recorded_at_utc: 2026-08-19T19:50:00Z
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
    baseline_commit: aa2f2c178
  authorization:
    requested_by: maintainer (member.derald), standing in-session "next unit",
      following the "dogfood" ruling -- taking two of R47 section 5's open items.
  report:
    path: docs/maintenance/AIF120_LOCK_GRANULARITY_V1.md
    kind: ruling
---

# AIF-120 -- R48: record granularity, and the number the runtime must never write

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R47 left two open items that look separate and are one:

> *"The runtime only ever takes TABLE locks... Locking a whole table to edit one row
> is correct and coarse."*
> *"AIF-116's defect class... nothing has checked that a frontend running under a
> grouping locale does not re-enter that bug from the other side."*

They are the same item, because **the moment a frontend takes a record lock it starts
emitting a record number**, and a record number in a command is exactly what AIF-116
was.

## 1. The surface is real, and it is two lines of C++

`gui/uidef/lock_number_probe.cpp`, under a grouping locale set globally -- AIF-116's
own runtime condition:

```
  default-constructed ostringstream : LOCK 16,984
  imbued with classic()             : LOCK 16984
  std::to_string                    : LOCK 16984
  round-trip of the grouped form    : 16   <-- AIF-116
```

A default-constructed `std::ostringstream` picks up the global locale. Nothing about
that line looks dangerous, which is why AIF-116 shipped and why it fired on **every**
acquisition rather than intermittently.

## 2. Ruling R48.1: the record-granularity domain lock

DotTalk++'s own `LOCK` with no argument locks the **current record** of the selected
area (`src/cli/cmd_lock.cpp`: *"LOCK with no arguments locks the current record"*).
So the record-granularity domain lock is, for every area in the domain:

```
SELECT <alias>
LOCK
```

all-or-nothing, sorted on acquire and reversed on release, exactly as the table form.

**R26's closure is what makes this correct.** A relation has already moved every
child area's pointer to the matching row, so locking the current record of every area
in the domain locks precisely the row set the handler can reach -- which is the whole
reason R26 locks the closure and not the named area. Record granularity would be
unsound without it.

## 3. Ruling R48.2: the runtime never renders a number into a command

Not "render it carefully". Never render it.

Bare `LOCK` carries no number, so the AIF-116 surface is **absent** rather than
handled. `LOCK <n>` and `LOCK WHO <n>` do carry one, and the runtime has no reason to
use either -- it does not know record numbers, and the area it just selected does.

`gui/uidef/lock_provider_test.py` asserts this directly: every emitted command
except `SELECT <alias>` must contain no digit. `SELECT` is excluded because the alias
is the document's text, not something the runtime rendered.

```
commands carrying a runtime-rendered number: none
```

If a future need does force `LOCK <n>`, the number must go through the classic
locale, and that test fails until it does.

## 4. Ruling R48.3: table stays the default, and the choice is the owner's

```
table  acquire : SELECT enroll ; LOCK TABLE ; SELECT students ; LOCK TABLE
record acquire : SELECT enroll ; LOCK ; SELECT students ; LOCK
both   release : SELECT students ; UNLOCK ; SELECT enroll ; UNLOCK
```

Record granularity is **finer, not safer**. A handler that scans an area to aggregate
it -- `TotalGpa` in this lane's own fixtures -- needs the whole area; locking one row
while another process edits the rest gives a correct lock and a wrong answer.

The document does not say whether a handler scans or edits one row. `HANDLERS` is
`Click = Name / dispatch -> Completion` and has no place to put it. So the runtime
cannot infer the granularity, table stays the default because it is the conservative
one, and **whether a document should be able to declare per-handler lock granularity
is a schema question and therefore the owner's.**

## 5. Ruling R48.4: a refused acquisition leaves nothing behind

```
refuse second : returned False, rolled back 1 lock(s)
                (SELECT a ; LOCK TABLE ; SELECT b ; LOCK TABLE ; SELECT a ; UNLOCK)
```

If the second area refuses, the first is released before returning. A partial
acquisition that survives a refusal is worse than no locking: the lock is held by a
process that does not believe it holds it, and `xbase::locks` will not call it stale
because the owning process is alive. It would sit there until `force_unlock_table`.

## 6. Runtime-proven

`gui/uidef/lock_provider_test.py` exits 0 on four cases: verbs and order, all-or-
nothing rollback, no runtime-rendered numbers, and a provider refusal refusing the
handler rather than running it anyway (`handler ran=False`, one refusal, the
completion delivered as `refused`).

Regressions: `lock_semantics_test.py` four cases pass; R26's `locked_test.py`
unchanged at area 60/60 wrong and domain 0/60; R38's `adopt_test.py` and R39's
`scope_test.py` reproduce their R47-corrected results.

**Evidence tier: `runtime-proven` for what the runtime SAYS, `planned` for what the
engine does with it.** The provider has still never issued a real `LOCK` -- this
sandbox cannot build dottalk++. The test reads command text from a recording sink.
That is a real and useful thing to test, and it is not the same as the lock working.

## 7. Still open

- **Nothing has run against the binary.** Unchanged from R47.5 and it is the largest
  gap in both rulings. `tools/regression/lock_mutual_exclusion_regression.ps1` proves
  the engine; nothing proves the frontend's use of it.
- **Per-handler granularity has no field.** Section 4. Owner's call.
- **`SET REPROCESS` has no field either.** R47.5, unchanged.
- **The C++ provider has no test.** `uidef_rt.h` takes a `LockProvider` callable and
  nothing exercises one; the seam is proven on the Python side only. The C++ seam is
  seven lines and untested is untested.
- **A grouping locale has not been set in a live frontend.** The probe shows the
  surface in isolation. R33 gave this lane a codepage and locale story; the two have
  not been run together.

## 8. Good Neighbor note

- **What changed.** `gui/uidef/uidef_runtime.py`: `LockProvider` takes a
  `granularity` of `table` or `record` and emits `LOCK TABLE` or bare `LOCK`. New:
  `gui/uidef/lock_provider_test.py`, `gui/uidef/lock_number_probe.cpp`.
- **Whose area.** AIF-120's own. `xbase::locks` is AIF-116's and **nothing in `src/`
  or `include/` was touched**; the probe is a standalone demonstration that links
  nothing from the engine.
- **What authorization.** Maintainer (member.derald), standing in-session "next
  unit", under the "dogfood" ruling.
- **How to verify or undo.** Verify: `python3 gui/uidef/lock_provider_test.py`
  (exit 0, four cases) and `g++ -std=c++14 gui/uidef/lock_number_probe.cpp -o
  lock_number_probe && ./lock_number_probe`, which must print `LOCK 16,984` for the
  un-imbued stream and `16` for the round trip. Undo: the change is one constructor
  argument and one attribute; removing them restores R47's table-only provider.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/uidef_runtime.py
git add gui/uidef/lock_provider_test.py
git add gui/uidef/lock_number_probe.cpp
git add docs/maintenance/AIF120_LOCK_GRANULARITY_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R48 -- record granularity via the house's own bare LOCK, which carries no number and so has no AIF-116 surface"
```
