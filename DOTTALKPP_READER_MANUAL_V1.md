# DotTalk++ Reader Manual v1

Status: reader-facing manual  
Audience: new DotTalk++ user, human developer, AI development agent  
Source root: `D:\code\ccode`  
Promoted from curated harvest material and runtime proofs on 2026-06-28

This manual is the first clean reader-facing pass over the current DotTalk++ documentation harvest. It is intentionally smaller than the harvest bundle. The goal is to explain what to run, what each workflow means, and what evidence a developer or AI agent should collect before changing runtime behavior.

The raw source pool remains available in:

- `DEVELOPER_MANUAL_HARVEST_INSPECTION_V1.md`
- `DEVELOPER_MANUAL_HARVEST_QUALITY_SCAN_V1.md`
- `DEVELOPER_MANUAL_HARVEST_MANIFEST_V1.csv`
- `DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`

The manual generation anchor map is:

- `DOTTALKPP_MANUAL_ANCHOR_MAP_V1.md`
- `docs/manuals/anchors/manual_generation_anchor_map_v1.csv`
- `docs/manuals/assets/diagrams/MANUAL_DIAGRAM_ASSET_REGISTRY_V1.md`
- `docs/manuals/assets/diagrams/manual_diagram_asset_registry_v1.csv`

The prose guide for turning anchors into readable sections is:

- `DOTTALKPP_MANUAL_PROSE_GUIDE_V1.md`
- `DOTTALKPP_PROFESSIONAL_MANUAL_BLUEPRINT_V1.md`
- `DOTTALKPP_MANUAL_MATURITY_MODEL_V1.md`

## Table of Contents

1. What DotTalk++ Is
2. The Trinity Headers
3. xBase Lineage and Compatibility
4. Build and Run
5. Shell Basics
6. DotScript
7. The x64 Workflow
8. Creating DBFs
9. Schema Rules
10. Indexes, CNX, CDX, and SET ORDER
11. Navigation, Search, and Browse
12. Editing Data
13. Work Areas and Cursor Control
14. Record and Table Locking
15. Table Buffering
16. Commit and Rollback
17. Operational Safety Checklist
18. Import and Export
19. Commands and Functions Reference
20. LabTalk Case Catalog
21. Troubleshooting
22. Developer Appendix
23. Evidence Anchors and Manual Generation

## 1. What DotTalk++ Is

DotTalk++ / x64base is a working educational xBase / FoxPro-inspired database runtime, command shell, and architecture lab built in modern C++.

It is not presented as a finished commercial database product. It is a working educational and research system: part DBF database runtime, part command shell, part historical teaching environment, part metadata experiment, and part architecture laboratory.

The project draws inspiration from the classic xBase lineage:

```text
dBase   - early interactive database shell
Clipper - compiled xBase systems
FoxPro  - relational navigation and index-driven querying
```

DotTalk++ preserves useful ideas from those systems while extending them with modern C++ structure, help catalogs, relation traversal, tuple projection, scripting, automation, metadata tables, validation tools, browsers, and simple text user interface surfaces.

It is not a direct port of an older product. It is a broader reimplementation and expansion.

DotTalk++ sits between FoxPro and Clipper:

```text
interactive and stateful like FoxPro
extensible and compilable like Clipper
```

The project is intended to serve as:

- a working DBF database runtime
- a relational exploration environment
- a scripting and automation shell
- a teaching system for database concepts
- an architecture lab for metadata, HELP, validation, and browser design

A major design goal is for DotTalk++ to become increasingly self-documenting. Commands, functions, arguments, aliases, subcommands, metadata tables, HELP output, validation reports, scripts, browsers, and TUI surfaces are being designed to reinforce each other instead of living as separate hand-written descriptions.

Some subsystems are runtime-proven. Other subsystems are canaries, source-supported features, or integration work. The repository is intentionally honest about that distinction. The goal is to build finished educational tools, database utilities, and applications from proven layers, not to pretend every subsystem is complete at the same time.

### History

DotTalk++ traces back to 1993, when Derald Grimwood wrote a small ANSI C database program as a practical and experimental system. That early program included fixed-length record storage and a simple in-memory B-tree.

In 2025, the earlier work was revived and used as the conceptual basis for a modern 64-bit rebuild in C++. The result became DotTalk++: not a direct port, but a broader reimplementation and expansion.

The project honors the xBase tradition while extending it into a modern, teachable, experiment-friendly database runtime.

Part of the educational value is historical. DotTalk++ shows students a transitional period in computing: the 8-bit and early-16-bit personal-computer era of the 8088, 8086, DOS, text UIs, command systems, DBF files, and direct file-based data work.

This is not nostalgia for its own sake. It is a way to make the layers visible.

### Educational Purpose

DotTalk++ is built for learning as much as for execution. The system is intended to help students see concepts that are usually hidden:

```text
table files
records
fields
field types
work areas
indexes
index tags
relations
tuple traversal
schemas
metadata
HELP generation
runtime validation
simple text interfaces
command discovery
```

Instead of presenting the database as a black box, DotTalk++ exposes the moving parts. A student can open a table, inspect its structure, browse records, change order, see relation trees, follow child records, inspect metadata tables, use HELP, run validation checks, and compare command documentation against runtime reflection.

The goal is not to teach old software as a museum piece. The goal is to use an understandable historical model to explain modern ideas:

```text
classic DBF tables        -> structured storage
records and fields        -> physical data modeling
indexes                   -> access paths
work areas                -> runtime context
relations                 -> graph navigation
tuple grids               -> joined views
metadata tables           -> self-description
HELP and CMDHELPCHK       -> documentation as executable contract
simple TUI menus          -> command discovery and reinforcement
scripts                   -> repeatable workflows
```

### Design Philosophy

DotTalk++ is built around a few practical beliefs:

- Preserve the engineering behavior of FoxPro/xBase where it still makes sense.
- Avoid copying branding or unnecessary legacy constraints.
- Separate engine, interface, metadata, HELP, validation, and storage concerns.
- Keep the command surface understandable.
- Let runtime behavior prove architecture.
- Teach by exposing records, fields, indexes, relations, work areas, metadata, HELP, and validation.
- Use the command surface as a learning tool, not just an operator interface.
- Treat the simple TUI as reinforcement for command discovery and historical context.
- Design toward a self-documenting runtime: commands, functions, metadata, HELP, reports, browsers, and validators should agree.

A useful project rule:

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
DotScript executes reviewed procedures.
Manualgen and maintenance packages preserve development intent.
```

The README form of the same rule is:

```text
Conventions suggest.
Registration declares.
Metadata records.
Runtime proves.
Validators enforce.
```

DotTalk++ is intentionally stateful and interactive. It exposes important runtime concepts directly:

```text
current work area
current record pointer
active order/index
active filter
relation graph
buffering state
workspace state
```

The goal is to make database behavior visible during live operation rather than hiding it behind abstraction.

### Working Model

DotTalk++ can be understood as four cooperating layers:

```text
1. Command Layer
   interactive commands, scripts, command discovery, and automation

2. Data Layer
   tables, records, fields, work areas, indexes, and storage behavior

3. Logic Layer
   expressions, predicates, functions, validation, and control flow

4. Projection Layer
   LIST, SMARTLIST, TUPLE, REL ENUM, ERSATZ, SMARTBROWSE, SIMPLEBROWSE, and other browsers
```

This model separates:

```text
what the user types
what the data engine stores
how logic is evaluated
how results are projected back to the screen
```

The important architectural parts are:

- `x64base`: storage/runtime foundation, including DBF and index work.
- DotTalk++ shell: command surface, work areas, table commands, HELP, scripts, and runtime validation.
- DotScript: repeatable script/proof layer for running command sequences.
- Schema and data dictionary files: contracts for tables, indexes, imports, and generated reports.
- SelfDoc and manualgen: provenance, documentation, and maintenance workflow.
- LabTalk: optional educational overlay and case catalog.

Keep these boundaries clear. LabTalk and story/case material should not become a dependency for the professional runtime. Manualgen and maintenance internals should not be presented as ordinary user commands.

### Current Status Snapshot

The x64base README describes the project as a working beta under active development. The current manual should preserve that honesty:

| Component | Manual stance |
|---|---|
| Engine | Working beta. |
| Indexing | INX/CNX/CDX/LMDB are active; promoted reader claims require transcripts. |
| Memo system | Active with canaries; large-object and repair/compaction claims need proof. |
| CLI and DotScript | Active and usable. |
| Tuple, relations, and browsers | Active; selected relation and browser paths are runtime-proven in the README development checkpoint. |
| HELP and metadata | Active; reflection-backed HELP exists and SYS* congruence validation is a next-step target. |
| DDL | Active / partial. |
| Python binding | Active with read-only smoke coverage. |
| Simple TUI | Active / experimental; discovery and teaching layer, not the canonical runtime surface. |

Manual rule: use this status snapshot as orientation, not as a substitute for proof. A feature becomes a reader workflow only when the manual has an anchor and a current transcript or an explicit maturity status.

## 2. The Trinity Headers

When this project says "the trinity headers," it means the three main xBase data-structure headers:

```text
include/xbase.hpp
include/xbase_vfp.hpp
include/xbase_64.hpp
```

They are the "three in one" data-structure spine for the runtime.

| Header | Role | Reader meaning |
|---|---|---|
| `xbase.hpp` | Core xBase engine types, constants, `DbArea`/engine contracts, runtime area kind, capabilities, memo/index hooks. | The neutral runtime foundation. |
| `xbase_vfp.hpp` | FoxPro / Visual FoxPro descriptor bridge, DBF level/flavor detection, VFP field extras, classic/VFP compatibility helpers. | The compatibility layer from classic DBF/FoxPro/VFP into DotTalk++. |
| `xbase_64.hpp` | x64 dialect expansion layer, x64 version byte, large header extension, X64 metadata blocks, fallback descriptor policy, name resolution. | The x64base extension layer that carries modern 64-bit and metadata-aware structure. |

The dependency direction matters:

```text
xbase.hpp
  -> xbase_vfp.hpp
    -> xbase_64.hpp
```

`xbase.hpp` stays neutral. `xbase_vfp.hpp` adds classic/FoxPro/VFP interpretation. `xbase_64.hpp` owns x64 extension structures, vector metadata, fallback descriptor policy, and authoritative name handling.

This is separate from, but connected to, the reader-facing data model:

```text
DBF/XDBF table storage
CNX/CDX/INX order and index containers
schema, HELP, and metadata contracts
```

The headers define the data structure spine. The reader-facing model explains how users experience that spine through tables, indexes/orders, schemas, HELP, and metadata.

## 3. xBase Lineage and Compatibility

DotTalk++ should be introduced as an xBase/FoxPro-inspired runtime, not as a blind clone. Its vocabulary deliberately overlaps with the world of dBASE, Clipper, FoxPro, and Visual FoxPro: tables, work areas, commands, record navigation, `USE`, `LIST`, `APPEND`, `REPLACE`, `SEEK`, `SET ORDER`, and index tags.

Reader-facing lineage:

| Era/family | Manual stance |
|---|---|
| MS-DOS-era dBASE/xBase | Historical root for DBF tables, command navigation, work areas, and visible record operations. |
| Clipper and DOS xBase applications | Useful lineage for compiled business workflows and direct command/data thinking. |
| FoxPro and Visual FoxPro | Strongest vocabulary bridge for commands, indexes, tags, work areas, browse/list behavior, and business database workflows. |
| Microsoft data pipeline era | Access, Excel, ODBC, SQL Server, and VFP are useful context for why xBase mattered in business data work. |
| DotTalk++ / x64base | Modern C++ continuation: visible xBase-style operation plus schema, metadata, HELP evidence, DotScript, and x64-oriented storage/index work. |

Compatibility rule: use lineage to explain vocabulary, but do not claim a specific dBASE/FoxPro/VFP behavior is supported unless the current runtime proves it. In the final manual, every compatibility claim should be marked as one of:

- supported and transcript-proven
- supported by current HELP/source contract
- lineage/background only
- future or experimental

Current classification for this manual:

| Claim area | Status | Evidence |
|---|---|---|
| DBF-style tables, fields, records, `APPEND`, `REPLACE`, `LIST`, `STRUCT` | Supported and transcript-proven | x64 walkthrough v2 transcript. |
| `CREATE X64` v64 table creation | Supported and transcript-proven | x64 walkthrough v2 transcript. |
| CDX tag order on v64 tables with LMDB backing | Supported and transcript-proven | CDX order v2 transcript. |
| `SET INDEX TO <cdx>` and `SET ORDER TO TAG <tag>` | Supported and transcript-proven for the CDX/LMDB v64 path | CDX order v2 transcript. |
| `DDL CREATE DBF ... FROM schema.json` | Supported and transcript-proven for the tested schema path | schema DDL v2 transcript. |
| `LOCATE`, `GO TOP`, `GO BOTTOM`, `SKIP`, `RECNO`, `DISPLAY`, `SMARTLIST` | Supported and transcript-proven for the tested forms | navigation/import/export probe transcript. |
| CSV `EXPORT` and matching-table `IMPORT` | Supported and transcript-proven | export probe and import probe v2 transcripts. |
| `BROWSE PAGE ... QUIET` and `BROWSE ALL QUIET` | Supported and transcript-proven for non-interactive listing | browse probe v1 transcript. |
| CNX tag order on v32/schema-created tables | Supported and transcript-proven | CNX order v1 transcript. |
| dBASE, Clipper, FoxPro, Visual FoxPro behavior beyond the tested command forms | Lineage/background only unless separately proven | case catalog and source harvest. |
| `DO X64` as setup/profile ceremony | Existing script vocabulary, but retired from the reader quickstart until an `X64.dts` profile is provided or a command form is proven | x64 walkthrough v1 transcript. |

## 4. Build and Run

Current proof-oriented runs should use the built executable:

```powershell
& D:\code\ccode\build\src\Release\dottalkpp.exe
```

Verification status: transcript-proven in the proof runs in `docs/manuals/developer/proofs`; the current Release executable path was used for those runs.

From the shell, use normal DotTalk++ commands interactively, or run repeatable command sequences through DotScript.

## 5. Shell Basics

The shell is the live command surface. Use it to open tables, inspect structures, add or edit records, build indexes, navigate records, and run scripts.

Useful readback commands after table or schema work include:

```text
STRUCT
FIELDS
LIST
TUPLE
STATUS
```

Use a readback command after every creation or mutation example. A command that creates a table is not fully proven until the table is opened and inspected.

## 6. DotScript

DotScript is the repeatable procedure layer for DotTalk++. Use it when a workflow needs to be replayed, reviewed, or captured as proof.

Use DotScript for:

- reproducible runtime procedures
- smoke tests
- schema and table creation candidates
- import/export experiments
- guarded maintenance execution
- command transcript generation
- repeatable proof capture

Run scripts from inside the DotTalk++ shell:

```text
DOTSCRIPT <file.dts>
DOTSCRIPT <file.dts> OUT <transcript-file>
DOTSCRIPT TRACE <file.dts> OUT <transcript-file>
```

Use `DOTSCRIPT ... OUT ...` when the result is meant to be reviewed later. The transcript is the evidence artifact.

DotScript comments are skipped when they begin with one of these prefixes after trimming:

```text
*
//
&&
;
```

Script resolution tries the typed path, then `.dts`, then `scripts/`, then `tests/`. Nesting is intentionally limited to a main script plus one subscript.

## 7. The x64 Workflow

Existing x64 scripts commonly begin with:

```text
DO X64
```

Treat `DO X64` as legacy/profile script vocabulary, not as the proven reader quickstart command. Do not remove it from existing x64 scripts as noise, but do not teach it as required for new readers until an `X64.dts` profile script or native command behavior is proven.

Current Release proof note: in the 2026-06-28 proof run, `DO X64` was interpreted through script resolution and reported `script not found` when no `X64.dts` profile script existed in the proof path. `CREATE X64` itself still created and opened v64 DBFs successfully. For now, document `DO X64` as legacy/profile ceremony used by existing scripts, and document `CREATE X64` as the proven table-creation command.

The reader-facing proven pattern is:

```text
CREATE X64 <table> (<field> <type>, <field> <type>, ...)
STRUCT
```

Concrete example:

```text
CREATE X64 DEV_STUDENTS (SID N(6,0), LNAME C(20), FNAME C(15), GPA N(4,2), ACTIVE L)
STRUCT
APPEND
REPLACE LNAME WITH "MARTIN"
REPLACE FNAME WITH "ADA"
REPLACE GPA WITH 3.75
REPLACE ACTIVE WITH .T.
LIST
```

Verification status: transcript-proven with `docs/manuals/developer/proofs/reader_manual_x64_walkthrough_v2.transcript.txt`.

Observed behavior from the proof:

- `CREATE X64 RM_X64_V2 (...)` created `D:\code\ccode\build\src\Release\dbf\RM_X64_V2.dbf`.
- The table opened immediately after creation.
- `STRUCT` showed the expected five fields.
- `APPEND` created an auto-numbered SID value.
- Character, numeric, and logical `REPLACE` commands ran.
- `LIST` and `STATUS` proved readback.

Do not use the older `REPLACE SID WITH 1001` pattern in the reader manual without another transcript. In the v1 proof, numeric SID replacement failed while the append path auto-assigned SID values.

Important `CREATE X64` behavior:

- `CREATE X64 <name> (...)` writes a DBF through the configured DBF path slot.
- It closes the current area before creating the table.
- It opens the new table after successful creation.
- It clears active order state.
- Memo fields attempt memo attach after open.
- Long or colliding field names may receive descriptor-safe fallback tokens while retaining authoritative logical names where supported.

### Theoretical Limits of x64base

x64base has two kinds of limits:

- Format limits: what the x64 file structures can theoretically describe.
- Runtime limits: what the current `DbArea`, loader, command surface, and proofed workflows can actually use today.

The x64 header extension in `include/xbase_64.hpp` is a 64-byte structure with 64-bit fields:

```text
record_count    uint64
data_start_64   uint64
record_size_64  uint64
autoq_next      uint64
```

That means the theoretical file-format direction is not the classic DBF ceiling. The design is aimed at very large record counts, large data offsets, large row geometry, and 64-bit autoincrement/sequence state.

Current runtime caveat: the loader validates the x64 extension, then mirrors `data_start_64` and `record_size_64` into current `DbArea` fields that are still constrained by compatible 16-bit ranges. `DbArea` also exposes 64-bit record number/count state, but legacy APIs clamp the visible 32-bit versions. So the theoretical x64base ceiling is 64-bit, while the current reader-proven runtime should be described as a compatibility-stage x64 implementation.

Reader rule: do not claim "unlimited" tables. Say x64base is designed around 64-bit record counts, offsets, record sizes, and sequence values, but current proven behavior is bounded by the active loader/runtime path.

### x64 Indexing Limits

x64 indexing has the same split.

For v64 tables, the proven reader workflow is:

```text
CDX container
LMDB backing environment
SET INDEX TO <table>.cdx
SET ORDER TO TAG <tag>
```

The logical xBase concept is still simple: records have physical order, and an index/tag supplies logical order. The x64 implementation can back that logical order with a CDX container and LMDB environment.

The theoretical limit of x64 indexing is therefore not just "how many records fit in an old `.idx` file." The direction is:

- many records addressed through 64-bit table state
- multi-tag logical containers
- backend index environments capable of scaling beyond flat legacy index assumptions
- physical backend hidden behind `SET INDEX` and `SET ORDER`

Current runtime caveat: the reader manual has proven CDX/LMDB ordering for a small v64 table and CNX ordering for a v32/schema-created table. It has not proven billion-row traversal, huge LMDB maps, multi-gigabyte index rebuilds, or all index families at x64 scale.

### x64 Memo Limits

x64 memos move away from old in-row memo text slots. `include/xbase.hpp` defines:

```text
LEGACY_MEMO_FIELD_LEN = 10
X64_MEMO_FIELD_LEN    = 8
```

The x64 memo slot is an 8-byte `uint64` object-id reference. The live memo backend is the DTX sidecar store. `include/memo/dtx_format.hpp` defines a `DTX1` file with:

```text
next_object_id       uint64
object_count_live    uint64
object_count_dead    uint64
first_object_offset  uint64
append_offset        uint64
payload_bytes        uint64
logical_bytes        uint64
previous_version_of  uint64
```

The theoretical direction is large memo object IDs, large append offsets, large payload sizes, tombstones, version chains, and future roots for index/free-list/metadata structures.

Current runtime caveat: the DTX backend is text-first, append-mostly, and keeps a live object map in memory after scan/open. The header comments explicitly defer free-space reuse and advanced repair. So x64 memos are architected for large-object sidecar storage, but the current reader manual should not claim mature garbage collection, compaction, free-list reuse, or huge-object operational proof until those paths are tested.

### Vectored Table Names and Field Names

Classic DBF/VFP descriptors have short compatibility names. In this codebase, descriptor field names remain 10-byte fallback tokens. x64base adds an optional metadata vector so the authoritative names can be longer and cleaner than the fallback descriptor tokens.

This feature exists because the project outgrew MS-DOS-era naming. Classic xBase systems were built around strict table and field-name limits, and the DBF descriptor still carries a short field-name slot for compatibility. Visual FoxPro opened parts of the model up, and DotTalk++ currently uses 128-byte x64 logical table and field names as its default policy. That 128-byte policy is not the theory of the format; it is the current compile-time contract.

SelfDoc and the Master Doc Organizer (MDO) made the need obvious. Documentation, provenance, command identity, source harvesting, and generated catalog tables naturally produce names such as `COMMAND_REFERENCE_ASSEMBLY_ALIAS_STATUS` or `MANUAL_GENERATION_ANCHOR_MAP_ENTRY`. Those names should explain themselves to the runtime and to future readers. Truncating them to 10-byte DBF tokens would destroy the meaning the system is trying to preserve.

In `include/xbase_64.hpp`:

```text
X64_TABLE_NAME_LENGTH = 128
X64_FIELD_NAME_LENGTH = 128
X64_TABLE_NAME_LENGTH_MAX = 128
X64_FIELD_NAME_LENGTH_MAX = 128
X64_FALLBACK_FIELD_TOKEN_BYTES = 10
```

Those values are C++ constants. A build can change the x64 vector-name policy by changing the compile-time constants and rebuilding, but that is a storage-contract change, not a cosmetic setting. Any longer-name build must also audit metadata serialization, loaders, command syntax, HELP/META rows, data dictionary tables, import/export, and proof scripts so the system agrees about the new maximum.

The optional metadata block is named `X64M`. It contains:

- table-name offset and length
- field-entry offset and count
- string-pool offset and length
- per-field metadata entries with field index, name offset, name length, flags, and field length

That is what "vectored table names and field names" means in this system: the short DBF/VFP descriptor token remains as compatibility fallback, while the x64 metadata vector carries the authoritative logical table name and field names.

The x64 DBF should therefore be self-describing. When `DBF64_FLAG_HAS_META_BLOCK` is set, the file carries the name vector needed to resolve its logical table and field names. In the current source, `X64M` is stored immediately after the descriptor terminator and before record data, with `data_start_64` and compatible header size pointing after that metadata. `X64MetaLocator` is reserved for later locator geometry. That means the current name-vector contract is header-resident metadata, not an external sidecar. Sidecar metadata could become a future extension, but it should be documented separately from the current in-file `X64M` block and from the DTX memo sidecar.

Example concept:

```text
Descriptor fallback token: CUSTOMER_O
Vector field name:        CUSTOMER_ORDER_HISTORY_STATUS
```

The runtime should resolve the vector name when `DBF64_FLAG_HAS_META_BLOCK` is present and the metadata is valid. If the metadata is missing, invalid, or the name is too long for the current contract, the system falls back to the descriptor token.

Reader rule: the vector name is the authoritative x64 name when present and valid. The 10-byte descriptor token is a compatibility fallback, not the real semantic name.

Developer rule: if the vector-name limit is raised beyond 128, the manual, data dictionary, HELP/META harvest, and proof suite must all be regenerated under the same compiled contract. A DBF created under a longer-name build should carry enough `X64M` metadata for the runtime to explain the file back to itself.

### Harvest Rule for Mentioned Concepts

This material should be harvested now because it was explicitly named and because the trinity headers already contain the contracts. It should also be harvested later by the systematic SelfDoc/manualgen path.

Immediate harvest captures the doctrine:

- x64base theoretical limits
- x64 indexing direction
- x64 memo direction
- vectored table and field names
- compile-time x64 vector-name policy
- self-describing x64 name metadata
- current runtime caveats

Systematic harvest should later attach source-level and runtime proof:

- source extraction from `include/xbase_64.hpp`, `include/xbase.hpp`, and `include/memo/dtx_format.hpp`
- proof scripts for 128-byte table/field names
- proof scripts for a deliberately longer compile-time vector-name build if the constants are changed
- proof scripts proving that a vectored DBF can explain its logical names from `X64M`
- proof scripts for x64 memo object IDs
- proof scripts for larger CDX/LMDB index scale
- reader-safe language once those paths are proven

## 8. Creating DBFs

There are two main creation paths:

- Direct x64 creation with `CREATE X64`.
- Schema-driven creation with `DDL CREATE DBF`.

Use direct creation when the table is small, local, and part of a runtime proof. Use schema-driven creation when the table contract must be explicit, reusable, or connected to data dictionary work.

Schema-driven pattern:

```text
DDL CREATE DBF <out.dbf> FROM <schema.json>
DDL CREATE DBF <out.dbf> FROM <schema.json> OVERWRITE
DDL CREATE DBF <out.dbf> FROM <schema.json> SEED BLANK <n>
DDL CREATE DBF <out.dbf> FROM <schema.json> EMIT SIDECARS
```

Path rules:

- Relative schema inputs resolve under the `SCHEMAS` path first, then the current working directory.
- Relative DBF outputs resolve under the `TMP` path by default.
- Existing DBF output is refused unless `OVERWRITE` is supplied.
- `SEED CSV` is recognized in the command surface but is not implemented in the current drop-in.
- `EMIT SIDECARS` writes companion schema/load/index metadata files.

Minimal schema shape:

```json
{
  "version": "1.0",
  "name": "students",
  "encoding": "UTF-8",
  "date_policy": "ISO",
  "null_policy": "EMPTY_AS_EMPTY",
  "logical_policy": "TF",
  "fields": [
    { "name": "SID", "type": "N", "length": 9, "decimals": 0, "required": true },
    { "name": "LNAME", "type": "C", "length": 20, "required": true, "trim": "right" },
    { "name": "FNAME", "type": "C", "length": 15, "required": true, "trim": "right" },
    { "name": "DOB", "type": "D", "length": 8, "zero_date": "ALLOW" },
    { "name": "ACTIVE", "type": "L" }
  ],
  "indexes": [
    { "name": "SID_PK", "engine": "CNX", "order": ["SID ASC"], "unique": true, "nullable": "DISALLOW" },
    { "name": "NAME1", "engine": "CNX", "order": ["LNAME ASC", "FNAME ASC"], "collation": "nocase", "trim": "right" }
  ]
}
```

The active schema contract is `src\cli\schema_json_v1.schema.json`. The `DDL CREATE DBF` schema path supports field types `C`, `N`, `D`, `L`, and `M`. Do not assume every direct `CREATE` type is valid in the JSON schema path.

Verification status: transcript-proven with `docs/manuals/developer/proofs/reader_manual_schema_ddl_v2.transcript.txt`.

Observed DDL proof:

- `DDL CREATE DBF RM_SCHEMA_V2.dbf FROM docs\manuals\developer\proofs\reader_manual_schema_v1.json OVERWRITE SEED BLANK 2 EMIT SIDECARS` succeeded.
- The relative DBF output resolved to `D:\code\ccode\build\src\Release\tmp\RM_SCHEMA_V2.dbf`.
- Opening the TMP output path succeeded.
- `STRUCT` showed the five schema fields.
- `LIST` showed two seeded blank rows.
- `STATUS` reported DBF flavor `v32` for the schema-created table.

Reader rule: after schema-driven creation, open the actual output path reported by DDL. A relative output name goes to the runtime `TMP` path, not the runtime `DBF` path.

## 9. Schema Rules

Classify a schema before using it:

| Schema kind | Meaning | Handling |
|---|---|---|
| `schema.json` | Table field/index/relation contract for DDL/import work. | Candidate until runtime-created and read back. |
| `.dtschema` / `.dtschemas` | x64base workspace/session schema for areas and optional relations. | Do not confuse with SQL schemas. |
| JSON Schema | Validator/specification for another artifact. | Use for structural validation, not runtime proof by itself. |
| Data dictionary package schema | Contract for generated reports/import candidates. | Keep package-local until promoted. |

Rules for schema work:

- Keep candidate schemas separate from active schemas.
- Never overwrite active schemas without an explicit promotion package.
- If a schema has indexes, also define how those indexes are created or activated at runtime.
- If a schema has relations, capture workspace/relation proof separately from table creation proof.
- A schema that parses is not proven.
- A schema is proven only after runtime creation, open, structure readback, and at least one navigation/readback command.
- For DBF work, prove with `STRUCT` and at least one data readback command.
- For index work, prove physical order versus logical order.

## 10. Indexes, CNX, CDX, and SET ORDER

The direct index command builds an INX file from the current open table.

Pattern:

```text
USE <table>
INDEX ON <field> TAG <name>
INDEX ON <field> TAG <name> DESC
INDEX ON <field> TAG <name> ASC 2INX
SET INDEX TO <name>.inx
```

Important rules:

- `INDEX` requires an open table.
- It reads records and writes an index file.
- It does not mutate table records.
- Deleted records are excluded.
- Default direction is `ASC`.
- Default output format is `2INX`.
- `TAG` names an INX file target.
- Non-`.inx` extensions are refused.
- Field-number tokens are accepted by the parser, but field names are clearer in docs and proof.

Index examples should prove both the underlying record data and the indexed navigation order.

### CNX, CDX, and LMDB Boundary

Keep the index terms distinct:

| Concept | Reader meaning |
|---|---|
| `INX` | Direct single index file path created by `INDEX ON ... TAG ...`, currently the simplest reader-facing index example. |
| `CNX` | DotTalk++ container concept for named tags and order metadata. Current tools include `CNX CREATE`, `CNX INFO`, `CNX TAGS`, `CNX ADDTAG`, `CNX DROPTAG`, `CNX WALK`, and `CNX TRACE`. |
| `CDX` | User-facing logical multi-tag index container concept. Current tools include `CDX CREATE`, `CDX INFO`, `CDX TAGS`, `CDX ADDTAG`, and `CDX DROPTAG`. |
| `LMDB` | Physical backend/index environment detail in some CDX paths. Do not expose it as the ordinary user concept unless the section is explicitly backend-facing. |

The reader model is:

```text
DBF/XDBF stores records.
CNX/CDX/INX describe or provide logical order.
SET INDEX attaches the container.
SET ORDER selects the active traversal order or tag.
LMDB may back a CDX path, but it is not the ordinary teaching abstraction.
```

### SET INDEX Versus SET ORDER

Use `SET INDEX TO <container>` to attach an index container. Use `SET ORDER` to choose the active logical traversal order.

Patterns:

```text
SET INDEX TO students.cdx
SET ORDER TO TAG LNAME
SET ORDER TO 0
SET ORDER PHYSICAL
```

Key distinction:

```text
INDEX creates an INX file from the current open table.
SET INDEX names or attaches the index container.
SET ORDER chooses the active logical traversal order.
```

Do not claim an index works until runtime output proves the order changed or a seek uses the expected access path. The important lesson is physical order versus logical order:

```text
physical record order
logical order
active tag/order
current cursor
filtered or predicate view
projected tuple output
persisted table state
buffered or dirty state
```

### Proven CDX Order Workflow

For v64 tables, the current proven order path is CDX plus LMDB backing store.

Transcript: `docs/manuals/developer/proofs/reader_manual_order_cdx_v2.transcript.txt`

Proof script: `docs/manuals/developer/proofs/reader_manual_order_cdx_v2.dts`

Pattern:

```text
CREATE X64 RM_ORDER_V2 (SID N(6,0), LNAME C(20), FNAME C(15), GPA N(4,2))
APPEND
REPLACE LNAME WITH "ZEKE"
APPEND
REPLACE LNAME WITH "ADAMS"
APPEND
REPLACE LNAME WITH "MARTIN"
GO TOP
LIST
CDX CREATE
CDX ADDTAG LNAME
CDX TAGS
BUILDLMDB YES
SET INDEX TO RM_ORDER_V2.cdx
SET ORDER TO TAG LNAME
GO TOP
LIST
SEEK "MARTIN"
RECNO
DISPLAY
SET ORDER TO 0
GO TOP
LIST
```

Observed proof:

- Physical order listed `ZEKE`, `ADAMS`, `MARTIN`.
- `CDX CREATE` created `RM_ORDER_V2.cdx` under the runtime `indexes` path.
- `CDX ADDTAG LNAME` added the `LNAME` tag.
- `BUILDLMDB YES` rebuilt the LMDB backing store and reported `done OK=1 tags rebuilt`.
- `SET INDEX TO RM_ORDER_V2.cdx` attached the CDX container.
- `SET ORDER TO TAG LNAME` selected the `LNAME` tag.
- Ordered `LIST` returned `ADAMS`, `MARTIN`, `ZEKE`.
- `SEEK "MARTIN"` found the record at physical recno 3.
- `SET ORDER TO 0` returned traversal to physical order.

Current caveat: the v1 proof showed that a v64 table refuses direct INX attachment with `SET INDEX: v64 tables require CDX (LMDB-backed)`. Keep INX examples for legacy/v32 or explicitly marked index-file examples until v64 INX behavior is separately proven.

### Proven CNX Order Workflow

For v32/schema-created tables, the current proven order path is CNX plus `REBUILD`.

Transcript: `docs/manuals/developer/proofs/reader_manual_order_cnx_v1.transcript.txt`

Proof script: `docs/manuals/developer/proofs/reader_manual_order_cnx_v1.dts`

Pattern:

```text
DDL CREATE DBF RM_CNX_V1.dbf FROM docs\manuals\developer\proofs\reader_manual_schema_v1.json OVERWRITE EMIT SIDECARS
USE D:\code\ccode\build\src\Release\tmp\RM_CNX_V1.dbf
IMPORT docs\manuals\developer\proofs\reader_manual_nav_export_v1.csv
GO TOP
LIST
CNX CREATE
CNX ADDTAG LNAME
CNX TAGS
REBUILD RM_CNX_V1.cnx
SET INDEX TO RM_CNX_V1.cnx
SET ORDER TO TAG LNAME
GO TOP
LIST
SEEK "CLARK"
RECNO
DISPLAY
SET ORDER TO 0
GO TOP
LIST
```

Observed proof:

- `DDL CREATE DBF` created a v32 table in the runtime `TMP` path.
- `IMPORT` loaded three records.
- `CNX CREATE` created `RM_CNX_V1.cnx` under the runtime `indexes` path.
- `CNX ADDTAG LNAME` added the `LNAME` tag.
- `REBUILD RM_CNX_V1.cnx` rebuilt the CNX container and reported `OK=1`.
- `SET INDEX TO RM_CNX_V1.cnx` attached the CNX container.
- `SET ORDER TO TAG LNAME` selected the CNX tag.
- `SEEK "CLARK"` found the matching row at record 2.

Reader rule: v32/schema-created DBFs can use CNX; v64 `CREATE X64` DBFs should use CDX/LMDB unless another path is separately proven.

## 11. Navigation, Search, and Browse

Navigation and search are transcript-backed by `docs/manuals/developer/proofs/reader_manual_nav_import_export_probe_v1.transcript.txt`.

Useful commands:

```text
USE
GO TOP
GO BOTTOM
SKIP
LIST
LOCATE
SEEK
BROWSE
SMARTLIST
```

Basic navigation pattern:

```text
GO TOP
RECNO
DISPLAY
SKIP
RECNO
DISPLAY
GO BOTTOM
RECNO
DISPLAY
```

Search/filter pattern:

```text
LOCATE FOR LNAME = "CLARK"
RECNO
DISPLAY
LOCATE FOR GPA >= 3.5
RECNO
DISPLAY
SMARTLIST SID,LNAME,FNAME,GPA NEXT 10
SMARTLIST SID,LNAME,FNAME,GPA NEXT 10 FOR GPA >= 3.0
```

Observed proof:

- `GO TOP`, `SKIP`, and `GO BOTTOM` moved through the three-record test table.
- `LOCATE FOR LNAME = "CLARK"` moved to the matching record.
- `LOCATE FOR GPA >= 3.5` found the first matching numeric predicate.
- `SMARTLIST` listed selected fields.
- `SMARTLIST ... FOR GPA >= 3.0` returned only matching rows.

Browse status: non-interactive BROWSE listing is transcript-backed by `docs/manuals/developer/proofs/reader_manual_browse_probe_v1.transcript.txt`.

Proven non-interactive browse pattern:

```text
GO TOP
BROWSE PAGE 2 QUIET
GO TOP
BROWSE ALL QUIET
```

Observed proof:

- `BROWSE PAGE 2 QUIET` rendered two tuple rows and returned to the script.
- `BROWSE ALL QUIET` rendered all rows and returned to the script.

Interactive `BROWSE`, `BROWSER`, and `BROWSETUI` remain separate terminal workflows. Do not promote interactive browse recipes until they are tested in a suitable terminal session.

## 12. Editing Data

Basic editing flow:

```text
APPEND
REPLACE <field> WITH <value>
LIST
```

For examples that matter, include a readback step after each mutation group. If buffering or transaction behavior is involved, the final manual should explain whether changes are immediate, buffered, committed, or rolled back.

## 13. Work Areas and Cursor Control

Anchor: `ANCHOR-CURSOR-WORKAREAS`

Maturity: M2 source-supported. The source and command surface are present; this section still needs current runtime transcripts before it becomes a promoted cursor tutorial.

DotTalk++ follows the xBase work-area model. A work area is an engine-owned table slot. Commands run against the current area unless they explicitly name another area or all areas.

Current source evidence:

- `src/cli/workareas.hpp` wraps engine-owned `DbArea` slots without taking ownership away from the engine.
- `src/cli/cmd_recno.cpp` implements `RECNO` as both a report command and a navigation command.
- Browser and status code report record number, deleted state, physical record, and logical row where available.

The reader-facing rule is simple:

```text
Open table -> current area -> current record -> command effect
```

Commands such as `LIST`, `REPLACE`, `LOCK`, `UNLOCK`, `COMMIT`, and `ROLLBACK` only make sense when the current area is clear. When proof scripts exercise cursor behavior, they should report the current record before and after mutation-sensitive commands.

Basic cursor pattern:

```text
USE CUSTOMER
RECNO
RECNO 3
LIST
RECNO
```

`RECNO` with no argument reports the current record number. `RECNO <n>` moves the cursor to record `n` and reports the resulting record number. It mutates cursor position but does not mutate table data.

Important manual distinction:

- Cursor movement changes what record is current.
- Record editing changes table data.
- Buffering may delay when edits become physical table data.
- Commit/rollback may preserve or discard buffered edits.
- Some commands restore the cursor best-effort after scans or aggregate operations.

Proof gap: this section is source-supported and command-supported, but still needs a dedicated transcript for current-area selection, `RECNO`, `GOTO`, `SKIP`, scan cursor restoration, and multi-area behavior.

Maturity target: M3 after `reader_manual_cursor_control_v1` proves cursor movement and readback; M4 after the section includes transcript paths and expected output.

## 14. Record and Table Locking

Anchor: `ANCHOR-LOCKING`

Maturity: M2 source-supported. `LOCK` and `UNLOCK` are implemented command surfaces with HELP messages, but this section still needs fresh lock transcripts before it is a full operational tutorial.

DotTalk++ has a locking surface for coordinating access to records and tables. The user-facing commands are:

```text
LOCK USAGE
LOCK
LOCK <n>
LOCK ALL
LOCK TABLE
LOCK STATUS
LOCK WHO <n>

UNLOCK USAGE
UNLOCK
UNLOCK <n>
UNLOCK ALL
UNLOCK TABLE
```

`LOCK` mutates lock state, not table data. `UNLOCK` releases lock state, not table data.

Reader-facing behavior from source:

- `LOCK` with no arguments locks the current record.
- `LOCK <n>` locks record `n`.
- `LOCK ALL` and `LOCK TABLE` lock the table.
- `LOCK STATUS` reports table lock state and current-record lock state.
- `LOCK WHO <n>` reports the recorded owner for a locked record.
- `UNLOCK` with no arguments unlocks the current record.
- `UNLOCK <n>` unlocks record `n`.
- `UNLOCK ALL` and `UNLOCK TABLE` release the table lock.

Operational pattern:

```text
USE CUSTOMER
RECNO 3
LOCK STATUS
LOCK
LOCK STATUS
REPLACE LNAME WITH "SMITH"
UNLOCK
LOCK STATUS
```

Commit-time locking matters. `COMMIT` applies buffered changes by locking each affected record at commit time. If a record cannot be locked, commit can be partial and the remaining buffered changes stay buffered so the user can retry.

Manual caveat: the command surface is supported in source and HELP messages, but this manual still needs fresh lock proof transcripts before presenting a full multi-user tutorial. Until then, locking prose should be direct but conservative.

Maturity target: M3 after `reader_manual_lock_unlock_v1` proves record lock, table lock, status, ownership, failed mutation under lock, and unlock readback.

## 15. Table Buffering

Anchor: `ANCHOR-TABLE-BUFFER`

Maturity: M2 source-supported. `TABLE BUFFER` and per-area buffer state exist; full reader promotion requires proof transcripts for staged changes, status/dump, commit, and rollback.

Table buffering lets DotTalk++ hold changes in a per-area buffer before they are physically applied to the DBF. It is one of the features that makes the system feel like a serious database runtime instead of a simple file editor.

Current command surface includes:

```text
TABLE BUFFER ON [PERSISTENT|RAM] [<n>|ALL|n,m,...]
TABLE BUFFER OFF [<n>|ALL|n,m,...]
TABLE BUFFER PERSISTENT [ON|OFF] [<n>|ALL|n,m,...]
TABLE BUFFER DIRTY [<n>|ALL|n,m,...]
TABLE BUFFER CLEAN [<n>|ALL|n,m,...]
TABLE BUFFER STALE [<n>|ALL|n,m,...]
TABLE BUFFER FRESH [<n>|ALL|n,m,...]
TABLE BUFFER STATUS [area|ALL]
TABLE BUFFER DUMP [area|ALL]
TABLE BUFFER TESTADD <recno> [flags] [field1] [value]
TABLE BUFFER RESET
```

The runtime model is per-area:

- enabled or disabled
- dirty or clean
- stale or fresh
- RAM-only or persistent-mode selection
- buffered change rows keyed by record number
- optional history mode where newer field changes win by priority

The current `TableBuffer` stores change entries by record number. A change can represent insert, update, or delete intent. Field-level changes store one-based field numbers and new values.

Reader-facing rule:

```text
TABLE BUFFER controls whether changes are staged.
COMMIT applies staged changes.
ROLLBACK discards staged changes.
```

Persistent buffering caveat: `src/cli/table_state.cpp` contains persistent journal hooks, but they are currently deliberate stubs. The manual should not claim crash-recovery journaling until a proof script shows journal creation, replay, commit closure, and rollback cleanup.

Maturity target: M3 after `reader_manual_table_buffer_commit_v1` and `reader_manual_table_buffer_rollback_v1` prove buffer state, physical readback, and rollback readback.

## 16. Commit and Rollback

Anchor: `ANCHOR-COMMIT-ROLLBACK`

Maturity: M2 source-supported. `COMMIT` and `ROLLBACK` have source-level contracts and command handlers; promoted reader workflows need current transcripts.

`COMMIT` and `ROLLBACK` define the lifecycle of buffered changes.

`COMMIT` usage:

```text
COMMIT USAGE
COMMIT
COMMIT ALL
COMMIT MANUAL
COMMIT INTERACTIVE
COMMIT AUTO
COMMIT ALL MANUAL
COMMIT ALL INTERACTIVE
COMMIT ALL AUTO
```

`ROLLBACK` usage:

```text
ROLLBACK USAGE
ROLLBACK
ROLLBACK ALL
```

`COMMIT` applies buffered table changes for the current area, or for all open buffered areas when `ALL` is supplied. It locks affected records at commit time. If all buffered record applications succeed, it clears the buffer, clears dirty/stale state, flushes memo changes when a memo manager is present, and runs only the appropriate legacy index maintenance path.

Important commit policy:

- `COMMIT` does not rebuild CDX/LMDB containers.
- CDX/LMDB update lifecycle belongs to runtime mutation hooks.
- CNX remains rebuild-based.
- INX/IDX remains reindex-based.
- `MANUAL`, `INTERACTIVE`, and `AUTO` are accepted for compatibility, but do not make `COMMIT` rebuild CDX/LMDB.

Partial commit is possible. If one or more records cannot be applied, successful records are committed and failed record changes remain buffered. The user can inspect the state, unlock or resolve the conflict, and retry `COMMIT`.

`ROLLBACK` discards buffered/uncommitted changes. `ROLLBACK` without arguments clears the current area's buffered state. `ROLLBACK ALL` clears buffered state across all areas. It mutates buffer state and dirty/stale flags, but it does not mutate physical table data.

Professional manual rule: every buffering example must end with either `COMMIT` plus readback or `ROLLBACK` plus readback. A database manual that teaches buffering without closure teaches unsafe habits.

Maturity target: M3 after successful commit, rollback, and partial-conflict transcripts exist; M4 after the manual includes expected output and recovery steps.

## 17. Operational Safety Checklist

Anchor: `ANCHOR-TABLE-BUFFER`, `ANCHOR-COMMIT-ROLLBACK`, `ANCHOR-LOCKING`, `ANCHOR-CURSOR-WORKAREAS`

Maturity: M1 anchored checklist. This is a reader-facing safety frame; each individual command still matures through its own proof transcripts.

Before running a data-changing command, identify five states:

| State | Question |
|---|---|
| Current area | Which table slot is active? |
| Current record | Which record will record-oriented commands affect? |
| Lock state | Is the record or table locked, and by whom? |
| Buffer state | Are changes immediate or staged in `TABLE BUFFER`? |
| Index/order state | Is logical order controlled by CNX, CDX, INX, IDX, or physical order? |

Safe mutation pattern:

```text
USE <table>
RECNO
LOCK STATUS
TABLE BUFFER STATUS
<mutation command>
<readback command>
COMMIT
<readback command>
UNLOCK
```

Safe rollback pattern:

```text
USE <table>
TABLE BUFFER ON
<mutation command>
TABLE BUFFER DUMP
ROLLBACK
LIST
TABLE BUFFER STATUS
```

Reader rule: never treat a mutation as complete until the intended closure is visible. For immediate edits, closure is physical readback. For buffered edits, closure is `COMMIT` plus readback or `ROLLBACK` plus readback.

Operational caveats:

- A cursor move can change which record is edited.
- A lock can prevent a commit from applying all buffered records.
- A partial commit leaves failed changes buffered.
- `ROLLBACK` discards buffered changes; it does not undo already committed physical table changes.
- `COMMIT` does not rebuild CDX/LMDB containers; their lifecycle belongs to mutation hooks.
- Persistent buffer journal recovery is future/stubbed until proven.

This checklist should eventually become a full Database Administration Guide chapter with transcripts for normal operation, lock conflict, partial commit, rollback, and recovery cases.

## 18. Import and Export

CSV export and import are now transcript-backed.

Export transcript: `docs/manuals/developer/proofs/reader_manual_nav_import_export_probe_v1.transcript.txt`

Import transcripts:

- `docs/manuals/developer/proofs/reader_manual_import_probe_v1.transcript.txt`
- `docs/manuals/developer/proofs/reader_manual_import_probe_v2.transcript.txt`

HELP reports:

```text
IMPORT <csv>
EXPORT <csv>
```

Export pattern:

```text
EXPORT docs\manuals\developer\proofs\reader_manual_nav_export_v1.csv
EXPORT TO docs\manuals\developer\proofs\reader_manual_nav_export_to_v1.csv
```

Observed export proof:

- `EXPORT <csv>` wrote three records to the target CSV.
- `EXPORT TO <csv>` also wrote three records.
- The exported file contained the header `SID,LNAME,FNAME,GPA` and three rows.

Import pattern:

```text
CREATE X64 RM_IMPORT_V2 (SID N(6,0), LNAME C(20), FNAME C(15), GPA N(4,2))
IMPORT docs\manuals\developer\proofs\reader_manual_nav_export_v1.csv
STRUCT
LIST
STATUS
```

Observed import proof:

- `IMPORT <csv>` with no open table did not create a table; the transcript reported `No file open`.
- After creating and opening a matching x64 table, `IMPORT <csv>` reported `Imported 3 records`.
- `STRUCT`, `LIST`, and `STATUS` confirmed the imported table and record count.

Reader rule: import requires an open compatible table. Export requires an open table and writes CSV.

## 19. Commands and Functions Reference

The command and function reference must be generated from the system catalogs, not hand-invented from memory.

Current anchors:

- `ANCHOR-HELP-COMMANDS`: `dottalkpp/data/help/COMMANDS.dbf`
- `ANCHOR-HELP-CMDARGS`: `dottalkpp/data/help/CMD_ARGS.dbf`
- `ANCHOR-HELP-TOPICS`: `dottalkpp/data/help/HELP_TOPIC.dbf`
- `ANCHOR-HELP-ARTIFACTS`: `dottalkpp/data/help/HELP_ARTIFACTS.dbf` and `dottalkpp/data/help/HELP_ARTIFACTS.dtx`
- `ANCHOR-META-COLLECT`: META semantic facts and comparison output.
- `ANCHOR-CMDHELPCHK`: HELP/META validation.
- `ANCHOR-RUNTIME-PROOFS`: transcript-backed behavior.
- `ANCHOR-COMMAND-USAGE-HARVEST`: source-local `@dottalk.usage v1` blocks and nearby command comments.

Current command-reference artifacts:

- `DOTTALKPP_COMMAND_REFERENCE_GUIDE_V1.md`: readable source-contract guide with one selected entry per command declaration where possible.
- `docs/manuals/command_reference/COMMAND_REFERENCE_USAGE_CONTRACT_HARVEST_V1.md`: raw source harvest preserving all usage blocks.
- `docs/manuals/command_reference/command_reference_guide_v1.csv`: structured selected guide rows.
- `docs/manuals/command_reference/command_reference_usage_contract_harvest_v1.csv`: structured raw harvest rows.
- `docs/manuals/developer/manualgen/accepted_docs/man_cli_v1/manualgen_man_cli_command_reference.md`: existing manualgen CLI command reference.

The reader-facing reference should be generated with one row per command, function, or operator identity:

```text
primary_name
kind
aliases
syntax
arguments
help_topic
meta_identity
proof_status
reader_status
manual_section
```

Reader status should use these values:

| Status | Meaning |
|---|---|
| `promoted` | Safe to describe as a normal user command because HELP/META and runtime proof agree. |
| `documented` | Appears in HELP/META and can be described, but still needs a fresh proof transcript. |
| `developer` | Useful to maintainers, but not a normal reader command. |
| `legacy` | Compatibility or historical surface; explain only with caveats. |
| `deferred` | Known name, but not enough evidence for reader-facing documentation. |

The first generated pass should focus on commands already used in this manual: `CREATE X64`, `DDL CREATE DBF`, `USE`, `STRUCT`, `FIELDS`, `LIST`, `APPEND`, `REPLACE`, `RECNO`, `LOCK`, `UNLOCK`, `TABLE BUFFER`, `COMMIT`, `ROLLBACK`, `IMPORT`, `EXPORT`, `BROWSE`, `SET INDEX`, `SET ORDER`, `DOTSCRIPT`, and `HELP`.

Functions and expression operators should follow the same rule: catalog first, proof second, reader prose third. If a function appears in a catalog but has no current proof example, it belongs in the generated reference with `reader_status=documented` or `deferred`, not in tutorial prose.

## 20. LabTalk Case Catalog

LabTalk is an optional educational overlay for DotTalk++ and x64base. It should help readers understand why data systems, DBF records, indexes, schemas, and runtime proof matter.

The current case catalog lives under:

```text
docs/cases
```

The catalog currently includes:

- 15 runtime-readable `CASE_*.md` files
- `CASE_FRAMEWORK.md`
- `REGISTRY_CASES_v0.csv`
- `REGISTRY_CASES_v0.md`
- `MEDIA_ASSET_REGISTRY_v0.csv`
- runtime proof scaffolds for engineering cases

First-wave review candidates:

- HIST-000 The Data Trail Overview
- HIST-020 JUMPS / 73C Army System
- HIST-030 Unisys / CODASYL at ALCOA
- HIST-040 xBase as a Major Platform
- HIST-090 DotTalk++ / LabTalk and the AI Future

Boundary rule: LabTalk case files are optional. Core x64base and professional DotTalk++ runtime behavior must remain usable without case media, storyboards, or source document files.

## 21. Troubleshooting

Use this checklist before changing code or docs:

- Can the executable be found at the expected path?
- Does the command appear in HELP or the command registry?
- Is a table open before table-dependent commands run?
- Did the script run through `DOTSCRIPT ... OUT ...`?
- Did the workflow produce a transcript?
- Did table creation include `STRUCT`, `FIELDS`, `LIST`, `TUPLE`, or `STATUS` readback?
- Did index creation prove logical order and table contents separately?
- Did `SET INDEX` attach the intended container?
- Did `SET ORDER` select the intended tag or return to physical order?
- Are CNX/CDX described as user-facing logical containers and LMDB as backend detail?
- Is the schema a candidate, active contract, workspace schema, JSON Schema, or package-local schema?
- Is the xBase/FoxPro material runtime-supported, source-supported, or only lineage/background?
- Is the material reader-facing, or should it live in the developer appendix?

## 22. Developer Appendix

The following material is important for maintainers but should not dominate the reader body:

- MAN* catalog internals
- manualgen lifecycle
- maintenance package and MDO terminology
- drift/canary/review notes
- harvest manifests
- raw proof logs
- deferred command-family reviews

Current manualgen caveat: `manual catalog status` reported `DRIFT` because the accepted MAN* DBFs also appear as duplicate `EXTRA_MAN_DBF` rows. The expected table counts passed. Treat this as a catalog visibility issue until repaired or explicitly waived.

## 23. Evidence Anchors and Manual Generation

This manual now uses `DOTTALKPP_MANUAL_ANCHOR_MAP_V1.md` as the bridge between bottom-up harvest evidence and top-down reader prose.

It uses `DOTTALKPP_MANUAL_PROSE_GUIDE_V1.md` as the rulebook for turning those anchors into readable orientation, tutorial, reference, concept, caveat, handoff, and data dictionary prose.

The core pipeline is:

```text
Source contracts
  -> HELP DBFs and metadata
  -> META/selfdoc inventories
  -> cmdhelpchk and maintenance validation
  -> runtime proof transcripts
  -> manualgen reviewed/published artifacts
  -> reader manual, developer manual, data dictionary
```

Reader-facing claims should be promoted from anchors, not from memory. The important current anchors are:

- `ANCHOR-X64-TRINITY`: `include/xbase.hpp`, `include/xbase_vfp.hpp`, and `include/xbase_64.hpp`.
- `ANCHOR-X64-VECTOR-NAMES`: x64 vectored table and field names.
- `ANCHOR-X64-INDEXING`: CNX/CDX/SET ORDER behavior and x64 indexing direction.
- `ANCHOR-X64-MEMOS`: x64 memo structure and limits.
- `ANCHOR-HELP-COMMANDS`, `ANCHOR-HELP-CMDARGS`, `ANCHOR-HELP-TOPICS`, `ANCHOR-HELP-ARTIFACTS`: HELP DBF surfaces.
- `ANCHOR-META-COLLECT`: semantic collection facts and comparison outputs.
- `ANCHOR-CMDHELPCHK`: HELP/META validation.
- `ANCHOR-SELFDOC-POLICY`: provenance and collection policy.
- `ANCHOR-MANUALGEN-LIFECYCLE` and `ANCHOR-MANUALGEN-CATALOG`: publication lifecycle and catalog state.
- `ANCHOR-DATADICT-SCHEMAS`: data dictionary schema and proof reports.
- `ANCHOR-RUNTIME-PROOFS`: transcript-backed command paths.
- `ANCHOR-CURSOR-WORKAREAS`: work areas and cursor control.
- `ANCHOR-LOCKING`: record and table locking.
- `ANCHOR-TABLE-BUFFER`: table buffering.
- `ANCHOR-COMMIT-ROLLBACK`: commit and rollback lifecycle.
- `ANCHOR-MANUAL-DIAGRAMS`: simple SVG diagrams and their registry.

The diagram registry is a visual companion to this anchor map. Diagrams may clarify architecture, harvest flow, locking, buffering, indexing, memo storage, and manual maturity, but they do not raise a claim's proof level by themselves. A visual should inherit the maturity state of the section and anchors it explains.

The next command/function manual pass should generate a skeleton from HELP plus META with these columns:

```text
command_id
primary_name
aliases
argument_rows
help_topic
meta_identity
proof_status
manual_section
reader_status
```

The simple usage-contract harvest is the first direct source-backed seed for that reference. It does not replace HELP/META/manualgen. It gives the manual a practical per-command prose source: usage contract, purpose, notes, risk/mutation profile, related commands, and nearby source comments.

That is the point where the richly cataloged system starts producing a reader-facing command and function reference instead of only a developer harvest ledger.

Prose rule: catalogs identify what exists, anchors identify what is safe to say, and prose explains why a reader should care and what they should do next.

## Proof Artifacts

Reader manual proof scripts and transcripts live in `docs/manuals/developer/proofs`.

Key transcripts:

- `reader_manual_x64_walkthrough_v2.transcript.txt`
- `reader_manual_order_cdx_v2.transcript.txt`
- `reader_manual_order_cnx_v1.transcript.txt`
- `reader_manual_browse_probe_v1.transcript.txt`
- `reader_manual_nav_import_export_probe_v1.transcript.txt`
- `reader_manual_import_probe_v1.transcript.txt`
- `reader_manual_import_probe_v2.transcript.txt`
- `reader_manual_schema_ddl_v2.transcript.txt`

Known caveat transcripts:

- `reader_manual_x64_walkthrough_v1.transcript.txt`: shows `DO X64` resolving as a missing script when no `X64.dts` profile exists.
- `reader_manual_order_cnx_cdx_v1.transcript.txt`: shows v64 direct INX attach refused, CNX path not proven, and CDX requiring an LMDB build step.
- `reader_manual_schema_ddl_v1.transcript.txt`: shows DDL succeeded but bare `USE RM_SCHEMA_V1.dbf` searched the DBF path instead of the TMP output path.

## Publication Notes

This v1 manual promotes the transcript-backed command paths only. Interactive `BROWSER` and `BROWSETUI` are intentionally not promoted here; this manual covers non-interactive `BROWSE` listing.

`DO X64` is preserved as legacy/profile script vocabulary, but the reader quickstart uses proven `CREATE X64` directly. If an `X64.dts` profile script is later restored or a native command form is proven, this manual can add it back to the quickstart.
