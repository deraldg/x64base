---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-102
  recorded_at_utc: 2026-08-22T01:29:34Z
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
    baseline_commit: 8aca9ef1b
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 --
      "ambiguity first, we need a good schema". Design only; authorises no build.
  report:
    path: docs/maintenance/AIF120_NAME_SCHEMA_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R112: the name schema. One name, not unique, and nothing says so

Status: **ruling, review-needed. NO BUILD AUTHORISED BY THIS DOCUMENT.**
Sec 6a records the steward's ruling of 2026-08-22 on the ambiguity behaviour;
the rest of the document is the design that ruling sits on, and still wants
review.
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `8aca9ef1b`.

Prerequisite for **I1.3** (scoped name resolution) and therefore for **I1.2**
(re-keying the relation graph). Both address things by name; neither is safe
until it is written down what a name *is* and what it guarantees.

---

## 1. What a name is today, measured

| identifier | lives at | unique? | enforced where |
|---|---|---|---|
| **logical name** | `DbArea::_logical_name`, `include/xbase.hpp:435` | **NO** | **nowhere** |
| **absolute path** | `DbArea::_dbf_abs_path` | yes | `WORKSPACE ADD`, `cmd_workspace.cpp:3645` `find_open_area_for_path` |
| **slot index** | **not on the area at all** -- recovered by linear scan, `workarea_util.cpp:53` `slot_of_area` | yes, by construction | implicit |
| **DTSHEMA `alias=`** | posture line | -- | -- |

Three facts that are easy to assume otherwise:

1. **`name()` and `logicalName()` are the same field.** `include/xbase.hpp:238`
   returns `_logical_name` by const reference; `:288` returns a copy of
   `_logical_name` and is commented `---- Legacy compatibility ----`. They are
   synonyms, not two handles.
2. **`alias=` is a RENAME, not an alias.** On load, `cmd_workspace.cpp:1948-1950`
   applies it through `setLogicalNameIf` -> `setLogicalName()`, which assigns
   `_logical_name` (`xbase.hpp:296`). The companion `setLegacyNameIf` resolves to
   the SFINAE no-op, because **`DbArea` has no `setName`** (0 matches in
   `xbase.hpp`). An area has exactly one name and `alias=` overwrites it.
3. **`DbArea` carries no alias member, no slot member and no owner back-pointer.**
   Which is why every one of these lives in a side table -- the finding AIF-078
   recorded and I1 exists to fix.

**The schema statement, in one line: the only unique identifiers an area has are
the ones nothing addresses by (path, slot), and the one everything addresses by
(name) is the one nothing keeps unique.**

## 1a. Prior art -- most of sec 1 was already written down, in the file I was reasoning about

`src/cli/cmd_use.cpp:378-399` carries a comment block dated 2026-08-12 that
states independently, and correctly, nearly everything in sec 1:

> `_db_name` -- 3 writers (`xbase.hpp:297`, `dbarea.cpp:128,205`), **ZERO
> readers** anywhere in the tree. A write-only member.
> `_setLegacyName()` -- DbArea has no `setName()`, so this SFINAE wrapper
> selects its empty fallback and has **ALWAYS** been a silent no-op.
> AREA's two lines -- "Logical name" and "Legacy name()" both render
> `_logical_name`, which is why they always agree.

and closes with:

> "The table-name-vs-alias split those fields were shaped for needs a setter and
> accessor on DbArea; `xbase.hpp` is a wide include, so that is **priced
> separately** rather than smuggled in here."

That is I1's wide-header pricing, anticipated ten days before R111 measured it.
**I should have read this before writing sec 1** -- it is in the file that
implements the verb the whole ruling is about. Recorded as a process miss, not
folded in silently.

It also supplies a **fourth name field and a syntactic rule sec 4 omitted**:

- **`_db_name`** is a fourth name-like member, written in three places and read
  nowhere. It is not an identity; it is dead weight, and any schema work should
  retire it rather than define it.
- **`alias_is_addressable()`** (`cmd_use.cpp:399`): a purely numeric name is
  **not addressable**, because `SELECT` reads a digit string as an AREA NUMBER --
  alias `3` would silently select slot 3 instead of the table. So the schema has
  a syntactic constraint as well as a uniqueness one, and it already exists in
  code.

## 2. A correction to my own claim of an hour ago

In session I said the resolver checks two *different* names, so area 7's
`logicalName()` could shadow area 3's `name()`. **That is wrong** --
`workarea_util.cpp:44-47` compares the target against `logicalName()` and then
against `name()`, which sec 1 shows is the same string. The second comparison
cannot match when the first did not. It is dead code, not a second alias.

The ambiguity is real; the mechanism I gave for it was not. The real mechanism is
sec 3. Recorded rather than quietly corrected, because the wrong mechanism would
have sent I1.3 after the wrong fix.

## 3. The collision is reachable today, and the corpus is full of it

`find_open_area_for_path` guards duplicates **by path**, so the same file cannot
occupy two areas. It says nothing about names. Two *different* files with the
same basename therefore both open, both take the same default logical name, and
`find_open_area_by_name_ci` silently returns the lower slot.

Measured under `dottalkpp/data/dbf/`:

    dbf/x64  14 tables      dbf/x32  13 tables      dbf/vfp  12 tables

**Twelve basenames exist in all three flavour roots** -- `students`, `teachers`,
`classes`, `enroll`, `courses`, `dept`, `majors`, `rooms`, `stud_maj`, `tassign`,
`terms`, `building`. That is the MCC schema, the main demo corpus. Open the x64
and x32 workspaces together and there are two areas named `STUDENTS`, addressed
by one string, resolved first-slot-wins, with no signal.

These same twelve are what the relation graph would collide on: one
`unordered_map` keyed on the bare uppercased parent name
(`set_relations.cpp:60`), no owner field.

**And it needs no second workspace.** `USE` guards duplicates by path only
(`cmd_use.cpp:688` `find_open_area_for_path`), and `USE ... ALIAS <name>` sets
the logical name with **no uniqueness check at all**. Both of these are legal
today, in one workspace:

    USE dbf\x64\students.dbf
    USE dbf\x32\students.dbf          -- two areas, both named STUDENTS

    USE dbf\x64\teachers.dbf ALIAS STUDENTS   -- a deliberate collision, accepted

That matters for sequencing: the **within-workspace** half of this schema is
worth enforcing now, on its own, before any multi-workspace work.

## 4. The proposed schema

Four levels of identity, most stable first. Only level 3 is new.

| # | identity | scope of uniqueness | status |
|---|---|---|---|
| 1 | **`(workspace_handle, slot_index)`** | global, by construction | **I1.0 puts it on the area**; today recovered by linear scan |
| 2 | **absolute path** | global | exists, enforced |
| 3 | **logical name** | **unique WITHIN a workspace** | **the new invariant** |
| 4 | **qualified name** `WS.#n.TABLE` | global | type exists, resolves nowhere (sec 6) |

**The new invariant, stated to be enforced:**

> Within one workspace, no two open areas may carry the same logical name.
> Across workspaces, logical names MAY repeat, and an unqualified name that
> matches in more than one open workspace is **ambiguous, not first-wins.**

That is the whole schema. It is the minimum rule that makes name addressing
sound, and it has exactly **two** enforcement points -- the open path and the
rename path (`setLogicalName`, reached from `alias=` and from `USE ... ALIAS`).

Level 1 is what makes level 3 checkable: you cannot ask "is this name already
taken in *this* workspace" until an area knows which workspace it is in.
**I1.0 is therefore a prerequisite of I1.3, not merely cheaper than it.**

## 5. The invariant is already true -- enforcing it breaks nothing measurable

Every `alias=` in every live posture, checked for repeats within its own
workspace (`tools/dbf/minidb_depth_census.py` reads the same containers):

    postures examined               : 37
    postures with a duplicate alias : 0

**37 of 37 already satisfy it.** Enforcement is therefore a guard on a rule the
data already keeps, not a migration. That is the cheapest kind of invariant to
add and the argument for adding it now, before I1.2 makes collisions likelier.

Each posture carries a single `DBFROOT`, which is *why* the invariant holds
today: one root cannot contain two files of the same basename. It is a property
of the current one-workspace-at-a-time model, and it stops holding the moment
two roots are open at once -- which is the entire point of the lane.

## 6. What the ambiguity rules then are

**Within a workspace -- prevent, do not report.** A second area taking a name
already held in the same workspace is refused at the point of the open or the
rename, naming the slot that holds it. Cheap, local, and no caller changes,
because it fails before an ambiguous state exists.

**Across workspaces -- refuse the unqualified name and say why.** An unqualified
name matching in two open workspaces returns "ambiguous", lists the candidates as
`WS.#n.TABLE`, and resolves nothing. This is the user-visible change and it is
the half that needs the steward's ruling.

Considered and rejected outright:

- **Auto-disambiguate (`STUDENTS`, `STUDENTS_2`).** Invents names the user never
  typed and that no posture records. It would also make the DTSHEMA round trip
  lossy, which is a worse defect than the one being fixed.

## 6a. Steward's ruling, 2026-08-22, and a contradiction of mine it exposes

**Ruled: require qualification when ambiguous, with first-wins-plus-warning as a
migration step.**

**The contradiction.** In session I proposed exactly that -- "the third with the
second as a migration step". The first draft of this document then listed
first-wins-plus-warning under *considered and rejected*, calling it "breaks
nothing, fixes nothing". Both statements are mine, an hour apart, and they do not
agree. The steward's ruling is the one that stands; what follows is the
reconciliation, because "the steward chose" is not by itself a reason the earlier
objection stopped being true.

**The objection was to option 2 as a DESTINATION, and it holds.** A warning
printed beside a wrong answer, from a resolver called at 32 sites across 10 files
most of which print nothing, is not a fix. As a permanent policy it should stay
rejected.

**As a time-boxed migration phase it is a different thing, on one condition:
it must be instrumented, not merely printed.** The warning's job is not to
inform a user at the console; it is to **enumerate every site that will break**
when the hard refusal lands. So:

- the ambiguity path **counts and records** each occurrence -- resolver call
  site, the name, and the candidate areas -- not just prints;
- the migration ends on a **measured zero**: the recorded count is zero across
  the `.dts` regression corpus and the relation scripts (once R111 sec 3a's
  coverage gap is closed);
- the phase is **time-boxed by that measurement**, not by a date, and flipping to
  hard refusal is its own commit and its own ruling.

Stated that way the two positions are one position: option 2 is not a weaker
version of option 3, it is the **instrument that tells you when option 3 is safe
to turn on**. A warning nobody reads stays worthless; a counter that has to reach
zero is a gate.

**A sequencing consequence the ruling makes visible.** The migration phase can
only observe cross-workspace ambiguity once two workspaces can be open at once --
before that it would record zero for the wrong reason, and a zero that means
"nothing was tested" is exactly the false green the house's trap-4 is about. So:

| half | when | what |
|---|---|---|
| **within-workspace: prevent** | **now**, independent of I1 | refuse a duplicate name at open/rename. Reachable today (sec 3), needs no workspace handle to check when there is only one workspace |
| **cross-workspace: qualify** | with multi-workspace | the instrumented warning phase, then hard refusal by measured zero |

The within-workspace half is not blocked on I1.0. The cross-workspace half is,
and on level 4 being wired (below).

**The cost that is not free:** level 4 exists as a *type* only. The parser and
renderer live in `src/reference/qualified_reference.cpp`, and the consumers are
`src/tests/test_pdlc_foundation_smoke.cpp` and **nothing else** -- **zero files
under `src/cli` reference it**. So "return the candidates as `WS.#n.TABLE`" means
wiring that surface to the resolver for the first time. That is real work and it
belongs in I1.3's price, not hidden in it.

## 7. What this changes in the plan

- **I1.0 is promoted from cheap-and-useless to prerequisite.** It carries level 1,
  without which level 3 cannot be checked. It also retires `slot_of_area`, a
  linear scan with **21 call sites across 15 files**, into a field read.
- **I1.3 gains a dependency** -- wiring the qualified-reference surface into the
  resolver -- and **loses** the one I invented, since sec 2 shows the two-name
  mechanism does not exist. Per sec 6a it also **splits**: the within-workspace
  refusal is separable and lands first, and the instrumented migration phase is
  a third piece that only becomes meaningful once two workspaces can coexist.
- **`_db_name` should be retired, not defined** (sec 1a): three writers, zero
  readers. Any hand that is already inside `xbase.hpp` for I1.0 can delete it in
  the same pass, at no extra rebuild -- that is the one genuinely free rider on
  the 337-TU recompile.
- **I1.2 inherits the schema.** Once a name is unique within a workspace, the
  relation map's key is `(workspace_handle, name)` and it is well-defined. Until
  then, any key is guesswork. R111 sec 3a's coverage gap still blocks it
  independently.

**Recommended order, unchanged from R111 except in confidence:** I1.0, I1.1,
I1.3, I1.2.

## 8. Evidence tier

**Source-evidenced:** sec 1, sec 2, sec 3, sec 5, sec 6 (consumer count) -- every
file:line verified at `8aca9ef1b`; the basename overlap counted on disk; the
posture alias check re-run over all 37 containers.

**Chat/AI output:** sec 4, sec 7. No code was written under this note.

## 9. Good Neighbor note

- **What changed.** One new file,
  `docs/maintenance/AIF120_NAME_SCHEMA_RULING_V1.md`. No source file edited.
- **Whose area.** The invariant lands in **engine** code (`src/cli/**`,
  `src/xbase/**`), which is not this lane's to change without an explicit go.
  This note proposes; it does not assume.
- **What authorization.** Steward, in session, 2026-08-22: "ambiguity first, we
  need a good schema." Design only. Ships `review-needed`; the author does not
  self-approve.
- **How to verify.** sec 1: read `xbase.hpp:238`, `:288`, `:296`, `:435` and
  `cmd_workspace.cpp:1948-1950`; `grep -c "void *setName" include/xbase.hpp`
  returns 0. sec 3: `ls dottalkpp/data/dbf/{x64,x32,vfp}/*.dbf` and compare
  basenames. sec 5: re-run the posture alias check over `tmp/minidb/`. sec 6:
  `git grep -l qualified_reference -- src/cli` returns nothing.
- **How to undo.** Delete this one file. Nothing else was touched.
