# Ticket: multi-workspace in `dottalk_wx` -- open the GUI over the schema

**Status: TICKET, ready to claim. Authorises no build until a number is
allocated.** Proposed assignment: **GUI slice of the multi-workspace work**,
steward ALPHA (`member.ai.claude.cowork`), owner `member.derald`.

Parent design of record: `docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md`
(target design, revised after hostile review). Related lanes: AIF-070 (what a
workspace IS), AIF-078 (how a name RESOLVES). This ticket takes neither claim --
it is the **presentation layer** over what those two settle.

Claim a number with `claim-aif` before anything here is built. Grep is not an
allocator.

---

## 1. The steward's thesis, checked

> *"It should be straightforward, we already have hydration to CLI, we just open
> the GUI over the schema."*

**Correct, and the tree says why.** The Workbench does not talk to the engine
through a private path -- `MainFrame` submits command strings to `AsyncSession`
(`LoadWorkspaceFile` sends `workspace load <path>`). One engine, one area array,
one command executor. So anything hydration puts in front of the CLI is already
in front of the GUI; the GUI has simply never rendered it.

Three things make the GUI slice genuinely small:

- `WorkbenchPage` already has `Tables`, `Indexes`, `Relations`, `Workspace`.
  The pages exist; they are single-workspace by assumption, not by design.
- `workspace_graph_` is a `wxTextCtrl` fed by `format_workspace_graph_text()`.
  There is a graph function already; it renders to text.
- The qualified spelling is **already written and already parsed**:
  `WS.#n.TABLE.RECNO(k).FIELD` through `QualifiedReferenceParser`, rendered by
  `DataAddress::diagnostic_text()`. The GUI does not need a new address syntax.
  It needs to *display* one that ships.

---

## 2. The column, and it is one column plus one selector

> *"the app also needs a column or more to accommodate multiple workspaces"*

Design invariant **I1**: *an area belongs to exactly one workspace, and there is
no null* -- bare `USE` opens into an implicit always-present `DEFAULT`.

That single invariant is what makes the GUI change small and total:

| surface | change |
| --- | --- |
| Tables page | **add `WS` column**, leftmost. Never blank -- `DEFAULT` is a workspace |
| Indexes page | same `WS` column; an order belongs to its area's workspace |
| Relations page | **two columns** -- `WS` and, for a crossing relation, the qualified child. A relation is only cross-workspace if the design later allows it; today it is intra-workspace and the column proves it |
| Areas list | group by workspace, or sort by `WS` then slot |
| Status bar | a **current-workspace** field beside the current-area field |
| Workspace page | becomes the registry projection -- `WORKSPACE LIST`'s columns: name, carrier, residence, areas, groups, locks held |

### 2a. Four rules, because the area space is not small

The first draft of this ticket assumed a few hundred areas and would have
shipped that assumption into the GUI. `MAX_AREA` is not a constant: it is
`static_cast<int>(dottalk::build::max_areas)` (`include/xbase.hpp:43`),
generated per build from the `DOTTALK_MAX_AREAS` cache variable and reported at
run time by `BUILDVECTORS`. The 512 this build carries is a GATE #1
compatibility default with **no upper bound**; the declared ceiling is the
build vector's own `max_areas <= uint32_t::max()`.

1. **Never render per slot.** The CLI's `WORKSPACE` listing prints one line per
   slot -- 512 `--- closed ---` lines in a live transcript -- and the WAM report
   prints one row per slot with a pointer. Correct as diagnostics, fatal as a
   grid. The Tables page lists **open areas only**, so row count tracks the
   working set and not the address space.
2. **The slot is not an int-safe display value.** Carry it as 64-bit and format
   it as text -- see F8.
3. **No linear name resolution in the GUI.** `find_open_area_by_name_ci` is a
   first-match linear scan with no ambiguity signal. The GUI asks the registry.
4. **`WS` is the grouping key**, not a decoration. Group open areas by
   workspace and the view stays proportional to what is open.

Plus one **workspace selector** (a `wxChoice` in the toolbar) bound to
`WORKSPACE SELECT <ws>`. That is the whole interaction model: the selector sets
scope, the `WS` column shows scope, and nothing in the GUI ever has to guess.

**The column is not decoration -- it is the ambiguity signal.** I4 says names
resolve within their workspace and *ambiguity is reported, never first-match*.
Today `find_open_area_by_name_ci` is a linear scan that silently takes the first
match. When two workspaces both hold `STUDENTS`, a `WS` column is the difference
between a user seeing two rows and a user seeing one row that is quietly the
wrong one.

---

## 3. DTSHEMA 3 mapped to the GUI, line by line

Every line kind, what it means, and where it lands. Measured across all 106
payloads in the live catalog.

| posture line | count | GUI home |
| --- | ---: | --- |
| `DTSHEMA <n>` | 106 | Workspace page header -- format badge |
| `WSID F<stamp>\|M<ws_id>` | 106 | Workspace page -- instance identity, and the link back to the catalog row |
| `FLAVOR X64` | 93 | Workspace page badge; drives the DBF version column |
| `DBFROOT` / `IDXROOT` / `LMDBROOT` | 93 each | Workspace page -- residence. **Colour RAM differently from disk**; a hydrated workspace looks identical to a disk one today and is not |
| `AREA <n> \| dbf= \| index= \| indextype= \| tag= \| alias=` | **1,798** | Tables page rows; `index`/`indextype`/`tag` feed the Indexes page |
| `RELATION <parent> <child> ON <key> [TO <childkey>]` | **1,102** | Relations page, and the edges of the schema graph |
| `CURSOR <area> <recno>` | 1,247 | per-row cursor position; restores the browse grid to where it was |
| `CURRENT <area>` | 89 | which area is selected on load |
| `KEY <table> <field> UNIQUE\|PRIMARY` | **0** | see section 5 |

**Two mapping notes that are not obvious:**

1. **`AREA <n>` is an ORDINAL, not a slot.** Invariant I3: LOAD walks the `AREA`
   lines in order, allocates a fresh slot per line, and resolves `CURSOR k` /
   `CURRENT k` **by position in that sequence**. The GUI must show the live slot
   from the runtime and must never present the posture's number as a slot -- the
   two agree only in the classic single-workspace case.
2. **`RELATION` carries an optional `TO`.** 190 of the 1,102 lines (17.2%) bind
   *differently named* endpoints -- `ON EMPLOYEE_ID TO APPROVED_BY`,
   `ON EMPLOYEE_ID TO REPORTS_TO` (a table related to itself). A renderer that
   labels edges with one key name is wrong one time in six.

---

## 4. `WS_ID`, and what it suggests about normalization

> *"check the workspace id for ideas for db normalization"*

**Why a meaningless key is the right one, demonstrated in this very table.**
`WS_ID` carries no business meaning, which is what lets it be stable identity
AND lets `PREV_ID` chain lineage across 106 rows. `WS_NAME` carries meaning, so
it is deliberately NOT unique -- 89 of the 106 rows are `SUPERSEDED` and the
names repeat on purpose. Had identity been keyed on the name, the supersede
chain could not exist. That is the reason the projection below hangs off
`WS_ID` and never off `WS_NAME`: the child tables join on the key that cannot
change, and inherit none of the name's mutability.

**What `WS_ID` already is.** A surrogate integer key, allocated max+1 under the
catalog `FLOCK`, declared PRIMARY through `unique_reg`, with `PREV_ID` carrying
lineage to the row a save superseded. Measured: 106 rows, ids 1..106 dense, and
the memo store's own object ids run 1..106 matching one-for-one. It is a real
key with a real chain, and 89 of the 106 rows are `SUPERSEDED` history hanging
off it.

**The normalization the schema is asking for.** The catalog is one wide row --
20 fields, reclen 703 -- with the entire structure (1,798 areas, 1,102
relations, 1,247 cursors) **denormalized inside a memo blob**. Everything the
GUI wants to put in a grid currently requires parsing a payload.

The relational shape is obvious once `WS_ID` is taken seriously as a key:

    WORKSPACES   WS_ID (PK)  WS_NAME  FMT  SIZE_B  PREV_ID  SUPERSEDED ...
    WS_AREAS     WS_ID (FK)  ORDINAL (PK with WS_ID)  DBF  INDEX  INDEXTYPE  TAG  ALIAS
    WS_RELATION  WS_ID (FK)  PARENT  CHILD  KEYFIELD  CHILDKEY
    WS_CURSOR    WS_ID (FK)  ORDINAL  RECNO
    WS_GROUP     WS_ID (FK)  GROUP_NAME          -- membership, per the groups design

`WS_AREAS` is in 1NF the moment the posture's `AREA` line stops being a string.
`WS_RELATION` is where `TO` stops being an optional clause and becomes an
honest nullable column. And the join that draws the whole GUI becomes
`WORKSPACES -> WS_AREAS -> WS_RELATION ON WS_ID` -- which is exactly the
relation model the engine already has, applied to itself.

**The constraint that decides the design.** The MINIDB record states it:
*"The catalog is the only index of what exists; there is deliberately no second
registry to drift."* Three child tables ARE a second registry -- unless they are
**derived**. So:

> **Proposal: normalize as a PROJECTION, not as a source.** The posture inside
> the memo stays authoritative. `WS_AREAS` / `WS_RELATION` / `WS_CURSOR` are
> regenerated from it, the way Tier 0 is regenerated from the tree -- generated
> files that carry their generator's name and cannot be hand-edited. Then the
> GUI joins tables instead of parsing blobs, the catalog gains no second truth,
> and a projection that disagrees with its posture is a detectable defect rather
> than a silent divergence.

And the part that makes it worth doing beyond the GUI: **the projection is
dogfooding.** The database that describes databases becomes a related schema you
open in the browser you are building. `USE WS_AREAS` and `SET RELATION` on
`WS_ID` is the map in the same ink as the territory -- which is what this
catalog already claims to be.

---

## 5. What I measured that changes the plan

**F1. `KEY` lines: declared, produced never.** The serializer emits
`KEY <table> <field> UNIQUE|PRIMARY` unconditionally over every open area
(`cmd_workspace.cpp:1586-1600`), and the loader parses it back into `unique_reg`
(`:2026-2038`). **Zero KEY lines exist across all 106 postures.** No area in any
saved workspace ever carried a unique or primary declaration, so the writer runs
and emits nothing. The format has a place for keys; the corpus has none. A GUI
column for PRIMARY would be empty on every row today -- worth building, worth
saying it will start empty, and it makes the normalization in section 4
declaration-driven rather than inferred.

**F2. AIF-108's recursion blocker is stale.** That charter (2026-08-11) records
that nested databases *"would FAIL SILENTLY today -- `build_minidb_container`
does not carry memo sidecars"*, and blocks all ten recursion test ideas on it.
Memo-sidecar carriage landed **2026-08-12**. Measured: **30 of the 37 MINIDB
containers carry a nested `.dtx`** (`MDMEMO.dtx`, `STUDENTS.dtx`,
`TEACHERS.dtx`; leading bytes `DT`). The blocker is closed and the row still
says it is open. Ten test ideas are unblocked and nobody has been told.

**F3. `DEPTH` and `SELF_REF` remain 0 and `F` on all 106 rows.** Reserved for
nesting, never non-zero. Unchanged by F2 -- carriage of a *sidecar* is not
carriage of a *catalog*.

**F4. The COMMIT ruling does NOT extend to RECALL, because `ALL` is two
different words.** `WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` section 3 records
the owner ruling of 2026-08-12: `COMMIT ALL` / `ROLLBACK ALL` scope to the
CURRENT workspace, `COMMIT GLOBAL` / `ROLLBACK GLOBAL` spell the crossing.
Reading `cmd_recall.cpp` and `cmd_delete.cpp` against `cmd_commit.cpp` shows the
parallel is false, and the shipped usage contracts say so themselves:

| verb | `ALL` means | evidence |
| --- | --- | --- |
| `COMMIT` | all **AREAS** | *"the current area or all open buffered areas"*; real sweeps at `cmd_commit.cpp:144`, `:615` |
| `ROLLBACK` | all **AREAS** | sweeps at `cmd_rollback.cpp:69`, `:148` |
| `DELETE` | all **RECORDS** in the current area | `DELETE ALL / REST / NEXT <n> / FOR <expr>` |
| `RECALL` | all **RECORDS** in the current area, deleted-only | `RECALL ALL / REST / NEXT <n> / FOR <expr>` |

`DELETE`/`RECALL`'s `ALL` is the classic dBASE **record scope** -- one of the
oldest constructs in the language, and orthogonal to areas entirely. Rescoping
it to "all areas of this workspace" would redefine a shipped verb whose meaning
predates workspaces by forty years.

**And neither verb crosses areas at all today.** Their only `MAX_AREA` loop is
`resolve_current_index()` (`cmd_recall.cpp:116-123`, `cmd_delete.cpp:149-156`)
-- a pointer scan to find which slot the CURRENT area occupies, so fields can be
marked stale. So `RECALL GLOBAL` would not be a widening of an existing sweep.
It would be a **new capability**: mass un-delete across every open table in
every workspace. That is a very sharp verb and it deserves its own ruling rather
than inheriting one written for buffer flushes.

**F5. Ten copies of the same slot scan, and two of them are byte-identical.**
`resolve_current_index()` -- `for (int i = 0; i < xbase::MAX_AREA; ++i) if
(&eng->area(i) == &A) return i;` -- appears in **ten files** under `src/cli/`:
`cmd_area`, `cmd_calcwrite`, `cmd_commit`, `cmd_delete`, `cmd_rebuild`,
`cmd_recall`, `cmd_reindex`, `cmd_replace`, `cmd_rollback`, `table_buffer`. The
`cmd_recall` and `cmd_delete` copies md5 the same. This is AIF-078's D2 --
*store the slot in `DbArea`, killing D2 and the duplicated scan sites* -- and it
is on the ordinary mutation path, so it runs per DELETE and per RECALL. It gets
worse with the cap raise the multi-workspace work wants, and the fix is the same
one P1 already recommends.

---

## 5b. The three limits the GUI must respect, measured

The engine already bounds this work in three independent ways. None of them
scales with the other two, which is what makes the GUI tractable.

| what | bound by | where |
| --- | --- | --- |
| open areas | the working set, not `MAX_AREA` | the GUI lists open areas only |
| the relation graph | cascade **depth** and **scan** | `src/cli/set_relations.cpp` |
| RAM residence | a **dynamic** budget from live available RAM | `src/cli/vdisk_config.cpp` |

**F6. The cascade limit is four literals and they already disagree.** The scan
limit is done properly: `g_scan_limit = 500000` (`src/cli/set_relations.cpp:73`),
settable through `REL SCANLIMIT`, floored at 1, and when it bites it **says so**
once per latch cycle -- *"REL: scan limit (N) reached; results may be
incomplete."* The depth limit is the opposite. It is a call-site literal with no
named constant:

    src/cli/cmd_rel.cpp:97           max_depth=24
    src/cli/cmd_relations.cpp:495    max_depth=24
    src/cli/rel_enum_engine.cpp:184  max_depth=24
    src/cli/cmd_dbareas.cpp:157      max_depth=64      <-- disagrees

and its enforcement (`set_relations.cpp:913`, `if (depth > max_depth) return;`)
is **silent** -- no note, no latch. So the two limits guarding one traversal
have opposite honesty, and the answer to "what is the cascade limit" is *24,
unless you came through DBAREAS*.

Consequence for this ticket: a drawn schema graph cannot say "adopt the
built-in cascade limit", because there is not one. **The GUI must not ship its
own fifth number.** Name it once beside `max_areas` in the generated capacity
authority, reconcile 24 vs 64 as a ruling, and give depth the truncation
announcement scan already has. A silently truncated graph is a picture that
looks complete and is not.

**F7. The RAM budget computes and reports; it does not refuse.** Layer 1 is
real and well built -- `recommended_budget_bytes()` (`src/cli/vdisk_config.cpp:182`)
reads physical AND available RAM at run time and prefers available, Auto takes
25% of it, floor/ceil clamp applies even to explicit overrides, and a host
hardcap of half physical RAM is applied **last**, so an admin's `size_mb`
cannot get past it.

Layer 2 is declared, not wired. The high-water check lives inside the VDISK
**report** (`src/cli/cmd_vdisk.cpp:216-228`) and only when `bin/vdisk.ini` is
present; `warn_pct` prints a warning, and **`on_full` is printed and never
acted on** -- `OnFull::Fail` and `OnFull::Spill` are parsed, named and
displayed, and nothing on any write path consults them
(`src/xbase/ramfs.cpp` has `used_bytes()` and no budget comparison). A message
can read `on_full=fail` while nothing fails.

This is recorded, not hidden: the MINIDB record already states *"No size
governance yet ... EST_HYD_B and the vdisk Layer-2 budget are the chartered
seams."* The measurement confirms it, and finds the seam unused: **`EST_HYD_B`
is blank on all 106 catalog rows while `SIZE_B` is populated on all 106.**

Consequence for this ticket: the browser knows a container's `SIZE_B` before it
hydrates and `recommended_budget_bytes()` is one call, so the size refusal is
small and belongs beside the co-residency refusal -- see G6.

**F8. `MAX_AREA` is an `int` and nothing guards the narrowing.** `xbase.hpp:43`
casts to `int` while `build_vectors.hpp` asserts only
`max_areas <= uint32_t::max()`, leaving a two-fold window in which the build
vector permits a value the cast silently narrows. AIF-078 filed this as D3;
confirmed still open. The same header already solves the identical hazard one
field over -- `recordLength()` returns `-1` rather than saturating, precisely so
a 32-bit consumer cannot act on the wrong record. Area numbers never got that
treatment, and a GUI that stores a slot in an `int` inherits the defect at the
presentation layer.

## 6. Gates

- **G1.** The `WS` column shows `DEFAULT` for every area in a classic
  single-workspace session, and every existing script behaves identically.
  *A regression that passes because nothing changed is the point.*
- **G2.** Two workspaces holding a same-named table render as two rows with
  different `WS` values -- and selecting either reaches the right one. This
  gate cannot pass before the registry lands; it is the GUI's acceptance of it.
- **G3.** The schema graph draws `ON key TO childkey` on at least one edge.
  Fixture: any CASCADE posture. *If it renders only `ON`, it is wrong for 17%
  of the corpus.*
- **G4.** A RAM-resident workspace is visually distinguishable from a
  disk-resident one without reading a path.
- **G5.** The projection tables of section 4, if built, regenerate from the
  posture and byte-compare. A projection nothing re-derives is an orphan.
- **G6.** A hydrate whose `SIZE_B` would push RAM past the live budget is
  **refused by name**, with used, budget and container size all stated. This is
  the first consumer of Layer 1 as a control rather than a report, and the
  first writer of `EST_HYD_B`.
- **G7.** The Tables page renders in bounded time with `DOTTALK_MAX_AREAS`
  raised well above this build's default. *A grid that enumerates slots fails
  this gate by construction, which is the point of having it.*

---

## 7. Open for the steward

- **T1.** Claim a number, or run this as a GUI slice under AIF-070? It is
  presentation over another lane's model, which argues for a slice; it also has
  its own gates, which argues for a number.
- **T2.** Section 4: projection-not-source -- accept? It is the only shape I can
  find that gives the GUI a relational map without creating the second registry
  the MINIDB record forbids.
- **T3.** F4: `RECALL ALL` already means all RECORDS, not all areas. Do you
  want (a) `RECALL`/`DELETE` left alone as single-area record-scope verbs, with
  the workspace ruling covering only `COMMIT`/`ROLLBACK`; or (b) a genuinely new
  `RECALL GLOBAL` that mass-undeletes across areas? I recommend (a), and if (b)
  is wanted it should be gated like a destructive verb -- CONFIRM, and a count
  reported before it acts.
- **T4.** F2: AIF-108's recursion block is stale. Whose correction is that --
  mine to file, or the challenge lane's to make?
