# SelfDoc Subsystem Matrix v1

This document inventories the main DotTalk++ / x64base SelfDoc-oriented subsystems and compares how they are being normalized and implemented.

It is written against the current repo-runtime tree under `dottalkpp` and the current stage/GitHub tree under `x64base`.

## Doctrine

There are two materially different environments and they must not be judged by the same rule:

- `dottalkpp` is the live repo/runtime tree. It requires working runtime data, including active indexes and LMDB payloads where the subsystem depends on them.
- `x64base` is the stage/GitHub promotion tree. It is allowed to keep rebuildable CDX containers while omitting generated LMDB payloads for distribution and later regeneration.

That split is now part of the architecture, not an accident.

## Normalization Themes

### 1. Storage normalization

The strongest repeated pattern is:

- table data in `dottalkpp/data/<workspace>`
- CDX containers in `dottalkpp/data/indexes/<workspace>`
- LMDB payloads in `dottalkpp/data/lmdb/<workspace>`
- workspace manifests in `dottalkpp/data/workspaces/*.dtschema`
- opener scripts in `dottalkpp/data/*.dts`

This pattern is strongest for `help`, `comments`, `manuals`, `messaging`, `locale`, `metadata`, and `datadict`.

### 2. Naming normalization

Two major naming migrations are visible:

- legacy compact names to longer x64 names, strongest in `datadict`
- older “schema” wording toward `workspace` wording for DBF/CDX/LMDB collections

The repo is still in mixed language. The implementation is ahead of the documentation in several places.

### 3. Governance normalization

The project is trying to separate:

- runtime commands
- runtime DotScript
- external maintenance scripts
- policy documents
- validator/checker commands

This separation is real, but some docs still describe already-implemented native commands as future work.

### 4. Distribution normalization

The stage tree is being cleaned toward:

- fewer runtime scripts
- fewer workspace artifacts
- rebuildable index containers
- no large generated LMDB payloads in GitHub/staging

That is consistent with distribution goals, but only if the live repo/runtime tree keeps the working versions.

## Current Snapshot

Top-level workspace file counts currently match between runtime and stage for the main service catalogs:

| Workspace | Runtime files | Stage files |
| --- | ---: | ---: |
| `comments` | 11 | 11 |
| `help` | 18 | 18 |
| `manuals` | 8 | 8 |
| `messaging` | 3 | 3 |
| `locale` | 2 | 2 |
| `metadata` | 15 | 15 |
| `datadict` | 35 | 35 |

The deliberate reduction is elsewhere:

| Area | Runtime files | Stage files |
| --- | ---: | ---: |
| `data/scripts` recursive | 671 | 8 |
| `data/workspaces` recursive | 33 | 9 |

Current stage LMDB root is intentionally reduced to placeholder directories:

- `dottalkpp/data/lmdb/help`
- `dottalkpp/data/lmdb/x64`

## Subsystem Matrix

| System | Runtime surface | Class | Primary truth | Runtime expectation | Stage expectation | Status | Main drift |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `COMMENTS` | comments workspace | table-backed evidence catalog | source comments and `@dottalk.usage` contracts | working tables for source evidence capture and review | workspace shape preserved | partially normalized | good structure, but current HELP builds still mine source directly instead of reading `SRC*` evidence back as the primary feed |
| `HELP` | `HELP`, `HELP /DOT`, `DOTHELP` | table-backed user help and router surfaces | generated help DBFs plus curated help rows | working HELP data and indexes | keep distributable HELP data and rebuildable index containers | mature | HELP DATA visibility and DOTREF/router visibility are related but not identical proof surfaces |
| `CMDHELP` | `CMDHELP`, `CMDHELP BUILD`, `CMDHELP LEGACY` | builder/export pipeline | registry, `dotref.hpp`, `foxref.hpp`, source usage contracts | builds and exports help artifacts | keep outputs and rebuild path | mature but transitional | current HELP DATA builder is strong, but it still runs beside the comments evidence lane instead of consuming it as the primary live feed |
| `CMDHELPCHK` | `CMDHELPCHK` | validator/checker | command reflection, help artifacts, legacy DBF help reports | validate catalog and reflection integrity | same command should validate staged help surface | mature | still straddles legacy DBF checking and newer reflection/artifact checking |
| `DATADICT` | `DDICT` | table-backed catalog with bridge layer | `DD*` and `DATA_DICTIONARY_*` catalogs | live catalog plus indexes/LMDB | keep clean promotable catalog, not all dev/archive variants | comparatively mature | repo contains extra backup/sandbox/promotion directories beside the live catalog |
| `MESSAGING` | future catalog-backed messaging plus locale settings | table-backed support catalog | message definitions and localization intent | live runtime should eventually depend on it more strongly | preserve schema and essential tables | early-to-mid transition | concept is clear, runtime adoption is incomplete |
| `GUI` | wx workbench, Python/Tkinter workbench, TurboTalk/FoxTalk TUI | shared UI/runtime contract lane | DotTalk++/x64base runtime plus GUI core contracts | live repo should keep wx, Python, and TUI aligned through shared models, message keys, and smoke gates | stage should retain GUI contracts, source lanes, and launch/build docs without generated build clutter | active skeleton | wx and Python are moving quickly; messaging is seeded but not yet one physical runtime catalog |
| `CONTRACTS` | `MAINT CONTRACTS` inspector first, future `CONTRACTS` alias later | registry-backed governance lane | source contracts, usage contracts, design contracts, runtime proofs | live repo should keep contract registry, lifecycle, intake, and scan reports current | stage should retain durable contract docs and scanner | lane seeded | contract-like artifacts are currently scattered and need generated inventory/drift checks |
| `MANUALGEN` | `MANUAL` and `MAN*` catalog family | table-backed publication/catalog subsystem | manual sections, manifests, anchors, review assets | repo keeps full dev/publish estate | stage should keep only promotable/manual-facing pieces | partially normalized | large document workflow exists, but boundaries and publication path are still mixed |
| `BBOX` | `BBOX` | native educational command | command code plus maintenance doctrine | runtime command should explain subsystem lanes accurately | stage should retain command/docs | implemented | policy docs still describe it as future |
| `MAINT` | `MAINT` | native maintenance/governance command | command code plus maintenance doctrine | runtime command should inspect and teach maintenance lanes | stage should retain command/docs | implemented | policy docs still describe it as future |

## Detailed Analysis

### COMMENTS

Purpose:

- preserve source comments and `@dottalk.usage` contracts as queryable evidence

Normalization attempt:

- move comment evidence into a distinct workspace and treat it as its own maintenance lane
- keep it separate from end-user help tables

Assessment:

- this is the correct direction
- the structure is understandable and consistent with the Blackbox model
- the main remaining problem is not table design but repeatable harvesting, review, and promotion discipline

### HELP / CMDHELP / CMDHELPCHK

Purpose:

- transform registry facts, source usage contracts, `dotref.hpp`, `foxref.hpp`, and curated help rows into end-user HELP DATA
- validate the result

Normalization attempt:

- `CMDHELP` acts as the builder/exporter
- `CMDHELPCHK` acts as the checker
- user help rows are being distinguished from source/evidence-style rows

Assessment:

- this is one of the strongest subsystem families in the codebase
- the build/check split is correct
- the remaining complexity comes from supporting both newer reflection/artifact checking and older `commands.dbf` / `cmd_args.dbf` legacy flows

The family is implementationally ahead of some documentation, but its architecture is defensible.

### DATADICT / DDICT

Purpose:

- inspect and govern the data dictionary catalog, including the bridge between legacy compact names and longer x64 catalog names

Normalization attempt:

- explicit alias bridge between compact and long names
- explicit runtime roots for DBF, CDX, and LMDB
- dedicated helper/resolver layer under `include/datadict` and `src/datadict`

Assessment:

- this is the clearest example of explicit normalization work in the repo
- the bridge layer is a strength, not a weakness, because it exposes the migration instead of hiding it
- the main drift is operational clutter: the live `datadict` root in the repo contains extra backup, sandbox, rebuild, and promotion directories beside the active catalog

That makes the logic clearer than the storage estate.

### BBOX

Purpose:

- teach the SelfDoc “data in -> process -> information out” model

Normalization attempt:

- map each lane to inputs, processing, and outputs
- use a native C++ command instead of leaving the concept only in documents

Assessment:

- the command exists and the idea is right
- the docs are behind reality

Current drift:

- maintenance docs still say BBOX is future
- runtime code already implements `src/cli/cmd_bbox.cpp`

This is a documentation-lag problem, not an implementation-missing problem.

### MAINT

Purpose:

- provide a native read-only maintenance/developer control surface

Normalization attempt:

- make maintenance governance inspectable from the runtime
- keep it read-only
- point to cookbooks, lanes, and boundaries without letting the command mutate data

Assessment:

- the command exists and is conceptually aligned with the documented maintenance doctrine
- again, the docs lag the runtime

Current drift:

- multiple docs still refer to MAINT as future or candidate work
- runtime code already implements `src/cli/cmd_maint.cpp`

### MANUALGEN

Purpose:

- build, publish, catalog, and inspect the developer manual and related manual artifacts

Normalization attempt:

- use MAN* catalog tables and a runtime inspector
- separate publication assets from runtime help

Assessment:

- the subsystem is real, but it is still operationally mixed with review queues, media anchors, and publication experiments
- compared with HELP and DATADICT, MANUALGEN is less normalized in day-to-day process even when its intent is clear

### MESSAGING / LOCALE

Purpose:

- replace scattered runtime text with typed, language-aware catalog-backed messages

Normalization attempt:

- explicit locale and language settings
- dedicated data workspaces

Assessment:

- the structure is plausible and necessary for cross-platform maturity
- runtime adoption still appears partial
- this is a forward-looking normalization effort more than a fully consolidated subsystem

### GUI

Purpose:

- provide orthogonal user-interface lanes over the same DotTalk++ / x64base
  runtime truth
- let wx, Python/Tkinter, and TurboTalk/FoxTalk develop in parallel without
  forking database behavior

Normalization attempt:

- `docs/gui` holds GUI architecture and frontend contracts
- `docs/ui` holds cross-UI principles
- `src/gui/core` owns toolkit-neutral models, events, localization helpers, and
  async/session boundaries
- `src/gui/wx`, `tools/gui_preview`, and `src/tv` adapt those concepts to their
  respective toolkits

Assessment:

- the lane is active and visible earlier than expected, which is useful but
  raises sync risk
- wx is the primary native workbench shell
- Python is the rapid mirror/prototype lane
- TUI remains valuable for command taxonomy and shell/session lessons, but not
  for rich windowed database workbench behavior

Current drift:

- GUI message seeds are generated from `dottalkpp/data/messaging/gui_messages.csv`
  and consumed by C++/Python adapters, but they are not yet unified with the
  full runtime DBF-backed message catalog
- some command/runtime behavior still crosses through compatibility bridges
  while typed GUI services mature

Workflow anchor:

- `docs/gui/GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md`

### CONTRACTS

Purpose:

- keep durable rules, source contracts, usage contracts, and design contracts
  from being lost across chat churn, implementation churn, and manual promotion

Normalization attempt:

- central contract shelf under `docs/contracts`
- registry plus lifecycle plus intake queue
- read-only scanner under `tools/contracts`
- lane entry in maintenance manifests

Assessment:

- the lane is newly seeded and intentionally conservative
- the registry does not replace source, HELP, or SelfDoc evidence
- the next maturity step is generated inventory and drift review against
  harvested source usage contracts and `@dottalk.contract` annotations

## What Is Working

- The repo now has a recognizable SelfDoc family instead of unrelated one-off tables.
- HELP/CMDHELP/CMDHELPCHK form a coherent builder-validator-user surface chain.
- DATADICT/DDICT has an explicit compatibility bridge and clearer normalization intent than most subsystems.
- BBOX and MAINT already exist as native commands, which is the right long-term direction.
- Stage/GitHub cleanup is correctly moving generated LMDB payloads out of the promotable tree while keeping rebuildable structure.

## What Is Not Fully Normalized Yet

- The docs still undersell or misstate already-implemented native maintenance commands.
- The live repo contains dev/archive/promotion clutter around some catalog families, especially `datadict`.
- Runtime DotScript, external maintenance scripts, and maintenance policy docs still need sharper boundary language in a few places.
- MANUALGEN, MESSAGING, and related support systems are structurally present but not as operationally settled as HELP or DATADICT.

## Recommended Next Corrections

### Short term

- update maintenance policy/docs so `BBOX` and `MAINT` are no longer described as future
- keep stage/GitHub rules explicit: preserve rebuildable containers, omit generated LMDB payloads
- document which workspaces are runtime-required versus dev-only

### Medium term

- separate live catalog roots from archive/sandbox/promotion roots more aggressively in repo-runtime trees
- finish centralizing source comment evidence handling as a first-class maintenance lane
- continue moving help-source evidence logic toward builder/checker tools instead of mixing it into user-facing help rows

### Longer term

- finish catalog adoption for messaging/locale
- tighten MANUALGEN publication boundaries
- publish one authoritative subsystem map tying runtime commands, workspaces, and maintenance lanes together

## Bottom Line

The project is no longer a loose collection of DBF folders. It is visibly converging on a SelfDoc architecture with repeatable subsystem families.

The strongest normalized families today are:

- HELP / CMDHELP / CMDHELPCHK
- DATADICT / DDICT

The clearest implementation-versus-documentation drift today is:

- `BBOX`
- `MAINT`

The most important environmental rule is:

- repo/runtime keeps working indexes and LMDB where needed
- stage/GitHub keeps promotable structure and rebuildable containers, not bulky generated payloads
