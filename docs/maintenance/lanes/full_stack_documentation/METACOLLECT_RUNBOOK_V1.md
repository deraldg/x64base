# metacollect runbook v1

Lane: `full_stack_documentation` (Phase 5, Metadata)
Owner: `member.derald`
Recorded: 2026-08-05
Purpose: build/run reference for `metacollect` so it is not re-derived each push.

## What it is

`metacollect` is a standalone C++ source-reflection metadata collector. It is NOT
part of `dottalkpp.exe`, NOT a registered command, and has **no launcher** (no
`.ps1`/`.sh`, not run via `datarun.ps1`). It is a separate CMake target run as a
raw exe. Read-only: it emits candidate reports and never mutates
metadata/help/runtime/source.

- Sources: `src/tools/metacollect_main.cpp` (entrypoint), `src/meta/metacollect.cpp`,
  `include/dt/meta/metacollect.hpp`.
- CMake target: `metacollect`, gated by option `DOTTALK_BUILD_METACOLLECT` (default OFF).
- Contract: `@dottalk.external v1` in `src/tools/metacollect_main.cpp`
  (external-kind `standalone-tool`). Concept:
  `labtalk/ai_portal/EXTERNAL_CALL_CONTRACT_V1.md`.

## Build

**Correction, 2026-08-26.** This heading read "host; not buildable in the
mounted sandbox". That is false and it is the AIF-130 shape: a routing document
telling an arriving agent a sandbox cannot build, which stops the agent before
it tries. AIF-130 corrected `AI_README.md` and did not sweep for siblings; this
was one of two left standing. **metacollect builds in a sandbox in under forty
seconds, and it was measured, not estimated** -- Cowork 2026-08-26, flush v6
Phase 5, which had been filed OWNER-BLOCKED for exactly this reason until the
block was tested.

### Host (MSVC)

```powershell
cmake -S . -B build -DDOTTALK_BUILD_METACOLLECT=ON   # only needed if the option is off
cmake --build build --target metacollect --config Release
# -> D:\code\ccode\build\Release\metacollect.exe
# (an isolated variant also exists: build\metacollect-docflush\Release\metacollect.exe)
```

### Sandbox (g++, no CMake)

`dt_meta` at `CMakeLists.txt:771` is FULLY ENUMERATED -- eleven translation
units, two include directories, `cxx_std_17` -- so the target needs no CMake to
reproduce. Measured: g++ 11.4, `-O0`, `-j4`, twelve objects and a link, **under
forty seconds**, and the binary ran a full source scan in one call.

```sh
CXXFLAGS="-std=c++17 -O0 -w -I include -I src/cli/expr"
# TU list, from CMakeLists.txt:771 -- keep it in step with that block:
#   src/cli/expr/date/date_arith.cpp   src/cli/expr/date/date_utils.cpp
#   src/cli/expr/fn_date.cpp           src/cli/expr/fn_numeric.cpp
#   src/cli/expr/fn_string.cpp         src/cli/expr/function_catalog.cpp
#   src/datadict/ddict_read_helpers.cpp  src/datadict/ddict_dbf_reader.cpp
#   src/meta/metacollect.cpp
#   src/common/path_resolver.cpp       src/common/path_state.cpp
# plus the entrypoint:
#   src/tools/metacollect_main.cpp
```

**Build OUTSIDE the tree** -- a sandbox build is a measurement, not a product.
Nothing should land in `build/`, and no `CMakeCache.txt` should be written.

The last two TUs are there for the reason `CMakeLists.txt:771` records at
length: `resolve_in_slot()` and the `dottalk::paths` state it sits on are
compiled into TWO link closures, and only the engine's carried them. If the link
fails on an undefined symbol, read that comment before adding a stub -- a local
stub compiles and then resolves paths differently from the engine, which is
worse than a link error, because a link error stops.

**A sandbox green is still not a green on the maintainer's toolchain. Name the
platform every time.**

## Run -- candidate-only seed emit (Phase 5)

From `D:\code\ccode`. Writes into the run's `metacollect_phase/`; imports nothing
into live metadata (that is a separate reviewed gate).

```powershell
$mc  = 'D:\code\ccode\build\Release\metacollect.exe'
$out = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260805-001\metacollect_phase'
New-Item -ItemType Directory -Force $out | Out-Null
& $mc --source-root D:\code\ccode\src --include-dev-commands --sysargs-include-keywords `
      --syscmd-import-out  "$out\SYSCMD_IMPORT_candidate_v1.csv" `
      --sysfunc-import-out "$out\SYSFUNC_IMPORT_candidate_v1.csv" `
      --sysargs-import-out "$out\SYSARGS_IMPORT_candidate_v1.csv" `
      > "$out\metacollect_facts_v1.csv" 2> "$out\metacollect_stderr_v1.txt"
Get-Content "$out\metacollect_stderr_v1.txt"
```

Optional source-vs-live drift compare (reads live metadata DBFs):

```powershell
& $mc --source-root D:\code\ccode\src --compare `
      --compare-out "$out\metacollect_compare_v1.csv" `
      --metadata-root D:\code\ccode\dottalkpp\data\metadata  2>&1 | Select-String 'issue'
```

## Flag reference (from `metacollect_main.cpp`)

| Flag | Effect |
| --- | --- |
| `--source-root <dir>` | add a source tree to scan (repeatable) |
| `--source-ext <ext>` | add a source extension (repeatable) |
| `--with-metadata` | include live metadata tables in facts |
| `--compare` | compare source facts vs live metadata (implies `--with-metadata`) |
| `--compare-out <path>` | write compare issues CSV |
| `--syscmd-import-out <path>` | emit SYSCMD seed candidate CSV |
| `--sysfunc-import-out <path>` | emit SYSFUNC seed candidate CSV |
| `--sysargs-import-out <path>` | emit SYSARGS seed candidate CSV |
| `--sysargs-include-keywords` | widen SYSARGS to include usage keyword args |
| `--include-dev-commands` | include dev/diagnostic command contracts (CANARY, EVALDIFF, ...) |
| `--metadata-root <dir>` | live metadata DBF root (for `--compare`) |
| `--no-source` | exclude source catalogs |
| `--no-skeleton-marker` | omit skeleton marker |
| `<positional>` | workspace root (default `.`) |

Behavior: the metafacts CSV goes to **stdout** (redirect it); each `--*-import-out`
writes its CSV and prints a row count to **stderr**.

## Last run baseline (re-measure, do not trust)

Run `DOCFLUSH-20260805-001`, 2026-08-05, exe `build\Release\metacollect.exe`
(engine version `v0.6 2026-08-05 b2699ee9 dirty`):

- SYSCMD candidate rows: 226
- SYSFUNC candidate rows: 74
- SYSARGS candidate rows: 959

Candidates under
`docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260805-001/metacollect_phase/`.
These are Phase 5 candidates; a Gate 5 review binds them and no live import occurs
without a separate reviewed gate.

## Related

- Contract concept: `labtalk/ai_portal/EXTERNAL_CALL_CONTRACT_V1.md`
- SYSCMD candidate contract:
  `docs/maintenance/lanes/full_stack_documentation/METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md`
- Flush plan Phase 5:
  `docs/maintenance/lanes/full_stack_documentation/FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md`
