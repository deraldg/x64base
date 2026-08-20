---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-097
  recorded_at_utc: 2026-08-21T03:10:00Z
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
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: fdacdbfe9
  authorization:
    requested_by: steward (member.derald), in-session -- "your job is still mostly
      gui and threading", after nine consecutive geometry units and no threading.
    scope: >
      Prove R21.4 scope containment across a splitter, whose panes are not
      sizer-parented. Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_SPLITTER_LIFETIME_V1.md
    kind: ruling
---

# AIF-120 -- R88: the splitter renders correctly and cannot be taken apart

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R85 added `splitter` to `CONTAINER_KINDS` in all four backends and proved it
RENDERS -- three toolkits, both sashes, measured off the pixels. It did not prove
the other half. A container in this lane also has a LIFETIME: destroying it must
cancel the work its handlers queued and nothing else (R21.4). Tested here for the
first time: **the semantics are right on Tk, 3 of 3, and wx segfaults on 1 of 3.**
Destroying a splitter that is itself a pane of another splitter is exit 139.

The defect is reported and NOT patched. I had a fix in the tree, it did not work,
and a half-understood patch in the cancellation path is worse than a known hole.

## 1. What was tested

Four disjoint work areas, so all four handlers are genuinely in flight:

    F1 (form)
      WORK (splitter)
        AREAP (panel) > BAR    a.x
        INNER (splitter)
          NBK (panel) > BNB    b.y
          LOG (panel) > BLG    c.z
      PSIB (panel) > BSIB      d.w      <- outside the splitter entirely

Three destroy targets, each proving a different thing:

| destroy | must cancel | must COMPLETE |
|---|---|---|
| `INNER` | NBK, LOG | **AREAP**, PSIB |
| `WORK` | AREAP, NBK, LOG | PSIB |
| `PSIB` | PSIB | AREAP, NBK, LOG |

`INNER` is the discriminating case, and for a reason R45 did not have: **AREAP is
INNER's sibling inside the same splitter.** An implementation that cancelled
per-splitter rather than per-pane would pass every other row and fail this one.

## 2. Result

    Tk   destroy INNER  PASS   AREAP=completed  NBK=cancelled  LOG=cancelled  PSIB=completed
    Tk   destroy WORK   PASS   AREAP=cancelled  NBK=cancelled  LOG=cancelled  PSIB=completed
    Tk   destroy PSIB   PASS   AREAP=completed  NBK=completed  LOG=completed  PSIB=cancelled
                                                                    splitter-scope: 3/3

    wx   destroy INNER  -> exit 139   SEGMENTATION FAULT
    wx   destroy WORK   -> exit 0     AREAP/NBK/LOG dropped, PSIB completed
    wx   destroy PSIB   -> exit 0     PSIB dropped, the other three completed

**So the design is right and one target cannot execute it.** Tk gets the
discriminating case exactly right, including the sibling that must survive. The
same document, the same three targets, on the real threading primitive
(`std::thread`, `wxWindow::CallAfter`, `uidef_rt.h`) crashes.

Reproduced against `uidef_rt.h` byte-identical to `HEAD`
(`d9426d05b665a08b537daeed42453d4e`), so this is the shipped runtime and not a
state I introduced while investigating.

## 3. Where it dies

    Thread 1 "splitscope" received signal SIGSEGV
    #0  wxSplitterWindow::AdjustSashPosition(int) const
    #1  wxSplitterWindow::DoSetSashPosition(int)
    #2  wxSplitterWindow::SizeWindows()
    ...
    #10 wxBoxSizer::RepositionChildren(wxSize const&)
    #11 wxSizer::Layout()
    #12 wxWindowBase::Layout()
    #13 uidef_after_init(wxWindow*)::{lambda(wxTimerEvent&)#1}

A splitter is being asked to size itself against a pane that is no longer there.

## 4. Why this was predictable, and why nobody predicted it

`destroy_container()` in `uidef_rt.h` already carries this exact lesson twice:

- **R45** -- a `wxStaticBox` is owned by its sizer. `Destroy()` on it then
  `Layout()` is a segfault. Removal verb: detach from the `wxStaticBoxSizer`.
- **R46** -- a notebook OWNS its pages. `Destroy()` on a page leaves the book
  holding a freed entry and the next `Layout()` segfaults. Removal verb:
  `DeletePage`. The comment there reads: *"the same shape as the wxStaticBox
  case, a different owner, a third removal verb."*

**A splitter is the fourth owner and it has no verb.** Its panes go in through
`Split*()`, never through a sizer -- which R85 had to special-case in three
generators and *still* did not connect to lifetime.

The rule this lane can now state, having paid for it three times:

> A new container KIND is not finished when it renders. It is finished when its
> owner knows how to let go of it.

`CONTAINER_KINDS` and `destroy_container()` are two lists that must move
together, and nothing enforces that.

## 5. What I tried, and why none of it shipped

Three variants, all still exit 139:

    Unsplit(w); w->Destroy(); split->Layout();
    Unsplit(w); split->CallAfter([w]{ w->Destroy(); });
    ... with the driver's frame->Layout() deferred to CallAfter

So the trigger is not the destroy timing and not the immediate `Layout()`. The
crash survives every ordering I tried, which means I do not yet understand it,
and `destroy_container` is the function every container's cancellation runs
through. A patch that changes behaviour I cannot explain, in that function, is
not an improvement -- it is a second unknown stacked on the first. The tree is
left at `HEAD` and the hole is documented.

## 6. Standing consequence for R85

R85's proof table said the splitter loses "nothing" on wx. That was true of
RENDERING and is now known to be incomplete. **The splitter is proven for layout
and unproven for lifetime under `--dispatch`.** Anyone generating a wx frontend
with `--dispatch` and a nested splitter should know that tearing down the inner
one is currently fatal.

## 7. How to disprove or advance this

- Run `python3 splitter_scope_test.py` -- expect 3/3 on Tk.
- Build the wx side: generate `/tmp/SPLITSCOPE.DBF` with `uidef_wx.py --dispatch`,
  compile against a driver modelled on `wx_nested_registry.cpp`, run with
  argument `INNER`. Expect exit 139.
- The fix is a fourth branch in `destroy_container()`. Whoever writes it should
  explain the backtrace first, not after.
- A cheap guard worth having either way: a check that every kind in
  `CONTAINER_KINDS` is handled by `destroy_container`, so the two lists cannot
  drift apart again silently.

## 8. Good Neighbor note

- **What changed:** one new file, `gui/uidef/splitter_scope_test.py`. Nothing
  else. `uidef_rt.h` was edited during investigation and restored to `HEAD`,
  verified by md5.
- **Whose area:** AIF-120. No engine source, no gate, no other lane's file.
- **What authorization:** steward, in-session, "your job is still mostly gui and
  threading".
- **How to verify:** section 7.
- **How to undo:** delete the test. It adds no behaviour; it only reports.
