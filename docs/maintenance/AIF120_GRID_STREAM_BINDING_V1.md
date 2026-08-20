---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-078
  recorded_at_utc: 2026-08-20T01:05:00Z
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
    baseline_commit: 4c336fd3b
  authorization:
    requested_by: maintainer (member.derald), in-session "good , resume our mission",
      returning the lane to its charter after the R69 engine detour. This ruling
      edits tools/uidef/ (AIF-120's own area) and adds one .dts under
      dottalkpp/data/scripts/aif120/. It does NOT edit src/ -- see section 8.
  report:
    path: docs/maintenance/AIF120_GRID_STREAM_BINDING_V1.md
    kind: ruling
---

# AIF-120 -- R70: the generated grid gets its rows, and running it found a join the document declared and the runtime never made

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R67 established that a `grid`'s runtime contract is `TupleStream`, and then nothing
constructed one. `uidef_wx.py` emitted a `wxListCtrl` with the right columns and no
rows -- a picture of a browse. R70 binds it: `--stream` makes the generated C++
construct a `DbTupleStream` from the same `BINDING` string the columns came from,
set the order, and fill from `next_page(RowLimit)`. The generated window was then
**built and run**, not syntax-checked, and that is where the ruling earned its
keep. It rendered three rows that looked completely correct and were wrong in the
two columns that came from the child area, because **the document declared
`STUDENTS -> ENROLL ON SID` and nothing had ever told the engine about it.** The
generator drew the relation in the tree and never established it. Four other
defects were found the same way. Fixed, re-run, and the three rows now match the
shell's answer for the same spec character for character.

**Evidence tier: runtime-proven.** A wx binary linking 44 house translation units,
filled from the shipped x64 school tables, screen-captured under Xvfb.

## 1. What the unit is

| | |
|---|---|
| Charter | give the existing GUI a language -- and a language whose data half is never executed is a diagram |
| Before | `grid` KIND declares columns from `BINDING` (10c) and shows an empty list |
| After | `--stream` binds the same `BINDING` to `DbTupleStream` and fills the list |
| Opt-in | yes, and deliberately -- see section 7 |
| Refusals | the contract's own, reused rather than restated -- see section 3 |
| Composes with | `--dispatch`; all four flag combinations verified -- see correction 50 |

## 2. What the generator emits

For `FRAMEDEMO.DBF`, `python3 tools/uidef/uidef_wx.py FRAMEDEMO.DBF out.cpp --stream`
adds exactly this to the file it already produced:

```cpp
extern "C" xbase::XBaseEngine* shell_engine();      // the HOST's engine, declared not defined
std::vector<std::unique_ptr<dottalk::DbTupleStream>> g_streams;
static void uidef_fill_grid(wxListCtrl*, dottalk::TupleStream&, std::size_t);
...
  relations_api::attach_engine(shell_engine());
  relations_api::add_relation("STUDENTS", "ENROLL", {"SID"});
  relations_api::set_current_parent_name("STUDENTS");
  relations_api::set_autorefresh(true);
...
  g_streams.push_back(std::make_unique<dottalk::DbTupleStream>(
      "students.lname,students.fname,enroll.cls_id,enroll.grade"));
  auto& w_G1_stream = *g_streams.back();
  w_G1_stream.set_order_physical();
  w_G1_stream.top();
  uidef_fill_grid(w_G1, w_G1_stream, 3);
...
  w_F1->SetStatusText(wxString::FromUTF8(w_G1_stream.status_line().c_str()));
```

Every line above is a call into the house. Nothing here parses a spec, walks a
cursor, joins two areas, or decides what a page is. That is the charter's line:
**glue is allowed, re-deriving is not.**

Four contract properties map to four house calls and nothing else:

| PROPS | call | closed by |
|---|---|---|
| `Order` | `set_order_physical` / `_inx` / `_cnx` | contract 4c, three values |
| `Filter` | `set_filter_for` | BETA-6.2, tuple values only |
| `RowLimit` | `next_page(max_rows)` | clamped 1..200, the house's own clamp |
| (the statusbar) | `status_line()` | contract 4b(c) |

## 3. The refusals are the contract's, not a second copy

The first version of `--stream` bound **every** grid, including three the contract
already refuses. That is worse than having no gate: the refusal is printed and the
binding ships anyway. Fixed by adding `manifest.stream_refusals(m)`, so the reasons
live in one file and the generator asks rather than re-decides. It is schema-free by
construction -- every reason is a property of the document -- which matters because
the generator is normally run with no schema at all.

Measured over the eighteen lane fixtures:

| document | outcome |
|---|---|
| `N1_editable_grid` | REFUSED -- `ReadOnly` false, contract 4b(b) / BETA-7.1 |
| `N5_ordinal_spec` | REFUSED -- ordinal spec `#2,#3`, contract 10c |
| `N6_join_no_relation` | REFUSED -- spec names two aliases, SOURCE declares no Relation |
| `P1_order_bad` | REFUSED -- `Order=lname` is not one of physical/inx/cnx |
| `P3_rowlimit_zero` | REFUSED -- `RowLimit=0` is not a positive integer |
| `FRAMEDEMO`, `N9`, `N10`, `P2`, `P4`, `P5`, `P6` | bound (7 of 7 with a grid and a legal spec) |
| `AUTHORED`, `N2`, `N3`, `N4`, `N7`, `N8` | no grid; nothing emitted |

Six refusals, seven bindings, five documents with nothing to bind. The refusal text
is the manifest's, verbatim, so a reader who wants to know why sees the same
sentence from the gate and from the generator.

## 4. Five defects, and how each was found

### R70.1 -- the gate was printed and ignored
`--stream` bound N1, N5, N6, P1 and P3 despite the manifest refusing all five.
**Found by:** sweeping the generator across the fixture set and reading what it
emitted, rather than only across the document it was written for.
**Fix:** `manifest.stream_refusals`, above.

### R70.2 -- a declared property dropped in silence
An `Order` the stream cannot be set to was skipped with no note. Harmless while
nothing consumed `Order`; the moment the stream did, a document that says `inx`
and a document that says `lname` produced the same binary. Now refused by the gate,
and the fall-through branch **kept on purpose** with a note, so a future loosening
of the gate reports the drop instead of vanishing it.

### R70.3 -- a syntax check is not a build, again
The fill helper was emitted for every document, including those with no grid, which
gives `-Wunused-function`. `g++ -fsyntax-only` **does not see it** -- gcc issues that
warning only once it generates code. R40 has said "a generator whose output is never
built is a text formatter" since the wx backend existed; this is the same sentence
one notch finer: *a generator whose output is never compiled to an object is not
checked either.* Every verification in this ruling is `-c`, not `-fsyntax-only`.

### R70.4 -- one spec, N values
The generator declares one column per comma-separated spec. That is right for
`alias.field` and wrong for `*` and `alias.*`, which are one spec and N values --
and N is a property of the schema, which the generator does not have. The first
version called `SetItem` on columns that did not exist: it compiled, it linked, it
ran, and it dropped every field after the first.
**Fix:** the columns are reconciled against the engine on the first row. Arity and
labels both come from `TupleRow::columns`, which is the only place that knows them.
The generated heads become the pre-fill placeholder -- exactly what they are
without `--stream`. This is why the rendered grid is headed `STUDENTS.LNAME`,
`STUDENTS.FNAME`, `ENROLL.CLS_ID`, `ENROLL.GRADE`: **the engine named its own
columns.**

### R70.5 -- the headline: a join the document declared and the runtime never made
The first run rendered:

```
STUDENTS.LNAME  STUDENTS.FNAME  ENROLL.CLS_ID  ENROLL.GRADE
Taylor          Quinn           S26PHYS210     IP
Martin          Mason           S26PHYS210     IP
Ramirez         Skyler          S26PHYS210     IP
```

Three distinct students, and the same enrollment three times. The parent area moved
and the child never did, because **nothing had told the engine about the relation.**
The generator drew `STUDENTS -> ENROLL ON SID` into the `tree` from `SOURCE` and
then constructed a two-alias stream over an engine that had no such edge.

This is the defect class that matters most in this lane, because there is no error
anywhere in it. Nothing refused, nothing warned, nothing returned false. Contract
10c requires a Relation edge in `SOURCE` for a cross-alias spec, the document has
one, the manifest checked it and passed it -- and the check was of a **declaration
that never reached the runtime.** A gate over a declaration proves the declaration.

**Fix:** in stream mode the generator emits the `SOURCE` relation graph through
`relations_api::add_relation`, before any stream is constructed. Same declaration,
one source, two consumers: the tree draws it and the engine enforces it.

After the fix, the same three rows read:

```
Taylor          Quinn           S26PHYS210     IP
Martin          Mason           W26CHEM200     B-
Ramirez         Skyler          F25ENGL260     C+
```

which is character for character what
`dottalkpp/data/scripts/aif120/r70_stream.dts` gets out of the shell for the same
spec. **The generated frontend and the house shell now answer the same question the
same way.** That sentence is the whole point of the lane, and it was not true
before this unit.

### Correction 49 -- mine, caught by the sweep
Having fixed R70.5, I gated the *relation calls* on "this document has relations"
and the *includes* on "a grid was actually bound." Nine of eighteen fixtures then
emitted `relations_api::` calls with no header. Two conditions for one fact.
**Fix:** one predicate, `will_bind`, computed before the walk -- necessary anyway,
because the form is emitted before its children. The class is old and keeps
recurring: **R22.1 and correction 45 were both a shared contract stated twice.**

### Correction 50 -- two modes that did not compose
`--dispatch` and `--stream` are independent, and generating with both produced a
file that did not compile: the dispatch branch built its file-scope block with
`pre = [...]`, an ASSIGNMENT, which silently discarded the stream block above it.
**Found by asking whether the two composed, not by anything failing** -- nothing in
the fixture set exercises both flags. Fixed to `pre += [...]`; all four
combinations (neither / dispatch / stream / both) now compile clean as objects, and
the no-flag output is still byte-identical to the pre-R70 baseline.

## 5. The proof

### 5a. Compiled -- objects, not syntax
All eighteen fixtures, with and without `--stream`:

```
g++ -std=c++20 -Wall -Wextra -Wsign-conversion -DDOTTALK_WITH_INDEX=1 -c ...
clean=18  dirty=0
```

The only warnings in the whole sweep are in house headers, not generated code, and
are reported in section 8.

### 5b. Unchanged -- the default generator is bit-identical
Every one of the eighteen documents generates **byte-identical** C++ without
`--stream` to what the pre-R70 generator produced. `--stream` is additive or it is
not opt-in.

### 5c. Linked -- and the link is a measurement
The generated file plus a 20-line harness links **44 house translation units**:
the xbase core (`dbarea`, `dbf_file`, `record_view`, `field_codec`, `ramfs`,
`index_hooks`, `trigger_hooks`, `xbase_locks`), the expression evaluator (17 units),
memo (5), relations, order state, work areas, path resolution, the tuple builder and
`db_tuple_stream` itself. **Not the shell.**

That number is a finding, not a footnote. R61 ruled that primitives live in
libraries and complex commands live at the CLI level; a GUI frontend is exactly the
consumer that needs `DbTupleStream` *as a library*, and today it reaches it by
linking 44 objects out of the CLI tree because there is no such library target. The
closure was computed from `nm`, not guessed -- see section 6.

The one seam that cannot be linked is `extern "C" xbase::XBaseEngine* shell_engine()`,
which `src/cli/shell.cpp` defines and which would drag in the whole REPL. The
generated file **declares** it and a host **defines** it. That is the correct shape:
the engine belongs to the host, not to the generated window.

### 5d. Rendered -- the standard R40 set
Built with wx 3.2.4, run under Xvfb against `dottalkpp/data/dbf/x64`, captured:

- the `tree` drew `STUDENTS -> ENROLL ON SID` from `SOURCE`;
- the `grid` drew four columns named by the engine and three rows of real records;
- the `statusbar` drew
  `SMARTBROWSER: rec 3 / 200 [physical] | AREA: STUDENTS [STUDENTS] | REL: conf...`
  straight out of `status_line()`.

Screen capture: `docs/maintenance/evidence/AIF120_R70_framedemo_stream.png`.

### 5e. Cross-checked -- the shell answers the same
`dottalkpp/data/scripts/aif120/r70_stream.dts` runs the same `SOURCE`, the same
spec and the same three rows through `dottalkpp`. Sections A through D of that
script are the parity proof; section E is a finding, below.

## 6. Method note -- the closure was measured

The link closure was not guessed. Seed objects were the generated file and the
harness; `nm -C` gave defined and undefined symbols per object; the closure was the
least fixed point over "who defines what." The first attempt resolved symbols by
grepping source for the function name and over-pulled 492 objects, including four
other programs' `main`. The `nm` closure is 44. **Naming a file that mentions a
symbol is not the same as naming the file that defines it**, and the difference here
was a factor of eleven.

## 7. Why `--stream` is opt-in

Binding the stream adds a hard dependency on `db_tuple_stream.hpp`,
`set_relations.hpp` and `xbase.hpp`, and turns a generated file that anyone can
compile into one that needs a built engine. Correction 39's rule is that a header
making a file buildable on exactly one machine is a defect. So the default backend
stays engine-free and portable, and `--stream` is a deliberate second mode with a
declared cost. The three other backends (Tk, HTML, character-cell) are untouched.

## 8. Reported, not fixed -- other areas

Each is outside AIF-120. None was touched.

**R70.6 -- `include/xbase.hpp`, three `-Wsign-conversion` warnings.**
`areaPtr(int)`, `areaPtr(int) const` and `area(int)` index a `std::array<...,512>`
with a signed `int`. All three are guarded by an explicit `idx < 0` test
immediately above, so they are correct today. They are the reason
`-Wsign-conversion` cannot be turned on tree-wide without touching the trinity,
which R68 declared the most conservative file in the house.

**R70.7 -- `src/cli/db_tuple_stream.hpp:71` cites the wrong ruling.**
The comment reads "PURE 64 (owner ruling, R70)". The pure-64 owner ruling is **R69**
(`AIF120_TUPLE_STREAM_RECNO64_V1.md`). It is a forward reference I wrote before the
number was assigned, and it now points at this document, which is about something
else. One word.

**R70.8 -- `HELP TUPLE` documents a syntax the lexer deletes.** This sharpens R65.3
from "unreachable" to "documented and unreachable." The shipped help text says:

```
    TUPLE #11.*                (all fields from area 11)
    TUPLE #9.*,#11.LNAME       (mix of areas)
```

Measured: `TUPLE #1.lname` prints **all ten fields of STUDENTS** -- output
identical to `TUPLE students.*`. AIF-037 cuts `#` to end of line, leaving bare
`TUPLE`, which defaults to `*`. There is no error. The user asked for one field of
one area and got the whole record, and it looks like it worked. The house's own
help is the best available argument for contract 10c's refusal.

## 9. Reported, not fixed -- in lane

**R70.9 -- the `summary` frame's static box clips its caption.** In the render,
"DESCENDANT SUMMARY" shows as "NDANT SUM". The `wxStaticBoxSizer` is sized to its
contents (`ENROLL : n`) and the caption is wider. Cosmetic, pre-existing since R66,
and not stream-related -- recorded here because this is the first run that produced
a picture of it.

## 10. Open

- **The generator does not run the manifest gate at all in default mode.** R70 wires
  it for the stream binding only. Whether a generator should refuse to emit anything
  at all for a document the contract refuses -- e.g. `P5_widths_mismatch`, which is
  a REFUSE in `check()` and is still bound here because a width mismatch does not
  make a *row* wrong -- is an owner decision, not the author's.
- **One statusbar, many grids.** Contract 4b(c) names one status source and does not
  say which when a form has two bound grids. The generator leaves the status text
  unset and emits a comment saying so, rather than guessing. Needs a contract
  sentence.
- **`RowLimit` is a first page, not paging.** Nothing yet calls `next_page` a second
  time; scrolling a generated grid is a later unit.
- **No boundary proof at the stream.** R69 left this open and R70 does not close it:
  no fixture anywhere exceeds 2^31 records with an index over it.
  `src/tests/test_recno64_sparse_e2e.cpp` proves the engine positions past 2^31 on a
  sparse table; nothing proves it *through a bound grid*.

## 11. Good Neighbor

| | |
|---|---|
| What changed | `tools/uidef/uidef_wx.py` (a `stream=` mode), `tools/uidef/manifest.py` (one new function, `stream_refusals`), one new `.dts`, one new harness file, one evidence image, contract section 4d, ledger rows |
| Whose area | AIF-120's own tools and docs. `src/` is **not** touched by this ruling |
| Authorization | maintainer, in-session: "good , resume our mission" |
| How to verify | `python3 tools/uidef/uidef_wx.py FRAMEDEMO.DBF out.cpp --stream`, then compile per section 5a; and `DOTSCRIPT aif120/r70_stream.dts` for the shell side |
| How to undo | `git revert` the commit. The default generator's output is byte-identical before and after, so reverting cannot change any existing generated file |
| Risk | low. New behavior is behind a flag that nothing calls by default |

## 12. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git status -uall

git add docs/maintenance/AIF120_GRID_STREAM_BINDING_V1.md
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add docs/maintenance/evidence/AIF120_R70_framedemo_stream.png
git add tools/uidef/uidef_wx.py
git add tools/uidef/manifest.py
git add tools/uidef/wx_stream_harness.cpp
git add dottalkpp/data/scripts/aif120/r70_stream.dts

git status -uall

git commit -m "AIF-120: R70 -- the generated grid binds DbTupleStream; running it found a relation the document declared and the runtime never made, plus a star spec that dropped every field after the first"
```
