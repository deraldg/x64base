# DotTalk++ / x64base

**Open, inspect, index, relate, and script DBF-family data with a modern C++20 runtime.**

[![CI](https://github.com/deraldg/x64base/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/deraldg/x64base/actions/workflows/ci.yml)

> **Current state:** active beta research software. The public `main` branch is
> the canonical collaboration and release branch. No production-readiness or
> cross-format atomic-transaction guarantee is made.

DotTalk++ / x64base is a working beta research and teaching system for DBF-style database ideas: tables, records, fields, work areas, indexes, memos, relations, metadata, HELP, scripts, browsers, and GUI/TUI experiments.

It is not currently presented as a finished commercial database product or a drop-in clone of Visual FoxPro, Harbour, Alaska Xbase++, or dBASE. It is a lineage evolution: a modern C++ architecture that preserves the visible, teachable parts of xBase while exploring larger DBF-family structures, self-documenting metadata, and repeatable educational workflows.

```text
USE students
SET ORDER TO TAG lname
SEEK "WHITE"
SMARTLIST NEXT 5
```

## Website

The public documentation site is now live:

**https://x64base.com/**

Start here:

- [Documentation](https://x64base.com/docs/)
- [Getting Started](https://x64base.com/docs/getting-started/overview/)
- [Engine Feature Crosswalk](https://x64base.com/docs/engine/feature-crosswalk/)
- [x64 Capacity Math](https://x64base.com/docs/engine/x64-capacity-math/)
- [xBase Ecosystem Feature Comparison](https://x64base.com/docs/engine/ecosystem-feature-comparison/)
- [DotScript Language Guide](https://x64base.com/docs/dottalk/dotscript-language-guide/)
- [Data Mutators](https://x64base.com/docs/dottalk/data-mutators/)
- [Historical Source Lineage](https://x64base.com/docs/dev/historical-source-lineage/)

The website is the preferred public manual. This repository is authoritative
for public source, build instructions, tests, licensing, and releases. Website
claims should cite a commit, test, or clearly labeled planned lane.

## Current Position

DotTalk++ / x64base is active beta. Some features are runtime-evidenced, some are source-evidenced, and some are planned lanes. The documentation separates those categories instead of flattening everything into a finished-product claim.

Current proven or active areas include:

- DBF-style table runtime with `DbArea` objects, cursor state, records, fields, and structure inspection.
- Workspaces as wrappers over active areas, preserving table, cursor, relation, index, memo, and metadata state.
- DBF flavor trinity: classic/MS-DOS-style DBF, Visual FoxPro DBF, and x64 `DBF_64` work.
- Visual FoxPro-style field/data type compatibility work, including currency-oriented support.
- x64 DBF extension work, including wider headers, vector table/field naming, and fallback descriptor tokens.
- Object-oriented memo architecture through memo refs, managers, objects, and stores.
- CDX/CNX/INX/LMDB index lanes, with V32 and V64 default index behavior documented on the site.
- Record navigation, filtering, searching, seeking, cursor control, and relation traversal.
- Record locking, buffered editing, dirty/stale state, commit/rollback, and mutation-sensitive commands.
- DotScript command files with variables, comments, line continuation, conditionals, loops, scans, and one-level subscript nesting.
- CSV import/export to and from DBF workflows.
- DDL schema fetch/validate/create DBF surfaces, with implementation caveats documented.
- HELP, CMDHELP, CMDHELPCHK, MAINT, DDICT, MANUAL, Blackbox, SelfDoc, MDO, contracts, and manual-generation lanes.
- Education commands and labs such as ASCII, SHELLO, RETRO, IDX, COBOL, CODASYL, NORMALIZE, and related teaching surfaces.
- Parallel GUI/TUI workbench lanes, including wxWidgets GUI work and Arctic as the TUI code name.
- Website documentation generated and curated from the same broader documentation system.

## What This Is

DotTalk++ / x64base is:

- a DBF-family runtime and command shell;
- a teaching system for database literacy;
- a self-documenting runtime and metadata experiment;
- a workspace and relation exploration environment;
- a cross-platform architecture lane for Windows, WSL/Linux, and Mac targets;
- a research system for x64 DBF-style storage, memos, indexes, and metadata.

It is designed to make database layers visible:

```text
tables -> records -> fields -> indexes -> memos -> work areas
      -> relations -> commands -> scripts -> metadata -> HELP
      -> manuals -> website
```

## Core Architecture

The project is organized around separate responsibilities:

| Layer | Responsibility |
| --- | --- |
| `xbase` | DBF table runtime, `DbArea`, records, cursor state, field metadata, table flavors |
| `xindex` / `cdx` / `cnx` | Index containers, tag/order behavior, backend index work |
| `memo` | Memo references, managers, objects, stores, verification |
| `cli` | DotTalk++ command surface, DotScript, HELP, DDL, browsers, mutations |
| `tuple` / relation code | Relation traversal, tuple projection, browser feeds |
| `tv` / GUI lanes | Arctic TUI, wxWidgets workbench, GUI/TUI bridging |
| `tools` / `docs` / SelfDoc | contracts, manual generation, metadata reports, publication feeds |

The design rule is:

```text
Conventions suggest.
Registration declares.
Metadata records.
Runtime proves.
Validators enforce.
```

## DBF and x64 Direction

x64base does not claim that every current command path is unlimited or fully widened. The x64 work is documented honestly:

- x64 table headers carry 64-bit record-count and geometry fields.
- Current shared runtime paths still have some compatibility gates that must be audited and widened.
- x64 memo work uses 64-bit object identifiers and offsets.
- x64 metadata supports richer table and field names while keeping classic descriptor fallback tokens.
- Index work must be audited backend by backend for true 64-bit record payloads and offsets.

See [x64 Capacity Math](https://x64base.com/docs/engine/x64-capacity-math/) for the lesson and matrix on why x32-to-x64 changes the engineering math.

## DotTalk++ Command Surface

Representative command families include:

```text
USE, SELECT, AREA, DBAREA, DBAREAS, STRUCT, FIELDS
TOP, BOTTOM, SKIP, GOTO, RECNO, SEEK, FIND, LOCATE
SET INDEX, SET ORDER, SET FILTER, SET RELATION, SET TABLE BUFFER
REPLACE, CALC, CALCWRITE, MULTIREP, COMMIT, ROLLBACK
REL, RELATIONS, ERSATZ, TUPLE, TUPEXPORT
LIST, SMARTLIST, SMARTBROWSE, SB, SIMPLEBROWSE
IMPORT, EXPORT, IMPORTSQL, EXPORTSQL, COPY
DDL, SQL, SQLITE
HELP, CMDHELP, CMDHELPCHK, MAINT, DDICT, MANUAL, BBOX
ASCII, SHELLO, RETRO, IDX
EDIT, TEXT, IMAGE, WEB, URL, SFTP, ZIP, PSHELL
```

`SB` is an alias for SmartBrowser. `SMARTLIST` is the table-aware listing surface. `TableTalk` refers to table buffering and dirty/stale table state, not generic table manipulation.

## DotScript

DotScript is the repeatable script form of the DotTalk++ command language. Current documentation covers:

- command files;
- variables;
- comments;
- line continuation;
- `IF` / `ELSE` / `ENDIF`;
- `LOOP` / `ENDLOOP`;
- `WHILE` / `ENDWHILE`;
- `UNTIL` / `ENDUNTIL`;
- `SCAN` / `ENDSCAN`;
- one-level subscript nesting;
- CSV/DBF import-export workflows.

DotScript can write programs that operate on data. A general application UI-definition language for menus, windows, dialogs, buttons, and events is a planned lane, not current runtime syntax.

## Parallel GUI/TUI

The user-facing workbench direction is documented as **Parallel GUI/TUI**.

- DotTalk++ Workbench is the family group.
- Arctic is the TUI code name.
- wxWidgets is the current C++ GUI lane.
- Python/Tk has been used as a mirror/prototype lane.
- GUI/TUI surfaces should share the same engine truth: areas, table state, relations, indexes, memos, commands, and scripts.

The planned Application UI DSL lane is tracked here:

- [Application UI DSL Lane](https://x64base.com/docs/dev/application-ui-dsl-lane/)

## SelfDoc and Documentation

The project is building a self-documentation system with a Master Documentation Organizer. The goal is for commands, functions, comments, contracts, HELP metadata, manuals, diagrams, and the website to form a repeatable publication chain.

The website is part of the product: x64base.com is an x64base publication surface. It is currently curated from the documentation system and should increasingly be fed by vertical content generation from SelfDoc/manual outputs.

Important documentation lanes:

- [SelfDoc Website Publication](https://x64base.com/docs/dev/selfdoc-website-publication/)
- [SelfDoc Feed Pipeline](https://x64base.com/docs/dev/selfdoc-feed-pipeline/)
- [Important Documents](https://x64base.com/docs/dev/important-documents/)
- [Historical Source Lineage](https://x64base.com/docs/dev/historical-source-lineage/)

## Historical Lineage

The project has historical roots in earlier ANSI C xBase/DotTalk work from the 1990s and later recovery branches. Those historical sources are being inventoried separately from modern DotTalk++ and from recent AI-assisted false starts.

The current preservation lane records source families, checksums, evidence labels, and feature tags so historical code can be studied without confusing it with current runtime truth.

## Quick Start

Requirements for the portable core build:

- CMake 3.21 or newer;
- a C++20 compiler;
- Ninja or another supported CMake generator.

```sh
cmake --preset core
cmake --build --preset core
ctest --preset core
```

The core preset disables optional TUI, GUI, Python, and LMDB-backed index
commands. LMDB itself remains a baseline dependency because the runtime
message catalog maintains LMDB mirrors. Enable optional surfaces explicitly
through the documented presets or CMake options. See
[`docs/getting-started/BUILDING.md`](docs/getting-started/BUILDING.md) for
Windows, Linux/WSL, macOS, and vcpkg instructions.

## Public Project Model

- `main` is the canonical public source, CI, and release branch.
- Feature and research branches may run ahead, but are not public runtime truth
  until promoted through a reviewed pull request.
- Local implementation or staging directories are maintainer workflow details,
  not alternate public authorities.
- Releases identify the commit, supported build profile, artifacts, checksums,
  and known limitations.

See [`docs/PUBLIC_PROJECT_MODEL.md`](docs/PUBLIC_PROJECT_MODEL.md).

## Status Language

Use these terms when describing the project:

- **runtime-evidenced**: command/source behavior has been observed or tested.
- **source-evidenced**: source structures exist, but public behavior needs review or proof.
- **active beta**: usable but still changing.
- **canary**: implemented or staged but not yet stable enough to present as finished.
- **planned lane**: design direction, not runtime syntax or finished behavior.

Avoid calling x64base:

- a finished commercial DBMS;
- a full Visual FoxPro clone;
- a drop-in Harbour/Xbase++ replacement;
- unlimited scale;
- fully compatible with every DBF/xBase dialect.

## Author

Derald Grimwood  
B.S. Management Information Systems  
xBase / SAP / ERP background

## License

The repository contains a **tentative MIT license** pending final maintainer and
legal review. See [`LICENSE`](LICENSE). The tentative label is intentional and
must remain visible until the review is complete.

## Final Note

> Preserve the past. Teach the layers. Fix the architecture. Move forward.
