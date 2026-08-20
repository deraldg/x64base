---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-046
  recorded_at_utc: 2026-08-19T13:30:00Z
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
    baseline_commit: eff5f86a0
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- R37
      section 6 recorded its own unadopted runtime as a defect and said it should be
      adopted in the same session.
  report:
    path: docs/maintenance/AIF120_RUNTIME_ADOPTION_V1.md
    kind: ruling
---

# AIF-120 -- R38: the backend stops deciding what to lock and is told

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R37 built a backend-independent runtime and left it unadopted, recording that as
the produced-but-never-consumed shape R24 section 4 named -- created deliberately
this time, and named rather than left to be found. This closes it in the same
session.

`uidef_tk.build_window(path, registry=..., host=...)` now constructs a `Runtime`
from the document's own `SOURCE`, fires every `Click` through it, pumps completions
on the UI thread, and cancels the scope when the window is destroyed. The backend
never chooses a lock.

## 1. The timeline, which is the whole result

A document with **two work areas and a relation between them**, and two buttons
whose handlers name **different** aliases -- `students.gpa` and `enroll.cls_id`:

```
lock domains, read from the document's SOURCE: [['enroll', 'students']]
UI thread: 139803099148416

TotalGpa         enter      [139803081713344]
host             edit.cut   [139803099148416]
TotalGpa         leave      [139803081713344]
ListEnrolments   enter      [139803073304256]
Done             completed  [139803099148416]
ListEnrolments   leave      [139803073304256]
Done             completed  [139803099148416]
```

**`TotalGpa` leaves before `ListEnrolments` enters.** Two handlers that name
different work areas were serialized against each other, because the document says
those areas are related and the runtime read it. Neither handler asked for a lock
and neither knows the other exists.

| clause | result |
| --- | --- |
| R21.1 two workers on one domain overlapped | **no** |
| R11.3 both ran off the UI thread | yes |
| R11.3 every completion ran on the UI thread | yes |
| R20 `host` ran with no thread rule | yes, on the calling thread |
| R11.3 worker with no `ON_COMPLETE` | refused |

## 2. What is now joined end to end

```
.SCX  ->  import_scx   ->  UIDEF table  ->  manifest   ->  runtime  ->  Tk
          R31 classes       R36 SOURCE       R26 lock       R37        R38
          R30 members       relations        domain
```

Every step reads what the one before it wrote, and the concurrency rule that
started as R11.4's sentence about workspaces is now enforced by a lock whose extent
was computed from a `relation` record the importer had been discarding two commits
ago.

## 3. R38.1 -- adoption is where a design stops being a hypothesis

R24 section 4 named four defects that shared a shape: a field read off the wrong
row, a field nothing read, a kind nothing rendered, a load-bearing property with no
name. All four survived because production and consumption were never checked
against each other.

R37 created a fifth on purpose and recorded it. **The recording is not the fix.**
The fix is one backend calling it, and the difference between the two states is the
timeline above -- which could not have been produced by reading either file.

> **R38.1.** A runtime, a profile or a rule is `planned` until a consumer uses it.
> Writing it and writing about it are the same tier.

## 4. Still open

- **Only Tk adopted it.** The HTML and character-cell backends still emit no
  dispatch at all; the runtime is toolkit-free precisely so they can, and neither
  does.
- **The workspace is still a Python model.** What the runtime locks is
  `relate_test.Workspace`, not a `src/gui/` cursor. The lock is real; the thing
  being protected is not.
- **`<Destroy>` fires for every widget**, and the binding filters for the root. On
  a target where a sub-container is destroyed independently, scope cancellation
  needs to be per container, not per window.
- **No deadlock test.** Unchanged from R37.
- **`host` runs on the calling thread**, which is right for a clipboard operation
  and wrong for a capability that blocks. Unchanged from R37.

## 5. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_RUNTIME_ADOPTION_V1.md
git add docs/maintenance/evidence/AIF120_adopt.txt
git add gui/uidef/uidef_tk.py
git add gui/uidef/adopt_test.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R38 -- the Tk backend fires every handler through the shared runtime; two handlers naming different work areas serialize because the document says they are related"
```
