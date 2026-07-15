# Building DotTalk++ / x64base

The front door for building the engine from a fresh clone. It describes the
build presets **that exist in this repository right now**. There is no prebuilt
binary here — this is a development-stage project; you build the runtime
yourself, then run the data build.

If a command below fails, that is a bug in this page — please report it. This
page is meant to describe only what a cold clone actually contains.

## Prerequisites (Windows)

- **Visual Studio 2022** (MSVC v143, "Desktop development with C++").
- **CMake ≥ 3.21** (the Visual Studio installer can provide it).
- **vcpkg** — clone and bootstrap from https://github.com/microsoft/vcpkg
- **Set the vcpkg environment variable.** The presets reference two names for
  historical reasons; set **both** to your vcpkg checkout so every preset
  resolves:

  ```powershell
  $env:VCPKG_ROOT              = "C:\path\to\vcpkg"
  $env:VCPKG_INSTALLATION_ROOT = "C:\path\to\vcpkg"
  ```

  Dependencies are declared in `vcpkg.json` and restored automatically on the
  first configure (manifest mode).

## Choose a build

Pick the preset that matches what you want. All are defined in
`CMakePresets.json`.

| Preset | Toolchain | Index engine | GUI/TUI | For |
| --- | --- | --- | --- | --- |
| `windows-core` | MSVC + vcpkg | none | none | The simplest Windows build of the core engine. |
| `index-vcpkg` | Ninja + vcpkg | **LMDB** | none | Core plus LMDB indexing. |
| `pro-md` | MSVC + vcpkg (/MD) | **LMDB** | Turbo Vision | Full DotTalk++ development build. |
| `pro-md-labtalk` | MSVC + vcpkg (/MD) | **LMDB** | Turbo Vision + Python | Development build with the pydottalk bindings. |
| `ansi-mt` | MSVC (/MT static) | LMDB | none | ANSI, static runtime, no TV. |
| `core` / `core-vcpkg` | Ninja | none | none | Portable core (system deps / vcpkg). |
| `wsl` | Ninja (Linux) | LMDB | none | Building under WSL. |

**If you just want a working database runtime on Windows, use `pro-md`** — it is
the fullest build (indexing + the Turbo Vision UI) and is the one named for
day-to-day development.

## Build it

```powershell
# Full Windows development build (indexing + TV)
cmake --preset pro-md
cmake --build --preset pro-md-Release --target dottalkpp

# Or the minimal core engine
cmake --preset windows-core
cmake --build --preset windows-core --target dottalkpp
```

Note: configure-preset names and build-preset names differ — the build presets
carry a `-Release` suffix (e.g. `pro-md` configures, `pro-md-Release` builds).

## After the build

The runtime has no sample data until you build it. Build the demo databases
(this is self-contained — it resets, extracts the canonical archive, and builds
all three lanes plus the x64 LMDB indexes):

```powershell
.\dottalkpp\scripts\mcc\build_mcc_demo_bases.ps1
```

It warns before overwriting and waits for you to type `YES`. Then run the
shell and query:

```powershell
.\datarun.ps1
```
```text
DO X64
USE STUDENTS
SET INDEX TO STUDENTS
SET ORDER TO TAG LNAME
SMARTLIST 10
```

`DO X64` first: the default DBF path is `data\dbf`, not a lane, so a bare
`USE STUDENTS` won't find the table. `DO X64` points DBF/INDEXES/LMDB at the
x64 lane (`DO X32` and `DO VFP` select the other flavors). Record 1 by `LNAME`
should read `Anderson`.

Notes:
- `datarun.ps1` copies the freshly-built `dottalkpp.exe` (and its runtime DLLs)
  from your build output into `dottalkpp\bin` automatically — you don't stage it
  by hand. This currently expects a **`pro-md`** build (`build\src\Release`).
- On x64, ordered reads are LMDB-backed, so the `SET ORDER` above needs the
  LMDB envs that `build_mcc_demo_bases.ps1` builds. The `.cnx`/`.cdx` shipped in
  the repo let you open and read, but ordered x64 access requires that databuild.

Full walkthrough: `dottalkpp/data/scripts/mcc/README.md`.

## Editions (in development — not yet in this repository)

A larger build-composition system is being developed: named **products**
(`LEAN`, `PROFESSIONAL`, `EDUCATIONAL`, `DEVELOPMENT`) and explicit **index
modes** (`NONE`, `LEGACY`, `LMDB`), with dedicated presets. It is **not on the
public repository yet** — do not expect `DOTTALK_PRODUCT` or `windows-lean-*`
presets in this clone.

The design and proof records for that in-progress work:

- `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md`
- `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`
- `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md`

When the edition system is published and certified with a cold-clone build, this
page will describe it. Until then, use the presets in the table above.

## License

To be determined. Editions intended for distribution will need this settled
before public release.
