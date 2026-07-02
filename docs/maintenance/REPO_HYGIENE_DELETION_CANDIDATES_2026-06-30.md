# Repo Hygiene Deletion Candidates - 2026-06-30

Status: deletion-candidate list only.

No files are deleted by this report. These are candidates to delete only after Derald reviews and explicitly approves deletion. In the current cleanup pass, matching items may be moved to an outside review folder instead.

## Candidate Rule

These entries are untracked by Git, classified low risk, and look like generated output, cache, screenshots, accidental root litter, or temporary local database/build output.

## Exact Candidates

- `__pycache__` - Generated build/cache output; keep out of repo root.
- `--runtime-root` - Accidental flag-like root file.
- `-Filter` - Accidental flag-like root file.
- `-Pattern` - Accidental flag-like root file.
- `.venv` - Generated build/cache output; keep out of repo root.
- `.vs` - Generated build/cache output; keep out of repo root.
- `=` - Accidental flag-like root file.
- `bin` - Generated build/cache output; keep out of repo root.
- `build` - Generated build/cache output; keep out of repo root.
- `build_rdi` - Generated build/cache output; keep out of repo root.
- `build-gui-core-check` - Generated build/cache output; keep out of repo root.
- `build-gui-lmdb-check` - Generated build/cache output; keep out of repo root.
- `build-gui-plan-check` - Generated build/cache output; keep out of repo root.
- `build-pro-md` - Generated build/cache output; keep out of repo root.
- `build-profile-dev-check` - Generated build/cache output; keep out of repo root.
- `build-profile-prod-check` - Generated build/cache output; keep out of repo root.
- `build-tests` - Generated build/cache output; keep out of repo root.
- `build-wsl` - Generated build/cache output; keep out of repo root.
- `build-wx-check` - Generated build/cache output; keep out of repo root.
- `build-wx-vcpkg-check` - Generated build/cache output; keep out of repo root.
- `build.ninja` - Generated CMake/build output.
- `cmake_install.cmake` - Generated CMake/build output.
- `CMakeCache.txt` - Generated CMake/build output.
- `CMakePresets.json.pre_msvc_runtime_fix_20260517-062406.bak` - Backup or generated local database output.
- `CTestTestfile.cmake` - Generated CMake/build output.
- `DartConfiguration.tcl` - Generated CMake/build output.
- `dist` - Generated build/cache output; keep out of repo root.
- `Screenshot 2026-05-06 153431.jpg` - Screenshot capture, not source.
- `Screenshot 2026-05-08 122827.jpg` - Screenshot capture, not source.
- `Screenshot 2026-05-09 091500.jpg` - Screenshot capture, not source.
- `Screenshot 2026-05-09 115355.jpg` - Screenshot capture, not source.
- `Screenshot 2026-05-10 095204.jpg` - Screenshot capture, not source.
- `Screenshot 2026-05-20 131334.jpg` - Screenshot capture, not source.
- `Screenshot 2026-05-31 080348.jpg` - Screenshot capture, not source.
- `Screenshot 2026-06-02 141131.jpg` - Screenshot capture, not source.
- `TMP` - Generated build/cache output; keep out of repo root.
- `tmpsql_regression.sqlite` - Backup or generated local database output.
- `Unknown` - Accidental flag-like root file.
- `vcpkg_installed` - Generated build/cache output; keep out of repo root.

## Not Deletion Candidates In This Pass

- Anything tracked by Git.
- `D:\code\ccode\x64base`.
- Source-bearing directories such as `src`, `include`, `bindings`, `tests`, `tools`, and intentional docs.
- Medium-risk archives/backups until reviewed.
- Review-first directories and root notes.

## Current Action

Move candidates may be relocated to `C:\dottalkpp-review\repo-cleanup-2026-06-30` for review. Deletion remains a separate later step.
