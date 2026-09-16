---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260916-COWORK-207
  recorded_at_utc: 2026-09-16T04:05:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_read_only
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260916-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 447962ccd
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- "the gui
      needs a redesign", then ruling YES to "does the redesigned Workbench get
      generated from its own design table?", then "document and continue".
    scope: >
      RE-MEASUREMENT of AIF120_SAMPLE_MEASUREMENT_V1.md section 6, which ran the
      same crosswalk before R85. Reports what moved: one gap closed, counts
      changed, and the contract's own KIND list left behind. Read-only.
  report:
    path: docs/maintenance/AIF120_WORKBENCH_SELF_DESCRIPTION_TEST_V1.md
    kind: measurement
---

# AIF-120 -- can the design table describe its own Workbench? (re-measurement)

**PRIOR ART: `AIF120_SAMPLE_MEASUREMENT_V1.md` section 6 asked this question
first and answered it.** I ran the crosswalk without finding that document,
which makes this the THIRD time this lane has re-done existing work -- its
standing constraints say so in as many words: *"Always look for prior art before
building. Twice this lane has written a procedure for a mechanism that already
existed."* Recorded rather than quietly folded in, because the count matters
more than my embarrassment.

**What survives is the DELTA**, and it is worth having: that measurement predates
R85.

Measured 2026-09-16 at `447962ccd`. Read-only.
Author: `member.ai.claude.cowork`. Owner: `member.derald`.
Status: **review-needed.**

---

## 0. What changed since the measurement that already existed

| | AIF120_SAMPLE_MEASUREMENT_V1 (pre-R85) | here, at `447962ccd` |
| --- | --- | --- |
| `wxSplitterWindow` | 3 uses, **"no word"** | 4 uses, **`splitter` -- CLOSED by R85** |
| `wxDialog` | 2 uses, "no word" | 2 uses, still no word |
| `wxScrolledWindow` | 1 use, "no word" | 1 use, still no word |
| `wxChoice` | 2 uses, "approximate" | 2 uses, **confirmed wrong** -- section 4 |

**Three gaps became two.** And the reason a reader following the charter still
sees three is section 3: the contract's KIND list was never updated for R85, so
the authority the charter points at gives the pre-R85 answer.

---

## 0b. Why the test, and why now

Owner ruling, 2026-09-16: **the redesigned Workbench is generated from its own
design table.**

The lane's charter says the deliverable is *"a portable UI description other
people can generate frontends from."* `dottalk_wb` is hand-written wx. **If the
table cannot describe the Workbench, that is the sharpest available evidence
that it is insufficient** -- and a redesign is the only moment the question is
cheap to ask, because nothing has been built on the answer yet.

This is also the first test of the vocabulary against a **running program this
house wrote**, rather than against the VFP corpus. R66 did that once, for
`ERSATZ GRID`, and it produced five new kinds. This is the same move at whole-
application scale.

---

## 1. The crosswalk

Every `new wx*` construction in `src/gui/wx/*.cpp`, against section 4's
vocabulary.

| wx class | uses | `KIND` | note |
| --- | ---: | --- | --- |
| `wxGrid` | 12 | `grid` | R66 |
| `wxStaticText` | 10 | `label` | |
| `wxTextCtrl` | 8 | `text` | |
| `wxMenu` | 7 | `menu` | |
| `wxButton` | 7 | `button` | |
| `wxPanel` | 5 | `panel` | |
| `wxSplitterWindow` | 4 | `splitter` | R85 -- **not in the contract's list, section 3** |
| `wxCheckBox` | 3 | `check` | |
| `wxNotebook` | 2 | `pageset` + `page` | |
| `wxChoice` | 2 | `combo` | see section 4 |
| `wxStaticBoxSizer` | 1 | `group` | |
| `wxListView` | 1 | `list` | |
| `wxListBox` | 1 | `list` | |
| `wxMenuBar` | 1 | `menu` | section 11 |
| `wxFrame` | 1 | `form` | |
| **`wxDialog`** | **2** | **none** | **gap -- section 2** |
| **`wxScrolledWindow`** | **1** | **none** | **gap -- section 2** |
| `wxBoxSizer` | 17 | *(none, by design)* | geometry is INTENT |
| `wxFlexGridSizer` | 1 | *(none, by design)* | geometry is INTENT |

**The sizers are not gaps and must not be counted as such.** `FLOW` and
`ORDINAL` exist precisely to replace them; a kind named `boxsizer` would be the
contract failing, not succeeding. Nineteen distinct classes, seventeen of them
answered.

---

## 2. The two gaps

Both are absent from the contract entirely -- **zero occurrences** of either
word across its ~1,100 lines.

### 2a. `wxDialog` -- nothing in the vocabulary says MODAL

`form` is the only container of that shape, and the contract never distinguishes
a modal dialog from a top-level frame. Two uses in the Workbench.

**This is not cosmetic.** Section 4 rules that a conformant reader meeting an
unknown `KIND` **must refuse the document and name the kind**, and must not
render a placeholder. So a design table authored from today's Workbench would be
**refused by its own reader**, at its dialogs.

Open question for the owner: is a modal a `form` carrying a property, or its own
kind? A property is cheaper; a kind is honest if modality changes what a backend
must do rather than how it looks -- and for a character-cell target it does.

### 2b. `wxScrolledWindow` -- nothing says SCROLL

One use. Plausibly a `PROP` rather than a `KIND`, since scrolling is a
behaviour a container has rather than a thing on the screen. No ruling picks,
and section 7's rule is that `PROPS` are **adopted, not invented**, so it cannot
be added by an author acting alone.

---

## 3. The contract's own KIND list is one behind the code

Section 4 opens: *"v1 names **nineteen** kinds"*, and lists them. `splitter` is
not among them. R85 ruled it in -- *"the design table now has a word for the
sash, and it is a KIND rather than a property so a target that cannot draw one
has to say so"* -- and the 2026-08-20 closeout records `KINDS` as **20**.

The word `splitter` appears **once** in the whole contract, in the R85 argument
that `Weight` cannot describe a sash. It never reaches the vocabulary list.

Per the lane's own authority chain, `AIF120_DESIGN_TABLE_CONTRACT_V1.md` is what
answers *"what does a field/kind/property MEAN"*. **So the authority is behind
the implementation on its most load-bearing list.** A reader following the
charter to that document gets nineteen and the code has twenty.

Not a defect in the splitter work -- a ruling landed and one document did not
catch up. It is the same shape as the superseded closeout: the record is thick,
and the piece of it a newcomer is told to trust went quietly stale.

---

## 4. `combo` does not cover `wxChoice`, and this is now measured

The prior measurement called this *"approximate -- `combo` means the editable
one"* and left it. It is worse than approximate.

`gui/uidef/uidef_wx.py:277` renders the kind as:

```python
'combo':  'new wxComboBox(%s, wxID_ANY, wxEmptyString, %s, %s)'
```

**`wxComboBox` is editable; `wxChoice` is not.** So a generated Workbench would
put a control accepting arbitrary typed text where the hand-written one offers a
fixed set. That is not a cosmetic loss -- it ADDS an affordance the document did
not ask for.

The charter's second governing fact is *"Four backends, and each must SAY what
it cannot do. A target that silently drops something the document states is the
defect."* Silently GAINING a capability is the same defect in the other
polarity, and the vocabulary currently has no way for the document to state
which one it meant. Two uses in the Workbench.

## 5. What this measures, and what it does not

- **It counts constructions, not screens.** Twelve `wxGrid` uses may be one grid
  built twelve ways or twelve grids. The crosswalk tests VOCABULARY COVERAGE,
  which is the question asked; it is not an inventory of the Workbench's layout.
- **It reads `src/gui/wx/` only** -- `main.cpp`, `main_frame.cpp`,
  `memo_browser_frame.cpp`. Anything the Workbench renders through
  `src/gui/core/` or through a registry under `gui/uidef/` is not counted.
- **It does not test BINDING, PROPS, HANDLERS or geometry.** A kind existing is
  necessary and nowhere near sufficient; `grid`'s columns must be declarable as
  a tuple spec, and that is a separate pass.
- **No fixture was generated and no document was authored.** This is the
  feasibility question answered ahead of the work, not the work.

---

## 6. The finding, stated plainly

**The design table can describe its own Workbench, with two named gaps and one
documentation drift.** For a vocabulary assembled from a target-platform
intersection and a VFP corpus, meeting a real wx application at seventeen of
nineteen classes is a strong result for the charter's central claim.

The three things that must happen before a Workbench design table can be
authored are all rulings, not code:

1. **Rule `modal`** -- property on `form`, or its own kind.
2. **Rule `scroll`** -- `PROP` or `KIND`.
3. **Update the contract's section 4 to name twenty**, so the document the
   charter points at stops being behind the code.

4. **Split `combo`**, or give it a property that says editable. Section 4 shows
   the current word renders `wxComboBox` unconditionally.

And the process item, which is not about kinds at all: **this crosswalk existed
and was re-run.** Whatever else comes of the redesign, the lane's prior-art
constraint has now been missed three times, and each miss was a search that did
not start at the index of what the lane already measured.
