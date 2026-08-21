# Plan: a recursive memo/schema browser in `dottalk_wx`

**Status: PLAN. Authorises no build.** AIF-120 lane, ALPHA
(`member.ai.claude.cowork`). Written 2026-08-20 after reading the AIF-070 /
AIF-078 record, the memo white paper, the DTX format header, and the live
`WORKSPACES` catalog and its sidecar. Every number below was measured in this
session unless it cites a document.

Steward's instruction: *"a hierarchical/recursive function/procedure in
dottalk_wx that allows you to click on workspaces memo field and open a whole
schema into a graphical database that can open a workspace in that area and so
on."* And: *"learn before you plan, plan before you build."* This is the plan.

---

## 1. What I learned, stated so it can be checked

### 1.1 The memo is an object store, not a block chain

The x64 memo inverts all three classic decisions: a memo is an **object**
addressed by a **64-bit id**; the record field carries a canonical
**16-character hex token** naming the object; the store has **no type word** and
is payload-agnostic by invariant. `update_text` is **append-new** -- it returns
a new token and never reuses the old id, so an object's history is a chain of
identifiers.

On-disk (DTX1): a 4096-byte file header, then objects at 16-byte alignment, each
a 56-byte `OBJ1` record header (`state`, `kind`, `object_id`, `payload_bytes`,
`logical_bytes`, `crc32`, `previous_version_of`) followed by the payload.

**Verified by walking it.** I wrote an independent reader from
`include/memo/dtx_format.hpp` and ran it against the live sidecar:

    dottalkpp/data/workspaces/WORKSPACES.dtx   2,844,400 bytes
    magic DTX1  v1.0  header 4096  align 16
    next_object_id 107   live 106   dead 0
    first_object_offset 4096   append_offset 2,844,400  (== file size)
    objects walked: 106   states {live: 106}   kinds {TextUtf8: 106}
    object ids 1..106, dense

106 objects against 106 catalog rows, ids matching `WS_ID` one-for-one, and the
append offset landing exactly on the file size. The format is a format, not a
habit.

One honest note: `previous_version_of` is **0 on all 106 objects**. Lineage is
carried in the catalog's `PREV_ID` column, not in the store header. The field
exists and is unused.

### 1.2 A mini-database is a whole database in one memo field

`MINIDB 1` is a length-prefixed container -- no delimiters, no escaping, binary
safe because DBF and CDX images contain every byte value:

    MINIDB 1\n
    POSTURE <len>\n <len bytes: DTSHEMA 3 posture, WSID-stamped>
    FILE <len> <relative-path>\n <len bytes: raw file image>
    ...
    END\n

I unpacked two of them with my own parser:

| container | object | bytes | posture | files | payload |
| --- | ---: | ---: | ---: | ---: | --- |
| `mcc_db` | 18 | 94,200 | 1,443 | 24 | 13 `.dbf` + 11 `indexes/*.cdx` |
| `cycle_from_ram` | 106 | 97,381 | 1,453 | 15 | 13 `.dbf` + **2 `.dtx`** |

Leading bytes confirm the cargo: `.dbf` -> `64 7e` (the x64 flavor byte),
`.cdx` -> `CD`, `.dtx` -> **`DT`**.

**That last row is the important one.** `cycle_from_ram` carries
`STUDENTS.dtx` and `TEACHERS.dtx` -- **memo sidecars inside a memo**. Thirty of
the thirty-seven containers carry a nested `.dtx`. The recursion the steward is
asking me to render is already present in the bytes; nothing needs inventing to
make it exist.

### 1.3 The posture is the graph

    DTSHEMA 3 / WSID M106 / FLAVOR X64 / DBFROOT ... IDXROOT ... LMDBROOT ...
    AREA <n> | dbf=<file> | index=<file|none> | indextype=<CDX|CNX|NONE> | tag=<t|none> | alias=<A>
    RELATION <parent-alias> <child-alias> ON <key> [TO <child-key>]
    CURSOR <area> <recno>
    CURRENT <area>

Census over all 106 payloads: **1,798 AREA lines and 1,102 RELATION lines.**
The graph is real and it is large. `RELATION` carries an optional `TO` for a
differing child key, which a renderer must not drop.

### 1.4 The catalog

`WORKSPACES.dbf` -- 106 live rows, reclen 703, 20 fields. `SNAPSHOT` is type
`M` **width 16**, which is the corrected width from the white paper's day-one
defect: the first catalog declared it at the classic 10 and silently truncated
six characters off every token, and the same-session oracle passed because it
compared against memory instead of against the field.

    FMT          DTSHEMA 2: 13   DTSHEMA 3: 56   MINIDB 1: 37
    SUPERSEDED   1: 89   0: 17
    DEPTH        0: 106      <-- every row
    SELF_REF     F: 106      <-- every row

**`DEPTH` and `SELF_REF` are declared and have never been non-zero.** No
container in the catalog carries a `WORKSPACES` table. Nesting was anticipated
in the schema and has never been exercised. That is the honest starting point
for this feature, and it is also the clearest statement of what the feature is
FOR.

### 1.5 The blocker, and it is not small

`WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md` section 5 enumerates,
at file:line, the process-global state that would have to move before two
workspaces can co-reside. Two rows decide this feature's shape:

> **the relation graph** -- `src/cli/set_relations.cpp:47-63` -- one
> `unordered_map` keyed by **bare uppercased parent name**, no owner field.
> *"Two workspaces holding `STUDENTS` collide silently on this key."*

> **name resolution** -- `src/cli/workarea_util.cpp:29-51`
> `find_open_area_by_name_ci` -- linear scan, **first match wins, no ambiguity
> signal.**

Add the flat RAM root and the single `static std::string` last-loaded
workspace, and the conclusion is unavoidable:

**Hydrating a second mini-database while a first one is live is not supported
today, and the failure mode is silent.** The MINIDB record says the same thing
in its own words: *"the per-workspace RAM subroot decision should be made
BEFORE anyone hydrates two containers."*

A GUI whose recursion works by hydrating would be a machine for producing
exactly the silent collision this codebase spends its days hunting.

### 1.6 The seam that makes the feature safe

A `MINIDB 1` container is **completely self-describing**. The posture gives
areas, relations, cursors. Each `FILE` section is a whole DBF image, so its
header yields field names, types and widths without opening anything. A nested
`.dtx` section is a whole memo store, walkable by the same 4096/56 reader. A
`.cdx` names its tags.

So the browser can descend **arbitrarily deep by reading bytes, with zero
engine state**. Nothing is opened, nothing is hydrated, no work area is
consumed, no relation key is written, and depth costs nothing but memory.

**That is the design.** Inspection recurses without limit. Hydration is a
separate, explicit, one-at-a-time act that the UI refuses to perform twice.

### 1.7 Two facts about the existing GUI

- `grep -i memo src/gui/wx/main_frame.cpp` returns **nothing**. The Workbench
  has no memo awareness at all today.
- `workspace_graph_` is a **`wxTextCtrl`**; `UpdateWorkspaceGraph()` calls
  `SetValue(format_workspace_graph_text(...))`. The existing "graph" is ASCII
  text in a text box. There is a Relations page, and it is a list.

And there is no shell verb that returns a memo payload: `MEMO` does
`STATUS`/`VERIFY`/`GC` only. The GUI must reach the bytes through the C++
`IMemoBackend`, not through a command string.

---

## 2. What I propose to build

### 2.1 The shape

A **`MinidbTree`** -- one recursive model, one recursive renderer, four node
kinds:

    CATALOG   the WORKSPACES table itself          children: ROW*
    ROW       one catalog row (name, FMT, size)    children: CONTAINER (if MINIDB) | POSTURE
    CONTAINER a MINIDB 1 payload                   children: AREA*, RELATION*, FILE*
    FILE      one carried file image               children: FIELD* (.dbf) | TAG* (.cdx)
                                                             | OBJECT* (.dtx)  <-- recursion
    OBJECT    one memo object inside a nested .dtx children: CONTAINER | POSTURE | (opaque)

The recursion closes on itself at `FILE(.dtx) -> OBJECT -> CONTAINER -> FILE`.
That is the whole hierarchy, and it is four cases, not a special case per level.

**Lazy by construction.** A node materialises its children on expand. A 94 KB
container is parsed once; a 2.8 MB store is never read whole.

### 2.2 The interaction the steward asked for

1. Browse `WORKSPACES` in the existing grid. The `SNAPSHOT` column shows its
   token today only because nothing renders it -- it will show
   `MINIDB 1 -- 13 areas, 24 files, 94,200 B` instead, read from the row and
   the container head.
2. **Click the memo cell** -> the Minidb page opens with that container
   expanded: its areas, its relations, its files.
3. **A schema drawn, not listed.** Areas as nodes, `RELATION` edges as arrows,
   `ON key` / `TO child-key` on the edge label. This is the "graphical
   database" -- and it is the first real consumer of the 1,102 relation lines
   already sitting in the catalog.
4. **Descend.** Click a carried `.dtx` -> its objects. Click an object that is
   itself a `MINIDB 1` -> its schema, drawn the same way, one level deeper.
   Breadcrumb across the top; depth is displayed, never guessed.
5. **Hydrate** is a button, not a click-through, and it is the ONLY action that
   touches the engine: `VDISK MOUNT` then
   `WORKSPACE LOAD <name> MEMO RAM`, submitted through the existing
   `AsyncSession` the way `LoadWorkspaceFile` already does.

### 2.3 The refusal that makes it honest

**One hydration at a time, refused by name.** If a mini-database is already
hydrated, the button reports:

    APPGUI/MINIDB: <name> is already hydrated. Two mini-databases cannot
    co-reside: the relation graph is keyed by bare parent alias with no owner
    field (set_relations.cpp:47-63) and area name resolution is first-match
    with no ambiguity signal (workarea_util.cpp:29-51). WRITEBACK or
    VDISK UNMOUNT first, or keep browsing -- inspection needs no hydration.

That message is the feature's whole ethic in one place: it names the member,
names the mechanism, cites the line, and gives the way forward. **Silence is
the defect** -- the same rule the four UIDEF backends live under.

### 2.4 Where the code goes

| file | change |
| --- | --- |
| `src/gui/core/minidb_model.{hpp,cpp}` | NEW. Pure model: DTX walk, `MINIDB 1` parse, DBF header parse, CDX tag read. No wx. Testable headless -- and testable against my Python reader, which is the point of having written it |
| `src/gui/wx/minidb_page.{hpp,cpp}` | NEW. The tree + the schema canvas + breadcrumb |
| `src/gui/wx/main_frame.{hpp,cpp}` | a `WorkbenchPage::Minidb`, the memo-cell click, the hydrate button |
| `src/memo/` | **unchanged.** The carrier needed no modification to carry databases; it needs none to be read |

The model links `MemoStore` for live reads and can also read a `.dtx` file
directly, which is what makes it testable without an engine.

### 2.5 Proof, before it is called done

1. **Cross-check against an independent reader.** The model's parse of all 106
   objects must agree with `tools/memo/dtxread.py` on object count, ids, payload sizes,
   container file lists and posture bytes. Two readers written from the spec,
   one in each language, agreeing -- that is a format check, not a self-check.
2. **Render `mcc_db`**: 13 areas, 24 files, and its relation edges, drawn.
3. **Descend into `cycle_from_ram`'s `STUDENTS.dtx`** and list its objects. That
   is the recursion, proven on data that already exists.
4. **The refusal fires.** Hydrate twice, get the message, and confirm the second
   hydration did not happen -- read the area list back, not the message.
5. Screenshot under Xvfb with the event loop pumped, not slept.

---

## 3. What I am NOT proposing, and why

- **No nested SAVE.** Writing a container that carries a `WORKSPACES` table
  would make `DEPTH` and `SELF_REF` meaningful, and it is the obvious next
  move. It is also a format decision with a cycle question attached, and
  AIF-070/078 already have an open ruling on exactly this
  (**Q-R5**: keep or revert `WorkspacePath`, where the recommendation is *keep
  and re-justify as headroom for the memo-resident case, which is structurally
  nested*). **This feature is the evidence that question was waiting for.**
  Read-only descent settles whether the nesting is real without committing the
  format.
- **No second registry.** The catalog is the only index of what exists and there
  is deliberately no second one to drift.
- **No new shell command.** The GUI reads through the C++ interface. Adding a
  `MEMO GET` would be a new surface needing help, harvesting and a usage
  contract, for one caller that is in the same process.
- **No ERP.** Object 1 and its siblings are `CASCADE_ERP` postures; the ERP is
  off-limits, so the demo fixture is the school database (`mcc_db`).
- **No writeback path in v1.** WRITEBACK exists and works; the browser will not
  wrap it until browsing is proven.

---

## 4. Open questions for the steward

- **P1.** Is read-only descent the right v1, with nested SAVE held until the
  Q-R5 ruling? I believe yes, and the argument is section 1.5.
- **P2.** Should the schema canvas be a real drawn graph (wxGraphicsContext,
  boxes and arrows) or a `wxTreeCtrl` with the relations as annotated children?
  Drawn is what "graphical database" sounds like and is more work; the tree is
  honest and cheap. I lean drawn, with the tree as the fallback the character
  cell taught me to keep.
- **P3.** The two prior chat sessions -- minidb, and multiple workstations. I
  have read what landed in the tree from both. If either holds design that
  never landed, it should be read before I build, not after.
- **P4.** `MEMO GC` exists and supersede does not reclaim: ten saves of a 94 KB
  container retain ~1 MB. Should the browser SHOW superseded rows and their
  retained bytes? It is the only place a person would ever see that cost.
