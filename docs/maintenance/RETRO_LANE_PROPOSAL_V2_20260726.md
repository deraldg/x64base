# Retro Lane Proposal V2 2026-07-26

Status: review-needed draft.
Ticket: AIF-064.
Basis: V1 external-AI proposal plus live-tree verification in `D:\code\ccode`.
Delivery rule: review package only; no source edit in this document.

## Summary

Create an optional private Retro lane that turns the existing `RETRO` screen
surface into a DBF-backed machine gallery and launcher. The first
implementation should be guarded behind `X64BASE_ENABLE_RETRO=OFF` by default.

## Resolved Tree Placeholders

| V1 Placeholder | Live-tree answer |
| --- | --- |
| top-level executable target | `dottalkpp` in `src/CMakeLists.txt` |
| core library target exposing `DbArea` | `xbase` is linked by `dottalkpp`; index support comes through `xindex`; memo through `memo` |
| command registration mechanism | `register_shell_commands()` in `src/cli/shell_commands.cpp` calls `registry().add(...)` |
| existing retro command | `src/cli/cmd_retro.cpp`, prototype in `src/cli/shell_commands.hpp`, registration in `src/cli/shell_commands.cpp` |
| existing screen repros | compiled screen records and render policy in `src/cli/retro_screen.*` and `src/cli/retro_render.*` |

## Proposed Layout

```text
retro/
  CMakeLists.txt
  include/retro/
    retro_lane.hpp
    machine.hpp
    registry.hpp
    backend.hpp
  src/
    retro_lane.cpp
    registry.cpp
    backends/
      vmware_backend.cpp
      winuae_backend.cpp
      fsuae_backend.cpp
      dosbox_backend.cpp
      exec_backend.cpp
  data/
    retro_machines.seed.toml
    screens/
  README.retro.md
```

The first code cut should either move or adapt the existing compiled screen
records into `retro/data/screens/` or retain them in source temporarily with a
documented migration plan. Do not orphan the current `RETRO` command behavior.

## CMake Plan

Top-level `CMakeLists.txt` should define:

```cmake
option(X64BASE_ENABLE_RETRO
       "Build the private Retro emulator/VM launchpad lane" OFF)
```

`src/CMakeLists.txt` or the top-level file should link only when enabled:

```cmake
if(X64BASE_ENABLE_RETRO)
  add_subdirectory(retro)
  target_link_libraries(dottalkpp PRIVATE x64base_retro)
  target_compile_definitions(dottalkpp PRIVATE X64BASE_RETRO=1)
endif()
```

`retro/CMakeLists.txt` should build `x64base_retro` as a static library and link
against the actual live storage targets:

```cmake
add_library(x64base_retro STATIC
  src/retro_lane.cpp
  src/registry.cpp
  src/backends/vmware_backend.cpp
  src/backends/winuae_backend.cpp
  src/backends/fsuae_backend.cpp
  src/backends/dosbox_backend.cpp
  src/backends/exec_backend.cpp
)
target_include_directories(x64base_retro PUBLIC include)
target_link_libraries(x64base_retro PUBLIC xbase xindex memo)
target_compile_definitions(x64base_retro PUBLIC X64BASE_RETRO=1)
```

## Command Hook

Current command registration is centralized in `src/cli/shell_commands.cpp`.
The guarded implementation should follow the local pattern:

```cpp
#if defined(X64BASE_RETRO)
#include "retro/retro_lane.hpp"
#endif

// inside register_shell_commands(...)
#if defined(X64BASE_RETRO)
registry().add("RETRO", [](DbArea& A, std::istringstream& S) {
    retro::cmd_RETRO(A, S);
});
#endif
```

The existing unguarded `RETRO` command is already public and supported. The
implementation decision for V3 is therefore one of:

1. Keep existing `RETRO` as the public screen-gallery command and add a new
   guarded `RETRO LAUNCH`/`RETRO MACHINES` sub-surface.
2. Move the whole `RETRO` command behind `X64BASE_ENABLE_RETRO`, accepting that
   public builds lose the current screen command.
3. Split names: keep public `RETRO` screens and add private `RETROMACHINE` or
   `RETROVM` for launch behavior.

Recommendation: option 1. It preserves current command truth and adds private
launcher capability without breaking HELP/manual coverage.

## Machine Schema

Initial DBF field proposal:

| Field | Type | Purpose |
| --- | --- | --- |
| `ID` | C(32) | stable machine id |
| `NAME` | C(80) | display name |
| `FAMILY` | C(24) | DOS, Windows, Amiga, Mainframe, Cloud, etc. |
| `GENERATION` | C(24) | 8-bit, 16-bit, 32-bit, 64-bit, cloud, simulated |
| `ERA` | C(24) | year or year range |
| `BACKEND` | C(16) | vmware, winuae, fsuae, dosbox, exec |
| `TARGET` | C(240) | VMX/config/path/command target |
| `ARGS` | C(240) | optional launch args |
| `HERITAGE` | C(180) | one-line gallery note |
| `RUN_MODE` | C(16) | runs-here, simulated, reference |

Recommendation: add `GENERATION` in the first cut. It is central to the charter
timeline and cheap to carry from the beginning.

## Command Surface

| Command | Behavior |
| --- | --- |
| `RETRO` / `RETRO GALLERY` | render current screen gallery plus machine gallery summary |
| `RETRO LIST` | list machine ids, names, backend, generation |
| `RETRO INFO <id>` | show placard and launch recipe |
| `RETRO DOCTOR` | report backend availability |
| `RETRO LAUNCH <id>` | launch backend when enabled and available |
| `RETRO IMPORT --RESEED` | rebuild DBF from seed by explicit request |

## Exit Conditions

- E1: `X64BASE_ENABLE_RETRO=OFF` build has no private launcher symbols and the
  public command surface remains intentional.
- E2: first-run seed creates `retro_machines.dbf`; `RETRO LIST` reads the DBF;
  an added row survives restart.
- E3: at least one VMware guest and one Amiga config launch on the owner's
  machine.
- E4: gallery entries are badged `runs-here`, `simulated`, or `reference`.

## Review Notes

- This is not source-evidenced until compiled.
- This is not runtime-evidenced until a machine actually launches.
- Launching external emulators is a high-side-effect operation and must remain
  explicit, never a default action.
- Keep the existing source/HELP truth for `RETRO` coherent if the command is
  split or expanded.

