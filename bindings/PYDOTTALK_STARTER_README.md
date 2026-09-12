# pydottalk starter bundle

This bundle is a conservative starter layer for using `pydottalk` with the existing DotTalk++ / x64base tree.

It does **not** turn Python into the DotTalk command shell. Current `pydottalk 0.3.0` is a small pybind11 binding over `xbase::DbArea`, so this bundle starts with read-only table access and helper ergonomics.

## Files

Drop these files into the repo root, preserving paths:

```text
cmake/AddPydotTalkIfPresent.cmake
bindings/pydottalk_helpers.py
bindings/pydottalk_probe_api.py
bindings/pydottalk_smoke_readonly.py
bindings/pydottalk_smoke_x64.py
bindings/run_pydottalk_smokes.ps1
bindings/PYDOTTALK_STARTER_README.md
```

## Build

From the repo root, beside `build.ps1` and its siblings:

```powershell
.\build_pydottalk.ps1
```

That is the LEAN path (2026-08-17): it configures `bindings/pydottalk` as its own
CMake project and builds `xbase`, `xindex`, `memo` and the module. It does NOT
build `dottalkpp.exe`, the Turbo Vision UI, or the BBS daemon -- the binding
links three libraries and references none of those.

The extension lands in:

```text
build-pydottalk\python\pydottalk.cp312-win_amd64.pyd
```

`-ViaRootBuild` restores the old behaviour (full tree, including the CLI) if you
need `dottalkpp.exe` present for something.

### The interpreter

**Python 3.12.** The module ships as `cp312-win_amd64.pyd` and the build script
refuses anything else -- a 3.13 with headers would configure happily and emit a
`cp313` module no 3.12 caller can import.

The interpreter is the **vcpkg root install**, which `.venv312\pyvenv.cfg` names:

```text
C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe
```

NOT `build-labtalk\vcpkg_installed\...\python3\` -- that directory contains
only `pkgconf`, and this README pointed at it until 2026-08-17. The script finds
the right one from `$VcpkgRoot`; pass `-PythonExe` to override.

## Run the probes

```powershell
$repo = (Resolve-Path .).Path
$py12 = "C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe"
$env:PYDOTTALK_BIN = Join-Path $repo "build-pydottalk\python"
$env:PYTHONPATH = $env:PYDOTTALK_BIN

& $py12 (Join-Path $repo "bindings\pydottalk_probe_api.py")
& $py12 (Join-Path $repo "bindings\pydottalk_smoke_readonly.py")
& $py12 (Join-Path $repo "bindings\pydottalk_smoke_x64.py")
```

Or let ctest run the two registered smokes:

```powershell
ctest --test-dir build-pydottalk -C Release --output-on-failure
```

Or the runner:

```powershell
.\bindings\run_pydottalk_smokes.ps1 `
  -PythonExe "C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe"
```

## Useful environment variables

```powershell
$repo = (Resolve-Path .).Path
$env:PYDOTTALK_BIN = Join-Path $repo "build-pydottalk\python"
$env:DOTTALK_DBF_DIR = Join-Path $repo "dottalkpp\data\dbf\sandbox"
$env:DOTTALK_X64_DBF = Join-Path $env:DOTTALK_DBF_DIR "students_x64.dbf"
$env:DOTTALK_X64_DBF_DIR = Join-Path $repo "dottalkpp\data\dbf\x64"
```

## What this proves

The starter smokes prove:

- Python can import the built `.pyd`.
- The live exposed API is known.
- `DbArea` can open a real DBF read-only.
- Field metadata and record values can be read.
- A candidate x64/x64base DBF can be opened and read.

## What this does not prove yet

These are later milestones:

- index/CDX/LMDB traversal from Python
- `seek` / `set_order` from Python
- relation traversal from Python
- memo payload read/write policy from Python
- command-shell execution from Python
- writes/appends/deletes safety contracts
