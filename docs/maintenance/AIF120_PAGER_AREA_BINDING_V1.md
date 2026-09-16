---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260916-COWORK-211
  recorded_at_utc: 2026-09-16T20:08:12Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260916-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: e98f67f5a
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-09-16 -- "Are you
      clear to resume appgui?", then "as independently as possible", then
      "assign an r number" on being shown the defect and told the allocator
      reported R146 free.
    scope: >
      Rules what a schema/sidecar panel is bound to in a browser that can change
      area. Names the defect in app_smart_browser.cpp and the remedy. NO CODE IS
      WRITTEN BY THIS RULING -- src/cli is engine and wants its own explicit go.
  report:
    path: docs/maintenance/AIF120_PAGER_AREA_BINDING_V1.md
    kind: ruling
---

# R146 -- a schema panel is bound to the AREA, and an area can change under it

Lane: AIF-120 (application-ui-dsl). Ruled by: `member.derald`.
Author: `member.ai.claude.cowork`.
Status: **review-needed** -- the author does not self-approve.

---

## 1. The ruling

**A derived view of a table -- its logical schema, its JSON sidecar, anything
resolved FROM the area rather than FROM the row -- is bound to the AREA, and it
must be re-derived when the area changes. A browser that can navigate between
areas and does not re-derive is not stale, it is WRONG: it is labelling one
table's rows with another table's structure.**

And the corollary, which is the part worth a number:

**THE SIGNAL FOR THIS IS AN AREA CHANGE, NOT A CURSOR MOVE.** These are
different events with different frequencies and different meanings, and a
listener that watches the second in order to learn about the first is inferring,
not observing.

---

## 2. The defect, measured at `e98f67f5a`

`src/cli/app_smart_browser.cpp`, `run_smart_browser()`:

    dottalk::DbTupleStream stream(spec, "");
    if (!for_expr.empty()) stream.set_filter_for(for_expr);
    stream.top();

    const auto schema  = dottalk::SchemaResolver::resolve(stream.current_area_name());
    const auto sidecar = dottalk::SidecarLoader::load_json_sidecar(stream.current_area_name());

    for (;;) {
        auto page = stream.next_page(...);
        ...
        if (ps.show_schema) { ...prints `schema`... }
        if (ps.show_json)   { ...prints `sidecar`... }
        auto pr = dispatch(stream, ps, breadcrumbs, cur_ctx);
        if (pr.action == PagerAction::Quit) break;
    }

Both are `const auto`, resolved ONCE, from the area the stream was pointing at
immediately after `top()`.

**THREE PAGER COMMANDS CHANGE THE AREA**, all via `DbTupleStream::set_spec`,
which is inline in `db_tuple_stream.hpp:41` and calls `top()` itself:

| command | what it does |
|---|---|
| `OPEN CHILD <area>` | pushes a breadcrumb, sets spec to `<area>.*` |
| `BACK` | pops a breadcrumb, restores the parent spec |
| `SPEC <spec>` | sets the spec outright |

`DbTupleStream::current_area_name()` (`db_tuple_stream.cpp:572`) reads through
`current_area()`, so it follows the spec. **After `OPEN CHILD ORDERS`, the
stream reads ORDERS and `schema` still holds CUSTOMER's.** `ps.show_schema`
lives outside the loop too, so a toggle set before the navigation keeps
printing across it.

**SO `SHOW SCHEMA` AFTER `OPEN CHILD` PRINTS THE PARENT'S FIELD LIST ABOVE THE
CHILD'S ROWS, WITH THE PARENT'S `Source:` LINE, AND SAYS NOTHING.** The same
for `SHOW JSON`. This is the one command in the tree whose stated purpose is
moving between related areas -- `OPEN CHILD`, `BACK`, breadcrumbs -- and the
derived panels are the only part of it that does not move.

### 2a. Why the previous description understated it

`SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_2026-08-20.md` called this
*"`next_page` is called once; the R74 fills also run once and nothing
recomputes them when the cursor moves"*, and the 2026-09-16 closeout narrowed
it to *"the loop is fine, the fills above it are the defect"*.

Both frame it as a CURSOR problem. It is not. A cursor move inside one area
leaves the schema correct -- the fields do not change because you skipped ten
records. **The failure needs an AREA change, which is a rarer event and a
worse one**, because a stale schema over a different table is not a delayed
truth, it is a false one.

---

## 3. The signal already exists, is exact, and is thrown away

`dispatch()` returns `PromptResult { PagerAction action; bool nav_event; }`.
`nav_event` is set `true` by `OPEN CHILD`, `BACK` and `SPEC` -- the three
commands above -- and also by `TOP`, `BOTTOM`, `SKIP`, `GOTO`, `FOR`,
`CLEAR FOR` and `ORDER`.

`run_smart_browser` reads `pr.action` and **discards `pr.nav_event`.** The
struct field is written at every site and read nowhere.

So the remedy needs no new plumbing. It needs the value to be read, and -- since
`nav_event` means "the stream moved", which is broader than "the area changed" --
**the exact test is the area NAME, compared each pass.** That re-derives on the
three commands that need it, and on nothing else, at the cost of one string
compare against a `next_page` call.

### 3a. `cursor_hook` is the wrong signal for this question, in both surfaces

The 2026-09-16 closeout offered *"R72's `cursor_hook::set_callback` is the
signal, and `gui/uidef/wx_host.cpp:91` already installs one."* Measured:

- `src/xbase/cursor_hook.hpp` declares
  `void(*)(DbArea& area, const char* reason, void* user)` and its own comment
  says **"Called by DbArea movement/edit methods."** It carries the area, so a
  listener CAN notice the area differs -- but it fires on record movement and
  edits, and there is no reason-code meaning *the view changed area*. An area
  change is learned as a side effect of the new area's cursor moving.
- A listener would therefore re-derive on every record move unless it kept the
  same last-area-name comparison the fix needs anyway.

**Use the direct test. The hook is for keeping a rendered row current; it is not
an area-change announcement, and R146 says these are different events.**

### 3b. The generated frontend does not have this defect, because it does not yet have this feature

Measured at `e98f67f5a`: `SchemaResolver` and `SidecarLoader::load_json_sidecar`
appear **zero times** in `gui/uidef/**` and `src/gui/**`. The wx host installs a
`cursor_hook` callback and no schema panel exists.

**This is recorded so the ruling is not credited with fixing something it never
touched, and so the order is clear:** when a generated Workbench grows a schema
or sidecar panel -- which is what the MINIDB browser plan
(`AIF120_MINIDB_BROWSER_PLAN_V1.md`) walks toward -- it must bind that panel to
the area from the first line, not acquire the CLI's bug by imitation. The CLI
pager is the prior art a frontend author will read.

---

## 4. The remedy, named and not written

Replace the two `const auto` initialisations with a small holder that keeps the
last area name and re-derives only when it differs, then sync it once per pass
before the panels print. Approximately eight lines, no new dependency, no
signature change, no behaviour change on any command that does not move area.

**NO CODE IS WRITTEN BY THIS RULING.** `src/cli/**` is engine and wants an
explicit go, the same posture R128, R131 and R135 each state of themselves.

**AND IT IS OWED A GRADED TEST, WHICH IS THE HARDER HALF.** The pager is
interactive, and `buffer_visibility_probe_v3_smartbrowser.dts` records the
constraint from its own run: *"SMARTBROWSER ... paints the FIRST PAGE BEFORE
reading input, and a failed `std::getline(std::cin)` returns Quit -- so under a
script it renders one page and exits."* **A `.dts` can therefore never reach
`OPEN CHILD`, so no script in this tree can exercise the defect or its fix.**
That is the same trap INDEX_X64 v2 fell into on 2026-09-13 and the suite called
PASS. The grading route is a registered ctest beside
`dottalkpp_gui_area_membership_test`, asserting on a holder that can be
constructed in a test -- which is a reason to EXTRACT the holder rather than
inline the comparison, and that is a design consequence of the test, stated
here rather than discovered later.

---

## 5. Not ruled

- **Whether `SPEC` should reset the filter.** `OPEN CHILD` clears `cur.filter`
  and `BACK` restores the previous one; `SPEC` leaves `cur.filter` untouched
  while replacing the area, so a `FOR` written against the old table's fields
  survives into the new one. Adjacent, real, and a separate question.
- **Whether the status line should NAME the area.** Today a reader has no
  cheap way to tell which area the rows came from except `SHOW BREADCRUMBS`.
  If the panels are going to follow the area, the area arguably belongs on
  screen.
- **Whether `describe()`-style struct-bound derivation exists elsewhere.**
  R82.1's third printer turned out to read a different authority than the other
  two; nothing has asked whether that shape repeats.

## 6. How to verify

    sed -n '/const auto schema/,/for (;;)/p' src/cli/app_smart_browser.cpp
    grep -n 'nav_event' src/cli/app_smart_browser.cpp     # written, never read
    grep -n 'set_spec' src/cli/db_tuple_stream.hpp        # :41, calls top()
    grep -rn 'SchemaResolver\|load_json_sidecar' gui/uidef/ src/gui/   # zero
