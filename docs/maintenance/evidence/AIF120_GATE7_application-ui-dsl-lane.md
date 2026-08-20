---
title: Application UI DSL
description: A portable UI description for DotTalk++ -- and the reason it is a table rather than a syntax.
---

# Application UI DSL

**Status: chartered and in progress.** AIF-120, lane `application-ui-dsl`.
Every ruling behind this page is marked *review-needed*; the authoring agent does
not self-approve.

This page previously said "Planned, not implemented" and proposed a command
syntax. Both parts are now out of date, and the second one is out of date in an
interesting way, so this page explains what changed rather than quietly
overwriting it.

## What the seed proposed

```
CREATE MENU MainMenu
CREATE WINDOW CustomerWin
CREATE DIALOG EditCustomer
DEFINE BUTTON Save
ON CLICK DO save_customer
```

That is the FoxPro screen-and-menu vocabulary, and it is still the right
vocabulary. What the lane changed is where it lives.

Worth noting, because it is easy to miss: `CREATE MENU` already appears in the
product's command catalogue, flagged *"Static historical reference entry. Not the
live DotTalk++ command contract."* The seed was proposing to implement words the
product already documents as history. That is a good sign about the vocabulary and
says nothing about the mechanism.

## What the lane built instead: a table

The deliverable is a **design table** -- a DBF with a memo sidecar -- and the DSL
text is a convenience over it, not the other way round.

The reason is thirty years old. In 1994 the FoxPro screen designer stored its work
as a database table, because the tool was built by database people who reached for
the thing they had. An `.SCX` was a `.DBF`. **You could `USE` your user
interface.** DotTalk++ is a DBF engine that wants a portable UI description, and
the same answer is still the right one, for the same reason.

A table has a property a syntax does not: **other people can generate frontends
from it without parsing anything.** A generator needs a schema, not a grammar.

## The schema

Three record kinds -- `DOC`, `FONT`, `OBJ` -- across sixteen fields:

    RECKIND  OBJID  PARENT  ORDINAL  TABORDINAL  SPAN  KIND  FLOW
    BINDING  FONTREF  PROVENANCE  PROPS  ORIGIN  HANDLERS  SOURCE  NOTES

Twenty object kinds:

    form panel group pageset page splitter
    label text button check radio list combo image menu
    grid tree detail summary statusbar

And a closed property vocabulary, keyed by record kind -- `Caption`, `Weight`,
`Fill`, `Order`, `RowLimit`, `MinPane`, `ReadOnly`, `Columns`, `ColumnWidths`,
`Shows`, `Mask`, `Filter` on an object; `SourceFile`, `Version`, `Title` on the
document; `Name`, `Size`, `Metrics` on a font.

Geometry is **intent**, not position: `FLOW` and `ORDINAL` describe how things are
arranged, and absolute coordinates are quarantined in `ORIGIN` with their unit
attached. A pixel does not travel to a character grid; "this row, in this order,
taking this share of the width" does.

## Four backends, and each one says what it cannot do

The same document renders through wxWidgets, Tk, HTML and a character grid. That
is the portability claim, and it is only worth something if the failures are
audible. So the rule this lane actually enforces is:

> A target that cannot honour something the document says must SAY SO, by name,
> every run. Silence is the defect.

The clearest example is the `splitter` -- a draggable boundary with two panes:

| target | what it does | what it loses, out loud |
|---|---|---|
| wxWidgets | `wxSplitterWindow`, sash at the stated position | nothing |
| Tk | `ttk.PanedWindow`, sash at the stated position | `MinPane` -- ttk has no per-pane minimum |
| HTML | flex panes, boundary at the stated position | the drag *target* -- CSS `resize` is a corner grip, not a sash |
| character grid | a column of `\|` at the derived cell | dragging; and it reports the pixel-to-cell division it performed |

Two of those are worth reading together: **Tk keeps the sash gravity and has no
minimum pane; a browser keeps the minimum pane and has no gravity at all.** Neither
toolkit carries both facts. The document carries both -- which is the strongest
evidence so far that this is not a transcription of any one toolkit.

## Proof gates

Adopted from this page's original list, plus four added by the charter.

| # | Gate | State |
|---|---|---|
| 1 | Syntax contract and examples | **Partial** -- the table contract is written and exercised by 29 documents; there is no DSL *text* syntax yet |
| 2 | Command registry entries | **Open, and smaller than it looks.** DotScript is a line iterator over the same executor the prompt uses, against a single command registry -- so there is no grammar to write. A command registered once is reachable from the prompt, from every `.dts`, and from ERSATZ and INIT |
| 3 | TUI proof for menu, window, dialog, button, event handler | **Partial** -- a character-cell backend renders windows, containers and controls; menus are imported but the `menu` kind is the one kind with no proof behind it |
| 4 | HELP / CMDHELP coverage | **Open** -- follows gate 2; there are no commands to document yet |
| 5 | SelfDoc metadata coverage | **Open** |
| 6 | Manualgen section | **Open** |
| 7 | Website comparison update | **In progress** -- this page |
| 8 | A coordinate-model ruling, recorded before the schema is fixed | **Closed** -- geometry is intent; absolute position quarantined |
| 9 | A threading ruling -- handlers on the UI thread with explicit hand-off, or a background construct with a defined completion path. Silence fails | **Closed** |
| 10 | The design table documented as a standalone contract, readable by someone with none of this source | **Substantially done** -- and this page is a fair test of it |
| 11 | A second backend spiked from the TABLE, not a parser | **Done** -- four of them, built and run |

## What this does not do yet

Stated here so nobody has to discover it:

- **Nothing has been built outside gcc 13 / wxWidgets 3.2.4 / Linux.** MSVC is the
  oldest open item in the lane by a wide margin, and a *failure* there would be
  more useful than another green Linux build.
- **No CLI commands.** Today a document is authored and read by tooling, not by
  typing `CREATE WINDOW` at a prompt. That gap is narrower than it sounds:
  DotScript is a line iterator over the same command executor the interactive
  prompt uses, against a single registry, so the seed's syntax needs commands --
  not a language. Whatever gets registered is scriptable the moment it exists.
- **`menu` is the one kind with no first-class proof.**
- **Paging is unfinished.** Data frames fill once; nothing recomputes them when the
  cursor moves.

## Recent additions

- The property vocabulary is now closed per record kind, and an unknown key is
  reported by name rather than ignored. Measured across 29 documents and 297
  rows, it fires exactly once -- on a property this lane invented and has not yet
  implemented.
- The tooling was found to be unbuildable from a clean checkout: eleven scripts
  imported a file that is deliberately untracked, one of them from inside the
  build. Fixed, and a check now derives the rule from the import graph instead of
  a hand-kept list.

## Why the rulings read the way they do

Each unit in this lane lands as a numbered ruling with a measurement, a way to
disprove it, and a note saying what changed, whose area it touched, and how to undo
it. Several rulings are corrections of earlier rulings, and one is void. That is
deliberate: the record is meant to show how a conclusion was reached and where it
was wrong, not to present a clean sequence that nobody actually walked.
