---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-048
  recorded_at_utc: 2026-08-19T14:00:00Z
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
    baseline_commit: d3a7f8b10
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- wx has
      been the top of the closeout's queue since R34.
  report:
    path: docs/maintenance/AIF120_WX_BACKEND_V1.md
    kind: ruling
---

# AIF-120 -- R40: a compiled backend, and the third sizer model

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Tk, HTML and the character grid are all Python and all interpreted. `src/gui/wx/`
in this tree is C++. `gui/uidef/uidef_wx.py` emits wx C++ from a UIDEF table, and
**the C++ is compiled and run** -- a generator whose output is never built is a
text formatter.

## 1. Measured

```
FLOWDEMO:        COMPILED 191824 bytes
TABDEMO:         COMPILED 177080 bytes
FONTDEMO:        COMPILED 137824 bytes
UIDEF_STUDENTS:  COMPILED 146424 bytes
UIDEF_FORM1:     COMPILED 243560 bytes
```

Five tables, five programs, `g++` with `wx-config --cxxflags --libs`, all five
built and the first run under Xvfb and screenshotted.
`docs/maintenance/evidence/AIF120_three_backends.png` is the same coordinate-free
document under `place`/`pack`/`grid`, flexbox, and wx sizers.

## 2. R40.1 -- a fourth geometry engine, and the same refusals

wx is a third layout model again: `wxBoxSizer` for `row` and `column`,
**`wxGridBagSizer`** for `grid` -- chosen because it is the only wx sizer with a
span -- and constructor `wxPoint`/`wxSize` for `free`.

The refusals are unchanged: the grid with no `Columns` is refused and falls back,
and `FLOW = free` with no `ORIGIN` derives from `ORDINAL` and says so. **Four
targets now, and the two rows `FLOWDEMO` was authored to trip are refused by all
four for the same reasons.**

`SPAN` reaches its third independent spelling: `columnspan` on Tk,
`grid-column: span N` in CSS, `wxGBSpan(1,n)` in wx. R34.1 argued from two that it
is not a toolkit accident; three engines that share no lineage is a stronger claim
than the contract made for it.

## 3. R40.2 -- compiling is not rendering

The first version parented a group's children to a bare `wxStaticBox`. It
**compiled cleanly, ran, and rendered two overlapping empty labels with every
child missing.** wx's actual idiom is that a `wxStaticBoxSizer` owns the box and
the box parents the children.

Worth a clause because a compiled target invites the mistake: a build that succeeds
feels like a proof and is not one. The same defect on Tk or in HTML would have been
a runtime error or visibly wrong markup; here it produced a valid binary.

> **R40.2.** For a compiled target, "it builds" is a syntax check. The evidence is
> still the render.

## 4. R40.3 -- a target may clip its own decoration, and R16 does not cover it

The wx render clips two group captions: *"Grid, Columns = 2, one spanning row"*
appears as *"Columns = 2, one spanning"*. A `wxStaticBox` does **not** widen to fit
its own label.

R16 governs a **control's** size from its content. A container's *decoration* --
the caption drawn on its frame -- is neither a control nor a child, and nothing in
the contract says whether a target must make room for it. Tk's `LabelFrame` and a
CSS `fieldset`/`legend` both do; wx does not.

Recorded rather than worked around, because the honest statement is that the table
said what it wanted and one of four targets cannot show it.

## 5. What this does and does not test

**Does:** a compiled language, a third sizer model, C++ construction order, and
that the generator's output survives a real compiler.

**Does not:** dispatch. The emitted C++ binds no events, starts no `wxThread`, and
uses no `CallAfter`. R37's runtime is Python and this backend cannot call it. So
the thing wx was wanted for -- testing the handler and threading model on a
compiled target -- is **still not tested**, and this ruling should not be read as
having done it.

That is the honest limit of a source generator: it proves the layout half travels
to C++ and leaves the concurrency half exactly where R39 left it.

## 6. Still open

- **Dispatch in C++.** The above. It needs `wxEvtHandler::Bind`, a `wxThread` and
  `CallAfter`, and a C++ equivalent of `LockDomains`.
- **No menus.** `KIND = menu` is refused by every backend but Tk.
- **`UIDEF_FORM1` refuses `image`** on this target and renders it on the others,
  which is a gap in this generator rather than in the format.
- **One compiler, one platform.** g++ 13 on Linux with wxGTK 3.2.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_WX_BACKEND_V1.md
git add docs/maintenance/evidence/AIF120_wx.txt
git add docs/maintenance/evidence/AIF120_three_backends.png
git add gui/uidef/uidef_wx.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R40 -- a compiled wx C++ backend; five tables generate and build, and compiling is not rendering"
```
