# x64base Engine and Product-Edition Separation Plan v1

Status: **implemented; core build, runtime, and package matrix proven**  
Created: 2026-07-14  
Authority: DotTalk++ SDLC for runtime/build work; PLDC for product editions  
Companions:

- `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`
- `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md`
- `docs/datadict/specs/DD-004_DD004_BUILD_PROFILE_OVERLAY_AUDIT_v0.md`
- `docs/datadict/specs/DD-001_DD001_ENGINE_BOUNDARY_AND_PROFILES_v0.md`
- `docs/contracts/DOTTALK_EXTENSION_EXIT_CONTRACT_V1.md`
- `labtalk/ai_portal/PROMOTION_MODEL_SEED_V1.md`

## Decision in one page

Do not conflate **lean**, **no-index**, and **professional**. They answer
different questions and must be independent build axes. Project licensing:
**To be determined.**

| Axis | Question | Proposed values |
| --- | --- | --- |
| Engine capability | Which physical/index services exist? | `TABLE_ONLY`, `LEGACY_INDEX`, `FULL_INDEX` |
| Product edition | Which runtime/content components ship? | `LEAN`, `PROFESSIONAL`, `EDUCATIONAL`, `DEVELOPMENT` |
| Front end | Which consumers are built? | CLI, `pydottalk`, Turbo Vision, wxWidgets |
| Project licensing | Under what terms may each artifact be used? | To be determined. |

The product-facing names map directly to the proposed build values:
`TABLE_ONLY=NONE`, `LEGACY_INDEX=LEGACY`, and `FULL_INDEX=LMDB`.

The recommended first customer-facing baseline is **LEAN + FULL_INDEX**, not
TABLE_ONLY. It gives a smaller, neutral product without silently removing a
fundamental database capability. `TABLE_ONLY` should first become an honest,
tested engine profile and a useful embedded/API option. It should not become
the default product merely because the current index lane is weakly proven.

The recommended education split is:

- `EDU_ESSENTIALS`: small, neutral onboarding/reference material that may ship
  with LEAN.
- `LABTALK_FULL`: campus, cases, history, student extensions, course projects,
  and large teaching datasets. This is an optional product/content pack.

The implemented component boundary is:

```text
xbase_core (table and record engine)
    <- xindex_legacy (CNX/CDX/order services)
        <- xindex_lmdb (LMDB-backed services)

dottalk_runtime_core
    + selected index provider
    + selected product components
    + selected front end(s)
```

`xbase_core` must not link to `xindex`. `xindex` may link to the stable xbase
engine interface. The executable and Python module are composition roots.
`pydottalk` is a binding over the engine; xbase is not a subset of a
`pydottalk.exe` product.

## What the deeper audit found and what changed

### 1. A real table-only binary now exists

The original audit found this two-way dependency shape:

- `src/xbase/CMakeLists.txt` publicly links `xbase` to `xindex` whenever that
  target exists.
- `src/CMakeLists.txt` always adds `xindex` before `xbase`.
- `DbArea` owns a concrete `xindex::IndexManager` and constructs it in xbase
  sources.
- replace, close, open, record-write, and key-codec paths refer directly to
  xindex types or functions.
- xindex implementations in turn consume `xbase::DbArea`.

`DOTTALK_WITH_INDEX=OFF` currently means approximately **xindex without the
direct LMDB backend source**. It does not mean **no xindex library**. Also, the
main `dottalkpp` target requires LMDB unconditionally for message-catalog
mirrors, so a no-index command surface is still not a no-LMDB product.

The implementation inverted that dependency. `xbase` now owns only neutral,
opaque optional-provider hooks; `xindex` attaches managers above it. A clean
`LEAN + NONE` build produces both `pydottalk` and `dottalkpp.exe` without an
`xindex` target or `xindex.lib`. Physical DBF reads, disposable-copy CRUD, and a
CLI `USE ... NOINDEX` runtime smoke pass. Index-only commands are absent.

The CLI still links LMDB for the independent runtime message catalog. Thus
`NONE` means no index engine, not yet a generally LMDB-free executable.

### 2. Product composition now gates source and command registration

The original `DOTTALK_WITH_EDUCATION` boolean was inert. It is now a derived
compatibility output of `DOTTALK_PRODUCT`. `LEAN` keeps the small essentials
set (`ASCII`, `EXAMPLE`, `BOOLEAN`, `FORMULA`, `EVALUATE`, `NORMALIZE`, `EDIT`,
and `TEXT`) while excluding full LabTalk, seasonal, Bible, ERP, MCC, history,
external-tool, and maintenance registration/source groups.

The main executable is built from a recursive source glob. At the time of this
audit, the glob's effective main-source candidate set was approximately:

| Source family | Candidate translation units | Approximate source size |
| --- | ---: | ---: |
| `src/cli` | 354 | 3,075 KiB |
| `src/edu` | 19 | 148 KiB |
| `src/ext` | 3 | 10 KiB |
| all main-target families | 430 | 4,131 KiB |

The exact final compiler list differs slightly because CMake later removes a
few known demo/main files. The important fact is that `src/edu` and `src/ext`
are not excluded or componentized.

The central shell registry contains 223 observed `registry().add` calls. It has
guards for several index, relation, and UI commands but no education guard.
Examples of unguarded education/history surfaces include `BIBLETALK`, `ERP`,
`CASE`, `COBOL`, `CODASYL`, `DRAWIO`, `RETRO`, `ASCII`, `CHRISTMAS`,
`HANUKKAH`, and the expression-teaching handlers. Student extension examples
self-register because their sources are compiled into the main executable.

The prior DD-004 report correctly found the same structural problem in the
2026-05-27 snapshot. Its heuristic classifications are useful review queues,
not final product decisions; this pass adds current source, package, index, and
third-party notice evidence.

### 3. The install boundary is now an allow-list

At the start of this audit, the install rule recursively copied almost all of
`dottalkpp/data` and excluded only `logs`, `tmp`, and `*.mdb`. In this working
tree that rule selected:

| Measure | Current result |
| --- | ---: |
| Files | 1,159 |
| Installed data size | 495.15 MiB |
| `biblebase` alone | 428.65 MiB before the current install exclusions |

Selected payloads include a 285.98 MiB Bible SQLite database, large derivative
CSV tables, teaching/course projects, generated HELP and dictionary tables,
ZIP archives, and two compiled COBOL executables.

The executables are ignored by `.gitignore` and are not git-tracked, but the
CMake directory install would still copy them from the working tree. This is a
direct example of why `.gitignore`, `PROMOTE.manifest`, and a product package
manifest are three different controls:

| Control | Job |
| --- | --- |
| `.gitignore` | Never version these development artifacts. |
| `PROMOTE.manifest` | Which clean development files publish to disposable staging/GitHub now. |
| Product component/package manifest | Which reviewed runtime files enter a named deliverable. |

The recursive directory install has been replaced by one product manifest per
edition under `config/package`. The validator selects only `git ls-files`
entries, rejects generated/binary/sidecar paths, and emits a SHA-256 source
inventory. CMake installs only those resolved entries.

A clean LEAN + NONE install now contains ten reviewed files before first
launch: the executable, Python module, three INI files, `LICENSE`, the selected
product manifest, the source-input inventory, and the app-local `lmdb.dll` and
`sqlite3.dll` runtime dependencies. An isolated installed-location smoke
detects SQLite 3.50.4, exits zero, and creates no files. The package inventory
currently covers tracked source inputs; a complete built-artifact SBOM and
third-party notice bundle remain release-control work.

### 4. Command and HELP metadata cannot yet express an edition

`CommandRegistration` currently records only origin, protected-name state, and
source text. It has no component, edition, risk, or visibility fields.

HELP DATA has catalog/category distinctions such as `ED`/`EDUCATION`, but its
canonical artifacts and command documents have no enforced product-component
or minimum-edition field. The data dictionary has begun using profile fields,
but those fields do not currently drive runtime registration or packaging.

Hiding a command while compiling and shipping its handler, HELP rows, scripts,
and data is useful for UI cleanliness but is not a product boundary. Project
licensing: To be determined.

### 5. Project status

To be determined.

### 6. Third-party code is generally separable, but notices are mandatory

The present dependency set is not just "MIT". The release inventory must use
the exact resolved package graph and preserve each dependency's terms.

| Dependency/surface | Observed terms | Product consequence |
| --- | --- | --- |
| LMDB | OpenLDAP Public License 2.8 | Binary notices and a verbatim license copy are required. |
| nlohmann/json | MIT, plus identified embedded components | Preserve notices; generate from resolved version. |
| SQLite | Public domain according to SQLite | Still record source/version in the SBOM. |
| pybind11 | BSD 3-Clause | Reproduce notice/disclaimer in binary distribution materials. |
| Turbo Vision | Borland disclaimer plus MIT and other component notices in the vcpkg copyright file | Do not summarize it as plain MIT; ship the complete resolved notice. |
| wxWidgets | wxWindows Library Licence 3.1 | Retain the applicable notice materials and review modifications. |
| Python runtime, if bundled | PSF license stack and incorporated-software notices | Do not assume pybind11's license covers a bundled Python runtime. |
| Project Gutenberg-derived Bible content | Work text plus Project Gutenberg license/trademark conditions | Treat content rights separately from software licensing; review commercial redistribution and transformed formats. |

wxWidgets and Python introduce many transitive packages. The table is not a
substitute for an automatically generated SBOM and `THIRD_PARTY_NOTICES` file.

## Proposed product/component model

### Engine capability axis

Introduce one new authoritative cache variable:

```text
DOTTALK_INDEX_MODE = NONE | LEGACY | LMDB
```

Meaning:

| Mode | xbase table engine | CNX/CDX/order code | LMDB index backend | LMDB message mirror |
| --- | --- | --- | --- | --- |
| `NONE` | yes | no | no | yes in the current CLI, independently |
| `LEGACY` | yes | yes | no | yes in the current CLI, independently |
| `LMDB` | yes | yes | yes | yes in the current CLI, independently |

Compatibility rule during migration:

- old `DOTTALK_WITH_INDEX=ON` maps to `DOTTALK_INDEX_MODE=LMDB`;
- old `DOTTALK_WITH_INDEX=OFF` maps to `DOTTALK_INDEX_MODE=LEGACY`, because
  that is closest to the current behavior;
- emit a deprecation warning;
- never reinterpret existing `OFF` as the new `NONE` silently.

The LMDB message-catalog mirror must move behind its own storage interface.
Otherwise `NONE` would still require LMDB and the profile name would be false.

### Product-edition axis

Introduce one authoritative product selector:

```text
DOTTALK_PRODUCT = LEAN | PROFESSIONAL | EDUCATIONAL | DEVELOPMENT
```

Profiles resolve to checked component sets; releases package the resolved set,
not a loose collection of independent booleans.

| Component | LEAN | PROFESSIONAL | EDUCATIONAL | DEVELOPMENT |
| --- | :---: | :---: | :---: | :---: |
| table/record/memo engine | yes | yes | yes | yes |
| chosen index provider | yes | yes | yes | yes |
| core CLI/API | yes | yes | yes | yes |
| core HELP/usage/about/project status | yes | yes | yes | yes |
| `EDU_ESSENTIALS` | yes | optional | yes | yes |
| relations, reporting, SQL, import/export | selected lean subset | yes | yes | yes |
| full maintenance/selfdoc/datadict mutation tools | no | no by default | instructor option | yes |
| external process/network integrations | no by default | separately entitled/configured | instructor option | yes |
| `LABTALK_FULL` content and commands | no | no | yes | yes |
| test/canary/regression commands | no | no | no | yes |
| student self-registering C++ examples | no | no | optional SDK samples, not main binary | yes |

`DOTTALK_PROFILE=DEV|PROD` and `DOTTALK_WITH_EDUCATION` should remain temporary
compatibility inputs only. The resolved component manifest is the truth.

### Proposed lean education baseline

LEAN should retain a small amount of educational usability, but not the campus.
Recommended initial classification:

| Keep in `EDU_ESSENTIALS` after review | Reason |
| --- | --- |
| core HELP, syntax, usage, warnings, and one small DBF walkthrough | Users need a self-explaining product. |
| `ASCII` | Small reference/diagnostic surface with no large content pack. |
| `EXAMPLE` only if rewritten as neutral product examples | Useful onboarding; must not load student/campus paths. |
| `BOOLEAN`, `FORMULA`, `EVALUATE` if they are real expression-runtime tools | Move genuine language capability out of `src/edu`; keep teaching prose optional. |

Recommended default exclusions from LEAN:

- `BIBLETALK`, Biblebase and Project Gutenberg derivatives;
- `CASE` and LabTalk case/history catalogs;
- `COBOL`, `CODASYL`, `DRAWIO`, `RETRO`, and ERP teaching stories;
- `CHRISTMAS`, `HANUKKAH`, MCC/course launchers and datasets;
- student self-registering command/function examples;
- full manuals, instructor material, labs, media, answer keys, and course projects;
- build probes, regressions, canaries, and maintenance mutation tools.

`NORMALIZE` and `IDX` need semantic review. If they are production database
operations, move their implementation to a neutral runtime component and keep
only lessons/examples in the education pack. Do not exclude useful engine
behavior merely because it currently lives in `src/edu`.

### Front-end axis

CLI, pydottalk, Turbo Vision, and wxWidgets should consume the same resolved
engine/product assembly. They must not each invent a different component list.

Recommended release artifacts:

| Artifact | Initial composition | Purpose |
| --- | --- | --- |
| `x64base-lean-indexed` | LEAN + LMDB | First practical lean product. |
| `x64base-lean-table` | LEAN + NONE | Embedded/API and architecture proof after the no-index gate passes. |
| `dottalk-professional` | PROFESSIONAL + LMDB | Full neutral database runtime. |
| `labtalk-education` | EDUCATIONAL + LMDB | Full teaching/campus pack. |
| `pydottalk` wheel/module | selected product + selected index mode | Python binding over the same engine, not a separate engine fork. |

Do not publish all combinations. Build more combinations in CI than are sold,
so dependency boundaries remain honest.

## Source and package architecture

### Replace recursive globs with explicit component targets

Proposed target direction:

```text
xbase_core
xbase_memo
xbase_index_contract        # small engine-owned interface, no concrete backend
xindex_legacy               # links xbase_core, implements the contract
xindex_lmdb                 # links xindex_legacy + LMDB

dottalk_runtime_core
dottalk_help_core
dottalk_relations
dottalk_sql
dottalk_import_export
dottalk_edu_essentials
labtalk_full
dottalk_maintenance
dottalk_external_tools
dottalk_dev_tests

dottalk_cli                 # composition root
pydottalk                   # composition root
dottalk_tv / dottalk_wx     # front ends
```

The target names are proposals. The dependency direction is the contract.

Use explicit `target_sources()` lists or generated, checked component lists.
Do not use a recursive glob as the edition boundary. A new source file must
fail closed until assigned to a component.

### Neutral xbase/index seam

The concrete API needs a focused design pass, but it must satisfy these rules:

1. No xbase public header mentions `xindex::IndexManager`.
2. No xbase source includes `xindex/*`.
3. xbase exposes neutral record lifecycle/change information sufficient for an
   optional index service to maintain keys transactionally.
4. A null/no-index provider is the engine default and has no xindex symbols.
5. xindex owns its manager/backends and may read DbArea through stable public
   engine interfaces.
6. The composition root attaches the selected provider.
7. Record write/delete/recall/append/pack failure semantics are explicit; an
   index update failure cannot be silently discarded as it is in some current
   paths.

Do not start by moving files or adding `#if` around every IndexManager call.
First define the mutation/ordering contract and direct dependency graph; then
move one lifecycle operation at a time under tests.

### One machine-readable component authority

Add a reviewed manifest such as `config/product_components.yaml` with rows like:

```yaml
id: dottalk.edu.essentials
target: dottalk_edu_essentials
sources: []
commands: []
help_topics: []
data_paths: []
dependencies: []
products: [LEAN, EDUCATIONAL, DEVELOPMENT]
project_license_status: To be determined.
risk: read_only
```

The implementation may generate checked CMake/registry/package lists from this
file or validate hand-maintained lists against it. Do not create two editable
authorities. Generated outputs must be reproducible and drift-tested.

Required component fields:

```text
id, owner, target, sources, public_headers, commands, functions, help_topics,
data_paths, dependencies, products, index_modes, project_license_status,
risk, tests
```

### Registration and HELP

Split the monolithic registry into component registration functions:

```text
register_core_commands()
register_index_commands()
register_professional_commands()
register_edu_essentials_commands()
register_labtalk_commands()
register_maintenance_commands()
register_external_tool_commands()
register_dev_commands()
```

Extend command metadata with stable `component_id`, `risk`, and visibility
information. Registration should occur only for linked/resolved components.
Runtime entitlement checks, if later required, are a second layer; they do not
replace compile/package separation.

Add the same `component_id` and product visibility to HELP, function, message,
data-dictionary, and script catalogs. A product build must not generate HELP
for an absent command, and an absent product component must not be recoverable
by scanning a shipped catalog DBF.

### Packaging

Use explicit CMake install components/CPack inputs or an equivalent packaging
tool generated from the component manifest.

Each release staging directory must be created empty and populated only from:

- built target outputs;
- explicit tracked data/package entries;
- the project status file (`LICENSE`: `To be determined.`) and third-party notices;
- the generated product manifest and SBOM.

Package validation must fail if:

- a file is untracked or ignored in the authority repo;
- a file is outside the resolved component allow-list;
- a forbidden extension such as a stray `.exe`, `.pdb`, cache, or database
  sidecar appears;
- a HELP/command/data row belongs to an absent component;
- a required third-party notice is missing;
- the resulting package differs from its recorded manifest.

## Project status

To be determined.

The engineering boundary remains useful regardless of that future decision.
Third-party terms and exact notices remain separate obligations and must not be
rewritten as project terms.

## Implementation passes

Keep these passes separate. Do not combine an index lifecycle refactor with a
product-surface purge in one change set.

### Pass 0 -- freeze names and establish measured baselines

Deliverables:

- current source-to-target inventory;
- current command/function/HELP/data inventory with stable IDs;
- current install dry-run manifest and size report;
- current resolved dependency/SBOM draft;
- decisions recorded for the proposed LEAN education baseline;
- compatibility mapping for old CMake options.

Gate:

```text
Every currently compiled source, registered public surface, and installed file
has a proposed component or an explicit REVIEW disposition.
```

### Pass 1 -- make component membership fail closed

Deliverables:

- component manifest;
- explicit CMake component targets/source lists;
- validation that no source is collected solely by the old recursive glob;
- component-aware command and HELP metadata, initially without behavior change;
- snapshots proving the DEVELOPMENT product still exposes the current surface.

Gate:

```text
Adding an unclassified source, command, HELP topic, or install file fails CI.
```

### Pass 2 -- invert xbase/xindex dependency

Deliverables:

- neutral xbase-owned optional index contract;
- xindex legacy and LMDB providers consuming xbase, never the reverse;
- message-catalog LMDB dependency separated from index mode;
- `DOTTALK_INDEX_MODE` compatibility layer;
- clean `TABLE_ONLY`, `LEGACY_INDEX`, and `FULL_INDEX` builds.

Gate:

```text
TABLE_ONLY builds and passes physical DBF CRUD without xindex symbols, xindex
libraries, LMDB imports, or index sidecars.
```

### Pass 3 -- implement edition/component registration

Deliverables:

- `DOTTALK_PRODUCT` resolver;
- split registration functions;
- `EDU_ESSENTIALS` and `LABTALK_FULL` source targets;
- maintenance, external-tool, and dev/test components;
- student extension examples moved to an SDK/sample tree and not linked into
  release executables.

Gate:

```text
LEAN starts with only its approved command/function surface; absent handlers are
not linked, not merely hidden.
```

### Pass 4 -- filter HELP, dictionaries, scripts, and data

Deliverables:

- component/profile fields in canonical catalogs;
- component-aware HELP generation and validators;
- explicit core HELP and `EDU_ESSENTIALS` data sets;
- separately packaged LabTalk, maintenance, and large-content packs;
- removal of recursive `install(DIRECTORY dottalkpp/data)` behavior.

Gate:

```text
No absent component appears in command listing, HELP, DDICT, script registry,
package files, or runtime path discovery.
```

### Pass 5 -- release controls

Deliverables:

- final product names/versions;
- consistent project wording: `To be determined.` until a later decision;
- per-artifact package manifest, SBOM, notices, hashes, and content-rights
  inventory;
- clean-room package staging from tracked allow-listed inputs;
- upgrade/install/uninstall behavior.

Gate:

```text
Every shipped byte belongs to a resolved component, has provenance, and is
covered by the product or third-party distribution terms.
```

### Pass 6 -- publish only after independent proof

Deliverables:

- clean builds from a fresh development checkout;
- signed/reproducible release candidates where practical;
- promotion into disposable staging through the existing promotion model;
- reviewed staging diff, then human commit/push.

Gate:

```text
Development remains authority; staging contains only the reviewed public
snapshot and release artifacts selected for promotion.
```

## Required proof matrix

### Engine proof

| Proof | TABLE_ONLY | LEGACY_INDEX | FULL_INDEX |
| --- | :---: | :---: | :---: |
| clean configure/build | required | required | required |
| DBF create/open/read/update/append/delete/reopen | required | required | required |
| no xindex symbols/import libraries | required | n/a | n/a |
| no LMDB index backend or index sidecar | required | required | n/a |
| no index sidecars created during physical operations | required | required unless explicitly indexing | required unless explicitly indexing |
| CNX/CDX create/open/order/seek/reopen | absent/negative | required | required |
| LMDB backend create/seek/reopen | absent/negative | absent/negative | required |
| update/delete/recall/pack synchronization | n/a | required | required |
| failure/recovery and stale-index reporting | n/a | required | required |
| pydottalk parity | required | required | required |

### Edition proof

For every published product:

1. Record exact linked source targets.
2. Snapshot command and function names.
3. Verify required commands exist and forbidden commands return unknown.
4. Verify absent handlers/symbols are not linked.
5. Export HELP/DDICT/script catalogs and reject rows for absent components.
6. Inspect the package manifest and reject untracked/ignored files.
7. Enforce a reviewed size budget; explain every change above the threshold.
8. Launch from an empty user profile and from an installed location.
9. Verify no source-tree fallback accidentally discovers full education data.
10. Generate and validate SBOM, third-party notices, project status, and content-rights manifest.

Recommended CI coverage (build all; initially publish only selected rows):

| Product | NONE | LEGACY | LMDB |
| --- | :---: | :---: | :---: |
| LEAN | build/test | build/test | **release candidate** |
| PROFESSIONAL | build/test | build/test | **release candidate** |
| EDUCATIONAL | optional test | build/test | **release candidate** |
| DEVELOPMENT | build/test | build/test | build/test |

## Remaining boundaries

- do not claim that xindex works merely because it links;
- do not claim the table-only CLI is LMDB-free while its message catalog still
  consumes LMDB;
- do not delete or relocate education files as a substitute for component
  selection;
- Project licensing: To be determined.
- no staging rebuild, commit, push, or public release is part of this work.

## Maintainer decisions before Pass 0 closes

Recommended defaults are shown first:

1. **First lean product:** LEAN + LMDB; keep TABLE_ONLY as a tested secondary
   product until index proof says otherwise.
2. **Lean education:** retain `EDU_ESSENTIALS` as proposed; exclude
   `LABTALK_FULL`.
3. **Project licensing:** To be determined.
4. **Full education:** package separately from code so software and content can
   have independent provenance and release cadences.
5. **Maintenance/external tools:** exclude from customer products by default;
   enable only through explicit components and policy.

## Official references used for third-party notice review

- OpenLDAP Public License 2.8:
  <https://www.openldap.org/software/release/license.html>
- SQLite copyright/public-domain statement:
  <https://sqlite.org/copyright.html>
- pybind11 license:
  <https://github.com/pybind/pybind11/blob/master/LICENSE>
- wxWidgets license:
  <https://wxwidgets.org/about/licence/>
- Python license history and incorporated-software notices:
  <https://docs.python.org/3.12/license.html>
- Project Gutenberg license and trademark/redistribution terms:
  <https://www.gutenberg.org/policy/license.html>
- SPDX SBOM standard overview:
  <https://spdx.dev/about/overview/>

Project licensing: To be determined.
