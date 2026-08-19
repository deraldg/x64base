---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-045
  recorded_at_utc: 2026-08-19T13:10:00Z
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
    baseline_commit: d431fd34c
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- the
      contract's open item 15, which this session put there: "Nothing takes a lock."
  report:
    path: docs/maintenance/AIF120_RUNTIME_V1.md
    kind: ruling
---

# AIF-120 -- R37: the concurrency rules leave the models and enter the runtime

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Every concurrency rule this lane produced was proven in a **model**.
`contend_test.py` and `relate_test.py` build a `Workspace` and drive it by hand;
`dispatch_test.py` fires handlers at a Tk window that owns no data. The contract's
open item 15 states the consequence: *"Nothing takes a lock."*

`tools/uidef/uidef_runtime.py` is the missing piece -- the runtime a generated
frontend actually runs on, with the lock domains read from the document's own
`SOURCE` (R36).

## 1. The experiment

Same two handlers as R26, same real tables, but fired through `Runtime.fire()` as
`DISPATCH = worker` with completions, exactly as a table would declare them. The
runtime decides what each one locks. One constructor argument selects between the
two readings:

| granularity | what it locks | which rule |
| --- | --- | --- |
| `area` | the work area the handler **names** | R11.4 as originally written |
| `domain` | the **relation set** | R26 |

The wrong reading is kept runnable **on purpose**. A runtime that can be configured
wrong on request is how the difference gets shown in the generated app rather than
in a model.

## 2. Measured, 60 trials each

```
lock domains read from the document's SOURCE: [['enroll', 'students']]

granularity=area    wrong 60/60   another student's rows 60/60
granularity=domain  wrong  0/60   another student's rows  0/60
```

**Same document, same two `worker` handlers, same completions, one constructor
argument between a correct frontend and a corrupt one.** And the domains were not
configured -- they were read from `SOURCE`, which R36 taught the importer to write
one commit earlier.

## 3. The rest of the dispatch contract, in the same runtime

```
R21.4 container destroyed mid-flight: completion DROPPED, not delivered
failed state reached on the UI thread : [("ValueError('handler raised')", 'failed')]
R11.3 worker with no ON_COMPLETE      : refused
R20   host capability not provided    : refused
```

R21 proved these against a Tk window; they now hold in the runtime a generated app
would embed, and the completion pump asserts its own thread identity rather than
trusting it.

## 4. What this changes

- **Open item 15 is closed for locking.** A generated frontend can take the right
  lock, and the document tells it which one.
- The runtime is **backend-independent** -- it imports no toolkit. Tk, HTML and the
  character grid can all use it, which is the first piece of this lane that is not
  written against a particular target.
- `R21.1`'s handler granularity is structural here rather than advisory: the lock
  is taken around `fn(scope)`, so there is no way to express per-operation locking
  without rewriting the runtime.

## 5. A defect of mine, found by running it on the maintainer's machine

`relate_test.py` resolved `STUDENTS.dbf` and `ENROLL.dbf` **beside itself**, which
worked only in the container it was written in. On the repo those tables live in
`dottalkpp/data/dbf/vfp/`, and both `relate_test.py` and the new `locked_test.py`
died with `FileNotFoundError` the first time they ran there.

`contend_test.py` already had the right pattern -- env override, then repo-relative,
then local -- and I did not follow it in the file I wrote next. **Third instance of
the same defect class this session**, after the `/tmp/gen` entries R23 swept out of
four tools and the absolute `CLASSLOC` in our own fixtures. Container-local paths
keep reaching the repo because everything is authored somewhere the paths happen to
work.

The check that caught it costs one command: run the tool on the maintainer's
machine before writing it up.

## 6. Still open

- **No backend uses it yet.** `uidef_tk.py` still wires handlers directly;
  `uidef_runtime.py` is proven and unadopted, which is precisely the
  produced-but-never-consumed shape R24 section 4 named. It should be adopted in
  the same session it was written, and is not.
- **The workspace is still a Python model.** The runtime is real; what it locks is
  `relate_test.Workspace`, not a `src/gui/` cursor.
- **No deadlock test.** R26.3 argued that locking the domain removes lock-order
  inversion by construction, because there is one lock. Still argued, still not
  measured.
- **`host` runs synchronously on the calling thread.** That is right for a
  clipboard operation and wrong for a capability that blocks, and nothing says
  which kind a capability is.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_RUNTIME_V1.md
git add docs/maintenance/evidence/AIF120_runtime.txt
git add tools/uidef/uidef_runtime.py
git add tools/uidef/locked_test.py
git add tools/uidef/relate_test.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R37 -- the concurrency rules move into a backend-independent runtime; 60/60 wrong on area granularity, 0/60 on domain"
```
