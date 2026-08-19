---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-042
  recorded_at_utc: 2026-08-19T12:05:00Z
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
    baseline_commit: a2ba450e7
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- the
      top of the queue the closeout names: a second real backend.
  report:
    path: docs/maintenance/AIF120_SECOND_BACKEND_V1.md
    kind: ruling
---

# AIF-120 -- R34: the same table, two geometry models, no coordinates

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

## 1. What this tests, and what it does not

Gate 11 (R28) asked whether a second **author** could build a consumer from the
contract. This asks something different: whether the format survives a different
**geometry model**.

Tk gave `place`, `pack` and `grid` -- all pixels, all imperative. A browser flows
boxes, and section 5 of the contract names it as a candidate target for exactly
that reason: *"Turbo Vision nests `TRect`s, wx nests sizers, Qt nests layouts, Tk
packs and grids, the browser flows boxes."* That sentence is a claim, and it had
never been tested.

**Same author as `uidef_tk.py`, and that is stated rather than glossed.** This is a
portability test, not an independence test. R28 was the independence test and this
does not repeat it.

## 2. The result

`tools/uidef/uidef_html.py`. All five tables generate; markup balances on every
one; and the layout intent lands.

`docs/maintenance/evidence/AIF120_two_backends.png` is one document -- `FLOWDEMO`,
which carries **zero coordinates** -- rendered by both backends side by side:

| the table says | Tk did | HTML did |
| --- | --- | --- |
| `FLOW = row` | `pack(side='left')` | `flex-direction:row` |
| `FLOW = column` | `pack(side='top')` | `flex-direction:column` |
| `FLOW = grid`, `Columns = 2` | `grid(row, column)` | `grid-template-columns:repeat(2,...)` |
| `SPAN = 2` | `columnspan=2` | `grid-column:span 2` |
| `FLOW = grid`, no `Columns` | refused, fell back (R23.2) | refused, fell back (R23.2) |
| `FLOW = free`, no `ORIGIN` | derived and declared (R23.3) | derived and declared (R23.3) |

**Both refusals fire on both targets, for the same reasons, from the same rows.**
That is the part worth having: not that two pictures look similar, but that two
unrelated geometry engines were told to refuse the same thing and both did.

## 3. R34.1 -- `SPAN` is not a Tk convenience

`SPAN` was implemented on Tk as `columnspan` and could reasonably have been a
toolkit accident. CSS grid has `grid-column: span N` natively and it means the same
thing. A concept that appears independently in two layout engines that share no
lineage is a portable concept, which is what section 5 claimed and this is the
first evidence for.

The same argument covers `TABORDINAL`. R27 added it as a second ordinal over the
same children, and a browser spells that **`tabindex`** -- an attribute that exists
precisely because focus order and layout order are different orders. The design did
not have to be translated for this target; it was already the target's own model.

## 4. R34.2 -- the refusal set is a property of the TARGET, not the format

`manifest.py` now imports a second **real** profile instead of comparing against the
hypothetical `minimal` one. Running `UIDEF_MENU` against both:

| | refusals |
| --- | --- |
| tk | 12 |
| html | **11** |

The difference is `edit.find`. A browser provides find natively; Tk does not. Same
document, same capability names, different answers -- and a generator author gets
that answer from the table without building either window.

This is R20.3's claim measured rather than argued: `host` is the most portable
dispatch value **because** refusal is a first-class outcome, so a target that
provides more simply refuses less.

## 5. R34.3 -- R25's mechanism travels and its constants do not

R25 measured `width = k * mask_length + 10` in pixels, from one wizard on one
machine with one font, and said the mechanism travels and the numbers do not.

The HTML backend is the test. It sizes a masked control in **`ch`** -- the CSS unit
that is one zero-width -- because a mask position is a character, not a pixel. Same
mechanism, no constants carried across, and the field comes out the right size.

A pixel target and a character target both size a bound control from its mask. That
is a stronger statement than the regression that produced R25.

## 6. Still open

- **wx is still untested**, and it is the one that matters most because
  `src/gui/wx/` already exists in this tree. HTML and Tk are both retained-mode
  widget toolkits driven from Python; wx is C++ and would test the handler and
  dispatch model, not just geometry.
- **Menus are not generated for HTML.** `KIND = menu` is refused by this target, so
  R18's nesting and R20's host capabilities are exercised on Tk only.
- **A character-cell target would test more than either.** Turbo Vision has no
  pixels and no fonts at all, so `ORIGIN_SCALE`, R16, R17 and R25 would all have to
  degrade rather than translate. That is the harshest available test of section 8
  and nothing has run it.
- **The HTML backend is not interactive.** `DISPATCH = worker` emits nothing; only
  `host` capabilities are wired, through `execCommand`.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_SECOND_BACKEND_V1.md
git add docs/maintenance/evidence/AIF120_html.txt
git add docs/maintenance/evidence/AIF120_two_backends.png
git add tools/uidef/uidef_html.py
git add tools/uidef/manifest.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R34 -- a second backend on a different geometry model; SPAN and TABORDINAL are the target's own concepts, and the refusal set differs by target"
```
