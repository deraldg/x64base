---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-083
  recorded_at_utc: 2026-08-20T05:20:00Z
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
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: ec8a00418
  authorization:
    requested_by: maintainer (member.derald), in-session -- pasted a REL ENUM
      demo walking five aliases with a ten-field tuple spec, then "both" to R73
      and R74. Also "mcc is made for this testing".
    scope: >
      The second grid shape the engine has and the design table does not; and
      filling the tree and summary frames from the relation introspection API
      instead of placeholders. Writes gui/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_RELATION_FRAMES_V1.md
    kind: ruling
---

# AIF-120 -- R74: the frames rendered placeholders next to an API commented "Debug / UI"

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

The maintainer pasted a `REL ENUM` demo. It walked five aliases of the MCC (My
Community College) schema -- STUDENTS -> ENROLL -> CLASSES -> TASSIGN -> TEACHERS
-- and returned ten fields per row with a limit, and `REL LIST ALL` printed the
same chain with **a match count at every hop**. R66 gave UIDEF a `summary` kind
that renders `ENROLL : n` with a literal letter *n*, because when I wrote it I had
no source for the number. `relations_api` has had one the whole time, under a
comment that reads `// Debug / UI`. R74 fills the `tree` and `summary` from that
API, and records the grid shape UIDEF still cannot express.

**Evidence tier: runtime-proven** for the fills. The second grid shape is
`source-evidenced` and named as the next unit.

## 1. What the demo showed

```
rel add students enroll on sid
rel add enroll classes on cls_id
rel add classes tassign on cls_id
rel add tassign teachers on tid
rel enum limit 10 enroll classes tassign teachers tuple students.sid,...,teachers.fname
```

```
STUDENTS
  -> ENROLL ON sid  (matches: 5)
    -> CLASSES ON cls_id  (matches: 8)
      -> TASSIGN ON cls_id  (matches: 8)
        -> TEACHERS ON tid  (matches: 5)
```

Two things follow. The first is that `rel add <parent> <child> on <field>` maps
exactly onto `relations_api::add_relation(parent, child, {field})` -- which is what
R72's generated `uidef_attach_source` emits. The generated frontend and the shell
say the same sentence to the same function. That is confirmation, and it was not
guaranteed.

The second is that **the engine has two grid shapes and UIDEF describes one.**

## 2. The two shapes

| | R70's grid | the demo's grid |
|---|---|---|
| rows | tuple spec over the **current parent record** | **enumerate a declared path** |
| runtime | `DbTupleStream::next_page(max_rows)` | `relations_api::enum_emit_for_current_parent(path, max_rows, emit)` |
| aliases | two, in practice | five, in the demo |
| contract | 4c, 10c | **nothing** |

`FRAMEDEMO` is the first. The maintainer's demo is the second, and no UIDEF
document can ask for it: contract 10c describes a spec, not a **path**. The
runtime contract for the missing shape already exists and is the exact analogue of
the one 4c named -- `max_rows` and an emit callback, against a chain that may be
given explicitly or inferred.

**This ruling does not add the kind.** It records the gap, names the runtime
contract, and leaves the design to an owner who has now seen both shapes. Adding a
half-specified `Path` property would be the R6 mistake -- generating structure from
a count property -- in a new place.

## 3. What this ruling does fix: the placeholders

`src/cli/set_relations.hpp`, immediately under `// Debug / UI`:

```cpp
std::vector<PreviewRow> list_tree_for_current_parent(bool recursive, int max_depth);
int  match_count_for_child(const std::string& child_area);
std::vector<std::string> child_areas_for_current_parent();
```

The house shipped a UI-facing relation surface and my frames rendered pictures of
it. In stream mode the generator now calls it:

- **`summary`** -- was `ENROLL : n` with a literal *n*. Now `uidef_fill_summary()` calls `match_count_for_child()`.
- **`tree`** -- was the `SOURCE` edges with no counts. Now `uidef_fill_tree()` rebuilds from `list_tree_for_current_parent(true, 8)`, which is what `REL LIST ALL` prints, and falls back to the SOURCE-drawn shape when the list is empty.

Measured, same window as R72, MCC x64 tables, current record 3 of 200:

```
before          after
ENROLL : n      ENROLL : 2
-> ENROLL ON SID          -> ENROLL ON SID  (matches: 2)
```

Capture: `docs/maintenance/evidence/AIF120_R74_live_frames.png`.

The static text remains as the **pre-fill** placeholder, exactly as the grid's
column heads do (R70.4) and for the same reason: without `--stream` there is no
engine, and a document must still render.

## 4. Correction 54 -- I fixed R70.3 once instead of making it a rule

R70.3 was: a helper emitted for a document that has no caller gives
`-Wunused-function`, and `-fsyntax-only` cannot see it. I fixed that for
`uidef_fill_grid` by gating it on `stream_vars`. Adding two more helpers
reintroduced it immediately -- **six of eighteen fixtures** bind a grid but have no
`tree` or `summary`, and got both helpers unused.

The fix is now the rule: **every emitted helper is gated on its own caller list**,
`live_trees` and `live_summaries` respectively. A defect fixed at one site and not
generalised is a defect scheduled to recur, and this one took two rulings to
recur.

## 5. Proof

- **Compiled:** 18/18 fixtures, with and without `--stream`, clean as objects under `-Wall -Wextra`.
- **Unchanged:** 18/18 byte-identical without `--stream` to the pre-R70 baseline.
- **Emitted where used:** the fills appear in 7 of 18 (the bound grids); the helper *definitions* only where a `tree` or `summary` exists.
- **Ran:** the window above, with counts the engine supplied.

## 6. Open

- **The second grid shape.** Named, not designed. `enum_emit_for_current_parent` is its runtime contract when someone rules on the document form.
- **`match_count_for_child` is `int`.** Every other count in this lane went to 64-bit under R69. Not touched here; flagged because a relation match count over a pinocchio-scale table is exactly where R69's argument applies.
- **The fills run once.** They are called after attach with the parent positioned. Nothing recomputes them when the cursor moves -- and R72 established that `cursor_hook::set_callback` is the signal that should. That is one line and belongs with the paging unit.

## 7. Good Neighbor

| | |
|---|---|
| What changed | `gui/uidef/uidef_wx.py` (two helpers, gated); this ruling; one evidence image; ledger rows |
| Whose area | AIF-120. `src/` read only. The ERP system was not touched, per the maintainer's instruction |
| Authorization | maintainer, in-session: the REL ENUM demo, then "both" |
| How to verify | `python gui/uidef/uidef_wx.py FRAMEDEMO.DBF out.cpp --stream`; build per R72 section 6; run with the MCC x64 tables |
| How to undo | `git revert`. No-`--stream` output is byte-identical before and after |
| Risk | low. Fills are additive and fall back to the placeholder when the API returns nothing |
