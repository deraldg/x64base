# AI Change Package -- Multi-Workspace Addressing (workspace alias above the table alias)

**File:** `AI_CHANGE_PACKAGE_MULTI_WORKSPACE_ADDRESSING_V1_20260730.md`
**Status:** `review-needed` -- **SUPERSEDED IN PART.** Read `AI_COST_BENEFIT_WORKSPACE_QUALIFIER_VS_SQLSEL_P41_V1_20260730.md` first. That analysis reframes this package: SQLSEL phase P4.1 already owns table-reference qualification (`SQLSEL_PDLC_LANE_V1.md:112`), so the live decision is the *namespace depth* of a qualifier being authored now, not a standalone multi-workspace lane. sec. 4.1's registry and sec. 4.2's grammar remain the reference design **if and when** the feature is built; sec. 9 Q8 is withdrawn as wrong. The recommendation there is to buy the option, not the feature.
**Author:** Claude (hosted AI). Delivered under the Outside-AI Delivery Rule: this is a reviewable package, no direct edits to `D:\code\ccode`.
**Proposed lane:** `AIF-077` *(highest lane ID found in `src/`+`include/` is `AIF-076`; confirm next free ID before adoption)*
**Scope:** Introduce a **workspace alias identifier** one level above the table alias, so relation/tuple/SQL references can name a table in a workspace other than the current one. Implemented as a **slot-partition tag** over the existing single `XBaseEngine`, plus a new `RootSyntax::Workspace` sigil. No second engine. No `DbArea` layout change.

> **Terminology.** In this document *workspace* means a **named, addressable partition of the engine's work-area slots**, not the current meaning ("the collective noun for all 512 open slots plus the relation graph, saveable to a file"). The existing meaning becomes "the default workspace, id 0". This is a widening, not a redefinition -- see §9 Q1 on whether to rename the `WORKSPACE` command surface.

---

## 1. Intent

x64base today has three addressing levels -- engine -> slot -> alias -> field -- with the engine implicit and unnamed. The requested model is five:

```
S/X (all workspaces)  ->  workspace alias  ->  dbarea (schema)  ->  table alias  ->  field
```

Two of those five already exist in source and are used. Two more (workspace, and the qualified-name grammar to reach it) **already exist as compiled C++ types that nothing calls**. This package wires the written-but-unwired foundation to the runtime and adds the one genuinely missing piece: a slot->workspace ownership map.

The change is deliberately *not* "add an object above the alias". The alias object is nearly free. The cost is in three resolution chokepoints that currently assume global uniqueness of a table name, and they must move together or the engine returns wrong rows instead of an error.

---

## 2. Contracts read

| File | Guarantee relied on |
|---|---|
| `src/cli/shell.cpp:527-533` | `XBaseEngine eng;` is the **only** instantiation in the tree. `g_shell_engine = &eng` (`:328-329`), then `relations_api::attach_engine(&eng)`. Every `extern "C"` bridge and `workareas::global()` resolve through this one pointer. |
| `include/xbase.hpp:472-496` | `XBaseEngine` owns `std::array<std::unique_ptr<DbArea>, MAX_AREA> _areas` + `int _current{0}`. `MAX_AREA = 512` (`:43`, from `config/build_vectors.cmake:14`). Slots are dense 0-based ints; `selectArea(int)` throws `out_of_range` outside `[0,512)`. |
| `include/xbase.hpp:139-468` | `DbArea` has **no** alias member, **no** slot member, **no** owner back-pointer. Its identity strings are `_logical_name` / `_db_name` / `_dbf_basename` / `_dbf_abs_path`. `name()` returns `_logical_name` -- `name()` and `logicalName()` are the same string. |
| `src/cli/workarea_util.cpp:29-51` | `find_open_area_by_name_ci` linear-scans all `workareas::count()` slots, uppercase-compares against `logicalName()` then `name()`, and **returns the first match with no ambiguity signal**. Consolidated under AIF-074 P0.2, status `supported` at gate G0 (header `workarea_util.hpp:12-16`). |
| `src/cli/tuple_builder.cpp:127-215` | `resolve_slot_by_area_name_all` is the **only** resolver that detects ambiguity and reports it: `"ERROR: TUPLE area name '<x>' is ambiguous; matching slots: ... Use #<slot>."` This is the precedent the new resolver copies. |
| `src/cli/set_relations.cpp:47-63` | Relation graph is a process-global `static std::unordered_map<std::string, std::vector<Relation>>` keyed by **uppercased parent logical name**. `Relation{ std::string child; ... }` -- child is a bare string. No slot, no path, no owner. |
| `src/cli/set_relations.hpp:123-135` | `RelationSpec{ parent, child, fields, parent_fields, child_fields }` -- the persistence shape. No workspace/slot field. Same for `include/workspace/relation_state.hpp:24-48` (`RelationState`), which has `parent_slot`/`child_slot` but no owner. |
| `src/cli/sqlsel_statement.cpp:89-99` | `is_bare_column()` rejects any name with more than one `.`. Grep for dot-counting across the tree returns **exactly one hit: line 94**. It is the single enforcement point for name-part count. |
| `src/cli/tuple_builder.cpp:197-200`, `rel_enum_engine.cpp:65-90`, `cmd_relations.cpp:153-176`, `set_relations.cpp:120-124` | All four split at the **first** dot with **no** part limit. `A.B.C` silently yields area=`A`, field=`"B.C"`, then falls through to `FieldRef{-1, tok}` ("keep literal token; will resolve to empty value later", `tuple_builder.cpp:223`). **Silent wrong answer, not an error.** |
| `include/reference/data_address.hpp:20-137` | `WorkspaceIdentity{logical_name, profile_path, session_id}` -> `DbAreaIdentity{slot, alias, generation}` -> `TableIdentity` -> `RecordSelector` -> `FieldIdentity`, plus `vector<RelationStep>`. Already written, already compiles. `diagnostic_text()` (`src/reference/data_address.cpp:111-167`) emits `MCC.#2.STUDENTS.CURRENT->ENROLL.RECNO(9).GRADE`; `"CURRENT_WORKSPACE"` sentinel at `:114`. |
| `include/reference/qualified_reference.hpp:11-76` | `RootSyntax{ Bare, Named, AreaSlot, Variable }`, `SegmentSyntax{ Member, Index, Key, Wildcard }`, unlimited-depth segment loop (`src/reference/qualified_reference.cpp:82`), `canonical_syntax()` round-trip (`:248-282`). |
| `src/CMakeLists.txt:45-56` | Verbatim: *"Compile-only foundation; no DbArea/tuple/expression/array integration yet. Built as an isolated static lib (like xexpr)..."* Target `dottalk_value STATIC`. Sole consumer in the tree: `src/tests/test_pdlc_foundation_smoke.cpp`. |
| `src/cli/cmd_workspace.cpp:1393-1560` | `schema_save_to_file` emits `DTSHEMA 2` + `AREA <slot> \| dbf= \| index= \| indextype= \| tag= \| alias=` + `RELATION` + `KEY`. `schema_load_from_file` **closes all areas first**, then restores. Workspaces are swapped, never co-resident. `last_loaded_workspace_file()` (`:172-175`) is a single `static std::string`. |
| `include/workspace/schema_area_state.hpp:31-61` | `SchemaAreaState{ slot, is_open, dbf_path, logical_name, alias, ... }` -- **no owner field**. Note `src/workspace/schema_workspace.cpp:259-269` writes `logical_name` but **not** `alias`; the alias field is not round-tripped today. |
| `include/cli/expr/token.hpp:15-20` | `TokKind{ End, Ident, Number, String, Eq, EqEq, Ne, Lt, Le, Gt, Ge, LParen, RParen, KW_NOT, KW_AND, KW_OR, Plus, Minus, Star, Slash }`. **No `@`, no `#`, no `->`.** `src/cli/expr/lexer.cpp:16-21`: `.` is not an identifier part; a leading `.` starts an xBase `.AND.`/`.T.` dot-keyword (`:95-106`). |
| `include/cli/expr/ast.hpp:48-52` | `FieldRef{ std::string name; }` -- a bare unqualified name. There is no alias environment in the expression evaluator. |
| *searched-and-absent* | No `WorkspaceManager` / `WorkspaceRegistry` / `g_workspaces` / `workspace_id` / `active_workspace` anywhere in `src/`+`include/`. No `ATTACH` / `MOUNT` / `LINK` command. No `cmd_SAY` and no `@ <row>,<col> SAY` surface -- **`@` is an unused sigil**. No SQL `JOIN`/`ON`/`GROUP BY` grammar (`sqlsel_statement.cpp:186-190` rejects a second FROM token). Cross-workspace hits for `cross.?workspace\|foreign.?table\|external.?table\|remote.?table\|attach.?db\|mount.?workspace` in C++ source: 3, all `src/edu/edu_erp.cpp:254,686,714`, all SQLite `pragma foreign_key_check` strings -- unrelated to the native engine. |
| `docs/maintenance/PSEUDO_CHAT_RETURN_LANE_V1.md:151-164` | *(documentation tier)* Records the decision as **deferred**, not absent: *"workspace identity is stable within a session; no cross-workspace addressing is required by the tuple contract yet."* |

---

## 3. As-is behavior (evidence)

```
[implicit, unnamed, exactly one]  XBaseEngine            shell.cpp:527
  └─ slot 0..511 (int)            _areas[MAX_AREA]       xbase.hpp:494
       └─ DbArea                                          xbase.hpp:139
            └─ alias == logicalName() == DBF file stem     cmd_use.cpp:321-322
                 └─ field (bare name, no qualifier)        ast.hpp:48
```

1. `USE <file>` sets alias = file stem. There is **no `USE ... ALIAS <name>` clause** -- grep of `cmd_use.cpp` returns only the two comment-bearing `_setLogicalName`/`_setLegacyName` lines at `:321-322`.
2. `SQLSEL ... FROM <t>` -> `find_open_area_by_name_ci(table_name)` (`sqlsel_statement.cpp:261`), first match wins, silently.
3. `REL ADD <parent> <child> ...` -> two `find_open_area_by_name_ci` calls (`set_relations.cpp:524-525`), stored under a bare uppercase key.
4. `SET RELATION TO <expr> INTO <child>` never names the parent; it is always `current_parent_name()` (`cmd_set_relation.cpp:217` -> `set_relations.cpp:110-118` `infer_parent_from_workarea()`).
5. `WORKSPACE LOAD` closes everything, then restores. **One workspace resident at a time.**
6. `A.B.C` in any tuple/relation term degrades silently to area=`A`, field=`"B.C"` -> empty value.

Net: cross-*area* addressing works and is the current ceiling. Cross-*workspace* addressing has no representation, no grammar, and no resolver.

---

## 4. Proposed design

### 4.1 The low-cost object -- `WorkspaceTag` + slot-partition registry

**New file `include/workspace/workspace_registry.hpp`** (sketch):

```cpp
namespace dottalk::workspace {

inline constexpr std::uint16_t WS_DEFAULT = 0;      // today's implicit workspace
inline constexpr std::uint16_t WS_ANY     = 0xFFFF; // the "S"/"X" all-workspaces pointer

struct WorkspaceTag final {
    std::uint16_t id{WS_DEFAULT};
    std::string   alias;          // uppercase, unique, validated like a table alias
    std::string   profile_path;   // maps to WorkspaceIdentity::profile_path
    std::uint64_t session_id{0};  // maps to WorkspaceIdentity::session_id
};

class WorkspaceRegistry final {
public:
    static WorkspaceRegistry& global() noexcept;      // mirrors workareas::global()

    std::uint16_t ensure(const std::string& alias);   // create-or-get, uppercased
    const WorkspaceTag* by_id(std::uint16_t) const noexcept;
    const WorkspaceTag* by_alias(const std::string&) const noexcept;

    std::uint16_t owner_of_slot(int slot) const noexcept;  // WS_DEFAULT if untagged
    void          bind_slot(int slot, std::uint16_t ws) noexcept;
    void          release_slot(int slot) noexcept;         // on CLOSE

    std::uint16_t current() const noexcept;
    bool          set_current(std::uint16_t) noexcept;
    std::vector<std::uint16_t> all() const;

    // Bridge to the already-written foundation type.
    reference::WorkspaceIdentity identity_of(std::uint16_t) const;

private:
    std::vector<WorkspaceTag> tags_{ WorkspaceTag{WS_DEFAULT, "", "", 0} };
    std::array<std::uint16_t, xbase::MAX_AREA> owner_{};   // <-- the entire storage cost
    std::uint16_t current_{WS_DEFAULT};
};

} // namespace dottalk::workspace
```

**Total added state: 1 KB** (512 x `uint16_t`) plus a small vector of tags. Zero bytes added to `DbArea`. No engine lifecycle change. Existing slot ints stay valid everywhere. `owner_` default-initialises to all-zero, i.e. every existing slot belongs to `WS_DEFAULT` -- which is why §7.4 (no-regression) should hold bit-identically.

The **alias itself does not move**. It stays `DbArea::logicalName()`. What is added is *ownership*, and with it the uniqueness contract weakens from **globally unique** to **unique within a workspace**. That weakening is the entire risk surface of this package, and §4.3 is the mitigation.

### 4.2 The grammar -- `RootSyntax::Workspace`, sigil `@`

`#n` (AreaSlot) and `$v` (Variable) are taken. `@` is free: it is absent from `TokKind` (`token.hpp:15-20`) and there is no `@ row,col SAY` surface in the tree (searched-and-absent, §2). Extend `include/reference/qualified_reference.hpp:11-16`:

```cpp
enum class RootSyntax : std::uint8_t {
    Bare, Named, AreaSlot, Variable,
    Workspace,      // NEW: @ALIAS
    AllWorkspaces   // NEW: @*   <-- the "S"/"X" pointer
};
```

Surface forms:

| Form | Meaning | Resolves to |
|---|---|---|
| `STUDENTS.SID` | unchanged -- current workspace | `ws = current()` |
| `#2.SID` | unchanged -- slot 2 of current workspace | `ws = current()`, slot 2 |
| `@MCC.STUDENTS.SID` | table `STUDENTS` in workspace `MCC` | `ws = by_alias("MCC")` |
| `@MCC.#2.SID` | slot 2 **within** workspace `MCC`'s partition | workspace-relative slot |
| `@.STUDENTS.SID` | explicit "current workspace" | `ws = current()` |
| `@*.STUDENTS` | every workspace owning a `STUDENTS` | set-valued; see §9 Q4 |

Parser change is contained: `src/reference/qualified_reference.cpp:48-78` (root dispatch) gains one branch. The `while(true)` segment loop at `:82` is already unlimited-depth, so `@MCC.STUDENTS.SID` needs **no** depth work. `canonical_syntax()` (`:248-282`) gains the `@` re-emit.

`DataAddress::diagnostic_text()` (`src/reference/data_address.cpp:111-167`) already prints the workspace level and already has the `"CURRENT_WORKSPACE"` sentinel -- **no change needed**, it becomes truthful for the first time.

### 4.3 The resolver -- scope + ambiguity (correctness core)

Keep the existing signature so all six call sites keep compiling, and add a scoped overload in `src/cli/workarea_util.hpp`:

```cpp
struct ResolveDiag final {
    int              matches{0};
    std::vector<int> slots;        // all matching slots, for the error text
    std::uint16_t    ws{0};
};

// UNCHANGED signature. Semantics narrow: now resolves within the CURRENT
// workspace only. Identical behavior while only WS_DEFAULT exists.
xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name);

// NEW. ws == WS_ANY searches every workspace and reports ambiguity.
xbase::DbArea* find_open_area_by_name_ci(const std::string& logical_or_name,
                                         std::uint16_t     ws,
                                         ResolveDiag*      diag = nullptr);
```

Body change to `src/cli/workarea_util.cpp:29-51` -- one added guard inside the existing loop:

```
for i in [0, workareas::count()):
    if ws != WS_ANY and registry.owner_of_slot(i) != ws: continue    # NEW
    ... existing logicalName()/name() uppercase compare ...
    if match:
        if diag: diag->matches++; diag->slots.push_back(i)           # NEW
        if !first_hit: first_hit = a
return first_hit
```

**Callers must stop treating "resolved" as "unambiguous".** Adopt the message shape `tuple_builder.cpp:204-215` already proves:

```
ERROR: area name 'STUDENTS' is ambiguous across workspaces (MCC slot 2, LAB slot 7).
       Qualify it: @MCC.STUDENTS  or  @LAB.STUDENTS
```

Call sites to update: `sqlsel_statement.cpp:261`, `set_relations.cpp:395,409,418,524,525,635,670,681,974,1030,1032`, `cmd_relations.cpp:197`, `rel_enum_engine.cpp:110`, `cmd_workspace.cpp:1647`.

### 4.4 The relation store -- add an owner key

`set_relations.cpp:47-63` is keyed by bare uppercase parent name. With two workspaces both holding `STUDENTS`, that key collides and one workspace's relations silently overwrite the other's. Minimum viable fix -- qualify the key, not the struct:

```cpp
// key becomes "<ws_id>:<UPPER(parent)>"  e.g. "1:STUDENTS"
static std::string rel_key(std::uint16_t ws, const std::string& parent);
struct Relation {
    std::uint16_t child_ws{WS_DEFAULT};   // NEW: child may live elsewhere
    std::string   child;
    std::vector<JoinField> joins;
    ...
};
```

`RelationSpec` (`set_relations.hpp:123-135`) gains `parent_ws` / `child_ws` **as optional trailing fields** so existing `.relations/*.json` files load unchanged (absent => `WS_DEFAULT`). Same for `RelationState` (`include/workspace/relation_state.hpp:24-48`).

This is the step that actually delivers "SQL relations between multiple workspaces": once `Relation::child_ws` exists, `enum_emit_for_current_parent` traversal spans partitions with no change to its algorithm, because it already works from resolved `DbArea*`, not from names.

### 4.5 The 2-part cap and the four silent splitters

`sqlsel_statement.cpp:89-99` `is_bare_column()` must accept `@WS.TABLE.FIELD`. Proposed: parse the optional `@`-root **off the front** first, then apply the existing <=1-dot rule to the remainder -- so the cap stays at two parts *after* the workspace root, and the one enforcement point stays one enforcement point.

The four first-dot splitters (`tuple_builder.cpp:197`, `rel_enum_engine.cpp:80`, `cmd_relations.cpp:166`, `set_relations.cpp:120`) must **reject** an unrecognised extra dot instead of degrading to `FieldRef{-1, tok}`. This is a behavior change independent of workspaces and arguably a standalone bug fix -- see §9 Q3 on splitting it into its own gate.

### 4.6 Persistence

`schema_save_to_file` (`cmd_workspace.cpp:1448-1493`) bumps `DTSHEMA 2` -> `DTSHEMA 4` *(note: `SchemaWorkspace::save_file` independently writes `DTSHEMA 3` at `src/workspace/schema_workspace.cpp:256` -- the two writers are already out of step; see §9 Q5)* and gains:

```
WORKSPACE <id> | alias=<ALIAS> | profile=<path>
AREA <slot> | ws=<id> | dbf=... | index=... | indextype=... | tag=... | alias=...
```

`ws=` absent on load => `WS_DEFAULT`. `SchemaAreaState` (`schema_area_state.hpp:31-61`) gains `std::uint16_t ws{0};`. **Also fix while here:** `save_file` currently writes `logical_name` but not `alias` (`schema_workspace.cpp:259-269`) -- the alias field does not round-trip, which will silently break workspace-scoped aliasing if left alone.

### 4.7 Command surface (additive)

```
WORKSPACE NEW <alias>            create partition, make current
WORKSPACE USE <alias>            switch current partition
WORKSPACE LIST                   id, alias, slot count, current marker
WORKSPACE DROP <alias>           close its areas, release slots
USE <file> [IN <alias>]          open into a named partition
SELECT @<alias>.<table>          cross-partition select
```

`WORKSPACE OPEN/ADD/CLOSE/SAVE/LOAD/TUPLES` (`cmd_workspace.cpp:12-105`) keep today's meaning, operating on the current partition.

---

## 5. Patch surface

| File | Change |
|---|---|
| `include/workspace/workspace_registry.hpp` | **NEW** -- `WorkspaceTag`, `WorkspaceRegistry` (§4.1) |
| `src/workspace/workspace_registry.cpp` | **NEW** -- impl + `global()` |
| `include/reference/qualified_reference.hpp:11-16` | add `Workspace`, `AllWorkspaces` to `RootSyntax` |
| `src/reference/qualified_reference.cpp:48-78, 248-282` | `@` root parse branch + `canonical_syntax()` re-emit |
| `src/cli/workarea_util.hpp` / `.cpp:29-51` | `ResolveDiag`, scoped overload, owner guard in loop |
| `src/cli/set_relations.hpp:123-135` / `.cpp:47-63, 508-575` | `rel_key`, `Relation::child_ws`, `RelationSpec` optional ws fields |
| `src/cli/sqlsel_statement.cpp:89-99, 261` | `@`-root strip before the <=1-dot rule; scoped FROM resolution |
| `src/cli/tuple_builder.cpp:197-223` | reject extra-dot instead of literal-token fallback |
| `src/cli/rel_enum_engine.cpp:65-90`, `cmd_relations.cpp:153-176`, `set_relations.cpp:120-124` | same |
| `src/cli/cmd_use.cpp:~321` | `IN <alias>` clause; `bind_slot` after open |
| `src/cli/cmd_workspace.cpp:1393-1560, 1647` | `NEW`/`USE`/`LIST`/`DROP`; `DTSHEMA 4`; `WORKSPACE`/`ws=` records |
| `include/workspace/schema_area_state.hpp:38` | add `std::uint16_t ws{0}` |
| `src/workspace/schema_workspace.cpp:256-269` | version bump; **fix alias not round-tripping** |
| `src/CMakeLists.txt:45-56` | `dottalk_value` stops being compile-only; link `dottalk_workspace`/`dottalkpp`. **Check for a link cycle** -- the registry needs `xbase::MAX_AREA`, and `dottalk_value` is currently isolated *precisely* to avoid that dependency. See §9 Q2. |
| **No change** | `include/xbase.hpp` (`DbArea`, `XBaseEngine`), `src/cli/shell.cpp`, `include/cli/expr/*` (no expression-level qualification in v1 -- §9 Q6) |

---

## 6. Behavioral effects (expected)

- Multiple named workspaces co-resident; total open areas still capped at 512 across **all** of them.
- `@MCC.STUDENTS.SID` resolves; `REL`/`TUPLE` traversal spans partitions unchanged (works from `DbArea*`, not names).
- Unqualified names resolve **within the current workspace only** -- a narrowing that is invisible while only `WS_DEFAULT` exists, and is the intended containment once it does not.
- Ambiguous unqualified names across workspaces become a **hard error with a suggested qualification**, replacing today's silent first-match.
- `A.B.C` becomes an error instead of an empty value (§4.5) -- a visible behavior change to existing scripts.
- Old `.relations/*.json` and `DTSHEMA 2`/`3` workspace files load unchanged into `WS_DEFAULT`.
- No change to record locking, transactions, indexing, or memo.

---

## 7. Falsifiable exit conditions / proof artifacts

1. **Co-residency.** `WORKSPACE NEW MCC`; `USE students.dbf`; `WORKSPACE NEW LAB`; `USE students.dbf`; `WORKSPACE LIST` -> two partitions, one slot each, both open simultaneously. `SELECT @MCC.STUDENTS` and `SELECT @LAB.STUDENTS` land on **different** slots.
2. **Ambiguity is loud.** With both open, `SELECT STUDENTS` from a third partition -> error naming `MCC slot n` and `LAB slot m` and suggesting `@MCC.STUDENTS`. Exit code non-zero. **Never a silent first-match.**
3. **Cross-workspace relation.** `REL ADD @MCC.STUDENTS @LAB.ENROLL ON SID`; `REL ENUM` -> rows joining across partitions. `REL SAVE` -> JSON carries `parent_ws`/`child_ws`. `REL LOAD` in a fresh session reproduces identical rows.
4. **No regression (the gate that matters).** Full `REGRESSION ALL` green with **zero** `WORKSPACE NEW` issued -- i.e. everything runs in `WS_DEFAULT` and behaves bit-identically to the pre-change build. Diff the captured output; require byte equality.
5. **Backward file compat.** A `DTSHEMA 2` workspace file and a pre-change `.relations/relations.json` both load; all areas land in `WS_DEFAULT`; relations resolve.
6. **Grammar round-trip.** `QualifiedReferenceParser` unit test: `@MCC.STUDENTS.SID`, `@.STUDENTS.SID`, `@MCC.#2.SID`, `@*.STUDENTS` each parse, and `canonical_syntax()` re-emits the input exactly. Extend `src/tests/test_pdlc_foundation_smoke.cpp`.
7. **Extra-dot rejection.** `TUPLE A.B.C` errors with a diagnostic; does not emit an empty column.
8. **Slot exhaustion.** Open areas across partitions until 512 is reached -> clean error naming the cap, no crash, no silent wrap.

Status stays `review-needed` until 1--5 are runtime-evidenced.

---

## 8. Sequencing (proposed gates)

| Gate | Content | Independently shippable? |
|---|---|---|
| **G0** | `WorkspaceRegistry` + `owner_` array, everything pinned to `WS_DEFAULT`. No grammar, no command surface. Proves exit condition 4 alone. | Yes -- pure no-op |
| **G1** | Scoped resolver + `ResolveDiag` + ambiguity errors. Still one workspace. | Yes |
| **G2** | Extra-dot rejection in the four splitters (§4.5). *Arguably a standalone bug fix.* | Yes -- see Q3 |
| **G3** | `RootSyntax::Workspace`, `@` parse, `canonical_syntax()`, foundation tests. Grammar only, no runtime binding. | Yes |
| **G4** | `WORKSPACE NEW/USE/LIST/DROP`, `USE ... IN`, persistence `DTSHEMA 4`. First user-visible multi-workspace. | Yes |
| **G5** | Relation store owner key + cross-workspace `REL`. Delivers the stated goal. | Yes |
| **G6** | `@*` all-workspaces pointer. | Yes |

G0--G2 carry all the regression risk and none of the new capability. Recommend landing and proving them before any of G3--G6 is written.

---

## 9. Open questions

- **Q1 (naming).** `WORKSPACE` currently means "all 512 slots + the relation graph". This package makes it mean "a named partition of them". Keep the word and widen it, or introduce a distinct term (`REALM`, `SPACE`, `DOMAIN`) and leave `WORKSPACE` alone? This affects HELP, CMDHELP, manualgen, the `@dottalk.usage v1` blocks, and every doc citing the current definition. **Recommend deciding before G0**, since it renames files.
- **Q2 (link topology).** `dottalk_value` is isolated in `src/CMakeLists.txt:45-56` *specifically* to avoid depending on `DbArea`. `WorkspaceRegistry` needs `xbase::MAX_AREA`. Options: (a) registry lives in `dottalkpp`, not `dottalk_value`, and `dottalk_value` stays pure; (b) `MAX_AREA` moves to a shared config header; (c) registry is sized dynamically and never sees `xbase.hpp`. **(a) or (b) preferred -- do not create a cycle.** I have not read the full link graph; confirm.
- **Q3 (gate split).** Should G2 (extra-dot rejection) ship as its own lane? It is a correctness fix to today's engine, independent of workspaces, and it will break any existing script relying on the silent-empty behavior. Bundling it hides that breakage inside a feature lane.
- **Q4 (`@*` semantics).** You chose a reserved sigil for the top-level pointer. What does `@*.STUDENTS` *evaluate to* -- an error unless exactly one match (safe), a union of rows requiring identical schemas (expensive, and there is no schema-compat check in the tree), or a metadata-only enumeration (`WORKSPACE LIST`-like)? **Recommend: enumeration only in v1**, since there is no planner (`sqlsel_statement.cpp:472-476`: "there is nothing to explain") and no union machinery.
- **Q5 (schema version drift).** `cmd_workspace.cpp:1448` writes `DTSHEMA 2`; `src/workspace/schema_workspace.cpp:256` writes `DTSHEMA 3`. Two writers, two versions, one format name. Which is authoritative, and should this package reconcile them or route around? Related: `save_file` drops `alias` (`:259-269`) -- confirm that is a bug, not intent.
- **Q6 (expression level).** `include/cli/expr/*` has no alias environment at all (`ast.hpp:48` `FieldRef{name}`; `.` is not an ident char, `lexer.cpp:16-21`). This package deliberately does **not** touch it -- `@WS.T.F` works in tuple/relation/FROM position only, not inside a `WHERE`. Is that an acceptable v1 boundary, or does `WHERE` need qualification too? (If yes, that is a substantially larger lane: new `TokKind`, new AST node, multi-area record binding in `compile_bool_predicate`.)
- **Q7 (dbarea vs schema).** Your framing says "workspace over multiple dbareas (schema)". In source, `DbArea` maps to a **file path**, not a schema object -- there is no schema binding on it (`dbarea_populate.hpp:31` just calls `setFilename`). Is a separate schema level wanted between workspace and area, or is "dbarea == schema" the intended identification? This package assumes the latter. If the former, `DataAddress` needs a sixth level and §4.2's grammar grows a part.
- **Q8 (slot budget).** ~~512 slots now shared across all partitions. Is a per-workspace reservation wanted?~~ **WITHDRAWN -- the question was wrong.** `MAX_AREA` is a settable build vector (`config/build_vectors.cmake:14`, AIF-044), and `:8-12` states 512 was chosen only to preserve compiled behavior. There is no budget to ration. See the companion cost/benefit for the measured cap analysis and the recommended raise to 4096.
- **Q9 (session_id).** `WorkspaceIdentity::session_id` exists (`data_address.hpp:23`) and is unpopulated. Should the registry fill it, and from what -- the traceability lane's run id (`AI_RUN_TRACEABILITY_CONTRACT_V1.md`)? Not read; flagged.

---

## 10. Fallback

Every gate is additive and defaults to `WS_DEFAULT`. Reverting is: stop issuing `WORKSPACE NEW`, and the `owner_` array is uniformly zero -- resolution collapses to today's global scan. G0--G1 can be compiled out behind a build vector (`config/build_vectors.cmake` already carries `DOTTALK_MAX_AREAS`; add `DOTTALK_MULTI_WORKSPACE` defaulting off) so the feature is dark until exit conditions 1--5 are runtime-evidenced.

The one change that is **not** trivially revertible is G2 (extra-dot rejection), because scripts relying on the silent-empty behavior will start erroring. That is the strongest argument for Q3.

---

## 11. Evidence tier

Everything in §2 and §3 is **source-evidenced** -- file and line verified against `D:\code\ccode` on 2026-07-30. Two claims were spot-checked directly rather than via search: `src/cli/shell.cpp:527-529` (single engine) and `src/CMakeLists.txt:45-56` (compile-only foundation).

Everything in §4 through §10 is **chat/AI output** -- the lowest tier. No code was compiled, no test was run, and the link graph (Q2) was not traced. Sketched signatures are illustrative and have not been checked against member layouts. This document does not claim more than "a reviewable proposal grounded in verified current-state evidence".
