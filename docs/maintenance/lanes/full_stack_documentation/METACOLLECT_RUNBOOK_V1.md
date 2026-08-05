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

## Build (host; not buildable in the mounted sandbox)

```powershell
cmake -S . -B build -DDOTTALK_BUILD_METACOLLECT=ON   # only needed if the option is off
cmake --build build --target metacollect --config Release
# -> D:\code\ccode\build\Release\metacollect.exe
# (an isolated variant also exists: build\metacollect-docflush\Release\metacollect.exe)
```

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
