# Pinocchio — engine stress-test lane

Codename **Pinocchio**: can the educational database perform like a *real boy*
at ~1,000× the MCC scale? Phase 1 is **performance at scale** (real-world ~1M
students / ~5–8M enrollments). Full design, metrics, and pass/fail thresholds:
`docs/maintenance/PINOCCHIO_STRESS_TEST_PLAN_V1.md`.

This lane is **fully derived and disposable**. It builds into its own
directories (`data/{tmp,dbf,indexes,lmdb}/pinocchio`) and never reads or writes
the MCC sample foundation. Its generated data and built artifacts are gitignored;
only these scripts and the plan are versioned.

## Scripts

| File | Role |
| ---- | ---- |
| `gen_pinocchio_data.ps1` | generate seeded, streamed CSVs at any scale (record 1 = the MCC canary) |
| `run_pinocchio.ps1` | orchestrate: generate → build → measure, tee transcripts |
| `../../data/scripts/pinocchio/pinocchio_build.dts` | `CREATE X64` (advanced types, `SID I`) → `IMPORT` → `CDX` → `BUILDLMDB` (CANDIDATE) |
| `../../data/scripts/pinocchio/pinocchio_measure.dts` | timed, read-only query battery (CANDIDATE) |

## Run (on the maintainer's machine)

```powershell
# one-shot: generate 1M, build, measure
.\dottalkpp\scripts\pinocchio\run_pinocchio.ps1 -Generate

# quick warm-up at 100k first (validate correctness + harness)
.\dottalkpp\scripts\pinocchio\run_pinocchio.ps1 -Generate -Students 100000

# stable machine label for comparable historical baselines
.\dottalkpp\scripts\pinocchio\run_pinocchio.ps1 -MachineType "alienware-m16-r2-i9-185h"
```

Ingest uses the mature path — `CREATE X64` (structural create) + `IMPORT`
(tested); `AUTODBF` is intentionally off the critical path (needs more testing).
The `.dts` scripts are **CANDIDATE / REVIEW_BEFORE_EXECUTION** — the first trace
confirms `CREATE`/`IMPORT` behavior (types, date parsing), the `BUILDLMDB
MAPSIZE` unit, and `SET TIMER` output before we trust the numbers. A zero exit code is not proof: read
`data/tmp/pinocchio/{build,measure}.log`, confirm the counts and the canary,
then we record the timings in a session closeout.

## Historical benchmark baseline

The first before/after engine ledger is
`docs/maintenance/PINOCCHIO_HISTORICAL_ENGINE_BENCHMARKS_V1.csv`; its human
summary is in the plan's **Historical engine benchmarks** subsection.

Every run now writes `data/tmp/pinocchio/machine_profile.json`. Pass
`-MachineType` to provide a stable lab label; otherwise the runner attempts CIM
discovery and falls back to Windows environment values. Historical measurements
whose artifacts did not record hardware remain `UNRECORDED` rather than being
retroactively attached to the current workstation.
