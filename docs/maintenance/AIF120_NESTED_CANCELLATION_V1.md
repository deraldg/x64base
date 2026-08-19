---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-053
  recorded_at_utc: 2026-08-19T17:30:00Z
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
    baseline_commit: bf1a95e20
  authorization:
    requested_by: maintainer (member.derald), in-session, "yes, nested-container
      cancelation".
  report:
    path: docs/maintenance/AIF120_NESTED_CANCELLATION_V1.md
    kind: ruling
---

# AIF-120 -- R45: nested cancellation, and two ways to remove a container that disagreed

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R44 closed the one-level case and listed what it had not proved: nested containers,
and whether destroying a `group` -- a `wxStaticBox` its sizer owns -- works at all.
It does not. It segfaults. Getting from there to a correct answer took two more
defects, both of which produced plausible output.

The table: `F1 > G1(group) > { BG, PIN(panel) > BIN }` and `F1 > PSIB(panel) > BSIB`,
three **disjoint** work areas so all three handlers are genuinely in flight together.

## 1. Why destroying the INNER container is the test that matters

"Destroy the middle container, check the sibling survives" is passed by an
implementation that resolves every handler to the *outermost* container as well as by
one that resolves to the nearest. The two differ only here:

> Destroy `PIN`. `BG` is inside `PIN`'s parent `G1` but not inside `PIN`. Its work
> must complete.

```
destroyed PIN -- G1 dropped=False completed=True | PIN dropped=True completed=False | PSIB dropped=False completed=True
```

`G1` completes. `scope_for` returns the nearest enclosing container, and that is now
observed rather than read off the generated source.

## 2. Defect one: a `group` cannot be destroyed

```
$ ./nested_test G1
Segmentation fault
PROGRAM EXIT=139
```

A `wxStaticBoxSizer` **owns** its `wxStaticBox`. R40 already learned the parenting
half of this ("bare `wxStaticBox` compiles and renders empty groups"); the ownership
half is that `Destroy()` on the box leaves the sizer holding a freed pointer, and the
next `Layout()` dereferences it. No diagnostic, no wx assertion, exit 139.

R44 made this reachable: it called `SetName(OBJID)` on the static box so a target
could find its containers, which handed out a handle that is unsafe to use in the
only obvious way. **Naming a thing is a promise you can use it.**

### Ruling R45.1: the runtime owns teardown, not the target

`uidef_rt.h` gains `destroy_container(root, objid)`. For a `wxStaticBox` it locates
the owning `wxStaticBoxSizer`, detaches it from whatever holds it, and deletes the
sizer -- whose destructor destroys the box. For anything else it is `Destroy()`.

This belongs in the runtime rather than in a comment because the failure is silent,
platform-specific, and indistinguishable from correct code at the call site. A target
should not have to know that one of a UIDEF document's five container kinds needs a
different removal verb.

## 3. Defect two: the safe path silently stopped cancelling descendants

The fix stopped the crash and broke the thing being tested:

```
destroyed G1 -- G1 dropped=True | PIN dropped=False completed=True | PSIB completed=True
```

`PIN` is *inside* `G1`. Its work completed.

`Destroy()` defers to idle, and every descendant window gets its own `wxEVT_DESTROY`
on the way down -- which is why the **crashing** version had cancelled the nested
scope correctly. Deleting a sizer runs destructors immediately, and the descendants'
bound handlers are gone by the time their windows die.

So two ways of removing the same container disagreed about R21.4, and the one that
crashed was the one that had the semantics right. Had R44's `SetName` never existed,
this would have shipped as a latent difference between "the form closed" and "this
group was removed".

### Ruling R45.2: destruction is announced, not inferred

`destroy_container` walks the subtree depth-first and dispatches
`wxWindowDestroyEvent` before either teardown path runs. Scope cancellation is
idempotent -- `Scope::destroy()` only sets two flags -- so the real `wxEVT_DESTROY`
arriving afterwards costs nothing.

The general form: **a lifetime rule must not depend on which API the caller used to
end the lifetime.** R21.4 says a container's destruction cancels its subtree's queued
work. If that only holds for one of two removal paths, the rule is a property of the
call site rather than of the document, which is the opposite of what this lane has
been arguing since R41.

## 4. Runtime-proven, identical on both targets

```
wx C++ (g++ / std::thread / CallAfter)
  destroyed G1   -- G1 dropped=True  | PIN dropped=True  | PSIB completed=True
  destroyed PIN  -- G1 completed=True | PIN dropped=True  | PSIB completed=True
  destroyed PSIB -- G1 completed=True | PIN completed=True | PSIB dropped=True

Tk (python3.12)
  destroyed G1   -- G1 dropped=True  | PIN dropped=True  | PSIB completed=True
  destroyed PIN  -- G1 completed=True | PIN dropped=True  | PSIB completed=True
  destroyed PSIB -- G1 completed=True | PIN completed=True | PSIB dropped=True
```

Cell for cell, across two implementations sharing no code and no language, from one
document. Every wx run exits 0. Evidence tier: **runtime-proven**.

Regressions after the change: R39's `scope_test.py`, R44's wx scope test, and R38's
`adopt_test.py` all reproduce their recorded results.

## 5. A shipped leak, cleaned up in passing

Every Tk evidence capture in this lane has carried, on stderr:

```
invalid command name "140573167365824_pump"
```

The pump reschedules itself, so at teardown there is always exactly one `after` in
flight, and it fires into a torn-down interpreter. Harmless, from a callback, with no
traceback into the backend file -- which is why it survived R37 through R44 as
scenery. `uidef_tk.py` now cancels the pending `after` with the window.

## 6. Correction 30: I nearly reported a phantom

The first three-target Tk run appeared to show the `G1` case producing no output at
all, matching the wx crash. I said so before checking.

It was my own `tail -10`. The Tcl warnings above are four lines each, and two of them
plus two result lines filled the window exactly, cutting the first result line. Run in
isolation, `G1` had passed all along.

The lesson is R44.4's, one ruling later and from the other side: there, a broken
harness produced output identical to a real defect; here, a truncated *view* did. In
both cases the output was consistent with a defect I was already expecting to find,
which is the condition under which I stop checking. **Evidence that confirms what you
predicted deserves the same verification as evidence that contradicts it.**

## 7. Still open

- **Cancellation remains cooperative.** `Slow` polls `sc.cancelled`. A handler that
  never checks runs to completion and is dropped only at delivery. Unchanged since
  R44 and worth an owner ruling: R21.4 says the completion is suppressed, and a
  reader may fairly take "cancelled" to mean the work stopped.
- **`destroy_container` is untested against `pageset`/`page`.** A `wxNotebook` page
  is removed with `DeletePage`, not `Destroy` -- likely a third removal verb, and
  section 3 says the rule must not depend on which one the caller uses.
- **Nothing tests two containers destroyed at once**, or a container destroyed from
  inside its own handler's completion.
- **No deadlock argument has been run** on either target. Argued since R26.3.

## 8. Good Neighbor note

- **What changed.** `tools/uidef/uidef_rt.h` gains `destroy_container`,
  `uidef_announce_destroy` and two sizer helpers. `tools/uidef/uidef_tk.py` cancels
  its pending `after` on window destruction. New: `tools/uidef/nested_scope_test.py`
  and `tools/uidef/wx_nested_registry.cpp`.
- **Whose area.** AIF-120's own; nothing outside `tools/uidef/` and
  `docs/maintenance/`.
- **What authorization.** Maintainer (member.derald), in-session: "yes,
  nested-container cancelation".
- **How to verify or undo.** Verify: `xvfb-run -a python3.12
  tools/uidef/nested_scope_test.py`, and for wx generate with `--dispatch`, build
  against `tools/uidef/wx_nested_registry.cpp`, and run with each of `G1`, `PIN`,
  `PSIB` as the argument; the two tables in section 4 must match cell for cell and
  every run must exit 0. Undo: removing `destroy_container` from `uidef_rt.h`
  restores the segfault in section 2; removing only `uidef_announce_destroy` restores
  the wrong-but-quiet result in section 3, which is the more dangerous of the two.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/uidef_rt.h
git add tools/uidef/uidef_tk.py
git add tools/uidef/nested_scope_test.py
git add tools/uidef/wx_nested_registry.cpp
git add docs/maintenance/AIF120_NESTED_CANCELLATION_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R45 -- nested cancellation proven on both targets; destroying a group segfaulted, and the safe fix silently stopped cancelling descendants"
```
