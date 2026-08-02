---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260730-001
  recorded_at_utc: 2026-07-30T22:24:18Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 349227c18e2f8781df0f576804bf962ff44797a3
  authorization:
    requested_by: maintainer
    scope: >
      Investigate whether a lane exists for multiple workspaces; determine the
      cost/benefit of adding a workspace alias identifier above the table alias
      for SQL relations; redefine the MAX_AREA cap. Owner directed the lane be
      opened and the findings published to curation.
  report:
    path: docs/maintenance/WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md
    kind: lane_charter
---

# Workspace Qualifier Namespace Depth -- Lane V1 (AIF-078)

**Lane:** `AIF-078` · `workspace-qualifier-namespace-depth`
**Status:** `review-needed` -- decision analysis; **no engine source changed; zero runtime evidence**
**Owner:** `member.derald` · **Steward:** `member.ai.claude.cowork`
**Claim:** `coordination/aif/AIF-078.claim` (run `WORKSPACE-QUALIFIER-20260730`)
**Bears on:** `AIF-074` (sqlsel-pldc, `active_development`), phase **P4.1**
**Companions:** `docs/maintenance/COST_BENEFIT_GATE_DOCTRINE_V1.md`; reference design at `src/AIPortal/sessions/2026-07-30_cowork_workspace_qualifier/`

---

## 0. Origin and the question actually at issue

The maintainer asked whether a lane was open for multiple workspaces, and if not to open one -- the stated need being *"a low cost object above the table alias identifier for a workspace alias identifier, for SQL relations between multiple workspaces,"* plus a top-level pointer over all workspaces.

**No such lane was open in the claim ledger** -- but see §0a: prior art exists, stranded. And the investigation found the question was mis-scoped, in the maintainer's favour.

`docs/maintenance/SQLSEL_PLDC_LANE_V1.md:112`, phase **P4.1**, verbatim:

> "INNER JOIN, two tables, one equi-key. **Adds table ALIASES (`FROM STUDENTS S`) and QUALIFIED column names (`S.LNAME`), which every later slice needs.** Nested loop, inner side SCANNED -- correctness before speed | G4a (SQLite oracle, incl. row multiplication)"

Table-reference qualification is already scheduled, already owned by AIF-074's P4.1, and the charter already states every later slice depends on it. The live question is therefore narrower and far cheaper:

> **When P4.1 authors the qualifier, is its namespace one level deep (table alias) or two (workspace + table alias)?**

That is a design decision on a grammar not yet written. It is not a feature request. This lane exists to force that decision **before** P4.1 rather than to build multi-workspace addressing.

---

## 0a. Prior art -- AIF-070, stranded (found late; correction to this lane's own opening claim)

**There is prior design work on concurrent named workspaces, and this session did not find it until after the lane was opened.** It surfaced only when `audit_trail.py` was run for verification and reported advisory findings against an intake package nobody had cited.

`docs/maintenance/external_ai_intake/virtual_workspaces_memo_resident_2026-07-28/` -- **Virtual Workspaces & Memo-Resident Mini-Databases**, an external design intake from `member.ai.grok.xai` (`AIPR-20260728-GROK-002`), with a local assessment (`ASSESSMENT_LOCAL_WORKBENCH.md`) that drafted an intake row for **AIF-070**.

State, verified 2026-07-30:

- `coordination/aif/AIF-070.claim` -- **does not exist.**
- `AIF-070` in `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- **zero rows.**
- `AIF-070` referenced anywhere under `docs/`, `labtalk/`, `coordination/` -- **zero hits.**

The only trace is the AIF-071 intake row's aside: *"AIF-070 deliberately left free for the Grok Virtual Workspaces / Memo-Resident lane."* The number is reserved by convention and unallocated in the ledger. The design is discoverable only by already knowing it exists.

**Overlap with this lane.** The Grok package proposes concurrent/named workspaces, per-area `kind`, scoped `WORKSPACE SAVE`, and an **extended DTSHEMA "illustrated v4"**. The reference design filed under this lane (`src/AIPortal/sessions/2026-07-30_cowork_workspace_qualifier/`) independently proposed **`DTSHEMA 4`** with a per-area `ws=` field, having never seen the Grok package. Convergent design, arrived at twice, neither aware of the other.

**Divergence, and why this lane does not simply defer to it.** AIF-070 is about *what a workspace is* -- named, concurrent, memo-resident, hydratable, area-budgeted. This lane is about *how a name resolves* once more than one workspace can exist, and it is on AIF-074's clock in a way AIF-070 is not. They are complementary: AIF-070 owns the container, AIF-078 owns the qualifier. **Neither should be built without the other's constraints in hand.**

**Also relevant:** the Grok package's source table records *"Confirmed Q2 (workspace addressability) still open"* from the AI Portal / agent-sync pages -- i.e. workspace addressability was already a tracked open question on the public portal, and this session re-derived it from source without knowing that.

**Governance reading.** This is a recurrence of the exact failure AIF-071 closed (*"a received Grok change package took several failed full-tree searches to locate"*). The landing zone is now indexed and the validator scans it advisorily, so the package was findable -- but nothing *pointed* to it from the intake queue, from the lane ledger, or from any AIF number, because the row was drafted and never committed. **A design that is registered nowhere is a design that will be done twice.** It was.

**Owed:** allocate AIF-070 properly, commit its intake row, and reconcile it with this lane before either proceeds. Recorded rather than acted on, because claiming another agent's lane is a maintainer call.

**Update, same session.** `coordination/aif/AIF-070.claim` did not exist at 22:23:46Z (when AIF-078 was claimed) and **did exist at 22:36:42Z** -- `member.ai.grok.xai`, run `AIPR-20260728-GROK-002`, lane `workspace.virtual_and_memo_resident`. Claimed concurrently on the shared tree while this lane doc was being written. The allocation half of the gap is therefore closed; **the intake row is still owed** -- `aif_collision_gate.py` reports `advisory: claim(s) with no intake row: AIF-068, AIF-070`. Reconciliation between AIF-070 and AIF-078 remains open and is now a two-lane, two-steward conversation.

---

## 1. As-is (source-evidenced, verified 2026-07-30 against `D:\code\ccode`)

```
[implicit, unnamed, exactly one]  XBaseEngine            shell.cpp:527
  └─ slot 0..MAX_AREA-1 (int)     _areas[MAX_AREA]       xbase.hpp:494
       └─ DbArea                                          xbase.hpp:139
            └─ alias == logicalName() == DBF file stem     cmd_use.cpp:321-322
                 └─ field (bare name, no qualifier)        expr/ast.hpp:48
```

- `XBaseEngine eng;` at `src/cli/shell.cpp:527` is the **only** instantiation in the tree. `g_shell_engine` (`:328-329`), `relations_api::attach_engine(&eng)` (`:532`), and `workareas::global()` all resolve through it.
- `DbArea` has **no** alias member, **no** slot member, **no** owner back-pointer. `name()` returns `_logical_name`; the two accessors are the same string.
- `WORKSPACE` is **not** a namespace. It is the collective noun for all open slots plus the relation graph, and a save/load file format. `WORKSPACE LOAD` closes everything then restores (`cmd_workspace.cpp:1499`) -- swap semantics, never co-residency.
- Qualified names are **two parts maximum**. `sqlsel_statement.cpp:89-99` `is_bare_column()` rejects >1 dot, and line 94 is the **only** dot-count check in the tree.
- **searched-and-absent:** no `WorkspaceManager` / `WorkspaceRegistry` / `workspace_id` / `active_workspace`; no `ATTACH`/`MOUNT`/`LINK`; no cross-workspace, foreign, or remote table concept in the native engine (the three `foreign_key` hits in `src/edu/edu_erp.cpp:254,686,714` are SQLite pragmas). No workspace-qualified table reference anywhere in source, in the AIF-074 charter, in any ruling, or in `include/sql_ref.hpp`.

### 1a. The written-but-unwired foundation

`include/reference/data_address.hpp:104-137` already defines the full five-level address -- `WorkspaceIdentity{logical_name, profile_path, session_id}` -> `DbAreaIdentity{slot, alias, generation}` -> `TableIdentity` -> `RecordSelector` -> `FieldIdentity` + `vector<RelationStep>`. `diagnostic_text()` (`src/reference/data_address.cpp:111-167`) emits `MCC.#2.STUDENTS.CURRENT->ENROLL.RECNO(9).GRADE` and carries a `"CURRENT_WORKSPACE"` sentinel at `:114`. `include/reference/qualified_reference.hpp:73` is a real unlimited-depth dotted parser with roots `Bare | Named | AreaSlot(#n) | Variable($v)`.

It is dead-ended by design. `src/CMakeLists.txt:46-49`, verbatim: *"Compile-only foundation; no DbArea/tuple/expression/array integration yet. Built as an isolated static lib (like xexpr)..."* Sole consumer in the tree: `src/tests/test_pdlc_foundation_smoke.cpp`.

**The object the maintainer asked for is already written. What is missing is ownership and scope, not the type.**

---

## 2. The cap -- corrected (maintainer ruling, 2026-07-30)

The maintainer ruled that 512 is arbitrary and `max_areas` is a real vector. **Confirmed, and an earlier draft of this analysis was wrong to ration it.** `config/build_vectors.cmake:8-12`, verbatim:

> "GATE #1 (non-negotiable): defaults preserve current COMPILED behavior. In particular MAX_AREAS = 512, matching the hard-coded `xbase::MAX_AREA` that the engine actually used..."

512 is a compatibility default under AIF-044, not an engineering limit. Bounds: `build_vectors.cmake:30-32` checks only `LESS 1`; there is **no upper bound at all**.

### 2a. Measured cost (compiled probe, this tree's generated vectors)

> **Framing corrected 2026-08-01 (maintainer): x64base is CROSS-PLATFORM. MSVC is not "the" toolchain and g++ is not a stand-in for it.** An earlier draft of this section called the libstdc++ figures "runtime-evidenced for the wrong compiler" and treated an MSVC number as the correction. That is wrong for a portable engine. The cap table is **per-toolchain**, both rows are real, and where they differ the difference is a finding rather than an error. The binding constraint is the **worst case across supported platforms** -- which for the stack column is Windows/MSVC (1 MB default main thread) and not Linux (8 MB), so the platform that limits the cap is not the platform with the largest structures.

**G0 CLOSED 2026-08-01. Both toolchains measured.**

| | g++ / libstdc++ x86-64 | MSVC `_MSC_VER=1944` |
|---|---|---|
| `sizeof(DbArea)` | 1088 | **840** |
| `sizeof(AreaState)` (`table_state.cpp:79-82`) | 176 | **144** |
| `sizeof(XBaseEngine)` | 4104 | 4104 |
| `sizeof(std::fstream)` | 528 | **280** |
| **bytes/slot** all-in | **1296** | **1016** |

`XBaseEngine` matches on both because it is only `MAX_AREA * 8 + 8` -- a pointer array, no layout freedom. The divergence is almost entirely `std::fstream` (528 vs 280), which `DbArea` embeds by value.

| Cap | resident, idle -- gcc | resident, idle -- MSVC | `XBaseEngine` stack frame | relation inner-loop |
|---|---|---|---|---|
| 512 (today) | 0.63 MB | 0.50 MB | 4 KB | 1x |
| 1024 | 1.27 MB | 0.99 MB | 8 KB | 2x |
| **4096** | **5.06 MB** | **3.97 MB** | **32 KB** | **8x** |
| 16384 | 20.25 MB | 15.88 MB | 128 KB | 32x |
| 65536 | 81.00 MB | 63.50 MB | 512 KB | 128x |

**The two axes have different worst cases, and this is the point of measuring both:**

- **Memory binds on Linux** (1296 B/slot, 81 MB at 65536) -- 27% heavier than MSVC.
- **Stack binds on Windows** (1 MB default main thread vs 8 MB on Linux). The frame column is identical on both platforms; only the ceiling it is measured against differs.

**Prediction recorded and WRONG.** Before measuring, this lane stated MSVC "will likely have larger structures" and framed Linux as the memory-comfortable side. The opposite holds: MSVC is **22% smaller per slot**. The reasoning was that MSVC's containers are generally fatter, which is true of `std::string` and `std::multimap` and irrelevant here, because the term that dominates `DbArea` is `std::fstream` -- and libstdc++'s is nearly twice MSVC's. Recorded rather than quietly corrected: it is a clean instance of doctrine rule 2 applied to a portability assumption instead of a constant, and of why the probe existed at all.

**Probe:** `src/tools/g0_slot_cost_probe.cpp`, built through CMake on either platform (`-DDOTTALK_BUILD_SLOT_COST_PROBE=ON`, target `g0_slot_cost_probe`). Transcripts: `labtalk/proofs/runs/20260801_aif078_g0_slot_cost_msvc.txt` and `..._gcc.txt`.

Cost is paid **eagerly and unconditionally** -- `src/xbase/dbf_file.cpp:409-411`:

```cpp
XBaseEngine::XBaseEngine() {
    for (auto& p : _areas) p = std::make_unique<DbArea>();
}
```

There is no lazy path, no free list, no null-until-used branch (searched -- absent). Every slot is constructed whether one table is open or five hundred.

### 2b. Two things gate the cap, and neither is memory

**(i) The engine is a stack local.** `src/cli/shell.cpp:527` -- at 65536 that is a **512 KB frame against MSVC's 1 MB default main-thread stack**, and there is **no `/STACK` linker setting or `LINK_FLAGS` stack override in any CMake file** in the tree. Failure to boot, not slowdown. At 4096 (32 KB) it is a non-issue.

**(ii) There is no reverse map `DbArea*` -> slot.** Nineteen copy-pasted linear scans exist instead (`cmd_replace.cpp:756`, `cmd_delete.cpp:149`, `cmd_recall.cpp:116`, `cmd_calcwrite.cpp:192`, `cmd_commit.cpp:142`, `cmd_rollback.cpp:65`, `cmd_rebuild.cpp:103`, `cmd_reindex.cpp:170`, `cmd_list.cpp:156`, `cmd_smartlist.cpp:371`, `cmd_area.cpp:86`, `cmd_close.cpp:85`, `cmd_dbarea.cpp:89`, `cmd_use.cpp:295`, `cmd_workspace.cpp:329`, `table_buffer.cpp:195,205`, `tabledata.cpp:214`, `dirty_prompt.cpp:108`).

Most are once-per-command and harmless. **One is not** -- `src/cli/set_relations.cpp:171-178`:

```cpp
static int slot_of_area_ptr(const xbase::DbArea* area) {
    const std::size_t n = workareas::count();      // == MAX_AREA, always
    for (std::size_t i = 0; i < n; ++i)
        if (workareas::db(i) == area) return static_cast<int>(i);
    return -1;
}
```

Called from `ScopedEngineSelect`'s constructor (`:182-193`), constructed inside `get_by_index_as_string` (`:300`) -- **once per join field per row compared** -- and inside `goto_first_match`'s record scan (`:365`) -- **once per scanned child record**. Reached from the cursor hook (`shell.cpp:339-348`, registered `:531`), so it fires on ordinary navigation, not only on explicit `REL` commands.

**Relation match cost is `O(MAX_AREA x join_fields x rows_scanned)` today, at 512.** Raising the cap multiplies it linearly.

### 2c. What does *not* gate the cap

- **No on-disk format encodes a slot width.** `DTSHEMA` writes `AREA <n>` as decimal text (`cmd_workspace.cpp:1448-1473`) and range-checks on load (`:1570`), skipping gracefully with `"! Skip AREA out of range"`. `RelationSpec` (`set_relations.hpp:123-135`) carries names only. DBF headers have no area field. `VFPFieldRec::workarea` is a `uint8_t` but is always written 0 (`dbf_create.cpp:359,515`) and is a VFP field-descriptor byte, not an engine slot.
- **No narrow slot type anywhere.** `_current` `int`; `WorkArea::slot0_` `size_t`; `RelationState::parent_slot`/`child_slot` `int`; `TupleColumn::area_slot` `int`.
- **No consumer outside `include/` and `src/cli/`**, plus one line in `src/xbase/dbf_file.cpp`. Nothing in GUI, browser, workspace, or tools.

### 2d. Two missing guards (independent defect)

`config/build_vectors.hpp.in:44-45` asserts `max_areas <= UINT32_MAX`, but `include/xbase.hpp:43` does `static_cast<int>(...)`. **There is no `static_assert(max_areas <= INT_MAX)`.** A cap above 2^31-1 silently yields a negative `MAX_AREA` and every `idx >= MAX_AREA` guard inverts. Combined with the absent CMake upper bound (§2), a settable-and-unguarded vector in a build system whose entire purpose is validated capacity.

### 2e. Cap ruling (proposed)

Measured on both platforms as of G0, so this is priced rather than argued. Ladder per R23:

| Cap | Memory (worst case: gcc) | Stack (worst case: MSVC, 1 MB default) | Relation loop | Verdict |
|---|---|---|---|---|
| **4096** | 5.06 MB | 32 KB = 3% of stack | 8x | **GOOD -- take it now.** No prerequisite. |
| **16384** | 20.25 MB | 128 KB = 13% of stack | 32x | **BETTER.** Both axes comfortable; the 32x relation multiplier is the only real cost, and P1 removes it. |
| 65536 | 81.00 MB | **512 KB = 50% of stack** | 128x | **NOT YET.** Needs `XBaseEngine` off the stack (`shell.cpp:527`; no `/STACK` override anywhere in the build) AND P1. |

Recommendation: **4096 now**, with both missing guards from sec 2d. **16384 becomes the natural target the moment P1 lands**, since P1 is exactly what stops the multiplier mattering. 65536 stays gated on moving the engine off the stack -- 512 KB against a 1 MB default is not a margin, it is a coin flip on someone else's machine.

---

## 3. Where AIF-074 actually is

**Built** (`src/cli/sqlsel_statement.cpp`, P3 closed G3 2026-07-29):

```
SQLSEL SELECT <col>[,<col>...] FROM <table>
       [WHERE <predicate>] [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]
SQLSEL SELECT * FROM <table>
SQLSEL SELECT COUNT(*) FROM <table> [WHERE <predicate>]
```

**There is no AST.** All statement state is function-local in one function, `try_execute_select` (`:142-479`): `select_list`, `table_name`, `where_text`, `order_field`, `order_desc`, `limit_n`, `spec`, `count_star`, `star`. The only struct in the file is `MatchRow{ int64_t recno; std::string key; }` (`:332`) -- a scan result, not a node. **Phase P2 (the `src/sqlsel/` library) has not started.**

**`FROM STUDENTS S` is rejected today**, `sqlsel_statement.cpp:186-190`:

```
SQLSEL: unexpected token 'S' after the table name.
        v1 reads a single table; joins arrive with the join phase.
```

The grammar seat for a qualifier is **empty and explicitly reserved**. It will not stay that way past P4.1.

**Planned** (documentation-tier, `SQLSEL_PLDC_LANE_V1.md:105-122`): P4.0a harness (implemented, **parity RED**), P4.0b evaluator seam (**blocked** on ED-01/ED-02), P4.1 INNER JOIN, P4.2 index-assisted inner, P4.3 LEFT, P4.4 RIGHT/FULL/CROSS, P4.5 DISTINCT + UNION/INTERSECT/EXCEPT, P4.6 GROUP BY/HAVING, P4.7 subqueries, P5 DML + transactions, P6 PLDC ascent. Ruling **R26** (`:48`): full modern relational algebra in scope, owner-accepted as *"ROUGHLY DOUBLES the lane."*

---

## 4. The asymmetry

### 4a. Decided now

| Surface | Cost |
|---|---|
| P4.1 qualifier grammar | **Zero marginal.** The grammar is being authored; one level vs two is a choice at authoring time. |
| SQLSEL statement structs | **Zero.** They do not exist. P2 has not started. |
| `RootSyntax` extension | ~10 lines (`qualified_reference.hpp:11-16`, `qualified_reference.cpp:48-78`). The segment loop is already unlimited-depth. |
| R27 scope clause | One sentence in the charter. |

### 4b. Deferred past P4.7

The qualifier is consumed by: table aliases and qualified columns (P4.1), join `ON` resolution (P4.1), index-assisted inner (P4.2), LEFT (P4.3), RIGHT/FULL/CROSS (P4.4), DISTINCT and set operations (P4.5), GROUP BY/HAVING (P4.6), subqueries (P4.7), DML (P5). Retrofitting a namespace level underneath it means touching each -- **and** because gates G4a--G4g each freeze semantics against a SQLite oracle, re-running every closed gate.

**~3 surfaces now vs ~10 surfaces plus re-gating later.**

### 4c. The R27 wrinkle -- the sharpest argument

Ruling **R27** (`SQLSEL_PLDC_LANE_V1.md:49`):

> "Declared relations are an OPTIMIZATION HINT, never a precondition... **any two OPEN tables** join on any comparable columns with no prior `SET RELATION` and no registry lookup."

With one workspace, "any two open tables" is unambiguous. With multiple workspaces and no scope, **every join site inherits the silent first-match behavior** of `cli::find_open_area_by_name_ci` (`workarea_util.cpp:29-51` -- first hit wins, no ambiguity signal).

Joins are the worst place for that failure, because a wrong resolution does not error: it produces **plausible, well-formed, wrong rows**. A `STUDENTS  JOIN  ENROLL` that silently bound `LAB.STUDENTS` instead of `MCC.STUDENTS` would pass any test that did not already know which workspace was meant.

Adding a scope clause to R27 now is a one-line ruling. Changing it after the join engine ships is a semantics change against closed gates.

### 4d. A live defect found on the way (independent of workspaces)

SQLSEL resolves `table_name` once (`sqlsel_statement.cpp:261`, `find_open_area_by_name_ci`) -- then **stringifies it back** into a tuple spec (`:288` `spec = area_label + ".*"`, `:303` `spec += area_label + "." + c`) and hands it to `build_tuple_from_spec`, which **re-resolves the same name with a different matcher**: `tuple_builder.cpp:127-160` `resolve_slot_by_area_name_all`, matching `workareas::name(i)` **or** `basename_upper(A->name())`.

The two differ in matching rules and, critically, in ambiguity behavior:

- `tuple_builder.cpp:204-215` **detects and reports**: `"ERROR: TUPLE area name '<x>' is ambiguous; matching slots: ... Use #<slot>."`
- `find_open_area_by_name_ci` **silently returns the first match.**

**One query, two resolvers, two semantics.** Any qualifier must survive that round-trip through `tuple_builder.cpp:197`'s split-at-first-dot. This is the fourth instance of the AIF-065 / AIF-066 / AIF-067 shape: *two things that never compare themselves.*

---

## 5. Recommendation -- buy the option, not the feature

Multi-workspace addressing as a runtime capability (`WORKSPACE NEW/USE/DROP`, cross-workspace `REL`, the all-workspaces pointer) is **not yet justified**. The only prior mention (`PSEUDO_CHAT_RETURN_LANE_V1.md:151-164`) records it as deferred: *"no cross-workspace addressing is required by the tuple contract yet."*

Three items are worth doing now, and **each pays for itself even if multi-workspace is never built**:

| # | Change | Justified alone? | Also unlocks |
|---|---|---|---|
| **P1** | **Store the slot index inside `DbArea`** (one `int`, set in the ctor loop at `dbf_file.cpp:410`) | **Yes** -- collapses 19 linear scans to O(1) and removes `slot_of_area_ptr` from the relation hot path (`set_relations.cpp:300,365`), a per-row cost **today at 512** | the cap raise **and** any workspace partition |
| **P2** | **Consolidate to one name resolver**, ambiguity-detecting, adopting `tuple_builder.cpp:204-215`'s message shape | **Yes** -- §4d is a live defect | any qualifier, workspace or not |
| **P3** | **Design P4.1's qualifier as a two-level namespace, outer level defaulted and unreachable** | **Yes** -- zero cost at authoring time | the whole workspace question, deferred at zero carrying cost |

Then amend R27 with a scope clause -- *"`any two OPEN tables` means open within the current workspace; the qualifier's outer level is reserved and defaults to it"* -- and stop.

**P1 is the highest-leverage item in this analysis: one fix, three unlocks, and it repairs a hot-path defect that exists right now.**

### 5a. Reserved grammar (design only -- not to be built by this lane)

`#n` (AreaSlot) and `$v` (Variable) are taken. **`@` is free** -- absent from `TokKind` (`include/cli/expr/token.hpp:15-20`), and there is no `@ row,col SAY` surface in the tree (searched -- absent).

| Form | Meaning |
|---|---|
| `STUDENTS.SID` | unchanged -- current workspace |
| `#2.SID` | unchanged -- slot 2, current workspace |
| `@MCC.STUDENTS.SID` | table in workspace `MCC` |
| `@.STUDENTS.SID` | explicit "current workspace" |

Reserving the sigil costs nothing and keeps a workspace prefix un-confusable with P4.1's table alias (`FROM STUDENTS S`) -- which is the argument for a sigil over a bare word.

### 5b. Recursive / hierarchical workspaces -- the scalar-vs-path decision

*(Raised by the maintainer 2026-07-30 after the lane opened: "can workspaces be recursive/hierarchical?" Recorded here because chat is an input channel, never the record -- AIF-073.)*

**The parser already says yes.** `src/reference/qualified_reference.cpp:82` is a `while (true)` segment loop emitting `SegmentSyntax::{Member, Index, Key, Wildcard}` (`qualified_reference.hpp:18-23`). `@MCC.FALL2026.SEC3.STUDENTS.SID` parses **today**, at unlimited depth, with no change. The grammar is free.

**`DataAddress` says no, and the asymmetry looks accidental:**

```
include/reference/data_address.hpp:131    WorkspaceIdentity          workspace_;   // scalar
include/reference/data_address.hpp:136    std::vector<RelationStep>  relations_;   // vector
```

Relations were designed to chain. Workspaces were designed not to. Nothing in the tree records that as a decision.

#### Arguments for

1. **Memo-residency makes recursion structural, not optional.** AIF-070 proposes memo bytes -> schema+data -> hydrated virtual areas. A workspace living in a memo field lives in a row, in a table, in a workspace. That is containment by construction. The choice is not whether to allow nesting but whether to *forbid* it -- and forbidding it requires a containment invariant that does not exist.
2. **The retention fit is exact, and this lane's task is memory retention.** AIF-073 models the Portal as event-sourced external memory in six classes (working / episodic / prospective / semantic / procedural / evidence). A hierarchy gives retention policy somewhere to attach that a flat namespace does not: drop `@AGENT.CLAUDE.SESSION-*` older than N, keep `@AGENT.CLAUDE.SEMANTIC` indefinitely. `@AGENT.CLAUDE.SESSION-20260730.EPISODIC.EVENTS` is simultaneously an address, a scope, and a retention boundary. For an append-only memory store the tree is not decoration -- it is the structure.
3. **The engine already has one tree.** `SET RELATION`'s parent->child traversal graph. Containment would be a second tree over the same objects. They must stay distinct: a relation crossing a containment boundary should be legal, as a foreign key crosses schemas. Naming that distinction now costs a sentence; discovering it after the join engine ships is a semantics change.

#### Costs

1. **The invariant weakens twice, not once.** Flat multi-workspace: *an alias resolves to one table given a scope.* Hierarchical: *given a scope AND a search rule.* Does bare `STUDENTS` search the current node only, or walk up ancestors? Lexical scoping is convenient and is exactly how action-at-a-distance arises. **Ruling proposed: no implicit ancestor walk in v1.** Resolution is current-node-only unless qualified. That can be relaxed later; it cannot be tightened.
2. **Cycles become reachable once memo-resident** -- a table whose memo holds a workspace containing that table. Needs a containment-DAG invariant and a depth cap. Natural home is `config/build_vectors.cmake` (`DOTTALK_MAX_WORKSPACE_DEPTH`), which per §2 is the established mechanism for exactly this kind of vectored capacity.
3. **Storage stays flat.** A workspace hierarchy still bottoms out in one `_areas[MAX_AREA]`. Naming is hierarchical, storage is not -- two different things wearing one word. Unless memo-residency makes *some* levels hydratable, in which case the tree is heterogeneous and that must be explicit rather than discovered.
4. **`RelationStep` carries flat `DbAreaIdentity{slot, alias, generation}`** with no path, so cross-level relations need the same widening as `workspace_`.

#### Recommendation

The question is not *"should we build recursion."* It is **"should `DataAddress::workspace_` be a scalar or a path."**

Make it `std::vector<WorkspaceIdentity>` (or a dedicated `WorkspacePath`) **now**, while `dottalk_value` is compile-only with exactly one consumer (`src/tests/test_pdlc_foundation_smoke.cpp`, per `src/CMakeLists.txt:46-49`). Default to length <= 1. Recursion then becomes a policy knob rather than a rewrite.

Cost today: one type change, one test touched, nothing else in the tree depends on it. Cost once P4.1 or AIF-070 consumes it: a breaking change across two lanes.

This is `COST_BENEFIT_GATE_DOCTRINE_V1.md` rule 3 applied to this lane's own foundation -- same change, different date, order-of-magnitude difference. **It is the cheapest moment this decision will ever have**, and unlike §5's P1-P3 it is not on AIF-074's clock, it is on AIF-070's and AIF-073's.

#### Three lanes, one hinge

AIF-070 owns *what a workspace is* (named, concurrent, memo-resident, hydratable). AIF-073 owns *agent memory as an event-sourced external store*. AIF-078 owns *how a name resolves once more than one workspace exists*. **Recursion is the hinge between them**: memo-resident containers nest structurally, nested containers are how retention scopes are expressed, and a nested namespace is what the resolver must then address. No one of the three can settle depth alone. Recorded as a cross-lane dependency, not as a proposal to merge them.

---

## 6. Gates / falsifiable exit conditions

| Gate | Content | Exit condition |
|---|---|---|
| **G0** | Run `g0_slot_cost_probe` under **both** supported toolchains | **CLOSED 2026-08-01.** Both rows in sec 2a; cap ladder in sec 2e priced against the worst case per axis. MSVC 1016 B/slot, gcc 1296 -- memory binds on Linux, stack binds on Windows. Transcripts `labtalk/proofs/runs/20260801_aif078_g0_slot_cost_{msvc,gcc}.txt`. Q7 separately proven under MSVC Release (`..._q7_workspace_path_msvc.txt`) |
| **G1** | P1 -- slot stored in `DbArea` | `REGRESSION ALL` green; 19 scan sites removed or reduced to O(1); relation traversal timing captured before/after on a multi-row `REL ENUM` |
| **G2** | P2 -- single ambiguity-detecting resolver | An ambiguous name errors with matching slots named; `SQLSEL_SELECT_V1` + `EXPORT_SDF` + REL regressions green |
| **G3** | Cap raise to 4096 + both guards | `REGRESSION ALL` green; measured RSS delta within §2a; boot clean on MSVC |
| **G4** | R27 scope clause + P4.1 two-level qualifier design accepted | Written into `SQLSEL_PLDC_LANE_V1.md` before P4.1 implementation opens |

**This lane closes at G4.** Building the workspace runtime is explicitly *out of scope* and requires a separate lane and a demand case.

---

## 7. Open questions

- **Q1.** Does P4.1's alias syntax (`FROM STUDENTS S`) and a workspace prefix share one namespace or two? `FROM @MCC.STUDENTS S` reads cleanly; `FROM S.STUDENTS` where `S` could be either is the collision to avoid. **Recommend sigil-distinguished.**
- **Q2.** Is P1 acceptable as a `DbArea` layout change? One `int`. An earlier draft promised no layout change; this reverses that, and it buys enough to be worth reversing.
- **Q3.** Should P2 fold into AIF-074's P4.0b (already touching the evaluator seam, already blocked on ED-01/ED-02), or land ahead of it as its own gate?
- **Q4.** `DOTTALK_MAX_AREAS` upper bound -- `INT_MAX` (correctness floor) or a lower advisory ceiling forcing a deliberate override?
- **Q5.** Terminology: if multi-workspace is ever built, does `WORKSPACE` widen (it currently means "all open slots") or does a new word appear? This affects HELP, CMDHELP, manualgen, and every `@dottalk.usage` block that cites the current definition. **Decide before any build, not during.**
- **Q7 (depth).** Scalar or path for `DataAddress::workspace_` -- see §5b. Decide while `dottalk_value` is still compile-only. Cross-lane: AIF-070 and AIF-073 both bear on it.
- **Q8 (search rule).** If depth > 1 is ever allowed, does an unqualified name search the current node only, or walk up ancestors? §5b proposes current-node-only. This is the invariant, and it should be ruled before any depth is built, not after.
- **Q9 (two trees).** Containment (workspace) vs navigation (`SET RELATION`). Confirm they stay distinct and that a relation may legally cross a containment boundary.
- **Q6.** Expression-level qualification is deliberately excluded -- `include/cli/expr/*` has no alias environment at all (`ast.hpp:48` `FieldRef{name}`; `.` is not an ident char per `lexer.cpp:16-21`). Acceptable boundary, or does `WHERE` need qualification too? If yes, that is a substantially larger lane.

---

## 8. Evidence tier

- **Measured:** all §2a sizes, from a compiled probe against this tree's headers and generated build vectors (g++/libstdc++ x86-64). **MSVC unverified -- G0 exists to close that.**
- **Source-evidenced:** §1, §2b--§2d, §3, §4c, §4d. File and line verified against `D:\code\ccode` at baseline `349227c18` on 2026-07-30.
- **Documentation-tier:** the P2 and P4.1--P6 phase register and rulings R20--R28 -- the AIF-074 charter's own statements of intent, not runtime evidence. §0's reframing rests on `SQLSEL_PLDC_LANE_V1.md:112`; if that line's intent is not current, §4's asymmetry must be re-derived.
- **Chat/AI output (lowest tier):** §5, §5a, §7. No code compiled beyond the `sizeof` probe, no test run, no gate exercised.

---

## 9. Correction recorded

An earlier draft of this analysis (delivered in-session, superseded here) asked whether the 512 slots should be **rationed per workspace**, treating the cap as a fixed budget. It is a settable build vector. **The maintainer caught it.** The error is recorded rather than quietly dropped because it is the origin of `COST_BENEFIT_GATE_DOCTRINE_V1.md` rule 2 -- *verify the constraint is real before designing around it.*

A second error: the in-session report stated `AIF-077` was free (an agent search returned zero hits repo-wide). By the time the lane was opened, AIF-077 was **claimed and closed** the same day for the Codex WIP housekeeping. The number was allocated through `session_coordinator.py claim-aif`, which is exactly the AIF-050 mechanism that made the stale search harmless. **Grep is not an allocator.**
