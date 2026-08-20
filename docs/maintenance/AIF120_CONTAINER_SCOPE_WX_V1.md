---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-052
  recorded_at_utc: 2026-08-19T16:55:00Z
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
    baseline_commit: e6091c5a1
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" --
      clearing the lane's own list of known-untested claims.
  report:
    path: docs/maintenance/AIF120_CONTAINER_SCOPE_WX_V1.md
    kind: ruling
---

# AIF-120 -- R44: the wx generator shipped a defect its sibling had already fixed

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R39 found that R38's Tk backend gave the whole window one `Scope`, so destroying any
container cancelled every container's pending work -- against R21.4, a rule this lane
wrote itself. R39 fixed Tk. R40 and R41 then wrote the wx C++ backend **from R38**,
and shipped the identical defect into a second target.

The lane's own open-items list has carried the line *"wx generator recreates R39's
one-scope-per-window defect"* since R41. This closes it, with a control run.

## 1. The defect, reproduced

The wx generator emitted a single global `g_scope` named for the frame, and every
button captured nothing and fired against it:

```cpp
w_B1->Bind(wxEVT_BUTTON, [](wxCommandEvent&){ g_rt->fire("Slow", "worker", g_scope, "a", "Done"); });
w_B2->Bind(wxEVT_BUTTON, [](wxCommandEvent&){ g_rt->fire("Slow", "worker", g_scope, "b", "Done"); });
```

Two panels, one worker in flight in each, two **unrelated** work areas so the lock
domains are genuinely disjoint and the handlers genuinely overlap. Destroy one panel:

```
  destroying P1 while both handlers are in flight
  completions delivered:
     (none)
  runtime log:
     worker Slow
     worker Slow
     dropped Done F1
     dropped Done F1
```

Both dropped, and the log names the frame twice. `wxEVT_DESTROY` propagates upward
from children exactly as Tk's `<Destroy>` does, so a child's destruction reached a
window-scoped handler and cancelled a sibling that was never touched. This is not an
argued defect; it is the run.

## 2. Ruling R44.1: one scope per container, and the handler captures its own

The generator now emits, at every container (`form`, `group`, `panel`, `page`,
`pageset`):

```cpp
w_P1->SetName("P1");
auto sc_P1 = std::make_shared<uidef::Scope>("P1");
w_P1->Bind(wxEVT_DESTROY, [sc_P1, w_P1](wxWindowDestroyEvent& e){ if (e.GetWindow() == w_P1) sc_P1->destroy(); e.Skip(); });
...
  w_B1->Bind(wxEVT_BUTTON, [sc_P1](wxCommandEvent&){ g_rt->fire("Slow", "worker", sc_P1, "a", "Done"); });
```

Three details each answer a way this can be got wrong:

- **`e.GetWindow() == w_P1`.** Without the guard, the first child destroyed cancels
  its parent -- the same off-by-one-container error in the other direction. Tk's
  version needs the same guard for the same reason, which is why R39 has one.
- **Captured `std::shared_ptr`, not a reference.** The scope must outlive the widget
  that owned it: a completion queued before the destroy is delivered after it, and
  it has to find an object to ask rather than a dangling one. The window pointer
  beside it is captured by value for identity comparison only and is never
  dereferenced -- it fires while that window is being destroyed.
- **`SetName(OBJID)`.** A target cannot exercise R21.4 without a handle to the
  container, and a generated `OnInit` keeps its locals. Tk hands back a dict of
  widgets; wx already had the mechanism, so containers now carry their `OBJID` as
  the window name and `wxWindow::FindWindowByName` resolves it. This is the first
  thing the generated code offers a target other than "it runs".

`scope_for(oid)` walks the `PARENT` chain to the nearest enclosing container, the
same function by the same name as the Tk backend. The window's scope remains
`g_scope`, because a window-wide cancel is still correct **for the window**.

## 3. Runtime-proven, against the same table on both targets

```
=== AFTER R44 (wx C++, g++ / std::thread / CallAfter) ===
  completions delivered:
     P2 | finished in P2 | completed
  runtime log:
     worker Slow / worker Slow / dropped Done P1 / complete Done completed

=== R39 (Tk, python3.12) ===
  completions delivered: [('P2', 'finished in P2', 'completed')]
  runtime log           : [('worker','Slow'), ('worker','Slow'), ('dropped','Done','P1'), ('complete','Done','completed')]
```

Same document, two implementations sharing no code and no language, dropping the same
completion and delivering the same one. This is the R41 argument extended from
ordering to **cancellation**: the scope tree is a property of the DOCUMENT, not of a
runtime. Evidence tier: **runtime-proven**.

## 4. Correction 29: the harness reproduced the defect it was testing for

The first version of the test driver destroyed P1 and reported from inside
`CallAfter` with a `sleep_for` between them. It reported both panels as failures --
output indistinguishable from the defect under test.

The cause is in the contract. R11.3 says a completion runs on the UI thread, and the
runtime delivers it *by* `CallAfter`. Sleeping on the UI thread inside a `CallAfter`
starves the delivery it is waiting for. The queued completions were behind the
sleeping callback and never ran before `ExitMainLoop`.

**The finding is not "use a timer".** It is that a harness for an asynchronous rule
can fail in a way that looks exactly like the rule being broken, and nothing in the
output distinguishes them. The control run in section 1 is what makes the section 3
result mean anything: without a known-bad build producing known-bad output, "both
dropped" is equally good evidence for a real defect and for a broken harness. Any
future test of a delivery guarantee in this lane ships with its control.

Also caught, by the compiler rather than by me: the generated destroy lambda first
named `w_P1` without capturing it. It did not build. R40.2 said "for a compiled
target, 'it builds' is a syntax check" -- the converse is that a compiled target
still catches the class of error an interpreter defers to runtime, and this one was
never at risk of shipping.

## 5. What this does not prove

- **Cancellation is observed, not honoured.** `Slow` polls `sc.cancelled` and the
  destroyed panel's handler returns early. A handler that never checks runs to
  completion and its result is dropped at delivery. That is R21.4 as written -- the
  completion is suppressed, the work is not killed -- but a reader could take
  "cancelled" to mean the thread stopped. It does not.
- **Nested containers are still untested.** A panel inside a group inside a form has
  three scopes and `scope_for` returns the innermost; nothing has destroyed a middle
  one and checked that the outer survives and the inner drops.
- **`group` carries its scope on the `wxStaticBox`,** which the sizer owns. Destroying
  a group in wx means destroying the box; whether that path fires `wxEVT_DESTROY` on
  the box before the sizer tears down its children has not been tested.
- **No deadlock argument has been run** on either target. It has been argued since
  R26.3 and remains argued.

## 6. Good Neighbor note

- **What changed.** `gui/uidef/uidef_wx.py` emits one `uidef::Scope` per container,
  names containers after their `OBJID`, and binds a guarded `wxEVT_DESTROY` per
  container; button handlers capture their nearest enclosing scope by value. New file
  `gui/uidef/wx_scope_registry.cpp`, the target-side harness for R21.4.
- **Whose area.** AIF-120's own; no file outside `gui/uidef/` and
  `docs/maintenance/` is touched.
- **What authorization.** Maintainer (member.derald), standing in-session "continue",
  clearing the lane's own list of known-untested claims.
- **How to verify or undo.** Verify: generate with `--dispatch`, build against
  `wx_scope_registry.cpp`, run under `xvfb-run`; expect `P2 | finished in P2 |
  completed` and `dropped Done P1`. Undo: the change is confined to `emit_scope`,
  `scope_for` and the `wxEVT_BUTTON` binding in `uidef_wx.py`; reverting them
  restores `g_scope` everywhere and the control output in section 1.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/uidef_wx.py
git add gui/uidef/wx_scope_registry.cpp
git add docs/maintenance/AIF120_CONTAINER_SCOPE_WX_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R44 -- the wx backend gets container scopes; a control run proves the defect it shipped with, and the harness that faked it"
```
