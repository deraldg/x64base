---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260818-COWORK-007
  recorded_at_utc: 2026-08-18T15:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 6d52c6d6f
  authorization:
    requested_by: maintainer (member.derald), in-session, uploaded ACCOUNTS.SCX/.SCT/.DBF/.FPT against AIF-120 -- "we also support vfp and its fields so it is also a good empirical test"
    scope: >
      Parses a real VFP 9 wizard-generated form and records what the .SCX
      actually contains, as the empirical baseline for the AIF-120 UI DSL.
      Findings only. No parser, no schema, no code proposed here.
  report:
    path: docs/maintenance/AIF120_VFP_SCX_EMPIRICAL_BASELINE_V1.md
    kind: measurement
---

# AIF-120 -- what a real .SCX actually contains

Status: measurement, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Date: 2026-08-18. Lane: AIF-120.
Companion: `APPLICATION_UI_DSL_LANE_V1.md`.
Specimen: `ACCOUNTS.SCX` / `.SCT` / `.DBF` / `.FPT`, maintainer-supplied
2026-08-18, VFP 9 wizard-generated single-table CRUD form.

Everything below was read out of the files, not recalled. Parser: a throwaway
Python DBF/FPT reader; memo occupancy was counted per field so that "empty"
is a measurement rather than the absence of output from a possibly blind
reader.

## The specimen

`ACCOUNTS.SCX` is a DBF, version byte `0x30`, 26 records, 23 fields, 109-byte
records, with `.SCT` as its memo sidecar (8,404 B, block size 1). Twenty of the
23 fields are memo. The form is the wizard "embossed" style over a single table.

`ACCOUNTS.DBF` is version `0x30`, 118-byte records, **zero rows**, ten fields:

| field | type | width | dec |
| --- | --- | --- | --- |
| ACCOUNTID | C | 15 | 0 |
| ACCOUNTNUM | C | 15 | 0 |
| ACCTNAME | C | 30 | 0 |
| ACCTTYPE | C | 20 | 0 |
| DESCRIPT | M | 4 | 0 |
| STARTDATE | D | 8 | 0 |
| TAXABLE | L | 1 | 0 |
| UNITS | N | 5 | 0 |
| TOTALDUE | N | 15 | 2 |
| NOTE | M | 4 | 0 |

All ten are bound by the form. The table is empty, so it is a schema donor and
not a data specimen. Six of the seven x64base field types appear (C, M, D, L, N),
which makes this a usable type-coverage probe as well as a layout one.

**The `.DBF`/`.FPT` pair was locked on first read** (`Permission denied`) while
`.SCX`/`.SCT` opened fine, because VFP still had the table open. Worth knowing
before any tooling tries to read a live VFP working set: the form definition is
readable while the data is not.

## Record shape

Records are **flat, with parentage by name**, not nested. `PARENT` is a string
matching another record's `OBJNAME`. A reader has to rebuild the tree.

`PLATFORM` discriminates: 24 records are `WINDOWS`, and **records 0 and 25 are
`COMMENT`** -- not objects at all. Record 25 holds the font table
(`Arial, 0, 9, 5, 15, 12, 32, 3, 0` and two more). A loop that treats every
record as an object emits two phantom controls. Filter on `PLATFORM` first.

## The portability seam: BASECLASS, not CLASS

This is the central finding and it decides the shape of the whole lane.

| BASECLASS (portable) | n | CLASS (VFP-specific) | n |
| --- | --- | --- | --- |
| label | 10 | embossedlabel | 10 |
| textbox | 7 | embossedfield | 7 |
| editbox | 2 | embossedmemo | 2 |
| dataenvironment | 1 | dataenvironment | 1 |
| cursor | 1 | cursor | 1 |
| form | 1 | embossedform | 1 |
| checkbox | 1 | embossedlogic | 1 |
| container | 1 | txtbtns | 1 |

Every visual control carries **both**: a `BASECLASS` naming what it *is*, and a
`CLASS` naming the wizard subclass that styles it. `CLASSLOC` for every one of
them is a relative path climbing five levels out of the project:

```
..\..\..\..\..\program files (x86)\microsoft visual foxpro 9\wizards\wizembss.vcx
..\..\..\..\..\program files (x86)\microsoft visual foxpro 9\wizards\wizbtns.vcx
```

So **an `.SCX` is not self-contained.** Its appearance lives in `.VCX` libraries
outside the project, addressed by a relative path that only resolves on a machine
with that exact VFP install at that exact drive layout.

The consequence for AIF-120 is a ruling, not a preference: **key the importer on
`BASECLASS` and treat `CLASS` as an optional theme hint.** A `textbox` is a
textbox on Win32, Qt, TurboVision and HTML; `embossedfield` is a bevel that
exists in one wizard on one product. An importer keyed on `CLASS` cannot open a
form authored by anyone whose VFP is installed elsewhere -- which is most people,
including this specimen's own `..\..\..\..\..` escape. Keying on `BASECLASS`
degrades gracefully to an unstyled but correct form; keying on `CLASS` fails
closed. Eight base classes cover this entire CRUD form.

## The form carries no behavior at all

Occupancy across all 26 records, counted rather than assumed:

| memo field | non-empty |
| --- | --- |
| PROPERTIES | 25 |
| CLASS / BASECLASS / OBJNAME | 24 |
| CLASSLOC | 22 |
| PARENT | 22 |
| **METHODS** | **0** |
| **OBJCODE** | **0** |
| PROTECTED, OLE, OLE2, USER | 0 |
| RESERVED1 / 2 / 4 | 1 each |

`METHODS` and `OBJCODE` are empty in **every** record. All behavior -- navigation,
add, edit, delete, find, print -- lives in the `.VCX` classes. An importer that
reads only `.SCX` therefore recovers **layout and data binding, and zero logic**.
That is a real scope boundary for the lane and should be stated in the charter
rather than discovered during implementation. Hand-authored forms will populate
these; wizard-generated ones do not.

## Coordinate model, answered empirically

`Form1` carries `ScaleMode = 3`, with `Height = 411` and control positions in the
same unit (`Left = 94`, `Top = 57`, `Width = 115`). VFP `ScaleMode` 3 reads as
pixels and 0 as foxels; this specimen is pixels.

The ruling this supports: **the DSL must carry an explicit scale mode**, because
the `.SCX` carries one. Assuming pixels would silently misplace every control in
a foxel-authored form, and foxel forms are common in older 2.6-era conversions.
This closes one of the two preconditions the charter named before syntax work.
The threading ruling remains open; nothing in this specimen speaks to it.

## Four traps a naive importer walks into

1. **Off-canvas parking.** `layoutsty.Left = 4004` with `layoutsty.Visible = .F.`
   The wizard parks its style container far off the form rather than deleting it.
   An importer that honors `Left` and ignores `Visible` renders a stray container
   4,004 pixels to the right and a canvas twenty times too wide.

2. **Runtime state stored as properties.** `BUTTONSET1` carries `oldtalk`,
   `oldsetdelete`, `oldreprocess`, `oldmultilocks`, `oldsetfields`,
   `oldbuffering`, `nworkarea`, `previewmode`, `previewinit`, `usedataenv`,
   `editmode`, `addmode`, `topfile`, `endfile`, `viewkey`, `parentkey`,
   `viewtype`, `gridalias`, `gridref`. These are **saved VFP session state**, not
   GUI properties, and nothing in the record marks them as such -- they sit in the
   same `PROPERTIES` memo, in the same `name = value` form, as `Top` and `Left`.
   There is no flag to filter on. **A GUI DSL needs an allow-list of properties
   it understands and must drop the rest**, because a deny-list cannot be written
   against a vocabulary that every third-party VCX extends.

3. **Mnemonic escapes in captions.** `cmdAdd.Caption = "\<Add"` and
   `cmdEdit.Caption = "\<Edit"`. `\<` is VFP's accelerator marker, equivalent to
   `&` in Win32 and Qt. Passed through literally, the user sees `\<Add` on the
   button and loses the keyboard accelerator.

4. **Dotted property paths address children of a class instance.**
   `cmdPrev.Enabled = .F.`, `Label1.Caption = "ACCOUNTS"`,
   `layoutsty.Shape1.Name = "Shape1"`. A record's `PROPERTIES` memo sets
   properties on objects that have **no record of their own** -- they come from
   the `.VCX`. So the object tree is not fully described by the record set; part
   of it is only reachable by resolving the class library.

## Data binding maps cleanly onto what we already have

The `dataenvironment` record parents a `cursor` record:

```
Alias              = "accounts"
CursorSource       = accounts.dbf
BufferModeOverride = 5
```

and every control binds with `ControlSource = "accounts.<field>"`, table-dot-field.
`InputMask` supplies the format vocabulary: `XXXXXXXXXXXXXXX` for character,
`99,999` for the integer, `999,999,999,999.99` for the currency. These are PICTURE
clauses in all but name.

This is the half of the problem x64base is already good at. Alias, cursor source,
buffer mode and table.field binding all have counterparts in the existing cursor
model, and `InputMask` maps onto PICTURE. **The data side is close to a rename;
the visual side is where the lane's actual work is.**

## What this specimen does NOT establish

- **Grids, pageframes, option groups, combos, toolbars, menus.** None appear.
  The base-class census above is 8 wide because the form is simple, not because
  the vocabulary is.
- **Hand-authored forms.** Everything here is wizard output, which is why
  `METHODS` is empty everywhere. A hand-written form is the harder specimen and
  the one that will show what the DSL must do about code.
- **`.MNX` menus.** The maintainer's original interest was the FoxPro menu
  syntax; nothing in an `.SCX` speaks to it. A menu specimen is a separate ask.
- **Foxel-scaled forms.** `ScaleMode = 3` here means the foxel path is inferred
  from the field's existence, not exercised.

## Suggested next measurement

A hand-authored `.SCX` with real method code, and one `.MNX`. Those two would
close the vocabulary question that this specimen opens but cannot answer.

# SECOND SPECIMEN 2026-08-18: `form1.scx`, and two claims above are wrong

Maintainer supplied `form1.scx` / `.SCT` the same day: 32 records, 30 objects,
a deliberate one-of-everything form over `payment_methods` in
`event management.dbc`. It answers the vocabulary question and **falsifies two
statements made above from a single specimen.**

## Correction 1: an `.SCX` is not necessarily dependent on external classes

Above reads: "So **an `.SCX` is not self-contained.**" That generalised one
wizard-generated file. In `form1.scx`, **`CLASSLOC` is non-empty in 0 of 32
records** and `CLASS` equals `BASECLASS` throughout. The form is entirely native
base classes and is completely self-contained.

The correct statement: **an `.SCX` is self-contained if and only if its controls
are native base classes; wizard or library subclasses make it dependent on
`.VCX` files addressed by a fragile relative path.** Both kinds exist in the
wild and an importer meets both.

Ruling R1 is unaffected and in fact strengthened -- keying on `BASECLASS` is what
lets one importer read both files, since the self-contained form has nothing
else to key on.

## Correction 2: the scale mode is often absent, so the default matters

Above reads: "Real source files declare theirs." **`form1.scx` contains no
`ScaleMode` property on any object.** A form that omits it inherits the VFP
default rather than declaring pixels.

So the requirement is stronger than "carry the unit": **the reader must supply
the correct default when the property is absent, and the DSL must record which
default was applied.** An importer that reads `ScaleMode` and does nothing when
it is missing gets a silently unitless document -- which is the same failure R2
was written to prevent, arriving through the door R2 left open.

## The vocabulary, now measured rather than guessed

Twenty-four base classes in one form, against eight in `ACCOUNTS.SCX`:

```
textbox 4, header 3, grid 2, and one each of:
dataenvironment, cursor, form, label, editbox, commandbutton, commandgroup,
optiongroup, checkbox, combobox, listbox, spinner, image, timer, pageframe,
olecontrol, oleboundcontrol, line, shape, container, hyperlink
```

This is the mapping surface for AIF-120. `grid`, `pageframe`, `optiongroup`,
`commandgroup`, `combobox`, `listbox` and `spinner` were all named above as
absent from the first specimen; all are present here.

## R5 (new): identity is the dotted path, never OBJNAME

`OBJNAME` is **not unique within a form**. This file contains three records named
`Header1` and four named `Text1`. They are distinguished only by `PARENT`, and
`PARENT` is itself sometimes a dotted path:

```
OBJNAME=Header1  PARENT=form1.grdPayment_methods.Column1   Caption="Payment Method ID"
OBJNAME=Header1  PARENT=form1.grdPayment_methods.Column2   Caption="Payment Method"
OBJNAME=Header1  PARENT=form1.grdPayment_methods.Column3   Caption="Credit Card?"
```

So neither end of the parent relation is a bare name. **Object identity is
`PARENT + "." + OBJNAME`.** A reader that keys a dictionary on `OBJNAME` keeps
one of the three column headers and silently drops the other two, producing a
grid whose columns are all captioned the same.

## R6 (new): part of the object tree has no records at all

`Column1`, `Column2` and `Column3` are named as parents but **have no records of
their own**. They exist because the grid carries `ColumnCount = 3`. The same
pattern appears three more times in this file:

| parent | count property | children |
| --- | --- | --- |
| `grdPayment_methods` | `ColumnCount = 3` | Column1..3, each with a `header` and a `textbox` record |
| `Pageframe1` | `PageCount = 2` | Page1, Page2 (properties only) |
| `Commandgroup1` | `ButtonCount = 2` | Command1, Command2 (properties only) |
| `Optiongroup1` | `ButtonCount = 2` | Option1, Option2 (properties only) |

**Part of the object tree is generated by property VALUES rather than described
by records.** An importer must materialise implicit children from the count
property before it can attach the records that hang off them. Walking records
alone loses six real objects in this file -- the three grid headers and three
grid textboxes, which is every visible label on the grid.

This was measured the hard way: the reader written this morning reported those
six as "unresolved parents ... they come from the class library", which was a
plausible and wrong explanation. They come from a count property in the same
file.

## The OLE control is opaque and should be declared out of scope

`Olecontrol1` carries `OLE` = 2,560 bytes and `OLE2` = 77 bytes. The payload
begins `D0 CF 11 E0 A1 B1 1A E1`, the OLE2 compound-file signature. This is an
embedded Windows COM object. There is no portable rendering of it and no
reasonable way for a cross-platform DSL to carry it. `olecontrol` and
`oleboundcontrol` should be **named as unsupported in the charter's scope
section**, so an importer refuses them loudly rather than emitting an empty box.

## Small traps this specimen adds

- **`Database = event management.dbc`** -- an unquoted value containing a space.
  A property parser splitting on whitespace loses the filename.
- **`RecordSourceType = 1`** with `RecordSource = "PAYMENT_METHODS"`: the grid
  binds to an alias, while its columns bind with `ControlSource` to
  `PAYMENT_METHODS.field`. Two binding mechanisms in one control.
- **`Caption = "ee"`** on the form, and `Label1.Caption = "Label1"`. Placeholder
  text; nothing to read into it.

## Still outstanding after two specimens

`METHODS` and `OBJCODE` are empty in **0 of 32** records here too. Both specimens
are designer output, so **R4 remains untested in the direction that matters**: no
file yet observed carries code, so nothing proves the reader can extract it. A
form with a real `Click` method is still the missing specimen, and so is an
`.MNX`.

# THIRD SPECIMEN 2026-08-18: four `.MNX` menus and two `.MPR` generated programs

Maintainer supplied `test_main`, `test_top`, `test_go` and `test_append` as
`.MNX`/`.MNT` pairs, plus `TEST_GO.MPR` and `TEST_MAIN.MPR`. APPBUILDER output
against `TEST_APP.H`. This closes the menu question and settles R4.

## The headline: the menu DSL already exists, as text, and VFP emits it

`.MPR` is a plain-text program generated from the `.MNX` by GENMENU. The whole of
`TEST_GO.MPR`'s menu definition is:

```
DEFINE PAD _msm_Go OF _MSYSMENU PROMPT "\<Go" COLOR SCHEME 3 ;
        BEFORE _MWINDOW ;
        KEY ALT+G, "ALT+G" ;
        MESSAGE "Navigates the currently selected table, cursor, or view"
ON PAD _msm_Go OF _MSYSMENU ACTIVATE POPUP _mgo

DEFINE POPUP _mgo MARGIN RELATIVE SHADOW COLOR SCHEME 4
DEFINE BAR 1 OF _mgo PROMPT "\<Top"
...
ON SELECTION BAR 1 OF _mgo APP_GLOBAL.GoTop()
...
ON SELECTION POPUP _mgo MESSAGEBOX(APP_FEATURE_NOT_AVAILABLE_LOC,0,APP_GLOBAL.cCaption)
```

**AIF-120 does not need to invent menu syntax.** The maintainer's original
instinct -- that the FoxPro menu language is a good candidate for a common GUI
interface -- is confirmed by the strongest possible evidence: the language exists,
it is textual, it is declarative, and Microsoft shipped a reference implementation
that produces it. Better still, every `.MNX` with its `.MPR` is a **free
input/output test pair**: a generator written for this lane can be checked
against GENMENU's own output rather than against opinion.

## The full menu vocabulary, counted in `TEST_MAIN.MPR`

| statement | count |
| --- | --- |
| `DEFINE BAR` | 60 |
| `ON SELECTION BAR` | 28 |
| `DEFINE POPUP` | 9 |
| `ON SELECTION POPUP` | 7 |
| `ON PAD` | 7 |
| `DEFINE PAD` | 7 |
| `SET SKIP OF BAR` | 6 |
| `SKIP FOR` | 4 |
| `SET SYSMENU TO / SAVE / AUTOMATIC / DEFAULT` | 5 |
| `ON BAR` | 2 |

Clause vocabulary: `MARGIN`, `RELATIVE`, `SHADOW`, `COLOR SCHEME n`, `BEFORE`,
`KEY`, `MESSAGE`, `NEGOTIATE`, `SKIP FOR`. Plus, in the cleanup section,
`RELEASE BAR / POPUP / PAD`, `ACTIVATE MENU ... NOWAIT`.

**This splits the lane's menu scope in two, and the charter should say which it
covers.** There is a declarative half (`DEFINE ...`) and an imperative runtime
half (`SET SKIP OF BAR`, `RELEASE POPUP`, `ACTIVATE MENU`) that mutates a live
menu. A DSL that covers only definition is coherent and much smaller; one that
covers mutation needs a live object model, which is exactly what the charter's
stopping rule says should stay hidden.

`SKIP FOR` is the conditional-enablement mechanism and it holds real expressions:

```
SKIP FOR TYPE("_SCREEN.Activeform") # "O" OR _SCREEN.ActiveForm.ShowWindow = 2
SKIP FOR EMPTY(AUSED(latemp))
```

That is host-language evaluation embedded in a menu definition. Any portable
target has to either evaluate it or refuse it.

## R4 is settled: menus carry code, and the reader extracts it

The open question after two form specimens was whether any designer file carries
code at all. In `test_go.mnx`: `PROCEDURE` non-empty in 1 of 14 records, `SETUP`
non-empty in 1 of 14.

```
SETUP     (file header record): #INCLUDE [..\TEST_APP.H] and the APPBUILDER banner
PROCEDURE (popup container)   : MESSAGEBOX(APP_FEATURE_NOT_AVAILABLE_LOC,0,APP_GLOBAL.cCaption)
COMMAND   (9 of 10 bars)      : APP_GLOBAL.GoTop(), APP_GLOBAL.DoSort(,,,.F.), ...
```

**R4 stands as written for `.SCX`** -- wizard forms keep behavior in their `.VCX`
-- **but it was never a property of the file format.** The reader extracts code
fine; the first two specimens simply had none. The distinction matters because
R4 was one measurement away from being written into the charter as a format
limitation, which it is not.

## R8 (new): a third parenting mechanism, sharing nothing with the first two

| format | how structure is expressed |
| --- | --- |
| `.SCX` wizard | `PARENT` = flat name |
| `.SCX` native | `PARENT` = dotted path, plus implicit children from count properties |
| `.MNX` | `LEVELNAME` (owning container) + `ITEMNUM` (ordinal within it) |

`.MNX` has no `PARENT` column at all. `OBJTYPE` classifies the row -- 1 file
header, 2 container, 3 item -- and containers carry `NUMITEMS` as a declared
count that can be checked against the rows found, which is a built-in integrity
check the format offers for free and the reader now performs.

**The designer formats share a container and nothing else.** They are all DBFs;
their structural conventions are unrelated. An importer needs a per-format
structure pass and can share only the DBF/memo layer beneath it.

## The `\<` and `\-` conventions are confirmed across formats

`.SCX` showed `Caption = "\<Add"`. `.MNX` shows `PROMPT = "\<Go"`, `"\<Top"`,
`"Set \<Filter..."`, and `"\-"` for a separator. Verified: **`PROMPT` passes
through to the `.MPR` verbatim in all 10 of 10 bars**, mnemonics included. So the
escape is not a designer artifact, it is the language's own syntax, and a DSL
adopting this vocabulary inherits it.

## Round-trip verified, with two fidelity notes

Checked `test_go.mnx` against `TEST_GO.MPR` mechanically:

- 10 MNX items to 10 MPR bars, **same numbering**: `ITEMNUM` becomes the `BAR n`
  ordinal directly.
- Bars carrying `ON SELECTION` are exactly the rows with a non-empty `COMMAND`
  column: `{1,2,3,4,6,7,8,9,10}` both ways. Bar 5 is the `\-` separator and
  correctly gets no action.

Two things a round-trip test must handle:

1. **GENMENU lowercases.** The container is `_mGo` in the `.MNX` and `_mgo` in
   the `.MPR`. A comparison that does not fold case reports a spurious diff.
2. **`.MPR` is not a pure function of the `.MNX` columns.** `MARGIN`, `RELATIVE`
   and `SHADOW` appear in every generated popup and correspond to no memo or
   column in the table -- GENMENU emits them unconditionally. A DSL adopting
   `.MPR` syntax must decide, clause by clause, which parts are semantic and
   which are generator boilerplate, or it will faithfully reproduce decoration
   it does not understand.

## Reader status

`read_vfp_binary.py` gained a `menu` mode. Both structural modes refuse the wrong
format by name rather than producing empty output: `form` on an `.MNX` reports
the missing object columns, `menu` on an `.SCX` reports the missing menu columns.
