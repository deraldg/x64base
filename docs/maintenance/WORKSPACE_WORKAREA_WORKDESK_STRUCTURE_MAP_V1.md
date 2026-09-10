---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260910-COWORK-201
  recorded_at_utc: 2026-09-10T20:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260910-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 95096c507
  authorization:
    requested_by: steward (member.derald), in-session 2026-09-10 -- "Nowhere that
      I know of do we have the structures of workdesk / workspaces / workarea,
      and how they interact together. So much is new that it is not in the ai
      portal yet. take a look at update the ai portal with our work, the files,
      etc."
  report:
    path: docs/maintenance/WORKSPACE_WORKAREA_WORKDESK_STRUCTURE_MAP_V1.md
    kind: structure-map
---

# Workspace / Work Area / Workdesk -- structure map V1

Status: **review-needed.** Evidence class: **source-defined** throughout, with
the runtime readings marked where they are runtime-proven.
Owner: member.derald. Author: member.ai.claude.cowork.
Date: 2026-09-10. Baseline `95096c507`.

---

## 0. Why this document exists, and what it is NOT

**The record is thick and it is scattered.** Twenty-seven documents under
`docs/maintenance` carry workspace material -- rulings (R128, R129, R131),
designs, staged plans, findings, closeouts. Every one of them answers *one
question*. None of them answers **what the three objects are and how they fit
together**, and two of the three levels have no document at all: `WorkArea` /
`WorkAreaSet` and the WORKDESK verb are undocumented outside their own headers.

This is that map. It is deliberately THIN where the record is already thick --
the rulings are cited and routed to, not restated -- and THICK where nothing
exists.

**It is not a ruling.** Nothing here decides anything. Where a question is
open, section 8 says so and names it.

**It is not a manual.** Command syntax lives in each verb's `@dottalk.usage`
block and in HELP. This describes the MODEL.

---

## 1. The three levels, in one picture

```text
   THE DESK          cli::workdesk::Desk            one SESSION's whole picture
      |              include/cli/cmd_workdesk.hpp   READ-ONLY. Owns nothing.
      |              A JOIN of the two below.
      |
      +-- workspaces (ascending by handle; DEFAULT first)
              |
   A WORKSPACE       xbase::workspace::Entry        a NAMED GROUP of work areas
      |              include/xbase/workspace_membership.hpp
      |              name, members, parent, ws_id, three path roots
      |
      +-- members (engine slot numbers)
              |
   A WORK AREA       xbase::DbArea                  one OPEN TABLE
                     wrapped by workareas::WorkArea (src/cli/workareas.hpp)
                     alias, filename, cursor, order state
```

Read it downward as containment and upward as ownership:

| level | the object | the collective | who owns it |
|---|---|---|---|
| area | `xbase::DbArea` | `workareas::WorkAreaSet` -- FLAT, `MAX_AREA` slots, **no workspace dimension** | `xbase::XBaseEngine` |
| workspace | `xbase::workspace::Entry` | `xbase::workspace::WorkspaceTable` | the table itself; one process-wide instance via `default_table()` |
| desk | `cli::workdesk::WorkspaceView` | `cli::workdesk::Desk` | **nobody** -- it is a value, computed on demand |

**The owner's governing sentence, 2026-08-22:** *"Multiple workspaces is just a
workspace of workspaces of areas."* Recursive containment: a workspace has
members; a member is an area (leaf) or another workspace (node).

---

## 2. Level 1 -- THE WORK AREA

### 2.1 What it is

An engine slot holding one open table. The engine owns the lifetime;
`src/cli/workareas.hpp` is a thin convenience wrapper and says so in its own
boundary line: *"Ownership stays in xbase::XBaseEngine."*

`workareas::WorkAreaSet` binds `MAX_AREA` slots to one engine and rebinds
lazily if the engine pointer changes. **It is FLAT BY DESIGN.** It has no idea
what a workspace is. Anything that needs ownership asks level 3.

### 2.2 The three names of an open table, which are three different strings

This is the single most confusable part of the model, and it produced a live
defect on 2026-09-11.

| accessor | what it returns | example |
|---|---|---|
| `DbArea::name()` == `logicalName()` == `_logical_name` | **THE ALIAS.** What this INSTANCE answers to. `USE` may have derived it as `<stem>2`. | `STUDENTS2` |
| `DbArea::filename()` | **THE FILE.** Absolute path. | `D:\...\dbf\x32\STUDENTS.dbf` |
| `DbArea::dbfBasename()` | the stem | `STUDENTS` |

The wrapper exposes the first two as `WorkArea::label()`
(`src/cli/workareas.hpp:76`) and `WorkArea::file_name()` (`:91`), and the
header now carries the instruction **"They must not collapse back into one
function"** -- because until 2026-09-11 `file_name()` returned the ALIAS, and
`cmd_wsreport.cpp` printed it under the literal column heading `FILE`. With two
workspaces holding different files that share a basename, that report answered
"which file" with a string both of them shared. Twelve such pairs were measured
in one session across an x64 and an x32 workspace.

### 2.3 `occupied_desc()` -- a contract that outlived its implementation

`workareas::occupied_desc()` renders which engine slots are open, as runs:
`{}` / `{5}` / `{0..16}` / `{0..19,50..54}`. Eight call sites in four verbs
(STATUS, GPS, AREA, WSREPORT).

The four-example contract is **declared** in
`src/workspace/workarea_utils.hpp:25-29`; the **definition** moved inline to
`src/cli/workareas.hpp` and left the documentation behind
(`src/workspace/workarea_utils.cpp:15` records the move). The implementation
that inherited the name did not inherit the spec: it printed
`{front..back}` -- a RANGE over a SET -- so open slots `{0,3}` rendered
`{0..3}`, four areas claimed where two were open. Repaired 2026-09-11 against
those four lines.

**It needed no second workspace to be wrong.** `USE <t> IN 3` with area 0 open
produces exactly that arrangement, which is what USE_ARGS U_T4 sets up on
purpose. Two workspaces only made it routine.

It is **still flat**: `{0..12,13..25}` says two runs, not two workspaces.

---

## 3. Level 2 -- THE WORKSPACE

### 3.1 What it is

`xbase::workspace::Entry` (`include/xbase/workspace_membership.hpp:125`):

```cpp
struct Entry {
    std::string               name;
    std::vector<std::int32_t> members;   // engine slots
    std::uint64_t             parent{0}; // 0 = a ROOT, not "no workspace"
    std::uint64_t             ws_id{0};  // durable identity; 0 legal ONLY for DEFAULT
    std::string dbf_root, idx_root, lmdb_root;   // R131
};
```

`DEFAULT` is handle **1** (`:105`) and exists before any command runs. Handle
**0** is reserved for "no such workspace / no parent", which is why
`find_by_name_ci()` can return 0 as a failure sentinel.

### 3.2 Runtime state, NOT the catalog

The header states the split in its own words: **the workspace CATALOG
(`WORKSPACES.dbf`) is the persistence authority** -- `WS_ID` allocates
identity, `WS_NAME` is the key, a saved posture's AREA lines are the child list
AT REST. None of that answers *which areas are open in which workspace RIGHT
NOW*, and a workspace can be open having never been saved. That is what this
table is.

`ws_id` and the three roots are **STAMPS, not lookups**. R1 of the identity
ladder says derivation runs DOWNWARD ONLY: the allocator lives CLI-side with
the catalog, and this header never reaches up to it. *A workspace knows its
WS_ID and its roots because it was TOLD; it cannot go and find out.*

### 3.3 Where membership is maintained, and why it is there

`DbArea::open()` and `DbArea::close()` are **the only two points in the tree
where an area joins or leaves a workspace**, and the engine already maintains
`_ws_handle` at exactly those two points. `DbArea::open()` is reached from
EIGHT distinct call sites in `src/cli` alone (cmd_use, cmd_workspace x3,
cmd_create, cmd_copy, cmd_ddl, cmd_autodbf, cmd_refresh) -- so stamping from
the CLI would need eight edits and would silently skip the ninth.

Registering at the choke point the engine already owns **cannot be skipped**.
It is deliberately NOT a callback. The membership header cites a cursor_hook header
as the house's cautionary example -- a hook whose `notify()` has zero call
sites, on whose strength the manual fallback was deleted (AIF-120 R117). **That
citation could not be resolved on 2026-09-10**: no `cursor_hook.hpp` exists
under the include tree in any of the three places the header's spelling could
mean, and that spelling -- a parent-relative form naming a cursor_hook header
under xbase -- resolves to nothing this tree contains. The literal string is
left out of this document ON PURPOSE: writing it here makes the cited-paths
gate chase a file that does not exist and report the absence against this
report rather than against the header that made the claim.
The ARGUMENT stands on its own -- a plain value the engine reads cannot fail
the way an uninstalled callback can -- but the example is currently
unverifiable and is recorded here as such rather than repeated as fact.

### 3.4 Three numbering systems, and which are addresses

| number | base | what it is | where |
|---|---|---|---|
| **engine slot** | 0 | an ADDRESS into the flat `MAX_AREA` array | `WorkArea::slot()` |
| **workspace-local slot** | 0 | an ADDRESS -- position within one workspace's members | return of `join()` (`:505`) |
| **handle** | 1 (DEFAULT) | a KEY -- the runtime twin of the catalog's `WS_ID` | `Entry` map key |

Local slots were rebased to 0 by owner ruling 2026-08-22 (*"0 based costs us
nothing to maintain forward in workspaces too"*), and it was free because
`DbArea::wsLocalSlot()` had **zero readers** at the time. `join()`'s failure
sentinel is `-1` and survived the rebase **precisely because it is negative**:
had it been 0, the first valid slot and "no such workspace" would now be the
same value.

`leave()` frees a local slot rather than shifting the survivors, **because
shifting would silently re-address live members** (`:539`).

**R6 (D10 sec 2a):** an absent value must not be representable in the space of
present ones. A negative engine slot means "this DbArea has no slot at all" and
`-1` is ALSO the members array's free-entry marker -- two absences sharing one
value. Before it was refused, roughly **47** slotless DbAreas in the tree
"joined" as silent no-ops, each reporting a local slot it did not hold.

### 3.5 The rules the table enforces, in one place

- `destroy()` (`:463`) refuses DEFAULT, refuses a workspace with members,
  refuses a parent with children, and re-points `current` to DEFAULT if it was
  destroying the current one.
- `set_ws_id()` refuses to overwrite a different non-zero id -- stamped once.
- `would_cycle()` refuses self-parenting and any cycle, with
  `kMaxWorkspaceDepth` (vectored in `config/build_vectors.cmake`, currently 32)
  as a backstop that ANNOUNCES when it fires.
- **DESIGN CONSTRAINT D3** (`:81`): *no operation here is O(MAX_AREA)*. Every
  walk is bounded by the members of ONE workspace. The owner's argument:
  MAX_AREA is 512 for testing and the real ceiling is not 512 -- *"can you
  imagine how long it would take to give you a dotscript results of a 10
  trillion max_area pass"*.

---

## 4. Level 3 -- THE WORKDESK

### 4.1 What it is, and why it had to exist

New this week. `include/cli/cmd_workdesk.hpp` + `src/cli/cmd_workdesk.cpp`.

**The two-level truth already existed and was already reachable. NOTHING
JOINED THEM.** `cmd_workspace.cpp` did the join inline and printed it, WSREPORT
did its own, and the ambiguity ledger built a third -- `cli::AmbiguityHit`
carries `ws_handles` parallel to `engine_slots`, which is this same pairing,
reinvented because there was nowhere to get it.

**Three consumers, three private joins, console text as the only output.** That
is why nothing outside those three could report at the workspace level: not a
silent engine, an **unpublished composition**.

**It is not a desktop.** No windows, no focus, no z-order. "Desk" is the
collective noun for the workspaces a session has open, the way `WorkAreaSet` is
the collective for areas.

### 4.2 The observe/render split

`Desk observe()` (`cmd_workdesk.cpp:91`) answers **WHAT IS TRUE**.
`void render(const Desk&, std::ostream&)` (`:209`) answers **HOW IT READS**.

They are separate on purpose. A caller wanting facts takes the `Desk` and never
calls `render`. `render` writes only to the stream it is handed -- it does not
reach for `std::cout`, and it does not know whether that stream is a console,
an alternate capture, or a string. What must not happen again is a fourth
caller doing its own walk because rendering and observing were welded together
and it only wanted one of them.

### 4.3 Two things `observe()` settles that every caller otherwise got wrong

1. **ORDER.** `handles()` walks a `std::unordered_map`, so its order is
   UNSPECIFIED and may differ between two runs of the same session shape. Any
   report built straight on it is non-deterministic and cannot be asserted on.
   `observe()` sorts by handle ascending, which also puts DEFAULT (handle 1)
   first, always.

2. **INVARIANT I1.** `owner_of_slot()` returns 0 when no workspace claims a
   slot. I1 says an area belongs to exactly ONE workspace and there is NO NULL,
   so for an OPEN area that answer is impossible. `observe()` collects those in
   `orphan_open_slots` -- walking **every engine slot**, not the membership
   lists, because the whole point is to find a slot the membership lists
   FORGOT. **It REPORTS the violation; it never repairs one.**

### 4.4 `NameFanout` -- one NAME, more than one open area

Reported as a fact, never as an error. It is a NAME COLLISION, not a second
handle on one file, and the difference cost this file's own regression spec two
red runs to learn.

**`USE <t> AGAIN` is the ONE route that CANNOT produce it.** `cmd_use.cpp`
resolves the alias BEFORE it touches the area --
`find_open_area_by_alias()` then `derive_distinct_alias()` -- renames the second
instance `STUDENTS` -> `STUDENTS2` and announces the rename. Two handles, two
NAMES. The fanout pass keys on `DbArea::name()`, which IS the logical name, so
on that path it can never fire, by construction.

What DOES land there is **two DIFFERENT files sharing a basename**, opened by a
route that skips that arm: `WORKSPACE OPEN`/`ADD`/`LOAD`, both schema restores,
`CREATE`, `AUTODBF`, `x64_apply_name_metadata`. See
`claude/FACT_ONLY_CMD_USE_UNIQUIFIES_A_LOGICAL_NAME.md` for the full census.

> **KNOWN DEFECT, 2026-09-10, NOT YET REPAIRED.** The struct comment in
> `include/cli/cmd_workdesk.hpp:100-102` still says the fanout is *"SUPPORTED
> -- `USE <t> AGAIN` asks for it on purpose"*, which is the exact inversion of
> the truth above. The corrected passage landed in the **.cpp** (`src/cli/cmd_workdesk.cpp:175-180`)
> and not in the **.hpp**. One struct, two comments, opposite claims; the
> header is the one a reader meets first. See section 8.

Measured live 2026-09-10, `do x64` then `do x32` in one session: **twelve
names, twenty-four areas, two directories, zero uses of `AGAIN`.**

---

## 5. How the three interact -- the five rules that actually govern

### R-A. SWITCH THEN OPEN. Never open then assign.

**An area joins whichever workspace is CURRENT when it is OPENED.** There is no
verb that moves an open area between workspaces. The sanctioned sequence is
`WORKSPACE NEW` / `SWITCH` / `SET PATH` / open.

### R-B. A workspace OWNS ITS ENVIRONMENT (R131).

DBF / INDEXES / LMDB roots are stamped per workspace; `WORKSPACE SWITCH`
restores them and **ANNOUNCES what it moves**. `SET PATH <slot> <v> IN <ws>`
binds another workspace's root without touching the session's own slots.

**Why three strings and not a workspace-aware resolver** (R131 sec 11.2):
`dottalk::paths::get_slot` has **102 CALL SITES** across thirty-odd files, and
most are not workspace code at all -- bbs_store, cmd_smtp, cmd_drawio,
edu_cobol, fn_string. Handing a workspace to code that has none is a rewrite,
not a design option. The global stays the single resolution authority and
SWITCH re-points it; all 102 readers are untouched.

**Q2 is INHERIT:** a workspace is stamped AT CREATION from whatever is current,
so a workspace whose environment is a question with no answer never exists.
EMPTY therefore means only NOT STAMPED YET, true of exactly one entry --
DEFAULT, stamped lazily from the INIT slots the first time anything asks.

### R-C. An unqualified name resolves in the CURRENT workspace. The qualified form is `WS:TABLE`.

- **Q8** (closed 2026-08-27, owner-accepted): unqualified names resolve to the
  current workspace's member; qualified form `SALES:STUDENTS.FNAME`.
- **R134** (2026-08-31, owner): *the alias is the path, COMPOSED not stored*.
  The alias namespace is GLOBAL, the alias is `WS:TABLE`, unique by
  construction. `logicalName()` keeps returning the bare name; the qualified
  form is DERIVED.
- Owner ruling 2026-09-10 extended the same scoping from `SELECT` to `USE`:
  *"an unqualified table name should open/select in the current workspace
  always -- then most legacy scripts will work by default."*
- A bracket spelling (`ws[3]:students`) was considered and **WITHDRAWN**: it
  dies in the shipped parser and would be a third address spelling beside a
  working one.

**Two resolvers answer the same question differently, and that is I1.3a:**

| resolver | scope | behaviour |
|---|---|---|
| `cli::find_open_area_in_workspace_ci()` (`src/cli/workarea_util.cpp:171`) | SCOPED to a workspace | first-wins within it, records an ambiguity-ledger entry, does not refuse |
| `find_open_area_by_name_ci()` (`:153`) | UNSCOPED | lowest matching slot, **no diagnostic** |
| `build_open_area_index_ci()` (`:69`) | UNSCOPED | `emplace`, so likewise first-wins |

SQL resolves through the unscoped one. **SQL does not open tables at all**; it
is a pure victim of duplicates created elsewhere.

### R-D. CLOSE is scoped; RECURSION decides whether it descends.

A bare `WORKSPACE CLOSE` is scoped to the CURRENT workspace. With one workspace
open this is byte-identical to the old sweep; with two it is the difference
between closing yours and closing someone else's.

`SET RECURSION ON|OFF` gates whether an operation DESCENDS, not whether nesting
may exist -- owner ruling: *"even with OFF we still allow multiple workspaces,
just parallel."*

### R-E. The duplicate-open guard is GLOBAL, in all three verbs that have one.

| verb | site | what it asks |
|---|---|---|
| `WORKSPACE OPEN <dir>` | `src/cli/cmd_workspace.cpp:1509` | is this FILE open ANYWHERE? then skip it |
| `WORKSPACE ADD <file>` | `src/cli/cmd_workspace.cpp:5947` | is this FILE open ANYWHERE? then SELECT that area and return |
| `USE` | `src/cli/cmd_use.cpp` | alias uniquing was scoped 2026-09-10; the OPEN guard is still global |

**All three were written when there was one workspace**, so "anywhere" and
"here" were the same question. They are not the same question now. This is the
open ruling in section 8 -- and it has already produced one false green: see
`claude/FINDING_FIRST_WINS_WAS_COMPLETING_THREE_ARMS_ADDRESSES_FOR_THEM.md`.

---

## 6. Reading the system at runtime -- which verb answers what

| question | verb | level it reads |
|---|---|---|
| which workspaces exist, who parents whom, who holds which slots | `WORKSPACE REGISTRY` | 2 |
| the whole desk: workspaces + areas + roots + orphans + name fanout | `WORKDESK` | 3 |
| where am I standing right now | `GPS` | 1 + 2 |
| which engine slots are occupied | `STATUS`, `AREA` | 1 |
| what is in the durable catalog | `WORKSPACE CATALOG` | persistence |

`STATUS`'s `Workspaces` block and `Work Areas` block are the two levels printed
one above the other; the `Work Areas` heading is level 1 and carries
`occupied_desc()`.

---

## 7. Where the rest of the record lives -- routing table

Do not restate these. Go to them.

| subject | document |
|---|---|
| the staged plan, decisions D1-D10, amendments | `docs/maintenance/AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md` |
| durable identity: WS_ID, DESTROY vs DELETE, high-water mark | `docs/maintenance/AIF078_D10_WORKSPACE_IDENTITY_LADDER_RULING_V1.md` |
| scoped close and the recursion flag | `docs/maintenance/AIF078_SCOPED_CLOSE_RECURSION_RULING_V1.md` |
| a workspace owns its environment (R131) | `docs/maintenance/R131_WORKSPACE_ENVIRONMENT_RULING_V1.md` |
| cursor semantics across workspaces (R129) | `docs/maintenance/R129_WORKSPACE_CURSOR_RULING_V1.md` |
| relations are workspace-blind | `docs/maintenance/AIF137_FINDING_RELATION_PARENT_IS_WORKSPACE_BLIND_V1.md` |
| four ladders resolve one workspace name | `docs/maintenance/AIF145_FINDING_FOUR_LADDERS_RESOLVE_ONE_WORKSPACE_NAME_V1.md` |
| name shadowing, qualifier namespace depth | `docs/maintenance/AIF120_WORKSPACE_NAME_SHADOWING_REPORT_V1.md`, `docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md` |
| MINIDB / memo-resident containers | `docs/maintenance/RAM_MINIDB_MEMO_WORKSPACE_OPERATIONS_V1.md`, `docs/maintenance/WORKSPACE_MEMO_RESIDENCE_PLAN_V1.md` |
| AIF-070 / AIF-078 reconciliation | `docs/maintenance/WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md` |
| GUI-side workspace architecture | `docs/maintenance/GUI_WORKSPACE_ARCHITECTURE_DESIGN_V1.md` |
| which openers can double a logical name (census) | project doc `claude/FACT_ONLY_CMD_USE_UNIQUIFIES_A_LOGICAL_NAME.md` |
| what scoping SELECT exposed in the regression corpus | project doc `claude/FINDING_FIRST_WINS_WAS_COMPLETING_THREE_ARMS_ADDRESSES_FOR_THEM.md` |
| metadata reports that predate the workspace model | project doc `claude/SCAN_20260910_METADATA_REPORTS_UNDER_THE_MULTI_WORKSPACE_MODEL.md` |

**Regression coverage of this model**, by spec name in
`src/cli/cmd_regression.cpp`: `WORKSPACE_SCOPE`, `WSMULTI`, `WSLADDER`,
`RELSCOPE2`, `MWXSHAKE`, `OPENJOIN`, `WSENV`, `WORKDESK`, `USE_ARGS`,
`NAME_AMBIG`.

---

## 8. What is OPEN, stated rather than implied

1. **Is the duplicate-open guard GLOBAL or PER-WORKSPACE?** Three verbs, one
   question, all three currently global (section 5, R-E). MWXSHAKE's `MWX_T5`
   is annotated as UNPROVEN pending this. The USE half is already an open item
   in its own right: a bare `USE` in ws3 still demands `AGAIN` when DEFAULT
   holds the file.

2. **R131 Q3.** `WORKSPACE OPEN <dir> AS <name>` does NOT stamp roots from the
   directory it opened. `WORKSPACES.dbf` carries `DBF_ROOT` and `IDX_ROOT`
   only, so the LMDB slot has no durable column to be written to at all.

3. **`cmd_workdesk.hpp`'s `NameFanout` comment is false** (section 4.4). A
   correction exists and is proven; it has not been applied to the header.

4. **The eighteen index/order/container display files return ZERO for
   `grep -ic workspace`.** They were written when there was one workspace, so
   "which one" was not a question they could get wrong. Four confirmed
   falsehoods are named in the 2026-09-10 scan and are not yet repaired:
   `cmd_cdx.cpp:145`, `cmd_setorder.cpp:662`, `cmd_setlmdb.cpp:179` and `:243`.

5. **WORKDESK has no HELP entry** -- `[WARN] HELP (1): WORKDESK` on every
   commit. Owner: *"let it mellow."*

---

## 9. Evidence and freshness

Every structural claim above was read off the working tree at `95096c507` on
2026-09-10, not recalled. Line numbers are as measured that day and **will
drift**; the shapes are the durable part, and each citation names the symbol as
well as the line so a moved line is still findable.

The runtime readings in sections 2.2 and 4.4 (twelve doubled names across an
x64 and an x32 workspace) are **runtime-proven** against `do x64` + `do x32` in
one session, `WORKDESK` output, 2026-09-10.

Ships **review-needed**. The author does not self-approve.
