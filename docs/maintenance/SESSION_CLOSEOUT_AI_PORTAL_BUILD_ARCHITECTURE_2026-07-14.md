# Session Closeout — AI Portal outcome and build architecture

Date: 2026-07-14.
Owning lifecycle: LabTalk SDLC and DotTalk++ SDLC maintenance/review.
SDLC lane: review and proof intake.
Truth state: mixed — documentation corrected, build graph source-defined, bounded table path runtime-proven.
Proof state: Git-verified, artifact inspection, and read-only runtime smoke.

## One-line summary

Corrected the AI Portal outcome record, routed the recursive human/AI coproject
idea into its existing doctrine, and established that the present pydottalk and
xbase builds still depend on xindex even though only the table path was
runtime-smoked.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Developer profile | `labtalk/LABTALK_DEVELOPER_PROFILE_v0.md` | Corrected the publication boundary: absent from public `main`, but already present in public branch history. Kept it out of new publication pending review. |
| AI interaction routing | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | Corrected AIF-012 and added AIF-013 for evidence-guided human/AI co-development. |
| Co-development doctrine | `labtalk/docs/co-development/recursive_coproject_model_v1.md` | Added AI collaborators as constrained coproject participants and recorded convergent/sculptural refinement without claiming infallibility. |
| AI status surface | `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | Added the corrected profile state, coproject state, build review, and this closeout. |

No C++ source, CMake source, DBF data, index, LMDB environment, build artifact,
staging tree, or publication surface was changed.

## Verified (proof performed this session)

### Publication-state correction

- Live Git ref inspection found GitHub `main` at
  `2675cdcd39133e5b02ca6ad2816d86d75d3f83a8` and the public
  `homegrown-cnx-20251112-branch` at
  `62f35aa88a10f8992f94b8b3e0ff14b1e8802ca8`.
- `labtalk/LABTALK_DEVELOPER_PROFILE_v0.md` entered history in `e7ddbc1b8`,
  which is an ancestor of that public branch. It is absent from public `main`.
- The derived profile does not contain the raw resume attachment or its contact
  details. This is a repository-content observation, not a guarantee about
  copies outside the repository.

### Current build graph

- Top-level CMake describes `DOTTALK_WITH_INDEX` as LMDB-backed xindex support
  and defaults it off, but `src/CMakeLists.txt` still adds `xindex` and then
  `xbase` whenever their directories exist.
- `src/xbase/CMakeLists.txt` publicly links `xbase` to `xindex` whenever the
  target exists. Current `DbArea` code owns and uses an
  `xindex::IndexManager`, so this is a code dependency, not only a CMake typo.
- With `DOTTALK_WITH_INDEX=OFF`, `src/xindex/CMakeLists.txt` removes only
  `lmdb_backend.cpp`; legacy/file index machinery remains in `xindex` because
  `DbArea` uses it.
- The main `dottalkpp` target still requires and links LMDB independently for
  its current runtime/catalog surfaces. PE inspection of the current Release
  executable shows a live `lmdb.dll` dependency.
- `pydottalk` is a Python extension (`.pyd`), not an executable. Its target
  links `xbase`, `memo`, and `xindex`; its small `.lib` is the Python extension
  import library, not a larger engine containing xbase.
- Both inspected build caches currently have `DOTTALK_WITH_INDEX=ON`; the
  normal `build` cache has `BUILD_PYDOTTALK=OFF` and `build-labtalk` has it on.

### Existing artifacts and bounded runtime smoke

| Artifact | Observed size | Observed evidence |
| --- | ---: | --- |
| `build/src/xbase/Release/xbase.lib` | 3,844,630 bytes | Built 2026-07-13; 2,436 public linker-member lines. |
| `build/src/xindex/Release/xindex.lib` | 5,981,578 bytes | Built 2026-07-13; 3,276 public linker-member lines including IndexManager and current backend symbols. |
| `build-labtalk/python/pydottalk.cp312-win_amd64.pyd` | 364,544 bytes | Imported as `pydottalk 0.4.0`; exposes `pydottalk.xbase.DbArea`. |
| `build-labtalk/python/pydottalk.lib` | 2,048 bytes | Fourteen linker-member lines; import-library scale, not engine scale. |
| `build/src/Release/dottalkpp.exe` | 6,737,920 bytes | Built 2026-07-14; links xbase, xindex, and LMDB in the generated Release project. |

The repository's `bindings/pydottalk_smoke_readonly.py` completed with exit 0
using the bundled Python 3.12 runtime and the existing extension. It opened
`dottalkpp/data/dbf/sandbox/STUDENTS.dbf`, found 45 DBFs in the directory, read
the 215-record/9-field table, printed five records, and closed it.

This proves that the existing pydottalk-to-xbase DBF read path is alive. It
does **not** prove that CDX ordering, CNX behavior, index mutation, or LMDB
index behavior is correct. No clean rebuild was performed, so the artifact
observations are not a clean-build certification.

`ctest -N -C Release` exposed only one index-related registered test:
`dottalkpp_lmdb_backend_smoke`. Its source checks standalone LMDB open,
upsert, duplicate keys, seek, range scan, erase, and reopen persistence. There
are no registered tests for CDX, CNX, IndexManager orchestration, or DBF/index
synchronization. The existing test executable is dated 2026-07-07, older than
the observed current libraries, so it was not counted as current proof and was
not run without first rebuilding it.

## AI-facing docs updated (AIF-006 gate)

- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` — corrected AIF-012 and
  added AIF-013.
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` — recorded the corrected lane
  states, current proof boundary, and this closeout.
- `labtalk/docs/co-development/recursive_coproject_model_v1.md` — anchored the
  co-development outcome in the existing doctrine.
- `docs/agents/CURRENT_TARGET.md` was not changed because this review did not
  replace the current project objective or authorize a source lane.

## Published

Not promoted and not published. All documentation changes remain uncommitted
in development. `C:\x64base` was not touched.

## Still open — for the next session

1. Decide whether the product needs three explicit build profiles:
   `CORE_TABLE` (no xindex, no LMDB), `LEGACY_INDEX` (file indexes without
   LMDB), and `FULL_INDEX` (all current backends).
2. A real `CORE_TABLE` profile requires source design work: put IndexManager
   behind an optional/null interface, remove direct xindex key-codec use from
   xbase, gate record-mutation index hooks, make the xindex target conditional,
   and separate the main executable's catalog/LMDB requirement.
3. Add focused, read-only or disposable-data proof for CDX, CNX, and LMDB.
   The table smoke must not be promoted into an index-health claim.
4. When a source lane is authorized, perform the source-mutation contract
   preflight before editing and hand the clean build/test commands to the
   maintainer as required by the portal.
5. Review the developer-profile wording and existing public-branch exposure.
   Treat any request to rewrite public history as a separate, explicit action.

## Provenance pointers

- `CMakeLists.txt`
- `src/CMakeLists.txt`
- `src/xbase/CMakeLists.txt`
- `src/xindex/CMakeLists.txt`
- `bindings/pydottalk/CMakeLists.txt`
- `bindings/pydottalk/src/module.cpp`
- `bindings/pydottalk_smoke_readonly.py`
- `docs/maintenance/DOTTALKPP_SDLC_CHARTER_v0.md`
- `labtalk/docs/co-development/recursive_coproject_model_v1.md`
- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`
- `labtalk/LABTALK_DEVELOPER_PROFILE_v0.md`
