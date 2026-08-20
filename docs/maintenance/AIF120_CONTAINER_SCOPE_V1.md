---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-047
  recorded_at_utc: 2026-08-19T13:45:00Z
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
    baseline_commit: 05af27848
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- R38
      section 4 named this gap in its own adoption one commit earlier.
  report:
    path: docs/maintenance/AIF120_CONTAINER_SCOPE_V1.md
    kind: ruling
---

# AIF-120 -- R39: the scope is the container, and unrelated work still runs at once

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R11.4 said it in the sentence this lane has been circling all day: *"Closing or
destroying a **container** cancels the pending work its handlers submitted."*

R38's adoption gave the whole **window** one scope. Destroying any container would
therefore have cancelled every container's pending work -- a defect against a rule
this lane wrote itself, named in R38 section 4 and fixed here.

## 1. The experiment

Two panels, each with a button whose handler is `DISPATCH = worker`. Their
`BINDING`s name **two work areas with no relation between them**, so they are
separate lock domains and genuinely run at the same time. Both fire; then one panel
is destroyed while both are in flight.

```
lock domains: [['a'], ['b']]
destroying P1 while both handlers are in flight

completions delivered: [('P2', 'finished in P2', 'completed')]
runtime log           : [('worker','Slow'), ('worker','Slow'),
                         ('dropped','Done','P1'), ('complete','Done','completed')]

R21.4  the destroyed container's work was dropped : True
R21.4  the SURVIVING container's work completed   : True
```

Each container gets its own `Scope`; a handler uses its **nearest enclosing** one,
found by walking `PARENT`. Destroying a container cancels exactly what that
container queued.

## 2. R39.1 -- the converse of R38, and the pair is the point

R38 showed two handlers naming **different** work areas serializing against each
other, because the document declared a relation between them.

R39 shows two handlers naming **different** work areas running **concurrently**,
because the document declared no relation.

Together: **the runtime serializes exactly as much as the document says and no
more.** Neither result alone would show that. R38 on its own is consistent with a
runtime that serializes everything; R39 on its own is consistent with one that
serializes nothing. The lock extent is a property of the document, and both
directions are now measured.

> **R39.1.** A generated frontend's concurrency is declared, not configured. Two
> handlers run at once if and only if the document does not relate the work areas
> they touch.

## 3. What was actually wrong, and how long it lived

One commit. R38 was written, its own gap was recorded in its section 4, and it was
fixed before anything else was started. That is the shortest a named defect has
survived in this lane, and it is what R38.1 asked for: recording is not fixing.

## 4. Still open

- **Nesting depth is untested.** `scope_for` walks `PARENT` to the nearest
  enclosing container. A panel inside a page inside a pageframe should cancel
  innermost-first and nothing exercises it.
- **Cancellation is cooperative.** `Slow` checks `scope.cancelled` between steps.
  A handler that never checks runs to completion and only its *completion* is
  dropped -- the work is not stopped, and the contract does not say it must be.
- **Only Tk.** Unchanged from R38.
- **Still a Python workspace.** Unchanged from R37.

## 5. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_CONTAINER_SCOPE_V1.md
git add docs/maintenance/evidence/AIF120_scopes.txt
git add gui/uidef/uidef_tk.py
git add gui/uidef/scope_test.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R39 -- one scope per container; and unrelated work areas run concurrently, so the runtime serializes exactly what the document declares"
```
