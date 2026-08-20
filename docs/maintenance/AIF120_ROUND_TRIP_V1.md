---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-087
  recorded_at_utc: 2026-08-20T15:00:00Z
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
    requested_by: maintainer (member.derald), in-session -- "begin", authorising
      the round trip R77 named as its own next unit.
    scope: >
      Author a UIDEF document describing src/gui/wx/main_frame.cpp, generate a wx
      frontend from it, build and run it, and report what did not survive.
      READ-ONLY against src/gui/wx. Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_ROUND_TRIP_V1.md
    kind: ruling
---

# AIF-120 -- R78: the round trip lost no CONTROLS and lost WEIGHT, which every toolkit has and the design table does not

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R77 measured vocabulary and called a round trip its next unit. This is it:
`author_mainframe.py` describes `src/gui/wx/main_frame.cpp` as a UIDEF document,
`uidef_wx.py` generates C++ from that document, and the result builds and runs.
**47 records, 45 elements, zero refusals** -- the language carried the whole tree,
including a nested `pageset` inside a `pageset`. What it could not carry was not an
exotic control. It was **proportion**: 13 of the sample's 33 sizer additions say
"take the remaining space", and UIDEF's `FLOW` has no way to say it. The render
shows a recognisable frame in which nothing stretches.

**Evidence tier: runtime-proven.** Built against wx alone -- no engine, because the
default generator is engine-free by R70's opt-in design -- and captured.

## 1. What survived

```
python author_mainframe.py         -> MAINFRAME.DBF   47 records
python uidef_wx.py MAINFRAME.DBF   -> 165 lines, 46 widgets
g++ ... $(wx-config --libs)        -> mainframe_demo
```

Rendered: the toolbar in order (`Open Table`, `Refresh`, `Close Area`, `Command`,
a text field, `Run`), the `Areas` label and list, the notebook with its tabs, a
grid inside the Tables page, and a status bar. The character-cell backend renders
the same document with `elements 45   refused 0`.

The tree that survived includes the part I expected to be hardest -- `pageset`
inside `page` inside `pageset`, seven pages then five, which no prior document in
this lane has ever nested.

## 2. What did not survive, in order of how much it matters

### 2a. WEIGHT. `FLOW` declares ORDER and CONTAINMENT, not PROPORTION

Measured in `main_frame.cpp`: **33 sizer additions carry an explicit proportion.
20 are `0` (fixed) and 13 are `1` (take the remaining space)**, alongside 27
`wxEXPAND` flags. The thirteen are:

```
command_   areas_   ddict_status_   ddict_source_text_   ddict_splitter
work_splitter   root   editor   field   box   scroll   text   grid
```

Every one of them is a child that must grow. `command_` is the wide command box in
the toolbar; `areas_` is the list that fills the left pane; `root` is the panel
that fills the frame. In the generated render they are all at their minimum size,
which is why the window looks emptied out rather than wrong.

R12 ruled that **layout intent is the portable geometry**, and quarantined absolute
coordinates because they do not travel. Weight is the opposite case and the ruling
did not reach it: **proportion is the MOST portable part of layout intent.** Every
toolkit in this lane's four backends has it -- wx `proportion`, Tk `weight`, CSS
`flex-grow`, and a character-cell renderer needs it to decide which region absorbs
the leftover columns. UIDEF captured order and containment and dropped the one
property all four targets share.

This is not the splitter problem in a smaller hat. A sash is negotiable geometry
that the user edits (R77 section 3); proportion is **declared** geometry the author
fixes, which is exactly the kind R12 says belongs in the document.

### 2b. The three sashes, now visible rather than argued

`220`, `500`, `260` -- the sash positions of `work_splitter`, `splitter` and
`ddict_splitter`. R77 recorded that UIDEF has no word for them. In this document
each splitter became a `panel` with a fixed `FLOW`, and the numbers had nowhere to
go. The render shows the consequence: the boundaries exist and cannot be moved.

### 2c. `CreateStatusBar(4)` collapses to one string

The sample creates four independent status fields and writes them separately:

```cpp
SetStatusText(gui_text(GuiTextId::Ready, locale_), 0);
SetStatusText(gui_text(GuiTextId::NoOpenAreas, locale_), 1);
SetStatusText("0 rows", 2);
SetStatusText("Recno: none | Logical row: none | Order: physical", 3);
```

Contract 4b(c) gives `statusbar` a `Shows` list closed to six values, rendering one
string. Four fields is not four `Shows` values; it is four regions. Not
expressible.

### 2d. R33.4 was ruled and never implemented

Every visible string in the sample is `gui_text(GuiTextId::X, locale_)` -- a
message-catalog key, not a literal. **This lane already ruled that.** R33.4, in
`AIF120_LOCALE_AND_ENCODING_V1.md`:

> the caption should be a reference, not a literal -- `Caption =
> @FORM_STUDENTS_TITLE` -- resolved by the target through the message catalog

Measured: no tool handles a leading `@` (checked `uidef.py`, `manifest.py`,
`uidef_wx.py`, `uidef_tk.py`), and the contract's five `Caption` mentions do not
describe one. **The ruling is right, the sample corroborates it at a scale no
authored document could, and nothing carried it into the contract or the tools.**

That is this session's signature finding for the fourth time -- a declaration
nothing acted on -- and the first time it belongs to a ruling made long before this
session. The captions in `author_mainframe.py` are therefore English literals the
sample does not contain, and the file says so.

### 2e. A grid whose rows come from code is not describable

Contract 10c requires a `grid` to carry a tuple spec in `BINDING`. The sample's
twelve grids are filled programmatically. The document leaves `BINDING` empty,
which is honest and means `stream_refusals` would refuse every one of them for
stream binding -- correctly, since there is no spec to bind. A screen whose data
arrives through a handler has no `BINDING` to declare, and the contract has no word
for "rows supplied by the target".

## 3. R78.1 -- a generator defect the round trip found and eighteen fixtures did not

The first build warned twice:

```
warning: unused variable 'w_NB_sizer'
warning: unused variable 'w_DD_NB_sizer'
```

A `pageset` adds its children through `AddPage`, never through a sizer -- and the
generator already knew, because it skips `close_sizer` for `pageset`. But it still
called `child_sizer()`, creating a `wxBoxSizer` that nothing added to and nothing
set.

**Not one of the eighteen fixtures has a `pageset`,** so nine rulings of sweeps
never surfaced it. The first document to nest one found it immediately.

Same class as R70.3 and correction 54 -- something emitted with no consumer -- and
the third time this lane has paid for that shape. Fixed by not creating the sizer.
All eighteen fixtures remain **byte-identical** without `--stream`, because none of
them could reach the branch.

## 4. Proof

| | |
|---|---|
| document | `MAINFRAME.DBF`, 47 records, authored by `author_mainframe.py` |
| character-cell | `elements 45   refused 0   derived-geometry containers 2` |
| generated | 165 lines, 46 widgets |
| built | wx 3.2.4 alone, **no engine** -- the default generator has no engine dependency (R70) |
| warnings after R78.1 | **0** |
| invariance | 18/18 fixtures byte-identical without `--stream` |
| ran | captured, `docs/maintenance/evidence/AIF120_R78_roundtrip.png` |

The two `DERIVED` notices are correct and expected: `pageset` with `FLOW = free`
and no `ORIGIN` falls back to `ORDINAL` order under R23.3, which is what a notebook
wants anyway.

## 5. Deliberately NOT designed here

No vocabulary is added -- same discipline as R74 and R77, for the same reason.

The candidate this ruling raises, for whoever rules on it:

- **A weight on the child, not the container.** wx puts proportion on the `Add`, Tk on the row/column, CSS on the item. The design table's `ORDINAL` and `SPAN` already live on the child row, which suggests a sibling field or a `PROPS` value rather than a container property -- but that is a contract decision and 13-of-33 is the evidence for making it, not the design.
- R77's open candidates (`splitter`, `dialog`, scrolling, `combo`/`choice`) are unchanged.
- **R33.4 needs carrying into the contract and the tools**, or withdrawing. It has been a ruling nothing implements for long enough that a hand-written GUI independently proved it right.

## 6. Good Neighbor

| | |
|---|---|
| What changed | new `gui/uidef/author_mainframe.py`; `gui/uidef/uidef_wx.py` (R78.1, one line); this ruling; one evidence image; ledger rows |
| Whose area | AIF-120. `src/gui/wx` was **read only** -- the sample is the maintainer's template and nothing here touches it |
| Authorization | maintainer, in-session: "begin" |
| How to verify | `cd gui/uidef && python author_mainframe.py && python uidef_text.py MAINFRAME.DBF`, then generate and build per section 1 |
| How to undo | `git revert`. The 18 fixtures are byte-identical before and after |
| Risk | low. One generator line, reachable only by a document containing a `pageset` |

## 7. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git status -uall

git add gui/uidef/author_mainframe.py
git add gui/uidef/uidef_wx.py
git add docs/maintenance/AIF120_ROUND_TRIP_V1.md
git add docs/maintenance/evidence/AIF120_R78_roundtrip.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md

git status -uall

git commit -m "AIF-120: R78 -- the round trip carried the whole tree with zero refusals and lost WEIGHT; 13 of 33 sizer adds say take the remaining space and FLOW cannot"
```
