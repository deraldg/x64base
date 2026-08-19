---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-054
  recorded_at_utc: 2026-08-19T18:05:00Z
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
    requested_by: maintainer (member.derald), standing in-session "continue" --
      the case R45 section 7 named as next.
  report:
    path: docs/maintenance/AIF120_PAGE_TEARDOWN_V1.md
    kind: ruling
---

# AIF-120 -- R46: the third removal verb, and the first case where the rule must not fire

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R45 shipped `destroy_container` and listed what it had not tested: *"a `wxNotebook`
page is removed with `DeletePage`, not `Destroy` -- likely a third removal verb."*
One commit later:

```
$ ./pages_test delete:PG1
PROGRAM EXIT=139
```

A `wxNotebook` owns its pages exactly as a `wxStaticBoxSizer` owns its box. Same
shape, different owner, third verb. `destroy_container` now covers all five
container kinds in the contract's vocabulary; before this it covered three and
crashed on the fourth.

**The cost of shipping a helper that covers most cases is that "most" is invisible at
the call site.** R45 named the gap in prose, and prose does not stop a segfault.

## 1. Ruling R46.1: the book control removes its own page

```cpp
if (auto* book = wxDynamicCast(w->GetParent(), wxBookCtrlBase)) {
    for (size_t i = 0; i < book->GetPageCount(); ++i)
        if (book->GetPage(i) == w) { book->DeletePage(i); book->Layout(); return true; }
}
```

`wxBookCtrlBase`, not `wxNotebook`, so `wxChoicebook`, `wxListbook`, `wxTreebook` and
`wxToolbook` are covered by the same branch -- the contract's `pageset` does not say
which one a backend picks.

## 2. Ruling R46.2: detaching is not destroying, and must not cancel

Every toolkit has a second verb that removes a page *without* destroying it --
`wxNotebook::RemovePage`, `ttk.Notebook.forget`. R45.2 said a lifetime rule must not
depend on which API ended the lifetime. This is the boundary of that sentence:
**these verbs do not end it.** The page window is alive, its handlers are still
bound, and R21.4 speaks about destruction.

```
remove:PG1   PG1 dropped=False completed=True     (wx)
forget:PG1   PG1 dropped=False completed=True     (Tk)
```

This is the first test in the lane where the correct result is that **nothing is
cancelled**. Every prior scope test could have been passed by an implementation that
cancelled too eagerly -- destroy the window, drop everything, all green. This one
fails such an implementation, on both targets.

## 3. Runtime-proven, both targets, including the negative case

```
wx C++                                    Tk (python3.12)
delete:PG1  PG1 dropped | PG2 PSIB done   destroy:PG1  PG1 dropped | PG2 PSIB done
delete:PS   PG1 PG2 dropped | PSIB done   destroy:PS   PG1 PG2 dropped | PSIB done
remove:PG1  nothing dropped | all done    forget:PG1   nothing dropped | all done
```

Every wx run exits 0. Regressions after the change: R45's nested tests on both
targets, R44's wx scope test and R39's `scope_test.py` all reproduce their recorded
results. Evidence tier: **runtime-proven**.

## 4. Reading the table: an empty scope is not a failed cancel

`PS` reports `dropped=False completed=False` in every single run, including the one
that destroys it. That is correct and it is worth saying out loud, because it looks
like a failure:

> A `pageset` in this document has no handler of its own. Its scope is destroyed and
> there was nothing queued against it to drop.

**"Nothing was dropped" is only evidence of a bug when something was queued.** A test
report that lists containers rather than in-flight work will show a column of `False`
for every decorative container, and a reader scanning for `True` will read it as
half-broken. The lane's own harnesses have this shape; the fix is to read the column
against what was fired, which is why every one of these tables names the work areas
in its header.

## 5. Open, and one of them is the owner's

- **Does removing a page mean cancelling its work?** R46.2 answers from the contract
  as written -- destruction cancels, detaching does not. But a UIDEF author writing
  `RemovePage` may well mean "the user closed this tab, stop working on it." The
  contract has no vocabulary for *deactivation* as distinct from destruction, and a
  backend cannot invent one. **Owner ruling wanted.**
- **`destroy_container` now covers five container kinds by knowing three owners.**
  The next widget wx owns specially -- a `wxAuiNotebook`, a splitter pane -- is a
  fourth. The helper's shape does not generalize; it enumerates. That is honest but
  it is not finished, and there is no test that fails when a new container kind is
  added to the contract.
- **Cancellation is still cooperative.** Unchanged since R44; a handler that never
  polls `cancelled` runs to completion and is dropped at delivery.
- **Nothing tests a container destroyed from inside its own completion**, or two
  containers removed in the same tick.
- **No deadlock argument has been run.** Argued since R26.3.

## 6. Good Neighbor note

- **What changed.** `tools/uidef/uidef_rt.h` gains a `wxBookCtrlBase` branch in
  `destroy_container`. New: `tools/uidef/page_scope_test.py` and
  `tools/uidef/wx_page_registry.cpp`.
- **Whose area.** AIF-120's own; nothing outside `tools/uidef/` and
  `docs/maintenance/`.
- **What authorization.** Maintainer (member.derald), standing in-session
  "continue", taking the case R45 section 7 named.
- **How to verify or undo.** Verify: `xvfb-run -a python3.12
  tools/uidef/page_scope_test.py`, and for wx generate with `--dispatch`, build
  against `tools/uidef/wx_page_registry.cpp`, and run with `delete:PG1`,
  `delete:PS` and `remove:PG1`; the two tables in section 3 must match and every run
  must exit 0. Undo: removing the `wxBookCtrlBase` branch restores the exit-139
  crash in section 1 and changes nothing else.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/uidef_rt.h
git add tools/uidef/page_scope_test.py
git add tools/uidef/wx_page_registry.cpp
git add docs/maintenance/AIF120_PAGE_TEARDOWN_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R46 -- a notebook owns its pages; the third removal verb, and the first case where the rule must not fire"
```
