---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-049
  recorded_at_utc: 2026-08-19T14:20:00Z
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
    baseline_commit: 907895cb2
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- R40
      section 5 named this as the thing wx was wanted for and explicitly did not do.
  report:
    path: docs/maintenance/AIF120_WX_DISPATCH_V1.md
    kind: ruling
---

# AIF-120 -- R41: the same timeline, on different threading primitives

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R40 emitted wx C++ and bound no events, and said so: *"the thing wx was actually
wanted for -- the handler and threading model on a compiled target -- is still
untested, and R40 should not be read as having done it."* This does it.

`gui/uidef/uidef_rt.h` is the dispatch runtime in C++ -- `std::thread`,
`std::mutex` and `wxWindow::CallAfter` where R37 used Python threads and a polled
queue. `uidef_wx.py --dispatch` emits the bindings and the domain table.

## 1. What the generator emits

```cpp
static const std::vector<std::vector<std::string>> DOMAINS = {{"enroll", "students"}};

w_B1->Bind(wxEVT_BUTTON, [](wxCommandEvent&){
    g_rt->fire("TotalGpa", "worker", g_scope, "students", "Done"); });
w_B2->Bind(wxEVT_BUTTON, [](wxCommandEvent&){
    g_rt->fire("ListEnrolments", "worker", g_scope, "enroll", "Done"); });
w_B3->Bind(wxEVT_BUTTON, [](wxCommandEvent&){
    g_rt->fire("edit.cut", "host", g_scope, "", ""); });
w_B4->Bind(wxEVT_BUTTON, [](wxCommandEvent&){
    g_rt->fire("TotalGpa", "worker", g_scope, "students", ""); });
```

The `DOMAINS` line was read out of the document's own `SOURCE` (R36). Handler
bodies are supplied by the target in a separate translation unit -- R14's model,
which in C++ becomes a linker symbol the generated file references and never
defines.

## 2. Measured -- the same experiment, twice, in two languages

**Locking the relation set (R26):**

```
TotalGpa enter          [worker]
host edit.cut           [UI]
TotalGpa leave          [worker]
ListEnrolments enter    [worker]
Done completed (588.74) [UI]
ListEnrolments leave    [worker]
Done completed (5 rows) [UI]
```

**Locking the work area each handler names (the reading R26 corrected):**

```
TotalGpa enter          [worker]
host edit.cut           [UI]
ListEnrolments enter    [worker]     <- inside TotalGpa
ListEnrolments leave    [worker]
Done completed (5 rows) [UI]
TotalGpa leave          [worker]
Done completed (588.74) [UI]
```

**This is R38's Python timeline, reproduced on `std::mutex` and `CallAfter`.**
Serialized when the document relates the areas; overlapped when the runtime locks
only what each handler names. Same document, same generated C++, one runtime
argument between them.

`refused TotalGpa worker with no ON_COMPLETE` fires as it did in Python, and every
completion carries `[UI]` -- the runtime asserts `wxThread::IsMain()` rather than
trusting it.

## 3. R41.1 -- the rule survived the primitives

R21 and R26 were measured on Python threads, then re-measured through a Python
runtime, then adopted by a Python backend. All of it could have been an artefact of
one concurrency model.

It is not. A different language, a different mutex, a different marshalling
mechanism -- `CallAfter` posting onto the wx event loop rather than a queue polled
by `after()` -- and the same two orderings come out, for the same reason, with the
same failure when the lock extent is wrong.

> **R41.1.** `DISPATCH` and the lock domain are properties of the document, not of
> a runtime. Two implementations sharing no code and no language produced the same
> orderings from the same table.

## 4. What is now true of the whole chain

```
.SCX -> import -> UIDEF table -> manifest -> runtime -> Tk    (Python)
                                          -> runtime -> wx    (C++)
                          |                    |
                   R36 relations         R26 lock domain
```

A `relation` record in a DataEnvironment, discarded by the importer this morning,
now determines which `std::mutex` a compiled C++ frontend takes.

## 5. Still open

- **Cancellation is not wired in C++.** `Scope` carries the flag and
  `uidef_after_init` never destroys one, so R21.4 and R39's container scopes are
  proven on Tk only.
- **One scope per window in the wx generator**, which is the defect R39 fixed for
  Tk, recreated here because the emitter has no container-scope pass. Named
  immediately rather than found later.
- **No deadlock test**, unchanged since R26.3.
- **The workspace is still a Python model** on the Tk side and nothing at all on
  the wx side -- the C++ handlers sleep rather than navigating a cursor.

## 6. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_WX_DISPATCH_V1.md
git add docs/maintenance/evidence/AIF120_wxdispatch.txt
git add gui/uidef/uidef_rt.h
git add gui/uidef/uidef_wx.py
git add gui/uidef/wx_demo_registry.cpp
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R41 -- the dispatch runtime in C++; the same two orderings on std::mutex and CallAfter"
```
