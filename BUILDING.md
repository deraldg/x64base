# Building DotTalk++ / x64base

The front door for building the engine from a fresh clone. It describes the
build presets **that exist in this repository right now**. There is no prebuilt
binary here -- this is a development-stage project; you build the runtime
yourself, then run the data build.

If a command below fails, that is a bug in this page -- please report it. This
page is meant to describe only what a cold clone actually contains.

## Prerequisites (Windows)

- **Visual Studio 2022** (MSVC v143, "Desktop development with C++").
- **CMake >= 3.21** (the Visual Studio installer can provide it).
- **vcpkg** -- clone and bootstrap from https://github.com/microsoft/vcpkg
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

**If you just want a working database runtime on Windows, use `pro-md`** -- it is
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

Note: configure-preset names and build-preset names differ -- the build presets
carry a `-Release` suffix (e.g. `pro-md` configures, `pro-md-Release` builds).

## After the build

The runtime has no sample data until you build it. Build the demo databases
(this is self-contained -- it resets, extracts the canonical archive, and builds
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
  from your build output into `dottalkpp\bin` automatically -- you don't stage it
  by hand. This currently expects a **`pro-md`** build (`build\src\Release`).
- On x64, ordered reads are LMDB-backed, so the `SET ORDER` above needs the
  LMDB envs that `build_mcc_demo_bases.ps1` builds. The `.cnx`/`.cdx` shipped in
  the repo let you open and read, but ordered x64 access requires that databuild.

Full walkthrough: `dottalkpp/data/scripts/mcc/README.md`.

## Editions

**Corrected 2026-08-17.** This section previously said the edition system was
"not on the public repository yet" and told readers not to expect
`DOTTALK_PRODUCT` or `windows-lean-*` presets in this clone. That is wrong, and
was wrong on `main` as well: `origin/main`'s `CMakePresets.json` carries 28
occurrences of those names, including the `windows-lean-table` and
`windows-lean-lmdb` presets. The page was telling readers that features present
in their own checkout were absent.

Both axes are live and are **independent** of each other:

- **Products** (`DOTTALK_PRODUCT`): `LEAN`, `PROFESSIONAL`, `EDUCATIONAL`,
  `DEVELOPMENT`. Default `DEVELOPMENT`.
- **Index modes** (`DOTTALK_INDEX_MODE`): `NONE`, `LEGACY`, `LMDB`.

`LEAN` does not mean engine-only and does not mean no-index. Note also that the
default index mode is **`LEGACY`, not `NONE`**: passing `-DDOTTALK_WITH_INDEX=OFF`
disables only the LMDB backend and leaves the house index in place.

**Full reference:** `docs/manuals/developer/dev/dev-21-build-system.md` (DEV-21
Build System) documents every target, option, preset, entry-point script and
platform status, with the measured landmines.

Design and proof records for the edition work:

- `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md`
- `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`
- `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md`

Still outstanding: a cold-clone build certification for the edition matrix. The
presets exist and are used daily; what has NOT been demonstrated is a fresh
clone building each product/index combination from scratch on a clean machine.

## License

To be determined. Editions intended for distribution will need this settled
before public release.
