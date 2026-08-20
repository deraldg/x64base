---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-086
  recorded_at_utc: 2026-08-20T14:00:00Z
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
    baseline_commit: 84301b07a
  authorization:
    requested_by: maintainer (member.derald), in-session -- "you can dogfood them
      and do something else with the samples", then "yes" to writing the
      measurement up without designing the vocabulary in the same document.
    scope: >
      Measure UIDEF's vocabulary against a wx GUI the lane did not author.
      READ-ONLY against src/gui/wx. Writes one ruling and ledger rows. No
      vocabulary change, no tool change.
  report:
    path: docs/maintenance/AIF120_SAMPLE_MEASUREMENT_V1.md
    kind: ruling
---

# AIF-120 -- R77: measured against a screen it did not author, the language has a word for 90% of the controls and no word for one CONCEPT

**Status: review-needed.** The author does not self-approve. **This ruling
deliberately does not change the vocabulary** -- see section 6.

## 0. Why this measurement exists

Every UIDEF document to date was authored by this lane. `FRAMEDEMO` was written to
match `ERSATZ`; the sixteen `N*`/`P*` cases were written to exercise refusals; the
`.SCX` corpus was read with an importer this lane wrote. **The language has only
ever been graded on its own homework.**

`src/gui/wx/main_frame.cpp` is not that. It is 2,140 lines of hand-written wx, one
of the template samples the maintainer keeps for someone to copy from, built with
no reference to UIDEF and no intention of being described by it. R67 made exactly
this move once before -- it stopped arguing from one authored document and measured
170 corpus forms instead -- and this is the same move against C++ rather than
`.SCX`.

## 1. The measurement

62 control constructions (excluding the 17 bare sizers, which are `FLOW`, not
kinds):

| wx control | n | UIDEF | |
|---|---|---|---|
| `wxStaticText` | 9 | `label` | clean |
| `wxTextCtrl` | 7 | `text` | clean |
| `wxMenu` | 7 | `menu` | clean |
| `wxButton` | 6 | `button` | clean |
| `wxPanel` | 5 | `panel` | clean |
| `wxCheckBox` | 3 | `check` | clean |
| `wxNotebook` | 2 | `pageset` | clean |
| `wxListBox` | 1 | `list` | clean |
| `wxFrame` | 1 | `form` | clean |
| `wxMenuBar` | 1 | menu container | clean |
| `wxGrid` | 12 | `grid` | **different control, same constraint** -- section 2 |
| `wxChoice` | 2 | `combo` | approximate -- `combo` means the editable one |
| `wxSplitterWindow` | 3 | -- | **no word** |
| `wxDialog` | 2 | -- | **no word** |
| `wxScrolledWindow` | 1 | -- | **no word** |

**56 of 62 have a word (90%). 42 map cleanly (68%). 6 have none.**

Sizers: 15 `wxBoxSizer` are `FLOW = row|column`; 1 `wxStaticBoxSizer` is the `group`
kind; 1 `wxFlexGridSizer` is approximately `FLOW = grid`, which UIDEF renders as
`wxGridBagSizer` because R23 needed `SPAN`. Proportional growth and span are
different capabilities wearing one word -- minor, and recorded.

## 2. The gap I went looking for was not there

I expected the twelve `wxGrid`s to be the headline. UIDEF's `grid` is a **read-only
browse**, locked that way by contract 4b(b) citing BETA-7.1, and rendered as a
`wxListCtrl` in report mode. A `wxGrid` is an editable cell grid. Same word,
different thing -- an obvious mismatch, and I was ready to write it up.

`main_frame.cpp:375`:

```cpp
grid->EnableEditing(false);
```

**The sample's grids are read-only too.** A hand-written GUI built with no
knowledge of this contract independently arrived at the constraint the contract
requires. That is corroboration of 4b(b) from outside the lane, and it is a better
result than the gap I was hunting.

What remains is a rendering difference -- `wxGrid` versus `wxListCtrl` -- not a
semantic one. Recorded so the next reader does not re-derive the alarm.

**The method note, because it is the third time this session:** I formed a
hypothesis from the shape of my own vocabulary and nearly asserted it. One grep
answered it. R74 has the same shape ("nothing connects grid selection to the
current record" -- there was a hook), and so does R72. *A search shaped by the
object you have cannot find an object with a different schema*, and the corollary
is that it will happily confirm the object you expected.

## 3. The real finding is a CONCEPT, not a control

Three controls have no word. Two of them -- `wxScrolledWindow`, `wxDialog` -- are
missing vocabulary, and missing vocabulary is cheap: a kind, a property, a
refusal. The third is not.

```cpp
work_splitter->SplitVertically(area_panel, splitter, 220);
splitter->SplitHorizontally(notebook_, log_, 500);
ddict_splitter->SplitHorizontally(ddict_objects_grid_, ddict_detail_notebook_, 260);
```

Nested splitters, each with a sash position. R12 ruled that **layout intent is the
portable geometry**, and section 8 quarantines absolute coordinates as advisory
because they do not travel. A splitter breaks the frame that ruling set up:

> A `FLOW` boundary is one the AUTHOR fixes. A sash is a boundary the author
> **proposes** and the USER moves. UIDEF can describe geometry that is decided and
> geometry that is derived. It has no way to describe geometry that is
> **negotiable**, and `ORIGIN` cannot carry it -- `ORIGIN` is advisory input, a
> sash position is live state that outlives the session.

That is the question this measurement raises and does not answer: **does UIDEF
describe negotiable geometry at all, or declare it out of scope the way it declared
absolute coordinates out of scope?** Both are defensible. Declaring it out of scope
is cheaper and costs three splitters in one sample. Describing it is a new axis in
a contract whose whole geometry model is R12's single ruling.

## 4. What UIDEF got right, stated because a measurement that only lists gaps is a complaint

- Ten control types map with no caveat, covering 42 of 62 constructions.
- `pageset`/`page` matched `wxNotebook` exactly, including nesting inside a splitter.
- The `group` kind renders as `wxStaticBoxSizer`, which is what the sample uses for the same purpose.
- 4b(b)'s read-only rule was independently arrived at by the sample -- section 2.
- The menu vocabulary (AIF-120 R31/R32) covered all 7 `wxMenu` plus the bar with no gaps.

## 5. Method, and its limits

Measured by enumerating `new wx*` constructions in `src/gui/wx/main_frame.cpp` and
mapping each against the nineteen KINDs. That counts **what is built**, not what is
*bound*, *laid out*, or *handled* -- a control UIDEF can name is not thereby a
control UIDEF can fully describe.

So this is a **vocabulary coverage** measurement and nothing more. Three things it
does not measure and should not be read as measuring:

- **Behaviour.** `HANDLERS` names references, never bodies (section 9); 2,140 lines of C++ is mostly behaviour and none of it was assessed.
- **Layout fidelity.** Whether a generated frame would LOOK like the sample is a render question, and R40 is emphatic that only a render answers it.
- **Data binding.** The sample's grids fill from the engine by paths this lane has not traced.

A round-trip -- author a UIDEF document describing this frame, generate it, compare
the two windows -- is the test that would answer those. It is a larger unit and
this ruling is the reconnaissance for it.

## 6. Deliberately NOT designed here

No KIND is added, no property, no refusal. R74 established the discipline and the
reason: adding a half-specified `Path` property would have been R6's
generate-from-a-count mistake in a new place. A `splitter` kind invented in the same
document that discovered the need for one would be the same error -- the author
grading his own homework twice in one file.

The candidates, for whoever rules on them:

- **`splitter`** -- with `Orientation` and `SashPosition`, IF section 3 is answered in favour of describing negotiable geometry.
- **`dialog`** -- distinct from `form`: different lifetime, and a result contract (`ShowModal` appears 4 times).
- **scrolling** -- a container property rather than a kind, most likely.
- **`combo`** -- currently means `wxComboBox`; `wxChoice` is a distinct control the word hides. The corpus should decide whether that distinction is worth a second word.

## 7. Good Neighbor

| | |
|---|---|
| What changed | this ruling and ledger rows. Nothing else |
| Whose area | AIF-120. `src/gui/wx` was **read only** -- the sample is a template the maintainer keeps and nothing here touches it |
| Authorization | maintainer, in-session: "you can dogfood them and do something else with the samples", then "yes" |
| How to verify | `grep -oE "new wx[A-Za-z]+" src/gui/wx/main_frame.cpp \| sort \| uniq -c`, and `sed -n '375p' src/gui/wx/main_frame.cpp` for section 2 |
| How to undo | `git revert`. It is a document |
| Risk | none. No tool and no contract changed |

## 8. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git status -uall

git add docs/maintenance/AIF120_SAMPLE_MEASUREMENT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md

git status -uall

git commit -m "AIF-120: R77 -- measured against a wx sample the lane did not author: a word for 90% of controls, corroboration of 4b(b) from outside, and no word for negotiable geometry"
```
