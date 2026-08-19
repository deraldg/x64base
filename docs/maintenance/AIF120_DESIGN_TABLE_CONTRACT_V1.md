---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-019
  recorded_at_utc: 2026-08-19T01:42:35Z
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
    baseline_commit: 7858acfa9
  authorization:
    requested_by: maintainer (member.derald), in-session, "keep going"; v1 scope chosen
      by the maintainer from an offered list -- forms and menus, contract prose plus
      field tables, reports deferred.
    scope: >
      Proof gate 10 of the Application UI DSL lane (AIF-120): the design table
      documented as a standalone contract. Draft for review; the author does not
      self-approve.
  report:
    path: docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
    kind: contract
---

# AIF-120 -- the UIDEF design table, v1 contract (proof gate 10)

Status: **DRAFT contract, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

The charter calls this the lane's actual deliverable: *"The table schema is the
deliverable. A text DSL that only ever fed FoxTalk would be a private
convenience; a documented design table with one interpreter and one generator is
a contract other people can build against."*

**Scope of v1: forms and menus.** Reports are deferred -- `.FRX` is measured
(M7, R15) but has no rulings, and adding it would need several.

**The test this document must pass** is the charter's own: *"could someone
implement this vocabulary on a platform nobody here has seen, working from the
specification alone?"* Everything needed is below. No file in this repository is
required reading.

---

## 1. What UIDEF is

**A DBF table with a memo sidecar.** Rows are objects. One document -- one form
or one menu -- is one table.

That choice is not decoration. This project is a DBF engine, so a UI definition
stored as a DBF is readable by `USE`, browsable by `BROWSE`, indexable, and
diffable through tooling that already exists. It is also what FoxPro did in 1994
for the same reason.

A consumer needs **only this document and a DBF reader**. It does not need the
DSL text, a parser, or any of this project's source.

## 2. The three record kinds

Every row is one of three kinds, given by `RECKIND`:

| `RECKIND` | meaning | count |
| --- | --- | --- |
| `DOC` | document header -- version, defaults, data source | exactly 1, first record |
| `FONT` | one font metric row | 0 or more, contiguous, after `DOC` |
| `OBJ` | a container, control, or menu item | 1 or more |

`DOC` first and `FONT` rows before any `OBJ` are **required on output** and
**must not be assumed on input** -- a conformant reader locates records by
`RECKIND`, never by position. (`.SCX` puts its header first and its font table
last; do not inherit that.)

## 3. Field-by-field

`R` marks requiredness, and it has **three values, not two** -- see section 6.

| field | type | R | meaning |
| --- | --- | --- | --- |
| `RECKIND` | C(4) | P+C | `DOC`, `FONT`, `OBJ` |
| `OBJID` | C(12) | P+C | identity. Unique within the document. Opaque; never parsed |
| `PARENT` | C(12) | P | `OBJID` of the containing object. Empty on `DOC`, `FONT`, and the root object |
| `ORDINAL` | N(5,0) | P | position among siblings, ascending, gaps allowed |
| `TABORDINAL` | N(5,0) | O | focus order among siblings, independent of `ORDINAL`. `0`/absent = the target derives it and must say so. Added 2026-08-19 by R27, the owner's decision; see `AIF120_TAB_ORDINAL_RULING_V1.md` |
| `SPAN` | N(5,0) | O | cells spanned in a `grid` flow. Default 1 |
| `KIND` | C(20) | P+C | the portable class name -- section 4 |
| `FLOW` | C(8) | P on containers | `row`, `column`, `grid`, `free`. Section 5 |
| `BINDING` | C(64) | O | data field this control reads and writes, as `alias.field` -- see section 10b |
| `FONTREF` | N(3,0) | O | 1-based index into this document's `FONT` rows. 0 = target default |
| `PROVENANCE` | C(10) | P | `authored`, `imported`, or `inherited` -- a row materialised from an object's class (R31) |
| `PROPS` | M | O | property text -- section 7. Named keys so far: `Caption`, `Mask` (R25), `Columns` on a `grid` container (R23.2), `Class` and `ClassSource` on an instance (R31), and the menu keys of section 11. Everything else passes through under the source's own key |
| `ORIGIN` | M | O | quarantined absolute geometry -- section 8 |
| `HANDLERS` | M | O | handler references -- section 9 |
| `SOURCE` | M | O | data source, relative to this document -- section 10 |
| `NOTES` | M | O | free text. Never interpreted |

Record length is not fixed by this contract. Column **order** is not significant;
a reader locates fields by name.

## 4. `KIND` -- the portable class vocabulary

v1 names **fourteen** kinds. They were selected as the intersection of what every
platform in the charter's target list provides, cross-checked against 3,010
measured object records.

**Containers:** `form`, `panel`, `group`, `pageset`, `page`
**Controls:** `label`, `text`, `button`, `check`, `radio`, `list`, `combo`, `image`
**Menus:** `menu`

A conformant reader that meets an unknown `KIND` **must refuse the document and
name the kind**. It must not render a placeholder. (R7's rule, generalised: an
importer that emits an empty box for something it does not understand produces a
document that looks correct and is not.)

Kinds deliberately absent from v1, with the ruling that excludes them: `grid` and
`pageframe` children generated by count properties (R6 -- implicit children are
unsolved); `olecontrol`, `oleboundcontrol` (R7 -- no portable rendering); `timer`,
`custom` (non-visual); anything report-shaped (out of v1 scope).

## 5. Geometry is INTENT. `FLOW` and `ORDINAL` are the whole model

Per R12: **layout intent is the portable geometry.** A container declares a
`FLOW`; its children declare `ORDINAL` and optionally `SPAN`. That is all a
conformant generator needs.

| `FLOW` | meaning |
| --- | --- |
| `row` | children left to right in `ORDINAL` order |
| `column` | children top to bottom in `ORDINAL` order |
| `grid` | children in reading order, wrapping; `SPAN` gives cells consumed |
| `free` | children positioned only by `ORIGIN`. **A generator may refuse `free`** |

Portable because ordinal containment is the one primitive every candidate has:
Turbo Vision nests `TRect`s, wx nests sizers, Qt nests layouts, Tk packs and
grids, the browser flows boxes.

> **TESTED 2026-08-19 by R34 and R35**, and this claim holds. One document carrying
> **zero coordinates** was rendered by three backends -- Tk (`place`/`pack`/`grid`,
> pixels), a browser (flexbox and CSS grid, pixels) and a character grid (no pixels,
> no fonts) -- and all three return the **identical** verdict from the table alone:
> two derivations, one refusal, for the same rows and the same reasons.
>
> `SPAN` and `TABORDINAL` are not conveniences of the first toolkit that met them.
> CSS grid spells `SPAN` as `grid-column: span N` and a browser spells `TABORDINAL`
> as `tabindex`, an attribute that exists precisely because focus order and layout
> order are different orders. Neither had to be translated for the second target;
> both were already its own model.

**An absent dimension is never defaulted to a number, and for many controls a
PRESENT one is ignored too** (R16, R17). A control that does not state a size gets
one from its content and its font -- from the `FONT` rows if
`FONTREF` is set, from the target's own font otherwise. A reader that derives a
dimension **must record that it derived it** and must never write the derived
value back into `ORIGIN`. (R12.3. Writing it back launders a guess into a
measurement.)

### 5b. FIRST TEST OF SECTION 5 -- imports are `free`, and R19 says that is CORRECT

> **THIS SECTION'S FRAMING WAS WITHDRAWN BY R19, same run, 2026-08-19.** What
> follows called the high `free` rate a **defect in this contract**. It is not. It
> is a fact about how forms were authored, and `free` plus an `ORIGIN` group is the
> **correct** representation of most imported documents.
>
> Two things were wrong with the test below. It clustered `TOP` independently,
> which baseline offsets defeat -- a label sits four units below its own field, so
> nine visual rows present as eighteen `TOP` values. And its lattice criterion was
> permissive to the point of meaninglessness: `19 tops x 3 lefts >= 19` holds for
> almost any arrangement, so it measured "no two controls share a coordinate".
>
> A correct method -- cluster on `LEFT` only, sort each column by `TOP`, read rows
> off by index, and treat a real form as **a grid plus outliers** -- infers
> `STUDENTS.SCX` as `grid, 2 columns x 9 rows + 1 outlier` and `ACCOUNTS.SCX` as
> `2 x 10 + 1`, both exactly right, where the test below called both `free`.
> Corpus-wide it finds **fewer** grids, not more: **16%** of 228 container groups
> against the 40% below, because the 40% counted arrangements that are not grids.
>
> **So 84% of real container groups genuinely are not row, column or grid**, and
> `free` is not an inference failure. `tools/uidef/infer_flow.py`, ruling
> `AIF120_FLOW_INFERENCE_V1.md`.
>
> **The correction this section proposes is still required, for a better reason.**
> A generator that refuses `FLOW = free` refuses most real documents
> **permanently**, not until an importer improves. Section 12 must be narrowed
> either way.
>
> **And R12 is confirmed with its scope measured.** Layout intent is right for
> AUTHORED documents -- the hand-authored test document is `FLOW = column` with no
> `ORIGIN` on any row and it renders. For imports the intent mostly does not exist
> to recover. UIDEF has two permanent populations, and an interchange format must
> represent what documents ARE.
>
> The original text follows as the record of what was claimed.

#### Original 5b, withdrawn -- imports are `free`, not `grid`

Run the same day this contract was drafted, against 228 container groups in 170
real forms. **The finding contradicts how section 5 reads.**

**What the test did.** For each container, cluster children's `Top` and `Left`
values with a tolerance, then classify: one row cluster -> `row`; one column
cluster -> `column`; a lattice no larger than 1.5x the child count -> `grid`;
otherwise `free`.

| tolerance | `row` | `column` | `grid` | **`free`** | expressible |
| --- | --- | --- | --- | --- | --- |
| 0 (exact) | 17 | 2 | 5 | **204** | 11% |
| 4 | 19 | 2 | 17 | **190** | 17% |
| 8 | 22 | 3 | 28 | **175** | 23% |
| 12 | 24 | 4 | 64 | **136** | 40% |

**Between 60% and 89% of real container groups do not express as
row/column/grid.**

**Why exact matching fails, which is the transferable part.** `STUDENTS.SCX` is
the cleanest imaginable case -- nine label/textbox pairs, labels at `Left = 10`,
textboxes at `Left = 71`, rows spaced 24 apart. A human sees a 2x9 grid. The
data says **nineteen** distinct `Top` values, because each label sits **4 units
below** its textbox:

```text
top=57  left=71  textbox SID1
top=61  left=10  label   LBLSID1
top=81  left=71  textbox LNAME1
top=85  left=10  label   LBLLNAME1
```

That is baseline alignment. **Visual alignment is not numerical alignment**, so
any derivation of layout intent from absolute coordinates needs tolerance
clustering, and this contract says nothing about it. Even with tolerance,
`STUDENTS.SCX` still classifies `free` because one button container sits at a
third `Left` -- real forms mix an aligned majority with outliers.

**A caution on the numbers.** The classifier is crude and the percentages move
with both the tolerance and the lattice criterion. **Treat the direction as the
finding, not the figure.** What is robust: exact matching is hopeless, tolerance
helps and does not rescue, and the majority stays `free` under every setting
tried.

**The contradiction this exposes in the contract as drafted.** Section 5 presents
`FLOW`/`ORDINAL` as the model and section 8 calls `ORIGIN` advisory, which a
generator "may ignore entirely and remain conformant". Section 12 then permits a
generator to refuse `FLOW = free`. Put together: **a conformant generator may
refuse the majority of imported documents, and may ignore the only field those
documents carry their layout in.**

**What this does NOT overturn.** R12 chose layout intent for *authored*
documents, and that choice stands -- it was decided on the sequencing argument,
and nothing here touches it. `ORIGIN`'s quarantine is also vindicated: it is not
a nicety for round-trip fidelity, it is **the load-bearing path for every
import**.

**Proposed correction, for owner ruling rather than steward fiat.** Section 8's
"a generator may ignore `ORIGIN` entirely" and section 12's "may refuse
`FLOW = free`" must both be narrowed. A defensible pair: a generator may refuse
`free` **only if** it also refuses documents whose `PROVENANCE` is `imported`;
and a generator that accepts `free` **must** honour `ORIGIN`, since there is
nothing else to lay the document out with. Recorded as a defect against this
draft, not silently patched into it.

## 6. Requiredness has three values, and this is the contract's sharpest rule

R13 was found by writing a real designer format and being refused twice. A schema
that records only "required / optional" is insufficient, because **requiredness
is not symmetric**.

| mark | meaning |
| --- | --- |
| **P** | required to PRODUCE. A writer must emit it. A reader may still find it absent in a non-conformant document and should say so |
| **C** | required to CONSUME. A reader must understand it. A document lacking it is invalid |
| **O** | optional to produce, and safely omitted. A reader must tolerate absence |

Worked example, from the format this was learned on: VFP's `.SCX` requires
`CLASS` on output -- omitting it makes VFP 9 refuse the file -- while an importer
may correctly ignore it and key on `BASECLASS`. **Optional to consume, mandatory
to produce.** A schema with two categories cannot express that, and a generator
built from such a schema emits files the reference implementation rejects.

There is a third asymmetry, found the same way: VFP writes `RESERVED4` into every
`.SCX` DataEnvironment and does not require it -- our generated file omitted it
and was opened, run and round-tripped anyway. That is the **O** case, and it is
invisible unless you write the format and get away with leaving something out.

## 7. `PROPS` -- adopted, not invented

Per R15, three of the four FoxPro designer formats carry a `name = value`
property mini-language, and share key names for the objects they share. **UIDEF
adopts it.**

```text
Caption = "Customer name"
Enabled = .T.
MaxLength = 40
```

Rules:

- one property per line, `name` `=` `value`, terminated by CRLF
- names are case-insensitive and must not be interpreted as paths
- values: `"quoted string"`, a number, `.T.`/`.F.`, or bare text
- **an unknown property is dropped silently, never rejected** (R3 -- import is an
  allow-list; a deny-list cannot be written against a vocabulary every third
  party extends)
- `PROPS` never carries geometry. Geometry is `FLOW`/`ORDINAL`, or `ORIGIN`

## 8. `ORIGIN` -- quarantined, advisory, and carrying its own unit

Absolute coordinates are permitted and **advisory**. Same property text form:

```text
ORIGIN_TOP = 24
ORIGIN_LEFT = 10
ORIGIN_WIDTH = 200
ORIGIN_SCALE = px
```

> **SUPERSEDED IN PART by R16 and R17, 2026-08-19, both runtime-proven.** The two
> permissions below -- honour it, or ignore it entirely -- were both measured and
> **both are wrong**. Honouring every width truncates every label on a toolkit
> whose font differs from the authoring font; ignoring every width discards field
> sizing the document knows and the target cannot infer. Evidence:
> `docs/maintenance/evidence/AIF120_width_ace.png`.
>
> The rule that replaces them, for SIZE only -- position is unaffected:
>
> | control | width comes from |
> | --- | --- |
> | content-sized (`label`, `button`, `check`, `radio`, `group`, `page`) | its own content in the target's font (**R16**) |
> | data-sized and **bound** | its **`Mask`**, which the schema determines (**R25**, narrowing R17) |
> | data-sized and **unbound** | `ORIGIN_WIDTH` with its `ORIGIN_SCALE` |
| a **container whose children carry `ORIGIN`** | its own stated width and height (**R30.3**) -- nothing else can supply them, because absolutely positioned children report no size |

### 8b. Units, and the conversion this section still does not give

**Added 2026-08-19 by R35.** `ORIGIN_SCALE` enumerates units and gives conversions
between none of them, which gate 11 logged as G-6 before a consumer needed one.

Measured: **20 objects in the corpus declare a `ScaleMode` and all 20 say pixels.**
The `cell` value has been specified and produced by nothing. The character-cell
backend is the first consumer that needs `px` in cells, and it divides by 7 and 20
-- numbers taken from R25's own measurements -- and **declares the conversion as
derived on every render** (R12.3).

> Either this section gives conversions between its units, or it should enumerate
> only `px`. An unconvertible unit is a promise the format cannot keep.

**A coarse target bands before it quantises (R35.1).** Converting each
`ORIGIN_TOP` independently splits a visual row in two, because a label sits a few
pixels off its own field's baseline. That is R19's inference finding governing
rendering: 19 `ORIGIN_TOP` values on one real form band into **10 visual rows**
within 8 px, and without banding a label and its field land on different lines.
> | containers (`form`, `panel`, `pageset`) | `ORIGIN`, honoured |
>
> **A width for a content-sized or bound control therefore need not be carried at
> all**, and a target must prefer content or schema over any width that is.
> Measured basis: authored pixel width correlates with the bound field's declared
> width at **r = 0.9982** (`STUDENTS`, n=9) and **r = 0.9977** (`ACCOUNTS`, n=8),
> fit `px = 7.00 * chars + 11.4` -- the slope is the authoring font's character
> cell, which is exactly what does not travel.
>
> Rulings: `AIF120_ORIGIN_AB_RULING_V1.md`, `AIF120_BOUND_WIDTH_RULING_V1.md`.

- ~~a generator may ignore `ORIGIN` entirely and remain conformant~~ -- see above;
  position may be ignored, size is governed by R16/R17
- a generator that honours a **position** or an unbound size **must** honour
  `ORIGIN_SCALE` or refuse the row
- any member may be absent. Absence is normal: measured across 2,684
  geometry-bearing records in 170 real forms, 13.7% are partial, and containers
  are the ones that omit -- `form` 57%, `panel`-shaped 47%, while sized controls
  omit nothing
- **`ORIGIN_SCALE` is per group, not per document.** A real designer format was
  measured expressing object geometry in ten-thousandths of an inch and page
  geometry in tenths of a millimetre **in the same record, declaring neither**
  (M7). Per-document would be unable to express that document at all

`ORIGIN_SCALE` values: `px`, `pt`, `mm`, `in`, `cell`. No default. A row with
`ORIGIN_*` and no `ORIGIN_SCALE` is invalid.

## 9. `HANDLERS` -- references, never bodies

Per R14: measured across 2,404 real procedures in forms and class libraries,
**86% navigate the target's object model**. The charter's stopping rule forbids
exposing that model to the script, so **method bodies do not enter v1**.

```text
Click = SaveCustomer / ui
Init = LoadDefaults / ui
Export = BuildReport / worker -> ExportDone
```

Each line is `Event = HandlerName / DISPATCH [-> CompletionHandler]`.

`DISPATCH` is `ui`, `worker` or `host` (R11, R20):

- **`ui`** -- runs on the platform's UI-owning thread, must not block
- **`worker`** -- runs off it, must not touch any UI object, and **must** name a
  completion handler which runs under `ui`. The completion is delivered **at most
  once**: destroying the container drops it (R21.4)
- **`host`** -- names a capability the HOST provides, such as `edit.cut`. No thread
  rule, no completion path, no registry entry. A target that does not provide the
  named capability **refuses the item and names it** (R20, R22.4)

The default is `ui`, chosen so failures are loud: a handler wrongly on the UI
thread freezes and is found in the first minute; wrongly off it corrupts widget
state intermittently and is found on someone else's platform.

**Event names in v1 -- nineteen.** The original ten:
`Click`, `Init`, `Change`, `Activate`, `Deactivate`, `Destroy`, `Error`,
`Focus`, `Blur`, `Load`.

Nine added 2026-08-19 by **R32.2**, which measured 92 handlers being silently
discarded because this list was shorter than the format: `Unload`, `MouseMove`,
`MouseDown`, `MouseUp`, `DoubleClick`, `DragOver`, `DragDrop`, `KeyPress`,
`Validate`. `Unload` is 72 of the 92 -- this list carried `Load` and dropped the
teardown event that pairs with it, while R21 was ruling on teardown.

A handler name defined on an object's CLASS reaches the instance (**R32**); an
event the instance defines itself wins. A method whose name is not an event is a
custom method: v1 has no concept for one, and the importer names them rather than
mapping them onto an event the source never declared (R32.3).

An unknown event name is dropped with a diagnostic.

**Completion order is not guaranteed.** A completion handler receives a task
identity and a terminal state and must tolerate arriving out of order.

**Lifetime:** destroying a container cancels the pending work its handlers
submitted. Nothing queued may outlive the object that queued it.

## 10. `SOURCE` -- relative to this document, always

```text
Alias = customers
Table = ..\data\customers.dbf
Order = cust_id
Relation = customer -> orders ON cust_id
```

**`Relation` added 2026-08-19 by R36**, closing the gap R26.2 named. A `Relation`
line states that navigating the parent work area repositions the child. The **lock
domain** is the transitive closure of these edges, and per **R26** a mutating
handler must serialize against the whole domain, not the area it names -- measured
at 100 failures in 100 trials when it does not. A document with several work areas
and no `Relation` line is ambiguous between "each is its own domain" and "the
document did not say", and a reader should report which it assumed.

Resolution is **case-insensitive** (R28.3): a document whose `Table` does not
resolve is refused, never rendered unbound, because a width silently derived from a
schema that was never opened is worse than no width.

`Table` is **relative to the UIDEF document's own location**, never absolute and
never a bare name resolved against ambient state.

This was measured rather than designed. VFP was observed rewriting a data-source
path to `..\..\..\dottalkpp\data\dbf\vfp\students.dbf` when the form lived three
directories away, and to the bare `students.dbf` when the same form was saved
beside its table -- recomputed relative to the document on every save. The bare
filename is the zero-distance case, not a fallback. The same convention appears
independently in `.FRX` (`Database = ..\..\data\testdata.dbc`) and in `.SCX`
class-library references.

## 10b. `BINDING` is `alias.field`, and the areas are open before any handler fires

**Added 2026-08-19 by R53.** Gate 11's second-nearest fix was *"Define `BINDING`'s
syntax"*; the field table said only "data field this control reads and writes", and
`manifest.py` had been enforcing a rule the contract never stated.

Measured over the 170-form corpus -- 159 `ControlSource` occurrences:

| shape | count | share | ruling |
|---|---|---|---|
| `alias.field` | 145 | 91.2% | **the form.** `alias` MUST name an `Alias` declared in `SOURCE` |
| empty | 8 | 5.0% | legal; the control is unbound |
| object reference, e.g. `This.Parent.SysTray1.Tiptext` | 4 | 2.5% | **refused.** Not data -- see below |
| bare `field` | 2 | 1.3% | **refused.** Ambient state -- see below |

VFP writes the value **quoted** in the designer record (`"books.desc"`). `BINDING`
holds it **unquoted**; the quotes are the container's, not the value's.

Resolution of `alias` is case-insensitive, matching `Table` resolution in section 10.

**A bare field name is refused**, not resolved. It means "the field of whatever work
area is current", and section 10 already refuses that reasoning for `Table`: *"never
a bare name resolved against ambient state."* One rule, applied twice.

**An object reference is refused for a different reason, and the reason matters.**
`This.Parent.SysTray1.Tiptext` binds a control's property to *another control's
property*. It is not a malformed `alias.field`; it is a kind of thing UIDEF v1 does
not model at all. A reader that reports it as "not alias.field" tells the author
they made a typo, when what they actually did was use a feature that is absent. Until
R53 these fell through the alias lookup and were skipped in **silence**, which is
worse than either message.

### The work areas are open before the first handler fires

`SOURCE` names an `Alias` and a `Table` for each work area (section 10), and the lock
domain is computed from the `Relation` edges between them (R36, R26). Nothing said
who **opens** them, and the runtime's lock provider emits `SELECT <alias>` -- which
presumes the alias is already open in a work area of its own.

> **A conforming frontend opens every `Alias` declared in `SOURCE` into its own work
> area, resolving `Table` per section 10, before it fires any handler.** A `Table`
> that does not resolve is refused there, as section 10 already requires -- not at
> first use, when a handler is already mid-flight.

This was found by a harness that opened two tables into one work area, silently
replacing the first, and then released a lock it did not hold while the lock it did
hold stayed held (R52.4). The precondition had been implicit across R47, R48 and R49.

## 11. Menus

Menu rows are `OBJ` with `KIND = menu`, nested by `PARENT`, ordered by `ORDINAL`.

**A menu row must not carry `ORIGIN`.** Measured: four `.MNX` files, 205 records,
25 columns, **zero geometry columns of any kind**. Menus have never had position;
a v1 that adds one for symmetry makes the menu half unportable for no gain.

Menu-specific properties live in `PROPS`. **Corrected 2026-08-19 by R28.2**, which
measured the six keys named here against the thirteen a real menu table carries:

| key | on | what it is |
| --- | --- | --- |
| `Caption`, `Mnemonic` | items | the label and its accelerator index |
| `Key`, `KeyLabel` | items | the shortcut and its printed form |
| `Message`, `Mark`, `SkipFor` | items | status text, mark, skip condition |
| `Separator` | items | `.T.` on a separator |
| **`Container`** | popups | **the only thing distinguishing a popup from an item** |
| **`OpenerPrompt`** | popups | **the only caption a popup row carries** |
| `Name`, `OpenedBy`, `DeclaredItems` | popups | identity, opener, declared count |

`Container` and `OpenerPrompt` were undocumented, and section 7 permits a reader to
drop any property it does not know. Two sound rules that together **produce a blank
menubar** -- R28.2's ruling is that structure must never travel in a channel a
reader may discard. The two keys this section used to name, `Checked` and
`Enabled`, appear **zero** times; the real one is `Mark`.

The `\<` mnemonic escape and `\-` separator convention are the source vocabulary's
(R8). **In the source.** In a UIDEF table the escape is already resolved into a
`Mnemonic` index: measured, `\<` appears in **0 of 55** captions. The claim that it
is used "consistently in both captions and prompts" is true of `.MNX` and false
here (R28.4).

## 12. Conformance

**A conformant READER** locates records by `RECKIND`; understands every **C**
field; tolerates absent **O** fields; drops unknown properties silently and
unknown `KIND` loudly; honours `ORIGIN_SCALE` if it honours `ORIGIN` at all;
records any dimension it derived.

**A target may also IGNORE an optional property its medium has no concept for, and
must say so** (R35.3). A character grid has no fonts: it cannot honour `FONTREF`
and must not refuse a document over it. Ignoring is not refusal and it is not
honouring, and this section had no word for it until a target existed that needed
one.

**A conformant WRITER** emits every **P** field; emits `ORIGIN_SCALE` whenever it
emits any `ORIGIN_*`; never writes a derived dimension into `ORIGIN`; sets
`PROVENANCE`; writes `SOURCE.Table` relative to the document.

**A conformant GENERATOR** may ignore `ORIGIN` **positions**, must apply R16/R17
for sizes rather than either honouring or ignoring `ORIGIN` wholesale, must refuse
unknown `KIND`, and must implement `DISPATCH`. Its permission to refuse
`FLOW = free` is contested -- see 5b, which measures that doing so refuses the
majority of imported documents.

## 13. What v1 does not do, stated so nobody has to discover it

- **No method bodies** (R14). Handler references only.
- **No implicit children** (R6). `grid` and `pageframe` count-generated children
  are out; the two-format structure pass they need is unsolved.
- **No OLE** (R7).
- **No reports** -- deferred by the maintainer's scope call. `.FRX` is measured
  in M7 and R15 and would need its own rulings.
- **No live menu mutation** (R9) -- `SET SKIP OF BAR`, `RELEASE POPUP` and the
  rest need a live object model, which the stopping rule forbids.
- **No expression evaluation.** `SKIP FOR` embeds host-language expressions; v1
  carries them as opaque text in `PROPS` or refuses them, and does not evaluate.

## 13b. The container declares ONE codepage

Added 2026-08-19 by **R33.** Header byte 29 is VFP's language driver and it holds a
single value, so **every text value in a document shares one codepage**. A reader
decodes with the codepage the file declares, never with an assumed one; a writer
declares and encodes with the same codepage and refuses text that will not fit,
naming the character and the codepage rather than raising a codec error.

Round-tripped: cp1252, cp1250, cp1253, cp932 and cp1256 -- Western European,
Central European, Greek, Japanese and Arabic.

The consequence is a real limit, not a defect: **one document cannot mix Japanese
and Greek.** That is workable for a per-locale document set and fatal for one
document in many languages. R33.4 proposes the way out -- a caption that names a
message symbol resolved through x64base's existing catalog, which already carries
4,756 texts in five locales behind `SET LOCALE`. Then the table holds ASCII
identifiers and the catalog holds the prose. Proposed, not adopted.

Columns of type `I`, `Y`, `B`, `T`, `W`, `G` and `0` are **binary**, not text, and
are unpacked rather than decoded (R33.3).

## 14. Open against this contract

**Updated 2026-08-19, same run.** Items 1 and 2 as first drafted are no longer
true and are struck rather than deleted, so the record shows what was believed
when.

1. ~~**Not implemented.** No writer, no reader, no round-trip. This is a
   specification, tier `planned`.~~ **Implemented the same day.** A writer and
   conformance validator (`tools/uidef/uidef.py`), two readers (`import_scx.py`,
   `import_mnx.py`), three consumers (`uidef_tk.py`, `uidef_tk_menu.py`,
   `uidef_tk_host.py`), a requirements/refusal checker (`manifest.py`), and eleven
   evidence renders and transcripts. Tier: **runtime-proven** for forms and menus
   on one backend.
2. ~~**`FLOW` has never been exercised.** 60-89% of 228 real container groups
   classify as `free`.~~ **Exercised, and the measurement was wrong twice.** R19
   corrected the inference; R23.4 then found that 14 of those 228 parents were
   `dataenvironment`/`cursor`/`relation`, which have no layout. Current figure:
   **214 visual positioned groups, 26 expressible, 12.1%** -- `free` is 87.9%, and
   R19's ruling that this is correct rather than a failure stands.
3. **The fourteen `KIND` values are a judgement**, checked against measured
   vocabulary but not against a second backend. Unchanged. `pageset` rendered for
   the first time on 2026-08-19 (R24.3) after being in the vocabulary and in no
   consumer.
4. **Gate 11 is the acceptance test for this document** -- a frontend generated
   from this table alone, by someone holding nothing else. **Spiked, not met.** The
   Tk consumers were written by the same author as the table. `manifest.py`'s
   `minimal` profile describes a target nobody has built.
5. **`SOURCE` cannot express a relation** (R26.2). It carries `Alias`, `Table` and
   `Order` per work area and has nowhere to record `SET RELATION`, so a generated
   frontend cannot know its own lock domain -- which R26 makes a correctness
   requirement, not a convenience.
6. **The property language names four keys and passes through 648** (R25.5).
   Measured over the corpus: 649 distinct `PROPS` keys, of which the DSL had named
   one. `Mask`, `Columns` and the menu keys are now named. `fontname`/`fontsize`
   are carried twice -- once raw, once resolved into `FONTREF` -- and
   `fontbold`/`fontitalic` are in neither, so the `FONT` row is the incomplete
   copy.
7. **Section 12's permission to refuse `FLOW = free`** and **section 4's
   refuse-the-whole-document rule** remain the two defects this contract records
   against itself. Unchanged and still owner decisions.
8. **Gate 11 was run for real on 2026-08-19** (R28) by an implementer holding only
   this document, a DBF reader and five tables. Four of five rendered and one was
   correctly refused. It logged **4 contradictions, 19 gaps and 7 ambiguities**;
   this document has since absorbed the five with measured consequences, and the
   rest are in `docs/maintenance/evidence/AIF120_gate11_FINDINGS.md`, untriaged.
   Its verdict stands as the honest summary: *this contract answers "how is a UIDEF
   document structured?" completely and "what is in one?" barely.*
9. **`SOURCE` cannot express a relation** (R26.2), and R26 makes that a correctness
   requirement rather than a convenience: the lock domain is the relation set, so a
   frontend that cannot see the relations cannot know what to serialize.
10. **Composition and inheritance are settled; the contract does not describe
    them.** R30 materialises a composite control's members as ordinary rows and R31
    flattens a class instance, both without a schema change -- but sections 2 and 4
    say nothing about either, and a second implementer would not deduce them.
11. **Captions are literals** (R33.4). x64base ships `SET LOCALE` and 4,756 texts
    in five locales; this document's `Caption` carries prose in one language and one
    codepage. Proposed, not adopted.
12. **`FLOW = row` is defined as "left to right"**, a hard-coded direction that is
    wrong in an RTL locale. Untouched.
13. **`ORIGIN_SCALE` gives no conversions** (R35.4, gate 11 G-6). Section 8b states
    the problem and does not solve it: the only consumer that has needed one chose
    its own divisor and declared it.
14. **The refusal set belongs to the target, not the format** (R34.2), which is a
    result rather than an open item -- but it means conformance cannot be stated as
    a single list. `tools/uidef/manifest.py` carries three real target profiles and
    a hypothetical one, and its five outcomes -- `REFUSE`, `DEGRADE`, `DERIVE`,
    `REQUIRE`, `NOTE` -- are richer than section 12's vocabulary.
15. **Nothing takes a lock.** R36 lets a document state its lock domain and R26
    proves what happens without one, but no generated frontend serializes anything.
    The same gap holds for `DISPATCH = worker`: all three backends are Python, and
    only Tk implements dispatch at all.

## 15. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git --no-optional-locks status --short -uall
git commit -m "AIF-120: gate 10 draft -- the UIDEF design table as a standalone contract (forms and menus)"
```
