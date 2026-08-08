# Editions, Builds, and Licensing -- Ground Truth (portal synapse)

**Status:** hardened ground truth. Date 2026-08-08. This exists because the facts below
took over an hour to rediscover from scratch. It is wired into the recall graph
(`trigger.release_or_license`) so the next agent -- or the next you -- reaches it in one hop
instead of re-deriving it. If you are about to cut a release, define an edition, or decide
licensing: **start here.**

## The one-paragraph answer

x64base already has a **product/edition system in CMake** that selectively builds LEAN /
PROFESSIONAL / EDUCATIONAL / DEVELOPMENT, with a real education strip and per-edition package
manifests. The engine is already factored into standalone static libraries that `pydottalk`
links **without** the shell or education. So the licensing "what are we shipping" boundaries
are **not something to invent -- they already exist as editions.** An education-stripped
executable is a config flip (done); an installable, embeddable engine **SDK** is a bounded
finish-the-packaging job (scoped, not yet built). And the editions were **blocked on the
license decision** -- which is why this licensing work unblocks a build system you already
finished.

## The edition selector (the master switch)

`CMakeLists.txt`:
- L139-141 -- `DOTTALK_PRODUCT` = `LEAN | PROFESSIONAL | EDUCATIONAL | DEVELOPMENT` (default
  `DEVELOPMENT`). This is the master product selector.
- L148-166 -- education is **derived** from the product: `DOTTALK_COMPONENT_LABTALK` (and
  MAINTENANCE / EXTERNAL / DEV) is set per product, then `DOTTALK_WITH_EDUCATION` is FORCED
  from it. `LEAN` and `PROFESSIONAL` leave education OFF.
- Related toggles: L75-83 `DOTTALK_WITH_TV/GUI/WX/INDEX/EDUCATION/RELATIONS`,
  `BUILD_PYDOTTALK`; L112 `DOTTALK_INDEX_MODE` = `NONE|LEGACY|LMDB`.

`config/build_vectors.cmake` holds only capacity vectors (MAX_AREAS=512, MAX_FIELDS=256) --
no feature gating.

## The education strip is real (source-level)

`src/CMakeLists.txt`:
- L205-213 -- a small keep-list `DOTTALKPP_EDU_ESSENTIAL_SOURCES` (edu_ascii_table,
  edu_boolean, edu_evaluate, edu_formula, edu_normalize, edu_edit, edu_text).
- L215-238 -- `if (NOT DOTTALK_COMPONENT_LABTALK)` physically removes every other `/src/edu/`
  file plus `app_army/app_erp/app_paxon/case_catalog/cmd_codasyl/cmd_drawio/cmd_erp/cmd_idx/
  cmd_mcc/cmd_retro`.
- L240-271 -- similar strips for EXTERNAL (`/src/ext`, `/src/ms365`, ftp/ssh/web/zip/sftp) and
  MAINTENANCE (ddict/maint/manual/msgmgr/bbox).
- L396 -- `add_executable(dottalkpp ...)`.

## The engine is already a set of libraries (the embed proof)

- `src/xbase/CMakeLists.txt` L11 -- `add_library(xbase STATIC ...)` (physical table/record engine).
- `src/xindex/CMakeLists.txt` L22/L42 -- `add_library(xindex STATIC ...)`,
  `target_link_libraries(xindex PUBLIC xbase)`.
- `src/memo`, `src/xexpr` libs; `src/CMakeLists.txt` L51-56 `add_library(dottalk_value STATIC ...)`.
- **`bindings/pydottalk/CMakeLists.txt` L60-92** -- `pydottalk` links `xbase` (+ `memo`,
  conditionally `xindex`), `HAVE_XBASE=1`, and compiles **no `src/cli` and no `src/edu`.**
  This is a working, shell-free, education-free embedded engine consumer TODAY.

## Presets and the "lean" red herring

`CMakePresets.json`: `core-base` (LEAN+NONE defaults), `windows-lean-table/-lmdb`,
`windows-educational-lmdb`, `windows-development-lmdb`, `pro-md` (day-to-day dev build ->
`build/`), `pro-md-labtalk`. **`wsl-lean` (L189-210) is a red herring:** its own description
says "lean means lean DEPENDENCIES, not a lean command surface" (`DOTTALK_PRODUCT=DEVELOPMENT`).
So `dottalkpp/bin-wsl-lean/` is a thin-deps Linux dev build, NOT the education strip. The real
strip is `DOTTALK_PRODUCT=LEAN/PROFESSIONAL`.

## Packaging and the sterilized public subset

- `config/package/{lean,professional,educational,development}.manifest` -- per-edition
  package manifests. `CMakeLists.txt` L545-575 runs `tools/packaging/build_product_inventory.py`
  to select only git-tracked runtime inputs for the chosen product + SHA-256 inventory;
  L613-628 registers `package_manifest_{edition}` ctest checks. A LEAN+NONE install is ~10 files.
- Promotion/staging: `tools/staging/` (`rebuild-staging.ps1`, `generate_public_manifest.py`,
  `create_public_baseline_escrow.py`, `prepush_gate.py`, `repository_role_guard.py`). Three
  filters: `.gitignore` vs `PROMOTE.manifest` vs the product package manifest.

## The engine-SDK gap (what "revive the library" actually costs)

Authority: `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md` -- status
"implemented; core build, runtime, and package matrix proven."
- L46-90 -- component boundary `xbase_core <- xindex_legacy <- xindex_lmdb`; a real
  `LEAN + NONE` build produces `pydottalk` + `dottalkpp.exe` with no `xindex` target.
- L294-338 -- the embeddable `x64base-lean-table` (Embedded/API) and the clean component
  targets are named as **PROPOSED future deliverables**; recursive globs still serve as the
  edition boundary.
- Passes 2-5 (L482-550) -- remaining work: fully invert the `xbase`<->`xindex` seam, replace
  globs with fail-closed component targets, move the LMDB message-catalog behind an interface
  (so `NONE` is truly LMDB-free).
- Companions: `EDITION_PUBLICATION_PLAN_A_V1.md` (editions exist in dev, NOT on `main`),
  `XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md`, `XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`.

**Verdict:** education-stripped executable = FLIP (done). Embeddable engine SDK = PARTIAL --
the separable libs exist and pydottalk proves the embed; the missing piece is packaging
(`install(EXPORT)` of the libs + public headers, one combined target) plus two known seams.
Bounded finish job, not a ground-up refactor.

## The gate: licensing blocked the editions

`BUILDING.md` L102-121: "Editions (in development -- not yet in this repository)" and,
verbatim, **"License: To be determined. Editions intended for distribution will need this
settled before public release."** So the whole edition/publication system has been waiting on
the license decision. The licensing work (the map, proposals, one-way-door principle) is the
key that unblocks it.

## The binding: license unit <-> edition <-> manifest

| License unit | Edition(s) | Package manifest | License (adoption posture) |
| --- | --- | --- | --- |
| Engine SDK (embeddable) | LEAN engine libs / `x64base-lean-table` (proposed) | `config/package/lean.manifest` (engine subset) | **Apache-2.0** -- once the SDK is packaged |
| dottalkpp app (full) | PROFESSIONAL, DEVELOPMENT | `professional` / `development.manifest` | **GPL-3.0 + commercial** |
| LabTalk / education | EDUCATIONAL | `educational.manifest` | **CC-BY** (content) |
| AI work | (not an edition) | n/a | **proprietary** |

## The cluster (read next)

- `PRODUCT_DELIVERABLE_LICENSE_MAP_V1.md` -- products vs deliverables vs units.
- `LICENSING_PRINCIPLE_ONE_WAY_DOOR_V1.md` -- the irreversibility rule + income levers.
- `PROPOSAL_1..4_*_V1.md` -- the per-unit license proposals.
- `X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md` -- the "how" for the Apache engine SDK.
