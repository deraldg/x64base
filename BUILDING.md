# Building DotTalk++ / x64base

This is the front door for building the engine. It tells you which **edition**
to build and the one command that builds it. The detailed proof and rationale
live in the linked records at the bottom; this page is the "just build it" path.

There is **no prebuilt binary in the repository** — this is a development-stage
project. You build the runtime yourself (onboarding steps 3–4), then run the
data build (step 5). See `dottalkpp/data/scripts/mcc/README.md` for step 5.

## The two choices

A build is defined by two independent axes.

### 1. Product — how much of the system is included

Set with `-D DOTTALK_PRODUCT=<name>`.

| Product | For | Includes |
| --- | --- | --- |
| `LEAN` | A minimal, shippable database runtime. | Core engine + essential education surface only. |
| `PROFESSIONAL` | A production-oriented runtime. | Core engine; professional composition. |
| `EDUCATIONAL` | Students and classrooms. | Core + the LabTalk campus / full education surface. |
| `DEVELOPMENT` | Working on the engine itself. | Everything: LabTalk, maintenance, external tools, developer aliases. |

The exact component composition per product (LabTalk, maintenance, external,
dev, education essentials) is defined and maintained in the architecture
decision record — see below. Treat that record as authority for what each
edition contains; this table is the intent, not the contract.

### 2. Index mode — which indexing engine is compiled in

Set with `-D DOTTALK_INDEX_MODE=<name>`. Runtime-proven, per the build proof
matrix:

| Index mode | Build graph | What you get |
| --- | --- | --- |
| `NONE` | `xbase` + `memo` + `xexpr`; **no** `xindex` library | Physical DBF open/read/CRUD. No `SEEK`, no index commands. |
| `LEGACY` | `xbase` + `xindex` **without** the LMDB backend | CNX attach / order / `SEEK`. No LMDB commands. |
| `LMDB` | `xbase` + full `xindex` | Full index surface: CNX + CDX + native LMDB persistence. |

Key architecture point: **`xbase.lib` no longer owns `xindex`.** The table
engine exposes neutral optional hooks; `xindex.lib` depends on `xbase` and
installs those hooks when an index manager is attached. A `NONE` build omits the
`xindex` target and library entirely.

One honest caveat, straight from the proof matrix: `dottalkpp.exe` still links
LMDB independently for the runtime message catalog, so `DOTTALK_INDEX_MODE=NONE`
means *no xindex engine* — not yet *no LMDB dependency anywhere*. The Python
module and `xbase` library need no xindex in `NONE`.

## Canonical builds (Windows presets)

These presets pin a product + index mode together. Copy-paste to build. Verified
against `CMakePresets.json` and the build proof matrix, 2026-07-14.

```powershell
# LEAN, physical only (no index engine)
cmake --preset windows-lean-table
cmake --build --preset windows-lean-table --target dottalkpp pydottalk
ctest --preset windows-lean-table

# LEAN with LMDB indexing
cmake --preset windows-lean-lmdb
cmake --build --preset windows-lean-lmdb --target dottalkpp
ctest --preset windows-lean-lmdb

# EDUCATIONAL with LMDB (students / classroom)
cmake --preset windows-educational-lmdb

# DEVELOPMENT with LMDB (working on the engine)
cmake --preset windows-development-lmdb
```

## Compatibility note

The older `DOTTALK_WITH_INDEX` boolean still works and now maps onto the modes:

- `DOTTALK_WITH_INDEX=ON`  → `LMDB`
- `DOTTALK_WITH_INDEX=OFF` (with no explicit mode) → `LEGACY`
- only an explicit `DOTTALK_INDEX_MODE=NONE` removes `xindex`

## After the build

The runtime has no sample data until you build it. Run the data build:

```powershell
.\dottalkpp\scripts\mcc\build_mcc_demo_bases.ps1
```

Then try it:

```powershell
.\datarun.ps1
```
```text
USE STUDENTS
SET INDEX TO STUDENTS
SET ORDER TO TAG LNAME
SMARTLIST 10
```

Full walkthrough: `dottalkpp/data/scripts/mcc/README.md`.

## Proof and rationale (authority)

This page summarizes; these records own the detail and the evidence:

- `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` — what is built and
  proven for each mode (NONE / LEGACY / LMDB), with the runtime evidence and the
  registered CTest proofs.
- `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md` — why the
  index engine is optional and how `xbase` / `xindex` are separated.
- `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md` — the plan
  behind the edition split.

If this page and those records ever disagree, the records win — and the
disagreement is a drift bug worth fixing.

## License

To be determined. Editions intended for distribution (LEAN, PROFESSIONAL) will
need this settled before public release.
