---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-028
  recorded_at_utc: 2026-08-19T09:40:00Z
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
    baseline_commit: 8de1b655c
  authorization:
    requested_by: maintainer (member.derald), in-session, "I just woke up an hour ago ---
      go go go!" -- taking the second item in the queue named at the end of the previous
      work: R11.4's serialization rule, which nothing had ever contended.
  report:
    path: docs/maintenance/AIF120_SERIALIZATION_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R21: serialization is per handler, and navigation is the trigger

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

## 0. What was untested, in my own words

`AIF120_DISPATCH_RUNTIME_V1.md` section 5 recorded two gaps against itself:

> **No contention.** A single worker fired once. R11.4's serialization rule --
> mutating work serialized per workspace -- is untested; nothing competed.

> **No lifetime test.** R11.4 also says destroying a container cancels the work
> its handlers queued. The window was destroyed after the worker finished, so
> the cancel path never ran.

Both are now runtime-proven, and both changed what R11.4 should say.

## 1. The experiment

`tools/uidef/contend_test.py` models one DBF work area as a `Workspace`: a record
pointer, a pending `REPLACE` buffer and an order, all of them **workspace** state
rather than call state. That is the entire reason R11.4 exists -- two handlers in
one work area share one pointer.

The table under test is `dottalkpp/data/dbf/vfp/STUDENTS.dbf`, the same
200-record table VFP 9 opened in this lane. Single-threaded truth: **200
students, GPA sum 588.74, mean 2.94.**

Two handlers, each a multi-operation transaction:

| handler | what it does | mutates? |
| --- | --- | --- |
| `TotalGpa` | `GO TOP`, then `read` + `SKIP` to the end, summing `GPA` | no |
| `BumpGpa` | `SEEK`, buffered `REPLACE`, `COMMIT` | yes |

Three lock modes, because the interesting result is not "a lock fixes it":

| mode | what locks |
| --- | --- |
| `none` | nothing |
| `per-op` | every cursor operation -- the naive fix |
| `per-handler` | the whole handler body -- R11.4 as written |

## 2. Measured -- 200 trials per mode

| mode | wrong walk | lost write | 
| --- | --- | --- |
| `none` | 200/200 | 200/200 |
| `per-op` | 200/200 | 199/200 |
| `per-handler` | **0/200** | **0/200** |

Transcript: `docs/maintenance/evidence/AIF120_contend.txt`.

Reproduced on two machines and two interpreters -- the container that authored it
and the maintainer's own workspace, resolving `STUDENTS.dbf` from the repo with no
environment override. Same 200/200, 200/200, 0/200.

## 3. R21.1 -- the unit of serialization is the handler, not the operation

**Locking every cursor operation is worth nothing.** `per-op` scored 200 of 200
wrong walks, identical to no lock at all. A walk is `GO TOP` plus 200 `SKIP`s
plus 200 reads; making each of those 401 operations individually atomic does not
make the walk atomic. The other handler's `SEEK` lands between two of them and
takes the walk with it.

This is the clause a target will get wrong, because per-operation locking is the
obvious implementation and it looks like it should work. R11.4 must say
*handler*, and now does.

## 4. R21.2 -- navigation is the trigger, not mutation

R11.4's heading says "**Mutating** work is serialized per workspace." Its body
says "commands that move the record **pointer** or change area, order, filter,
relation, lock or buffer state." The body is right and the heading is mine to
correct.

The measurement that separates them: run `BumpGpa` with its buffer held for
**0 ms**, so it never gives navigation a chance to discard the write.

| buffer held | lost write | wrong walk |
| --- | --- | --- |
| 0.000 ms | **0/200** | **200/200** |
| 0.050 ms | 197/200 | 200/200 |
| 1.000 ms | 200/200 | 200/200 |

The write survives. The walk is still wrong every single time. **A handler that
writes nothing at all still corrupts a concurrent walk, because `SEEK` alone
moves the shared pointer.** A target that serializes only its mutating handlers
has implemented the heading and not the rule.

## 5. R21.3 -- the failure is a plausible answer, not an error

This is the part that decides how much the rule is worth. Forty unserialized
trials, and what the walk actually reported:

| | students | GPA sum | mean |
| --- | --- | --- | --- |
| truth | 200 | 588.74 | 2.94 |
| observed 30x | 100 | 291.54 | 2.92 |
| observed 9x | 101 | 295.13 | 2.92 |
| observed 1x | 111 | 325.16 | 2.93 |

`BumpGpa`'s `SEEK` landed on record 101 of 200 and the walk went with it, so the
walk reported **half the roster with a mean that is right to two significant
figures**. Nothing raised. Nothing was empty. No widget failed to populate.

R7 named the empty-box failure: a control that binds to nothing renders blank and
the user cannot tell. This is its sibling and it is worse -- **the full box with
the wrong number.** A blank box is a visible defect. "100 students, mean 2.92" is
a report someone acts on.

The test also carried a steal detector: a read whose record is not the one that
thread selected. Across roughly a thousand trials it fired **zero** times. The
window between a thread's own `SKIP` and its own read is too narrow to catch the
other thread's single `SEEK`. That null result is itself the finding: **the
handler cannot detect this from the inside.** There is no defensive check to
recommend. Serialization is the only remedy.

## 6. R21.4 -- a completion handler is delivered at most once, never exactly once

`tools/uidef/lifetime_test.py` destroys a Tk container **while** a worker is in
flight, which dispatch_test.py never did. Two runtimes, same worker:

| runtime | result |
| --- | --- |
| naive -- deliver the completion regardless | `TclError: invalid command name ".!frame.!label"` |
| scoped -- the pump drops a dead scope's completion | completion never ran; state `cancelled` |

The worker observed its cancel in both, at step 6 of 20, and returned early. But
the completion handler's whole job is to touch a widget, so delivering it to a
destroyed container is guaranteed to fail on the least thread-tolerant backend in
the tree.

So R11.3's "must name a completion handler" is a **production** obligation, not a
consumption guarantee. The table must name one; the target must not promise to
call it. A handler that only releases a resource in its completion leaks the
moment a window closes -- the release belongs to the container's lifetime, not to
the completion.

R11's dispatch states are now all three runtime-proven: `completed` (previous
run), and `cancelled` and `failed` here. `failed` was caught in the worker and
delivered as a state; the exception never crossed onto the UI thread.

Transcript: `docs/maintenance/evidence/AIF120_lifetime.txt`.

## 7. R21.5 -- the runtime's own pump is queued work and obeys the same rule

The first run of the lifetime test printed `invalid command name "...pump"`. My
completion pump reschedules itself with `after()`, and the pending callback
outlived the window that owned it -- the same defect the test was written to
prove, one level up, in the machinery doing the proving. Fixed by tracking the
`after` id and cancelling it on teardown.

Worth recording rather than quietly fixing: the rule is not about handlers. It is
about anything queued against a container, including the runtime's own plumbing.

## 8. What this changes

- R11.4's heading is corrected from "mutating work" to navigation-triggered. The
  heading in `AIF120_THREADING_RULING_V1.md` is left as written with a correction
  note above it, so the record shows what was ruled and when.
- The ledger's claim that the charter carries "rulings R1 through R20" was false --
  the charter stops at R12 and R13 onward have never been in it. Corrected while
  adding R21, rather than propagated.
- The charter's threading amendment gains R21.1 (handler granularity) as a
  conformance requirement, not advice.
- The design table is unchanged. **No new column.** `DISPATCH` already carries
  everything a target needs; every clause here is a target obligation. That is
  the right outcome for a portability rule -- it costs the table nothing.

## 9. Still untested

- **Two workers, not one worker and the UI thread.** Both handlers here ran with
  one on a worker and one driving the cursor directly. Two `worker` handlers
  contending is the same shape, but it has not run.
- **Contention across work areas.** R11.4 serializes "against one workspace".
  Two workspaces with a `SET RELATION` between them is a second sharing channel
  and nothing has touched it.
- **A real backend.** This is a Python model of a cursor, not `src/gui/`'s
  cursor. The model is faithful to the house rule it cites, but it is a model.
  Evidence tier: **runtime-proven for the rule, source-evidenced for the
  workspace semantics.**

## 10. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Explicit paths only; no `git add -A`. Review before staging -- the author does
not self-approve.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_SERIALIZATION_RULING_V1.md
git add docs/maintenance/evidence/AIF120_contend.txt
git add docs/maintenance/evidence/AIF120_lifetime.txt
git add tools/uidef/contend_test.py
git add tools/uidef/lifetime_test.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add docs/maintenance/AIF120_THREADING_RULING_V1.md
git diff --cached --stat
git commit -m "AIF-120: R21 -- serialization is per handler and navigation-triggered; R11.4 contention and lifetime runtime-proven"
```
