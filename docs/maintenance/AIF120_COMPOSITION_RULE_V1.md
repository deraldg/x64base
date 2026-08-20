---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-038
  recorded_at_utc: 2026-08-19T12:10:00Z
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
    baseline_commit: b7f292aa6
  authorization:
    requested_by: maintainer (member.derald), in-session, "composition rule" -- R29
      section 5 named it as the thing option 1 would require.
  report:
    path: docs/maintenance/AIF120_COMPOSITION_RULE_V1.md
    kind: ruling
---

# AIF-120 -- R30: the composition rule, and a correction to R29

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

## 0. R29's headline number is wrong, and this corrects it

R29, committed an hour ago, said **775 implied children lost -- 26% of every form
never reaches the design table.** Designing the rule required looking at what the
parents actually are, and they are two different things:

```
Form1        BASECLASS form       CLASS embossedform
                                  CLASSLOC ...\wizards\wizembss.vcx
BUTTONSET1   BASECLASS container  CLASS txtbtns
                                  CLASSLOC ...\wizards\wizbtns.vcx
```

The ten navigation buttons are **not lost by the document.** They are defined in
`wizbtns.vcx`, class `txtbtns`, and the `.SCX` carries only this instance's
overrides to them. The document is complete. **My importer is what loses them,
because it ignores `CLASS` and `CLASSLOC` entirely.**

Measured across 2,751 visual objects in 170 files:

| mechanism | parents | member names | what it is |
| --- | --- | --- | --- |
| **A -- inheritance** | 118 | **646** | subclassed; members live in a `.VCX`, dotted props are overrides |
| **B -- inline composition** | 72 | **272** | not subclassed; members are stored on a composite control |

Also measured: of every dotted prefix in the corpus, **918 name an object with no
record and exactly 1 names an object that does exist.** So the mechanism is
essentially never property-override-on-a-real-child; the distinction that matters
is A versus B, and R29 conflated them.

**Correct statement:** 15.7% of visual objects are subclass instances whose class
this lane has never resolved (A). A further 272 member names are genuinely carried
inline and genuinely dropped (B). R29's "26% never reaches the table" should read
"646 are inherited and unresolved; 272 are dropped." The importer's behaviour is
equally wrong in both cases; the *reason* is different, and only B is a
composition question.

R29's ruling text stands. Its arithmetic is corrected here rather than edited
there.

## 1. Mechanism B -- the composition rule

This is what was asked for. Measured member properties, corpus-wide:

| composite | members | what a member carries |
| --- | --- | --- |
| `optiongroup` | 72 | `caption`, `top`, `left`, `width`, `height`, `name`, fonts |
| `commandgroup` | 7 | `caption`, `top`, `left`, `width`, `height`, `name`, fonts |
| `pageframe` | 59 | `caption`, `name`, `pageorder`, fonts, `backcolor` -- **no geometry** |
| `grid` | 134 | `name`, `controlsource`, `width`, `columnorder`, `sparse` |

> **R30.** A composite control's members materialise as ordinary `OBJ` rows,
> parented to the composite. `KIND` comes from the composite; `ORDINAL` from the
> member's declared order where it has one and its index otherwise; `ORIGIN` from
> the member's own geometry where it declares any, which is already
> parent-relative; everything else goes to `PROPS` under the existing rules.

**No schema change. No new `RECKIND`. No new column.** The table has been able to
express composition since gate 10 -- `PARENT`, `ORDINAL`, `KIND`, `PROPS` and
`ORIGIN` say all of it. The importer simply never did the work. That is the
seventh ruling in a row that costs the schema nothing, and the first where the
reason is that the answer was already there.

Member kinds:

| composite | member `KIND` |
| --- | --- |
| `optiongroup` -> `group` | `radio` |
| `commandgroup` -> `group` | `button` |
| `pageframe` -> `pageset` | `page` |
| `grid` | refused in v1 (R7); the rule holds if `grid` is ever admitted |

`ORDINAL` comes from `pageorder` for pages and `columnorder` for grid columns
where present, and from the member's numeric suffix otherwise -- `option1`,
`option2` is an order the source states in the name.

## 2. R30.1 -- the composite declares its own member count, so check it

Every composite carries a count:

```
Commandgroup1   buttoncount = 2      members: command1, command2
Optiongroup1    buttoncount = 2      members: option1, option2
Pageframe1      pagecount   = 2      members: page1, page2
```

> **R30.1.** `buttoncount`, `pagecount` and `columncount` are verified against the
> number of members materialised, and a mismatch is reported.

Third time this lane has used the same principle -- R13's `RESERVED2`, R22.1's
caption guard, and now this. A declared count that can be checked should be
checked, and composition is exactly where a silent miscount would produce a
plausible control with the wrong number of buttons.

## 3. R30.2 -- geometry is parent-relative, which section 8 already says

`Commandgroup1` sits at `top 228, left 624`. Its member `command1` is at
`top 5, left 5`. Those are coordinates **inside the group**, and section 8's
`ORIGIN` is already parent-relative for every other nested control. So a
materialised member needs no special geometry rule, and R16 and R17 apply to it
unchanged -- a `radio` is content-sized, so its stated width is advisory.

Pages carry no geometry at all, which is correct: a page fills its frame. That is
also what `TABDEMO` assumed when it was authored by hand, so the authored document
and the real format agree without either having been checked against the other.

## 4. Mechanism A -- inheritance, which is a bigger question

The composition rule does not solve A, and A is 646 of the 918.

An object with `CLASS != BASECLASS` is an **instance of a class defined
elsewhere**. To render it a consumer must load that class's members and apply the
instance's overrides. The design table has nowhere to put the reference: there is
no class field, and `PROVENANCE` only says `imported` or `authored`.

**Addressing, and this one is mine again.** Measured `CLASSLOC` across the corpus:
**412 relative paths, 19 bare filenames, 0 absolute.** The corpus is portable. My
own wizard-generated `STUDENTS.SCX` carries

```
c:\program files (x86)\microsoft visual foxpro 9\wizards\wizbtns.vcx
```

an absolute path into a vendor install on a machine that is not yours. 4b already
ruled that addressing is relative to the document and *does* travel; the fixtures
this lane generated are the ones that violate it.

Proposed, and left for the owner because it is a scope question of the same size
as R6:

- `PROPS` gains named keys `Class` and `ClassSource` (R25.5: a load-bearing
  property must be named, not passed through).
- `ClassSource` is relative to the document. An absolute path is refused.
- A consumer that cannot resolve `ClassSource` **refuses the object and names the
  class** -- R20 and R22.4's shape, a third time.
- Whether v1 resolves `.VCX` at all is the owner's call. The lane has measured
  `.VCX` already (`AIF120_VCX_SPECIMEN_V1.md`); it has never read one as a class
  library.

## 5. R30.3 -- a container with placed children is not content-sized

Found by implementing R30, and it is a refinement of R16.

The materialised option-group members rendered and then **vanished**. R16 filters a
stated width when content determines the size, and `group` is content-sized. But a
container whose children are absolutely positioned has **no content-determined
size** -- `place` does not propagate geometry, so the frame collapsed to its label
and clipped both radios.

> **R30.3.** A container whose children carry `ORIGIN` is not content-sized. Its
> stated width and height are authoritative, because nothing else can supply them.

R16 stands for controls. It needed this exception for containers, and only a
container with real children could have shown it -- which is why an hour of
rendering `form1.scx` with an empty option group never surfaced it.

## 6. Implemented, and measured

R30 is implemented in `gui/uidef/import_scx.py`, R30.3 in `uidef_tk.py`.

| | |
| --- | --- |
| composite members materialised, corpus-wide | **138** -- `radio` 72, `page` 59, `button` 7 |
| `OBJ` rows after | **2,324** (was 2,186) |
| **R30.1 declared-count mismatches** | **0 of 170 files** |
| dotted names still unresolved | 637, all mechanism A |

**Zero count mismatches across 170 files.** Every `buttoncount` and `pagecount` in
the corpus agrees with the number of members the rule produced. That is the
strongest single check on the grouping, and it was free -- the format was already
carrying the answer.

The rows for `form1.scx`, which has one of each composite:

```
OBJID  PARENT   KIND     ORD  ORIGIN                          PROPS
M001   O009     button   1    ORIGIN_TOP = 5  ORIGIN_LEFT = 5  caption = "Command1"
M002   O009     button   2    ORIGIN_TOP = 34 ORIGIN_LEFT = 5  caption = "Command2"
O009   O001     group    5    ORIGIN_TOP = 228 ...             buttoncount = 2
M003   O010     radio    1    ORIGIN_TOP = 5  ORIGIN_LEFT = 5  caption = "Option1"
M004   O010     radio    2    ORIGIN_TOP = 24 ORIGIN_LEFT = 5  caption = "Option2"
O010   O001     group    6    ORIGIN_TOP = 24 ...              buttoncount = 2
M005   O015     page     1                                     caption = "Page1"
M006   O015     page     2                                     caption = "Page2"
O015   O001     pageset  11   ORIGIN_TOP = 24 ...              pagecount = 2
```

`docs/maintenance/evidence/AIF120_composite.png` is `form1.scx` rendered: the
pageframe now shows **Page1 and Page2**, and the option group shows **Option1 and
Option2** inside its frame. Two hours ago R24.3 taught the renderer to draw a
`pageset` and it drew an empty notebook. R29.3 predicted why. This closes it.

`grid` members are not materialised because `grid` is a refused `KIND` in v1 (R7);
the rule holds unchanged if it is ever admitted, and would add 134 columns.

## 6. Still open

- **A is unaddressed.** 646 member names behind 118 class references, and no field
  to carry the reference.
- **`.VCX` has never been read as a class library**, only measured as a container.
- **Nesting.** `layoutsty.Shape1.Name` is two levels deep. The rule as stated
  handles one level; deeper members are undercounted, not over.
- **Round trip.** An exporter must fold materialised members back into dotted
  properties. Untested; the lane has only ever exported a form built from real
  records.
- **`M###` identifiers.** Members get their own `OBJID` space. Whether a member
  should be addressable from outside its composite at all is not settled.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_COMPOSITION_RULE_V1.md
git add docs/maintenance/evidence/AIF120_composite.txt
git add docs/maintenance/evidence/AIF120_composite.png
git add gui/uidef/import_scx.py
git add gui/uidef/uidef_tk.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R30 -- composition rule implemented; 138 members materialised, 0 count mismatches; R29 corrected"
```
