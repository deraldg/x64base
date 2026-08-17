# DEV-21 Build System

```yaml
page_id: DEV-21
title: Build System
status: DRAFT
last_verified: 2026-08-17
```

Companion to DEV-02, which describes where things LIVE. This chapter describes
how they are BUILT. Everything below was measured against the working tree on
2026-08-17; where something was not measured it says so.

## What the build produces

The tree declares **seven executable targets and exactly one loadable module.**
The distinction matters because the module is routinely described as a build
option of the CLI, and it is not one.

| target | declared at | kind |
| --- | --- | --- |
| `dottalkpp` | `src/CMakeLists.txt:406` | executable, the CLI |
| `dottalk_bbsd` | `CMakeLists.txt:503` | executable, BBS agent-server daemon |
| `metacollect` | `CMakeLists.txt:754` | executable, metadata/contract collector |
| `schema_inventory` | `CMakeLists.txt:763` | executable, tool |
| `g0_slot_cost_probe` | `CMakeLists.txt:779` | executable, tool |
| `fox_palette` | `src/CMakeLists.txt:473` | executable, tool |
| `dottalkpp_*_smoke` / `_test` | `src/tests/CMakeLists.txt` | executables, ctest |
| `pydottalk` | `bindings/pydottalk/CMakeLists.txt:352` | **module**, not an executable |

`pydottalk` is a `pybind11_add_module`: a `.pyd` on Windows, a `.so` on Linux,
loadable only by the Python interpreter it was built against. No executable
links it, and it links no executable.

## The two axes, which are independent

`DOTTALK_PRODUCT` and `DOTTALK_INDEX_MODE` are separate questions and are
frequently conflated. LEAN does not mean engine-only and does not mean no-index.

**Product composition** (`CMakeLists.txt:158-180`), default `DEVELOPMENT`:

| product | EDU_ESSENTIALS | LABTALK | MAINTENANCE | EXTERNAL | DEV |
| --- | --- | --- | --- | --- | --- |
| `LEAN` | ON | OFF | OFF | OFF | OFF |
| `PROFESSIONAL` | ON | OFF | OFF | OFF | OFF |
| `EDUCATIONAL` | ON | ON | OFF | OFF | OFF |
| `DEVELOPMENT` | ON | ON | ON | ON | ON |

Note LEAN and PROFESSIONAL currently select the SAME component set. That is what
the code does; whether it is intended is not recorded here.

**Index engine** (`CMakeLists.txt:131-156`), three states:

| `DOTTALK_INDEX_MODE` | `DOTTALK_HAS_XINDEX` | `DOTTALK_WITH_INDEX` | meaning |
| --- | --- | --- | --- |
| `NONE` | OFF | OFF | no xindex target at all |
| `LEGACY` | **ON** | OFF | house index (CNX, native CDX, index_manager); no lmdb |
| `LMDB` | ON | ON | everything, including `lmdb_backend.cpp` |

**LEGACY is the trap worth knowing.** `DOTTALK_HAS_XINDEX=1` sits next to
`DOTTALK_WITH_INDEX=0`, which reads literally as "xindex exists, lmdb does not".
Code that tests `WITH_INDEX` to decide whether an index exists at all is wrong.

**And the default is LEGACY, not NONE.** If `DOTTALK_INDEX_MODE` is unset and
`DOTTALK_WITH_INDEX` is OFF, `CMakeLists.txt:139` resolves the mode to LEGACY,
because historically `WITH_INDEX=OFF` disabled only LMDB. Passing
`-DDOTTALK_WITH_INDEX=OFF` to work around a missing `lmdb.h` therefore does NOT
give you a no-index build.

## Root options

From `CMakeLists.txt:94-126` and `:494`. All default OFF unless stated.

| option | default | effect |
| --- | --- | --- |
| `DOTTALK_WITH_TV` | OFF | Turbo Vision features (pulls the tvision vcpkg package) |
| `DOTTALK_WITH_GUI` | OFF | GUI-neutral application services |
| `DOTTALK_WITH_WX` | OFF | wxWidgets frontend |
| `DOTTALK_WITH_INDEX` | OFF | compatibility switch, see the table above |
| `DOTTALK_WITH_EDUCATION` | ON | FORCED from the product matrix; do not set by hand |
| `DOTTALK_WITH_DEV` | derived | FORCED from the product matrix |
| `DOTTALK_WITH_RELATIONS` | ON | relationship support |
| `DOTTALK_BUILD_METACOLLECT` | OFF | builds `metacollect` |
| `DOTTALK_BUILD_BBSD` | **ON** | builds `dottalk_bbsd` |
| `BUILD_PYDOTTALK` | OFF | adds `bindings/pydottalk` as a SUBDIRECTORY of the root build |

`DOTTALK_WITH_EDUCATION` and `DOTTALK_WITH_DEV` are written back to the cache
with `FORCE` at `:182-185`. Setting them on the command line is overwritten by
the product matrix.

## Presets

### Root: `CMakePresets.json`

Thirteen visible configure presets. Measured columns:

| preset | generator | index | pydottalk | TV |
| --- | --- | --- | --- | --- |
| `core` | Ninja | NONE (base) | -- | -- |
| `core-vcpkg` | Ninja | NONE (base) | -- | -- |
| `windows-core` | VS 17 2022 | NONE (base) | -- | -- |
| `windows-lean-table` | VS 17 2022 | NONE | **ON** | -- |
| `windows-lean-lmdb` | VS 17 2022 | LMDB | -- | -- |
| `windows-educational-lmdb` | VS 17 2022 | LMDB | -- | -- |
| `windows-development-lmdb` | VS 17 2022 | LMDB | -- | -- |
| `index-vcpkg` | Ninja | LMDB | -- | -- |
| `pro-md` | VS 17 2022 | LMDB | OFF | ON |
| `pro-md-labtalk` | VS 17 2022 | LMDB | **ON** | ON |
| `ansi-mt` | VS 17 2022 | LMDB | -- | OFF |
| `wsl` | Ninja | LMDB | -- | OFF |
| `wsl-lean` | Ninja | LMDB | OFF | OFF |

Three things to know about this table:

1. **`pro-md` is the house default and has `BUILD_PYDOTTALK=OFF`.** The default
   build does not produce the Python module.
2. **Only `wsl-lean` carries a host condition.** The five `windows-*` presets
   have none, so on Linux `cmake --list-presets` offers them with a Visual Studio
   generator that cannot work there.
3. **No preset builds pydottalk on Linux.** Both `wsl` and `wsl-lean` set
   `BUILD_PYDOTTALK=OFF`, and the two presets that turn it ON are MSVC.

**Configure-preset and build-preset names differ.** `cmake --preset pro-md` then
`cmake --build --preset pro-md-Release`. This bites everyone once.

### Binding: `bindings/pydottalk/CMakePresets.json`

Added 2026-08-17. Builds the module and NOTHING else. Build trees land in
`build-pydottalk/<presetName>`, which `.gitignore` covers via `/build-*/`.

| preset | generator | index | note |
| --- | --- | --- | --- |
| `lean-legacy` | Ninja | LEGACY | **default**; no lmdb needed to configure |
| `lean-lmdb` | Ninja | LMDB | requires the vcpkg toolchain |
| `lean-none` | Ninja | NONE | 25 objects instead of 47 |
| `lean-legacy-msvc` | VS 17 2022 | LEGACY | Windows; NOT yet run |
| `lean-lmdb-msvc` | VS 17 2022 | LMDB | Windows; NOT yet run |

LEGACY is the default because, as of this writing, **all three modes ship a
byte-identical module**: 665336 bytes, sha256 `54cb15eb...`, measured three
times on Linux. `module.cpp` references the index zero times, so `libxindex.a`
resolves nothing and the linker discards it, `lmdb_backend.o` included. LEGACY
buys the same artifact for one fewer dependency. See
`proof.build.index_mode_changes_nothing_shipped` and OI-007; re-measure once the
binding exposes an index API.

## Entry-point scripts

| script | builds | notes |
| --- | --- | --- |
| `build.ps1` | the root tree | `-Config`, `-UseNinja`, `-BuildDir`, `-VcpkgRoot`, `-VcpkgTriplet`, `-PythonExe`, `-NoIndex`, `-NoTV`, `-WithGui`, `-WithWx`, `-WithPyDotTalk` |
| `build_pydottalk.ps1` | the module ONLY | lean standalone by default; `-ViaRootBuild` restores the heavy path |
| `build-labtalk.ps1` | root tree into `build-labtalk` | |
| `build_help.ps1` | HELP artifacts | not measured for this chapter |
| `build_website.ps1` | website artifacts | not measured for this chapter |
| `datarun.ps1` | nothing; RUNS the CLI | stages the newest exe into the runtime bin |

**`build.ps1 -WithPyDotTalk` also builds the CLI.** Lines 164/170 hardcode
`--target dottalkpp pydottalk`, and there is no switch to say otherwise. That is
OI-003. Use `build_pydottalk.ps1` when you want the module alone.

## Two builds, two trees

The root build and the lean binding build are separate configures with separate
caches. `build_pydottalk.ps1` deliberately does NOT use `build-labtalk`, because
sharing a build directory would mean the two configures overwrite each other.

The lean binding build adds `src/xbase`, `src/memo` and `src/xindex` by
`add_subdirectory` against `DOTTALK_ROOT`. **It does not restate their source
lists**: those directories glob their own sources, and a second hand-kept copy
would drift silently. This is the co-sourced rule, and it is doctrine rather
than convenience. See `PYDOTTALK_SDLC_CHARTER_v0.md` and AIF-119.

## Build-order constraints

- **`dottalk_bbsd` cannot be rebuilt while its scheduled task is running.**
  A live instance locks the exe and the build fails with `LNK1104`.
  `Stop-ScheduledTask -TaskName 'DotTalkBBSD'` first.
- **`datarun.ps1` warns loudly and quantifies staleness** if it cannot copy the
  fresh build into the runtime bin. A silent stale run is a defect, not a
  fallback. See OI-009 for a predecessor script that does NOT do this.

## Platform status

Measured 2026-08-17.

| | Windows | Linux |
| --- | --- | --- |
| `dottalkpp` | green, the primary target | `wsl` / `wsl-lean` presets exist; not run this session |
| `dottalk_bbsd` | green, runs as a scheduled task | not measured |
| `pydottalk` lean | green, `pydottalk.cp312-win_amd64.pyd`, ctest 2/2 | green, `pydottalk.cpython-310-x86_64-linux-gnu.so`, 665336 B, imports, reports 0.4.0 |
| `pydottalk` via root build | green (`windows-lean-table`, `pro-md-labtalk`) | **FAILS at link** -- no PIC anywhere in the root tree (OI-006) |
| LMDB index mode | green via vcpkg | compiles and links; proven only against a hand-built lmdb, NOT the house vcpkg route |

**The ABI tag is the practical trap.** `cp312-win_amd64` imports only under
Python 3.12; the Linux build emitted `cpython-310`. The module is not pinned to
one Python version, but each artifact is. `build_pydottalk.ps1` warns when it
resolves an unexpected interpreter, because a silent swap produces an artifact
no caller can import.

## Landmines, all measured

1. **Extracting a subproject inherits five invisible globals.** The root build
   supplies the GENERATED `dottalk/build_vectors.hpp`, `NOMINMAX`,
   `CMAKE_MSVC_RUNTIME_LIBRARY`, seven feature flags, and
   `CMAKE_POSITION_INDEPENDENT_CODE`. **Only the first two fail loudly.** A CRT
   mismatch links cleanly and misbehaves at runtime; an undefined
   `DOTTALK_WITH_INDEX` reads as 0 under `#if`, so the consumer compiles a
   different view of the same structs than the libraries it links.
   `proof.build.parent_provided_globals`.
2. **`NOMINMAX` failures name the wrong problem.** `<windows.h>` defines `max()`
   as a macro, so `std::numeric_limits<T>::max()` becomes
   `C2589: '(' illegal token on right side of '::'` -- 30+ errors across 7 lines
   of `dbf_file.cpp`, none of which mention `windows.h` or `max`.
3. **Do not re-emit a flag a linked target already exports PUBLIC.**
   `src/xindex/CMakeLists.txt:38` exports `DOTTALK_HAS_XINDEX=1` PUBLIC. A
   consumer that also emits it is not configuring, it is arguing, and the last
   flag on the command line wins per translation unit.
   `proof.build.macro_defined_twice_disagreeing`.
4. **The root build has no `CMAKE_POSITION_INDEPENDENT_CODE`.** On ELF this
   makes `-DBUILD_PYDOTTALK=ON` fail at link with a relocation error naming a
   thread-local three libraries deep. Windows never surfaces it. OI-006.
5. **`find_package(unofficial-lmdb CONFIG REQUIRED)` is a vcpkg-only name.**
   A system lmdb will not satisfy it. Two call sites:
   `src/xindex/CMakeLists.txt:51` and `src/CMakeLists.txt:417`.
6. **`src/bindings/` is dead code and a SECOND `pydottalk` definition.** Nothing
   adds it; `src/CMakeLists.txt` excludes it twice. It has already misled one
   session into editing the wrong file. OI-002.
7. **`src/cli` is globbed with `GLOB_RECURSE CONFIGURE_DEPENDS`**
   (`src/CMakeLists.txt:92`). Anything dropped there is compiled into the CLI
   whether or not it is tracked in git.

## Verifying a build

A zero exit code is not proof. The house minimum:

- **Assert the artifact exists** before reporting success. `build_pydottalk.ps1`
  throws if no `.pyd` is found, because a green build once reported success with
  no artifact produced.
- **Treat a warning in a green build as a finding.** Landmine 3 announced itself
  as a compiler warning in the middle of a 52-step log that ended in success.
- **Record size and sha256** for any change claiming to alter what ships.
  Identical sizes are not proof of identical content, and identical content is
  not proof of an identical dependency set; check symbols (`nm -D`, `dumpbin`)
  and dynamic dependencies (`ldd`, `dumpbin /dependents`) separately.

## Related

- `BUILDING.md` -- the user-facing quickstart. This chapter is the reference.
- DEV-02 -- where build outputs live (source, runtime and evidence estates).
- DEV-09 -- indexing, INX/CNX/CDX/LMDB, the engine side of `DOTTALK_INDEX_MODE`.
- `PYDOTTALK_SDLC_CHARTER_v0.md`, `AIF_119_PYDOTTALK_CO_SOURCED_PRODUCT_LANE_V1.md`.
- `docs/agents/HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md` -- sandbox
  limits and what a mounted Linux agent can and cannot build.

## Not covered here

`build_help.ps1` and `build_website.ps1` were not measured for this chapter, and
the `wsl` / `wsl-lean` presets have not been run on the maintainer's WSL host by
the session that wrote this. Those are gaps in the evidence, not claims of
absence.
