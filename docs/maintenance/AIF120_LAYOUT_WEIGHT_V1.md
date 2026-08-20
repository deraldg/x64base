---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-088
  recorded_at_utc: 2026-08-20T16:00:00Z
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
    baseline_commit: 851a664bd
  authorization:
    requested_by: maintainer (member.derald), in-session -- "gold standard",
      invoking the house rule "go for gold unless the cost is platinum" against
      R78's finding, which had recorded the gap and declined to design it.
    scope: >
      Add Weight and Fill to the design table, implement in the wx backend, gate
      in the manifest, prove by render. Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_LAYOUT_WEIGHT_V1.md
    kind: ruling
---

# AIF-120 -- R79: `Weight` and `Fill`, the two per-child properties every backend has and the design table did not

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R78 measured the gap and deliberately did not design it. The maintainer answered
**"gold standard"**, which in this house is a rule: *go for gold unless the cost is
platinum -- the only brake is disproportionate cost*, and its sequencing half,
*ship the gold design now, shaped so the platinum upgrade is an extension, not a
rewrite.* So this ruling designs it, ships it, gates it, and proves it with a
render. `Weight` is a child's share of the flow axis; `Fill` is whether it stretches
across. Absent means `0` and `false`, which is exactly what every document said
before -- **all eighteen fixtures generate byte-identical output.**

**Evidence tier: runtime-proven.** Before and after renders of the same document.

## 1. Why PROPS and not a seventeenth field -- the gold/platinum test, applied

The design table has sixteen fields. `Weight` could be one of them: it is per-child
layout data, and `ORDINAL` and `SPAN` are already per-child layout data sitting in
their own columns. That is the tidy answer.

It is also the platinum one. A seventeenth field changes the record length, which
means every existing `.DBF` in the corpus, every reader (`read_vfp_binary.py`,
`uidef.py`, four backends, two importers), and every document anyone has ever
authored. Section 7 of the contract already designates `PROPS` as the extension
point -- *"PROPS -- adopted, not invented"* -- and the cost there is zero.

**Gold is `PROPS`.** The brake in the house rule is disproportionate cost, and a
schema change to carry two optional values is disproportionate.

## 2. The design

> **`Weight`** -- a non-negative integer on a CHILD. Its share of the parent's
> `FLOW` axis. `0` means fixed: take the minimum and no more. Absent means `0`.
>
> **`Fill`** -- a boolean on a CHILD. Whether it stretches ACROSS the flow axis.
> Absent means false.

Two properties because they are two questions, and every toolkit asks both
separately. Along the axis and across it are independent: a toolbar button is
`Weight = 0, Fill = .T.` (fixed width, full height); a command box is
`Weight = 1, Fill = .F.`.

Measured against this lane's four backends before writing a line -- all four carry
both, and none needs a new concept:

| | along the axis | across it |
|---|---|---|
| wx | `Add(child, proportion, ...)` | `wxEXPAND` |
| Tk | `pack(expand=True)` / `grid(weight=)` | `fill=` / `sticky=` |
| HTML | `flex-grow` | `align-self: stretch` |
| character cell | proportional column share | full span of the cross axis |

## 3. Why the platinum upgrade is an extension, not a rewrite

The platinum question is R77's: does UIDEF describe **negotiable** geometry -- a
splitter's sash, which the author proposes and the user moves?

Putting `Weight` on the child is the foundation that question needs. A splitter is
two children with weights plus a movable boundary. If weight already lives on the
child, a future `splitter` kind takes its proportions from the property that is
already there, and the only new thing is the sash's movability -- a container
property, not a redesign. Had `Weight` gone on the container instead, splitters
would have had to move it.

That is the sequencing the house rule asks for, stated so it can be checked later
rather than claimed now.

## 4. What it does NOT do, said plainly

**Weight does not replace a sash.** `author_mainframe.py` turns the sample's
`SplitHorizontally(notebook_, log_, 500)` into `Weight = 3` and `Weight = 1`. That
is an **approximation the author chooses, not a translation.** 500 pixels is not a
ratio; converting it is a judgement about how the frame should behave when resized,
and nothing in the source says 3:1. The document records the judgement and the
comment says it is one. R77's question stands untouched.

**`FLOW = grid` gets `Fill` and not `Weight`.** `wxGridBagSizer` grows by row and
column, which is a container question. A `Weight` on a grid-flow child is reported
as dropped rather than silently ignored.

**Three backends are owed.** Only wx implements this. Tk, HTML and character-cell
carry the concept (section 2, measured) and each is its own change with its own
render. Naming them here so the gap is a queue and not a surprise.

## 5. Proof

Same document, `MAINFRAME.DBF`, before and after declaring 24 `Weight` and 22
`Fill` values:

| | before | after |
|---|---|---|
| Areas list | a small fixed box | fills its pane |
| notebook | 2 tabs visible | 5 tabs visible, fills the width |
| frame | content in a corner | content uses the window |
| `wxEXPAND` emitted | 0 | 11 |
| non-zero proportions | 0 | 8 |

Capture: `docs/maintenance/evidence/AIF120_R79_before_after.png`.

| | |
|---|---|
| build | wx 3.2.4, **0 warnings** |
| manifest, valid document | no finding on 24 Weight and 22 Fill values |
| manifest, bad document | `REFUSE button B1 Weight=-3`, `REFUSE button B2 Fill=maybe`, both naming contract 5c |
| invariance | **18/18 fixtures byte-identical** -- absent Weight and Fill reproduce the old behaviour exactly |

That last row is the load-bearing one. A layout property added to a layout language
is the kind of change that quietly moves every existing document; this one provably
moves none.

## 6. R79.1 -- the manifest could not see most of a document

Adding the gate exposed that `manifest()` collected PROPS only for the subsets
earlier rulings happened to need -- `bound`, `frames`, `fontrefs`. There was no way
to ask "what does every object declare", so a property belonging to *any* child had
nowhere to be checked from.

Added `all_props`: every object's id, kind and parsed PROPS. Not a new source of
truth, just the whole of the existing one. Any future per-child property gets a
checker for free; before this, each would have needed its own collection pass.

## 7. Open

- **Tk, HTML, character-cell** -- section 4.
- **`FLOW = grid` row/column growth** -- `wxGridBagSizer::AddGrowableRow/Col` exists and no property names it.
- **R77's negotiable geometry** -- unchanged, and now cheaper to answer.
- **MSVC** -- unchanged, and still the oldest thing on this list.

## 8. Good Neighbor

| | |
|---|---|
| What changed | `gui/uidef/uidef_wx.py` (Weight/Fill in `add_to`), `gui/uidef/manifest.py` (`all_props` + the 5c checks), `gui/uidef/author_mainframe.py` (declares the sample's 24 weights), contract 5c, this ruling, one evidence image, ledger rows |
| Whose area | AIF-120. `src/` untouched |
| Authorization | maintainer, in-session: "gold standard" |
| How to verify | `python author_mainframe.py && python uidef_wx.py MAINFRAME.DBF out.cpp`, build against wx, compare to the before image; and `python manifest.py` on any fixture for the 18/18 invariance |
| How to undo | `git revert`. Documents without Weight or Fill are unaffected by construction |
| Risk | low, and measured: 18/18 fixtures byte-identical |

## 9. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git status -uall

git add gui/uidef/uidef_wx.py
git add gui/uidef/manifest.py
git add gui/uidef/author_mainframe.py
git add docs/maintenance/AIF120_LAYOUT_WEIGHT_V1.md
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add docs/maintenance/evidence/AIF120_R79_before_after.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md

git status -uall

git commit -m "AIF-120: R79 -- Weight and Fill, the two per-child layout properties every backend has and the design table did not; PROPS not a 17th field, and 18/18 fixtures byte-identical"
```
