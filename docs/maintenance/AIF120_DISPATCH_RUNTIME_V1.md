---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-025
  recorded_at_utc: 2026-08-19T09:08:09Z
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
    baseline_commit: 6c08c5792
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "keep going" -- wiring
      a handler was the last named untested item, R11 and R14 having been parsed and
      printed but never invoked.
  report:
    path: docs/maintenance/AIF120_DISPATCH_RUNTIME_V1.md
    kind: measurement
---

# AIF-120 -- R11 and R14 verified at runtime, on the least thread-safe target available

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

**Evidence tier: `runtime-proven`.** Executed under `xvfb` in the agent's
container; thread identities compared at each call.
Test: `tools/uidef/dispatch_test.py`. Document: `tools/uidef/author_uidef.py`.

R11 was adopted from a shipped C++ contract and never invoked. R14 ruled that the
table carries handler references and never bodies, and nothing had resolved one.
Both are now exercised.

## 1. Why Tk

The charter's own threading table lists Tk as **"not thread-safe at all"** --
weaker than Win32's handle affinity, wx's `CallAfter`, or Qt's queued
connections. If R11's model holds there, the platforms with real marshalling
primitives are easier, not harder.

## 2. The document, and two firsts

The test runs against a **hand-authored** UIDEF document, not an import. That
exercises two things nothing had:

- **`PROVENANCE = authored`** -- every prior document was `imported`.
- **`FLOW` with no `ORIGIN` at all.** Contract section 5b recorded that `FLOW` had
  never been exercised because every imported document lands `FLOW = free` with an
  origin group. This document is `FLOW = column`, carries no `ORIGIN` on any row,
  and **renders**. That is the authored path R12 was ruled for, running for the
  first time.

It declares two handlers, one of each dispatch:

```text
Click = MarkUi / ui
Click = SlowWork / worker -> WorkDone
```

## 3. Result -- all three R11 clauses hold

```text
   MarkUi       on UI                    sets label directly -- legal, it is on the UI thread
   SlowWork     on worker(140172362688192) sleeping 0.25s; MUST NOT touch a widget
   WorkDone     on UI                    state=completed result='worked' -- touches the widget
```

| clause | claim | result |
| --- | --- | --- |
| **R11.1** | a `ui` handler runs on the UI-owning thread | **PASS** |
| **R11.2** | a `worker` handler runs off it | **PASS** -- distinct thread id |
| **R11.3** | completion marshals back to the UI thread | **PASS** |
| **R14** | handlers resolve by NAME against a target registry; nothing evaluated | **PASS** |

The marshalling primitive on Tk is a `queue.Queue` drained by `root.after(30, ...)`
on the main loop -- which is exactly what the charter's threading table predicted
for Tk (*"worker output returns through a queue and `after()` polling"*). The
generator needed **no** platform-specific knowledge from the table: `worker` plus
a completion name was sufficient.

## 4. Two refusals fired, which is the part worth keeping

R11.3 requires that a `worker` handler name a completion path, and R14 requires
that a handler name resolve. Both were implemented as refusals rather than
warnings, and both fire:

- a `DISPATCH = worker` with no `-> Completion` is **refused**, not silently run
  on the UI thread
- a handler name absent from the registry is **refused and named**, not eval'd

**Nothing in the table is executable.** `HANDLERS` carries `SlowWork`, a string;
the body lives in the target's registry. That is R14 working as designed -- and it
is why 86% of real form code navigating the object model does not matter here.
None of it crosses.

## 5. What this does not establish

- **One platform, one process, one document.** No wx, Qt, Win32 or browser.
- **No contention.** A single worker fired once. R11.4's serialization rule --
  mutating work serialized per workspace -- is untested; nothing competed.
- **No lifetime test.** R11.4 also says destroying a container cancels the work
  its handlers queued. The window was destroyed after the worker finished, so the
  cancel path never ran.
- **No error path.** The worker returned normally. `TaskState` `cancelled` and
  `failed` were never produced.
- **`FLOW = column` only.** `row` and `grid` remain unexercised.
- **Handlers were no-ops.** They logged a thread id; none touched real data.

## 6. Where this leaves the lane

Every ruling R1 through R18 now has either a measurement or a runtime behind it,
and the four gates the charter set out are addressed: 8 and 9 ruled, 10 drafted
and reconciled, 11 spiked on a second backend for both forms and menus.

The largest remaining hole is the one section 5b opened and this document only
partly fills: **`FLOW` works for authored documents and imports still cannot
produce it.** Until an importer can derive intent from coordinates, UIDEF has two
disjoint populations -- authored documents that use `FLOW`, and imported ones that
use `ORIGIN` -- and only the authored half is portable in the sense R12 intended.

## 7. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add tools/uidef/dispatch_test.py tools/uidef/author_uidef.py
git add docs/maintenance/AIF120_DISPATCH_RUNTIME_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R11 and R14 verified at runtime on Tk; FLOW and PROVENANCE=authored exercised for the first time"
```
