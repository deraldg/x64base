# DEV-22 The UIDEF GUI Language

```yaml
page_id: DEV-22
title: The UIDEF GUI Language
status: DRAFT
last_verified: 2026-08-20
evidence_classes: [SOURCE, MEASURED]
lane: AIF-120
```

The complete portable UI description language: every field, every vocabulary,
every rule that can refuse a document, what each of the four backends does with
it, and the DotTalk and DotScript that pair with it.

**This chapter was written from the implementation, not from the specification.**
Where the two disagree, section 17 names the disagreement rather than resolving
it silently. Every vocabulary below was read out of `gui/uidef/manifest.py` and
the four backend modules on 2026-08-20; every rule in section 13 is a branch that
exists in that file today.

## 1. What a UIDEF document is

**A DBF table with a memo sidecar.** Rows are objects. One document -- one form,
one menu -- is one table.

That is the whole transport. A consumer needs this document and a DBF reader. It
does not need a parser, a grammar, or any of this project's source. The design
follows FoxPro's 1994 answer for the same reason: a project whose engine is a DBF
engine gets `USE`, `BROWSE`, indexes and diff tooling for free the moment its UI
description is a table.

**There is no DSL text.** The "language" in this chapter's title is a schema and a
closed set of vocabularies, not a syntax. Nothing parses. That is deliberate: a
generator needs a schema, not a grammar, and four independent backends were built
from this table without one.

## 2. Record kinds

Every row is one of three kinds, given by `RECKIND`.

| `RECKIND` | meaning | cardinality |
| --- | --- | --- |
| `DOC` | document header -- version, defaults, data source | exactly 1 |
| `FONT` | one font metric row | 0 or more |
| `OBJ` | a container, control, menu item or frame | 1 or more |

`DOC` first and `FONT` before any `OBJ` are **required on output** and **must not
be assumed on input**. A conformant reader locates records by `RECKIND`, never by
position.

The three kinds carry **three different property vocabularies** -- see section 7.
Treating them as one vocabulary is a measured error, not a hypothetical one: a
flat scan reported 128 dead properties and was wrong twice.

## 3. Field reference

Sixteen fields. Column order is not significant; a reader locates fields by name.
Record length is not fixed.

| field | type | R | meaning |
| --- | --- | --- | --- |
| `RECKIND` | C(4) | P+C | `DOC`, `FONT`, `OBJ` |
| `OBJID` | C(12) | P+C | identity, unique within the document. Opaque -- never parsed |
| `PARENT` | C(12) | P | `OBJID` of the container. Empty on `DOC`, `FONT` and the root |
| `ORDINAL` | N(5,0) | P | position among siblings, ascending, gaps allowed |
| `TABORDINAL` | N(5,0) | O | focus order among siblings, independent of `ORDINAL`. `0`/absent means the target derives it and must say so |
| `SPAN` | N(5,0) | O | cells spanned in a `grid` flow. Default 1 |
| `KIND` | C(20) | P+C | the portable class name -- section 5 |
| `FLOW` | C(8) | P on containers | `row`, `column`, `grid`, `free` -- section 6 |
| `BINDING` | C(64) | O | what this object reads -- section 11 |
| `FONTREF` | N(3,0) | O | 1-based index into this document's `FONT` rows. 0 = target default |
| `PROVENANCE` | C(10) | P | `authored`, `imported`, `inherited` |
| `PROPS` | M | O | property text -- section 7 |
| `ORIGIN` | M | O | quarantined absolute geometry -- section 8 |
| `HANDLERS` | M | O | handler references, never bodies -- section 9 |
| `SOURCE` | M | O | data source, relative to this document -- section 10 |
| `NOTES` | M | O | free text. Never interpreted |

## 4. Requiredness has three values

`R` above is not a boolean. Requiredness is not symmetric, and a schema with two
categories cannot express the common case.

| mark | meaning |
| --- | --- |
| `P` | required to PRODUCE. A writer must emit it |
| `C` | required to CONSUME. A reader must understand it; a document lacking it is invalid |
| `O` | optional to produce and safely omitted. A reader must tolerate absence |

The case that forces this: VFP's `.SCX` requires `CLASS` on output -- omit it and
VFP 9 refuses the file -- while an importer may correctly ignore it and key on
`BASECLASS`. Optional to consume, mandatory to produce. A generator built from a
two-category schema emits files the reference implementation rejects.

## 5. `KIND` -- the class vocabulary

**Twenty kinds.** Fourteen were selected as the intersection of what every
platform in the charter's target list provides, cross-checked against 3,010
measured object records; five data-frame kinds were added from the browse this
house already ships; `splitter` was added by R85.

A reader that meets an unknown `KIND` **must refuse the document and name the
kind**. It must not render a placeholder -- a placeholder produces a document that
looks correct and is not.

| group | kind | wx | Tk | HTML | cell |
| --- | --- | --- | --- | --- | --- |
| container | `form` | yes | yes | yes | yes |
| container | `panel` | yes | yes | yes | yes |
| container | `group` | yes | yes | yes | yes |
| container | `pageset` | yes | yes | yes | yes |
| container | `page` | yes | yes | yes | yes |
| container | `splitter` | yes | yes | yes | yes |
| control | `label` | yes | yes | yes | yes |
| control | `text` | yes | yes | yes | yes |
| control | `button` | yes | yes | yes | yes |
| control | `check` | yes | yes | yes | yes |
| control | `radio` | yes | yes | yes | yes |
| control | `list` | yes | yes | yes | yes |
| control | `combo` | yes | yes | yes | yes |
| control | `image` | **no** | yes | yes | **no** |
| menu | `menu` | **no** | **no** | **no** | **no** |
| frame | `grid` | yes | yes | yes | yes |
| frame | `tree` | yes | yes | yes | yes |
| frame | `detail` | yes | yes | yes | yes |
| frame | `summary` | yes | yes | yes | yes |
| frame | `statusbar` | yes | yes | yes | yes |

**`menu` is rendered by nothing.** It is in the vocabulary, it is imported from
`.MNX`, and no backend draws it. That is the lane's oldest declared-and-unproven
item and it is stated here rather than left to be discovered by rendering a menu
and getting a refusal.

**`image` is rendered by two of four.** wx and the character cell refuse it.

### 5b. The three groups differ in what `BINDING` means

- a **control** binds one FIELD (`alias.field`)
- a **spec frame** -- `grid`, `detail` -- binds a ROW (a tuple spec)
- a **root frame** -- `tree`, `summary` -- binds a bare ALIAS: the root
- `statusbar` binds **nothing**; `BINDING` must be empty

That three-way split is why one `alias.field` rule could not cover the frames.

### 5c. Kinds deliberately absent from v1

`pageframe` children generated by count properties (implicit children are
unsolved); `olecontrol` and `oleboundcontrol` (no portable rendering); `timer` and
`custom` (non-visual); anything report-shaped (out of scope).

## 6. `FLOW` -- geometry is INTENT

A container declares a `FLOW`; its children declare `ORDINAL` and optionally
`SPAN`. That is all a conformant generator needs.

| `FLOW` | meaning |
| --- | --- |
| `row` | children left to right in `ORDINAL` order |
| `column` | children top to bottom in `ORDINAL` order |
| `grid` | children in reading order, wrapping; `SPAN` gives cells consumed |
| `free` | children positioned only by `ORIGIN`. A generator may refuse `free` |

All four backends support all four flows.

Ordinal containment is portable because it is the one primitive every candidate
has: Turbo Vision nests rects, wx nests sizers, Qt nests layouts, Tk packs and
grids, a browser flows boxes. Tested: one document carrying **zero coordinates**
rendered by Tk, a browser and a character grid returns the identical verdict from
the table alone -- two derivations and one refusal, same rows, same reasons.

**An absent dimension is never defaulted to a number, and for many controls a
present one is ignored too.** A control that does not state a size gets one from
its content and its font. A reader that derives a dimension **must record that it
derived it** and must never write the derived value back into `ORIGIN`; writing it
back launders a guess into a measurement.

On a `splitter`, `FLOW` is not layout -- it is the axis of the boundary. `row` is
a vertical sash, `column` a horizontal one. There is no third answer and no
default worth guessing, so a splitter with any other `FLOW` is refused.

## 7. `PROPS` -- three closed vocabularies, one per `RECKIND`

`PROPS` is `name = value` lines, adopted from the FoxPro designer formats rather
than invented. The **key vocabulary is closed and keyed by `RECKIND`**.

| `RECKIND` | keys |
| --- | --- |
| `DOC` | `sourcefile`, `contract`, `version`, `title`, `origin`, `kind` |
| `FONT` | `name`, `size`, `metrics`, `bold`, `italic` |
| `OBJ` | `caption`, `columns`, `columnwidths`, `fill`, `filter`, `mask`, `minpane`, `order`, `readonly`, `rowlimit`, `shows`, `weight` |

Keys are matched case-insensitively and stored lowercase.

**A row whose `PROVENANCE` is `imported` is exempt.** An imported row carries what
the source record carried -- 116 distinct keys across the VFP imports, 404
occurrences. That is preservation, and it is the importer working, not a document
making claims a target ignores.

**An unknown key on an authored row is NOTED, not refused.** The asymmetry with
`KIND` has a reason: an unknown kind cannot be drawn at all, while an unknown
property loses a modifier on an object that still renders. Silently ignored
becomes named.

`multiline` is deliberately absent from the `OBJ` list. It is stated by a real
document and no target reads it, so the checker names it on every run. It goes in
when all four backends can each say what they do with it.

### 7b. Object property semantics

| key | applies to | value | meaning |
| --- | --- | --- | --- |
| `caption` | most | text | the visible label |
| `columns` | container with `FLOW=grid` | integer | cells per row. Required -- a grid flow with no `Columns` is refused |
| `columnwidths` | `grid` | comma list | ordinal-aligned with the spec's columns; a length mismatch is refused |
| `fill` | any child of a flowed container | boolean | does the child stretch ACROSS the flow axis |
| `weight` | any child of a flowed container | non-negative integer | share of the flow axis. `0` means fixed |
| `filter` | frames | expression | passed through |
| `mask` | bound data controls | picture | determines width; see section 8 |
| `minpane` | `splitter` | whole pixels | minimum pane size |
| `order` | `grid` | `physical`, `ordered` | the stream's nav mode -- see below |
| `readonly` | `grid`, `detail` | boolean | must not be false |
| `rowlimit` | `grid` | 1..200 | `next_page(max_rows)` |
| `shows` | `statusbar` | subset of `rows limit order root recno status` | what the frame reports |

**`Order` is a MODE, not an index format.** It was three values until the engine
was measured: `set_order_inx()` and `set_order_cnx()` are byte-identical, both
setting the same nav mode and neither attaching an index or selecting a tag. The
engine picks the format from the table itself -- x64 chooses CDX, classic chooses
CNX. A document naming `inx` or `cnx` purports to choose something the engine
derived from the file. There are two modes. `inx` and `cnx` are still accepted,
mapped to `ordered`, and **reported** -- a vocabulary change must not invalidate
documents that were correct when written, and it must not silently equate them
either.

### 7c. The `FONT` row

A `FONT` row carries `name`, `size`, `metrics`, `bold`, `italic`. Objects select
one by 1-based `FONTREF`. `FONTREF` out of range is refused; a `FONT` row nobody
references is noted, not refused -- it is carried as source metrics.

## 8. `ORIGIN` -- quarantined, advisory, carrying its own unit

```text
ORIGIN_TOP = 24
ORIGIN_LEFT = 10
ORIGIN_WIDTH = 200
ORIGIN_SCALE = px
```

Absolute coordinates are permitted and advisory. Position is never portable;
`FLOW` and `ORDINAL` are.

**Neither "always honour it" nor "always ignore it" is correct**, and both were
measured wrong. Honouring every width truncates every label on a toolkit whose
font differs from the authoring font. Ignoring every width discards field sizing
the document knows and the target cannot infer. The rule that replaces them, for
SIZE only:

| control | width comes from |
| --- | --- |
| content-sized (`label`, `button`, `check`, `radio`, `group`, `page`) | its own content in the target's font |
| data-sized and **bound** | its `Mask`, which the schema determines |
| data-sized and **unbound** | `ORIGIN_WIDTH` with its `ORIGIN_SCALE` |
| a container whose children carry `ORIGIN` | its own stated width and height -- nothing else can supply them, because absolutely positioned children report no size |

**Units are an open hole.** `ORIGIN_SCALE` enumerates units and gives conversions
between none of them. Measured: 20 objects in the corpus declare a scale and all
20 say pixels; `cell` has been specified and produced by nothing. The character
cell backend is the first consumer that needs pixels in cells, and it declares the
conversion as derived on every render rather than pretending the format supplied
one.

**A coarse target bands before it quantises.** Converting each `ORIGIN_TOP`
independently splits a visual row in two, because a label sits a few pixels off
its own field's baseline. Nineteen `ORIGIN_TOP` values on one real form band into
ten visual rows within 8 px; without banding, a label and its field land on
different lines.

## 9. `HANDLERS` -- references, never bodies

```text
Click = SaveCustomer / ui
Init = LoadDefaults / ui
Export = BuildReport / worker -> ExportDone
```

Each line is `Event = HandlerName / DISPATCH [-> CompletionHandler]`.

Measured across 2,404 real procedures, **86% navigate the target's object model**.
The charter forbids exposing that model to the script, so method bodies do not
enter v1. A handler is a name the host resolves.

### 9b. The three dispatch values

| dispatch | thread | rules |
| --- | --- | --- |
| `ui` | the platform's UI-owning thread | must not block. The default |
| `worker` | off the UI thread | must not touch any UI object, and **must** name a completion handler which runs under `ui`. The completion is delivered at most once; destroying the container drops it |
| `host` | none -- names a capability the HOST provides | no thread rule, no completion path, no registry entry. A target that does not provide the named capability refuses the item and names it |

`ui` is the default because its failure is loud: a handler wrongly on the UI
thread freezes and is found in the first minute, while one wrongly off it corrupts
widget state intermittently and is found on someone else's platform.

**Completion order is not guaranteed.** A completion handler receives a task
identity and a terminal state and must tolerate arriving out of order.

**Lifetime:** destroying a container cancels the pending work its handlers
submitted. Nothing queued may outlive the object that queued it.

### 9c. Event names -- nineteen

`Click`, `Init`, `Change`, `Activate`, `Deactivate`, `Destroy`, `Error`, `Focus`,
`Blur`, `Load`, `Unload`, `MouseMove`, `MouseDown`, `MouseUp`, `DoubleClick`,
`DragOver`, `DragDrop`, `KeyPress`, `Validate`.

The last nine were added after measuring 92 handlers being silently discarded
because the list was shorter than the format. `Unload` is 72 of the 92: the list
carried `Load` and dropped the teardown event that pairs with it.

A handler name defined on an object's CLASS reaches the instance; an event the
instance defines itself wins. A method whose name is not an event is a custom
method, and v1 has no concept for one -- the importer names them rather than
mapping them onto an event the source never declared. An unknown event name is
dropped **with a diagnostic**.

### 9d. Host capabilities, by backend

| capability | wx | Tk | HTML | cell |
| --- | --- | --- | --- | --- |
| `edit.cut` | yes | yes | yes | -- |
| `edit.copy` | yes | yes | yes | -- |
| `edit.paste` | yes | yes | yes | -- |
| `edit.undo` | yes | yes | yes | -- |
| `edit.redo` | yes | yes | yes | -- |
| `edit.select_all` | yes | yes | yes | -- |
| `edit.clear` | **no** | yes | yes | -- |
| `edit.find` | **no** | **no** | yes | -- |

The character cell backend provides none and supports only `ui` dispatch -- no
threads, no host clipboard.

## 10. `SOURCE` -- relative to this document, always

```text
Alias = customers
Table = ..\data\customers.dbf
Order = cust_id
Relation = customer -> orders ON cust_id
```

A `Relation` line states that navigating the parent work area repositions the
child. The **lock domain** is the transitive closure of these edges, and a
mutating handler must serialize against the whole domain, not the area it names --
measured at 100 failures in 100 trials when it does not.

`Table` is resolved relative to this document. **Never a bare name resolved
against ambient state.**

**A conforming frontend opens every `Alias` declared in `SOURCE` into its own work
area, resolving `Table` per this section, before it fires any handler.** A `Table`
that does not resolve is refused there -- not at first use, when a handler is
already mid-flight. This was found by a harness that opened two tables into one
work area, silently replacing the first, then released a lock it did not hold
while the lock it did hold stayed held.

## 11. `BINDING`

### 11a. On a control: `alias.field`

Measured over the 170-form corpus, 159 `ControlSource` occurrences:

| shape | count | share | ruling |
| --- | --- | --- | --- |
| `alias.field` | 145 | 91.2% | **the form.** `alias` MUST name an `Alias` declared in `SOURCE` |
| empty | 8 | 5.0% | legal; the control is unbound |
| object reference, e.g. `This.Parent.SysTray1.Tiptext` | 4 | 2.5% | **refused** |
| bare `field` | 2 | 1.3% | **refused** |

Alias resolution is case-insensitive. VFP writes the value quoted in the designer
record; `BINDING` holds it unquoted -- the quotes are the container's, not the
value's.

**A bare field name is refused, not resolved.** It means "the field of whatever
work area is current", and ambient resolution is already refused for `Table`. One
rule, applied twice.

**An object reference is refused for a different reason, and the reason matters.**
It binds a control's property to another control's property -- not a malformed
`alias.field` but a kind of thing UIDEF does not model at all. A reader that
reports it as "not alias.field" tells the author they made a typo when what they
actually did was use a feature that is absent.

### 11b. On a spec frame: a tuple spec

`grid` and `detail` bind a ROW, so they take the engine's own spec grammar --
which `alias.field` turns out to be a strict subset of.

| spec | v1 | note |
| --- | --- | --- |
| `alias.field` | accepted | 11a's form, unchanged; the unit a spec list is built from |
| `alias.field,alias.field,...` | accepted on `grid` and `detail` only | the columns, declared |
| `alias.*` | accepted on `grid` and `detail` only | every field of a NAMED area |
| `*` | accepted on `grid` and `detail` only | every field of the FIRST alias in `SOURCE` |
| `#n` | **refused** | unreachable through the shell |
| bare `field` | **refused** | 11a's rule |
| object reference | **refused** | 11a's rule |

Every alias in a spec list must be declared in `SOURCE`, and a spec may name more
than one -- `students.lname,enroll.grade` is a legal `grid` binding and is the case
the whole thing exists for. **A spec naming two aliases requires a `Relation` edge
between them**, because the row it describes is a join and the lock domain must
already cover both.

**`*` resolves against the FIRST alias declared in `SOURCE`, not the current work
area.** The engine's `*` means the current area, which is ambient state. Same rule
as `Table` and as a bare field, applied a third time. A reader that cannot
determine a first alias refuses the document.

**`#n` is refused, and not because it is a bad idea.** `TUPLE #1` never reaches
the engine's spec parser: the canonical comment vocabulary cuts `#` and everything
after it to end of line, on both the prompt path and the script path, so the
command degrades to a bare `TUPLE` and prints every field with no header. The
engine's own frozen spec declares a form its lexer deletes. A reader must say
*"ordinal spec `#n` is unreachable through the shell; name the field"*, not *"bad
binding"*.

### 11c. On a root frame: a bare alias

`tree` and `summary` bind the root of the relation closure, as a bare alias name.

### 11d. On `statusbar`: nothing

`BINDING` must be empty. A statusbar renders the frame's own status line; `Shows`
filters what it reports rather than naming values the reader computes.

## 12. The report vocabulary

Five verbs. **Silence is the defect** -- a target that cannot honour something the
document says must say so, by name, every run.

| verb | meaning | stops the render |
| --- | --- | --- |
| `REFUSE` | the target cannot render this document | **yes** |
| `DEGRADE` | rendered, but something the document said was lost | no |
| `DERIVE` | the target supplied a value the document did not state | no |
| `REQUIRE` | the target must supply something before this document runs | no |
| `NOTE` | legal, and worth saying out loud | no |

The report prints in that order, with a per-severity count.

## 13. Every rule that fires

The complete rule set as implemented. `s4`, `s5`, `4b`, `4c`, `5c` are contract
sections; `R11.3`, `R23.2`, `R85.1` and so on are the rulings that added them.

### 13a. Capability rules -- document against target profile

| verb | fires when | reference |
| --- | --- | --- |
| `REFUSE` | a `KIND` the target does not render | s4 |
| `REFUSE` | a `FLOW` the target does not implement | s5 |
| `REFUSE` | a `DISPATCH` value the target does not implement | R11, R20 |
| `REFUSE` | a host capability the target does not provide | R20, R22.4 |
| `REFUSE` | `SPAN` present and the target does not implement it | s5 |
| `DEGRADE` | `ORIGIN` present and the target ignores it -- layout falls back to `ORDINAL` | R16 |

### 13b. Structural rules

| verb | fires when | reference |
| --- | --- | --- |
| `REFUSE` | `FLOW=grid` with no `Columns` property | R23.2 |
| `REFUSE` | `DISPATCH=worker` with no `ON_COMPLETE` | R11.3 |
| `REFUSE` | `FONTREF` is not a 1-based index into this document's `FONT` rows | -- |
| `REFUSE` | a frame kind has child rows -- a second copy of the closure | 4b(a) |
| `NOTE` | a `FONT` row nothing references | -- |
| `DERIVE` | `FLOW=free` with no `ORIGIN` on any child | R12.3, R23.3 |
| `DERIVE` | no control states `TABORDINAL` -- a derived order matches the document exactly in 25.7% of groups | R27 |
| `DERIVE` | SOME controls state `TABORDINAL` -- the worst case: gaps must be derived and interleaved with declared stops | R27 |
| `REQUIRE` | any bound control -- the target must supply a data source | R17 |

### 13c. Layout property rules

| verb | fires when | reference |
| --- | --- | --- |
| `REFUSE` | `Weight` is not a non-negative integer | 5c |
| `REFUSE` | `Fill` is not a boolean | 5c |

`Weight` and `Fill` are checked on EVERY object, not just frames -- any child of a
flowed container may carry them. Absent means 0 and false, which is what every
document said before they existed, so silence is never a finding.

### 13d. Data frame rules

| verb | fires when | reference |
| --- | --- | --- |
| `REFUSE` | `ReadOnly` is false on `grid` or `detail` | 4b(b) |
| `REFUSE` | `Order` is not `physical` or `ordered` | 4c |
| `DEGRADE` | `Order` is `inx` or `cnx` -- read as `ordered`, format is the engine's choice | R73 |
| `REFUSE` | `RowLimit` is not a positive integer | 4c |
| `DEGRADE` | `RowLimit` exceeds 200 -- the house browser clamps, and a reader that clamps must say so | 4c |
| `REFUSE` | `ColumnWidths` entry count differs from the spec's column count | 4c |
| `REFUSE` | `statusbar` `Shows` names something outside `rows limit order root recno status` | 4b(c) |
| `NOTE` | `statusbar` with no `Shows` -- the reader decides what to report | 4b(c) |

### 13e. Splitter rules

| verb | fires when | reference |
| --- | --- | --- |
| `REFUSE` | pane count is not exactly 2 -- a document that means three panes means two splitters | R85 |
| `REFUSE` | `FLOW` is not `row` or `column` | R85 |
| `REFUSE` | `MinPane` is not a whole number, or is negative | R85 |
| `REFUSE` | the splitter states `ORIGIN` but carries no `Weight` and no `Fill`, and its parent is not itself a splitter | R85.1 |
| `NOTE` | neither pane declares `Weight` -- sash gravity is 0.0, the first pane holds its size | R85 |
| `NOTE` | no `MinPane` -- a pane can be dragged to nothing and its control becomes unreachable | R85 |
| `NOTE` | no `Weight` and no `ORIGIN` -- laid out at best size rather than filling its parent | R85.1 |
| `DERIVE` | no `ORIGIN` -- the initial boundary is the target's, and wx centres it | R85 |

**R85.1 is the sharpest rule in the language and it was measured, not reasoned.**
The same document was rendered twice, changing one emitted argument:

```text
Add(splitter, 0, wxALL, 6)              sash lands at 119
Add(splitter, 1, wxALL|wxEXPAND, 6)     sash lands at 220
```

The document said `ORIGIN_WIDTH = 220` both times. Unweighted, the splitter gets
its best size and the toolkit clamps a 220 sash against a 120 `MinPane` down to an
even split -- silently. The screen then contradicts the document and nothing says
so. This is refused rather than noted because the author cannot know the best size:
it depends on the pane contents, the font and the platform. An `ORIGIN` under an
unweighted splitter is not wrong, it is **unpredictable**, and a coordinate that
might mean itself is worse than one that does not.

A splitter nested inside a splitter is exempt: a pane of another splitter already
fills, so there is nothing to state and nothing to lose.

### 13f. Binding rules -- against a schema

| verb | fires when |
| --- | --- |
| `REFUSE` | an `Alias` in `SOURCE` names a table that does not resolve |
| `REFUSE` | `BINDING` is a bare field -- ambient state |
| `REFUSE` | `BINDING` is an object reference -- a feature v1 does not model |
| `REFUSE` | `BINDING` names an alias not declared in `SOURCE` |
| `REFUSE` | `BINDING` names a field the schema does not have |
| `REFUSE` | a spec list on a kind that is not `grid` or `detail` |
| `REFUSE` | `*` with no determinable first alias |
| `REFUSE` | `#n` ordinal spec |
| `REFUSE` | a multi-alias spec with no `Relation` edge between the aliases |
| `REFUSE` | `BINDING` on `statusbar` |
| `NOTE` | a width check across the bound controls |

### 13g. Lock domain rules

| verb | fires when | reference |
| --- | --- | --- |
| `REQUIRE` | two or more work areas share a lock domain -- a mutating handler must serialize against the whole set | R26 |
| `NOTE` | several work areas and no `Relation` declared -- each is its own domain, or the document did not say | R26.2 |

### 13h. Vocabulary rules

| verb | fires when | reference |
| --- | --- | --- |
| `NOTE` | a `PROPS` key outside the `RECKIND`'s vocabulary, on a non-`imported` row | R86 |

## 14. What each backend loses, out loud

The same document renders through wxWidgets, Tk, HTML and a character grid. That
is the portability claim, and it is only worth something if the failures are
audible.

| target | module | what it loses, by name |
| --- | --- | --- |
| wxWidgets | `gui/uidef/uidef_wx.py` | `image`, `menu` |
| Tk | `gui/uidef/uidef_tk.py` | `menu`; `MinPane` on a splitter -- ttk's paned window has no per-pane minimum; `edit.find` |
| HTML | `gui/uidef/uidef_html.py` | `menu`; the splitter's drag TARGET -- CSS `resize` is a corner grip, not a sash |
| character cell | `gui/uidef/uidef_text.py` | `image`, `menu`; dragging; all host capabilities; `worker` and `host` dispatch. Reports the pixel-to-cell division it performed |

Two of those are worth reading together. **Tk keeps sash gravity and has no
minimum pane; a browser keeps the minimum pane and has no gravity at all.**
Neither toolkit carries both facts. The document carries both -- which is the
strongest evidence available that this is not a transcription of any one toolkit.

## 15. Usage

### 15a. Check a document against every backend

```text
python manifest.py <document.dbf> --all
```

Profile selection, from `gui/uidef/manifest.py`:

| flag | profile |
| --- | --- |
| *(none)* | Tk -- requires tkinter |
| `--minimal` | a deliberately small target: labels, fields, buttons, stacked, synchronous. Nothing implements it; it is a profile, not a claim |
| `--html` | the browser backend |
| `--text` | the character cell backend |
| `--both` | Tk and HTML |
| `--all` | minimal, HTML and text |
| `--workspace <file.dtschema>` | resolve `Table` through a workspace as the engine would |
| `--schema <a.dbf,b.dbf>` | check every `BINDING` against real table schemas, and report widths |

### 15b. What a run prints

```text
<document> -- <n> objects
  kinds     : form x1, grid x1, splitter x1, ...
  flows     : column x2, row x1
  dispatch  : ui x4
  host caps : 2 -- edit.copy, edit.cut
  vs <profile name>
      REFUSE   kind image (x2)                  target does not render this kind -- contract s4
      DEGRADE  grid G1 Order=cnx                R73: `cnx` names an index FORMAT ...
      DERIVE   splitter WORK                    no ORIGIN, so the initial boundary is the target's ...
      REQUIRE  6 bound control(s)               target must supply a data source ...
      NOTE     splitter WORK                    no MinPane; a pane can be dragged to nothing ...
      -> DEGRADE 1, DERIVE 1, NOTE 1, REFUSE 1, REQUIRE 1
  vs contract s10 -- does every declared Table resolve?
      ...
```

The severity block is printed in fixed order -- `REFUSE`, `DEGRADE`, `DERIVE`,
`REQUIRE`, `NOTE` -- so a diff of two runs is stable.

### 15c. Launch the windowed frontend from the shell

```text
APPGUI
GUI
APPGUI USAGE
```

`GUI` is an alias of `APPGUI`. The command is authorized by the identity
permission `app.gui`, resource class `app` -- not `host` -- so it does not require
enabling arbitrary shell execution. The owner is exempt; any other member needs
the permission through a role or a grant, and a refusal names the acting member
and the stage that denied it. When the executable is absent, the command names
the build flag and lists every path it probed, each tagged with where that path
came from.

## 16. DotScript and DotTalk samples

**DotScript is not a second language.** It is a line iterator over the same
command executor the interactive prompt uses, against a single command registry.
Every DotTalk command is therefore a DotScript statement, and anything registered
once is reachable from the prompt, from every `.dts`, and from the engine's other
front ends. A `*` in column one is a comment line.

This matters to UIDEF directly: **a document's `SOURCE` section and its `BINDING`
specs are executable**. The same alias set, the same relation edge and the same
tuple spec that a document declares can be typed at the prompt, and that is how
the language is verified rather than asserted.

### 16a. A document's `SOURCE`, executed

A document declaring

```text
Alias = students
Table = dbf\x64\STUDENTS.dbf
Alias = enroll
Table = dbf\x64\ENROLL.dbf
Relation = students -> enroll ON SID
```

is exactly this, at the prompt or in a `.dts`:

```text
SET PATH DBF dbf/x64
SELECT 1
USE STUDENTS
SELECT 2
USE ENROLL
SELECT 1
SET RELATION TO SID INTO ENROLL
```

Note the ordering rule from section 10: every alias is opened into **its own work
area** before any handler fires. Two tables opened into one work area silently
replace each other, which is a measured defect and not a hypothetical one.

### 16b. A `grid` `BINDING`, executed

A grid binding `students.lname,students.fname,enroll.cls_id,enroll.grade` is a
tuple spec, and `TUPLE` takes the same string:

```text
GOTO FIRST
TUPLE students.lname,students.fname,enroll.cls_id,enroll.grade
SKIP
TUPLE students.lname,students.fname,enroll.cls_id,enroll.grade
```

The generated frontend declares its columns from that spec and then fills them
from the same engine call. Running both halves is what proves they agree -- a
generator whose heads and rows disagree compiles perfectly and renders a lie.

`alias.*` and `*` are the other two accepted forms:

```text
TUPLE students.*
TUPLE *
```

### 16c. The refusal cases, as a script

```text
* T1  bare field list   -> the ENGINE resolves it; UIDEF refuses it (ambient state)
* T2  *                 -> all fields of the first alias
* T3  AREA.FIELD        -> resolves, spanning two work areas
* T4  AREA.*            -> all fields of a NAMED area
* T5  #n ordinal        -> DOES NOT RESOLVE: the comment lexer cuts '#' to end of
*                          line before the spec parser sees it, so the line
*                          degrades to a bare TUPLE and prints every field with
*                          no header
```

T1 and T5 are the two places where **the engine and UIDEF deliberately disagree**,
and both disagreements are documented refusals rather than gaps. T1: the engine
resolves a bare field against the current work area, and UIDEF refuses ambient
resolution everywhere. T5: the engine's own frozen spec declares a form its lexer
deletes.

### 16d. A regression script's shape

The house form, from the lane's own scripts:

```text
* <name>.dts
* <what is being measured and why>
*
* Fixture: <tables>, read-only.
* Regression doctrine: every test sets its own environment.

SET ECHO OFF
STOP_ON_ERROR OFF
SET PATH DBF dbf/x64

FORMULA "<CANARY-BEGIN>"

ECHO
ECHO --- A. <the claim> ---
<commands>

FORMULA "<CANARY-END>"
```

`FORMULA` bookends give the transcript a greppable canary; every script sets its
own `SET PATH DBF` rather than inheriting one.

## 17. Where this chapter and the v1 contract disagree

Stated so a miner does not have to reconcile them.

**The v1 contract still says nineteen kinds and does not list `splitter`.** R85
added `splitter` as the twentieth kind, all four backends render it, the checker
enforces eight rules about it, and the public lane page says twenty. The contract
-- which is proof gate 10, the document a consumer is told to read -- was never
updated. **This chapter's count of twenty is the measured one.** The contract
needs a section 4 amendment; that is an open item against AIF-120 and not
something this chapter can fix on its own authority.

**`menu` and `image` support is stated here and nowhere else.** The contract lists
both as v1 kinds without recording that no backend draws a `menu` and only two
draw an `image`.

**`weight_of()` exists in five copies** -- once in each backend and once in the
checker. A property whose meaning lives in five places can mean five things, and
the only reason it does not yet is that all five were written the same afternoon.
Recorded rather than smoothed.

**`ORIGIN_SCALE` still enumerates units without conversions.** Either the format
gives conversions between its units or it enumerates only `px`. An unconvertible
unit is a promise the format cannot keep.
