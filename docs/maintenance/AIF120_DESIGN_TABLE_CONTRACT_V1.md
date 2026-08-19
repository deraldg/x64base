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
| `SPAN` | N(5,0) | O | cells spanned in a `grid` flow. Default 1 |
| `KIND` | C(20) | P+C | the portable class name -- section 4 |
| `FLOW` | C(8) | P on containers | `row`, `column`, `grid`, `free`. Section 5 |
| `BINDING` | C(64) | O | data field this control reads and writes |
| `FONTREF` | N(3,0) | O | 1-based index into this document's `FONT` rows. 0 = target default |
| `PROVENANCE` | C(10) | P | `authored` or `imported` |
| `PROPS` | M | O | property text -- section 7 |
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

**An absent dimension is never defaulted to a number.** A control that does not
state a size gets one from its content and its font -- from the `FONT` rows if
`FONTREF` is set, from the target's own font otherwise. A reader that derives a
dimension **must record that it derived it** and must never write the derived
value back into `ORIGIN`. (R12.3. Writing it back launders a guess into a
measurement.)

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

- **a generator may ignore `ORIGIN` entirely and remain conformant**
- a generator that honours it **must** honour `ORIGIN_SCALE` or refuse the row
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

`DISPATCH` is `ui` or `worker` (R11):

- **`ui`** -- runs on the platform's UI-owning thread, must not block
- **`worker`** -- runs off it, must not touch any UI object, and **must** name a
  completion handler which runs under `ui`

The default is `ui`, chosen so failures are loud: a handler wrongly on the UI
thread freezes and is found in the first minute; wrongly off it corrupts widget
state intermittently and is found on someone else's platform.

**Event names in v1** -- ten, covering 65% of 1,583 measured implementations:
`Click`, `Init`, `Change`, `Activate`, `Deactivate`, `Destroy`, `Error`,
`Focus`, `Blur`, `Load`. An unknown event name is dropped with a diagnostic.

**Completion order is not guaranteed.** A completion handler receives a task
identity and a terminal state and must tolerate arriving out of order.

**Lifetime:** destroying a container cancels the pending work its handlers
submitted. Nothing queued may outlive the object that queued it.

## 10. `SOURCE` -- relative to this document, always

```text
Alias = customers
Table = ..\data\customers.dbf
Order = cust_id
```

`Table` is **relative to the UIDEF document's own location**, never absolute and
never a bare name resolved against ambient state.

This was measured rather than designed. VFP was observed rewriting a data-source
path to `..\..\..\dottalkpp\data\dbf\vfp\students.dbf` when the form lived three
directories away, and to the bare `students.dbf` when the same form was saved
beside its table -- recomputed relative to the document on every save. The bare
filename is the zero-distance case, not a fallback. The same convention appears
independently in `.FRX` (`Database = ..\..\data\testdata.dbc`) and in `.SCX`
class-library references.

## 11. Menus

Menu rows are `OBJ` with `KIND = menu`, nested by `PARENT`, ordered by `ORDINAL`.

**A menu row must not carry `ORIGIN`.** Measured: four `.MNX` files, 205 records,
25 columns, **zero geometry columns of any kind**. Menus have never had position;
a v1 that adds one for symmetry makes the menu half unportable for no gain.

Menu-specific properties live in `PROPS`: `Caption`, `Key`, `Message`, `Checked`,
`Enabled`, `Separator`. The `\<` mnemonic escape and `\-` separator convention are
inherited from the source vocabulary, which uses them consistently in both
captions and prompts (R8).

## 12. Conformance

**A conformant READER** locates records by `RECKIND`; understands every **C**
field; tolerates absent **O** fields; drops unknown properties silently and
unknown `KIND` loudly; honours `ORIGIN_SCALE` if it honours `ORIGIN` at all;
records any dimension it derived.

**A conformant WRITER** emits every **P** field; emits `ORIGIN_SCALE` whenever it
emits any `ORIGIN_*`; never writes a derived dimension into `ORIGIN`; sets
`PROVENANCE`; writes `SOURCE.Table` relative to the document.

**A conformant GENERATOR** may ignore `ORIGIN` wholly, may refuse `FLOW = free`,
must refuse unknown `KIND`, and must implement `DISPATCH`.

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

## 14. Open against this contract

1. **Not implemented.** No writer, no reader, no round-trip. This is a
   specification, tier `planned`.
2. **`FLOW` has never been exercised.** Every layout ruling behind it is measured
   from formats that use absolute geometry. The first import of a real `.SCX`
   into `FLOW`/`ORDINAL` is the test that could break section 5.
3. **The fourteen `KIND` values are a judgement**, checked against measured
   vocabulary but not against a second backend.
4. **Gate 11 is the acceptance test for this document** -- a frontend generated
   from this table alone, by someone holding nothing else.

## 15. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: gate 10 draft -- the UIDEF design table as a standalone contract (forms and menus)"
```
