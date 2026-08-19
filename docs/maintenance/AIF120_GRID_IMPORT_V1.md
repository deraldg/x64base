---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-075
  recorded_at_utc: 2026-08-20T17:05:00Z
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
    baseline_commit: 8145e0880
  authorization:
    requested_by: maintainer (member.derald), in-session "continue", with three
      corrections during the run -- "our tuple system tuple_stream",
      "tuptalk allows you to build tuples", and "the smartbrowser does not need the
      cli cycle when in a gui".
  report:
    path: docs/maintenance/AIF120_GRID_IMPORT_V1.md
    kind: ruling
---

# AIF-120 -- R67: the grid imports from the corpus, and its runtime contract was already written

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R66 added `grid` and answered R6 by declaring the columns in `BINDING`. That was an
argument. This measured it against 195 corpus files, implemented the import, and then
found that the runtime half of the kind had been written in C++ long before the
vocabulary existed.

## 1. What the corpus says about grids

33 `grid` objects in 27 files. Measured, not sampled:

| measurement | result |
|---|---|
| `Column<n>.ControlSource` shapes | **99 `alias.field`**, 42 absent or empty, 3 expression, **0 bare field** |
| grids whose every bound column is `alias.field` | **17** |
| of those, satisfying 10c's Relation rule | **17 of 17** |
| grids declaring `ReadOnly = .F.` | **0 of 33** (7 say `.T.`, 26 are silent) |
| `Column<n>.Width` present | 23 of 33 |
| `ColumnCount` vs highest declared `Column<n>.` | no mismatches |

Three of these decide things that were open.

**R66's answer to R6 is reachable from real documents, not only authored ones.**
Seventeen corpus grids state their columns well enough to produce a tuple spec with
nothing inferred.

**Contract 10c's Relation rule is obeyed by the corpus, 17 of 17.** Only one grid
spans two work areas -- `1_many.scx`'s `grdItems`, columns
`orditems.line_no, products.prod_name, orditems.quantity, orditems.unit_price` -- and
that form's DataEnvironment declares `Relation3: orditems -> products ON product_id`.
The join a grid describes was already related in `SOURCE`. **A rule that no document
violates is a rule worth having and a cheap one to add.**

**4b(b) costs nothing.** Not one grid in the corpus would be refused by the read-only
rule. The constraint written in at R66 turns out to describe what VFP authors already
did.

Also worth recording: at the *column* level VFP authors qualify their bindings
completely -- 99 of 102 non-empty are `alias.field` and **none** is a bare field.
R53 measured 91.2% with 2 bare at the *control* level. A grid column is more
carefully bound than a textbox.

## 2. The import, and its four refusals

`import_scx.py` maps `grid` -> `grid`, derives `BINDING` from the columns, and
**removes `grid` from `COMPOSITE`** -- its columns are the spec, not child rows. A
grid carrying both would hold two copies of its own column list, which is the drift
4b(a) forbids for `tree` and `summary` for exactly the same reason.

Run on real forms:

```
1_many.scx    grid O007  BINDING orders.order_id,orders.order_date,orders.to_name,...
                         ColumnWidths = 55,55,207,69   ReadOnly = .T.
              grid O012  BINDING orditems.line_no,products.prod_name,...   <- the join
products.scx  grid O003  BINDING products.product_id,...  (10 columns)
                         ColumnWidths = 37,51,240,2,63,69,99,99,115,115

calc.scx      REFUSED grdProducts  column 3's ControlSource is a computed expression,
                                   not alias.field
lookup.scx    REFUSED grdCust      ColumnCount = -1: the columns are generated at
                                   runtime from the RecordSource, which is R6's
                                   implicit children exactly and is still out of v1
custorder.scx REFUSED grdOrders    RecordSourceType 4: the source is a query or a SQL
                                   statement, not a work area, and SOURCE can only
                                   name work areas (contract section 13)
books.scx     REFUSED Grid1        no column carries a ControlSource, so the columns
                                   are not declared anywhere the document can be
                                   read from
```

Four distinct reasons, each naming what the document actually did. Refusals are
recorded in `LAST_GRID_REFUSED` and printed -- R28.1's rule: v1 may decline to carry
something, it may not lose it in silence.

`calc.scx` deserves a note. Its refused columns are
`products.unit_price - products.unit_cost` and
`products.unit_price / VAL(LEFT(products.no_in_unit, AT(" ", products.no_in_unit,1)))`.
x64base has `VAL`, `LEFT` and `AT` in its own function inventory (R62), so this is a
**v1 scope statement, not an impossibility** -- the engine could evaluate these. It
is the same shape as R53's object-reference refusal: not a malformed binding, a kind
of thing v1 does not model.

`lookup.scx` is R6's original case surviving intact, and it is now refused **by
name** rather than by the whole kind being absent.

## 3. The runtime contract was already written -- new contract section 4c

The maintainer's correction mid-run: *"our tuple system tuple_stream"*.
`src/cli/tuple_stream.hpp` is five virtual methods with no console in them:

```cpp
virtual void top();  virtual void bottom();  virtual void skip(long n);
virtual std::vector<TupleRow> next_page(std::size_t max_rows);
virtual std::string status_line() const;
```

`DbTupleStream` implements it and is **constructed from a spec string**
(`DbTupleStream(std::string spec, ...)`, `set_spec`) -- the same spec `TUPLE` takes.
A `grid`'s `BINDING` is therefore not *like* a stream spec; it **is** one.

Which means R66's `PROPS` were guesses at things that already have definitions.
Contract 4c now binds each to its method:

| `PROPS` | engine | rule |
|---|---|---|
| `RowLimit` | `next_page(max_rows)` | positive integer; `app_smart_browser.cpp` clamps **1..200**, and a reader that clamps must say so |
| `Order` | `set_order_physical/_inx/_cnx` | closed set `physical`, `inx`, `cnx` -- **refused otherwise** |
| `Filter` | `set_filter_for(expr)` | BETA-6.2: evaluates on **tuple values only** |
| `ColumnWidths` | -- | ordinal-aligned with the spec; advisory under R16 |
| `ReadOnly` | -- | 4b(b): `.T.` only |

And a `statusbar` renders **`status_line()`**. `Shows` filters what the stream
reports; it does not name values the reader computes. That is the sharp form of
4b(c), and it is why the list is closed -- so a reader cannot add a seventh value the
stream never produced.

Six new refusals, authored and run: a bad `Order`, `RowLimit=0`, `RowLimit=500`
(DEGRADE, naming the clamp), and `ColumnWidths` whose count disagrees with the spec.

## 4. R67.1 -- the grid does not go through the command layer, and that is the rule

The maintainer's second correction: *"the smartbrowser does not need the cli cycle
when in a gui"*. It is right and it draws a line R66 left blurred.

R66 ruled that a frontend drives the engine through its published commands and
confirms with its observers. `SMARTBROWSER` is not such a command. It is an
interactive pager that owns stdin and runs a loop -- `TOP`, `BOTTOM`, `SKIP`, `GOTO`,
`FOR`, `ORDER`, `SPEC`, `SHOW`, `STATUS`, `QUIT`. A GUI grid already has navigation,
ordering and painting; what it needs is the rows.

> **A one-shot command is called. A REPL is not.** A frontend binds `TupleStream`
> directly for a `grid`, and drives the command layer for everything that is a single
> command with a single effect.

Driving the pager from a GUI would be reading the console output of a program nobody
asked a question -- the anti-pattern `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`
names and R55 removed. The CLI pager and a GUI `grid` are **peers over one stream**,
not layers. R66's lock methodology is untouched: `SELECT`/`LOCK TABLE` are single
commands with single effects, which is exactly the case it covers.

## 5. R67.2 -- `TUPTALK` is the type surface, and it found a defect in my own change

The maintainer's third correction: *"tuptalk allows you to build tuples"*.
`TUPTALK ADD <type> <len> [<dec>] <raw>` and `TUPTALK PUSH <field>` construct a tuple
cell by cell **with an explicit type, length and decimals** -- which is
`TupleColumn{ftype, flen, fdec}` in `tuple_types.hpp`, the engine-owned type surface
(AIF-074 R16a, *"blank-is-a-value; there is no null state"*).

That means a grid column carries a declared width from the schema the same way a
bound control does under R17 -- and the first version of my import branch **threw the
design widths away**, popping every `Column<n>.*` key once the spec was built.
`Column<n>.Width` is present on 23 of 33 corpus grids. Fixed: `ColumnWidths`, one
ordinal-aligned list, so the grid still holds exactly one copy of its column list.

## 6. R67.3 -- the tuple stream is 32-bit where the engine is 64-bit

**Finding, source-evidenced. Reported, not fixed** -- `src/cli/` is not this lane.

R63 proved the engine positions past 2^31 (`recCount64() = 2147483649`,
`gotoRec64(2147483648)`), and that `recno()` returns **-1** to signal overflow rather
than clamping. Three places downstream are narrower:

1. **`app_smart_browser.cpp:81-107`** -- the pager snapshots every open work area's
   cursor as `int32_t recno` via `a->recno()`, and restores with
   `gotoRec(slots[i].recno)` guarded by `if (slots[i].recno <= 0) continue;`.
   Past 2^31, `recno()` is `-1`, so the guard fires and the cursor is **silently not
   restored** -- then `relations_api::refresh_if_enabled()` re-syncs children to
   wherever the browse left the parent. The Smart Browser's stated promise is to
   preserve every cursor. **The failure is a missing restore, not a corrupt seek, and
   only because `recno()` signals rather than clamps** -- the same design decision
   that made R63's `.lock.-1` visible instead of plausible.
2. **`db_tuple_stream.hpp:26-59`** -- `skip(long)`, `goto_pos(long)`,
   `goto_recno(long)`, `cur_recno_`, `max_recno_`, `last_emitted_recno_` are all
   `long`. `long` is **64-bit under gcc (LP64) and 32-bit under MSVC (LLP64)**, and
   `ABOUT` reports the shipping build is MSVC 1944. So the same source is 64-bit on
   the WSL build and 32-bit on the Windows one.
3. **`db_tuple_stream.hpp:51`** -- `std::vector<uint32_t> order_recnos_` is 32-bit on
   **both** platforms.

None of this bites today: pinocchio is 5,501,358 rows (R61.6) and nothing in the
corpus is near 2^31. It is recorded because R63 established the engine goes there and
these three are where a browse would stop following.

## 7. Correction 46

Two in one branch, both found by running it rather than reading it:

- The design widths dropped (section 5). Found because the maintainer named
  `TUPTALK`, not because anything failed.
- `ReadOnly` written **twice** -- my `keep['ReadOnly'] = '.T.'` landed beside the
  source's surviving lowercase `readonly`, leaving a reader to break a tie. Fixed by
  dropping every case variant first.

The second is the same shape as R66.1: a property that is present twice, like an
alias table that keeps only the last entry, is not a wrong answer -- it is an answer
nobody would think to check.

## 8. Evidence tier

**runtime-proven**: sections 1, 2, 3 and 5 -- 195 corpus files measured, six real
forms imported (three grids carried, four refused with four distinct reasons), six
new `PROPS` refusals authored and run, and all four backends still render
`FRAMEDEMO` (wx clean under `-Wall -Wextra`).
**source-evidenced**: sections 4 and 6, from `tuple_stream.hpp`,
`db_tuple_stream.hpp`, `tuple_types.hpp` and `app_smart_browser.cpp`.
**Regression swept**: `lock_provider_test`, `lock_semantics_test` and R66's eight
refusal cases all still pass.

## 9. Still open

- **The stream is not wired.** Contract 4c states the binding between a `grid` and
  `DbTupleStream`; no generated frontend constructs one yet. That is the next unit
  and it is a real one -- `uidef_wx.py` emits a `wxListCtrl` with columns and no
  rows.
- R67.3 is reported. So are R64.1, R64.2, R65.3 and R65.4.
- `TupleStream` has `top`/`bottom`/`skip` but no `goto`, while **BETA-6.1** freezes
  "TOP/BOTTOM/SKIP/GOTO semantics for tuple iteration". `DbTupleStream` has
  `goto_pos`/`goto_recno` outside the interface. A second implementation would not
  have to provide them. Noted, not a finding -- the interface may be deliberate.
- Unchanged: R55.2; the section 13 query limit (R62.2), which section 2's
  `RecordSourceType 4` refusal now has a concrete instance of; per-handler metadata
  on `HANDLERS`; pinocchio-scale; whether the lane's harnesses become `.dts` (R64).

## 10. Good Neighbor note

- **What changed.** Contract section 4b's `grid` row and 4b(c); new section 4c.
  `import_scx.py` (grid mapping, spec derivation, four refusals, `ColumnWidths`) and
  `manifest.py` (the 4c property checks). New document:
  `docs/maintenance/AIF120_GRID_IMPORT_V1.md`.
- **Whose area.** AIF-120's own. **No engine source was edited.** `src/cli/`'s tuple
  stream and smart browser were read and are named in section 6; the corpus was read
  only.
- **What authorization.** Maintainer (member.derald), in-session "continue" plus the
  three corrections recorded in the front matter.
- **How to verify or undo.** Verify: `python3 tools/uidef/import_scx.py 1_many.scx
  UI_1_many` (needs `1_many.sct` beside it) and read `BINDING` on the two `grid`
  rows; `calc.scx`, `lookup.scx`, `custorder.scx` and `books.scx` print the four
  refusals. Undo: the contract sections and the two tool diffs revert
  independently; no existing document imports a grid today, so nothing regresses.

## 11. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

R65 and R66 are still uncommitted; their blocks are in
`AIF120_TUPLE_SPEC_V1.md` and `AIF120_FRAME_KINDS_V1.md` section 11. Run those
first, then:

```powershell
cd D:\code\ccode
git add tools/uidef/import_scx.py
git add tools/uidef/manifest.py
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add docs/maintenance/AIF120_GRID_IMPORT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R67 -- the grid imports from the corpus, 17 of 17 obey the Relation rule, and TupleStream is the kind's runtime contract"
```
