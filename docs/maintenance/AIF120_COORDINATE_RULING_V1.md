---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260818-COWORK-010
  recorded_at_utc: 2026-08-18T15:37:58Z
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
    baseline_commit: 1a40c97a7
  authorization:
    requested_by: maintainer (member.derald), in-session, "do it" -- in reply to
      "the coordinate fork is the only remaining precondition before syntax ...
      say the word and I'll take gate 8".
    scope: >
      Proof gate 8 of the Application UI DSL lane (AIF-120): the coordinate-model
      ruling, recorded before the table schema is fixed. Measures the two form
      specimens, the four menu specimens, the shipped wx frontend and the TV
      layer. Does NOT restate the charter, R11, or the SCX baseline.
  report:
    path: docs/maintenance/AIF120_COORDINATE_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R12, the coordinate ruling (proof gate 8)

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-18.
Baseline `1a40c97a7`. Charter: `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md`.

The charter calls this "the fork that decides everything else" and requires it be
recorded **before the table schema is fixed**. R2 narrowed it and explicitly did
not choose. This chooses.

---

## 1. The three options, as the charter states them

1. **keep cells** and scale for GUI targets -- cheapest, permanently TUI-flavoured
2. **abstract units** with cells as one backend -- portable, more design up front
3. **declare layout intent** rather than position, cells derived -- most portable,
   furthest from FoxPro, most work

---

## 2. Six measurements

All at `1a40c97a7`, all re-runnable. Nothing here is recalled. Every specimen
named below is in `tools/vfp/fixtures/`; the manifest with sizes and hashes is
in `docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md`.

### M1. The one real GUI in this tree already lays out by intent, not position

`src/gui/wx/main_frame.cpp`, 81,859 bytes, the only non-TUI frontend that ships:

| construct | occurrences |
| --- | --- |
| `wxBoxSizer` | 15 |
| `wxFlexGridSizer` | 1 |
| `wxStaticBoxSizer` | 1 |
| `SetSizer` | 14 |
| `wxPoint(` | **0** |
| `SetPosition` | **0** |
| `Move(` | **0** |

**Not one absolute position in the entire frontend.** When this project builds a
real GUI it declares intent and lets the toolkit compute geometry. Option 1 is
not merely TUI-flavoured; it is contradicted by the house's own shipped practice.

### M2. The shipped GUI core carries no geometry at all

`include/gui/core/*.hpp`: the only dimension anywhere is `TableColumn::width`
(`model.hpp:164`), a display width for a browse column. No rect, no point, no
position, no layout type. The core ships models and events; the frontend owns
geometry.

This is the same architecture R11 adopted for threading. Adopting the core's
geometry answer as well is consistency, not a new opinion: **the portable
contract carries no absolute geometry.**

### M3. Menus carry zero geometry -- the fork does not touch half the DSL

Four `.MNX` specimens, **205 records**, 25 columns each:

| file | records | geometry columns | rows mentioning coordinates |
| --- | --- | --- | --- |
| `test_go.mnx` | 14 | NONE | 0 |
| `test_append.mnx` | 35 | NONE | 0 |
| `test_main.mnx` | 78 | NONE | 0 |
| `test_top.mnx` | 78 | NONE | 0 |

No `TOP`, `LEFT`, `HEIGHT`, `WIDTH`, `ROW`, `COL`, `X` or `Y` column exists in
the menu format. Position is `LEVELNAME` plus an `ITEMNUM` ordinal -- **ordinal
containment, which is exactly option 3's shape.** R8 already ruled the lane
adopts this vocabulary. It follows that the lane has *already* adopted a
layout-intent model for menus, and has been calling the fork undecided while
half of it was settled.

### M4. The form specimens are not fully absolute either -- 22 of 45 are partial

Both `.SCX` files, 58 records. 45 carry at least one of
`top`/`left`/`height`/`width`; 13 carry none (`dataenvironment` 1, `cursor` 2,
`header` 3, `textbox` 3, unclassified 4). Of the 45:

| baseclass | declares | count |
| --- | --- | --- |
| `label` | top, left, width -- **no height** | 10 |
| `textbox` | top, left, width -- **no height** | 7 |
| `editbox` | top, left -- no height, no width | 2 |
| `checkbox` | top, left, width -- **no height** | 1 |
| `container` | top, left only | 1 |
| `form` | **height only** | 1 |

**22 of 45 geometry-bearing records declare fewer than all four values**, and the
omission is systematic: text-bearing controls omit height. The source format
already expects the target to derive a dimension from content. An importer must
have a rule for the missing value, and that rule is a layout rule, not a
coordinate one.

`ACCOUNTS.SCX`'s form record declaring *only* `height` is the sharpest case: the
top-level container of a real shipped CRUD form does not state where it is or how
wide it is.

### M5. There is no typographic anchor in the file

**Zero font properties across all 58 records** -- no `fontname`, no `fontsize`,
nothing matching `font*`. So "derive cells from font metrics in the document" is
not available: the document does not carry metrics. Whatever supplies a label's
missing height, it is the target's font, not the file's.

### M6. There is no resize story in the source format

Across 58 records, properties matching `center|anchor|resiz|dock|stretch|autosiz|scale`:
`scalemode` x1, `autosize` x1. **Nothing else.** The charter's "FoxPro has no
layout manager" is confirmed by count. A DSL that copies the source format's
geometry model inherits a format with no answer for a resized window -- which is
every GUI target except the TUI.

---

## 3. R12 -- the ruling

**R12. The design table's portable geometry is layout INTENT, not position.
Absolute coordinates are permitted, quarantined, and advisory: they travel in a
separate origin group carrying the R2 scale unit, they are marked as imported
rather than authored, and a generator that ignores them entirely is still
conformant. Option 3 is chosen; option 1 survives only as a recorded import
artifact.**

Four parts.

### R12.1 -- Intent is the primary geometry, and it is ordinal

A control's placement in the table is a container reference plus an ordinal plus
an optional span -- the same shape `.MNX` already uses and the same shape the wx
frontend already builds. A generator reading only this can produce a correct
layout on any target in the charter's platform list, including the two that have
no absolute positioning worth using.

Portable because ordinal containment is the one geometry primitive every
candidate has: TV nests `TRect`s, wx nests sizers, Qt nests layouts, Tk packs and
grids, the browser flows boxes.

### R12.2 -- Absolute coordinates are quarantined, not deleted

A row may carry an origin group -- `ORIGIN_TOP`, `ORIGIN_LEFT`, `ORIGIN_HEIGHT`,
`ORIGIN_WIDTH`, `ORIGIN_SCALE` -- where `ORIGIN_SCALE` is R2's unit and any
member may be absent, because M4 proves absence is normal.

Three rules make it advisory rather than authoritative:

- a generator may ignore the whole group and remain conformant;
- a target that honours it must honour `ORIGIN_SCALE` or refuse the row -- R2 is
  unchanged, the unit still travels with the document;
- the group is marked with its provenance (imported from `.SCX`, or authored),
  so a round-trip back to a designer format can restore what it read.

This is what keeps R12 from throwing away real information. The specimens contain
genuine design decisions expressed as numbers, and discarding them at import
would make the interchange story lossy in the one direction it most needs to be
faithful.

### R12.3 -- An absent dimension is derived by the target, never defaulted to a number

M4 and M5 together: the file omits height systematically, and carries no font to
compute it from. So the table records *that* a dimension is unspecified and the
target computes it from its own content and font metrics.

The importer records which dimensions it derived, in the same discipline R2
requires for an absent scale mode. **A derived value must never be written back
into the origin group** -- that would launder a guess into a measurement, and it
is the exact shape of the failure R2 exists to prevent.

### R12.4 -- Menus declare no geometry, and the table forbids it there

M3 measured 205 records with no geometry column. The table's menu rows carry no
origin group at all. Stated so a future implementer does not add one for
symmetry and quietly make the menu half unportable.

---

## 4. Why option 3 despite being "the most work"

The charter prices option 3 highest and it is right about the absolute cost. Two
house rules say to pay it anyway.

**"Measure twice, cut once" -- the sequencing sense.** The two directions are not
symmetric. Intent-first can add absolute later as an optional annotation, which
is precisely what R12.2 does, in one commit. Absolute-first cannot add intent
later without rewriting every consumer, because a generator that has been reading
positions has no containment structure to hang intent on. **The cheap option is
cheap now and a rewrite later; the expensive option is an extension later.** That
is the house's stated sequencing test, and it points one way.

**"Go for gold unless the cost is platinum."** M1 and M3 cut the cost badly. The
wx frontend is 17 sizer constructions of worked example, and the menu half of the
vocabulary is already ordinal. Option 3's design work is not being invented from
nothing; two thirds of it can be read off shipped code.

The honest remaining cost is the form half: a container/ordinal/span model for
`.SCX` import that M4's partial records will exercise hard. That is real work and
R12 does not pretend otherwise.

---

## 5. What R12 deliberately does NOT do

- **It does not settle DPI or scaling factors.** A target that honours the origin
  group needs a DPI story; R12 makes that a target concern because ignoring the
  group is conformant.
- **It does not define the container vocabulary.** Whether intent is row/column,
  or grid, or both, is schema work under gate 10. R12 fixes that intent is
  ordinal and primary, not which containers exist.
- **It does not reopen R2.** The unit still travels. It travels attached to the
  advisory group instead of to the primary layout, which is a smaller surface,
  not a weaker rule.
- **It does not touch R9's `SKIP FOR` expressions**, which are unaffected by
  geometry.

---

## 6. Proof and disproof

**Evidence tier: source-evidenced.** Every number above is read from files at
`1a40c97a7` by `tools/vfp/read_vfp_binary.py` and by `grep -c` over tracked
source. The engine was not built or run; nothing here is `runtime-proven`.

R12 is refuted by any of:

1. a `.SCX` or `.VCX` in which controls are positioned in a way that carries
   design intent no ordinal model can express -- overlapping controls, or
   deliberate optical alignment across containers, are the cases to look for;
2. a candidate platform with no ordinal containment primitive;
3. a measured case where R12.3's derived height differs enough from VFP's
   rendering to change meaning rather than appearance;
4. a hand-authored `.SCX` that declares all four dimensions on every control,
   which would show M4's partiality as a wizard artifact rather than a property
   of the format. **This is the same specimen the lane is already waiting on**,
   which raises its value: it now tests two rulings instead of one.

The cheapest live check is gate 11's second backend. Implement R12.1 on Tk, whose
`pack`/`grid` are ordinal by construction, and see whether the two form specimens
survive the trip with the origin group switched off.

---

## 7. Handoff -- PowerShell, run in `D:\code\ccode`

Explicit paths only. Review before staging; the author does not self-approve.

```powershell
git add docs/maintenance/AIF120_COORDINATE_RULING_V1.md
git add docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R12 coordinate ruling (gate 8) -- layout intent primary, absolute quarantined"
```
