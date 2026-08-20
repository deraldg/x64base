---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-093
  recorded_at_utc: 2026-08-20T23:55:00Z
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
    baseline_commit: fbd6f56ed
  authorization:
    requested_by: maintainer (member.derald), in-session -- "does gold stadard say
      property", then "build it", closing R77's sash finding which had sat open
      through six rulings.
    scope: >
      Add `splitter` to the design table's KIND vocabulary, carry it into all four
      backends, and prove it built and RUN. Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_SPLITTER_KIND_V1.md
    kind: ruling
---

# AIF-120 -- R85: the sash is a kind, and an unweighted one lies

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

The shipped frame has three draggable boundaries and the design table had no word
for any of them. R77 found that and it sat open through six rulings. This ruling
gives it a word. The word is a **KIND** -- `splitter`, the twentieth -- and not a
`Sash` property, and the deciding argument is not aesthetic: **an unknown KIND is
REFUSED by contract section 4; an unknown PROPERTY is silently ignored.** A
document that names a boundary a backend cannot draw should hear about it. Then,
building it, the thing worth a ruling turned up: **a splitter that does not fill
its parent cannot honour its own ORIGIN, and says nothing about it.**

## 1. The ruling

**R85. A draggable boundary is a KIND with exactly two panes. Its FLOW says
which way the boundary runs. Its ORIGIN says where the boundary starts. Its
panes' Weight IS the sash gravity. Only `MinPane` is new vocabulary.**

Nothing here is invented. The mapping is total and it is a mapping onto words the
contract already had:

| the toolkit fact      | the document already had | spelled            |
|-----------------------|--------------------------|--------------------|
| orientation           | FLOW                     | `row` = a vertical sash |
| initial sash position | ORIGIN (R12)             | `origin_width` / `origin_height` |
| sash gravity          | child Weight (R79)       | `w1 / (w1 + w2)`   |
| minimum pane size     | -- nothing --            | `MinPane`, px      |

One new property against three re-used ones is the test R79 should have been held
to and was not. That is the whole argument for KIND-over-property: the vocabulary
does not grow, the *refusal surface* does.

**R85.1. A splitter that does not fill its parent may not state an ORIGIN.**
REFUSED, not noted. See section 3 -- this is measured, and it is the finding.

**R85.2. A pane may itself be a splitter, and a pane always fills.** So R85.1
does not apply to a splitter whose parent is a splitter: `Split*()` gives a pane
the whole side and there is no proportion to state.

**R85.3. Weight and Fill own different axes, and the Tk backend was reading only
one of them.** See section 5.

## 2. What the twenty KINDs now are

    form panel group pageset page splitter
    label text button check radio list combo image menu
    grid tree detail summary statusbar

## 3. R85.1 -- the finding, measured

P7 was built twice from the same document. One emitted argument changed.

    Add(splitter, 0, wxALL, 6)             sash lands at 119
    Add(splitter, 1, wxALL|wxEXPAND, 6)    sash lands at 220

The document said `origin_width = 220` both times. Unweighted, the splitter is
laid out at its BEST size -- 245 px for two empty panes -- and wx clamps a 220
sash against a 120 `MinPane` down to an even split. Silently. The screen then
contradicts the document and nothing anywhere says so.

This is refused rather than noted because **the author cannot know the best
size**: it depends on the pane contents, the font and the platform. An ORIGIN
under an unweighted splitter is not wrong, it is UNPREDICTABLE, and a coordinate
that might mean itself is worse than one that does not. R79 already gives the
document the words to fix it -- `Weight` and `Fill` -- so the refusal costs an
author one line and buys a coordinate that means what it says.

`N12_splitter_origin_no_weight` is that document, kept as a fixture. It is the
P7 that shipped for one afternoon.

## 4. Proof: built AND run, all four backends, one document

`P8_splitter_nested` transcribes `main_frame.cpp:697-703` -- a vertical sash at
220 whose SECOND pane is itself a horizontal splitter at 500. Measured off the
rendered pixels, not eyeballed:

| backend        | outer sash | inner sash | what it loses |
|----------------|-----------|-----------|----------------|
| wx (gcc 13, wx 3.2.4, Xvfb) | 220 | 500 | nothing |
| Tk (ttk.PanedWindow)        | 220 | 500 | `MinPane` -- ttk has no per-pane minimum |
| HTML (chromium headless)    | 220 | 500 | the drag TARGET -- CSS `resize` is a corner grip, not a boundary |
| character cell              | col 31 (220/7) | reported, not placed | drag; and a column sash on a content-grown canvas |

Every loss in that last column is REPORTED by the backend that takes it, by name,
every run. None of them is a comment in a file.

Two of them are worth reading together, because they are opposite:

- **ttk.PanedWindow keeps Weight and has no MinPane.**
- **A browser keeps MinPane (`min-width`) and has no gravity at all.**

Neither toolkit carries both facts. The document carries both. That is the
clearest evidence so far that the design table is not a transcription of any one
toolkit -- if it were, it would have exactly one of these.

## 5. R85.3 -- found by looking at a splitter, and not about splitters

The Tk backend packed a child as `fill='both' if Fill else 'none'` in a row, and
`fill='x' if Fill else 'none'` in a column. Both read `Fill` and ignore `Weight`.
So Tk granted a weighted child its share of the slack with `expand` and then left
the widget at its own size inside that share, centred.

R79 defines the two words on different axes -- Weight is the share of the FLOW
axis, Fill is stretch ACROSS it -- so the mapping is mechanical:

    row      Weight -> x     Fill -> y
    column   Weight -> y     Fill -> x

The old row mapping also over-reached: `Fill` alone produced `both`, stretching
along the flow axis as well, so a document that asked for the cross axis got
both.

**Blast radius, measured before and after over all 19 rendering fixtures: one.**
P8, the fixture that exposed it. Eighteen renders byte-identical.

It took a splitter to find this because a splitter is the first child whose own
size is the entire point. A label that comes out its natural size inside a
too-large share looks fine.

## 6. Corrections owed, and they are mine

1. **P7 mis-transcribed the source it claimed.** `PROVENANCE: measured`, and it
   dropped `root_sizer->Add(work_splitter, 1, wxEXPAND ...)` -- the proportion
   and the expand flag -- from `main_frame.cpp:703`. That omission is R85.1's
   whole finding, arrived at by building my own error.
2. **P7's first nested rewrite invented a call the source does not make.** I gave
   the inner panes Weight 1 and 0, which generated `SetSashGravity(1.0000)`.
   `main_frame.cpp` calls `SetMinimumPaneSize` and never `SetSashGravity`. The
   rendered inner sash came out at 601 instead of 500 and the fixture would have
   been filed as a measurement. Corrected: the true transcription states no
   Weight on either inner pane, emits no gravity call, and lands at 500.
3. **The gravity formula was written `w2/(w1+w2)` in a comment in `manifest.py`**
   -- from memory, after the code had already been corrected to `w1/(w1+w2)` by
   measurement. A stale comment beside correct code is a trap laid for the next
   reader. Corrected, with the measurement written beside it.
4. **This work was done in two scratch copies and not in the working tree.**
   `uidef_wx.py` was edited under `/home/claude/r66/tools/uidef/` -- a path that
   does not exist in this repository -- and the checker and fixtures under a
   third copy, while `D:/code/ccode/gui/uidef/` had none of it. That is
   correction 52 violated in the exact shape correction 52 describes. All seven
   files were reconciled onto the working tree and verified byte-identical by
   md5 before this ruling was written. Both scratch copies were supersets of the
   tree, so nothing was lost -- which is luck, not method.

## 7. How to disprove this

- **R85.1 is wrong** if a splitter with no Weight in a sizer honours its ORIGIN
  on any platform. Build `N12_splitter_origin_no_weight`, run it, measure the
  sash. If it lands at 220, the refusal is over-broad and should become a NOTE.
- **R85.2 is wrong** if a splitter nested in a splitter needs a proportion. P8
  states none on `INNER` and lands at 500; a platform where it does not would
  disprove it.
- **The KIND-over-property argument is wrong** if a target can be shown to
  usefully ignore a boundary it cannot draw. The counter-evidence is in the
  refusal itself: before the Tk backend gained `PanedWindow`, `manifest.py`
  reported `REFUSE kind splitter (x1) -- target does not render this kind` with
  no code written. A `Sash` property would have produced silence.
- **R85.3 is wrong** if some document depends on `Fill` meaning both axes in a
  row. Eighteen of nineteen fixtures say no; a corpus document could say yes.

## 8. What this does NOT do

- **MSVC.** Still the oldest open item. Nothing in R70-R85 has been built outside
  gcc 13 / wx 3.2.4 / Linux.
- **The character cell's column sash.** It reports the row it would have used and
  then puts the boundary under the first pane, because the canvas grows to its
  content and there is no height to divide. That is R81's wall, not a new one.
- **`ReadOnly` / `Multiline` on a `text` pane.** P8 states both, from the
  measured `wxTE_MULTILINE|wxTE_READONLY|wxTE_RICH2`; the wx backend emits a
  plain `wxTextCtrl` and says nothing. Found while reading generated output for
  this ruling, reported here, not fixed here.
- **`menu`** remains the one KIND with no splitter-grade proof behind it.

## 9. Good Neighbor note

- **What changed:** `gui/uidef/` -- one new KIND across `uidef.py`, `manifest.py`,
  `author_cases.py` and all four backends; two new fixtures (`P8`, `N12`); one
  fixture corrected (`P7`); one Tk layout correction (R85.3).
- **Whose area:** AIF-120, lane `application-ui-dsl`. No file outside
  `gui/uidef/` and `docs/maintenance/` is touched. No engine source, no gate.
- **What authorization:** maintainer, in-session, "build it".
- **How to verify:** `python3 author_cases.py`, then
  `python3.12 manifest.py N12_splitter_origin_no_weight.DBF` (expect the R85.1
  REFUSE), then `python3 uidef_wx.py P8_splitter_nested.DBF p8.cpp` and build it.
- **How to undo:** revert this commit. The KIND is additive -- no existing
  document names `splitter`, so nothing already written changes meaning. The one
  exception is R85.3, which changes Tk layout for any document combining `Fill`
  with a row flow; that is section 5, and its blast radius over the fixtures is
  one.
